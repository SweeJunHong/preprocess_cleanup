# additive simulation mvp plan

## project overview
build fdm additive simulation system that takes stl files and outputs manufacturing metrics for RL training

## metrics to extract
- manufacturing cost
- time to completion  
- quality metrics (surface finish, tolerances)
- material waste
- post-processing requirements

## phase 1: foundation (sequential - do first)

### 1.1 environment setup
- [ ] python environment with key libraries
- [ ] install: trimesh, numpy, matplotlib, pyvista (for visualisation)
- [ ] test stl file loading and basic manipulation

### 1.2 stl analysis pipeline
- [ ] build stl parser using trimesh
- [ ] extract basic geometry: volume, surface area, bounding box
- [ ] identify overhangs and support requirements
- [ ] calculate part orientation optimisation

### 1.3 basic slicing algorithm
- [ ] implement simple layer-by-layer slicing
- [ ] generate 2d cross-sections at layer heights
- [ ] calculate perimeter and infill paths per layer

## phase 2: core simulation (can be done in parallel)

### 2.1 time calculation module
- [ ] layer printing time estimation
- [ ] travel time between features
- [ ] heating/cooling time
- [ ] support generation time

### 2.2 material calculation module  
- [ ] filament volume per layer
- [ ] support material volume
- [ ] waste calculation (failed prints, purging)
- [ ] material cost estimation

### 2.3 quality assessment module
- [ ] surface finish prediction based on layer height
- [ ] dimensional accuracy estimation
- [ ] overhang quality assessment
- [ ] support mark impact on surface

## phase 3: advanced metrics (parallel development)

### 3.1 cost modeling
- [ ] machine hourly rates
- [ ] material costs per gram
- [ ] labour costs (setup, removal)
- [ ] failure probability costs

### 3.2 post-processing requirements
- [ ] support removal complexity scoring
- [ ] surface finishing requirements
- [ ] assembly preparation needs

## phase 4: integration and testing

### 4.1 pipeline integration
- [ ] combine all modules into single pipeline
- [ ] standardise input/output formats
- [ ] error handling and edge cases

### 4.2 validation
- [ ] test with simple geometric shapes
- [ ] compare against known printing times
- [ ] validate cost calculations

### 4.3 optimisation
- [ ] performance improvements
- [ ] batch processing capability
- [ ] memory usage optimisation

## phase 5: mvp completion

### 5.1 api development
- [ ] create simple api interface
- [ ] json output format for metrics
- [ ] batch processing endpoint

### 5.2 documentation
- [ ] usage examples
- [ ] metric definitions
- [ ] calibration guidelines

## critical path dependencies
1. **must complete phase 1 first** - foundation for everything else
2. **phase 2 modules can be parallel** - independent calculations
3. **phase 3 builds on phase 2** - needs basic metrics first
4. **phase 4-5 sequential** - integration requires completed modules

## estimated timeline
- phase 1: 1-2 weeks
- phase 2: 2-3 weeks (parallel)
- phase 3: 1-2 weeks (parallel with phase 2)
- phase 4: 1 week
- phase 5: 1 week

**total: 6-8 weeks for mvp**

## first week priorities
1. get trimesh working with sample stl files
2. basic geometry extraction
3. simple slicing proof of concept
4. time estimation for single layer

## success criteria
- processes simple stl files (cubes, cylinders)
- outputs all 5 required metrics
- runs without gui dependencies
- processing time < 30 seconds per simple part