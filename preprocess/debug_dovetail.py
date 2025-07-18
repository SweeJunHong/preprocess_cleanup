import sys
sys.path.append('preprocess')

import trimesh
import numpy as np
from undercut_check import find_undercuts
from geometric_context import analyze_face_context

# Load the dovetail joint STL
mesh_path = "testcases/undercut/dovetail_joint_red.stl"
mesh = trimesh.load(mesh_path)

print(f"Debugging dovetail joint undercut detection...")
print(f"Mesh bounds: {mesh.bounds}")

# Get basic undercuts first
basic_undercuts = find_undercuts(mesh)
print(f"Basic detection found {len(basic_undercuts)} undercut faces")

# Sample some of the basic undercut faces and analyze their context
sample_indices = basic_undercuts[:10] if len(basic_undercuts) > 10 else basic_undercuts

print(f"\nAnalyzing context for sample undercut faces:")
for i, face_idx in enumerate(sample_indices):
    face_center = mesh.triangles_center[face_idx]
    face_normal = mesh.face_normals[face_idx]
    
    try:
        context = analyze_face_context(face_idx, mesh)
        print(f"\nFace {face_idx}:")
        print(f"  Center: {face_center}")
        print(f"  Normal: {face_normal}")
        print(f"  Is external: {context['is_external']}")
        print(f"  Has tool access: {context['has_tool_access']}")
        print(f"  Is deep: {context['is_deep']}")
        print(f"  Face area: {context['face_area']:.6f}")
        
        # This is the condition used in context_aware_undercuts
        is_undercut = not context['has_tool_access'] and not context['is_external']
        print(f"  Would be flagged as undercut: {is_undercut}")
        
    except Exception as e:
        print(f"  Error analyzing face {face_idx}: {e}")

# Let's also check some faces that should be dovetail undercuts
# Look for faces with specific characteristics
face_normals = mesh.face_normals
face_centers = mesh.triangles_center

print(f"\nLooking for dovetail characteristics...")
print(f"Total faces: {len(mesh.faces)}")

# Look for faces that point inward and are not on the boundary
inward_faces = []
for i, (center, normal) in enumerate(zip(face_centers, face_normals)):
    # Check if face is in the middle region where dovetail undercuts would be
    if -10 < center[0] < 30 and -15 < center[1] < -5 and 0.5 < center[2] < 3.5:
        # Check if normal points inward (negative X direction for dovetail)
        if normal[0] < -0.5:  # Points toward negative X
            inward_faces.append(i)

print(f"Found {len(inward_faces)} faces that might be dovetail undercuts")

# Analyze a few of these
for i, face_idx in enumerate(inward_faces[:5]):
    face_center = mesh.triangles_center[face_idx]
    face_normal = mesh.face_normals[face_idx]
    
    try:
        context = analyze_face_context(face_idx, mesh)
        print(f"\nPotential dovetail face {face_idx}:")
        print(f"  Center: {face_center}")
        print(f"  Normal: {face_normal}")
        print(f"  Is external: {context['is_external']}")
        print(f"  Has tool access: {context['has_tool_access']}")
        print(f"  Is deep: {context['is_deep']}")
        
    except Exception as e:
        print(f"  Error analyzing face {face_idx}: {e}")