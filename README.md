# V2G Microgrid Optimization Pipeline

A comprehensive Python framework for optimizing Vehicle-to-Grid (V2G) integrated microgrids using renewable energy sources. This implementation is based on advanced optimization algorithms including the Improved Antlion Optimizer (IALO) with Lévy flight enhancement, designed for academic research and practical microgrid applications.

## Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [PSO vs ALO Comparison](#pso-vs-alo-comparison)
- [Configuration Guide](#configuration-guide)
- [Component Documentation](#component-documentation)
- [Optimization Algorithms](#optimization-algorithms)
- [Usage Examples](#usage-examples)
- [Results and Analysis](#results-and-analysis)
- [Mathematical Foundation](#mathematical-foundation)
- [Benchmarking](#benchmarking)
- [Contributing](#contributing)
- [Citation](#citation)
- [License](#license)

## Features

### Core Capabilities
- **Multi-Algorithm Optimization**: IALO, ALO, PSO, and CSA algorithms with comprehensive benchmarking
- **V2G Integration**: Complete electric vehicle fleet modeling with bidirectional charging capabilities
- **Renewable Energy Modeling**: PV and wind turbine systems with real meteorological data integration
- **Energy Storage Management**: Advanced battery system with state-of-charge constraints and degradation modeling
- **Economic Analysis**: Lifecycle cost optimization (COE, LPSP, REF, NPC) with sensitivity analysis
- **Monte Carlo Simulation**: Stochastic modeling of EV behavior and system uncertainties
- **Comprehensive Visualization**: Publication-ready plots and interactive dashboards

### Advanced Features
- **Lévy Flight Enhancement**: Improved exploration capabilities in IALO algorithm
- **Multi-Objective Optimization**: Simultaneous optimization of cost, reliability, and sustainability
- **Uncertainty Quantification**: Monte Carlo analysis with confidence intervals
- **Sensitivity Analysis**: Parameter sensitivity with tornado diagrams
- **Real-Time Energy Management**: Rule-based energy management system with mode switching
- **Modular Architecture**: Easily extensible component-based design

## System Architecture

```
v2g_microgrid_optimization/
├── data/                           # Input data files
│   ├── weather_data.csv           # Solar irradiance, wind speed, temperature
│   ├── load_data.csv              # Hourly electricity demand profile
│   ├── ev_data.csv                # EV behavior patterns and characteristics
│   └── economic_parameters.json   # Economic and cost parameters
├── src/                           # Source code
│   ├── components/                # System component models
│   │   ├── photovoltaic.py       # PV system with temperature effects
│   │   ├── wind_turbine.py       # Wind turbine with power curve modeling
│   │   ├── battery.py            # Battery storage with SOC management
│   │   ├── electric_vehicle.py   # EV fleet with V2G capabilities
│   │   ├── grid.py               # Grid interface and economics
│   │   └── converter.py          # Power electronics modeling
│   ├── optimization/              # Optimization algorithms
│   │   ├── ialo.py               # Improved Antlion Optimizer
│   │   ├── alo.py                # Standard Antlion Optimizer
│   │   ├── pso.py                # Particle Swarm Optimization
│   │   ├── csa.py                # Cuckoo Search Algorithm
│   │   └── benchmark_functions.py # Testing and validation functions
│   ├── energy_management/         # Energy management system
│   │   ├── rule_based_ems.py     # Rule-based energy management
│   │   └── operation_modes.py    # System operation modes
│   ├── analysis/                  # Analysis and evaluation
│   │   ├── economic_analysis.py  # Economic metrics calculation
│   │   ├── monte_carlo.py        # Stochastic simulation
│   │   └── sensitivity_analysis.py # Parameter sensitivity analysis
│   ├── utils/                     # Utilities and tools
│   │   ├── data_loader.py        # Data loading and preprocessing
│   │   ├── visualization.py      # Plotting and visualization
│   │   └── constants.py          # Physical constants and parameters
│   └── main.py                    # Main execution script
├── outputs/                       # Generated results
│   ├── optimization_results/      # Optimization solutions and metrics
│   ├── figures/                   # Generated plots and visualizations
│   └── reports/                   # Analysis reports and summaries
├── config.yaml                    # System configuration file
├── requirements.txt               # Python dependencies
└── README.md                      # This documentation
```

## Installation

### Prerequisites
- Python 3.8 or higher
- Git (for cloning repository)
- At least 4GB RAM for large simulations
- Optional: CUDA-capable GPU for accelerated computations

### Step 1: Clone Repository
```bash
git clone https://github.com/your-repo/v2g-microgrid-optimization.git
cd v2g-microgrid-optimization
```

### Step 2: Create Virtual Environment
```bash
# Using venv (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using conda
conda create -n v2g-optimization python=3.9
conda activate v2g-optimization
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Verify Installation
```bash
python src/main.py --help
```

## Quick Start

### Basic Optimization Run
```bash
# Run optimization with default configuration
python src/main.py

# Run with custom configuration
python src/main.py --config custom_config.yaml

# Run specific algorithm only
python src/main.py --algorithms IALO

# Run with multiple algorithms for comparison
python src/main.py --algorithms IALO,ALO,PSO,CSA
```

### Monitor Progress
```bash
# View real-time logs
tail -f outputs/pipeline.log

# Check intermediate results
ls outputs/optimization_results/
```

### View Results
After completion, results are saved in:
- `outputs/optimization_results/`: Numerical results and best solutions
- `outputs/figures/`: Convergence plots and energy flow diagrams
- `outputs/reports/`: Comprehensive analysis reports

---

## PSO vs ALO Comparison

A self-contained pipeline that runs both **Particle Swarm Optimization (PSO)** and the **Ant-Lion Optimizer (ALO)** against the full 8,760-hour V2G microgrid simulation, then generates a complete set of publication-ready comparison figures and reports.

### What it produces

All outputs are saved to `outputs/pso_alo_comparison/`:

| File | Description |
|------|-------------|
| `fig1_convergence.png` | Convergence curves — PSO vs ALO |
| `fig2_kpi_comparison.png` | COE, LPSP, REF, NPC side-by-side |
| `fig3_component_sizing.png` | Optimal component counts and capacities |
| `fig4_energy_sources.png` | Annual energy source distribution |
| `fig5_operation_modes.png` | System operation mode statistics |
| `fig6_monte_carlo.png` | Monte Carlo uncertainty analysis (100 EV scenarios) |
| `fig7_economic_breakdown.png` | NPC cost breakdown by category |
| `fig8_seasonal.png` | Seasonal energy flow and battery cycles |
| `fig9_sensitivity.png` | Sensitivity tornado chart (±20% parameter variation) |
| `fig10_dashboard.png` | Single-page summary dashboard |
| `comparison_report.md` | Structured data report |
| `PSO_vs_ALO_Full_Report.md` | Full narrative comparison report |


```bash
source .venv/bin/activate
python3 launch_comparison.py
```

That's it. The script runs in two steps automatically:

1. **Step 1** — Runs PSO and ALO against the real simulation (takes 30–90 min depending on hardware)
2. **Step 2** — Generates all 10 figures and 2 reports (takes a few seconds)

### Options

```bash
python3 launch_comparison.py --iters 50        # fewer iterations, faster run
python3 launch_comparison.py --pop 20          # smaller population
python3 launch_comparison.py --pop 20 --iters 50   # quick debug run (~5 min)
```

### How it works internally

| Script | Role |
|--------|------|
| `launch_comparison.py` | Single entry point — calls the two scripts below in sequence |
| `run_real.py` | Runs PSO and ALO for real, saves timing and results to `real_results.json` |
| `generate_comparison.py` | Generates all figures and markdown reports |

---

## Configuration Guide

The system is configured through `config.yaml`. Key sections include:

### System Location
```yaml
location:
  name: "Tripoli, Libya"
  latitude: 32.8872
  longitude: 13.1913
```

### Component Specifications
```yaml
components:
  photovoltaic:
    rated_power_per_panel: 325  # W
    temp_coefficient: -3.7e-3   # 1/°C
    noct: 45                    # °C
    
  wind_turbine:
    rated_power_per_turbine: 5000  # W
    cut_in_speed: 2.5             # m/s
    rated_speed: 9.5              # m/s
    
  battery:
    capacity_per_unit: 35380    # Wh
    round_trip_efficiency: 0.85
    depth_of_discharge: 0.8
    
  electric_vehicle:
    capacity_per_vehicle: 24000  # Wh
    charge_rate: 7.2            # kW
    discharge_rate: 7.2         # kW
```

### Optimization Parameters
```yaml
optimization:
  algorithms: ["IALO", "ALO", "PSO", "CSA"]
  population_size: 50
  max_iterations: 100
  
bounds:
  n_pv: [0, 100]      # Number of PV panels
  n_wt: [0, 50]       # Number of wind turbines
  n_bt: [0, 100]      # Number of batteries
  autonomy_days: [0, 5] # Days of energy autonomy
```

### Economic Parameters
```yaml
economic:
  interest_rate: 0.03
  project_lifetime: 20
  grid_buy_price: 0.023    # $/kWh
  grid_sell_price: 0.015   # $/kWh
```

## Component Documentation

### Photovoltaic System
The PV system model implements temperature-dependent power output:

**Key Equations:**
- Cell Temperature: `Tc = Tamb + G × ((NOCT - 20) / 800)`
- Power Output: `Ppv = Prated × (G/1000) × [1 + αt × (Tc - 25)]`

**Usage:**
```python
from src.components import PhotovoltaicSystem

pv = PhotovoltaicSystem(
    rated_power=325,         # W per panel
    temp_coefficient=-3.7e-3,# Temperature coefficient
    noct=45,                 # Nominal operating cell temperature
    num_panels=50            # Number of panels
)

power_output = pv.calculate_output_power(
    solar_irradiance=800,    # W/m²
    ambient_temp=30          # °C
)
```

### Wind Turbine System
Wind turbine with piecewise linear power curve and hub height adjustment:

**Key Features:**
- Hub height wind speed correction
- Cut-in, rated, and cut-out speed modeling
- Power curve implementation

**Usage:**
```python
from src.components import WindTurbine

wt = WindTurbine(
    rated_power=5000,        # W per turbine
    cut_in_speed=2.5,        # m/s
    rated_speed=9.5,         # m/s
    cut_out_speed=40,        # m/s
    num_turbines=10
)

power_output = wt.calculate_output_power(wind_speed=8.5)
```

### Battery System
Advanced battery model with SOC management and efficiency modeling:

**Key Features:**
- State-of-charge constraints
- Round-trip efficiency modeling
- Depth-of-discharge limits
- Autonomy days calculation

**Usage:**
```python
from src.components import BatterySystem

battery = BatterySystem(
    capacity=35380,          # Wh per battery
    soc_min=0.2,            # Minimum SOC (20%)
    soc_max=1.0,            # Maximum SOC (100%)
    efficiency=0.85,         # Round-trip efficiency
    num_batteries=20
)

energy_charged, surplus = battery.charge(energy_available=5000)
```

### Electric Vehicle Fleet
V2G-capable EV fleet with stochastic behavior modeling:

**Key Features:**
- Bidirectional charging (V2G/G2V)
- Arrival/departure pattern modeling
- SOC management and constraints
- Fleet aggregation capabilities

**Usage:**
```python
from src.components import ElectricVehicle

ev_fleet = ElectricVehicle(
    capacity=24000,          # Wh per vehicle
    charge_rate=7.2,         # kW
    discharge_rate=7.2,      # kW
    num_vehicles=30
)

# Generate availability patterns
availability = ev_fleet.generate_availability_pattern(hours=8760)

# Charge fleet with surplus energy
energy_used, remaining = ev_fleet.charge_fleet(50.0, time_step=0)
```

## Optimization Algorithms

### Improved Antlion Optimizer (IALO)
Enhanced ALO with Lévy flight for better exploration:

**Key Features:**
- Lévy flight random walk
- Elite antlion guidance
- Dynamic boundary adjustment
- Superior convergence properties

**Mathematical Foundation:**
- Lévy flight step: `step = u / |v|^(1/β)`
- Sigma calculation: `σ = [Γ(1+β)sin(πβ/2) / (Γ((1+β)/2)β2^((β-1)/2))]^(1/β)`

### Standard Antlion Optimizer (ALO)
Original ALO algorithm implementation:

**Key Features:**
- Roulette wheel selection
- Random walk around antlions
- Shrinking boundaries mechanism
- Elite preservation

### Particle Swarm Optimization (PSO)
Classical PSO with inertia weight adaptation:

**Key Features:**
- Dynamic inertia weight
- Cognitive and social learning
- Velocity clamping
- Global best tracking

### Cuckoo Search Algorithm (CSA)
Nature-inspired algorithm with Lévy flights:

**Key Features:**
- Lévy flight exploration
- Alien egg discovery
- Population diversity maintenance
- Simple parameter setting

## Usage Examples

### Example 1: Basic Optimization
```python
import yaml
from src.main import main

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Run optimization
results = main()
print(f"Best solution: {results['best_solution']}")
print(f"Best fitness: {results['best_fitness']}")
```

### Example 2: Custom Component Configuration
```python
from src.components import PhotovoltaicSystem, WindTurbine, BatterySystem
from src.optimization import ImprovedAntlionOptimizer

# Configure components
pv = PhotovoltaicSystem(rated_power=325, num_panels=100)
wt = WindTurbine(rated_power=5000, num_turbines=25)
battery = BatterySystem(capacity=35380, num_batteries=50)

components = {'pv': pv, 'wt': wt, 'battery': battery}

# Define objective function
def objective_function(solution):
    # Implement your objective calculation
    return cost_of_energy + loss_of_power_supply_probability

# Run optimization
optimizer = ImprovedAntlionOptimizer(
    objective_function=objective_function,
    bounds=[(0, 100), (0, 50), (0, 100), (0, 5)],
    population_size=50,
    max_iterations=100
)

best_solution, best_fitness, history = optimizer.optimize()
```

### Example 3: Monte Carlo Analysis
```python
from src.analysis import MonteCarloSimulation

# Initialize Monte Carlo simulation
mc_sim = MonteCarloSimulation(num_simulations=1000)

# Run simulation for different EV fleet sizes
for num_evs in [10, 30, 60]:
    results = mc_sim.simulate_ev_behavior(
        num_evs=num_evs,
        data=data,
        components=components,
        solution=best_solution
    )
    
    print(f"EV Fleet Size: {num_evs}")
    print(f"Mean COE: {results['summary_statistics']['mean_coe']:.4f}")
    print(f"Mean LPSP: {results['summary_statistics']['mean_lpsp']:.4f}")
```

### Example 4: Economic Analysis
```python
from src.analysis import EconomicAnalysis

# Initialize economic analysis
economic = EconomicAnalysis({
    'interest_rate': 0.03,
    'project_lifetime': 20,
    'grid_buy_price': 0.023,
    'grid_sell_price': 0.015
})

# Calculate all economic metrics
metrics = economic.calculate_all_objectives(components, simulation_results)

print(f"Cost of Energy: ${metrics['coe']:.4f}/kWh")
print(f"LPSP: {metrics['lpsp']:.4f}")
print(f"REF: {metrics['ref']:.4f}")
print(f"NPC: ${metrics['npc']:,.0f}")
```

## Results and Analysis

### Output Files Structure
```
outputs/
├── optimization_results/
│   ├── best_solution.csv              # Optimal component sizing
│   ├── economic_analysis.csv          # Economic metrics
│   ├── convergence_history.csv        # Algorithm convergence data
│   └── algorithm_comparison.csv       # Multi-algorithm comparison
├── figures/
│   ├── ialo_convergence.png           # Convergence plots
│   ├── energy_flows.png               # Energy flow diagrams
│   ├── monte_carlo_analysis.png       # Monte Carlo results
│   ├── economic_analysis.png          # Economic breakdown
│   └── component_sizing.png           # Optimal sizing visualization
└── reports/
    ├── optimization_report.html       # Comprehensive HTML report
    ├── sensitivity_analysis.csv       # Sensitivity analysis results
    └── system_performance.json        # Performance metrics
```

### Key Performance Metrics

**Economic Metrics:**
- **COE (Cost of Energy)**: Total system cost per kWh delivered
- **NPC (Net Present Cost)**: Lifecycle cost in present value
- **LPSP (Loss of Power Supply Probability)**: System reliability metric
- **REF (Renewable Energy Fraction)**: Sustainability indicator

**Technical Metrics:**
- **System Efficiency**: Overall energy conversion efficiency
- **Battery Utilization**: Storage system usage patterns
- **V2G Contribution**: Electric vehicle energy contribution
- **Grid Interaction**: Import/export energy patterns

**Optimization Metrics:**
- **Convergence Rate**: Algorithm convergence speed
- **Solution Quality**: Final objective function value
- **Computational Time**: Algorithm execution time
- **Robustness**: Solution stability across runs

### Interpreting Results

**Optimal Component Sizing:**
The optimization determines the optimal number of:
- PV panels for solar energy generation
- Wind turbines for wind energy harvesting
- Battery units for energy storage
- Days of autonomy for system reliability

**Economic Performance:**
- Lower COE indicates more cost-effective system
- Higher REF indicates greater renewable energy utilization
- Lower LPSP indicates better system reliability
- Trade-offs between cost, reliability, and sustainability

**Monte Carlo Analysis:**
- Confidence intervals for key metrics under uncertainty
- Impact of EV behavior variability on system performance
- Risk assessment for different scenarios
- Sensitivity to input parameter variations

## Mathematical Foundation

### Objective Function
The multi-objective optimization combines three key objectives:

```
f(x) = w₁ × COE + w₂ × γ × pf × LPSP - w₃ × REF + constraints
```

Where:
- `w₁, w₂, w₃`: Weighting factors
- `γ`: Scaling factor (1000)
- `pf`: Balancing factor (1.0)
- Constraints: LPSP ≤ 0.01, REF ≥ 0.5

### Component Models

**PV Power Output:**
```
Ppv(t) = Prated × (G(t)/1000) × [1 + αt × (Tc - 25)]
Tc = Tamb + G(t) × ((NOCT - 20)/800)
```

**Wind Turbine Power:**
```
Pwt(t) = {
  0,                           if v < vci or v ≥ vco
  Prated × (v-vci)/(vr-vci),  if vci ≤ v < vr
  Prated,                      if vr ≤ v < vco
}
```

**Battery SOC:**
```
SOC(t) = SOC(t-1) + [Ech(t) - Edch(t)] / Capacity
SOCmin ≤ SOC(t) ≤ SOCmax
```

**Economic Calculations:**
```
COE = (CRF × NPC + GridCost - GridRevenue) / TotalLoad
CRF = ir × (1+ir)ⁿ / [(1+ir)ⁿ - 1]
LPSP = Σ(LoadNotServed) / Σ(TotalLoad)
REF = Σ(RenewableEnergy) / Σ(TotalEnergySupply)
```

## Benchmarking

### Algorithm Performance Testing
```python
from src.optimization.benchmark_functions import BenchmarkFunctions
from src.optimization import ImprovedAntlionOptimizer

# Test IALO on standard benchmark functions
functions = ['sphere', 'rosenbrock', 'ackley', 'rastrigin']

for func_name in functions:
    result = BenchmarkFunctions.run_benchmark_test(
        ImprovedAntlionOptimizer, 
        func_name,
        population_size=30,
        max_iterations=100
    )
    print(f"{func_name}: Best fitness = {result['best_fitness']:.6f}")
```

### Algorithm Comparison
The framework includes comprehensive algorithm comparison capabilities:

```bash
# Run all algorithms on benchmark functions
python -m src.optimization.benchmark_functions

# Compare algorithms on microgrid optimization
python src/main.py --algorithms IALO,ALO,PSO,CSA --benchmark
```

### Performance Metrics
- **Convergence Speed**: Iterations to reach target fitness
- **Solution Quality**: Final objective function value
- **Robustness**: Standard deviation across multiple runs
- **Computational Efficiency**: Runtime per iteration

## Contributing

We welcome contributions to improve the V2G microgrid optimization framework. Please follow these guidelines:

### Development Setup
```bash
# Clone development branch
git clone -b develop https://github.com/your-repo/v2g-microgrid-optimization.git

# Install development dependencies
pip install -e .[dev]

# Run tests
pytest tests/ -v

# Check code quality
flake8 src/ tests/
black src/ tests/
mypy src/
```

### Contribution Areas
- **Algorithm Implementation**: New optimization algorithms
- **Component Models**: Additional renewable energy technologies
- **Analysis Tools**: Advanced economic and reliability analysis
- **Visualization**: Enhanced plotting and dashboard capabilities
- **Performance**: Computational efficiency improvements
- **Documentation**: Examples, tutorials, and guides

### Submission Process
1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Make changes with appropriate tests
4. Ensure code quality checks pass
5. Submit pull request with detailed description

## Citation

If you use this framework in your research, please cite:

```bibtex
@software{v2g_microgrid_optimization,
  title={V2G Microgrid Optimization Pipeline: A Comprehensive Framework for Vehicle-to-Grid Integration},
  author={V2G Research Team},
  year={2024},
  url={https://github.com/your-repo/v2g-microgrid-optimization},
  version={1.0.0}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support and Contact

- **Documentation**: [Project Wiki](https://github.com/your-repo/v2g-microgrid-optimization/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-repo/v2g-microgrid-optimization/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/v2g-microgrid-optimization/discussions)
- **Email**: research@v2g-optimization.com

## Acknowledgments

This work is based on advanced research in vehicle-to-grid integration and renewable energy optimization. We acknowledge the contributions of the research community and the open-source software ecosystem that made this implementation possible.

---

**Note**: This implementation is designed for research and educational purposes. For commercial applications, additional validation and regulatory compliance may be required.

