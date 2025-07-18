"""
Test script to verify mesh handling improvements.
"""

from fdm_simulation import FDMSimulator, validate_and_fix_mesh
import trimesh

def test_mesh_loading():
    """Test mesh loading with different file types."""
    
    test_files = [
        ("testcases/simple/cube.stl", "Simple Cube"),
        ("testcases/simple/cylinder.stl", "Cylinder"),
        ("testcases/simple/sphere.STL", "Sphere")
    ]
    
    print("Testing Improved Mesh Handling")
    print("=" * 40)
    
    simulator = FDMSimulator()
    
    for file_path, description in test_files:
        print(f"\nTesting: {description}")
        print("-" * 30)
        
        try:
            # Test loading
            success = simulator.load_stl(file_path)
            
            if success:
                print(f"[OK] Mesh loaded successfully")
                print(f"  Type: {type(simulator.mesh)}")
                print(f"  Has bounds: {hasattr(simulator.mesh, 'bounds')}")
                
                # Test accessing bounds
                try:
                    bounds = simulator.mesh.bounds
                    print(f"  Bounds shape: {bounds.shape}")
                    print(f"  Bounds: {bounds}")
                    
                    # Test geometry analysis
                    geometry = simulator.analyze_geometry()
                    print(f"  Geometry analysis: [OK]")
                    
                except Exception as e:
                    print(f"  Error in geometry analysis: {e}")
                
            else:
                print(f"[FAILED] Failed to load mesh")
                
        except Exception as e:
            print(f"[ERROR] Exception during loading: {e}")
    
    print(f"\n{'='*40}")
    print("Mesh handling test complete!")

def test_validation_function():
    """Test the mesh validation function directly."""
    
    print("\nTesting Validation Function")
    print("-" * 30)
    
    # Test with a valid mesh
    try:
        mesh = trimesh.load("testcases/simple/cube.stl")
        validated_mesh, is_valid = validate_and_fix_mesh(mesh)
        
        print(f"Original mesh type: {type(mesh)}")
        print(f"Validation result: {is_valid}")
        print(f"Validated mesh type: {type(validated_mesh) if validated_mesh else None}")
        
    except Exception as e:
        print(f"Error in validation test: {e}")

if __name__ == "__main__":
    test_mesh_loading()
    test_validation_function()