# 6-DOF Flight Dynamics Framework - Development Plan

## Project Overview
Build a production-ready 6-DOF flight dynamics simulation framework that integrates with aerodynamic analysis tools (AVL, XFOIL) for rapid aircraft design iteration. Target use case: UAV and advanced aircraft concept evaluation for nTop workflows.

## Repository Structure
```
flight-dynamics-6dof/
├── README.md
├── LICENSE
├── setup.py
├── requirements.txt
├── pyproject.toml
├── .gitignore
├── docs/
│   ├── getting_started.md
│   ├── theory.md
│   ├── api_reference.md
│   ├── examples.md
│   └── validation.md
├── src/
│   └── flight6dof/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── state.py          # State vector and conversions
│       │   ├── dynamics.py       # 6-DOF equations of motion
│       │   ├── integrators.py    # RK4, RK45, etc.
│       │   └── quaternion.py     # Quaternion utilities
│       ├── aerodynamics/
│       │   ├── __init__.py
│       │   ├── base.py           # Abstract aerodynamics model
│       │   ├── simple.py         # Simple coefficient-based model
│       │   ├── avl_interface.py  # AVL integration
│       │   ├── xfoil_interface.py # XFOIL integration
│       │   └── database.py       # Lookup table interpolation
│       ├── propulsion/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── simple_thrust.py
│       │   └── propeller.py      # Propeller models
│       ├── atmosphere/
│       │   ├── __init__.py
│       │   ├── standard.py       # ISA atmosphere
│       │   └── wind.py           # Wind/turbulence models
│       ├── control/
│       │   ├── __init__.py
│       │   ├── autopilot.py      # PID controllers
│       │   └── trim.py           # Trim calculation
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── stability.py      # Stability analysis
│       │   ├── linearization.py  # Linear model extraction
│       │   └── frequency.py      # Frequency response
│       ├── io/
│       │   ├── __init__.py
│       │   ├── avl_parser.py     # Parse AVL output files
│       │   ├── xfoil_parser.py   # Parse XFOIL output files
│       │   └── config.py         # YAML/JSON config loading
│       └── visualization/
│           ├── __init__.py
│           ├── plotting.py       # Standard plots
│           └── animation.py      # 3D trajectory animation
├── examples/
│   ├── 01_basic_simulation.py
│   ├── 02_avl_integration.py
│   ├── 03_xfoil_drag_estimation.py
│   ├── 04_autopilot_design.py
│   ├── 05_stability_analysis.py
│   ├── 06_trim_analysis.py
│   └── aircraft_configs/
│       ├── cessna_172.yaml
│       ├── generic_uav.yaml
│       └── bwb_concept.yaml
├── tests/
│   ├── __init__.py
│   ├── test_state.py
│   ├── test_dynamics.py
│   ├── test_integrators.py
│   ├── test_aerodynamics.py
│   ├── test_avl_parser.py
│   └── test_validation.py
├── tools/
│   ├── batch_avl.py              # Run AVL in batch mode
│   ├── batch_xfoil.py            # Run XFOIL in batch mode
│   ├── build_aero_database.py    # Create aero lookup tables
│   └── convert_legacy.py         # Import from other formats
└── validation/
    ├── reference_data/
    │   ├── cessna_flight_test.csv
    │   └── simulator_comparison.csv
    └── validation_scripts/
        ├── compare_cessna.py
        └── benchmark_performance.py
```

## Phase 1: Core Framework (Priority 1)

### Task 1.1: Project Setup
**Files to create:**
- `setup.py` with proper packaging
- `pyproject.toml` for modern Python packaging
- `requirements.txt` (numpy, scipy, matplotlib, pandas, pyyaml)
- `.gitignore` (Python, virtual environments, data files)
- `README.md` with badges, installation, quick start
- `LICENSE` (MIT or Apache 2.0)

**Key points:**
- Make it pip installable: `pip install -e .`
- Python 3.9+ minimum
- Clean dependency management

### Task 1.2: State Vector Implementation
**File:** `src/flight6dof/core/state.py`

**Requirements:**
- `State6DOF` class with:
  - Position [x, y, z] in NED frame
  - Velocity [u, v, w] in body frame
  - Quaternion [q0, q1, q2, q3]
  - Angular rates [p, q, r]
- Methods:
  - `to_array()` and `from_array()` for integration
  - `get_euler_angles()` - quaternion to Euler
  - `get_velocity_inertial()` - transform to inertial frame
  - `get_airspeed()` - compute total airspeed
  - `get_alpha_beta()` - angle of attack and sideslip
  - `copy()` - deep copy state
