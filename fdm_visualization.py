"""
FDM Visual Simulation Module

This module provides 3D visualization capabilities for FDM printing simulation,
including layer-by-layer printing visualization, support structures, and print paths.
"""

import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pyvista as pv
import trimesh
from typing import Dict, List, Optional, Tuple
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import io
import base64

class FDMVisualizer:
    """3D visualization for FDM printing simulation."""
    
    def __init__(self):
        """Initialize the visualizer."""
        self.mesh = None
        self.layers = []
        self.support_regions = []
        self.print_paths = []
        
    def load_mesh_data(self, mesh: trimesh.Trimesh, layers: List[Dict], 
                      support_data: Optional[Dict] = None):
        """
        Load mesh and layer data for visualization.
        
        Args:
            mesh: Trimesh object
            layers: List of layer data from slicing
            support_data: Support structure data
        """
        self.mesh = mesh
        self.layers = layers
        if support_data:
            self.support_regions = self._extract_support_regions(support_data)
    
    def create_3d_mesh_view(self, show_supports: bool = True) -> go.Figure:
        """
        Create 3D visualization of the mesh with optional support structures.
        
        Args:
            show_supports: Whether to show support structures
            
        Returns:
            Plotly figure
        """
        if self.mesh is None:
            raise ValueError("No mesh loaded. Call load_mesh_data() first.")
        
        fig = go.Figure()
        
        # Main mesh
        vertices = self.mesh.vertices
        faces = self.mesh.faces
        
        fig.add_trace(go.Mesh3d(
            x=vertices[:, 0],
            y=vertices[:, 1], 
            z=vertices[:, 2],
            i=faces[:, 0],
            j=faces[:, 1],
            k=faces[:, 2],
            color='lightblue',
            opacity=0.8,
            name='Part',
            showscale=False
        ))
        
        # Support structures if requested
        if show_supports and self.support_regions:
            support_points = self._generate_support_visualization()
            if support_points is not None:
                fig.add_trace(go.Scatter3d(
                    x=support_points[:, 0],
                    y=support_points[:, 1],
                    z=support_points[:, 2],
                    mode='markers',
                    marker=dict(size=2, color='red', opacity=0.6),
                    name='Support Structures'
                ))
        
        # Update layout
        fig.update_layout(
            scene=dict(
                xaxis_title='X (mm)',
                yaxis_title='Y (mm)',
                zaxis_title='Z (mm)',
                aspectmode='data'
            ),
            title='3D FDM Print Visualization',
            width=800,
            height=600
        )
        
        return fig
    
    def create_educational_printing_animation(self, max_layers: int = 50) -> go.Figure:
        """
        Create an educational 3D printing animation that shows the actual printing process
        with print head, extruded material, and layer-by-layer construction.
        
        Args:
            max_layers: Maximum number of layers to animate
            
        Returns:
            Plotly figure with educational printing animation
        """
        if not self.layers:
            raise ValueError("No layer data available.")
        
        # Limit layers for performance and educational clarity
        display_layers = self.layers[:min(max_layers, len(self.layers))]
        z_positions = [layer['z_height'] for layer in display_layers]
        
        # Get mesh bounds for positioning elements
        bounds = self.mesh.bounds if self.mesh else np.array([[-50, -50, 0], [50, 50, 50]])
        
        # Create educational frames
        frames = []
        
        for i, layer in enumerate(display_layers):
            current_z = z_positions[i]
            
            # Create frame data
            frame_data = []
            
            # 1. Show the build platform (always visible)
            platform_size = max(bounds[1][0] - bounds[0][0], bounds[1][1] - bounds[0][1]) * 1.2
            platform_z = bounds[0][2] - 2
            
            frame_data.append(go.Mesh3d(
                x=[bounds[0][0] - platform_size/4, bounds[1][0] + platform_size/4, 
                   bounds[1][0] + platform_size/4, bounds[0][0] - platform_size/4],
                y=[bounds[0][1] - platform_size/4, bounds[0][1] - platform_size/4, 
                   bounds[1][1] + platform_size/4, bounds[1][1] + platform_size/4],
                z=[platform_z, platform_z, platform_z, platform_z],
                i=[0, 1], j=[1, 2], k=[2, 3],
                color='rgb(100, 100, 100)',
                opacity=0.3,
                name='Build Platform',
                showscale=False,
                hovertemplate='Build Platform<extra></extra>'
            ))
            
            # 2. Show completed layers (with layer-by-layer color progression)
            visible_z = z_positions[:i+1]
            layer_meshes = self._create_real_layer_meshes(visible_z)
            
            # Combine all previous layers with distinct colors
            for j, layer_mesh in enumerate(layer_meshes):
                if layer_mesh is not None:
                    # Color progression: early layers are cooler (blue), recent layers are warmer (red)
                    layer_age = (i - j) / max(i, 1)  # 0 = newest, 1 = oldest
                    
                    if layer_age < 0.1:  # Current layer - bright and warm
                        color = 'rgb(255, 100, 50)'  # Bright orange-red (hot plastic)
                        opacity = 1.0
                        layer_name = f'🔥 Layer {j+1} (Just Printed!)'
                    elif layer_age < 0.3:  # Recent layers - warm
                        color = 'rgb(255, 150, 100)'  # Warm orange
                        opacity = 0.9
                        layer_name = f'🌡️ Layer {j+1} (Cooling)'
                    else:  # Older layers - cooler
                        color = 'rgb(100, 150, 255)'  # Cool blue
                        opacity = 0.8
                        layer_name = f'❄️ Layer {j+1} (Solid)'
                    
                    frame_data.append(go.Mesh3d(
                        x=layer_mesh['vertices'][:, 0],
                        y=layer_mesh['vertices'][:, 1],
                        z=layer_mesh['vertices'][:, 2],
                        i=layer_mesh['faces'][:, 0],
                        j=layer_mesh['faces'][:, 1],
                        k=layer_mesh['faces'][:, 2],
                        color=color,
                        opacity=opacity,
                        name=layer_name,
                        showscale=False,
                        hovertemplate=f'{layer_name}<br>Height: {visible_z[j]:.2f}mm<extra></extra>',
                        lighting=dict(ambient=0.2, diffuse=1, fresnel=0.1, specular=1, roughness=0.1)
                    ))
            
            # 3. Show print head/nozzle position
            nozzle_x = bounds[0][0] + (bounds[1][0] - bounds[0][0]) * 0.7  # Position nozzle
            nozzle_y = bounds[0][1] + (bounds[1][1] - bounds[0][1]) * 0.3
            nozzle_z = current_z + 5  # 5mm above current layer
            
            frame_data.append(go.Scatter3d(
                x=[nozzle_x],
                y=[nozzle_y],
                z=[nozzle_z],
                mode='markers',
                marker=dict(
                    size=15,
                    color='rgb(200, 50, 50)',
                    symbol='diamond',
                    line=dict(width=2, color='rgb(100, 0, 0)')
                ),
                name='🖨️ Print Head',
                hovertemplate='Print Head<br>Printing Layer %{customdata}<extra></extra>',
                customdata=[i+1]
            ))
            
            # 4. Show extruded filament coming out (if not first layer)
            if i > 0:
                filament_stream = []
                for k in range(5):  # Show 5 droplets
                    stream_z = current_z + 4 - k * 0.8
                    filament_stream.append([nozzle_x, nozzle_y, stream_z])
                
                if filament_stream:
                    stream_array = np.array(filament_stream)
                    frame_data.append(go.Scatter3d(
                        x=stream_array[:, 0],
                        y=stream_array[:, 1],
                        z=stream_array[:, 2],
                        mode='markers',
                        marker=dict(
                            size=3,
                            color='rgb(255, 200, 0)',
                            opacity=0.8
                        ),
                        name='💧 Molten Plastic',
                        hovertemplate='Molten Plastic<br>Temperature: ~200°C<extra></extra>'
                    ))
            
            # 5. Add progress indicators
            progress_text = f"Layer {i+1} of {len(display_layers)}<br>"
            progress_text += f"Height: {current_z:.1f}mm<br>"
            progress_text += f"Progress: {((i+1)/len(display_layers)*100):.0f}%"
            
            frame_data.append(go.Scatter3d(
                x=[bounds[1][0] + 10],
                y=[bounds[1][1] + 10],
                z=[current_z],
                mode='text',
                text=[progress_text],
                textposition='middle center',
                textfont=dict(size=12, color='rgb(0, 0, 0)'),
                name='📊 Progress',
                showlegend=False
            ))
            
            # Create frame
            frame = go.Frame(
                data=frame_data,
                name=str(i),
                layout=dict(
                    title=f"🖨️ 3D Printing Layer {i+1} - {progress_text.split('<br>')[2]}"
                )
            )
            frames.append(frame)
        
        # Initial frame - show build platform and print head ready to start
        initial_data = []
        
        # Build platform
        platform_size = max(bounds[1][0] - bounds[0][0], bounds[1][1] - bounds[0][1]) * 1.2
        platform_z = bounds[0][2] - 2
        
        initial_data.append(go.Mesh3d(
            x=[bounds[0][0] - platform_size/4, bounds[1][0] + platform_size/4, 
               bounds[1][0] + platform_size/4, bounds[0][0] - platform_size/4],
            y=[bounds[0][1] - platform_size/4, bounds[0][1] - platform_size/4, 
               bounds[1][1] + platform_size/4, bounds[1][1] + platform_size/4],
            z=[platform_z, platform_z, platform_z, platform_z],
            i=[0, 1], j=[1, 2], k=[2, 3],
            color='rgb(100, 100, 100)',
            opacity=0.3,
            name='Build Platform',
            showscale=False,
            hovertemplate='Build Platform<extra></extra>'
        ))
        
        # Print head ready to start
        nozzle_x = bounds[0][0] + (bounds[1][0] - bounds[0][0]) * 0.7
        nozzle_y = bounds[0][1] + (bounds[1][1] - bounds[0][1]) * 0.3
        nozzle_z = z_positions[0] + 5
        
        initial_data.append(go.Scatter3d(
            x=[nozzle_x],
            y=[nozzle_y],
            z=[nozzle_z],
            mode='markers',
            marker=dict(
                size=15,
                color='rgb(200, 50, 50)',
                symbol='diamond',
                line=dict(width=2, color='rgb(100, 0, 0)')
            ),
            name='🖨️ Print Head',
            hovertemplate='Print Head<br>Ready to Start!<extra></extra>'
        ))
        
        # Welcome message
        initial_data.append(go.Scatter3d(
            x=[bounds[1][0] + 10],
            y=[bounds[1][1] + 10],
            z=[z_positions[0]],
            mode='text',
            text=['Ready to Print!<br>Press Play to Start<br>🎬 Educational Mode'],
            textposition='middle center',
            textfont=dict(size=14, color='rgb(0, 100, 0)'),
            name='Welcome',
            showlegend=False
        ))
        
        fig = go.Figure(
            data=initial_data,
            frames=frames
        )
        
        # Add educational animation controls
        fig.update_layout(
            scene=dict(
                xaxis_title='X Position (mm)',
                yaxis_title='Y Position (mm)',
                zaxis_title='Height (mm)',
                aspectmode='data',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5),  # Better viewing angle
                    center=dict(x=0, y=0, z=0)
                )
            ),
            title='🎓 Educational 3D Printing Animation - See How Layer-by-Layer Manufacturing Works!',
            updatemenus=[{
                'type': 'buttons',
                'showactive': False,
                'x': 0.1,
                'y': 0.9,
                'buttons': [
                    {
                        'label': '▶️ Start Printing',
                        'method': 'animate',
                        'args': [None, {
                            'frame': {'duration': 1000, 'redraw': True},  # Slower for education
                            'fromcurrent': True,
                            'transition': {'duration': 300}
                        }]
                    },
                    {
                        'label': '⏸️ Pause',
                        'method': 'animate',
                        'args': [[None], {
                            'frame': {'duration': 0, 'redraw': False},
                            'mode': 'immediate',
                            'transition': {'duration': 0}
                        }]
                    },
                    {
                        'label': '⏹️ Reset',
                        'method': 'animate',
                        'args': [['0'], {
                            'frame': {'duration': 0, 'redraw': True},
                            'mode': 'immediate',
                            'transition': {'duration': 0}
                        }]
                    }
                ]
            }],
            sliders=[{
                'steps': [
                    {
                        'args': [[str(i)], {
                            'frame': {'duration': 300, 'redraw': True},
                            'mode': 'immediate',
                            'transition': {'duration': 150}
                        }],
                        'label': f'🏗️ Layer {i+1}',
                        'method': 'animate'
                    }
                    for i in range(len(display_layers))
                ],
                'active': 0,
                'currentvalue': {'prefix': 'Current Layer: '},
                'transition': {'duration': 150},
                'x': 0.1,
                'len': 0.8,
                'bgcolor': 'rgba(255, 255, 255, 0.8)',
                'bordercolor': 'rgba(0, 0, 0, 0.5)',
                'borderwidth': 2
            }],
            width=1000,
            height=800,
            annotations=[
                dict(
                    text="🎯 This animation shows how 3D printing works:<br>" +
                         "• 🔥 Hot plastic (orange/red) is extruded layer by layer<br>" +
                         "• 🌡️ Each layer cools down (becomes blue)<br>" +
                         "• 🖨️ The print head moves to build the object<br>" +
                         "• 📊 Watch the progress in real-time!",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.02, y=0.98,
                    xanchor="left", yanchor="top",
                    bgcolor="rgba(255, 255, 255, 0.8)",
                    bordercolor="rgba(0, 0, 0, 0.5)",
                    borderwidth=1,
                    font=dict(size=12)
                )
            ]
        )
        
        return fig
    
    def create_simple_printing_animation(self, max_layers: int = 50) -> go.Figure:
        """
        Create a simple, clean printing animation without heat effects.
        Focus on the building process with slower, clearer visualization.
        """
        if not self.layers:
            raise ValueError("No layer data available.")
        
        # Limit layers for clear visualization
        display_layers = self.layers[:min(max_layers, len(self.layers))]
        z_positions = [layer['z_height'] for layer in display_layers]
        
        # Get mesh bounds for positioning
        bounds = self.mesh.bounds if self.mesh else np.array([[-50, -50, 0], [50, 50, 50]])
        
        # Create simple frames
        frames = []
        
        for i, layer in enumerate(display_layers):
            current_z = z_positions[i]
            frame_data = []
            
            # 1. Build platform (always visible)
            platform_size = max(bounds[1][0] - bounds[0][0], bounds[1][1] - bounds[0][1]) * 1.1
            platform_z = bounds[0][2] - 1
            
            frame_data.append(go.Mesh3d(
                x=[bounds[0][0] - platform_size/6, bounds[1][0] + platform_size/6, 
                   bounds[1][0] + platform_size/6, bounds[0][0] - platform_size/6],
                y=[bounds[0][1] - platform_size/6, bounds[0][1] - platform_size/6, 
                   bounds[1][1] + platform_size/6, bounds[1][1] + platform_size/6],
                z=[platform_z, platform_z, platform_z, platform_z],
                i=[0, 1], j=[1, 2], k=[2, 3],
                color='rgb(120, 120, 120)',
                opacity=0.4,
                name='Print Bed',
                showscale=False
            ))
            
            # 2. Show all completed layers in consistent color
            visible_z = z_positions[:i+1]
            layer_meshes = self._create_real_layer_meshes(visible_z)
            
            # Combine all layers into one clean mesh
            combined_vertices = []
            combined_faces = []
            vertex_offset = 0
            
            for j, layer_mesh in enumerate(layer_meshes):
                if layer_mesh is not None:
                    combined_vertices.append(layer_mesh['vertices'])
                    faces_with_offset = layer_mesh['faces'] + vertex_offset
                    combined_faces.append(faces_with_offset)
                    vertex_offset += len(layer_mesh['vertices'])
            
            if combined_vertices:
                all_vertices = np.vstack(combined_vertices)
                all_faces = np.vstack(combined_faces)
                
                # Simple blue color for all printed material
                frame_data.append(go.Mesh3d(
                    x=all_vertices[:, 0],
                    y=all_vertices[:, 1],
                    z=all_vertices[:, 2],
                    i=all_faces[:, 0],
                    j=all_faces[:, 1],
                    k=all_faces[:, 2],
                    color='rgb(70, 130, 220)',  # Clean blue
                    opacity=0.9,
                    name='Printed Object',
                    showscale=False,
                    hovertemplate=f'Layer {i+1}<br>Height: {current_z:.2f}mm<extra></extra>',
                    lighting=dict(ambient=0.3, diffuse=0.8, specular=0.1, roughness=0.2)
                ))
            
            # 3. Print head (slower moving, less prominent)
            nozzle_x = bounds[0][0] + (bounds[1][0] - bounds[0][0]) * 0.8
            nozzle_y = bounds[0][1] + (bounds[1][1] - bounds[0][1]) * 0.2
            nozzle_z = current_z + 3  # Closer to layer
            
            frame_data.append(go.Scatter3d(
                x=[nozzle_x],
                y=[nozzle_y],
                z=[nozzle_z],
                mode='markers',
                marker=dict(
                    size=8,
                    color='rgb(150, 150, 150)',
                    symbol='square',
                    line=dict(width=1, color='rgb(100, 100, 100)')
                ),
                name='Print Head',
                hovertemplate='Print Head<extra></extra>'
            ))
            
            # 4. Simple progress text
            progress_text = f"Layer {i+1} / {len(display_layers)}"
            
            frame_data.append(go.Scatter3d(
                x=[bounds[1][0] + 5],
                y=[bounds[1][1] + 5],
                z=[current_z + 2],
                mode='text',
                text=[progress_text],
                textposition='middle center',
                textfont=dict(size=10, color='rgb(60, 60, 60)'),
                name='Progress',
                showlegend=False
            ))
            
            # Create frame
            frame = go.Frame(
                data=frame_data,
                name=str(i)
            )
            frames.append(frame)
        
        # Initial frame
        initial_data = []
        
        # Build platform
        platform_size = max(bounds[1][0] - bounds[0][0], bounds[1][1] - bounds[0][1]) * 1.1
        platform_z = bounds[0][2] - 1
        
        initial_data.append(go.Mesh3d(
            x=[bounds[0][0] - platform_size/6, bounds[1][0] + platform_size/6, 
               bounds[1][0] + platform_size/6, bounds[0][0] - platform_size/6],
            y=[bounds[0][1] - platform_size/6, bounds[0][1] - platform_size/6, 
               bounds[1][1] + platform_size/6, bounds[1][1] + platform_size/6],
            z=[platform_z, platform_z, platform_z, platform_z],
            i=[0, 1], j=[1, 2], k=[2, 3],
            color='rgb(120, 120, 120)',
            opacity=0.4,
            name='Print Bed',
            showscale=False
        ))
        
        # Print head at start position
        initial_data.append(go.Scatter3d(
            x=[bounds[0][0] + (bounds[1][0] - bounds[0][0]) * 0.8],
            y=[bounds[0][1] + (bounds[1][1] - bounds[0][1]) * 0.2],
            z=[z_positions[0] + 3],
            mode='markers',
            marker=dict(
                size=8,
                color='rgb(150, 150, 150)',
                symbol='square',
                line=dict(width=1, color='rgb(100, 100, 100)')
            ),
            name='Print Head',
            hovertemplate='Print Head<extra></extra>'
        ))
        
        fig = go.Figure(data=initial_data, frames=frames)
        
        # Simple, clean layout
        fig.update_layout(
            scene=dict(
                xaxis_title='X (mm)',
                yaxis_title='Y (mm)',
                zaxis_title='Z (mm)',
                aspectmode='data',
                bgcolor='rgb(250, 250, 250)',
                camera=dict(eye=dict(x=1.3, y=1.3, z=1.3))
            ),
            title='3D Printing Process - Layer by Layer Construction',
            updatemenus=[{
                'type': 'buttons',
                'showactive': False,
                'x': 0.1,
                'y': 0.9,
                'buttons': [
                    {
                        'label': '▶ Play',
                        'method': 'animate',
                        'args': [None, {
                            'frame': {'duration': 2000, 'redraw': True},  # 2 seconds per layer
                            'fromcurrent': True,
                            'transition': {'duration': 500}
                        }]
                    },
                    {
                        'label': '⏸ Pause',
                        'method': 'animate',
                        'args': [[None], {
                            'frame': {'duration': 0, 'redraw': False},
                            'mode': 'immediate'
                        }]
                    }
                ]
            }],
            sliders=[{
                'steps': [
                    {
                        'args': [[str(i)], {
                            'frame': {'duration': 500, 'redraw': True},
                            'mode': 'immediate'
                        }],
                        'label': f'Layer {i+1}',
                        'method': 'animate'
                    }
                    for i in range(len(display_layers))
                ],
                'active': 0,
                'currentvalue': {'prefix': 'Layer: '},
                'x': 0.1,
                'len': 0.8
            }],
            width=900,
            height=700,
            paper_bgcolor='rgb(255, 255, 255)',
            plot_bgcolor='rgb(255, 255, 255)'
        )
        
        return fig
    
    def create_layer_by_layer_animation(self, max_layers: int = 50) -> go.Figure:
        """
        Create the original technical layer-by-layer animation.
        For educational purposes, use create_educational_printing_animation() instead.
        """
        return self.create_simple_printing_animation(max_layers)
    
    def create_print_path_visualization(self, layer_index: int = 0) -> go.Figure:
        """
        Create visualization of print paths for a specific layer.
        
        Args:
            layer_index: Index of layer to visualize
            
        Returns:
            Plotly figure showing print paths
        """
        if not self.layers or layer_index >= len(self.layers):
            raise ValueError("Invalid layer index or no layer data.")
        
        layer = self.layers[layer_index]
        z_height = layer['z_height']
        
        # Generate simulated print paths
        paths = self._generate_print_paths(layer)
        
        fig = go.Figure()
        
        if paths:
            # Perimeter paths
            if 'perimeter' in paths:
                perimeter = paths['perimeter']
                fig.add_trace(go.Scatter3d(
                    x=perimeter[:, 0],
                    y=perimeter[:, 1],
                    z=perimeter[:, 2],
                    mode='lines',
                    line=dict(color='blue', width=4),
                    name='Perimeter'
                ))
            
            # Infill paths
            if 'infill' in paths:
                infill = paths['infill']
                fig.add_trace(go.Scatter3d(
                    x=infill[:, 0],
                    y=infill[:, 1],
                    z=infill[:, 2],
                    mode='lines',
                    line=dict(color='orange', width=2),
                    name='Infill'
                ))
        
        # Add layer outline
        if self.mesh:
            outline = self._get_layer_outline(z_height)
            if outline is not None:
                fig.add_trace(go.Scatter3d(
                    x=outline[:, 0],
                    y=outline[:, 1],
                    z=outline[:, 2],
                    mode='lines',
                    line=dict(color='black', width=3),
                    name='Layer Outline'
                ))
        
        fig.update_layout(
            scene=dict(
                xaxis_title='X (mm)',
                yaxis_title='Y (mm)',
                zaxis_title='Z (mm)',
                aspectmode='data'
            ),
            title=f'Print Paths - Layer {layer_index + 1} (Z = {z_height:.2f}mm)',
            width=800,
            height=600
        )
        
        return fig
    
    def create_printing_analytics_dashboard(self, analysis_results: Dict) -> go.Figure:
        """
        Create comprehensive analytics dashboard for the print.
        
        Args:
            analysis_results: Complete FDM analysis results
            
        Returns:
            Multi-panel dashboard figure
        """
        # Extract metrics
        rl_metrics = analysis_results['rl_metrics']
        time_data = analysis_results['detailed_analysis']['time_analysis']
        material_data = analysis_results['detailed_analysis']['material_analysis']
        quality_data = analysis_results['detailed_analysis']['quality_analysis']
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Cost Breakdown', 
                'Time Distribution',
                'Quality Metrics',
                'Material Usage'
            ],
            specs=[
                [{'type': 'pie'}, {'type': 'bar'}],
                [{'type': 'bar'}, {'type': 'pie'}]
            ]
        )
        
        # Cost breakdown pie chart
        cost_breakdown = rl_metrics['manufacturing_cost']
        cost_data = analysis_results['detailed_analysis']['cost_analysis']['cost_breakdown']
        
        fig.add_trace(go.Pie(
            labels=['Material', 'Machine', 'Labor', 'Energy', 'Failure Risk'],
            values=[
                cost_data['material_cost'],
                cost_data['machine_cost'], 
                cost_data['labor_cost'],
                cost_data['energy_cost'],
                cost_data['failure_cost']
            ],
            name="Cost"
        ), row=1, col=1)
        
        # Time distribution
        time_breakdown = time_data['breakdown']
        fig.add_trace(go.Bar(
            x=['Print', 'Travel', 'Heating', 'Layer Changes'],
            y=[
                time_breakdown['print_time']/60,
                time_breakdown['travel_time']/60,
                time_breakdown['heating_time']/60,
                time_breakdown['layer_change_time']/60
            ],
            name="Time (min)"
        ), row=1, col=2)
        
        # Quality metrics
        quality_scores = quality_data['scores']
        fig.add_trace(go.Bar(
            x=['Surface Finish', 'Accuracy', 'Overhang', 'Support Impact'],
            y=[
                quality_scores['surface_finish'],
                quality_scores['dimensional_accuracy'],
                quality_scores['overhang_quality'],
                quality_scores['support_impact']
            ],
            name="Quality Score"
        ), row=2, col=1)
        
        # Material usage pie chart
        material_volumes = material_data['volumes']
        fig.add_trace(go.Pie(
            labels=['Part Material', 'Support Material', 'Waste'],
            values=[
                material_volumes['effective_part_volume'],
                material_volumes['support_volume'],
                material_volumes['waste_volume']
            ],
            name="Material"
        ), row=2, col=2)
        
        fig.update_layout(
            title_text="FDM Printing Analytics Dashboard",
            showlegend=False,
            height=600,
            width=1000
        )
        
        return fig
    
    def save_visualization_html(self, fig: go.Figure, filename: str):
        """Save visualization as HTML file."""
        fig.write_html(filename)
        print(f"Visualization saved to: {filename}")
    
    def _extract_support_regions(self, support_data: Dict) -> List:
        """Extract support regions from support analysis data."""
        # This would be implemented based on the support analysis results
        # For now, return empty list
        return []
    
    def _generate_support_visualization(self) -> Optional[np.ndarray]:
        """Generate support structure visualization points."""
        if not self.mesh or not self.support_regions:
            return None
        
        # Generate random support points for demonstration
        bounds = self.mesh.bounds
        n_points = 100
        
        x = np.random.uniform(bounds[0][0], bounds[1][0], n_points)
        y = np.random.uniform(bounds[0][1], bounds[1][1], n_points)
        z = np.random.uniform(bounds[0][2], bounds[1][2] * 0.8, n_points)
        
        return np.column_stack([x, y, z])
    
    def _create_layer_visualization_data(self, z_positions: List[float]) -> Dict:
        """Create visualization data for layers at given Z positions."""
        if not self.mesh:
            return {'x': [], 'y': [], 'z': []}
        
        bounds = self.mesh.bounds
        points_per_layer = 200
        
        all_x, all_y, all_z = [], [], []
        
        for z in z_positions:
            # Generate points within the mesh bounds for this layer
            n_points = int(points_per_layer * (1 - z / bounds[1][2]) + 20)  # Fewer points at top
            
            # Create circular pattern for demonstration
            angles = np.linspace(0, 2*np.pi, n_points)
            radius = min(bounds[1][0] - bounds[0][0], bounds[1][1] - bounds[0][1]) / 3
            
            x = bounds[0][0] + (bounds[1][0] - bounds[0][0])/2 + radius * np.cos(angles) * np.random.uniform(0.3, 1.0, n_points)
            y = bounds[0][1] + (bounds[1][1] - bounds[0][1])/2 + radius * np.sin(angles) * np.random.uniform(0.3, 1.0, n_points)
            z_layer = np.full(n_points, z)
            
            all_x.extend(x)
            all_y.extend(y)
            all_z.extend(z_layer)
        
        return {'x': all_x, 'y': all_y, 'z': all_z}
    
    def _create_real_layer_meshes(self, z_positions: List[float]) -> List[Optional[Dict]]:
        """
        Create actual filled mesh cross-sections for the given Z positions.
        
        Args:
            z_positions: List of Z heights to create cross-sections at
            
        Returns:
            List of mesh data dictionaries or None for each position
        """
        if not self.mesh:
            return [None] * len(z_positions)
        
        layer_meshes = []
        
        for z_height in z_positions:
            try:
                # Create cross-section at this height
                section = self.mesh.section(plane_origin=[0, 0, z_height], plane_normal=[0, 0, 1])
                
                if section is not None:
                    # Handle Path3D objects (common for simple shapes like cubes)
                    if hasattr(section, 'discrete') and callable(section.discrete):
                        # Get discretized path points
                        try:
                            path_points = section.discrete[0]  # Get first path
                            if len(path_points) >= 4:  # Need at least 4 points for a closed shape
                                # Create a simple filled rectangle/polygon
                                layer_thickness = 0.2
                                
                                # Bottom vertices
                                bottom_vertices = np.column_stack([
                                    path_points[:, 0],
                                    path_points[:, 1],
                                    np.full(len(path_points), z_height - layer_thickness/2)
                                ])
                                
                                # Top vertices  
                                top_vertices = np.column_stack([
                                    path_points[:, 0],
                                    path_points[:, 1],
                                    np.full(len(path_points), z_height + layer_thickness/2)
                                ])
                                
                                # Combine vertices
                                vertices = np.vstack([bottom_vertices, top_vertices])
                                
                                # Create faces
                                faces = []
                                n_vertices = len(path_points)
                                
                                # Bottom face (fan triangulation from first vertex)
                                for i in range(1, n_vertices - 1):
                                    faces.append([0, i, i + 1])
                                
                                # Top face (fan triangulation, reversed)
                                for i in range(1, n_vertices - 1):
                                    faces.append([n_vertices, n_vertices + i + 1, n_vertices + i])
                                
                                # Side faces
                                for i in range(n_vertices):
                                    next_i = (i + 1) % n_vertices
                                    faces.extend([
                                        [i, next_i, n_vertices + i],
                                        [next_i, n_vertices + next_i, n_vertices + i]
                                    ])
                                
                                layer_meshes.append({
                                    'vertices': vertices,
                                    'faces': np.array(faces)
                                })
                            else:
                                layer_meshes.append(None)
                        except:
                            layer_meshes.append(None)
                    
                    # Try to get filled polygon from section
                    elif hasattr(section, 'polygons_full') and len(section.polygons_full) > 0:
                        # Use filled polygons for better visualization
                        combined_vertices = []
                        combined_faces = []
                        vertex_offset = 0
                        
                        layer_thickness = 0.2  # Thickness for visualization
                        
                        for polygon in section.polygons_full:
                            if len(polygon.vertices) >= 3:
                                # Bottom vertices
                                bottom_verts = np.column_stack([
                                    polygon.vertices[:, 0],
                                    polygon.vertices[:, 1],
                                    np.full(len(polygon.vertices), z_height - layer_thickness/2)
                                ])
                                
                                # Top vertices
                                top_verts = np.column_stack([
                                    polygon.vertices[:, 0],
                                    polygon.vertices[:, 1],
                                    np.full(len(polygon.vertices), z_height + layer_thickness/2)
                                ])
                                
                                # Combine vertices
                                vertices = np.vstack([bottom_verts, top_verts])
                                combined_vertices.append(vertices)
                                
                                # Create faces for this polygon
                                n_verts = len(polygon.vertices)
                                
                                # Bottom face (triangulated)
                                for i in range(1, n_verts - 1):
                                    combined_faces.append([
                                        vertex_offset,
                                        vertex_offset + i,
                                        vertex_offset + i + 1
                                    ])
                                
                                # Top face (triangulated, reversed for correct normal)
                                for i in range(1, n_verts - 1):
                                    combined_faces.append([
                                        vertex_offset + n_verts,
                                        vertex_offset + n_verts + i + 1,
                                        vertex_offset + n_verts + i
                                    ])
                                
                                # Side faces
                                for i in range(n_verts):
                                    next_i = (i + 1) % n_verts
                                    
                                    # Two triangles for each side
                                    combined_faces.extend([
                                        [vertex_offset + i, vertex_offset + next_i, vertex_offset + n_verts + i],
                                        [vertex_offset + next_i, vertex_offset + n_verts + next_i, vertex_offset + n_verts + i]
                                    ])
                                
                                vertex_offset += len(vertices)
                        
                        if combined_vertices:
                            all_vertices = np.vstack(combined_vertices)
                            all_faces = np.array(combined_faces)
                            
                            layer_meshes.append({
                                'vertices': all_vertices,
                                'faces': all_faces
                            })
                        else:
                            layer_meshes.append(None)
                    
                    # Fallback to outline method if no filled polygons
                    elif hasattr(section, 'vertices') and len(section.vertices) > 2:
                        # Create a simple filled layer from outline
                        layer_thickness = 0.2
                        
                        # Bottom vertices
                        bottom_vertices = np.column_stack([
                            section.vertices[:, 0],
                            section.vertices[:, 1],
                            np.full(len(section.vertices), z_height - layer_thickness/2)
                        ])
                        
                        # Top vertices  
                        top_vertices = np.column_stack([
                            section.vertices[:, 0],
                            section.vertices[:, 1],
                            np.full(len(section.vertices), z_height + layer_thickness/2)
                        ])
                        
                        # Combine vertices
                        vertices = np.vstack([bottom_vertices, top_vertices])
                        
                        # Create faces
                        faces = []
                        n_vertices = len(section.vertices)
                        
                        # Bottom face (fan triangulation)
                        for i in range(1, n_vertices - 1):
                            faces.append([0, i, i + 1])
                        
                        # Top face (fan triangulation, reversed)
                        for i in range(1, n_vertices - 1):
                            faces.append([n_vertices, n_vertices + i + 1, n_vertices + i])
                        
                        # Side faces
                        for i in range(n_vertices):
                            next_i = (i + 1) % n_vertices
                            faces.extend([
                                [i, next_i, n_vertices + i],
                                [next_i, n_vertices + next_i, n_vertices + i]
                            ])
                        
                        layer_meshes.append({
                            'vertices': vertices,
                            'faces': np.array(faces)
                        })
                    else:
                        layer_meshes.append(None)
                else:
                    layer_meshes.append(None)
                    
            except Exception as e:
                print(f"Warning: Could not create layer mesh at z={z_height}: {e}")
                layer_meshes.append(None)
        
        return layer_meshes
    
    def _create_layer_outlines(self, z_positions: List[float]) -> Optional[Dict]:
        """
        Create 2D outlines for layers as a fallback visualization.
        
        Args:
            z_positions: List of Z heights to create outlines at
            
        Returns:
            Dictionary with x, y, z coordinates for line visualization
        """
        if not self.mesh:
            return None
        
        all_x, all_y, all_z = [], [], []
        
        for z_height in z_positions:
            try:
                # Create cross-section at this height
                section = self.mesh.section(plane_origin=[0, 0, z_height], plane_normal=[0, 0, 1])
                
                if section is not None and hasattr(section, 'vertices'):
                    # Get the outline vertices
                    vertices = section.vertices
                    
                    if len(vertices) > 0:
                        # Create outline by connecting vertices
                        outline_x = vertices[:, 0].tolist()
                        outline_y = vertices[:, 1].tolist()
                        outline_z = [z_height] * len(vertices)
                        
                        # Close the outline by connecting back to first point
                        if len(outline_x) > 2:
                            outline_x.append(outline_x[0])
                            outline_y.append(outline_y[0])
                            outline_z.append(z_height)
                        
                        all_x.extend(outline_x)
                        all_y.extend(outline_y)
                        all_z.extend(outline_z)
                        
                        # Add separator (NaN) between different layers
                        if z_height != z_positions[-1]:
                            all_x.append(np.nan)
                            all_y.append(np.nan)
                            all_z.append(np.nan)
                        
            except Exception as e:
                print(f"Warning: Could not create layer outline at z={z_height}: {e}")
                continue
        
        if all_x:
            return {'x': all_x, 'y': all_y, 'z': all_z}
        else:
            return None
    
    def _generate_print_paths(self, layer: Dict) -> Dict:
        """Generate simulated print paths for a layer."""
        if not self.mesh:
            return {}
        
        z_height = layer['z_height']
        bounds = self.mesh.bounds
        
        paths = {}
        
        # Generate perimeter path (simplified rectangular)
        perimeter_x = [bounds[0][0], bounds[1][0], bounds[1][0], bounds[0][0], bounds[0][0]]
        perimeter_y = [bounds[0][1], bounds[0][1], bounds[1][1], bounds[1][1], bounds[0][1]]
        perimeter_z = [z_height] * 5
        
        paths['perimeter'] = np.column_stack([perimeter_x, perimeter_y, perimeter_z])
        
        # Generate infill paths (simple grid)
        n_lines = 5
        infill_x, infill_y, infill_z = [], [], []
        
        for i in range(n_lines):
            x_pos = bounds[0][0] + (bounds[1][0] - bounds[0][0]) * (i + 1) / (n_lines + 1)
            infill_x.extend([x_pos, x_pos])
            infill_y.extend([bounds[0][1], bounds[1][1]])
            infill_z.extend([z_height, z_height])
        
        paths['infill'] = np.column_stack([infill_x, infill_y, infill_z])
        
        return paths
    
    def _get_layer_outline(self, z_height: float) -> Optional[np.ndarray]:
        """Get outline of mesh at given Z height."""
        if not self.mesh:
            return None
        
        try:
            # Create cross-section
            section = self.mesh.section(plane_origin=[0, 0, z_height], plane_normal=[0, 0, 1])
            
            if section is not None and hasattr(section, 'vertices'):
                # Add Z coordinate
                outline = np.column_stack([
                    section.vertices[:, 0],
                    section.vertices[:, 1],
                    np.full(len(section.vertices), z_height)
                ])
                return outline
        except:
            pass
        
        return None


