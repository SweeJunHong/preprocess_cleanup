import numpy as np
import trimesh

def estimate_pocket_depth(mesh, center, normal):
    """Estimate the depth of pockets at a specific face using ray casting."""
    try:
        # Cast ray outward from face
        locations, _, _ = mesh.ray.intersects_location(
            ray_origins=center.reshape(1, -1),
            ray_directions=normal.reshape(1, -1)
        )

        if len(locations) > 0:
            depths = np.linalg.norm(locations - center, axis=1)
            valid_depths = depths[depths > 0.1]  # Ignore very close hits
            
            return np.min(valid_depths) if len(valid_depths) > 0 else 0

        return 0
    except:
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
    

def detect_deep_pockets(mesh, tool_direction=None, threshold=25.0):
    # If tool_direction is None, check all principal axes
    directions = [np.array([1,0,0]), np.array([0,1,0]), np.array([0,0,1])] if tool_direction is None else [tool_direction]
    max_depth = 0
    for direction in directions:
        # Project all vertices onto the direction
        projections = mesh.vertices @ direction
        depth = projections.max() - projections.min()
        max_depth = max(max_depth, depth)
    has_problem = max_depth > threshold
    return {
        "count": int(has_problem),
        "severity": 2 if max_depth > 2*threshold else 1 if has_problem else 0,
        "has_problem": has_problem,
        "recommendation": f"Deep pocket detected ({max_depth:.1f}mm). Consider reducing depth or using longer tools."
    }