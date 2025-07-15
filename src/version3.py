import numpy as np
import trimesh
import plotly.graph_objects as go

def load_stl(file_path):
    try: 
        mesh = trimesh.load(file_path)
        return mesh
    except Exception as e:
        print(f"Error loading file: {e}")
        return None
# ==================== GEOMETRIC CONTEXT FUNCTIONS ====================

def is_surface_external(face_center, face_normal, mesh_bounds, tolerance=2.0):
    """Check if a face is on the external boundary (good for CNC)."""
    for axis in range(3):
        for bound_idx in [0, 1]:
            distance_to_boundary = abs(face_center[axis] - mesh_bounds[bound_idx, axis])
            if distance_to_boundary < tolerance:
                return True
    return False

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

# ==================== CONTEXT-AWARE ANALYSIS FUNCTIONS ====================

def context_aware_undercuts(mesh):
    """Find undercuts that are ACTUALLY problematic."""
    face_normals = mesh.face_normals
    upward_faces = np.where(face_normals[:, 2] > 0.3)[0]
    
    actual_undercuts = []
    
    for face_idx in upward_faces:
        context = analyze_face_context(face_idx, mesh)
        
        if not context['has_tool_access'] and not context['is_external']:
            actual_undercuts.append(face_idx)
    
    return np.array(actual_undercuts)

def context_aware_steep_walls(mesh, angle_threshold=80.0):
    """Find steep walls that are ACTUALLY problematic."""
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

def context_aware_narrow_channels(mesh, min_channel_width=2.0):
    """Find ACTUAL narrow channels, not just small external faces."""
    face_areas = mesh.area_faces
    estimated_widths = np.sqrt(face_areas)
    potentially_narrow = np.where(estimated_widths < min_channel_width)[0]
    
    actual_narrow_channels = []
    
    for face_idx in potentially_narrow:
        context = analyze_face_context(face_idx, mesh)
        
        if context['is_deep'] and not context['has_tool_access'] and not context['is_external']:
            actual_narrow_channels.append(face_idx)
    
    return np.array(actual_narrow_channels)

def context_aware_internal_volumes(mesh):
    """Improved internal volume detection."""
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

