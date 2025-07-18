# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a CNC Manufacturability Analyzer - a Python framework for analyzing STL files to identify manufacturing issues before CNC machining. The system uses modular analysis functions to detect problems like undercuts, internal volumes, steep walls, narrow channels, small features, and deep pockets.

## Development Commands

### Environment Setup
```bash
pip install -r requirements.txt
```

### Running the Application
```bash
# Web interface (recommended)
streamlit run app.py

# Direct Python usage
python -c "from cnc_analyzer import CNCAnalyzer; analyzer = CNCAnalyzer(); analyzer.load_mesh('part.stl'); results = analyzer.analyze_all()"
```

### Mesh Repair
If meshes are not watertight, the system automatically attempts repair using the `repair_mesh()` function in `mesh_utils.py`.

## Architecture

### Core Components

**CNCAnalyzer (`cnc_analyzer.py`)**
- Main orchestrator class that coordinates all analysis modules
- Handles configuration, mesh loading, and result aggregation
- Calculates overall manufacturability score (0-100)

**Analysis Modules**
Each analysis is in its own module following a consistent pattern:
- `undercut_check.py` - Detects surfaces inaccessible from standard machining directions
- `internal_volumes_check.py` - Finds enclosed spaces that can't be accessed by tools
- `steep_walls_check.py` - Identifies problematic vertical walls in deep pockets
- `narrow_channels_check.py` - Detects channels too narrow for standard tools
- `small_features_check.py` - Finds features smaller than minimum tool size
- `deep_pockets_check.py` - Identifies pockets too deep for standard tools

**Support Modules**
- `geometric_context.py` - Context-aware analysis helpers to reduce false positives
- `mesh_utils.py` - Mesh processing utilities including repair functions
- `visualization.py` - 3D visualization using Plotly
- `report_generator.py` - HTML, JSON, and Markdown report generation

**User Interface**
- `app.py` - Streamlit web interface with interactive controls and real-time visualization

### Analysis Function Pattern

All analysis functions return a standardized result dictionary:
```python
{
    'count': int,           # Number of issues found
    'indices': list,        # Face/vertex indices of problems
    'has_problem': bool,    # Whether issues were detected
    'severity': int,        # 0=None, 1=Minor, 2=Major
    'data': dict           # Additional metadata
}
```

### Configuration

Default analysis parameters in `CNCAnalyzer.get_default_config()`:
- `min_tool_diameter`: 3.0 mm
- `min_channel_width`: 2.0 mm  
- `steep_angle_threshold`: 80.0 degrees
- `deep_pocket_threshold`: 30.0 mm
- `use_context_aware`: True (reduces false positives)

### Test Cases

STL test files are organized in `testcases/` directory:
- `simple/` - Basic shapes (cube, cylinder, sphere)
- `moderate/` - Standard parts (bracket, cone)
- `difficult/` - Complex geometries (t-slot, undercut bottle, vase)
- `undercut/` - Specific undercut test cases

## Key Dependencies

- **trimesh** - Core 3D mesh processing and STL loading
- **numpy** - Numerical computations and geometry calculations
- **plotly** - Interactive 3D visualization
- **streamlit** - Web interface framework
- **scipy** - Advanced mathematical operations (auto-installed with trimesh)

## Adding New Analysis Modules

1. Create new module (e.g., `new_check.py`) with analysis function
2. Import and add to `CNCAnalyzer.analyze_single_function()`
3. Update scoring logic in `CNCAnalyzer.calculate_score()`
4. Follow the standard return format for consistency

## Known Issues

From development notes in `app.py:278-284`:
- Dovetail joints may be detected as small features instead of undercuts
- Deep T-slot geometries may not trigger deep pocket detection as expected
- Scoring system may rate some complex geometries as more manufacturable than expected