- Properties for easy access (e.g., `state.altitude`, `state.roll`)

### Task 1.3: Quaternion Utilities
**File:** `src/flight6dof/core/quaternion.py`

**Functions:**
- `quat_multiply(q1, q2)` - quaternion multiplication
- `quat_inverse(q)` - quaternion inverse
- `quat_normalize(q)` - normalize quaternion
- `quat_to_rotation_matrix(q)` - convert to DCM
- `quat_from_euler(roll, pitch, yaw)` - Euler to quaternion
- `euler_from_quat(q)` - quaternion to Euler
- `quat_derivative(q, omega)` - quaternion kinematic equation
- Include comprehensive docstrings with math notation

### Task 1.4: Integrators
**File:** `src/flight6dof/core/integrators.py`

**Implementations:**
- `RK4Integrator` - 4th order Runge-Kutta (default)
- `RK45Integrator` - Adaptive step size Runge-Kutta-Fehlberg
- `EulerIntegrator` - Simple Euler (for testing only)

**Interface:**
```python
class Integrator:
    def step(self, state, derivative_func, dt, *args) -> State6DOF:
        """Take one integration step"""
        pass
```

### Task 1.5: Core Dynamics Engine
**File:** `src/flight6dof/core/dynamics.py`

**Class:** `FlightDynamics6DOF`

**Responsibilities:**
- Compute state derivatives: `compute_derivatives(state, controls, atmosphere)`
- Force and moment aggregation from:
  - Aerodynamics model (pluggable)
  - Propulsion model (pluggable)
  - Gravity (internal)
- Rigid body dynamics:
  - Translational: F = m*(dV/dt + ω × V)
  - Rotational: M = I*dω/dt + ω × (I*ω)
- Integration loop with time stepping
- Event detection (ground contact, etc.)

**Key features:**
- Modular architecture - aerodynamics is injected dependency
- Efficient numpy operations
- Handles mass properties (inertia tensor, CG location)

## Phase 2: Aerodynamics Models (Priority 1)

### Task 2.1: Base Aerodynamics Interface
**File:** `src/flight6dof/aerodynamics/base.py`

**Abstract class:**
```python
class AerodynamicsModel(ABC):
    @abstractmethod
    def compute_forces_moments(self, state, controls, atmosphere):
        """Returns (forces_body, moments_body)"""
        pass
    
    @abstractmethod
    def get_reference_geometry(self):
        """Returns dict with S_ref, b_ref, c_ref"""
        pass
```

### Task 2.2: Simple Coefficient Model
**File:** `src/flight6dof/aerodynamics/simple.py`

**Implementation:**
- Polynomial or linear coefficients
- User provides: CL0, CLa, Cma, etc.
- Same as the initial demo code but cleaned up
- Good for quick studies and testing

### Task 2.3: AVL Interface
**File:** `src/flight6dof/aerodynamics/avl_interface.py`

**Features:**
- Parse AVL stability derivative output
- Parse AVL control derivative output
- Parse AVL geometry file for reference values
- Build `AVLAerodynamicsModel` from files
- Include damping derivatives (Clp, Cmq, Cnr, etc.)
- Support multiple flight conditions (alpha sweep)

**Key functions:**
```python
def parse_avl_stability_file(filepath) -> Dict
def parse_avl_control_file(filepath) -> Dict
def create_model_from_avl_outputs(stability_file, control_file) -> AVLAerodynamicsModel
```

### Task 2.4: XFOIL Interface
**File:** `src/flight6dof/aerodynamics/xfoil_interface.py`

**Features:**
- Automated XFOIL execution
- Parse XFOIL polar output
- Batch processing for alpha/Re sweeps
- Component drag buildup calculator
- Integration with wing sections

**Classes:**
```python
class XFOILRunner:
    def run_polar(airfoil_file, re, mach, alpha_range)
    def parse_polar_file(filepath)

class ParasiticDragCalculator:
    def calculate_cd0(wing_sections, fuselage, tails)
```

### Task 2.5: Aerodynamic Database
**File:** `src/flight6dof/aerodynamics/database.py`

**Purpose:** Multi-dimensional lookup tables

**Features:**
- Load pre-computed aero data (from AVL/CFD sweeps)
- 3D interpolation: CL(alpha, beta, Mach), etc.
- Fast lookup during simulation
- Support for control surface effects
- File formats: CSV, HDF5, or custom binary

```python
class AeroDatabaseModel:
    def load_from_hdf5(filepath)
    def interpolate(alpha, beta, mach, control_deflections)
```

## Phase 3: Supporting Systems (Priority 2)

