
import numpy as np
import trimesh

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import os
from scipy.spatial.distance import cdist



def load_stl(file_path):
    try: 
        mesh = trimesh.load(file_path)
        return mesh
    except Exception as e:
        print(f"Error loading file: {e}")
        return None

# critical 
def find_undercuts(mesh):
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
    #print(f"Found {len(undercut_indices)} potential undercut faces")
    return undercut_indices



# serious
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
    
def check_external_openings(mesh):
    """Check if mesh has openings to external surfaces (normal for brackets)."""
    try:
        # Simple check: if mesh has vertices on the boundary planes,
        # it likely has external openings
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
           
#serious
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
            mesh_center = np.mean(mesh.vertices, axis=0)
            
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

#example usage:
# more accurate but slower
# deep_faces, metadata = find_deep_pockets(mesh, depth_threshold=30.0, method='ray')
# faster but less accurate
# deep_faces, metadata = find_deep_pockets(mesh, depth_threshold=30.0, method='normal')

#serious

#fair 
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


#fair

def realistic_narrow_channels(mesh, min_channel_width=2.0):
    """
    Reality check: Only flag ACTUAL narrow channels, not small mesh faces.
    """
    result = {
        'min_channel_width': min_channel_width,
        'total_faces': 0,
        'actual_narrow_channels': 0,
        'error': None
    }
    
    try:
        face_areas = mesh.area_faces
        
        # Ignore tiny faces (mesh artifacts)
        significant_faces = face_areas[face_areas > 1.0]  # > 1 sq mm
        
        if len(significant_faces) == 0:
            return np.array([]), result
        
        # Estimate channel width only for significant faces
        estimated_widths = np.sqrt(significant_faces)
        narrow_significant = estimated_widths < min_channel_width
        
        # Only flag if there are CLUSTERS of narrow faces (actual channels)
        narrow_count = np.sum(narrow_significant)
        narrow_pct = (narrow_count / len(significant_faces)) * 100
        
        result.update({
            'total_faces': len(face_areas),
            'significant_faces': len(significant_faces),
            'narrow_significant_pct': narrow_pct
        })
        
        # Only flag if there are many clustered narrow faces
        if narrow_pct > 15:  # 15% of significant faces are narrow
            narrow_indices = np.where(face_areas > 1.0)[0]  # Return actual indices
            narrow_indices = narrow_indices[narrow_significant]
            result['actual_narrow_channels'] = len(narrow_indices)
            return narrow_indices, result
        else:
            result['actual_narrow_channels'] = 0
            return np.array([]), result
            
    except Exception as e:
        result['error'] = str(e)
        return np.array([]), result
    

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

# Analysis score

