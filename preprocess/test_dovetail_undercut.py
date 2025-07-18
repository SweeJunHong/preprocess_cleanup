import sys
sys.path.append('preprocess')

import trimesh
import numpy as np
from undercut_check import find_undercuts, context_aware_undercuts, analyze_undercuts

# Load the dovetail joint STL
mesh_path = "testcases/undercut/dovetail_joint_red.stl"
mesh = trimesh.load(mesh_path)

print(f"Loaded mesh: {mesh}")
print(f"Number of faces: {len(mesh.faces)}")
print(f"Mesh bounds: {mesh.bounds}")

# Test basic undercut detection
basic_undercuts = find_undercuts(mesh)
print(f"\nBasic undercut detection:")
print(f"Number of undercut faces: {len(basic_undercuts)}")
print(f"Undercut indices: {basic_undercuts}")

# Test context-aware undercut detection
try:
    context_undercuts = context_aware_undercuts(mesh)
    print(f"\nContext-aware undercut detection:")
    print(f"Number of undercut faces: {len(context_undercuts)}")
    print(f"Undercut indices: {context_undercuts}")
except Exception as e:
    print(f"Error in context-aware detection: {e}")

# Test full analysis
try:
    analysis_basic = analyze_undercuts(mesh, use_context=False)
    print(f"\nBasic analysis results:")
    print(f"Count: {analysis_basic['count']}")
    print(f"Percentage: {analysis_basic['percentage']:.2f}%")
    print(f"Severity: {analysis_basic['severity']}")
    
    analysis_context = analyze_undercuts(mesh, use_context=True)
    print(f"\nContext-aware analysis results:")
    print(f"Count: {analysis_context['count']}")
    print(f"Percentage: {analysis_context['percentage']:.2f}%")
    print(f"Severity: {analysis_context['severity']}")
except Exception as e:
    print(f"Error in full analysis: {e}")

# Analyze the mesh characteristics
face_normals = mesh.face_normals
upward_faces = np.where(face_normals[:, 2] > 0.3)[0]
print(f"\nMesh characteristics:")
print(f"Faces with upward normals (Z > 0.3): {len(upward_faces)}")

# Check face normal distribution
print(f"Face normal Z-component stats:")
print(f"Min: {np.min(face_normals[:, 2]):.3f}")
print(f"Max: {np.max(face_normals[:, 2]):.3f}")
print(f"Mean: {np.mean(face_normals[:, 2]):.3f}")