### Task 3.1: Standard Atmosphere
**File:** `src/flight6dof/atmosphere/standard.py`

**Implementation:**
- ISA (International Standard Atmosphere)
- Compute: density, pressure, temperature, speed of sound
- Altitude input (geometric or geopotential)
- Include troposphere, stratosphere models

### Task 3.2: Propulsion Models
**File:** `src/flight6dof/propulsion/simple_thrust.py`

**Models:**
- Constant thrust
- Throttle-dependent thrust
- Velocity-dependent thrust (jet)
- Simple propeller model (thrust = function of RPM, airspeed)

### Task 3.3: Control System
**File:** `src/flight6dof/control/autopilot.py`

**Autopilots:**
- `PIDController` - generic PID
- `AltitudeHoldAutopilot` - maintain altitude
- `HeadingHoldAutopilot` - maintain heading
- `AirspeedHoldAutopilot` - maintain airspeed
- `AttitudeController` - inner loop (roll/pitch rate)

### Task 3.4: Trim Calculation
**File:** `src/flight6dof/control/trim.py`

**Algorithm:**
- Find equilibrium control settings
- For given: airspeed, altitude, flight path angle
- Minimize: derivatives of velocity and angular rates
- Use scipy.optimize
- Return trim state and controls

## Phase 4: Analysis Tools (Priority 2)

### Task 4.1: Stability Analysis
**File:** `src/flight6dof/analysis/stability.py`

**Features:**
- Linearize dynamics about trim point
- Extract A, B, C, D matrices
- Compute eigenvalues (modes)
- Identify: phugoid, short period, dutch roll, roll, spiral
- Plot mode shapes

### Task 4.2: Frequency Response
**File:** `src/flight6dof/analysis/frequency.py`

**Analysis:**
- Bode plots (control to state)
- Step responses
- Impulse responses
- Useful for control design

## Phase 5: I/O and Configuration (Priority 2)

### Task 5.1: Configuration Files
**File:** `src/flight6dof/io/config.py`

**Format:** YAML for aircraft definitions

**Example structure:**
```yaml
aircraft:
  name: "Generic UAV"
  mass: 25.0  # kg
  inertia:
    Ixx: 15.0
    Iyy: 20.0
    Izz: 30.0
    Ixz: 2.0
  reference:
    S: 1.5  # m²
    b: 3.0  # m
    c: 0.5  # m
  aerodynamics:
    type: "avl"
    stability_file: "data/uav_stability.txt"
    control_file: "data/uav_control.txt"
  propulsion:
    type: "constant_thrust"
    max_thrust: 50.0  # N
```

**Loader function:**
```python
def load_aircraft_config(yaml_file) -> Dict
def build_simulation_from_config(config) -> FlightDynamics6DOF
```

### Task 5.2: AVL File Parsers
**File:** `src/flight6dof/io/avl_parser.py`

**Functions:**
- `parse_avl_run_file()` - Parse .run case files
- `parse_avl_mass_file()` - Parse .mass files
- `parse_forces_moments()` - Parse force/moment output
- Robust error handling for malformed files

### Task 5.3: XFOIL File Parsers
**File:** `src/flight6dof/io/xfoil_parser.py`

**Functions:**
- `parse_xfoil_polar()` - Parse polar dump files
- `parse_xfoil_cp_distribution()` - CP output
- Extract transition locations

## Phase 6: Visualization (Priority 3)

### Task 6.1: Standard Plotting
**File:** `src/flight6dof/visualization/plotting.py`

**Plots:**
- `plot_trajectory_3d()` - 3D flight path
- `plot_states_vs_time()` - Position, velocity, angles
- `plot_controls_vs_time()` - Control deflections
- `plot_forces_moments()` - Force/moment time histories
- `plot_trim_envelope()` - Trim conditions
- All plots using matplotlib with clean styling

### Task 6.2: Animation
**File:** `src/flight6dof/visualization/animation.py`

**Features:**
- Animate 3D aircraft motion
- Show attitude (aircraft reference frame)
- Velocity vector
- Export to MP4 or GIF
- Use matplotlib animation or plotly

## Phase 7: Testing and Validation (Priority 1)

### Task 7.1: Unit Tests
**Files:** `tests/test_*.py`

**Coverage:**
- State vector operations
- Quaternion math (compare against known results)
- Integrator accuracy (compare against analytical solutions)
- Aerodynamics models
- Parser functions

**Use pytest with:**
- Fixtures for common test data
- Parametrized tests
- Coverage >80%

### Task 7.2: Integration Tests
**Test scenarios:**
- Constant altitude flight
- Coordinated turn
- Climb to altitude
- Control step response

