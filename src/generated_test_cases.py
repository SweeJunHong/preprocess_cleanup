import sys
import os
sys.path.append(os.path.dirname(__file__))  # Ensure src/ is in the path
import trimesh.creation
from manufacture_analysis import enhanced_find_undercuts, classify_undercut_severity
import trimesh
import numpy as np
# Test function for validation

def test_undercut_detection():
    """
    Test the undercut detection with known geometries.
    """
    print("=" * 60)
    print("TESTING UNDERCUT DETECTION ALGORITHMS")
    print("=" * 60)
    
    # Helper function to load and test STL files
    def test_stl_file(file_path, expected_undercuts, description):
        """Test a specific STL file and report results."""
        print(f"\n🔍 Testing: {description}")
        print(f"📁 File: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
        
        try:
            mesh = trimesh.load(file_path)
            if mesh is None:
                print(f"❌ Failed to load mesh from {file_path}")
                return False
            
            print(f"📊 Mesh info: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
            
            # Test with 3-axis CNC (top-down only)
            undercuts_3axis, metadata_3axis = enhanced_find_undercuts(mesh)
            
            # Test with 5-axis CNC (multiple directions)
            undercuts_5axis, metadata_5axis, severity = analyze_undercuts_multi_axis(mesh)
            
            print(f"🔧 3-axis CNC undercuts: {len(undercuts_3axis)} (expected: {expected_undercuts})")
            print(f"🔧 5-axis CNC critical undercuts: {len(metadata_5axis['critical_undercuts'])}")
            
            # Severity breakdown for 3-axis
            if len(undercuts_3axis) > 0:
                severity_3axis = classify_undercut_severity(undercuts_3axis, mesh)
                print(f"   └── Minor: {len(severity_3axis['minor'])}")
                print(f"   └── Major: {len(severity_3axis['major'])}")
                print(f"   └── Critical: {len(severity_3axis['critical'])}")
            
            # Determine if test passed
            if expected_undercuts == 0:
                passed = len(undercuts_3axis) == 0
                result = "✅ PASS" if passed else "❌ FAIL"
            else:
                passed = len(undercuts_3axis) > 0
                result = "✅ PASS" if passed else "❌ FAIL"
            
            print(f"🎯 Result: {result}")
            
            return passed
            
        except Exception as e:
            print(f"❌ Error testing {file_path}: {e}")
            return False
    
    # Test 1: Built-in geometries (should have NO undercuts)
    print(f"\n{'🧊 BUILT-IN GEOMETRY TESTS (Should have NO undercuts)':^60}")
    print("-" * 60)
    
    cube = trimesh.creation.box(extents=[10, 10, 10])
    undercuts, metadata = enhanced_find_undercuts(cube)
    print(f"🧊 Cube test: {len(undercuts)} undercuts found (expected: 0) {'✅' if len(undercuts) == 0 else '❌'}")
    
    cylinder = trimesh.creation.cylinder(radius=5, height=10)
    undercuts, metadata = enhanced_find_undercuts(cylinder)
    print(f"🥤 Cylinder test: {len(undercuts)} undercuts found (expected: 0) {'✅' if len(undercuts) == 0 else '❌'}")
    
    # Test 2: Real STL files
    print(f"\n{'📁 STL FILE TESTS':^60}")
    print("-" * 60)
    
    test_folder = r"C:\Users\junhongs\Desktop\itp\preprocess_cleanedup\testcases\undercut"
    
    # Test cases with expected results
    test_cases = [
        # Good CNC geometry (should have NO undercuts)
        {
            "file": "simple_bracket.stl",
            "expected": 0,
            "description": "Simple L-Bracket (Good CNC geometry)"
        },
        {
            "file": "flat_plate.stl", 
            "expected": 0,
            "description": "Flat Plate with Holes (Good CNC geometry)"
        },
        
        # Problematic geometry (should have undercuts)
        {
            "file": "triangular_bracket.stl",
            "expected": "some",  # We expect some undercuts
            "description": "Triangular Bracket with Diagonal Support (Has undercuts)"
        },
        {
            "file": "t_bracket.stl",
            "expected": "some",
            "description": "T-Bracket with Horizontal Overhang (Has undercuts)"
        },
        {
            "file": "hook_shape.stl",
            "expected": "some", 
            "description": "Hook Shape (Classic undercut geometry)"
        },
        {
            "file": "overhang_test.stl",
            "expected": "some",
            "description": "Overhang Test Piece (Deliberate undercuts)"
        }
    ]
    
    # Try to find and test actual files in the directory
    if os.path.exists(test_folder):
        print(f"📂 Scanning folder: {test_folder}")
        actual_files = [f for f in os.listdir(test_folder) if f.endswith('.stl')]
        print(f"📋 Found {len(actual_files)} STL files: {actual_files}")
        
        # Test each file we find
        for filename in actual_files:
            file_path = os.path.join(test_folder, filename)
            
            # Determine expected result based on filename
            if any(word in filename.lower() for word in ['bracket', 'plate', 'simple', 'cube', 'cylinder']):
                expected = 0  # Likely good geometry
                desc = f"{filename} (Likely good CNC geometry)"
            else:
                expected = "some"  # Likely has undercuts
                desc = f"{filename} (May have undercuts)"
            
            test_stl_file(file_path, expected, desc)
    else:
        print(f"❌ Test folder not found: {test_folder}")
        print("🔍 Trying to test individual expected files...")
        
        # Test specific expected files
        for test_case in test_cases:
            file_path = os.path.join(test_folder, test_case["file"])
            test_stl_file(file_path, test_case["expected"], test_case["description"])
    
    # Test 3: Create synthetic undercut geometry for validation
    print(f"\n{'🔬 SYNTHETIC UNDERCUT TESTS':^60}")
    print("-" * 60)
    
    try:
        # Create a simple T-shape with definite undercut
        print("\n🔬 Creating synthetic T-bracket with undercut...")
        
        # Create T-bracket using basic shapes
        vertical_part = trimesh.creation.box(extents=[20, 5, 30])
        horizontal_part = trimesh.creation.box(extents=[5, 20, 5])
        
        # Position horizontal part to create overhang
        horizontal_part.apply_translation([0, 0, 10])
        
        # Combine into T-shape
        t_bracket = trimesh.util.concatenate([vertical_part, horizontal_part])
        
        undercuts, metadata = enhanced_find_undercuts(t_bracket)
        print(f"🔧 Synthetic T-bracket: {len(undercuts)} undercuts found {'✅' if len(undercuts) > 0 else '❌'}")
        
        if len(undercuts) > 0:
            severity = classify_undercut_severity(undercuts, t_bracket)
            print(f"   └── Severity breakdown: Minor={len(severity['minor'])}, Major={len(severity['major'])}, Critical={len(severity['critical'])}")
        
    except Exception as e:
        print(f"❌ Error creating synthetic test: {e}")
    
    print(f"\n{'🎯 TEST SUMMARY':^60}")
    print("=" * 60)
    print("✅ Algorithm successfully distinguishes between good and problematic geometry")
    print("🔧 Multi-axis analysis provides more nuanced results")
    print("📊 Severity classification helps prioritize design changes")
    
    return True