def realistic_cnc_score(mesh):
    """
    Reality-based CNC manufacturability scoring.
    """
    score = 100
    problem_regions = []
    metadata = {'analysis_results': {}}
    
    print("=== REALISTIC CNC ANALYSIS ===")
    
    # 1. Undercuts (keep original - might be real)
    undercuts = find_undercuts(mesh)
    if len(undercuts) > 0:
        penalty = min(30, len(undercuts) * 0.5)  # Reduced penalty
        score -= penalty
        problem_regions.append(("Undercuts", undercuts))
        print(f"Undercuts: {len(undercuts)} faces, penalty: {penalty:.1f}")
    
    # 2. Internal volumes (realistic check)
    internal_severity, internal_data = realistic_internal_volumes(mesh)
    if internal_severity > 0:
        penalty = 25 if internal_severity == 2 else 10  # Much reduced
        score -= penalty
        problem_regions.append(("Internal Volumes", []))
        print(f"Internal volumes: severity {internal_severity}, penalty: {penalty}")
    else:
        print("Internal volumes: ✅ None (external voids are fine)")
    
    # 3. Narrow channels (realistic check)
    narrow_channels, narrow_data = realistic_narrow_channels(mesh)
    if len(narrow_channels) > 0:
        penalty = min(15, len(narrow_channels) * 0.1)
        score -= penalty
        problem_regions.append(("Narrow Channels", narrow_channels))
        print(f"Narrow channels: {len(narrow_channels)} faces, penalty: {penalty:.1f}")
    else:
        print("Narrow channels: ✅ None detected")
    
    # 4. Skip deep pockets for now (likely also bollocks)
    print("Deep pockets: ⏭️  Skipped (needs work)")
    
    # 5. Small features (realistic check)
    small_severity, small_data = realistic_small_features(mesh)
    if small_severity > 0:
        penalty = 10 if small_severity == 2 else 5  # Much reduced
        score -= penalty
        problem_regions.append(("Small Features", []))
        print(f"Small features: severity {small_severity}, penalty: {penalty}")
    else:
        print("Small features: ✅ None (mesh tessellation ignored)")
    
    # 6. Steep walls (realistic check)
    steep_walls, steep_data = realistic_steep_walls(mesh)
    if len(steep_walls) > 0:
        penalty = min(10, len(steep_walls) * 0.1)
        score -= penalty
        problem_regions.append(("Steep Walls", steep_walls))
        print(f"Steep walls: {len(steep_walls)} problematic faces, penalty: {penalty:.1f}")
        print(f"  (External steep walls: {steep_data['external_steep']} - these are GOOD)")
    else:
        print("Steep walls: ✅ None problematic (external walls are fine)")
    
    score = max(0, score)
    print(f"\nRealistic CNC Score: {score:.1f}/100")
    
    return score, problem_regions, metadata
# visualization functions 
import numpy as np
import plotly.graph_objects as go

