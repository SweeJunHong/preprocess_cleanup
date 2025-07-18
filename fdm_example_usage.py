"""
Example usage of the FDM Simulation System for RL Training Data Generation

This script demonstrates how to use the FDMSimulator to generate
manufacturing metrics for reinforcement learning training.
"""

from fdm_simulation import FDMSimulator
import json
import time

def analyze_single_part(file_path: str) -> dict:
    """
    Analyze a single STL file and extract RL training metrics.
    
    Args:
        file_path: Path to STL file
        
    Returns:
        dict: RL training metrics
    """
    print(f"Analyzing: {file_path}")
    
    # Create simulator with default config
    # Custom config can be passed if needed
    
    simulator = FDMSimulator()  # Use default config
    
    # Load and analyze
    if simulator.load_stl(file_path):
        results = simulator.run_complete_analysis()
        return results['rl_metrics']
    else:
        return None

def batch_analysis(file_list: list) -> list:
    """
    Analyze multiple STL files for batch RL data generation.
    
    Args:
        file_list: List of STL file paths
        
    Returns:
        list: List of RL metrics for each file
    """
    rl_dataset = []
    
    for file_path in file_list:
        metrics = analyze_single_part(file_path)
        if metrics:
            metrics['file_path'] = file_path
            rl_dataset.append(metrics)
    
    return rl_dataset

def save_rl_dataset(dataset: list, output_file: str):
    """Save RL dataset to JSON file."""
    with open(output_file, 'w') as f:
        json.dump(dataset, f, indent=2)
    print(f"Dataset saved to: {output_file}")

def main():
    """Example usage of the FDM simulation system."""
    print("FDM Simulation System - RL Training Data Generation")
    print("=" * 60)
    
    # Example 1: Single file analysis
    print("\n1. Single File Analysis:")
    metrics = analyze_single_part("testcases/simple/cube.stl")
    if metrics:
        print(f"Cost: ${metrics['manufacturing_cost']:.2f}")
        print(f"Time: {metrics['time_to_completion']:.1f} hours")
        print(f"Quality: {metrics['quality_metrics']['overall_score']:.1f}/100")
        print(f"Waste: {metrics['material_waste']['waste_percentage']:.1f}%")
        print(f"Post-processing: {metrics['post_processing_requirements']['time_hours']:.1f} hours")
    
    # Example 2: Batch analysis
    print("\n2. Batch Analysis:")
    test_files = [
        "testcases/simple/cube.stl",
        "testcases/simple/cylinder.stl",
        "testcases/simple/sphere.STL"
    ]
    
    dataset = batch_analysis(test_files)
    print(f"Generated {len(dataset)} RL training samples")
    
    # Save dataset
    save_rl_dataset(dataset, "fdm_rl_dataset.json")
    
    # Example 3: Custom configuration
    print("\n3. Custom Configuration Analysis:")
    custom_config = {
        'layer_height': 0.1,  # Higher quality
        'print_speed': 30,    # Slower speed
        'material_cost_per_kg': 35.0,  # Premium material
        'support_threshold': 30.0,  # More aggressive support
    }
    
    simulator = FDMSimulator(custom_config)
    if simulator.load_stl("testcases/simple/cube.stl"):
        results = simulator.run_complete_analysis()
        rl_metrics = results['rl_metrics']
        print(f"High-quality settings cost: ${rl_metrics['manufacturing_cost']:.2f}")
        print(f"Quality improvement: {rl_metrics['quality_metrics']['overall_score']:.1f}/100")

if __name__ == "__main__":
    main()