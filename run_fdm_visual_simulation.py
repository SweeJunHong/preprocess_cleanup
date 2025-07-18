"""
FDM Visual Simulation - Command Line Interface

Simple command-line interface for running FDM simulation with visualization.
"""

import sys
import os
from fdm_simulation import FDMSimulator
from fdm_visualization import FDMVisualizer
import webbrowser

def run_visual_simulation(stl_file_path: str, open_browser: bool = True):
    """
    Run FDM simulation with visualization for a given STL file.
    
    Args:
        stl_file_path: Path to STL file
        open_browser: Whether to open results in browser
    """
    print(f"FDM Visual Simulation")
    print(f"Analyzing: {stl_file_path}")
    print("=" * 60)
    
    # Check if file exists
    if not os.path.exists(stl_file_path):
        print(f"ERROR: File not found: {stl_file_path}")
        return False
    
    try:
        # Create simulator
        simulator = FDMSimulator()
        
        # Load STL file
        print("Loading STL file...")
        if not simulator.load_stl(stl_file_path):
            print("ERROR: Failed to load STL file")
            return False
        
        # Run complete analysis
        print("Running FDM simulation...")
        results = simulator.run_complete_analysis()
        
        # Create visualizer
        print("Generating visualizations...")
        visualizer = FDMVisualizer()
        visualizer.load_mesh_data(
            simulator.mesh,
            simulator.layers,
            results['detailed_analysis']['geometry']['overhang_analysis']
        )
        
        # Generate visualizations
        base_name = os.path.splitext(os.path.basename(stl_file_path))[0]
        
        # 3D Mesh View
        mesh_fig = visualizer.create_3d_mesh_view()
        mesh_file = f"fdm_mesh_{base_name}.html"
        visualizer.save_visualization_html(mesh_fig, mesh_file)
        
        # Layer Animation (limited layers for performance)
        animation_fig = visualizer.create_layer_by_layer_animation(max_layers=20)
        animation_file = f"fdm_animation_{base_name}.html"
        visualizer.save_visualization_html(animation_fig, animation_file)
        
        # Print Paths
        if simulator.layers:
            path_fig = visualizer.create_print_path_visualization(len(simulator.layers)//2)
            path_file = f"fdm_paths_{base_name}.html"
            visualizer.save_visualization_html(path_fig, path_file)
        
        # Analytics Dashboard
        dashboard_fig = visualizer.create_printing_analytics_dashboard(results)
        dashboard_file = f"fdm_dashboard_{base_name}.html"
        visualizer.save_visualization_html(dashboard_fig, dashboard_file)
        
        # Print summary
        rl_metrics = results['rl_metrics']
        print("\n" + "=" * 60)
        print("SIMULATION RESULTS")
        print("=" * 60)
        print(f"Manufacturing Cost:    ${rl_metrics['manufacturing_cost']:.2f}")
        print(f"Time to Completion:    {rl_metrics['time_to_completion']:.1f} hours")
        print(f"Quality Score:         {rl_metrics['quality_metrics']['overall_score']:.1f}/100")
        print(f"Material Waste:        {rl_metrics['material_waste']['waste_percentage']:.1f}%")
        print(f"Post-Processing:       {rl_metrics['post_processing_requirements']['time_hours']:.1f} hours")
        print("=" * 60)
        
        print("\nGenerated Visualization Files:")
        print(f"  - {mesh_file} (3D mesh view)")
        print(f"  - {animation_file} (layer animation)")
        print(f"  - {path_file} (print paths)")
        print(f"  - {dashboard_file} (analytics dashboard)")
        
        # Open in browser if requested
        if open_browser:
            print(f"\nOpening dashboard in browser...")
            try:
                webbrowser.open(f"file://{os.path.abspath(dashboard_file)}")
            except Exception as e:
                print(f"Could not open browser: {e}")
        
        print(f"\n[SUCCESS] Visual simulation complete!")
        return True
        
    except Exception as e:
        print(f"ERROR: Simulation failed: {e}")
        return False

def main():
    """Main command-line interface."""
    
    print("FDM Visual Simulation System")
    print("=" * 40)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        stl_file = sys.argv[1]
        open_browser = len(sys.argv) <= 2 or sys.argv[2].lower() != 'nobrowser'
    else:
        # Interactive mode
        print("\nAvailable test files:")
        test_files = [
            "testcases/simple/cube.stl",
            "testcases/simple/cylinder.stl", 
            "testcases/simple/sphere.STL"
        ]
        
        for i, file in enumerate(test_files, 1):
            print(f"  {i}. {file}")
        
        print(f"  {len(test_files)+1}. Enter custom file path")
        
        try:
            choice = input(f"\nSelect file (1-{len(test_files)+1}): ").strip()
            
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(test_files):
                    stl_file = test_files[choice_num - 1]
                elif choice_num == len(test_files) + 1:
                    stl_file = input("Enter STL file path: ").strip()
                else:
                    print("Invalid choice")
                    return
            else:
                stl_file = choice
            
            open_browser_input = input("Open visualizations in browser? (y/n): ").lower()
            open_browser = open_browser_input in ['y', 'yes', '']
            
        except KeyboardInterrupt:
            print("\nCancelled by user")
            return
    
    # Run simulation
    success = run_visual_simulation(stl_file, open_browser)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()