**Validation:**
- Compare against analytical solutions where possible
- Compare against published flight test data
- Regression tests to prevent breakage

### Task 7.3: Validation Against Reference
**Files:** `validation/validation_scripts/`

**References:**
- Cessna 172 flight test data (if available)
- Comparison with FlightGear, JSBSim, or X-Plane
- Document differences and accuracy

## Phase 8: Examples and Documentation (Priority 2)

### Task 8.1: Example Scripts
**Files:** `examples/*.py`

**Examples:**
1. **Basic simulation** - Simple straight flight
2. **AVL integration** - Load AVL data, simulate
3. **XFOIL drag** - Estimate CD0, use in sim
4. **Autopilot** - Design altitude hold controller
5. **Stability analysis** - Linearize and analyze modes
6. **Trim analysis** - Find trim at various speeds

### Task 8.2: Documentation
**Files:** `docs/*.md`

**Content:**
- **Getting Started:** Installation, first simulation in 5 minutes
- **Theory:** 6-DOF equations, coordinate frames, quaternions
- **API Reference:** Auto-generated from docstrings (use Sphinx)
- **Examples:** Detailed walkthrough of each example
- **Validation:** Results vs. reference data

**Setup:**
- Use Sphinx for HTML docs
- Host on ReadTheDocs or GitHub Pages
- Include math equations (LaTeX)

### Task 8.3: README
**Content:**
- Project description and motivation
- Key features (bullet points)
- Installation instructions
- Quick start (5-line example)
- Link to full documentation
- Contributing guidelines
- License information
- Badges: build status, coverage, PyPI version

## Phase 9: Advanced Features (Priority 3)

### Task 9.1: Wind and Turbulence
**File:** `src/flight6dof/atmosphere/wind.py`

**Models:**
- Constant wind vector
- Wind shear (altitude dependent)
- Dryden turbulence model
- von Kármán turbulence model

### Task 9.2: Ground Effect
**Enhancement to aerodynamics models**

**Implementation:**
- Modify induced drag when close to ground
- Altitude-dependent factor
- Simple empirical model

### Task 9.3: Actuator Dynamics
**File:** `src/flight6dof/control/actuators.py`

**Models:**
- First-order lag (control surface delay)
- Rate limits (deg/sec)
- Position limits

### Task 9.4: Mass Properties Changes
**Enhancement to dynamics**

**Features:**
- Variable mass (fuel burn)
- Variable CG location
- Update inertia tensor

### Task 9.5: Landing Gear
**File:** `src/flight6dof/systems/landing_gear.py`

**Model:**
- Ground contact detection
- Normal force
- Friction force
- Simple spring-damper model

## Phase 10: Tooling and Utilities (Priority 3)

### Task 10.1: Batch AVL Runner
**File:** `tools/batch_avl.py`

**Purpose:** Automate AVL sweeps

**Features:**
- Run AVL for multiple flight conditions
- Generate stability derivatives vs. alpha
- Generate control derivatives
- Save results to database format

### Task 10.2: Batch XFOIL Runner
**File:** `tools/batch_xfoil.py`

**Purpose:** Automate XFOIL polars

**Features:**
- Run XFOIL for alpha/Re sweeps
- Multiple airfoils in batch
- Generate drag polar data
- Export to CSV or database

### Task 10.3: Aero Database Builder
**File:** `tools/build_aero_database.py`

**Purpose:** Create lookup tables

**Workflow:**
1. Run batch AVL/CFD simulations
2. Collect results
3. Build interpolation database (HDF5)
4. Validate interpolation accuracy

### Task 10.4: Converter from Other Formats
**File:** `tools/convert_legacy.py`

**Support:**
- JSBSim XML → our YAML format
- X-Plane → our format (if feasible)
- Simple CSV tables → aero database

## Implementation Notes for Claude Code

### Project Initialization
```bash
# Start with:
mkdir flight-dynamics-6dof
cd flight-dynamics-6dof
git init

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Initial dependencies
pip install numpy scipy matplotlib pandas pyyaml pytest
pip freeze > requirements.txt
```

### Development Workflow
1. **Start with Phase 1, Task 1.1** - Get the project structure right
2. **Then Task 1.2-1.5** - Core dynamics working end-to-end
3. **Then Phase 2** - Get aerodynamics models working
4. **Iterate and test** - Don't move on until current phase works
5. **Examples early** - Create example scripts as you build features

