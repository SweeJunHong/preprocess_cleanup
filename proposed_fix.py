import sys
sys.path.append('preprocess')

import trimesh
import numpy as np

def improved_has_clear_tool_access(face_center, face_normal, mesh, tool_diameter=3.0):
    """
    Improved tool access check that properly detects dovetail undercuts.
    
    The key insight is that for a dovetail undercut, the face normal points
    inward (negative direction) but there's no clear path for a tool to reach
    the surface from that direction due to the geometry.
    """
    # Standard CNC machining directions (top-down and 4 horizontal sides)
    machining_directions = [
        np.array([0, 0, -1]),  # Top-down (most common)
        np.array([1, 0, 0]),   # +X direction
        np.array([-1, 0, 0]),  # -X direction  
        np.array([0, 1, 0]),   # +Y direction
        np.array([0, -1, 0]),  # -Y direction
    ]
    
    tool_radius = tool_diameter / 2.0
    accessible_directions = 0
    
    for direction in machining_directions:
        # Check if the face normal is roughly aligned with the tool approach direction
        # If the face normal points away from the tool direction, it's potentially accessible
        alignment = np.dot(face_normal, direction)
        
        # If face normal points in the same direction as tool approach, it's not accessible
        if alignment > 0.3:  # Face points away from tool
            continue
            
        # Cast ray from far away towards the face
        ray_start = face_center - direction * 100.0  # Start far away
        ray_end = face_center + direction * 0.1      # End just past the face
        
        try:
            # Check if ray hits any geometry before reaching the target face
            locations, ray_indices, face_indices = mesh.ray.intersects_location(
                ray_origins=ray_start.reshape(1, -1),
                ray_directions=direction.reshape(1, -1)
            )
            
            if len(locations) == 0:
                # No intersections - clear path
                accessible_directions += 1
                continue
            
            # Check if first intersection is close to our target face
            distances = np.linalg.norm(locations - ray_start, axis=1)
            target_distance = np.linalg.norm(face_center - ray_start)
            
            if len(distances) > 0:
                first_hit_distance = np.min(distances)
                
                # If first hit is much closer than target, there's an obstruction
                if first_hit_distance < target_distance - tool_radius:
                    continue  # Obstructed
                else:
                    accessible_directions += 1
                    
        except Exception:
            # If ray casting fails, assume accessible (conservative)
            accessible_directions += 1
    
    return accessible_directions > 0

def improved_context_aware_undercuts(mesh):
    """
    Improved undercut detection that properly identifies dovetail undercuts.
    """
    face_normals = mesh.face_normals
    face_centers = mesh.triangles_center
    mesh_bounds = mesh.bounds
    
    undercut_faces = []
    
    # Focus on faces that could be problematic undercuts
    for i, (center, normal) in enumerate(zip(face_centers, face_normals)):
        # Check if face points inward (key characteristic of undercuts)
        mesh_center = np.mean(face_centers, axis=0)
        to_face = center - mesh_center
        to_face_norm = to_face / (np.linalg.norm(to_face) + 1e-8)
        
        # Face points inward relative to its position
        alignment = np.dot(normal, to_face_norm)
        
        if alignment < -0.1:  # Face points inward
            # Check if it's not on the external boundary
            is_external = False
            tolerance = 2.0
            for axis in range(3):
                for bound_idx in [0, 1]:
                    distance_to_boundary = abs(center[axis] - mesh_bounds[bound_idx, axis])
                    if distance_to_boundary < tolerance:
                        is_external = True
                        break
                if is_external:
                    break
            
            if not is_external:
                # Check tool access with improved method
                has_access = improved_has_clear_tool_access(center, normal, mesh)
                
                if not has_access:
                    undercut_faces.append(i)
    
    return np.array(undercut_faces)

# Test the improved detection
if __name__ == "__main__":
    mesh_path = "testcases/undercut/dovetail_joint_red.stl"
    mesh = trimesh.load(mesh_path)
    
    print("Testing improved undercut detection...")
    
    # Test improved detection
    improved_undercuts = improved_context_aware_undercuts(mesh)
    print(f"Improved detection found {len(improved_undercuts)} undercut faces")
    
    # Compare with a few sample faces
    if len(improved_undercuts) > 0:
        print("\nSample detected undercuts:")
        for i, face_idx in enumerate(improved_undercuts[:5]):
            face_center = mesh.triangles_center[face_idx]
            face_normal = mesh.face_normals[face_idx]
            print(f"Face {face_idx}: center={face_center}, normal={face_normal}")
    
    # Test the improved tool access function on known dovetail faces
    print(f"\nTesting improved tool access on known dovetail faces...")
    
    # Face 362 was identified as a dovetail candidate
    face_idx = 362
    face_center = mesh.triangles_center[face_idx]
    face_normal = mesh.face_normals[face_idx]
    
    from geometric_context import has_clear_tool_access
    original_access = has_clear_tool_access(face_center, face_normal, mesh)
    improved_access = improved_has_clear_tool_access(face_center, face_normal, mesh)
    
    print(f"Face {face_idx} (dovetail candidate):")
    print(f"  Center: {face_center}")
    print(f"  Normal: {face_normal}")
    print(f"  Original tool access: {original_access}")
    print(f"  Improved tool access: {improved_access}")