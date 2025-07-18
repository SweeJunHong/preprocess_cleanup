# Copilot Instructions for preprocess_cleanedup

## Project Overview
- This project analyzes 3D mesh files (STL) for CNC manufacturability using context-aware geometric analysis and interactive 3D/2D visualization.
- The codebase is modular: each manufacturability check (deep pockets, undercuts, etc.) is in its own file under `src/`.
- The main user interface is in `app.py` (Streamlit), which orchestrates file upload, parameter selection, analysis, visualization, and report generation.

## Key Components
- `app.py`: Streamlit UI for uploading STL files, setting parameters, running analysis, and generating reports.
- `cnc_analyzer.py`: Central class for running selected manufacturability checks and aggregating results.
- `*_check.py` (e.g., `deep_pockets_check.py`, `undercut_check.py`): Each file implements a specific geometric analysis function. All checks should be context-aware and modular.
- `geometric_context.py`: Utilities for geometric reasoning, e.g., tool accessibility, orientation, or context-aware checks.
- `visualization.py`: Contains both interactive 3D Plotly visualization and 2D summary chart generation (matplotlib).
- `report_generator.py`: Generates HTML, Markdown, and JSON reports from analysis results and visualizations.
- `testcases/`: STL files for testing, organized by scenario/difficulty.

## Developer Workflows
- **Run the app:**  
  `streamlit run app.py` (activate `itp_venv` first)
- **Add new manufacturability checks:**  
  - Create a new `*_check.py` file with a function that takes a mesh and returns a result dict.
  - Register the function in `cnc_analyzer.py` so it can be called dynamically.
- **Add new test cases:**  
  - Place STL files in `testcases/`.
- **Generate reports:**  
  - Use the UI buttons in `app.py` after analysis to download HTML, Markdown, or JSON reports.

## Project Conventions
- Each check returns a dict with at least: `count`, `severity` (int or string), `has_problem` (bool), and optionally `recommendation`.
- All geometry logic should be context-aware (e.g., tool accessibility, not just face normals).
- Visualization uses per-face coloring and dropdowns for isolating problem regions.
- Reports include mesh info, per-check results, and visualizations.

## Critical Considerations
- **Orientation:** Many checks assume Z is the tool direction. If the part is oriented differently, deep pockets or undercuts may be missed. Consider allowing user-specified or auto-detected tool direction.
- **Thresholds:** All thresholds (e.g., for deep pockets, narrow channels) are user-configurable in the UI. Ensure these are respected in each check.
- **Tool Accessibility:** Checks should simulate tool access, not just geometric dimensions.
- **Performance:** For large meshes, per-face checks can be slow. Consider batching or mesh simplification if extending.
- **Robustness:** Always validate mesh integrity (watertightness, nonzero faces/vertices) before analysis.

## Example Usage
```python
# Run analysis in app.py via Streamlit UI
# Or programmatically:
from cnc_analyzer import CNCAnalyzer
analyzer = CNCAnalyzer(config)
analyzer.mesh = load_stl("testcases/your_part.stl")
analyzer.run_selected_checks()
results = analyzer.results
```

## Key Files/Directories
- `app.py`: Main UI and workflow
- `cnc_analyzer.py`: Analysis orchestration
- `*_check.py`: Individual manufacturability checks
- `visualization.py`: Visualization utilities
- `report_generator.py`: Report generation
- `testcases/`: STL test files
- `requirements.txt`: Python dependencies
- `itp_venv/`: Virtual environment

---

**When adding new features or checks, follow the modular, context-aware pattern and ensure results are compatible with reporting and visualization.**