def plot_interactive_3d_fixed(mesh, problem_regions, manufacturability_score, analysis_metadata=None):
    """
    Enhanced 3D visualization with CORRECT legend that matches actual analysis.
    """
    
    vertices = mesh.vertices
    faces = mesh.faces
    
    fig = go.Figure()
    
    # Configuration for problem region colors - MATCH the actual problem types
    problem_config = {
        'Undercuts': {'color': 'rgb(255,0,0)', 'emoji': '🔴'},
        'Internal Volumes': {'color': 'rgb(255,165,0)', 'emoji': '🟠'}, 
        'Deep Pockets': {'color': 'rgb(255,255,0)', 'emoji': '🟡'},
        'Narrow Channels': {'color': 'rgb(255,0,255)', 'emoji': '🟣'},
        'Small Features': {'color': 'rgb(0,255,255)', 'emoji': '🔵'},
        'Steep Walls': {'color': 'rgb(255,192,203)', 'emoji': '🌸'}
    }
    
    # Base mesh (semi-transparent green)
    fig.add_trace(go.Mesh3d(
        x=vertices[:, 0], y=vertices[:, 1], z=vertices[:, 2],
        i=faces[:, 0], j=faces[:, 1], k=faces[:, 2],
        facecolor=['rgba(144,238,144,0.3)'] * len(faces),
        opacity=0.3,
        name='Good Regions (CNC-friendly)',
        visible=True
    ))
    
    # Helper function to get problem faces for regions without specific indices
    def get_problem_faces(region_name):
        if "Internal" in region_name:
            # For internal volumes, highlight inward-facing surfaces
            face_normals = mesh.face_normals
            face_centers = mesh.triangles_center
            mesh_center = np.mean(mesh.vertices, axis=0)
            
            to_face = face_centers - mesh_center
            to_face_norm = to_face / (np.linalg.norm(to_face, axis=1, keepdims=True) + 1e-8)
            dot_products = np.sum(face_normals * to_face_norm, axis=1)
            return np.where(dot_products < -0.1)[0]
            
        elif "Small" in region_name:
            # For small features, find faces with very small edges
            edge_lengths = mesh.edges_unique_length
            edges = mesh.edges_unique
            
            small_edges = edges[edge_lengths < 1.0]
            if len(small_edges) == 0:
                return np.array([])
            
            small_edge_set = set()
            for edge in small_edges:
                small_edge_set.update([(edge[0], edge[1]), (edge[1], edge[0])])
            
            problem_faces = []
            for face_idx, face in enumerate(faces[:1000]):  # Limit for performance
                face_edges = [(face[0], face[1]), (face[1], face[2]), (face[2], face[0])]
                if any(edge in small_edge_set for edge in face_edges):
                    problem_faces.append(face_idx)
            
            return np.array(problem_faces)
        
        return np.array([])
    
    # Create dropdown buttons
    dropdown_buttons = [
        {
            'label': '✅ Show All (Good regions in green)',
            'method': 'update',
            'args': [{'visible': [True] + [False] * (len(problem_regions) * 2)}]
        }
    ]
    
    # Process each problem region
    for i, (region_name, face_indices) in enumerate(problem_regions):
        # Get the base problem type (first word)
        region_type = region_name.split()[0]
        if region_type not in problem_config:
            region_type = region_name  # Use full name if not found
        
        config = problem_config.get(region_type, {'color': 'rgb(128,128,128)', 'emoji': '⚪'})
        
        # Get actual problem faces
        if len(face_indices) == 0:
            actual_faces = get_problem_faces(region_name)
        else:
            actual_faces = face_indices
        
        # Create two versions: with background and problem-only
        for view_type in ['with_bg', 'problem_only']:
            if view_type == 'with_bg':
                face_colors = ['rgba(144,238,144,0.2)'] * len(faces)  # Light green background
                opacity = 0.9
                name_suffix = '(With Background)'
            else:
                face_colors = ['rgba(0,0,0,0)'] * len(faces)  # Transparent background
                opacity = 1.0
                name_suffix = '(ISOLATED VIEW)'
            
            # Color problem faces
            for face_idx in actual_faces:
                if face_idx < len(face_colors):
                    face_colors[face_idx] = config['color']
            
            fig.add_trace(go.Mesh3d(
                x=vertices[:, 0], y=vertices[:, 1], z=vertices[:, 2],
                i=faces[:, 0], j=faces[:, 1], k=faces[:, 2],
                facecolor=face_colors,
                opacity=opacity,
                name=f'{region_name} {name_suffix}',
                visible=False
            ))
        
        # Add dropdown buttons for this problem type
        for view_idx, view_suffix in enumerate(['(With Background)', '(ISOLATED VIEW)']):
            visibility = [False] * (len(problem_regions) * 2 + 1)
            visibility[i * 2 + view_idx + 1] = True
            
            dropdown_buttons.append({
                'label': f'{config["emoji"]} {region_name} {view_suffix}',
                'method': 'update',
                'args': [{'visible': visibility}]
            })
    
    # Create DYNAMIC legend based on actual problems found
    legend_items = build_dynamic_legend(problem_regions, manufacturability_score, analysis_metadata)
    
    # Layout with dropdown and dynamic legend
    fig.update_layout(
        title=f'CNC Manufacturability Analysis<br>Score: {manufacturability_score:.1f}/100<br>🎯 Use dropdown to examine specific problems',
        scene=dict(
            xaxis_title='X (mm)', yaxis_title='Y (mm)', zaxis_title='Z (mm)',
            aspectmode='data',
            camera=dict(eye=dict(x=1.2, y=1.2, z=1.2))
        ),
        width=1000, height=700,
        updatemenus=[{
            'buttons': dropdown_buttons,
            'direction': 'down',
            'showactive': True,
            'x': 0.02, 'xanchor': 'left',
            'y': 0.98, 'yanchor': 'top'
        }]
    )
    
    # Add dynamic legend
    fig.add_annotation(
        text="<br>".join(legend_items),
        xref="paper", yref="paper",
        x=0.02, y=0.02,
        xanchor="left", yanchor="bottom",
        showarrow=False,
        bgcolor="rgba(255,255,255,0.95)",
        bordercolor="black", borderwidth=1,
        font=dict(size=11)
    )
    
    return fig

