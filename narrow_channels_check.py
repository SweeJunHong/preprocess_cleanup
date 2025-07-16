import numpy as np
import trimesh
from scipy.spatial import KDTree

# def find_narrow_channels(mesh, min_channel_width=2.0):
#     """
#     Find narrow channels based on face area.
    
#     Args:
#         mesh: trimesh object
#         min_channel_width: minimum channel width in mm
        
#     Returns:
#         array: indices of faces in narrow channels
#     """
#     face_areas = mesh.area_faces
    
#     # Estimate channel width from face area (assuming roughly square faces)
#     estimated_widths = np.sqrt(face_areas)
    
#     # Find faces that are too narrow
#     narrow_mask = estimated_widths < min_channel_width
#     narrow_indices = np.where(narrow_mask)[0]
    
#     return narrow_indices

# def realistic_narrow_channels(mesh, min_channel_width=2.0):
#     """
#     Reality check: Only flag ACTUAL narrow channels, not small mesh faces.
#     """
#     result = {
#         'min_channel_width': min_channel_width,
#         'total_faces': 0,
#         'actual_narrow_channels': 0,
#         'error': None
#     }
    
#     try:
#         face_areas = mesh.area_faces
        
#         # Ignore tiny faces (mesh artifacts)
#         significant_faces = face_areas[face_areas > 1.0]  # > 1 sq mm
        
#         if len(significant_faces) == 0:
#             return np.array([]), result
        
#         # Estimate channel width only for significant faces
#         estimated_widths = np.sqrt(significant_faces)
#         narrow_significant = estimated_widths < min_channel_width
        
#         # Only flag if there are CLUSTERS of narrow faces (actual channels)
#         narrow_count = np.sum(narrow_significant)
#         narrow_pct = (narrow_count / len(significant_faces)) * 100
        
#         result.update({
#             'total_faces': len(face_areas),
#             'significant_faces': len(significant_faces),
#             'narrow_significant_pct': narrow_pct
#         })
        
#         # Only flag if there are many clustered narrow faces
#         if narrow_pct > 15:  # 15% of significant faces are narrow
#             narrow_indices = np.where(face_areas > 1.0)[0]  # Return actual indices
#             narrow_indices = narrow_indices[narrow_significant]
#             result['actual_narrow_channels'] = len(narrow_indices)
#             return narrow_indices, result
#         else:
#             result['actual_narrow_channels'] = 0
#             return np.array([]), result
            
#     except Exception as e:
#         result['error'] = str(e)
#         return np.array([]), result

# def context_aware_narrow_channels(mesh, min_channel_width=2.0):
#     """Find ACTUAL narrow channels, not just small external faces."""
#     from geometric_context import analyze_face_context
    
#     face_areas = mesh.area_faces
#     estimated_widths = np.sqrt(face_areas)
#     potentially_narrow = np.where(estimated_widths < min_channel_width)[0]
    
#     actual_narrow_channels = []
    
#     for face_idx in potentially_narrow:
#         context = analyze_face_context(face_idx, mesh)
        
#         if context['is_deep'] and not context['has_tool_access'] and not context['is_external']:
#             actual_narrow_channels.append(face_idx)
    
#     return np.array(actual_narrow_channels)

# def analyze_narrow_channels(mesh, min_channel_width=2.0, use_context=True):
#     """
#     Analyze narrow channels with metadata.
    
#     Args:
#         mesh: trimesh object
#         min_channel_width: minimum channel width in mm
#         use_context: whether to use context-aware analysis
        
#     Returns:
#         dict: analysis results with metadata
#     """
#     if use_context:
#         try:
#             narrow_indices = context_aware_narrow_channels(mesh, min_channel_width)
#             analysis_type = "context-aware"
#             data = {'actual_narrow_channels': len(narrow_indices)}
#         except ImportError:
#             # Fallback to realistic if context module not available
#             narrow_indices, data = realistic_narrow_channels(mesh, min_channel_width)
#             analysis_type = "realistic"
#     else:
#         narrow_indices = find_narrow_channels(mesh, min_channel_width)
#         analysis_type = "basic"
#         data = {'total_narrow': len(narrow_indices)}
    
#     return {
#         'count': len(narrow_indices),
#         'indices': narrow_indices,
#         'data': data,
#         'analysis_type': analysis_type,
#         'min_channel_width': min_channel_width,
#         'has_problem': len(narrow_indices) > 0,
#         'severity': 'high' if len(narrow_indices) > 100 else 'medium' if len(narrow_indices) > 50 else 'low'
#     }


from scipy.spatial import KDTree

def detect_narrow_channels(mesh, min_width=5.0):
    tree = KDTree(mesh.triangles_center)
    narrow_faces = []
    for i, center in enumerate(mesh.triangles_center):
        dists, idxs = tree.query(center, k=10)
        min_dist = np.min(dists[2:]) if len(dists) > 2 else np.inf
        # Optionally, check if face is internal (not on boundary)
        if min_dist < min_width:
            narrow_faces.append(i)
    return {
        "count": len(narrow_faces),
        "indices": np.array(narrow_faces),
        "severity": 'high' if len(narrow_faces) > 100 else 'medium' if len(narrow_faces) > 50 else 'low',
        "has_problem": len(narrow_faces) > 0,
        "recommendation": "Widen channels to improve tool access and chip evacuation." if len(narrow_faces) > 0 else "No problematic narrow channels."
    }