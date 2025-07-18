"""
FDM Visual Simulation Demo

Comprehensive demonstration of the FDM simulation system with complete visual feedback.
This script showcases all visualization capabilities for different STL files.
"""

import os
import time
from fdm_simulation import FDMSimulator
from fdm_visualization import FDMVisualizer, create_interactive_visualization_app
import webbrowser

def run_comprehensive_demo():
    """Run comprehensive demo of FDM visual simulation system."""
    
    print("="*80)
    print("🖨️  FDM VISUAL SIMULATION SYSTEM - COMPREHENSIVE DEMO")
    print("="*80)
    print()
    
    # Test files to analyze
    test_files = [
        ("testcases/simple/cube.stl", "Simple Cube"),
        ("testcases/simple/cylinder.stl", "Cylinder"),
        ("testcases/simple/sphere.STL", "Sphere")
    ]
    
    all_results = []
    
    for file_path, description in test_files:
        print(f"\n🔄 ANALYZING: {description} ({file_path})")
        print("-" * 60)
        
        # Create simulator
        simulator = FDMSimulator()
        
        # Load and analyze
        if simulator.load_stl(file_path):
            start_time = time.time()
            
            # Run complete analysis
            results = simulator.run_complete_analysis()
            analysis_time = time.time() - start_time
            
            # Store results
            results['file_info'] = {
                'path': file_path,
                'description': description,
                'analysis_time': analysis_time
            }
            all_results.append(results)
            
            # Create visualizations
            print(f"\n📊 GENERATING VISUALIZATIONS...")
            
            visualizer = FDMVisualizer()
            visualizer.load_mesh_data(
                simulator.mesh,
                simulator.layers,
                results['detailed_analysis']['geometry']['overhang_analysis']
            )
            
            # Generate and save individual visualizations
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # 3D Mesh View
            mesh_fig = visualizer.create_3d_mesh_view()
            mesh_filename = f"fdm_mesh_{base_name}.html"
            visualizer.save_visualization_html(mesh_fig, mesh_filename)
            
            # Layer Animation
            animation_fig = visualizer.create_layer_by_layer_animation(max_layers=15)
            animation_filename = f"fdm_animation_{base_name}.html"
            visualizer.save_visualization_html(animation_fig, animation_filename)
            
            # Print Paths
            if simulator.layers:
                path_fig = visualizer.create_print_path_visualization(len(simulator.layers)//3)
                path_filename = f"fdm_paths_{base_name}.html"
                visualizer.save_visualization_html(path_fig, path_filename)
            
            # Analytics Dashboard
            dashboard_fig = visualizer.create_printing_analytics_dashboard(results)
            dashboard_filename = f"fdm_dashboard_{base_name}.html"
            visualizer.save_visualization_html(dashboard_fig, dashboard_filename)
            
            print(f"  ✅ Visualizations saved for {description}")
            
        else:
            print(f"  ❌ Failed to load {file_path}")
    
    # Generate comparison report
    print(f"\n📈 GENERATING COMPARISON REPORT...")
    create_comparison_report(all_results)
    
    # Generate batch visualization
    print(f"\n🎯 GENERATING BATCH VISUALIZATION...")
    create_batch_visualization(all_results)
    
    print(f"\n🎉 DEMO COMPLETE!")
    print("="*80)
    print("📁 Generated Files:")
    print("  • Individual visualizations for each part")
    print("  • fdm_comparison_report.html - Side-by-side comparison")
    print("  • fdm_batch_analysis.html - Batch analytics")
    print("  • Open any HTML file in your browser to view")
    print("="*80)
    
    # Ask if user wants to open visualizations
    try:
        choice = input("\n🌐 Open visualizations in browser? (y/n): ").lower()
        if choice == 'y':
            open_visualizations()
    except KeyboardInterrupt:
        print("\nDemo completed.")

def create_comparison_report(results_list):
    """Create side-by-side comparison of multiple parts."""
    
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    if not results_list:
        return
    
    # Extract data for comparison
    parts = []
    costs = []
    times = []
    qualities = []
    wastes = []
    
    for result in results_list:
        rl_metrics = result['rl_metrics']
        parts.append(result['file_info']['description'])
        costs.append(rl_metrics['manufacturing_cost'])
        times.append(rl_metrics['time_to_completion'])
        qualities.append(rl_metrics['quality_metrics']['overall_score'])
        wastes.append(rl_metrics['material_waste']['waste_percentage'])
    
    # Create comparison chart
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['Manufacturing Cost ($)', 'Time to Completion (hours)', 
                       'Quality Score (/100)', 'Material Waste (%)'],
        specs=[[{'type': 'bar'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'bar'}]]
    )
    
    # Cost comparison
    fig.add_trace(go.Bar(x=parts, y=costs, name='Cost', marker_color='lightcoral'), row=1, col=1)
    
    # Time comparison
    fig.add_trace(go.Bar(x=parts, y=times, name='Time', marker_color='lightblue'), row=1, col=2)
    
    # Quality comparison
    fig.add_trace(go.Bar(x=parts, y=qualities, name='Quality', marker_color='lightgreen'), row=2, col=1)
    
    # Waste comparison
    fig.add_trace(go.Bar(x=parts, y=wastes, name='Waste', marker_color='lightyellow'), row=2, col=2)
    
    fig.update_layout(
        title_text="FDM Parts Comparison Report",
        showlegend=False,
        height=600,
        width=1000
    )
    
    # Save comparison report
    fig.write_html("fdm_comparison_report.html")
    print("  ✅ Comparison report saved: fdm_comparison_report.html")

