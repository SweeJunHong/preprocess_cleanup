import numpy as np
import trimesh

# def estimate_pocket_depth(mesh, center, normal):
#     """Estimate the depth of pockets at a specific face using ray casting."""
#     try:
#         # Cast ray outward from face
#         locations, _, _ = mesh.ray.intersects_location(
#             ray_origins=center.reshape(1, -1),
#             ray_directions=normal.reshape(1, -1)
#         )

#         if len(locations) > 0:
#             depths = np.linalg.norm(locations - center, axis=1)
#             valid_depths = depths[depths > 0.1]  # Ignore very close hits
            
#             return np.min(valid_depths) if len(valid_depths) > 0 else 0

#         return 0
#     except:
#         return 0

def estimate_pocket_depth(mesh, center, normal):
    """More robust depth estimation with error handling"""
    try:
        # Normalize the direction vector
        direction = normal / (np.linalg.norm(normal) + 1e-10)
        
        # Add small offset to avoid self-intersection
        ray_origin = center + direction * 0.01
        
        with np.errstate(invalid='ignore'):  # Suppress runtime warnings
            locations, _, _ = mesh.ray.intersects_location(
                ray_origins=[ray_origin],
                ray_directions=[direction],
                multiple_hits=False
            )
        
        if len(locations) > 0:
            depth = np.linalg.norm(locations[0] - center)
            return depth if depth > 0.1 else 0  # Ignore tiny depths
        
        return 0
    except Exception:
        return 0
    
def find_deep_pockets(mesh, depth_threshold=30.0, method='ray'):
    """
    Find faces in deep pockets that may cause machining issues.
    
    Args:
        mesh: trimesh object
        depth_threshold: minimum depth to consider problematic
        method: 'ray' for ray casting, 'normal' for normal analysis
    
    Returns:
        tuple: (face_indices, metadata)
    """
    face_centers = mesh.triangles_center
    face_normals = mesh.face_normals
    
    result = {
        'method': method,
        'depth_threshold': depth_threshold,
        'total_faces': len(face_centers),
        'deep_faces_count': 0,
        'max_depth': 0,
        'error': None
    }
    
    try:
        if method == 'ray':
            deep_faces = []
            max_depth = 0
            
            for i, (center, normal) in enumerate(zip(face_centers, face_normals)):
                depth = estimate_pocket_depth(mesh, center, normal)
                if depth > depth_threshold:
                    deep_faces.append(i)
                    max_depth = max(max_depth, depth)
            
            result['max_depth'] = max_depth
            
        elif method == 'normal':
            mesh_center = np.mean(mesh.verticesh.vertices, axis=0)
            
            # Vectorized approach for better performance
            to_faces = face_centers - mesh_center
            to_faces_norm = to_faces / (np.linalg.norm(to_faces, axis=1, keepdims=True) + 1e-8)
            
            # Calculate dot products for all faces at once
            alignments = np.sum(face_normals * (-to_faces_norm), axis=1)
            deep_faces = np.where(alignments > 0.3)[0].tolist()
            
        else:
            raise ValueError(f"Unknown method: {method}")
            
        result['deep_faces_count'] = len(deep_faces)
        return np.array(deep_faces), result
        
    except Exception as e:
        result['error'] = str(e)
        return np.array([]), result

def analyze_deep_pockets(mesh, depth_threshold=30.0, method='ray'):
    """
    Analyze deep pockets with metadata.
    
    Args:
        mesh: trimesh object
        depth_threshold: minimum depth to consider problematic
        method: 'ray' for ray casting, 'normal' for normal analysis
        
    Returns:
        dict: analysis results with metadata
    """
    deep_indices, data = find_deep_pockets(mesh, depth_threshold, method)
    
    return {
        'count': len(deep_indices),
        'indices': deep_indices,
        'data': data,
        'method': method,
        'depth_threshold': depth_threshold,
        'has_problem': len(deep_indices) > 0,
        'severity': 'high' if len(deep_indices) > 50 else 'medium' if len(deep_indices) > 20 else 'low',
        'max_depth': data.get('max_depth', 0)
    }
    
    