def complete_cnc_analysis(mesh, verbose=True):
    """
    Complete context-aware CNC manufacturability analysis.
    
    Returns:
        tuple: (score, problem_regions, detailed_metadata)
    """
    if verbose:
        print("=== COMPLETE CNC MANUFACTURABILITY ANALYSIS ===")
        print(f"Mesh: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
        print(f"Bounds: {mesh.bounds}")
        print(f"Volume: {mesh.volume:.2f}")
        print()
    
    score = 100
    problem_regions = []
    metadata = {
        'mesh_info': {
            'vertices': len(mesh.vertices),
            'faces': len(mesh.faces),
            'volume': mesh.volume,
            'bounds': mesh.bounds.tolist(),
            'is_watertight': mesh.is_watertight
        },
        'analysis_results': {}
    }
    
    # 1. Context-aware undercuts
    if verbose:
        print("1. Analyzing undercuts (context-aware)...")
    undercuts = context_aware_undercuts(mesh)
    if len(undercuts) > 0:
        penalty = min(30, len(undercuts) * 1.0)
        score -= penalty
        problem_regions.append(("True Undercuts", undercuts))
        metadata['analysis_results']['undercuts'] = {
            'count': len(undercuts),
            'penalty': penalty,
            'description': 'Surfaces that truly cannot be machined with standard CNC'
        }
        if verbose:
            print(f"   ❌ Found {len(undercuts)} true undercuts, penalty: {penalty:.1f}")
    else:
        if verbose:
            print("   ✅ No problematic undercuts")
    
    # 2. Context-aware internal volumes
    if verbose:
        print("2. Analyzing internal volumes (context-aware)...")
    internal_severity, internal_data = context_aware_internal_volumes(mesh)
    if internal_severity > 0:
        penalty = 25 if internal_severity == 2 else 10
        score -= penalty
        problem_regions.append(("Enclosed Internal Volumes", []))
        metadata['analysis_results']['internal_volumes'] = {
            'severity': internal_severity,
            'penalty': penalty,
            'volume_ratio': internal_data['volume_ratio'],
            'has_external_openings': internal_data['has_external_openings'],
            'description': 'Completely enclosed spaces that cannot be machined'
        }
        if verbose:
            print(f"   ❌ Internal volumes severity: {internal_severity}, penalty: {penalty}")
    else:
        if verbose:
            print("   ✅ No problematic internal volumes")
    
    # 3. Context-aware narrow channels
    if verbose:
        print("3. Analyzing narrow channels (context-aware)...")
    narrow_channels = context_aware_narrow_channels(mesh)
    if len(narrow_channels) > 0:
        penalty = min(20, len(narrow_channels) * 0.2)
        score -= penalty
        problem_regions.append(("Confined Narrow Channels", narrow_channels))
        metadata['analysis_results']['narrow_channels'] = {
            'count': len(narrow_channels),
            'penalty': penalty,
            'description': 'Internal channels too narrow for standard tools'
        }
        if verbose:
            print(f"   ❌ Found {len(narrow_channels)} confined channels, penalty: {penalty:.1f}")
    else:
        if verbose:
            print("   ✅ No confined narrow channels")
    
    # 4. Context-aware steep walls
    if verbose:
        print("4. Analyzing steep walls (context-aware)...")
    steep_walls = context_aware_steep_walls(mesh)
    if len(steep_walls) > 0:
        penalty = min(15, len(steep_walls) * 0.3)
        score -= penalty
        problem_regions.append(("Inaccessible Steep Walls", steep_walls))
        metadata['analysis_results']['steep_walls'] = {
            'count': len(steep_walls),
            'penalty': penalty,
            'description': 'Steep walls in deep pockets with poor tool access'
        }
        if verbose:
            print(f"   ❌ Found {len(steep_walls)} inaccessible steep walls, penalty: {penalty:.1f}")
    else:
        if verbose:
            print("   ✅ No problematic steep walls")
    
    score = max(0, score)
    metadata['final_score'] = score
    metadata['total_penalty'] = 100 - score
    
    if verbose:
        print(f"\nFinal CNC Manufacturability Score: {score:.1f}/100")
        print(f"Number of problem types: {len(problem_regions)}")
        print()
    
    return score, problem_regions, metadata

def get_problem_faces_for_display(region_name, mesh):
    """
    Get face indices for problems that don't have specific face lists.
    """
    if "Internal" in region_name:
        # For internal volumes, highlight faces that point inward
        face_normals = mesh.face_normals
        face_centers = mesh.triangles_center
        mesh_center = np.mean(mesh.vertices, axis=0)
        
        to_face = face_centers - mesh_center
        to_face_norm = to_face / (np.linalg.norm(to_face, axis=1, keepdims=True) + 1e-8)
        dot_products = np.sum(face_normals * to_face_norm, axis=1)
        return np.where(dot_products < -0.2)[0]  # More aggressive threshold
        
    return np.array([])

# ==================== INTEGRATED PLOTTING FUNCTION ====================

def plot_interactive_3d_integrated(mesh, problem_regions, manufacturability_score, analysis_metadata=None):
    """
    Enhanced 3D visualization integrated with context-aware analysis.
    """
    vertices = mesh.vertices
    faces = mesh.faces
    
    print(f"DEBUG: Plotting mesh with {len(faces)} faces")
    print(f"DEBUG: Found {len(problem_regions)} problem regions:")
    for region_name, face_indices in problem_regions:
        print(f"  - {region_name}: {len(face_indices)} faces")
    
    fig = go.Figure()
    
    # Problem type configurations
    problem_config = {
        'True': {'color': 'rgb(255,0,0)', 'emoji': '🔴'},  # True Undercuts
        'Enclosed': {'color': 'rgb(255,165,0)', 'emoji': '🟠'},  # Enclosed Internal Volumes
        'Confined': {'color': 'rgb(255,0,255)', 'emoji': '🟣'},  # Confined Narrow Channels
        'Inaccessible': {'color': 'rgb(255,192,203)', 'emoji': '🌸'},  # Inaccessible Steep Walls
    }
    
    # Base mesh (green = good for CNC)
    fig.add_trace(go.Mesh3d(
        x=vertices[:, 0], y=vertices[:, 1], z=vertices[:, 2],
        i=faces[:, 0], j=faces[:, 1], k=faces[:, 2],
        facecolor=['rgba(34,139,34,0.4)'] * len(faces),  # Forest green
        opacity=0.4,
        name=f'CNC-Friendly Regions (Score: {manufacturability_score:.1f})',
        visible=True
    ))
    
    # Create dropdown buttons
    dropdown_buttons = [
        {
            'label': '✅ Show All (CNC-friendly in green)',
            'method': 'update',
            'args': [{'visible': [True] + [False] * (len(problem_regions) * 2)}]
        }
    ]
    
    # Process each problem region
    for i, (region_name, face_indices) in enumerate(problem_regions):
        # Get problem type from region name
        region_type = region_name.split()[0]
        config = problem_config.get(region_type, {'color': 'rgb(128,128,128)', 'emoji': '⚪'})
        
        # Handle different problem types
        if len(face_indices) == 0:
            # For problems without specific face indices (like internal volumes)
            actual_faces = get_problem_faces_for_display(region_name, mesh)
        else:
            actual_faces = face_indices
        
        print(f"DEBUG: {region_name} has {len(actual_faces)} faces to display")
        
        # Create two versions: with background and isolated
        for view_type in ['with_bg', 'isolated']:
            if view_type == 'with_bg':
                face_colors = ['rgba(34,139,34,0.1)'] * len(faces)  # Light green background
                opacity = 0.9
                name_suffix = '(With Background)'
            else:
                face_colors = ['rgba(0,0,0,0)'] * len(faces)  # Transparent
                opacity = 1.0
                name_suffix = '(ISOLATED)'
            
            # Color problem faces - FIXED LOGIC
            if len(actual_faces) > 0:
                for face_idx in actual_faces:
                    if 0 <= face_idx < len(face_colors):  # Bounds check
                        face_colors[face_idx] = config['color']
            
            fig.add_trace(go.Mesh3d(
                x=vertices[:, 0], y=vertices[:, 1], z=vertices[:, 2],
                i=faces[:, 0], j=faces[:, 1], k=faces[:, 2],
                facecolor=face_colors,
                opacity=opacity,
                name=f'{region_name} {name_suffix}',
                visible=False
            ))
        
        # Add dropdown buttons
        for view_idx, view_suffix in enumerate(['(With Background)', '(ISOLATED)']):
            visibility = [False] * (len(problem_regions) * 2 + 1)
            visibility[i * 2 + view_idx + 1] = True
            
            dropdown_buttons.append({
                'label': f'{config["emoji"]} {region_name} {view_suffix}',
                'method': 'update',
                'args': [{'visible': visibility}]
            })
    
    # Build dynamic legend
    legend_items = build_comprehensive_legend(problem_regions, manufacturability_score, analysis_metadata)
    
    # Layout
    fig.update_layout(
        title=f'Smart CNC Manufacturability Analysis<br>Score: {manufacturability_score:.1f}/100 ({interpret_score(manufacturability_score)})<br>🎯 Context-aware analysis - external surfaces ignored',
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
    
    # Add legend
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

def build_comprehensive_legend(problem_regions, score, analysis_metadata=None):
    """Build comprehensive legend with context-aware results."""
    legend_items = [
        "📊 SMART CNC ANALYSIS RESULTS:",
        f"Manufacturability Score: {score:.1f}/100",
        f"Assessment: {interpret_score(score)}",
        ""
    ]
    
    if len(problem_regions) == 0:
        legend_items.extend([
            "🎉 EXCELLENT FOR CNC MACHINING!",
            "✅ No geometric constraints detected",
            "✅ All surfaces are accessible",
            "✅ Perfect for standard 3-axis CNC",
            "✅ External walls and voids are fine"
        ])
    else:
        legend_items.append("⚠️  ACTUAL PROBLEMS DETECTED:")
        
        for region_name, face_indices in problem_regions:
            face_count = len(face_indices) if isinstance(face_indices, (list, np.ndarray)) else "Multiple"
            
            if "True Undercuts" in region_name:
                legend_items.extend([
                    f"🔴 {region_name}: {face_count} faces",
                    "   → Surfaces with no tool access from any direction",
                    "   → Requires 5-axis CNC or design changes"
                ])
                
            elif "Enclosed Internal Volumes" in region_name:
                legend_items.extend([
                    f"🟠 {region_name}",
                    "   → Completely sealed internal spaces",
                    "   → Impossible to machine - redesign needed"
                ])
                
            elif "Confined Narrow Channels" in region_name:
                legend_items.extend([
                    f"🟣 {region_name}: {face_count} faces",
                    "   → Internal channels too narrow for tools",
                    "   → Increase channel width or use smaller tools"
                ])
                
            elif "Inaccessible Steep Walls" in region_name:
                legend_items.extend([
                    f"🌸 {region_name}: {face_count} faces",
                    "   → Deep vertical walls with poor access",
                    "   → May need special long tools or 5-axis"
                ])
    
    legend_items.extend([
        "",
        "🧠 SMART ANALYSIS FEATURES:",
        "• External surfaces ignored (they're good for CNC)",
        "• Only flags truly inaccessible geometry",
        "• Context-aware geometric understanding",
        "• Distinguishes real problems from false alarms"
    ])
    
    return legend_items

def interpret_score(score):
    """Human-readable score interpretation."""
    if score >= 90:
        return "Excellent"
    elif score >= 80:
        return "Good"
    elif score >= 70:
        return "Fair"
    elif score >= 50:
        return "Challenging"
    else:
        return "Difficult"

# ==================== MAIN INTEGRATED FUNCTION ====================

def analyze_and_visualize(mesh, verbose=True):
    """
    Complete workflow: analyze with context awareness and visualize results.
    
    Usage:
        mesh = trimesh.load('your_part.stl')
        fig = analyze_and_visualize(mesh)
        fig.show()
    """
    # Run smart analysis
    score, problem_regions, metadata = complete_cnc_analysis(mesh, verbose=verbose)
    
    # Create visualization
    fig = plot_interactive_3d_integrated(mesh, problem_regions, score, metadata)
    
    return fig

# ==================== EXAMPLE USAGE ====================

def example_usage():
    """Example of how to use the complete integrated system."""
    print("=== INTEGRATED CNC ANALYSIS SYSTEM ===")
    print("Usage:")
    print("1. Load your STL: mesh = trimesh.load('bracket.stl')")
    print("2. Analyze and visualize: fig = analyze_and_visualize(mesh)")
    print("3. Show results: fig.show()")
    print()
    print("Your triangular bracket should now score 80-95/100!")
    
    
    file = r'C:\Users\junhongs\Desktop\itp\preprocess_cleanedup\testcases\moderate\cone.STL'
    fig = analyze_and_visualize(load_stl(file), verbose=True)
    fig.show()

if __name__ == "__main__":
    example_usage()