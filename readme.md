Problems to be fixed: 
add a mesh repair functions
# CNC Manufacturability Analyzer

A modular Python framework for analyzing STL files for CNC manufacturability issues.

## Features

- **Modular Architecture**: Each analysis function is in its own module
- **Context-Aware Analysis**: Smart detection that ignores false positives
- **Interactive Web Interface**: Streamlit-based UI for easy file upload and analysis
- **Comprehensive Reporting**: HTML, JSON, and Markdown report generation
- **3D Visualization**: Interactive Plotly visualizations with problem highlighting
- **Test Framework**: Built-in testing system for validating analysis functions

## Analysis Modules

1. **undercut_check.py**: Detects surfaces that can't be machined from standard directions
2. **internal_volumes_check.py**: Finds enclosed spaces that can't be accessed
3. **steep_walls_check.py**: Identifies problematic vertical walls in deep pockets
4. **narrow_channels_check.py**: Detects channels too narrow for standard tools
5. **small_features_check.py**: Finds features smaller than minimum tool size
6. **deep_pockets_check.py**: Identifies pockets that may be too deep for standard tools
7. **geometric_context.py**: Provides context-aware analysis helpers

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### 1. Web Interface (Recommended)

```bash
streamlit run app.py
```

Then:
- Upload your STL file
- Configure analysis parameters
- Select which analyses to run
- View results and download reports

### 2. Command Line

```python
from cnc_analyzer import CNCAnalyzer

# Create analyzer
analyzer = CNCAnalyzer()

# Load mesh
analyzer.load_mesh("your_part.stl")

# Run single analysis
result = analyzer.analyze_single_function("undercuts")

# Run all analyses
results = analyzer.analyze_all()

# Get score
score = analyzer.calculate_score()
print(f"CNC Manufacturability Score: {score}/100")
```

### 3. Test Framework

```python
from test_framework import TestFramework

# Create tester
tester = TestFramework()

# Create synthetic test cases
tester.create_test_cases()

# Run tests on all cases
results = tester.test_all_cases()

# Generate comparison report
summary = tester.generate_comparison_report(results)
```

## Configuration

Default configuration in `cnc_analyzer.py`:

```python
{
    'min_tool_diameter': 3.0,      # mm
    'min_channel_width': 2.0,      # mm
    'steep_angle_threshold': 80.0,  # degrees
    'deep_pocket_threshold': 30.0,  # mm
    'min_depth': 5.0,              # mm
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
```

## Scoring System

- **90-100**: Excellent - Perfect for standard CNC
- **80-89**: Good - Minor issues, easily machinable
- **70-79**: Fair - Some challenges, may need special tools
- **50-69**: Difficult - Requires advanced CNC or redesign
- **0-49**: Very Difficult - Major redesign recommended

## Adding Test Cases

Place STL files in the `test_cases` directory and run:

```python
tester = TestFramework("test_cases")
results = tester.test_all_cases()
```

## Report Types

1. **HTML Report**: Comprehensive report with visualizations
2. **JSON Report**: Machine-readable format for integration
3. **Markdown Report**: Human-readable text format

## Context-Aware Analysis

The analyzer includes smart detection that:
- Ignores external surfaces (they're good for CNC)
- Checks tool accessibility from multiple directions
- Considers geometric context before flagging issues
- Reduces false positives from mesh tessellation

## Extending the Framework

To add a new analysis:

1. Create a new module (e.g., `new_check.py`)
2. Implement analysis function following the pattern:
   ```python
   def analyze_new_feature(mesh, **kwargs):
       return {
           'count': count,
           'indices': indices,
           'has_problem': bool,
           'severity': level,
           'data': metadata
       }
   ```
3. Add to `CNCAnalyzer.analyze_single_function()`
4. Update scoring logic in `calculate_score()`



## citation 
@software{trimesh,
	author = {{Dawson-Haggerty et al.}},
	title = {trimesh},
	url = {https://trimesh.org/},
	version = {3.2.0},
	date = {2019-12-8},
}
