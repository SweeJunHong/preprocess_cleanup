import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import io
import base64

def create_3d_visualization(mesh, problem_regions, score):
    """Create interactive 3D visualization with Plotly."""
    vertices = mesh.vertices
    faces = mesh.faces
    
    fig = go.Figure()
    
    # Problem type configurations
    problem_config = {
        'Undercuts': {'color': 'rgb(255,0,0)', 'emoji': '🔴'},
        'Internal Volumes': {'color': 'rgb(255,165,0)', 'emoji': '🟠'},
        'Deep Pockets': {'color': 'rgb(255,255,0)', 'emoji': '🟡'},
        'Narrow Channels': {'color': 'rgb(255,0,255)', 'emoji': '🟣'},
        'Small Features': {'color': 'rgb(0,255,255)', 'emoji': '🔵'},
        'Steep Walls': {'color': 'rgb(255,192,203)', 'emoji': '🌸'}
    }
    
    # Base mesh (green for CNC-friendly)
    fig.add_trace(go.Mesh3d(
        x=vertices[:, 0], y=vertices[:, 1], z=vertices[:, 2],
        i=faces[:, 0], j=faces[:, 1], k=faces[:, 2],
        facecolor=['rgba(34,139,34,0.4)'] * len(faces),
        opacity=0.4,
        name=f'CNC-Friendly (Score: {score:.1f}/100)',
        visible=True
    ))
    
    # Create dropdown buttons
    dropdown_buttons = [
        {
            'label': '✅ Show All',
            'method': 'update',
            'args': [{'visible': [True] + [False] * (len(problem_regions) * 2)}]
        }
    ]
    
    # Add problem regions
    for i, (region_name, face_indices) in enumerate(problem_regions):
        config = problem_config.get(region_name, {'color': 'rgb(128,128,128)', 'emoji': '⚪'})
        
        # Handle empty face indices
        if len(face_indices) == 0:
            face_indices = get_problem_faces_for_region(region_name, mesh)
        
        # With background version
        face_colors_bg = ['rgba(34,139,34,0.1)'] * len(faces)
        for idx in face_indices:
            if 0 <= idx < len(faces):
                face_colors_bg[idx] = config['color']
        
        fig.add_trace(go.Mesh3d(
            x=vertices[:, 0], y=vertices[:, 1], z=vertices[:, 2],
            i=faces[:, 0], j=faces[:, 1], k=faces[:, 2],
            facecolor=face_colors_bg,
            opacity=0.9,
            name=f'{region_name} (With Background)',
            visible=False
        ))
        
        # Isolated version
        face_colors_iso = ['rgba(0,0,0,0)'] * len(faces)
        for idx in face_indices:
            if 0 <= idx < len(faces):
                face_colors_iso[idx] = config['color']
        
        fig.add_trace(go.Mesh3d(
            x=vertices[:, 0], y=vertices[:, 1], z=vertices[:, 2],
            i=faces[:, 0], j=faces[:, 1], k=faces[:, 2],
            facecolor=face_colors_iso,
            opacity=1.0,
            name=f'{region_name} (Isolated)',
            visible=False
        ))
        
        # Add dropdown buttons
        for j, suffix in enumerate(['(With Background)', '(Isolated)']):
            visibility = [False] * (len(problem_regions) * 2 + 1)
            visibility[i * 2 + j + 1] = True
            dropdown_buttons.append({
                'label': f'{config["emoji"]} {region_name} {suffix}',
                'method': 'update',
                'args': [{'visible': visibility}]
            })
    
    # Update layout
    fig.update_layout(
        title=f'CNC Manufacturability Analysis<br>Score: {score:.1f}/100',
        scene=dict(
            xaxis_title='X (mm)',
            yaxis_title='Y (mm)',
            zaxis_title='Z (mm)',
            aspectmode='data',
            camera=dict(eye=dict(x=1.2, y=1.2, z=1.2))
        ),
        width=1000,
        height=700,
        updatemenus=[{
            'buttons': dropdown_buttons,
            'direction': 'down',
            'showactive': True,
            'x': 0.02,
            'xanchor': 'left',
            'y': 0.98,
            'yanchor': 'top'
        }]
    )
    
    return fig

def get_problem_faces_for_region(region_name, mesh):
    """Get face indices for regions without specific faces."""
    if "Internal" in region_name:
        face_normals = mesh.face_normals
        face_centers = mesh.triangles_center
        mesh_center = np.mean(mesh.vertices, axis=0)
        
        to_face = face_centers - mesh_center
        to_face_norm = to_face / (np.linalg.norm(to_face, axis=1, keepdims=True) + 1e-8)
        dot_products = np.sum(face_normals * to_face_norm, axis=1)
        return np.where(dot_products < -0.2)[0]
    
    return np.array([])

def create_summary_chart(results, score):
    """Create summary visualization of analysis results."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Score gauge
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 5)
    
    # Draw gauge background
    colors = ['#FF0000', '#FFA500', '#FFFF00', '#90EE90', '#228B22']
    labels = ['0-20', '20-40', '40-60', '60-80', '80-100']
    
    for i, (color, label) in enumerate(zip(colors, labels)):
        rect = Rectangle((i*2, 0), 2, 4, facecolor=color, alpha=0.3)
        ax1.add_patch(rect)
        ax1.text(i*2 + 1, 4.5, label, ha='center', fontsize=10)
    
    # Draw score indicator
    score_pos = score / 10
    ax1.arrow(score_pos, -0.5, 0, 1, head_width=0.3, head_length=0.2, 
              fc='black', ec='black', lw=2)
    ax1.text(score_pos, -1, f'{score:.1f}', ha='center', fontsize=14, fontweight='bold')
    
    ax1.set_title('CNC Manufacturability Score', fontsize=16, fontweight='bold')
    ax1.axis('off')
    
    # Problem breakdown
    problems = []
    counts = []
    
    for key, value in results.items():
        if 'count' in value and value['count'] > 0:
            problems.append(key.replace('_', ' ').title())
            counts.append(value['count'])
        if isinstance(value, dict) and 'severity' in value and isinstance(value['severity'], (int, float)) and value['severity'] > 0:
        
            problems.append(key.replace('_', ' ').title())
            counts.append(value['severity'] * 50)  # Scale for visibility
    
    if problems:
        bars = ax2.barh(problems, counts)
        
        # Color bars based on severity
        for i, bar in enumerate(bars):
            if counts[i] > 100:
                bar.set_color('#FF0000')
            elif counts[i] > 50:
                bar.set_color('#FFA500')
            else:
                bar.set_color('#FFFF00')
        
        ax2.set_xlabel('Issue Count/Severity')
        ax2.set_title('Problem Breakdown', fontsize=16, fontweight='bold')
    else:
        ax2.text(0.5, 0.5, 'No Problems Detected!', 
                ha='center', va='center', fontsize=20, 
                color='green', fontweight='bold', transform=ax2.transAxes)
        ax2.axis('off')
    
    plt.tight_layout()
    
    # Convert to base64 for embedding
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close()
    
    return image_base64

def interpret_score(score):
    """Get interpretation of score."""
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