def create_interactive_visualization_app(simulator, file_path: str):
    """
    Create an interactive visualization application.
    
    Args:
        simulator: FDMSimulator instance
        file_path: Path to STL file
    """
    print("Creating interactive FDM visualization...")
    
    # Load and analyze
    if not simulator.load_stl(file_path):
        print("Failed to load STL file")
        return
    
    # Run analysis
    results = simulator.run_complete_analysis()
    
    # Create visualizer
    visualizer = FDMVisualizer()
    visualizer.load_mesh_data(
        simulator.mesh, 
        simulator.layers,
        results['detailed_analysis']['geometry']['overhang_analysis']
    )
    
    # Generate visualizations
    print("Generating 3D mesh view...")
    mesh_fig = visualizer.create_3d_mesh_view()
    
    print("Generating layer animation...")
    animation_fig = visualizer.create_layer_by_layer_animation(max_layers=20)
    
    print("Generating print path visualization...")
    if simulator.layers:
        path_fig = visualizer.create_print_path_visualization(len(simulator.layers)//2)
    else:
        path_fig = None
    
    print("Generating analytics dashboard...")
    dashboard_fig = visualizer.create_printing_analytics_dashboard(results)
    
    # Save visualizations
    visualizer.save_visualization_html(mesh_fig, "fdm_mesh_view.html")
    visualizer.save_visualization_html(animation_fig, "fdm_layer_animation.html")
    if path_fig:
        visualizer.save_visualization_html(path_fig, "fdm_print_paths.html")
    visualizer.save_visualization_html(dashboard_fig, "fdm_analytics_dashboard.html")
    
    print("\nVisualization files created:")
    print("- fdm_mesh_view.html")
    print("- fdm_layer_animation.html")
    print("- fdm_print_paths.html")
    print("- fdm_analytics_dashboard.html")
    
    return {
        'mesh_view': mesh_fig,
        'animation': animation_fig,
        'print_paths': path_fig,
        'dashboard': dashboard_fig
    }


if __name__ == "__main__":
    # Example usage
    from fdm_simulation import FDMSimulator
    
    simulator = FDMSimulator()
    create_interactive_visualization_app(simulator, "testcases/simple/cube.stl")