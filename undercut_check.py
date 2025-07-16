import numpy as np
import trimesh
from geometric_context import is_tool_accessible
def find_undercuts(mesh):
    """Find undercut faces in mesh - surfaces that face upward and inward."""
    face_normals = mesh.face_normals
    face_centers = mesh.triangles_center
    mesh_center = np.mean(face_centers, axis=0)
    undercut_faces = []
    
    for i, (center, normal) in enumerate(zip(face_centers, face_normals)):
        # Look for faces that point upward (positive Z)
        if normal[2] > 0.3:  # Face points somewhat upward
            # Check if this face is "hidden" inside the mesh
            # by comparing face direction with direction from mesh center
            to_face = center - mesh_center
            to_face_norm = to_face / (np.linalg.norm(to_face) + 1e-8)
            
            # If face normal and position vector point in opposite directions,
            # this suggests an internal/undercut surface
            alignment = np.dot(normal, to_face_norm)
            
            if alignment < -0.2:  # Face points inward relative to its position
                undercut_faces.append(i)
    
    undercut_indices = np.array(undercut_faces)
    return undercut_indices

def context_aware_undercuts(mesh):
    """Find undercuts that are ACTUALLY problematic with context awareness."""
    from geometric_context import analyze_face_context
    
    face_normals = mesh.face_normals
    upward_faces = np.where(face_normals[:, 2] > 0.3)[0]
    
    actual_undercuts = []
    
    for face_idx in upward_faces:
        context = analyze_face_context(face_idx, mesh)
        
        if not context['has_tool_access'] and not context['is_external']:
            actual_undercuts.append(face_idx)
    
    return np.array(actual_undercuts)

def analyze_undercuts(mesh, use_context=True):
    """
    Analyze undercuts with metadata.
    
    Args:
        mesh: trimesh object
        use_context: whether to use context-aware analysis
        
    Returns:
        dict: analysis results with metadata
    """
    if use_context:
        undercut_indices = context_aware_undercuts(mesh)
        analysis_type = "context-aware"
    else:
        undercut_indices = find_undercuts(mesh)
        analysis_type = "basic"
    
    return {
        'count': len(undercut_indices),
        'indices': undercut_indices,
        'percentage': (len(undercut_indices) / len(mesh.faces)) * 100,
        'analysis_type': analysis_type,
        'severity': 'high' if len(undercut_indices) > 100 else 'medium' if len(undercut_indices) > 50 else 'low'
    }
    
def detect_undercuts(mesh, tool_direction=np.array([0, 0, 1]), min_angle=100):
    undercut_faces = []
    for i, normal in enumerate(mesh.face_normals):
        angle = np.degrees(np.arccos(np.clip(np.dot(normal, tool_direction), -1.0, 1.0)))
        if angle > min_angle:
            # Check if tool can actually reach this face
            if not is_tool_accessible(mesh, i, tool_direction):
                undercut_faces.append(i)
    return {
        "count": len(undercut_faces),
        "severity": min(len(undercut_faces) // 10, 2),
        "has_problem": len(undercut_faces) > 0,
        "recommendation": "Redesign to eliminate undercuts or ensure tool access."
    }