import numpy as np
import trimesh

def find_steep_walls(mesh, angle_threshold=80.0):
    """
    Find steep walls (near-vertical surfaces).
    
    Args:
        mesh: trimesh object
        angle_threshold: angle from horizontal in degrees
        
    Returns:
        array: indices of steep faces
    """
    face_normals = mesh.face_normals
    
    # Convert angle threshold to radians and calculate z-component threshold
    angle_rad = np.radians(angle_threshold)
    z_threshold = np.sin(np.pi/2 - angle_rad)
    
    # Find faces where the normal's z-component is small (near-vertical)
    steep_mask = np.abs(face_normals[:, 2]) < z_threshold
    steep_indices = np.where(steep_mask)[0]
    
    return steep_indices

def realistic_steep_walls(mesh, angle_threshold=80.0, min_depth=5.0):
    """
    Reality check: Only flag steep walls that are ACTUALLY problematic.
    External walls are GOOD for CNC.
    """
    face_normals = mesh.face_normals
    face_centers = mesh.triangles_center
    
    # Find steep faces
    angle_rad = np.radians(angle_threshold)
    z_threshold = np.sin(np.pi/2 - angle_rad)
    steep_mask = np.abs(face_normals[:, 2]) < z_threshold
    
    # Only flag if they're deep inside the part
    bounds = mesh.bounds
    depth_from_top = bounds[1, 2] - face_centers[:, 2]
    deep_mask = depth_from_top > min_depth
    
    # AND not near external boundaries
    tolerance = 2.0  # mm from boundary
    near_boundary = (
        (np.abs(face_centers[:, 0] - bounds[0, 0]) < tolerance) |
        (np.abs(face_centers[:, 0] - bounds[1, 0]) < tolerance) |
        (np.abs(face_centers[:, 1] - bounds[0, 1]) < tolerance) |
        (np.abs(face_centers[:, 1] - bounds[1, 1]) < tolerance)
    )
    
    # Only problematic if steep AND deep AND not external
    problematic_mask = steep_mask & deep_mask & (~near_boundary)
    problematic_indices = np.where(problematic_mask)[0]
    
    result = {
        'total_steep': np.sum(steep_mask),
        'deep_steep': np.sum(steep_mask & deep_mask),
        'external_steep': np.sum(steep_mask & near_boundary),
        'problematic_steep': len(problematic_indices),
        'min_depth': min_depth
    }
    
    return problematic_indices, result

def context_aware_steep_walls(mesh, angle_threshold=80.0):
    """Find steep walls that are ACTUALLY problematic with context."""
    from geometric_context import analyze_face_context
    
    face_normals = mesh.face_normals
    
    angle_rad = np.radians(angle_threshold)
    z_threshold = np.sin(np.pi/2 - angle_rad)
    steep_faces = np.where(np.abs(face_normals[:, 2]) < z_threshold)[0]
    
    problematic_steep = []
    
    for face_idx in steep_faces:
        context = analyze_face_context(face_idx, mesh)
        
        if context['is_deep'] and not context['has_tool_access']:
            problematic_steep.append(face_idx)
    
    return np.array(problematic_steep)

def analyze_steep_walls(mesh, angle_threshold=80.0, min_depth=5.0, use_context=True):
    """
    Analyze steep walls with metadata.
    
    Args:
        mesh: trimesh object
        angle_threshold: angle from horizontal in degrees
        min_depth: minimum depth to consider problematic
        use_context: whether to use context-aware analysis
        
    Returns:
        dict: analysis results with metadata
    """
    if use_context:
        try:
            steep_indices = context_aware_steep_walls(mesh, angle_threshold)
            analysis_type = "context-aware"
            data = {'problematic_steep': len(steep_indices)}
        except ImportError:
            # Fallback to realistic if context module not available
            steep_indices, data = realistic_steep_walls(mesh, angle_threshold, min_depth)
            analysis_type = "realistic"
    else:
        steep_indices = find_steep_walls(mesh, angle_threshold)
        analysis_type = "basic"
        data = {'total_steep': len(steep_indices)}
    
    return {
        'count': len(steep_indices),
        'indices': steep_indices,
        'data': data,
        'analysis_type': analysis_type,
        'angle_threshold': angle_threshold,
        'has_problem': len(steep_indices) > 0,
        'severity': 'high' if len(steep_indices) > 50 else 'medium' if len(steep_indices) > 20 else 'low'
    }