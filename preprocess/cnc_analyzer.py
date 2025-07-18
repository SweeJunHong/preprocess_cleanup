import numpy as np
import trimesh
from undercut_check import analyze_undercuts
from internal_volumes_check import analyze_internal_volumes
from small_features_check import analyze_small_features
from steep_walls_check import analyze_steep_walls
from narrow_channels_check import analyze_narrow_channels
from deep_pockets_check import analyze_deep_pockets

class CNCAnalyzer:
    """Main analyzer class for CNC manufacturability."""
    
    def __init__(self, config=None):
        """
        Initialize analyzer with configuration.
        
        Args:
            config: dict with analysis parameters
        """
        self.config = config or self.get_default_config()
        self.results = {}
        
    @staticmethod
    def get_default_config():
        """Get default configuration for analysis."""
        return {
            'min_tool_diameter': 3.0,  # mm
            'min_channel_width': 2.0,  # mm
            'steep_angle_threshold': 80.0,  # degrees
            'deep_pocket_threshold': 30.0,  # mm
            'min_depth': 5.0,  # mm
            'use_context_aware': True,
            'analysis_methods': {
                'undercuts': True,
                'internal_volumes': True,
                'small_features': True,
                'steep_walls': True,
                'narrow_channels': True,
                'deep_pockets': True
            }
        }
    
    def load_mesh(self, file_path):
        """Load STL file."""
        try:
            self.mesh = trimesh.load(file_path)
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False
    
    def analyze_single_function(self, function_name):
        """Analyze using a single function."""
        if not hasattr(self, 'mesh'):
            raise ValueError("No mesh loaded. Call load_mesh() first.")
        
        results = {}
        
        if function_name == 'undercuts':
            results = analyze_undercuts(
                self.mesh, 
                use_context=self.config['use_context_aware']
            )
        elif function_name == 'internal_volumes':
            results = analyze_internal_volumes(
                self.mesh,
                use_context=self.config['use_context_aware']
            )
        elif function_name == 'small_features':
            results = analyze_small_features(
                self.mesh,
                min_tool_diameter=self.config['min_tool_diameter'],
                use_realistic=True
            )
        elif function_name == 'steep_walls':
            results = analyze_steep_walls(
                self.mesh,
                angle_threshold=self.config['steep_angle_threshold'],
                min_depth=self.config['min_depth'],
                use_context=self.config['use_context_aware']
            )
        elif function_name == 'narrow_channels':
            results = analyze_narrow_channels(
                self.mesh,
                min_channel_width=self.config['min_channel_width'],
                use_context=self.config['use_context_aware']
            )
        elif function_name == 'deep_pockets':
            results = analyze_deep_pockets(
                self.mesh,
                depth_threshold=self.config['deep_pocket_threshold'],
                method='ray'
            )
        else:
            raise ValueError(f"Unknown function: {function_name}")
        
        self.results[function_name] = results
        return results
    
    def analyze_all(self):
        """Run complete analysis."""
        if not hasattr(self, 'mesh'):
            raise ValueError("No mesh loaded. Call load_mesh() first.")
        
        for function_name, enabled in self.config['analysis_methods'].items():
            if enabled:
                try:
                    self.analyze_single_function(function_name)
                except Exception as e:
                    print(f"Error in {function_name}: {e}")
                    self.results[function_name] = {'error': str(e)}
        
        return self.results
    
    # In cnc_analyzer.py
    def calculate_score(self):
        """Modified scoring system with higher penalties for deep pockets"""
        score = 100
        penalties = {
            'undercuts': {'base': 40, 'per_face': 0.8},  # Increased penalties
            'internal_volumes': {0: 0, 1: 15, 2: 35},
            'small_features': {0: 0, 1: 5, 2: 10},
            'steep_walls': {'base': 20, 'per_face': 0.4},
            'narrow_channels': {'base': 30, 'per_face': 0.5},
            'deep_pockets': {'base': 40, 'per_face': 1.0}  # Much higher penalty
        }

        
        # Calculate penalties
        if 'undercuts' in self.results:
            count = self.results['undercuts'].get('count', 0)
            penalty = min(penalties['undercuts']['base'], 
                         count * penalties['undercuts']['per_face'])
            score -= penalty
        
        if 'internal_volumes' in self.results:
            severity = self.results['internal_volumes'].get('severity', 0)
            score -= penalties['internal_volumes'].get(severity, 0)
        
        if 'small_features' in self.results:
            severity = self.results['small_features'].get('severity', 0)
            score -= penalties['small_features'].get(severity, 0)
        
        if 'steep_walls' in self.results:
            count = self.results['steep_walls'].get('count', 0)
            penalty = min(penalties['steep_walls']['base'],
                         count * penalties['steep_walls']['per_face'])
            score -= penalty
        
        if 'narrow_channels' in self.results:
            count = self.results['narrow_channels'].get('count', 0)
            penalty = min(penalties['narrow_channels']['base'],
                         count * penalties['narrow_channels']['per_face'])
            score -= penalty
        
        if 'deep_pockets' in self.results:
            count = self.results['deep_pockets'].get('count', 0)
            penalty = min(penalties['deep_pockets']['base'],
                         count * penalties['deep_pockets']['per_face'])
            score -= penalty
        
        return max(0, score)
    
    def get_problem_regions(self):
        """Get all problem regions for visualization."""
        problem_regions = []
        
        if 'undercuts' in self.results and self.results['undercuts']['count'] > 0:
            problem_regions.append(("Undercuts", self.results['undercuts']['indices']))
        
        if 'internal_volumes' in self.results and self.results['internal_volumes']['severity'] > 0:
            problem_regions.append(("Internal Volumes", []))
        
        if 'steep_walls' in self.results and self.results['steep_walls']['count'] > 0:
            problem_regions.append(("Steep Walls", self.results['steep_walls']['indices']))
        
        if 'narrow_channels' in self.results and self.results['narrow_channels']['count'] > 0:
            problem_regions.append(("Narrow Channels", self.results['narrow_channels']['indices']))
        
        if 'deep_pockets' in self.results and self.results['deep_pockets']['count'] > 0:
            problem_regions.append(("Deep Pockets", self.results['deep_pockets']['indices']))
        
        return problem_regions