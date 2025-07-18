import numpy as np
import trimesh

def is_surface_external(face_center, face_normal, mesh_bounds, tolerance=2.0):
    """Check if a face is on the external boundary (good for CNC)."""
    for axis in range(3):
        for bound_idx in [0, 1]:
            distance_to_boundary = abs(face_center[axis] - mesh_bounds[bound_idx, axis])
            if distance_to_boundary < tolerance:
                return True
    return False
''' tool diameter ranging from 1mm to 25mm'''
def has_clear_tool_access(face_center, face_normal, mesh, tool_diameter=3.0):
    """Check if a standard CNC tool can access this face."""
    try:
        test_directions = [
            np.array([0, 0, -1]), np.array([0, 0, 1]),
            np.array([1, 0, 0]), np.array([-1, 0, 0]),
            np.array([0, 1, 0]), np.array([0, -1, 0])
        ]
        
        accessible_directions = 0
        tool_radius = tool_diameter / 2.0
        
        for direction in test_directions:
            ray_start = face_center - direction * 50.0
            
            locations, ray_indices, face_indices = mesh.ray.intersects_location(
                ray_origins=ray_start.reshape(1, -1),
                ray_directions=direction.reshape(1, -1)
            )
            
            if len(locations) == 0:
                accessible_directions += 1
                continue
            
            distances = np.linalg.norm(locations - ray_start, axis=1)
            target_distance = np.linalg.norm(face_center - ray_start)
            
            if len(distances) > 0:
                first_hit_distance = np.min(distances)
                if abs(first_hit_distance - target_distance) < tool_radius:
                    accessible_directions += 1
        
        return accessible_directions > 0
        
    except Exception:
        return True

def is_face_in_deep_pocket(face_center, mesh_bounds, min_depth=10.0):
    """Check if face is deep inside the part."""
    depths = []
    for axis in range(3):
        depth_from_min = face_center[axis] - mesh_bounds[0, axis]
        depth_from_max = mesh_bounds[1, axis] - face_center[axis]
        min_depth_this_axis = min(depth_from_min, depth_from_max)
        depths.append(min_depth_this_axis)
    
    return min(depths) > min_depth

def analyze_face_context(face_idx, mesh):
    """Analyze the geometric context of a face."""
    face_center = mesh.triangles_center[face_idx]
    face_normal = mesh.face_normals[face_idx]
    face_area = mesh.area_faces[face_idx]
    mesh_bounds = mesh.bounds
    
    context = {
        'is_external': is_surface_external(face_center, face_normal, mesh_bounds),
        'has_tool_access': has_clear_tool_access(face_center, face_normal, mesh),
        'is_deep': is_face_in_deep_pocket(face_center, mesh_bounds),
        'face_area': face_area,
    }
    
    return context