def create_batch_visualization(results_list):
    """Create batch analytics visualization."""
    
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    
    if not results_list:
        return
    
    # Prepare data
    data = []
    for result in results_list:
        rl_metrics = result['rl_metrics']
        geometry = result['detailed_analysis']['geometry']
        
        data.append({
            'Part': result['file_info']['description'],
            'Volume': geometry['volume'],
            'Cost': rl_metrics['manufacturing_cost'],
            'Time': rl_metrics['time_to_completion'],
            'Quality': rl_metrics['quality_metrics']['overall_score'],
            'Complexity': geometry['complexity']['score'],
            'Analysis_Time': result['file_info']['analysis_time']
        })
    
    # Create multi-panel dashboard
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=[
            'Volume vs Cost', 'Time vs Quality',
            'Complexity Distribution', 'Analysis Performance',
            'Cost-Quality Relationship', 'Processing Efficiency'
        ],
        specs=[
            [{'type': 'scatter'}, {'type': 'scatter'}],
            [{'type': 'bar'}, {'type': 'bar'}],
            [{'type': 'scatter'}, {'type': 'scatter'}]
        ]
    )
    
    parts = [d['Part'] for d in data]
    volumes = [d['Volume'] for d in data]
    costs = [d['Cost'] for d in data]
    times = [d['Time'] for d in data]
    qualities = [d['Quality'] for d in data]
    complexities = [d['Complexity'] for d in data]
    analysis_times = [d['Analysis_Time'] for d in data]
    
    # Volume vs Cost
    fig.add_trace(go.Scatter(
        x=volumes, y=costs, mode='markers+text',
        text=parts, textposition='top center',
        marker=dict(size=10, color='blue'),
        name='Volume vs Cost'
    ), row=1, col=1)
    
    # Time vs Quality
    fig.add_trace(go.Scatter(
        x=times, y=qualities, mode='markers+text',
        text=parts, textposition='top center',
        marker=dict(size=10, color='green'),
        name='Time vs Quality'
    ), row=1, col=2)
    
    # Complexity Distribution
    fig.add_trace(go.Bar(
        x=parts, y=complexities,
        marker_color='orange',
        name='Complexity'
    ), row=2, col=1)
    
    # Analysis Performance
    fig.add_trace(go.Bar(
        x=parts, y=analysis_times,
        marker_color='purple',
        name='Analysis Time (s)'
    ), row=2, col=2)
    
    # Cost-Quality Relationship
    fig.add_trace(go.Scatter(
        x=costs, y=qualities, mode='markers+text',
        text=parts, textposition='top center',
        marker=dict(size=10, color='red'),
        name='Cost vs Quality'
    ), row=3, col=1)
    
    # Processing Efficiency (Volume/Analysis Time)
    efficiency = [v/t for v, t in zip(volumes, analysis_times)]
    fig.add_trace(go.Bar(
        x=parts, y=efficiency,
        marker_color='teal',
        name='Processing Efficiency'
    ), row=3, col=2)
    
    # Update layout
    fig.update_layout(
        title_text="FDM Batch Analysis Dashboard",
        showlegend=False,
        height=900,
        width=1200
    )
    
    # Update axes labels
    fig.update_xaxes(title_text="Volume (mm³)", row=1, col=1)
    fig.update_yaxes(title_text="Cost ($)", row=1, col=1)
    fig.update_xaxes(title_text="Time (hours)", row=1, col=2)
    fig.update_yaxes(title_text="Quality Score", row=1, col=2)
    fig.update_xaxes(title_text="Cost ($)", row=3, col=1)
    fig.update_yaxes(title_text="Quality Score", row=3, col=1)
    fig.update_yaxes(title_text="Volume/Time (mm³/s)", row=3, col=2)
    
    # Save batch visualization
    fig.write_html("fdm_batch_analysis.html")
    print("  ✅ Batch analysis saved: fdm_batch_analysis.html")

def open_visualizations():
    """Open key visualizations in web browser."""
    
    key_files = [
        "fdm_comparison_report.html",
        "fdm_batch_analysis.html",
        "fdm_mesh_cube.html",
        "fdm_animation_cube.html"
    ]
    
    for filename in key_files:
        if os.path.exists(filename):
            try:
                webbrowser.open(f"file://{os.path.abspath(filename)}")
                time.sleep(1)  # Delay between opens
            except Exception as e:
                print(f"Could not open {filename}: {e}")

def quick_visualization_test():
    """Quick test of visualization capabilities."""
    
    print("[QUICK TEST] Visualization Test")
    print("-" * 40)
    
    simulator = FDMSimulator()
    if simulator.load_stl("testcases/simple/cube.stl"):
        results = simulator.run_complete_analysis()
        
        visualizer = FDMVisualizer()
        visualizer.load_mesh_data(
            simulator.mesh,
            simulator.layers, 
            results['detailed_analysis']['geometry']['overhang_analysis']
        )
        
        # Create quick dashboard
        dashboard = visualizer.create_printing_analytics_dashboard(results)
        dashboard.write_html("quick_test_dashboard.html")
        
        print("[SUCCESS] Quick test complete - check quick_test_dashboard.html")
        
        return True
    else:
        print("[FAILED] Quick test failed")
        return False

if __name__ == "__main__":
    print("FDM Visual Simulation Demo")
    print("Choose an option:")
    print("1. Full comprehensive demo")
    print("2. Quick visualization test")
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            run_comprehensive_demo()
        elif choice == "2":
            quick_visualization_test()
        else:
            print("Invalid choice. Running quick test...")
            quick_visualization_test()
            
    except KeyboardInterrupt:
        print("\nDemo cancelled by user.")