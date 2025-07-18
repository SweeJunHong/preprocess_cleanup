# FDM Visual Simulation System

## 🎯 Overview

Complete FDM additive manufacturing simulation system with comprehensive visual feedback, designed for generating training data for reinforcement learning models. The system analyzes STL files and provides:

- **5 Key RL Training Metrics**: Manufacturing cost, time to completion, quality metrics, material waste, post-processing requirements
- **Interactive 3D Visualizations**: Mesh views, layer-by-layer animations, print paths, support structures
- **Analytics Dashboards**: Cost breakdowns, time analysis, quality assessments
- **Multiple Interfaces**: Command-line, web interface, Python API

## 📊 System Capabilities

### Core FDM Simulation (Phases 1-3 ✅)

**Phase 1: Foundation**
- ✅ STL loading and mesh analysis
- ✅ Geometry extraction (volume, surface area, complexity)
- ✅ Layer-by-layer slicing algorithm

**Phase 2: Core Simulation** 
- ✅ Print time calculation (heating, printing, travel, layer changes)
- ✅ Material usage analysis (filament consumption, support material, waste)
- ✅ Quality assessment (surface finish, dimensional accuracy, overhang quality)

**Phase 3: Advanced Metrics**
- ✅ Comprehensive cost modeling (materials, machine time, labor, failure probability)
- ✅ Post-processing requirements (support removal, surface finishing, complexity)

### Visual Simulation Features ✅

**3D Visualizations**
- ✅ Interactive 3D mesh viewer with support structure overlay
- ✅ Layer-by-layer printing animation with controls
- ✅ Print path visualization showing perimeters and infill
- ✅ Support structure visualization

**Analytics & Dashboards**
- ✅ Multi-panel analytics dashboard (cost, time, quality, materials)
- ✅ Comparison reports for multiple parts
- ✅ Batch analysis capabilities
- ✅ Interactive charts and metrics

## 🚀 Usage

### Command Line Interface

```bash
# Analyze single file
python run_fdm_visual_simulation.py path/to/file.stl

# Analyze without opening browser
python run_fdm_visual_simulation.py path/to/file.stl nobrowser

# Interactive mode
python run_fdm_visual_simulation.py
```

### Web Interface

```bash
# Launch Streamlit web app
streamlit run fdm_web_interface.py
```

### Python API

```python
from fdm_simulation import FDMSimulator
from fdm_visualization import FDMVisualizer

# Create simulator
simulator = FDMSimulator()

# Load and analyze
simulator.load_stl("part.stl")
results = simulator.run_complete_analysis()

# Get RL training metrics
rl_metrics = results['rl_metrics']
print(f"Cost: ${rl_metrics['manufacturing_cost']:.2f}")
print(f"Time: {rl_metrics['time_to_completion']:.1f} hours")

# Create visualizations
visualizer = FDMVisualizer()
visualizer.load_mesh_data(simulator.mesh, simulator.layers)
mesh_fig = visualizer.create_3d_mesh_view()
mesh_fig.write_html("visualization.html")
```

## 📁 Generated Files

### Analysis Output
- **RL Metrics JSON**: Core training data for ML models
- **Complete Analysis JSON**: Detailed simulation results
- **Training Samples**: Formatted data for RL training

### Visualizations
- **3D Mesh View**: Interactive 3D model with support structures
- **Layer Animation**: Animated layer-by-layer printing simulation
- **Print Paths**: Visualization of tool paths for specific layers
- **Analytics Dashboard**: Multi-panel metrics and charts

## 🎯 RL Training Metrics

The system extracts 5 key metrics designed for reinforcement learning:

### 1. Manufacturing Cost ($)
- Material costs (filament consumption)
- Machine time costs (hourly rates)
- Labor costs (setup, removal, post-processing)
- Failure risk costs (probability-based)
- Energy costs (power consumption)

### 2. Time to Completion (hours)
- Print time (layer printing + travel)
- Heating/cooling time
- Post-processing time (support removal, finishing)
- Setup and removal time

### 3. Quality Metrics (0-100 score)
- Surface finish quality (layer visibility, overhangs)
- Dimensional accuracy (tolerances, small features)
- Overhang quality (support effectiveness)
- Support impact on surface quality

### 4. Material Waste (%)
- Filament waste (failed prints, purging)
- Support material percentage
- Total waste calculation

### 5. Post-Processing Requirements
- Time required (hours)
- Complexity score (0-1)
- Skill level required (Beginner/Intermediate/Advanced)
- Tools required (count and types)

## 🔧 Configuration

### Default Print Settings
```python
{
    'layer_height': 0.2,          # mm
    'print_speed': 50,            # mm/s
    'nozzle_diameter': 0.4,       # mm
    'material_cost_per_kg': 25.0, # USD
    'support_threshold': 45,      # degrees
    'infill_percentage': 0.20     # 20%
}
```

### Customization
All parameters can be customized through configuration objects for different materials, printers, and quality requirements.

## 📈 Performance

- **Processing Speed**: < 30 seconds per simple part
- **Scalability**: Batch processing capable
- **Memory Efficient**: Optimized mesh handling
- **Visualization Performance**: Layer animation limited to 20 layers for responsiveness

## 🧪 Testing

### Test Cases Included
- **Simple**: Cube, cylinder, sphere (basic geometries)
- **Moderate**: Bracket, cone (standard parts)
- **Complex**: T-slot, undercut bottle, vase (challenging geometries)

### Validation
- ✅ All 5 RL metrics successfully extracted
- ✅ Visualizations generate correctly
- ✅ Performance meets requirements
- ✅ No GUI dependencies
- ✅ Works with various STL formats

## 🔮 Applications

### Reinforcement Learning
- **Training Data Generation**: Automated analysis of large STL datasets
- **Reward Function Design**: Use quality/cost metrics as RL rewards
- **Policy Learning**: Optimize print parameters for specific objectives

### Manufacturing Optimization
- **Design for Manufacturing**: Early-stage manufacturability assessment
- **Cost Estimation**: Accurate pre-production cost analysis
- **Quality Prediction**: Predict print quality before manufacturing

### Educational & Research
- **Process Understanding**: Visual learning of FDM printing dynamics
- **Parameter Studies**: Systematic analysis of parameter effects
- **Algorithm Development**: Baseline for advanced simulation methods

## 🏆 Success Criteria Met

✅ **Processes simple STL files** (cubes, cylinders, spheres)  
✅ **Outputs all 5 required metrics** for RL training  
✅ **Runs without GUI dependencies** (headless operation)  
✅ **Processing time < 30 seconds** per simple part  
✅ **Visual simulation capabilities** with interactive feedback  
✅ **Multiple interfaces** (CLI, web, API)  
✅ **Comprehensive documentation** and examples  

## 🎉 Ready for RL Training!

The FDM Visual Simulation System is now complete and ready to generate high-quality training data for reinforcement learning models in additive manufacturing optimization.