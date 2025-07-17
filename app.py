import streamlit as st
import tempfile
import os
import trimesh
from cnc_analyzer import CNCAnalyzer
from visualization import create_3d_visualization, create_summary_chart
from report_generator import ReportGenerator
import plotly.graph_objects as go
from mesh_utils import repair_mesh

# Page configuration
st.set_page_config(
    page_title="CNC Manufacturability Analyzer",
    page_icon="🔧",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .reportview-container .main .block-container {
        max-width: 1200px;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("🔧 CNC Manufacturability Analyzer")
st.markdown(
    """
        Analyze STL files for CNC manufacturability issues. Upload your part and get instant feedback on:
            - Undercuts
            - Internal volumes
            - Steep walls
            - Narrow channels
            - Small features
            - Deep pockets
    """)

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Analysis Configuration")
    
    # Analysis settings
    st.subheader("Tool Parameters")
    min_tool_diameter = st.slider("Minimum Tool Diameter (mm)", 1.0, 10.0, 3.0, 0.5)
    min_channel_width = st.slider("Minimum Channel Width (mm)", 1.0, 10.0, 2.0, 0.5)
    
    st.subheader("Geometry Thresholds")
    steep_angle_threshold = st.slider("Steep Wall Angle (degrees)", 60.0, 89.0, 80.0, 1.0)
    deep_pocket_threshold = st.slider("Deep Pocket Threshold (mm)", 10.0, 50.0, 30.0, 5.0)
    
    st.subheader("Analysis Options")
    use_context_aware = st.checkbox("Use Context-Aware Analysis", value=True)
    
    # Select which analyses to run
    st.subheader("Select Analyses")
    analyses = {
        'undercuts': st.checkbox("Undercuts", value=True),
        'internal_volumes': st.checkbox("Internal Volumes", value=True),
        'small_features': st.checkbox("Small Features", value=True),
        'steep_walls': st.checkbox("Steep Walls", value=True),
        'narrow_channels': st.checkbox("Narrow Channels", value=True),
        'deep_pockets': st.checkbox("Deep Pockets", value=True)
    }

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📁 Upload STL File")
    uploaded_file = st.file_uploader("Choose an STL file", type=['stl', 'STL'])
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.stl') as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name
        
        # Load and analyze
        try:
            st.info("Loading mesh...")
            mesh = trimesh.load(tmp_path)
            mesh, repair_log = repair_mesh(mesh)
           
            if not isinstance(mesh, trimesh.Trimesh) or mesh.vertices.shape[0] == 0 or mesh.faces.shape[0] == 0:
                st.error("Uploaded file could not be loaded as a valid mesh. Please check your STL file.")
                st.stop()
        
            # Display mesh info
            st.success("Mesh loaded successfully!")
            
            
            mesh_info = {
                'vertices': len(mesh.vertices),
                'faces': len(mesh.faces),
                'volume': mesh.volume,
                'is_watertight': mesh.is_watertight,
                'bounds': mesh.bounds.tolist()
            }
            
            st.subheader("Mesh Information")
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Vertices", f"{mesh_info['vertices']:,}")
                st.metric("Volume", f"{mesh_info['volume']:.2f} mm³")
            with col_b:
                st.metric("Faces", f"{mesh_info['faces']:,}")
                st.metric("Watertight", "Yes" if mesh_info['is_watertight'] else "No")
            
            # Run analysis button
            if st.button("🔍 Run Analysis", type="primary"):
                with st.spinner("Analyzing..."):
                    # Create analyzer with config
                    config = {
                        'min_tool_diameter': min_tool_diameter,
                        'min_channel_width': min_channel_width,
                        'steep_angle_threshold': steep_angle_threshold,
                        'deep_pocket_threshold': deep_pocket_threshold,
                        'min_depth': 5.0,
                        'use_context_aware': use_context_aware,
                        'analysis_methods': analyses
                    }
                    
                    analyzer = CNCAnalyzer(config)
                    analyzer.mesh = mesh
                    
                    # Run selected analyses
                    if any(analyses.values()):
                        results = analyzer.analyze_all()
                        score = analyzer.calculate_score()
                        problem_regions = analyzer.get_problem_regions()
                        
                        # Store in session state
                        st.session_state['analysis_complete'] = True
                        st.session_state['analyzer'] = analyzer
                        st.session_state['mesh'] = mesh
                        st.session_state['mesh_info'] = mesh_info
                        st.session_state['score'] = score
                        st.session_state['problem_regions'] = problem_regions
                    else:
                        st.warning("Please select at least one analysis to run.")
            
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

# Results column
with col2:
    if 'analysis_complete' in st.session_state and st.session_state['analysis_complete']:
        st.header("📊 Analysis Results")
        
        # Score display
        score = st.session_state['score']
        score_color = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
        st.metric(f"{score_color} Manufacturability Score", f"{score:.1f} / 100")
        
        # Summary chart
        st.subheader("Problem Summary")
        summary_chart = create_summary_chart(
            st.session_state['analyzer'].results,
            st.session_state['score']
        )
        st.image(f"data:image/png;base64,{summary_chart}")
        
        # Detailed results
        with st.expander("📋 Detailed Results", expanded=True):
            for function_name, results in st.session_state['analyzer'].results.items():
                if 'error' not in results:
                    problem_name = function_name.replace('_', ' ').title()
                    count = results.get('count', 0)
                    severity = results.get('severity', 0)
                    # Only treat severity as a number if it's int or float
                    severity_val = severity if isinstance(severity, (int, float)) else 0
                    has_problem = results.get('has_problem', count > 0 or severity_val > 0)

                    if has_problem:
                        st.markdown(f"** {problem_name}**")
                        if 'count' in results:
                            st.write(f"- Found: {results['count']} issues")
                        if 'severity' in results:
                            sev = results['severity']
                            if isinstance(sev, (int, float)):
                                sev_str = ['None', 'Minor', 'Major'][sev] if sev in [0, 1, 2] else str(sev)
                            else:
                                sev_str = str(sev)
                            st.write(f"- Severity: {sev_str}")
                        if 'recommendation' in results:
                            st.info(results['recommendation'])
                    else:
                        st.markdown(f"** {problem_name}** - No issues")

# 3D Visualization section
if 'analysis_complete' in st.session_state and st.session_state['analysis_complete']:
    st.header("🎯 3D Visualization")
    
    # Create 3D plot
    fig = create_3d_visualization(
        st.session_state['mesh'],
        st.session_state['problem_regions'],
        st.session_state['score']
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Report generation section
    st.header("📄 Generate Report")
    
    col_1, col_2, col_3 = st.columns(3)
    
    report_gen = ReportGenerator(
        st.session_state['analyzer'],
        st.session_state['mesh_info']
    )
    
    with col_1:
        if st.button("📄 Generate HTML Report"):
            html_report = report_gen.generate_html_report(
                summary_chart_base64=summary_chart
            )
            st.download_button(
                label="Download HTML Report",
                data=html_report,
                file_name="cnc_analysis_report.html",
                mime="text/html"
            )
    
    with col_2:
        if st.button("📊 Generate JSON Report"):
            json_report = report_gen.generate_json_report()
            st.download_button(
                label="Download JSON Report",
                data=json_report,
                file_name="cnc_analysis_report.json",
                mime="application/json"
            )
    
    with col_3:
        if st.button("📝 Generate Markdown Report"):
            md_report = report_gen.generate_markdown_report()
            st.download_button(
                label="Download Markdown Report",
                data=md_report,
                file_name="cnc_analysis_report.md",
                mime="text/markdown"
            )

# Footer
st.markdown("---")
st.markdown("""
            <div style='text-align: center'>
                <p>CNC Manufacturability Analyzer v1.0 | Built with Streamlit</p>
            </div>
            """,unsafe_allow_html=True)


# # web interface
# streamlit run app.py

# # or programmatic
# from cnc_analyzer import CNCAnalyzer
# analyzer = CNCAnalyzer()
# analyzer.load_mesh("part.stl")
# results = analyzer.analyze_all()




# cad model such as dover joint, where as there should be undercut detected, it is not detected, detected as small feature instead
# for L bracket, small features detected for the hole
# a t-slot stl file, where it has  should have deep pockets detected, undercuts detected, and narrow channels detected, however its not, its 50 mm in z value 
# another question i have is why t-slot has been rated at 90% manufacturable, as when its been cut, its a 20mm width (x), 20mm height(y), and 50 mm depth(z), if taken this way, the bottom of the t-slot, thats been laid on the workstation wont be assessible by the tool,
# if its the z value thats take to be the top, then wont deep pockets be detected ?  theres a hole in the middle of the t-slot, which is 20mm in diameter, and 50mm deep, so should it be detected as a deep pocket  
# for a traffic cone should, it should be detected as not watertight, undercut detected since the width of the top of the cone is smaller then the bottom
# 
