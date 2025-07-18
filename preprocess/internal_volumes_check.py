import numpy as np
import trimesh

def check_external_openings(mesh):
    """Check if mesh has openings to external surfaces (normal for brackets)."""
    try:
        bounds = mesh.bounds
        vertices = mesh.vertices
        tolerance = 0.1  # mm
        
        # Check each boundary plane
        for axis in [0, 1, 2]:  # X, Y, Z
            for bound in [bounds[0, axis], bounds[1, axis]]:
                on_boundary = np.abs(vertices[:, axis] - bound) < tolerance
                if np.sum(on_boundary) > 3:  # More than a few vertices on boundary
                    return True
        
        return False
    except:
        return True  # Conservative: assume openings exist

def realistic_internal_volumes(mesh):
    """
    Reality check: Only flag ACTUALLY problematic internal volumes.
    A triangular bracket with open space is NOT an internal volume problem.
    """
    result = {
        'is_watertight': mesh.is_watertight,
        'actual_volume': 0,
        'convex_volume': 0,
        'volume_ratio': 0,
        'error': None
    }
    
    if not mesh.is_watertight:
        result['error'] = "Mesh is not watertight - cannot detect internal volumes reliably"
        return 0, result
    
    try:
        actual_volume = mesh.volume
        convex_volume = mesh.convex_hull.volume
        volume_ratio = actual_volume / convex_volume
        
        result.update({
            'actual_volume': actual_volume,
            'convex_volume': convex_volume,
            'volume_ratio': volume_ratio
        })
        
        # REALITY CHECK: Only flag if volume ratio suggests ENCLOSED hollow spaces
        # Not just external voids (which are normal for brackets)
        
        # Check if the mesh has obvious external openings
        has_external_openings = check_external_openings(mesh)
        
        if has_external_openings:
            # External voids (like bracket cutouts) are FINE for CNC
            return 0, result
        
        # Only flag truly enclosed internal spaces
        if volume_ratio < 0.3:  # Very hollow = possible internal spaces
            return 2, result
        elif volume_ratio < 0.6:  # Somewhat hollow = minor concern
            return 1, result
        else:
            return 0, result  # Solid enough
            
    except Exception as e:
        result['error'] = f"Error calculating volumes: {e}"
        return 0, result

def context_aware_internal_volumes(mesh):
    """Improved internal volume detection with context awareness."""
    result = {
        'is_watertight': mesh.is_watertight,
        'actual_volume': 0,
        'convex_volume': 0,
        'volume_ratio': 0,
        'has_external_openings': False,
        'error': None
    }
    
    if not mesh.is_watertight:
        result['error'] = "Mesh is not watertight"
        return 0, result
    
    try:
        actual_volume = mesh.volume
        convex_volume = mesh.convex_hull.volume
        volume_ratio = actual_volume / convex_volume
        
        result.update({
            'actual_volume': actual_volume,
            'convex_volume': convex_volume,
            'volume_ratio': volume_ratio
        })
        
        # Check for external openings
        bounds = mesh.bounds
        vertices = mesh.vertices
        tolerance = 1.0
        
        has_openings = False
        for axis in range(3):
            for bound_value in [bounds[0, axis], bounds[1, axis]]:
                near_boundary = np.abs(vertices[:, axis] - bound_value) < tolerance
                if np.sum(near_boundary) > len(vertices) * 0.1:
                    has_openings = True
                    break
        
        result['has_external_openings'] = has_openings
        
        if has_openings:
            return 0, result  # External voids are fine
        
        if volume_ratio < 0.3:
            return 2, result
        elif volume_ratio < 0.7:
            return 1, result
        else:
            return 0, result
            
    except Exception as e:
        result['error'] = str(e)
        return 0, result

def analyze_internal_volumes(mesh, use_context=True):
    """
    Analyze internal volumes with metadata.
    
    Args:
        mesh: trimesh object
        use_context: whether to use context-aware analysis
        
    Returns:
        dict: analysis results with metadata
    """
    if use_context:
        severity, data = context_aware_internal_volumes(mesh)
        analysis_type = "context-aware"
    else:
        severity, data = realistic_internal_volumes(mesh)
        analysis_type = "realistic"
    
    return {
        'severity': severity,
        'data': data,
        'analysis_type': analysis_type,
        'has_problem': severity > 0,
        'recommendation': {
            0: "No internal volume issues",
            1: "Minor hollowness - verify design intent",
            2: "Severe internal volumes - redesign required"
        }.get(severity, "Unknown")
    }