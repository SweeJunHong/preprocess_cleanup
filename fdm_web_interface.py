"""
FDM Simulation Web Interface

Interactive Streamlit web application for FDM simulation with visual feedback.
"""

import streamlit as st
import tempfile
import os
import json
from fdm_simulation import FDMSimulator
from fdm_visualization import FDMVisualizer, create_interactive_visualization_app
import plotly.graph_objects as go
import time

# Page configuration
st.set_page_config(
    page_title="FDM Simulation & Visualization",
    page_icon="🖨️",
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
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main Streamlit application."""
    
    # Title and description
    st.title("🖨️ FDM Additive Manufacturing Simulator")
    st.markdown("""
    **Complete FDM simulation with visual feedback for RL training data generation**
    
    Upload STL files to analyze manufacturing metrics, visualize the printing process, 
    and generate training data for reinforcement learning models.
    """)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Simulation Settings")
        
        # Print settings
        st.subheader("Print Parameters")
        layer_height = st.slider("Layer Height (mm)", 0.1, 0.4, 0.2, 0.05)
        print_speed = st.slider("Print Speed (mm/s)", 20, 100, 50, 5)
        
        # Material settings
        st.subheader("Material Settings")
        material_cost = st.slider("Material Cost ($/kg)", 15.0, 50.0, 25.0, 1.0)
        filament_diameter = st.selectbox("Filament Diameter (mm)", [1.75, 2.85], index=0)
        
        # Visualization settings
        st.subheader("Visualization Options")
        show_supports = st.checkbox("Show Support Structures", value=True)
        max_animation_layers = st.slider("Max Animation Layers", 10, 100, 50, 5)
        
        # Animation speed control
        st.subheader("Animation Settings")
        animation_speed = st.selectbox("Animation Speed", 
                                     ["Very Slow (3s/layer)", "Slow (2s/layer)", "Normal (1s/layer)", "Fast (0.5s/layer)"],
                                     index=1)  # Default to "Slow"
        
        # Create custom config
        custom_config = {
            'layer_height': layer_height,
            'print_speed': print_speed,
            'material_cost_per_kg': material_cost,
            'filament_diameter': filament_diameter,
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
            
            try:
                # Initialize simulator
                if 'simulator' not in st.session_state:
                    st.session_state.simulator = FDMSimulator(custom_config)
                
                # Load mesh
                with st.spinner("Loading STL file..."):
                    if st.session_state.simulator.load_stl(tmp_path):
                        st.success("✅ STL file loaded successfully!")
                        
                        # Display mesh info
                        mesh = st.session_state.simulator.mesh
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("Vertices", f"{len(mesh.vertices):,}")
                            st.metric("Volume", f"{mesh.volume:.1f} mm³")
                        with col_b:
                            st.metric("Faces", f"{len(mesh.faces):,}")
                            st.metric("Watertight", "Yes" if mesh.is_watertight else "No")
                
                # Run simulation button
                if st.button("🚀 Run Complete Simulation", type="primary"):
                    with st.spinner("Running FDM simulation..."):
                        start_time = time.time()
                        
                        # Run complete analysis
                        results = st.session_state.simulator.run_complete_analysis()
                        
                        # Store results
                        st.session_state.results = results
                        st.session_state.analysis_time = time.time() - start_time
                        
                        st.success(f"✅ Simulation complete! ({st.session_state.analysis_time:.1f}s)")
                
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
    
    with col2:
        if 'results' in st.session_state:
            st.header("📊 Simulation Results")
            
            # Display RL metrics
            rl_metrics = st.session_state.results['rl_metrics']
            
            # Key metrics in cards
            metric_col1, metric_col2 = st.columns(2)
            
            with metric_col1:
                st.metric(
                    "💰 Manufacturing Cost", 
                    f"${rl_metrics['manufacturing_cost']:.2f}",
                    help="Total cost including materials, machine time, labor, and failure risk"
                )
                
                st.metric(
                    "⏱️ Time to Completion", 
                    f"{rl_metrics['time_to_completion']:.1f} hours",
                    help="Total time including printing and post-processing"
                )
                
                st.metric(
                    "🎯 Quality Score", 
                    f"{rl_metrics['quality_metrics']['overall_score']:.1f}/100",
                    help="Overall print quality assessment"
                )
            
            with metric_col2:
                st.metric(
                    "♻️ Material Waste", 
                    f"{rl_metrics['material_waste']['waste_percentage']:.1f}%",
                    help="Percentage of material wasted (supports + failures)"
                )
                
                st.metric(
                    "🔧 Post-Processing", 
                    f"{rl_metrics['post_processing_requirements']['time_hours']:.1f} hours",
                    help="Estimated post-processing time required"
                )
                
                st.metric(
                    "📏 Complexity", 
                    f"{rl_metrics['post_processing_requirements']['skill_level']}",
                    help="Required skill level for post-processing"
                )
    
    # Visualization section
    if 'results' in st.session_state and 'simulator' in st.session_state:
        st.header("🎥 3D Visualization")
        
        # Create visualizer
        visualizer = FDMVisualizer()
        visualizer.load_mesh_data(
            st.session_state.simulator.mesh,
            st.session_state.simulator.layers,
            st.session_state.results['detailed_analysis']['geometry']['overhang_analysis']
        )
        
        # Visualization tabs
        tab1, tab2, tab3, tab4 = st.tabs(["3D Mesh View", "Layer Animation", "Print Paths", "Analytics"])
        
        with tab1:
            st.subheader("3D Mesh with Support Structures")
            try:
                mesh_fig = visualizer.create_3d_mesh_view(show_supports=show_supports)
                st.plotly_chart(mesh_fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating 3D mesh view: {e}")
        
        with tab2:
            st.subheader("🎓 Educational 3D Printing Animation")
            st.markdown("**See how 3D printing works step by step!**")
            try:
                animation_fig = visualizer.create_educational_printing_animation(max_layers=max_animation_layers)
                st.plotly_chart(animation_fig, use_container_width=True)
                st.info("🎬 **How to watch:** Press '▶️ Start Printing' to see the layer-by-layer process. Notice how hot plastic (orange/red) is extruded and cools down (blue)!")
                
                # Add educational explanations
                with st.expander("🔍 What am I seeing?"):
                    st.markdown("""
                    - **🖨️ Print Head (red diamond)**: This is the nozzle that melts and extrudes plastic filament
                    - **💧 Molten Plastic (yellow dots)**: Hot plastic being extruded at ~200°C
                    - **🔥 Fresh Layers (orange/red)**: Newly printed layers that are still hot
                    - **🌡️ Cooling Layers (warm colors)**: Layers that are cooling down
                    - **❄️ Solid Layers (blue)**: Cooled and solidified layers
                    - **Build Platform (gray)**: The surface where printing begins
                    """)
            except Exception as e:
                st.error(f"Error creating animation: {e}")
        
        with tab3:
            st.subheader("Print Path Visualization")
            if st.session_state.simulator.layers:
                layer_selector = st.slider(
                    "Select Layer", 
                    0, 
                    len(st.session_state.simulator.layers)-1, 
                    len(st.session_state.simulator.layers)//2
                )
                try:
                    path_fig = visualizer.create_print_path_visualization(layer_selector)
                    st.plotly_chart(path_fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating print path view: {e}")
            else:
                st.warning("No layer data available for print path visualization")
        
        with tab4:
            st.subheader("Analytics Dashboard")
            try:
                dashboard_fig = visualizer.create_printing_analytics_dashboard(st.session_state.results)
                st.plotly_chart(dashboard_fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating dashboard: {e}")
    
    # Data export section
    if 'results' in st.session_state:
        st.header("💾 Export Data")
        
        col_export1, col_export2, col_export3 = st.columns(3)
        
        with col_export1:
            if st.button("📄 Download RL Metrics (JSON)"):
                rl_data = st.session_state.results['rl_metrics']
                rl_data['file_name'] = uploaded_file.name if uploaded_file else 'unknown'
                rl_data['analysis_timestamp'] = time.time()
                
                json_str = json.dumps(rl_data, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name=f"fdm_rl_metrics_{int(time.time())}.json",
                    mime="application/json"
                )
        
        with col_export2:
            if st.button("📊 Download Complete Analysis"):
                complete_data = st.session_state.results
                json_str = json.dumps(complete_data, indent=2, default=str)
                st.download_button(
                    label="Download Complete Analysis",
                    data=json_str,
                    file_name=f"fdm_complete_analysis_{int(time.time())}.json",
                    mime="application/json"
                )
        
        with col_export3:
            if st.button("🎯 Generate Training Sample"):
                # Create formatted training sample
                training_sample = {
                    'input_features': {
                        'volume': st.session_state.simulator.mesh.volume,
                        'surface_area': st.session_state.simulator.mesh.area,
                        'layer_height': custom_config['layer_height'],
                        'print_speed': custom_config['print_speed'],
                        'material_cost_per_kg': custom_config['material_cost_per_kg']
                    },
                    'target_metrics': st.session_state.results['rl_metrics'],
                    'metadata': {
                        'file_name': uploaded_file.name if uploaded_file else 'unknown',
                        'analysis_time': st.session_state.analysis_time,
                        'timestamp': time.time()
                    }
                }
                
                json_str = json.dumps(training_sample, indent=2)
                st.download_button(
                    label="Download Training Sample",
                    data=json_str,
                    file_name=f"fdm_training_sample_{int(time.time())}.json",
                    mime="application/json"
                )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center'>
        <p>FDM Simulation & Visualization System v1.0 | Built with Streamlit & Plotly</p>
        <p>Generates manufacturing metrics for reinforcement learning training</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()