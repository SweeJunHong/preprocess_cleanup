import trimesh
import numpy as np

def repair_mesh(mesh):
    """
    Repair mesh to ensure it's watertight and suitable for analysis
    Returns repaired mesh and repair status message
    """
    repair_log = []
    
    # Handle different mesh types first
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))
        repair_log.append("converted scene to single mesh")
    elif isinstance(mesh, list):
        if len(mesh) > 0:
            mesh = mesh[0]  # take first mesh from list
            repair_log.append("extracted first mesh from list")
        else:
            raise ValueError("empty mesh list")
    
    # Ensure we have a valid trimesh object
    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError(f"expected trimesh.Trimesh, got {type(mesh)}")
    
    # Basic repair operations
    if not mesh.is_watertight:
        repair_log.append("original mesh is not watertight")
        
        # Remove duplicate vertices (correct method)
        mesh.remove_duplicate_faces()
        repair_log.append("removed duplicate faces")
        
        # Remove unreferenced vertices
        mesh.remove_unreferenced_vertices()
        repair_log.append("removed unreferenced vertices")
        
        # Process mesh (this does merge vertices and other cleanup)
        mesh.process(validate=True)
        repair_log.append("processed mesh (cleanup)")
        
        # Check if watertight now
        if not mesh.is_watertight:
            repair_log.append("warning: mesh could not be made fully watertight")
    else:
        repair_log.append("mesh was already watertight")
    
    return mesh, repair_log