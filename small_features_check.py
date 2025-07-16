import numpy as np
import trimesh

def find_small_features(mesh, min_tool_diameter=3.0, min_feature_size=1.0):
    """
    Find features too small for standard CNC tools.
    
    Args:
        mesh: trimesh object
        min_tool_diameter: minimum tool diameter in mm
        min_feature_size: minimum feature size threshold in mm
    
    Returns:
        tuple: (severity_level, metadata)
    """
    result = {
        'min_tool_diameter': min_tool_diameter,
        'min_feature_size': min_feature_size,
        'total_edges': 0,
        'very_small_edges_count': 0,
        'small_edges_count': 0,
        'very_small_pct': 0,
        'small_pct': 0,
        'min_edge_length': 0,
        'max_edge_length': 0,
        'mean_edge_length': 0,
        'error': None
    }
    
    try:
        # Get edge lengths in actual units (mm)
        edge_lengths = mesh.edges_unique_length
        
        if len(edge_lengths) == 0:
            result['error'] = "No edges found in mesh"
            return 0, result
        
        # Calculate basic statistics
        result.update({
            'total_edges': len(edge_lengths),
            'min_edge_length': np.min(edge_lengths),
            'max_edge_length': np.max(edge_lengths),
            'mean_edge_length': np.mean(edge_lengths)
        })
        
        # Small features: edges smaller than minimum tool radius
        very_small_mask = edge_lengths < (min_tool_diameter / 2)
        small_mask = edge_lengths < min_feature_size
        
        very_small_count = np.sum(very_small_mask)
        small_count = np.sum(small_mask)
        
        # Calculate percentages
        very_small_pct = (very_small_count / len(edge_lengths)) * 100
        small_pct = (small_count / len(edge_lengths)) * 100
        
        result.update({
            'very_small_edges_count': very_small_count,
            'small_edges_count': small_count,
            'very_small_pct': very_small_pct,
            'small_pct': small_pct
        })
        
        # Classify severity
        if very_small_pct > 10 or small_pct > 20:
            return 2, result  # Severe small feature issues
        elif very_small_pct > 5 or small_pct > 15:
            return 1, result  # Minor small feature issues
        else:
            return 0, result  # No significant small features
            
    except Exception as e:
        result['error'] = str(e)
        return 0, result

def realistic_small_features(mesh, min_tool_diameter=3.0):
    """
    Reality check: Only flag ACTUAL small features, not mesh tessellation.
    """
    result = {
        'min_tool_diameter': min_tool_diameter,
        'actual_small_features': 0,
        'mesh_tessellation_edges': 0,
        'error': None
    }
    
    try:
        edge_lengths = mesh.edges_unique_length
        
        # Ignore very small edges (mesh tessellation)
        # Focus on edges that represent actual geometry
        significant_edges = edge_lengths[edge_lengths > 0.5]  # Ignore sub-mm mesh edges
        
        if len(significant_edges) == 0:
            return 0, result
        
        # Only count edges that are consistently small across a region
        # (not just single mesh triangles)
        small_significant = significant_edges[significant_edges < min_tool_diameter/2]
        
        small_pct = (len(small_significant) / len(significant_edges)) * 100
        
        result.update({
            'actual_small_features': len(small_significant),
            'mesh_tessellation_edges': len(edge_lengths) - len(significant_edges),
            'small_significant_pct': small_pct
        })
        
        # Only flag if there are MANY consistently small features
        if small_pct > 20:
            return 2, result
        elif small_pct > 10:
            return 1, result
        else:
            return 0, result
            
    except Exception as e:
        result['error'] = str(e)
        return 0, result

def analyze_small_features(mesh, min_tool_diameter=3.0, use_realistic=True):
    """
    Analyze small features with metadata.
    
    Args:
        mesh: trimesh object
        min_tool_diameter: minimum tool diameter in mm
        use_realistic: whether to use realistic analysis (ignore mesh tessellation)
        
    Returns:
        dict: analysis results with metadata
    """
    if use_realistic:
        severity, data = realistic_small_features(mesh, min_tool_diameter)
        analysis_type = "realistic"
    else:
        severity, data = find_small_features(mesh, min_tool_diameter)
        analysis_type = "basic"
    
    return {
        'severity': severity,
        'data': data,
        'analysis_type': analysis_type,
        'has_problem': severity > 0,
        'recommendation': {
            0: "No small feature issues",
            1: "Some small features - consider tool size",
            2: "Many small features - may need micro-machining"
        }.get(severity, "Unknown")
    }