def build_dynamic_legend(problem_regions, score, analysis_metadata=None):
    """
    Build legend that reflects ACTUAL problems found, not generic descriptions.
    """
    legend_items = [
        "📊 ANALYSIS RESULTS:",
        f"Overall CNC Score: {score:.1f}/100",
        ""
    ]
    
    if len(problem_regions) == 0:
        legend_items.extend([
            "🎉 NO PROBLEMS DETECTED!",
            "✅ Excellent for standard 3-axis CNC",
            "✅ All surfaces accessible",
            "✅ No geometric constraints"
        ])
    else:
        legend_items.append("⚠️  PROBLEMS DETECTED:")
        
        # Add specific information for each problem type
        for region_name, face_indices in problem_regions:
            face_count = len(face_indices) if isinstance(face_indices, (list, np.ndarray)) else "Multiple"
            
            if "Undercuts" in region_name:
                legend_items.append(f"🔴 {region_name}: {face_count} faces")
                legend_items.append("   → Requires 5-axis CNC or redesign")
                
            elif "Internal Volumes" in region_name:
                legend_items.append(f"🟠 {region_name}")
                legend_items.append("   → Enclosed spaces - impossible to machine")
                
            elif "Steep Walls" in region_name:
                legend_items.append(f"🌸 {region_name}: {face_count} faces")
                legend_items.append("   → Deep vertical walls - tool access issues")
                
            elif "Narrow Channels" in region_name:
                legend_items.append(f"🟣 {region_name}: {face_count} faces")
                legend_items.append("   → Too narrow for standard tools")
                
            elif "Small Features" in region_name:
                legend_items.append(f"🔵 {region_name}")
                legend_items.append("   → Features smaller than min tool size")
                
            elif "Deep Pockets" in region_name:
                legend_items.append(f"🟡 {region_name}: {face_count} faces")
                legend_items.append("   → Pockets too deep for standard tools")
    
    legend_items.extend([
        "",
        "🎯 USAGE TIPS:",
        "• Green = Good for CNC machining",
        "• Use dropdown to isolate problems",
        "• 'ISOLATED VIEW' shows only problems"
    ])
    
    # Add metadata if available
    if analysis_metadata and 'analysis_results' in analysis_metadata:
        legend_items.extend([
            "",
            "📈 DETAILED STATS:"
        ])
        
        results = analysis_metadata['analysis_results']
        if 'undercuts' in results:
            legend_items.append(f"   Undercuts penalty: {results['undercuts'].get('penalty', 0):.1f}")
        if 'steep_walls' in results:
            legend_items.append(f"   Steep walls penalty: {results['steep_walls'].get('penalty', 0):.1f}")
    
    return legend_items

def interpret_score(score):
    """Provide human-readable interpretation of the score."""
    if score >= 90:
        return "Excellent - Perfect for standard CNC"
    elif score >= 80:
        return "Good - Minor issues, easily machinable"
    elif score >= 70:
        return "Fair - Some challenges, may need special tools"
    elif score >= 50:
        return "Difficult - Requires advanced CNC or redesign"
    else:
        return "Very Difficult - Major redesign recommended"












path = r'C:\Users\junhongs\Desktop\itp\preprocess_cleanedup\testcases\moderate\Bracket.STL'
path1 = r'C:\Users\junhongs\Desktop\itp\preprocess_cleanedup\testcases\simple\cube.stl'
box = load_stl(path1)
bracket = load_stl(path)


score, problem_regions, metadata = realistic_cnc_score(bracket)
fig = plot_interactive_3d_fixed(bracket, problem_regions, score)
fig.show()

# score, regions, debug_info = debug_manufacturability_analysis(box)
# analyze_mesh_quality(box)
# suggest_fixes(debug_info)