### Code Quality Standards
- **Type hints:** Use throughout (Python 3.9+ syntax)
- **Docstrings:** NumPy style for all public functions/classes
- **Testing:** Write tests alongside implementation
- **Linting:** Use black for formatting, flake8 for linting
- **Comments:** Explain the physics/math, not just the code

### Key Design Principles
1. **Modularity:** Aerodynamics, propulsion, etc. are pluggable
2. **Performance:** Use vectorized numpy operations
3. **Usability:** Simple API, config files for complex setups
4. **Extensibility:** Easy to add new models
5. **Documentation:** Theory + practical examples

### Mathematical Notation in Code
Use clear variable names that match standard notation:
- `alpha` not `a` for angle of attack
- `q_bar` not `qb` for dynamic pressure
- `omega` not `w` for angular velocity (avoid confusion with w = downward velocity)

### Critical Validation Points
After implementing each phase, validate:
1. **Steady level flight** - Should maintain altitude with proper trim
2. **Energy conservation** - Check in unpowered glide
3. **Symmetry** - Left/right turns should be symmetric
4. **Stability** - Known stable aircraft should be stable
5. **Published data** - Match known aircraft performance where possible

## Deliverables Checklist

### Must Have (MVP)
- [ ] Core 6-DOF dynamics (Phase 1)
- [ ] Simple aerodynamics model (Phase 2, Task 2.2)
- [ ] AVL integration (Phase 2, Task 2.3)
- [ ] Basic example working (Phase 8, Task 8.1, #1-2)
- [ ] Unit tests passing (Phase 7, Task 7.1)
- [ ] README with quick start (Phase 8, Task 8.3)

### Should Have
- [ ] XFOIL integration (Phase 2, Task 2.4)
- [ ] Autopilot controllers (Phase 3, Task 3.3)
- [ ] Trim calculation (Phase 3, Task 3.4)
- [ ] Plotting utilities (Phase 6, Task 6.1)
- [ ] All examples (Phase 8, Task 8.1)
- [ ] Full documentation (Phase 8, Task 8.2)

### Nice to Have
- [ ] Aero database interpolation (Phase 2, Task 2.5)
- [ ] Stability analysis (Phase 4)
- [ ] Wind/turbulence (Phase 9, Task 9.1)
- [ ] Animation (Phase 6, Task 6.2)
- [ ] Batch processing tools (Phase 10)

## Estimated Timeline

**If working full-time on this:**
- Phase 1 (Core): 3-5 days
- Phase 2 (Aero): 4-6 days
- Phase 3 (Support): 2-3 days
- Phase 7 (Testing): Ongoing, 2-3 days
- Phase 8 (Examples/Docs): 2-3 days
- **MVP Total: ~2 weeks**

**Full featured release:**
- Phases 4, 6, 9, 10: +1 week
- **Total: ~3 weeks**

## Success Criteria

The framework is successful if:
1. **A new user can simulate an aircraft in <10 minutes** from install
2. **AVL derivatives integrate seamlessly** - no manual reformatting
3. **Results match published data** within 10% for test cases
4. **Code is maintainable** - clean, tested, documented
5. **Extensible for nTop workflows** - easy to add new aircraft, sweep parameters

## Next Steps After Completion

Once the framework is working:
1. **Integrate with nTop** - Export design parameters → run sim → return performance
2. **Optimization loop** - Wrap in optimizer for automated design
3. **Uncertainty quantification** - Monte Carlo for robust design
4. **Real-time visualization** - Web interface for interactive exploration
5. **Database of aircraft** - Build library of validated models

---

## Instructions for Claude Code

**Start here:**
1. Create repository structure (Task 1.1)
2. Implement `State6DOF` class (Task 1.2)
3. Implement quaternion utilities (Task 1.3)
4. Implement integrators (Task 1.4)
5. Implement core dynamics (Task 1.5)
6. Create first example and verify it works

**Key files to start with:**
- `src/flight6dof/core/state.py`
- `src/flight6dof/core/quaternion.py`
- `src/flight6dof/core/integrators.py`
- `src/flight6dof/core/dynamics.py`
- `examples/01_basic_simulation.py`

**Testing as you go:**
- Create `tests/test_state.py` while writing `state.py`
- Create `tests/test_quaternion.py` while writing `quaternion.py`
- Etc.

**When you have questions:**
- Refer back to the working prototypes in `/mnt/user-data/outputs/`
- Coordinate systems: NED inertial, body-fixed for dynamics
- Units: SI throughout (meters, kg, seconds, radians)

**Remember:**
- Clean, documented code > clever code
- Tests > no tests
- Working MVP > feature-complete but broken
- Incremental development > big bang

Good luck! This will be a solid foundation for aircraft simulation work.
