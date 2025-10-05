# V2G MICROGRID OPTIMIZATION RESEARCH PROJECT

## Pipeline Architecture

```
📦 v2g_microgrid_optimization/
├── 📁 data/
│   ├── weather_data.csv
│   ├── load_data.csv
│   ├── ev_data.csv
│   └── economic_parameters.json
├── 📁 src/
│   ├── 📁 components/
│   │   ├── __init__.py
│   │   ├── photovoltaic.py
│   │   ├── wind_turbine.py
│   │   ├── battery.py
│   │   ├── converter.py
│   │   ├── electric_vehicle.py
│   │   └── grid.py
│   ├── 📁 optimization/
│   │   ├── __init__.py
│   │   ├── ialo.py
│   │   ├── alo.py
│   │   ├── pso.py
│   │   ├── csa.py
│   │   └── benchmark_functions.py
│   ├── 📁 energy_management/
│   │   ├── __init__.py
│   │   ├── rule_based_ems.py
│   │   └── operation_modes.py
│   ├── 📁 analysis/
│   │   ├── __init__.py
│   │   ├── monte_carlo.py
│   │   ├── economic_analysis.py
│   │   └── sensitivity_analysis.py
│   ├── 📁 utils/
│   │   ├── __init__.py
│   │   ├── data_loader.py
│   │   ├── constants.py
│   │   └── visualization.py
│   └── main.py
├── 📁 outputs/
│   ├── optimization_results/
│   ├── figures/
│   └── reports/
├── requirements.txt
├── config.yaml
└── README.md
```

## Pipeline Flow

### 1. Data Preparation Phase
```python
# data_loader.py
import pandas as pd
import numpy as np
import json

class DataLoader:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
    
    def load_weather_data(self):
        # Load solar irradiance, wind speed, ambient temperature
        return pd.read_csv(self.config['weather_data_path'])
    
    def load_load_profile(self):
        # Load hourly residential load demand
        return pd.read_csv(self.config['load_data_path'])
    
    def load_ev_data(self):
        # Load EV arrival/departure patterns
        return pd.read_csv(self.config['ev_data_path'])
```

### 2. Component Modeling Phase
```python
# photovoltaic.py
class PhotovoltaicSystem:
    def __init__(self, rated_power, temp_coefficient=-3.7e-3, noct=45):
        self.rated_power = rated_power
        self.temp_coefficient = temp_coefficient
        self.noct = noct
    
    def calculate_output(self, solar_irradiance, ambient_temp):
        """Calculate PV output power using Eq.(3.1) and Eq.(3.2)"""
        tc = ambient_temp + solar_irradiance * ((self.noct - 20) / 800)
        p_pv = self.rated_power * (solar_irradiance / 1000) * \
               (1 + self.temp_coefficient * (tc - 25))
        return p_pv

# wind_turbine.py
class WindTurbine:
    def __init__(self, rated_power, cut_in_speed, cut_out_speed, rated_speed):
        self.rated_power = rated_power
        self.cut_in_speed = cut_in_speed
        self.cut_out_speed = cut_out_speed
        self.rated_speed = rated_speed
    
    def calculate_output(self, wind_speed):
        """Calculate WT output power using Eq.(3.3)"""
        if wind_speed < self.cut_in_speed or wind_speed >= self.cut_out_speed:
            return 0
        elif self.cut_in_speed <= wind_speed < self.rated_speed:
            return self.rated_power * (wind_speed - self.cut_in_speed) / \
                   (self.rated_speed - self.cut_out_speed)
        else:
            return self.rated_power
```

### 3. Energy Management System Phase
```python
# rule_based_ems.py
class RuleBasedEMS:
    def __init__(self, components):
        self.components = components
        self.operation_modes = {
            'mode1': self.renewable_supply,
            'mode2': self.battery_discharge,
            'mode3': self.grid_to_vehicle,
            'mode4': self.vehicle_to_grid
        }
    
    def execute(self, time_step, load_demand, ev_demand):
        """Execute RB-EMS logic based on conditions"""
        # Check power availability and execute appropriate mode
        pv_power = self.components['pv'].get_power(time_step)
        wt_power = self.components['wt'].get_power(time_step)
        
        total_renewable = pv_power + wt_power
        
        if total_renewable > load_demand:
            return self.operation_modes['mode1'](time_step)
        elif self.components['battery'].soc > 0.2:
            return self.operation_modes['mode2'](time_step)
        # ... additional logic
```

### 4. Optimization Phase
```python
# ialo.py
class ImprovedAntlionOptimizer:
    def __init__(self, objective_function, constraints, bounds):
        self.objective_function = objective_function
        self.constraints = constraints
        self.bounds = bounds
    
    def levy_flight(self, current_pos, best_pos, alpha=0.01):
        """Implement Lévy flight using Eq.(3.28)-(3.33)"""
        beta = 1.5
        sigma = self.calculate_sigma(beta)
        u = np.random.normal(0, sigma)
        v = np.random.normal(0, 1)
        step = u / (abs(v) ** (1/beta))
        
        new_pos = current_pos + alpha * step * (best_pos - current_pos)
        return self.apply_bounds(new_pos)
    
    def optimize(self, max_iterations=100, population_size=50):
        """Main optimization loop"""
        # Initialize population
        # Evaluate fitness
        # Update positions using Lévy flight
        # Return best solution
```

### 5. Analysis Phase
```python
# monte_carlo.py
class MonteCarloSimulation:
    def __init__(self, num_simulations=1000):
        self.num_simulations = num_simulations
    
    def simulate_ev_behavior(self, num_evs):
        """Simulate EV arrival/departure using SMCM"""
        results = []
        for _ in range(self.num_simulations):
            # Generate random SOC values
            soc_arrival = np.random.uniform(0.2, 0.95, num_evs)
            # Generate arrival/departure times
            arrival_times = np.random.normal(18, 2, num_evs)
            departure_times = np.random.normal(7, 2, num_evs)
            
            results.append({
                'soc_arrival': soc_arrival,
                'arrival_times': arrival_times,
                'departure_times': departure_times
            })
        return results
```

### 6. Main Execution Pipeline
```python
# main.py
import yaml
from src.utils.data_loader import DataLoader
from src.energy_management.rule_based_ems import RuleBasedEMS
from src.optimization.ialo import ImprovedAntlionOptimizer
from src.analysis.monte_carlo import MonteCarloSimulation
from src.utils.visualization import Visualizer

def main():
    # Load configuration
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Phase 1: Data Loading
    print("Phase 1: Loading data...")
    data_loader = DataLoader(config)
    weather_data = data_loader.load_weather_data()
    load_profile = data_loader.load_load_profile()
    ev_data = data_loader.load_ev_data()
    
    # Phase 2: Component Initialization
    print("Phase 2: Initializing components...")
    components = initialize_components(config['components'])
    
    # Phase 3: Energy Management System
    print("Phase 3: Setting up EMS...")
    ems = RuleBasedEMS(components)
    
    # Phase 4: Optimization
    print("Phase 4: Running optimization...")
    optimizer = ImprovedAntlionOptimizer(
        objective_function=calculate_objectives,
        constraints=config['constraints'],
        bounds=config['bounds']
    )
    
    best_solution = optimizer.optimize(
        max_iterations=config['optimization']['max_iterations'],
        population_size=config['optimization']['population_size']
    )
    
    # Phase 5: Monte Carlo Analysis
    print("Phase 5: Running Monte Carlo simulations...")
    mc_sim = MonteCarloSimulation(config['monte_carlo']['num_simulations'])
    
    ev_scenarios = {}
    for num_evs in [10, 30, 60]:
        ev_scenarios[f'{num_evs}_evs'] = mc_sim.simulate_ev_behavior(num_evs)
    
    # Phase 6: Results Analysis and Visualization
    print("Phase 6: Analyzing results...")
    results = analyze_results(best_solution, ev_scenarios)
    
    # Phase 7: Generate Reports and Visualizations
    print("Phase 7: Generating outputs...")
    visualizer = Visualizer()
    visualizer.plot_optimization_convergence(optimizer.convergence_history)
    visualizer.plot_energy_flows(results['energy_flows'])
    visualizer.plot_economic_analysis(results['economic'])
    
    # Save results
    save_results(results, config['output_dir'])
    
    print("Pipeline completed successfully!")

def calculate_objectives(solution):
    """Calculate COE, LPSP, and REF objectives"""
    # Implement Eq.(3.15), Eq.(3.23), and Eq.(3.24)
    pass

def initialize_components(component_config):
    """Initialize all microgrid components"""
    pass

def analyze_results(solution, scenarios):
    """Analyze optimization results and scenarios"""
    pass

def save_results(results, output_dir):
    """Save all results to files"""
    pass

if __name__ == "__main__":
    main()
```

## Configuration File (config.yaml)
```yaml
# System configuration
location:
  name: "Tripoli, Libya"
  latitude: 32.8872
  longitude: 13.1913

# Data paths
weather_data_path: "data/weather_data.csv"
load_data_path: "data/load_data.csv"
ev_data_path: "data/ev_data.csv"

# Component specifications
components:
  pv:
    rated_power: 5000  # W
    temp_coefficient: -0.0037
    noct: 45
  wind_turbine:
    rated_power: 5000  # W
    cut_in_speed: 2.8  # m/s
    cut_out_speed: 20  # m/s
    rated_speed: 7.5  # m/s
  battery:
    capacity: 35380  # Wh
    soc_min: 0.2
    soc_max: 1.0
    efficiency: 0.85
  ev:
    capacity: 14000  # Wh
    soc_min: 0.2
    soc_max: 0.95

# Optimization parameters
optimization:
  algorithm: "IALO"
  max_iterations: 100
  population_size: 50
  
bounds:
  n_pv: [0, 100]
  n_wt: [0, 50]
  n_bat: [0, 100]
  autonomy_days: [0, 5]

constraints:
  lpsp_max: 0.01
  ref_min: 0.5

# Monte Carlo parameters
monte_carlo:
  num_simulations: 1000
  ev_scenarios: [10, 30, 60]

# Economic parameters
economic:
  interest_rate: 0.03
  project_lifetime: 25
  grid_buy_price: 0.04  # $/kWh
  grid_sell_price: 0.05  # $/kWh

# Output settings
output_dir: "outputs/"
```

## Key Implementation Notes

1. **Modular Design**: Each component is a separate class with clear interfaces
2. **Configuration-Driven**: All parameters are externalized to config files
3. **Scalable**: Easy to add new optimization algorithms or components
4. **Testable**: Each module can be unit tested independently
5. **Reproducible**: Random seeds and configurations ensure reproducibility
6. **Visualization**: Comprehensive plotting functions for all results
7. **Logging**: Built-in logging for debugging and monitoring

## Running the Pipeline

```bash
# Install dependencies
pip install -r requirements.txt

# Run the pipeline
python src/main.py

# Run with custom config
python src/main.py --config custom_config.yaml

# Run specific phases only
python src/main.py --phases optimization,analysis
```

## Output Structure
- Optimization results (CSV, JSON)
- Convergence plots
- Energy flow diagrams
- Economic analysis reports
- Monte Carlo simulation results
- Sensitivity analysis plots


## Complete System Architecture & Data Flow -

```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                    V2G MICROGRID OPTIMIZATION PIPELINE                           ║
║              Vehicle-to-Grid Integration with Renewable Energy                   ║
║                   Location: Tripoli, Libya (32.8872°N, 13.1913°E)               ║
╚══════════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: CONFIGURATION & DATA PREPARATION                                        │
└──────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
    │  config.yaml    │      │  DataLoader     │      │  Input Data     │
    │  ─────────────  │      │  ─────────────  │      │  ─────────────  │
    │ • System params │──────│ • Weather data  │──────│ • Solar (G)     │
    │ • Bounds        │      │ • Load profile  │      │ • Wind (v)      │
    │ • Constraints   │      │ • EV patterns   │      │ • Temperature   │
    │ • Economics     │      │ • Validation    │      │ • Load demand   │
    │ • Algorithms    │      │ • Preprocessing │      │ • EV SOC/times  │
    └─────────────────┘      └─────────────────┘      └─────────────────┘
              │                       │                       │
              └───────────────────────┴───────────────────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │   8760 Hourly Data    │
                          │   (Full Year 2024)    │
                          └───────────────────────┘
                                      │
                                      ▼

┌──────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: COMPONENT MODELING & INITIALIZATION                                     │
└──────────────────────────────────────────────────────────────────────────────────┘

 ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
 │ PV System       │  │ Wind Turbine    │  │ Battery System  │  │ EV Fleet        │
 │ ─────────────   │  │ ─────────────   │  │ ─────────────   │  │ ─────────────   │
 │ Eq. 3.1, 3.2    │  │ Eq. 3.3         │  │ SOC Management  │  │ V2G/G2V Modes   │
 │                 │  │                 │  │                 │  │                 │
 │ P_pv = P_rated  │  │ P_wt = f(v)     │  │ E_bat(t+1) =    │  │ E_ev(t+1) =     │
 │  × (G/1000)     │  │                 │  │  E_bat(t) ±     │  │  E_ev(t) ±      │
 │  × [1+α(Tc-25)] │  │ v_ci  = 2.8 m/s │  │  P_ch/dis × η   │  │  P_ch/dis       │
 │                 │  │ v_r   = 7.5 m/s │  │                 │  │                 │
 │ T_c = T_amb +   │  │ v_co  = 20 m/s  │  │ Capacity: 35kWh │  │ Capacity: 14kWh │
 │  G×(NOCT-20)    │  │                 │  │ η = 0.85        │  │ SOC: [0.2,0.95] │
 │  /800           │  │ P_rated = 5 kW  │  │ SOC: [0.2,1.0]  │  │                 │
 │                 │  │                 │  │ DoD Management  │  │ T_arr ~ N(18,2) │
 │ P_rated = 5 kW  │  │ Cut-in/Cut-out  │  │ Autonomy Days   │  │ T_dep ~ N(7,2)  │
 │ α = -0.0037/°C  │  │ Piecewise curve │  │ Cycle tracking  │  │ Availability    │
 │ NOCT = 45°C     │  │                 │  │                 │  │ scheduling      │
 └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │                    │                    │
         └────────────────────┴────────────────────┴────────────────────┘
                                      │
         ┌─────────────────┐  ┌──────┴──────┐  ┌─────────────────┐
         │ Grid Interface  │  │ Converters  │  │ Component Dict  │
         │ ─────────────   │  │ ─────────── │  │ ───────────────  │
         │ Buy: $0.04/kWh  │  │ DC/DC: PV   │  │ components = {  │
         │ Sell: $0.05/kWh │  │ DC/DC: Bat  │  │   'pv': PV,     │
         │ Import/Export   │  │ DC/AC: Grid │  │   'wt': WT,     │
         │ Net metering    │  │ Efficiency  │  │   'bt': Bat,    │
         │ Cost tracking   │  │ losses      │  │   'ev': EV,     │
         └─────────────────┘  └─────────────┘  │   'grid': Grid} │
                                               └─────────────────┘
                                                       │
                                                       ▼

┌──────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: RULE-BASED ENERGY MANAGEMENT SYSTEM (RB-EMS)                           │
└──────────────────────────────────────────────────────────────────────────────────┘

                        ┌─────────────────────────────┐
                        │   Decision Logic Flow       │
                        │   Every Hour (t = 1..8760)  │
                        └─────────────────────────────┘
                                      │
                                      ▼
                        ┌─────────────────────────────┐
                        │  Calculate P_renewable(t)   │
                        │  P_ren = P_pv(t) + P_wt(t)  │
                        └─────────────────────────────┘
                                      │
                                      ▼
                  ┌───────────────────────────────────────┐
                  │  Compare with Load: P_load(t)         │
                  └───────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
  ┌───────────────┐         ┌─────────────────┐        ┌──────────────────┐
  │  SURPLUS      │         │  BALANCED       │        │  DEFICIT         │
  │  P_ren > Load │         │  P_ren = Load   │        │  P_ren < Load    │
  └───────────────┘         └─────────────────┘        └──────────────────┘
          │                           │                           │
          ▼                           ▼                           ▼
  ┌───────────────┐         ┌─────────────────┐        ┌──────────────────┐
  │ MODE 1        │         │  Direct Supply  │        │  Check Battery   │
  │ ─────────     │         │  No storage     │        │  SOC_bat > Min?  │
  │ Supply load   │         │  needed         │        └──────────────────┘
  │ Charge battery│         └─────────────────┘                 │
  │ Charge EV (G2V)│       ┌──────────────────┐         ┌──────┴──────┐
  │ Sell to grid   │       │  EV Available?   │         │             │
  │ (if capacity)  │       │  Opportunistic   │        YES           NO
  └───────────────┘        │  charging        │         │             │
                           └──────────────────┘         ▼             ▼
                                                ┌──────────────┐ ┌──────────┐
  ┌─────────────────────────────────────────┐  │  MODE 2      │ │ MODE 3   │
  │  OPERATION MODES SUMMARY                │  │  ──────────  │ │ ──────── │
  │  ───────────────────────────────────    │  │ Discharge    │ │ Buy from │
  │                                          │  │ battery to   │ │ grid     │
  │  MODE 1: Renewable Supply Direct        │  │ meet load    │ │          │
  │    - P_ren ≥ P_load                     │  │              │ │ P_grid = │
  │    - Load satisfied first               │  │ Update SOC   │ │ P_deficit│
  │    - Excess to battery/EV/grid          │  │              │ │          │
  │                                          │  │ DoD tracking │ │ Cost +=  │
  │  MODE 2: Battery Discharge              │  │              │ │ Buy_price│
  │    - P_ren < P_load                     │  └──────────────┘ └──────────┘
  │    - SOC_bat > SOC_min (20%)            │         │             │
  │    - Supply deficit from battery        │         └──────┬──────┘
  │                                          │                │
  │  MODE 3: Grid Import (G2V)              │                ▼
  │    - P_ren + P_bat < P_load             │      ┌──────────────────┐
  │    - Buy from grid                      │      │  MODE 4 (V2G)    │
  │    - Charge EVs when available          │      │  Check EV Fleet  │
  │                                          │      │  ──────────────  │
  │  MODE 4: Vehicle-to-Grid (V2G)          │      │ If EVs available │
  │    - Critical deficit                   │      │ & SOC_ev > 0.5   │
  │    - EVs available (connected)          │      │ Discharge to grid│
  │    - SOC_ev > threshold (50%)           │      │ Support system   │
  │    - Discharge EVs to support system    │      │ Update SOC_ev    │
  └─────────────────────────────────────────┘      └──────────────────┘
                                                              │
                                                              ▼
                                              ┌────────────────────────┐
                                              │  Record Metrics (t)    │
                                              │  ──────────────────    │
                                              │ • P_load_met(t)        │
                                              │ • P_load_unmet(t)      │
                                              │ • P_grid_import(t)     │
                                              │ • P_grid_export(t)     │
                                              │ • E_bat(t), SOC_bat(t) │
                                              │ • E_ev(t), SOC_ev(t)   │
                                              │ • P_renewable_used(t)  │
                                              │ • Cost_grid(t)         │
                                              └────────────────────────┘
                                                              │
                                                              ▼
                                              ┌────────────────────────┐
                                              │  t = t + 1             │
                                              │  Loop: t = 1..8760     │
                                              └────────────────────────┘
                                                              │
                                                              ▼

┌──────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: MULTI-OBJECTIVE OPTIMIZATION (Component Sizing)                         │
└──────────────────────────────────────────────────────────────────────────────────┘

                    ┌───────────────────────────────────────┐
                    │  Decision Variables: X = [x₁,x₂,x₃,x₄]│
                    │  ─────────────────────────────────────│
                    │  x₁: N_pv  ∈ [0, 100]    (PV panels)  │
                    │  x₂: N_wt  ∈ [0, 50]     (Wind units) │
                    │  x₃: N_bt  ∈ [0, 100]    (Batteries)  │
                    │  x₄: AD    ∈ [0, 5]      (Auto. days) │
                    └───────────────────────────────────────┘
                                      │
                                      ▼
              ┌────────────────────────────────────────────┐
              │  Objective Function: Multi-criteria       │
              │  ─────────────────────────────────────────│
              │                                            │
              │  f(X) = w·COE + (1-w)·γ·pf·LPSP - w·REF  │
              │                                            │
              │  where: w = 0.5  (weight factor)          │
              │         γ = 1000 (penalty coefficient)    │
              │         pf = penalty function             │
              └────────────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
  ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
  │  Minimize COE    │      │  Minimize LPSP   │      │  Maximize REF    │
  │  ────────────    │      │  ─────────────   │      │  ────────────    │
  │  Eq. 3.15        │      │  Eq. 3.23        │      │  Eq. 3.24        │
  │                  │      │                  │      │                  │
  │  COE = NPC       │      │      Σ LPSP(t)   │      │      Σ E_ren(t)  │
  │       ─────      │      │ LPSP = ────────  │      │ REF = ──────────│
  │       Σ E_load   │      │      Σ E_load(t) │      │      Σ E_load(t) │
  │                  │      │                  │      │                  │
  │ NPC = C_cap +    │      │ where:           │      │ where:           │
  │       C_repl +   │      │ LPSP(t) = unmet  │      │ E_ren = P_pv +   │
  │       C_O&M -    │      │ load at hour t   │      │         P_wt     │
  │       C_salvage  │      │                  │      │                  │
  │                  │      │ Constraint:      │      │ Constraint:      │
  │ Target: $/kWh    │      │ LPSP ≤ 0.01 (1%) │      │ REF ≥ 0.5 (50%)  │
  │ (Minimize)       │      │ (Max 88 hrs/year)│      │ (Maximize)       │
  └──────────────────┘      └──────────────────┘      └──────────────────┘
          │                           │                           │
          └───────────────────────────┴───────────────────────────┘
                                      │
                                      ▼

  ╔══════════════════════════════════════════════════════════════════════╗
  ║              OPTIMIZATION ALGORITHMS COMPARISON                      ║
  ╚══════════════════════════════════════════════════════════════════════╝

  ┌────────────────────────────────────────────────────────────────────────┐
  │ 1. IALO (Improved Ant Lion Optimizer) - PRIMARY ALGORITHM             │
  │ ──────────────────────────────────────────────────────────────────────│
  │                                                                        │
  │  Initialize: N_ant = 50 antlions, Max_iter = 100                      │
  │                                                                        │
  │  FOR each iteration t = 1 to Max_iter:                                │
  │                                                                        │
  │    1. Evaluate fitness of all ants (candidate solutions)              │
  │       f_i = objective_function(X_i) for i = 1..50                     │
  │                                                                        │
  │    2. Select elite antlions (best solutions)                          │
  │       Elite = antlions with lowest fitness                            │
  │                                                                        │
  │    3. For each ant, perform random walk around:                       │
  │       a) Random antlion (roulette wheel selection)                    │
  │       b) Elite antlion                                                │
  │                                                                        │
  │    4. Apply LÉVY FLIGHT mechanism (Eq. 3.28-3.33):                   │
  │       ┌─────────────────────────────────────────────────┐            │
  │       │  Lévy(λ) ~ u/|v|^(1/β)   where β = 1.5         │            │
  │       │                                                  │            │
  │       │  σ_u = [Γ(1+β)·sin(πβ/2)]^(1/β)                │            │
  │       │        ─────────────────────────────            │            │
  │       │        Γ((1+β)/2)·β·2^((β-1)/2)                │            │
  │       │                                                  │            │
  │       │  u ~ N(0, σ_u²)                                 │            │
  │       │  v ~ N(0, 1)                                    │            │
  │       │                                                  │            │
  │       │  Step = α · Lévy(λ) · (X_best - X_current)     │            │
  │       │                                                  │            │
  │       │  X_new = X_current + Step                       │            │
  │       └─────────────────────────────────────────────────┘            │
  │                                                                        │
  │    5. Update antlion positions if ants found better solutions         │
  │                                                                        │
  │    6. Shrink search space (trap building):                            │
  │       c^t = c^t/I    where I = 10^(w·t/Max_iter)                     │
  │                                                                        │
  │    7. Record convergence: best_fitness[t]                             │
  │                                                                        │
  │  END FOR                                                              │
  │                                                                        │
  │  RETURN: X_best (optimal component sizing)                            │
  │                                                                        │
  │  Advantages:                                                          │
  │  • Enhanced exploration via Lévy flights                              │
  │  • Balanced exploitation with elite mechanism                         │
  │  • Faster convergence than standard ALO                               │
  │  • Better global optimum finding                                      │
  └────────────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────────────────┐
  │ 2. ALO (Standard Ant Lion Optimizer) - BASELINE                       │
  │ ──────────────────────────────────────────────────────────────────────│
  │  • Mimics hunting behavior of antlions                                 │
  │  • Random walk of ants in search space                                 │
  │  • Roulette wheel selection for antlions                               │
  │  • No Lévy flights (standard random walk)                              │
  │  • Used for performance comparison                                     │
  └────────────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────────────────┐
  │ 3. PSO (Particle Swarm Optimization) - COMPARISON                     │
  │ ──────────────────────────────────────────────────────────────────────│
  │  • Velocity-based movement: V(t+1) = w·V(t) + c₁·r₁·(pbest-X) +      │
  │                                       c₂·r₂·(gbest-X)                  │
  │  • Position update: X(t+1) = X(t) + V(t+1)                            │
  │  • Personal best (pbest) and Global best (gbest)                       │
  │  • Inertia weight w decreases over iterations                          │
  └────────────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────────────────┐
  │ 4. CSA (Cuckoo Search Algorithm) - COMPARISON                         │
  │ ──────────────────────────────────────────────────────────────────────│
  │  • Lévy flight-based search                                            │
  │  • Parasitic breeding behavior                                         │
  │  • Nest abandonment probability (Pa = 0.25)                            │
  │  • Random nest selection and replacement                               │
  └────────────────────────────────────────────────────────────────────────┘

                                      │
                                      ▼
                    ┌─────────────────────────────────┐
                    │  All Algorithms Output:         │
                    │  • Best solution X*             │
                    │  • Best fitness f(X*)           │
                    │  • Convergence history          │
                    │  • Computation time             │
                    └─────────────────────────────────┘
                                      │
                                      ▼

┌──────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 5: SEQUENTIAL MONTE CARLO METHOD (SMCM) FOR EV BEHAVIOR                   │
└──────────────────────────────────────────────────────────────────────────────────┘

                    ┌───────────────────────────────────────┐
                    │  Monte Carlo Simulation Framework     │
                    │  N_sim = 1000 simulations             │
                    └───────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
  ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
  │ Scenario 1       │      │ Scenario 2       │      │ Scenario 3       │
  │ ────────────     │      │ ────────────     │      │ ────────────     │
  │ 10 EVs           │      │ 30 EVs           │      │ 60 EVs           │
  │ (Low penetration)│      │ (Mid penetration)│      │ (High penetr.)   │
  └──────────────────┘      └──────────────────┘      └──────────────────┘
          │                           │                           │
          └───────────────────────────┴───────────────────────────┘
                                      │
                                      ▼
                    ┌───────────────────────────────────────┐
                    │  FOR each simulation s = 1 to 1000:   │
                    │                                        │
                    │  1. Generate Random Variables:         │
                    │     • SOC_arrival ~ Uniform(0.2,0.95)  │
                    │     • T_arrival ~ Normal(18:00, 2h)    │
                    │     • T_departure ~ Normal(07:00, 2h)  │
                    │     • Trip distance ~ empirical dist   │
                    │                                        │
                    │  2. Calculate for each EV:             │
                    │     • Energy needed for trip           │
                    │     • Available charging window        │
                    │     • V2G availability period          │
                    │     • SOC at departure                 │
                    │                                        │
                    │  3. Run EMS with simulated EV fleet    │
                    │                                        │
                    │  4. Record metrics:                    │
                    │     • LPSP_s, REF_s, COE_s            │
                    │     • Grid import/export_s             │
                    │     • Battery cycles_s                 │
                    │     • EV satisfaction_s                │
                    └────────────────────────────────────────┘
                                      │
                                      ▼
                    ┌───────────────────────────────────────┐
                    │  Statistical Analysis:                 │
                    │  ────────────────────────              │
                    │  • Mean(LPSP), Std(LPSP)              │
                    │  • Mean(REF), Std(REF)                │
                    │  • Mean(COE), Std(COE)                │
                    │  • Confidence intervals (95%)         │
                    │  • Probability distributions          │
                    │  • Risk metrics (VaR, CVaR)           │
                    │  • Sensitivity to N_EV                │
                    └───────────────────────────────────────┘
                                      │
                                      ▼

┌──────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 6: COMPREHENSIVE ANALYSIS & RESULTS PROCESSING                            │
└──────────────────────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────────────────┐
  │ ECONOMIC ANALYSIS (Using Optimal X*)                                   │
  │ ────────────────────────────────────────────────────────────────────── │
  │                                                                        │
  │  1. Net Present Cost (NPC):                                            │
  │     ┌──────────────────────────────────────────────────┐             │
  │     │  NPC = C_cap + Σ[C_O&M(t) + C_repl(t)]·PWF(t)   │             │
  │     │              t=1..25                              │             │
  │     │        - C_salvage·PWF(25)                        │             │
  │     │                                                   │             │
  │     │  where PWF(t) = 1/(1+r)^t   (r = 3%)            │             │
  │     └──────────────────────────────────────────────────┘             │
  │                                                                        │
  │     Component Costs:                                                   │
  │     • PV: $400/panel capital, $10/panel/yr O&M, 25yr life             │
  │     • WT: $5000/turbine capital, $150/turbine/yr O&M, 20yr life       │
  │     • Battery: $200/kWh capital, $5/kWh/yr O&M, 10yr life             │
  │     • Converter: $150/kW capital, $5/kW/yr O&M, 15yr life             │
  │     • EV infrastructure: Variable by N_EV                              │
  │                                                                        │
  │  2. Cost of Energy (COE):                                              │
  │     ┌──────────────────────────────────────────────────┐             │
  │     │           NPC                                     │             │
  │     │  COE = ──────────────                            │             │
  │     │        Σ E_load_served(t)                         │             │
  │     │        t=1..8760×25                               │             │
  │     │                                                   │             │
  │     │  Units: $/kWh                                     │             │
  │     └──────────────────────────────────────────────────┘             │
  │                                                                        │
  │  3. Payback Period:                                                    │
  │     Time until cumulative savings = Initial investment                 │
  │                                                                        │
  │  4. Internal Rate of Return (IRR):                                     │
  │     Discount rate where NPV = 0                                        │
  └────────────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────────────────┐
  │ RELIABILITY ASSESSMENT                                                 │
  │ ────────────────────────────────────────────────────────────────────── │
  │                                                                        │
  │  • Loss of Power Supply Probability (LPSP): 0.01 target               │
  │  • System availability: (8760 - hours_unmet)/8760                     │
  │  • Battery depth of discharge cycles                                   │
  │  • EV fleet reliability contribution                                   │
  │  • Grid dependency index                                               │
  │  • System autonomy hours/days                                          │
  └────────────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────────────────┐
  │ ENVIRONMENTAL IMPACT                                                   │
  │ ────────────────────────────────────────────────────────────────────── │
  │                                                                        │
  │  Renewable Energy Metrics:                                             │
  │    • Renewable Energy Fraction (REF): 0.5 minimum target               │
  │    • CO₂ emissions avoided = E_renewable × grid_carbon_intensity       │
  │    • Fossil fuel displacement (liters/year)                            │
  │    • Carbon footprint reduction (tons CO₂/year)                        │
  │    • Lifecycle emissions analysis                                      │
  │    • Environmental benefit-cost ratio                                  │
  │                                                                        │
  │  Grid Carbon Intensity (Libya):                                        │
  │    • Baseline: ~0.68 kg CO₂/kWh (fossil fuel grid)                    │
  │    • Renewable generation offset calculation                           │
  │    • Net environmental impact                                          │
  └────────────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────────────────┐
  │ SENSITIVITY ANALYSIS                                                   │
  │ ────────────────────────────────────────────────────────────────────── │
  │                                                                        │
  │  Varying Parameters (±20%):                                            │
  │    • Solar irradiance (weather uncertainty)                            │
  │    • Wind speed patterns                                               │
  │    • Load demand variations                                            │
  │    • EV penetration levels (10, 30, 60 EVs)                           │
  │    • Component costs (±20%)                                            │
  │    • Grid prices (buy/sell rates)                                      │
  │    • Interest rate (1%-5%)                                             │
  │    • Battery/EV degradation rates                                      │
  │                                                                        │
  │  Analysis Methods:                                                     │
  │    • One-at-a-time (OAT) sensitivity                                   │
  │    • Tornado diagrams for visual comparison                            │
  │    • Sensitivity indices (normalized impact)                           │
  │    • Multi-parameter interaction effects                               │
  │                                                                        │
  │  Output: Ranking of most influential parameters                        │
  └────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 7: OUTPUT GENERATION & VISUALIZATION                                       │
└──────────────────────────────────────────────────────────────────────────────────┘

                    ┌───────────────────────────────────────┐
                    │  ALGORITHM-SPECIFIC OUTPUT STRUCTURE  │
                    │  Each algorithm gets its own tree:    │
                    └───────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
  ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
  │ outputs/ialo/    │      │ outputs/alo/     │      │ outputs/pso/     │
  │ run_YYYYMMDD_    │      │ run_YYYYMMDD_    │      │ run_YYYYMMDD_    │
  │ HHMMSS/          │      │ HHMMSS/          │      │ HHMMSS/          │
  └──────────────────┘      └──────────────────┘      └──────────────────┘
          │                           │                           │
          └───────────────────────────┴───────────────────────────┘
                                      │
                                      ▼
              ┌──────────────────────────────────────────────┐
              │  DIRECTORY STRUCTURE (Per Algorithm Run)    │
              │  ─────────────────────────────────────────── │
              │                                              │
              │  📁 optimization_results/                    │
              │     • {algorithm}_best_solution.csv          │
              │     • {algorithm}_economic_analysis.csv      │
              │     • component_sizing_details.csv           │
              │     • constraint_satisfaction.csv            │
              │                                              │
              │  📁 figures/                                 │
              │     • {algorithm}_convergence.png            │
              │     • {algorithm}_energy_flows.png           │
              │     • {algorithm}_economic_analysis.png      │
              │     • {algorithm}_component_sizing.png       │
              │     • {algorithm}_monte_carlo_analysis.png   │
              │     • power_balance_hourly.png               │
              │     • soc_tracking.png                       │
              │     • grid_interaction.png                   │
              │                                              │
              │  📁 reports/                                 │
              │     • {algorithm}_summary_report.txt         │
              │     • detailed_analysis.html                 │
              │     • comparison_metrics.md                  │
              │                                              │
              │  📁 raw_data/                                │
              │     • {algorithm}_convergence.csv            │
              │     • {algorithm}_energy_flows.csv           │
              │     • hourly_simulation_data.csv             │
              │     • monte_carlo_results.csv                │
              │                                              │
              │  📄 config_used.yaml                         │
              │  📄 pipeline_YYYYMMDD_HHMMSS.log            │
              └──────────────────────────────────────────────┘
                                      │
                                      ▼

  ╔══════════════════════════════════════════════════════════════════════╗
  ║                    VISUALIZATION OUTPUTS                             ║
  ╚══════════════════════════════════════════════════════════════════════╝

  ┌────────────────────────────────────────────────────────────────────────┐
  │ 1. CONVERGENCE PLOTS                                                   │
  │ ────────────────────────────────────────────────────────────────────── │
  │                                                                        │
  │  Graph: Fitness vs. Iteration                                          │
  │  • X-axis: Iteration number (1-100)                                    │
  │  • Y-axis: Best fitness value                                          │
  │  • Shows optimization progress                                         │
  │  • Comparative overlay of all algorithms                               │
  │  • Convergence rate analysis                                           │
  │  • Final fitness comparison                                            │
  └────────────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────────────────┐
  │ 2. ENERGY FLOW DIAGRAMS                                                │
  │ ────────────────────────────────────────────────────────────────────── │
  │                                                                        │
  │  Sankey Diagram / Stacked Area Chart:                                  │
  │  • PV generation profile (8760 hrs)                                    │
  │  • Wind generation profile (8760 hrs)                                  │
  │  • Battery charge/discharge cycles                                     │
  │  • EV charging patterns (G2V/V2G)                                      │
  │  • Load demand curve                                                   │
  │  • Grid import/export                                                  │
  │  • Power balance verification                                          │
  │                                                                        │
  │  Time scales: Hourly, Daily, Monthly, Annual                           │
  └────────────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────────────────┐
  │ 3. COMPONENT SIZING VISUALIZATION                                      │
  │ ────────────────────────────────────────────────────────────────────── │
  │                                                                        │
  │  Bar Charts:                                                           │
  │  • N_pv: Number of PV panels                                           │
  │  • N_wt: Number of wind turbines                                       │
  │  • N_bt: Number of battery units                                       │
  │  • AD: Autonomy days                                                   │
  │  • Comparison across algorithms                                        │
  │  • Cost breakdown per component                                        │
  └────────────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────────────────┐
  │ 4. ECONOMIC ANALYSIS CHARTS                                            │
  │ ────────────────────────────────────────────────────────────────────── │
  │                                                                        │
  │  Multi-panel Figure:                                                   │
  │  • COE comparison ($/kWh)                                              │
  │  • NPC breakdown (capital, O&M, replacement, salvage)                  │
  │  • Payback period timeline                                             │
  │  • Cash flow over 25 years                                             │
  │  • Sensitivity tornado diagram                                         │
  │  • Cost-benefit ratio                                                  │
  └────────────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────────────────┐
  │ 5. MONTE CARLO RESULTS                                                 │
  │ ────────────────────────────────────────────────────────────────────── │
  │                                                                        │
  │  Statistical Plots:                                                    │
  │  • Probability distribution of LPSP                                    │
  │  • Probability distribution of REF                                     │
  │  • Probability distribution of COE                                     │
  │  • Box plots by EV scenario (10, 30, 60 EVs)                          │
  │  • Confidence intervals (95%)                                          │
  │  • Risk curves (VaR, CVaR)                                             │
  │  • Scenario comparison heatmaps                                        │
  └────────────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────────────────┐
  │ 6. RELIABILITY & PERFORMANCE METRICS                                   │
  │ ────────────────────────────────────────────────────────────────────── │
  │                                                                        │
  │  Dashboard View:                                                       │
  │  • LPSP gauge (target: ≤ 0.01)                                         │
  │  • REF gauge (target: ≥ 0.5)                                           │
  │  • System availability %                                               │
  │  • Battery cycle count                                                 │
  │  • EV satisfaction rate                                                │
  │  • Grid dependency index                                               │
  │  • Unmet load hours histogram                                          │
  └────────────────────────────────────────────────────────────────────────┘

                                      │
                                      ▼

  ╔══════════════════════════════════════════════════════════════════════╗
  ║                    SUMMARY REPORT CONTENT                            ║
  ╚══════════════════════════════════════════════════════════════════════╝

  ┌────────────────────────────────────────────────────────────────────────┐
  │  V2G MICROGRID OPTIMIZATION SUMMARY REPORT                             │
  │  Algorithm: {IALO/ALO/PSO/CSA}                                         │
  │  Timestamp: YYYY-MM-DD HH:MM:SS                                        │
  │  ══════════════════════════════════════════════════════════════════    │
  │                                                                        │
  │  OPTIMIZATION RESULTS:                                                 │
  │  ══════════════════════                                                │
  │  • PV Panels (N_pv): XX units                                          │
  │  • Wind Turbines (N_wt): XX units                                      │
  │  • Battery Units (N_bt): XX units                                      │
  │  • Autonomy Days (AD): XX.XX days                                      │
  │  • Best Fitness: XXXX.XXXX                                             │
  │  • Convergence Iterations: XXX                                         │
  │  • Computation Time: XX.XX seconds                                     │
  │                                                                        │
  │  ECONOMIC METRICS:                                                     │
  │  ══════════════════                                                    │
  │  • Cost of Energy (COE): $X.XXXX/kWh                                   │
  │  • Net Present Cost (NPC): $XXX,XXX.XX                                 │
  │  • Total Capital Cost: $XXX,XXX.XX                                     │
  │  • Annual O&M Cost: $XX,XXX.XX                                         │
  │  • Payback Period: XX.X years                                          │
  │  • Internal Rate of Return: XX.X%                                      │
  │                                                                        │
  │  RELIABILITY METRICS:                                                  │
  │  ══════════════════════                                                │
  │  • LPSP: X.XXXX (Target: ≤ 0.01) [PASS/FAIL]                          │
  │  • Unmet Load Hours: XXX hours/year                                    │
  │  • System Availability: XX.XX%                                         │
  │  • Battery Cycles/Year: XXXX                                           │
  │  • Grid Dependency: XX.XX%                                             │
  │                                                                        │
  │  ENVIRONMENTAL IMPACT:                                                 │
  │  ═══════════════════════                                               │
  │  • Renewable Energy Fraction (REF): X.XXXX (Target: ≥ 0.5) [PASS/FAIL]│
  │  • Annual Renewable Energy: XXX,XXX kWh                                │
  │  • CO₂ Emissions Avoided: XX.XX tons/year                              │
  │  • Fossil Fuel Displaced: XX,XXX liters/year                           │
  │                                                                        │
  │  EV FLEET PERFORMANCE (Monte Carlo Analysis):                          │
  │  ═══════════════════════════════════════════                           │
  │  Scenario 1 (10 EVs):                                                  │
  │    • Mean LPSP: X.XXXX ± X.XXXX                                        │
  │    • Mean REF: X.XXXX ± X.XXXX                                         │
  │    • Mean COE: $X.XXXX ± $X.XXXX                                       │
  │                                                                        │
  │  Scenario 2 (30 EVs):                                                  │
  │    • Mean LPSP: X.XXXX ± X.XXXX                                        │
  │    • Mean REF: X.XXXX ± X.XXXX                                         │
  │    • Mean COE: $X.XXXX ± $X.XXXX                                       │
  │                                                                        │
  │  Scenario 3 (60 EVs):                                                  │
  │    • Mean LPSP: X.XXXX ± X.XXXX                                        │
  │    • Mean REF: X.XXXX ± X.XXXX                                         │
  │    • Mean COE: $X.XXXX ± $X.XXXX                                       │
  │                                                                        │
  │  KEY FINDINGS:                                                         │
  │  ══════════════                                                        │
  │  1. Optimal component sizing achieved                                  │
  │  2. All constraints satisfied: LPSP ≤ 0.01, REF ≥ 0.5                 │
  │  3. {Algorithm} converged in XXX iterations                            │
  │  4. System is economically viable with XX.X year payback              │
  │  5. High EV penetration improves grid stability via V2G               │
  │                                                                        │
  │  OUTPUT FILES:                                                         │
  │  ══════════════                                                        │
  │  • Optimization: optimization_results/{algorithm}_best_solution.csv    │
  │  • Economics: optimization_results/{algorithm}_economic_analysis.csv   │
  │  • Convergence: raw_data/{algorithm}_convergence.csv                   │
  │  • Energy Flows: raw_data/{algorithm}_energy_flows.csv                 │
  │  • All Figures: figures/*.png                                          │
  └────────────────────────────────────────────────────────────────────────┘

                                      │
                                      ▼

  ╔══════════════════════════════════════════════════════════════════════╗
  ║                    PIPELINE COMPLETION                               ║
  ╚══════════════════════════════════════════════════════════════════════╝

                    ┌───────────────────────────────────────┐
                    │  FINAL LOGGING & CLEANUP              │
                    │  ────────────────────────────────────  │
                    │                                        │
                    │  ✓ All phases completed successfully   │
                    │  ✓ Results saved to algorithm directory│
                    │  ✓ Visualizations generated            │
                    │  ✓ Reports created                     │
                    │  ✓ Log file closed                     │
                    │  ✓ Configuration archived              │
                    │                                        │
                    │  Total Runtime: XX minutes XX seconds  │
                    │  Peak Memory Usage: XXXX MB            │
                    │  Files Generated: XXX                  │
                    └───────────────────────────────────────┘
                                      │
                                      ▼
                    ┌───────────────────────────────────────┐
                    │  READY FOR:                            │
                    │  • Algorithm comparison analysis       │
                    │  • Thesis/paper integration            │
                    │  • Sensitivity studies                 │
                    │  • What-if scenario analysis           │
                    │  • Presentation generation             │
                    └───────────────────────────────────────┘

═════════════════════════════════════════════════════════════════════════════
                          END OF PIPELINE ARCHITECTURE
═════════════════════════════════════════════════════════════════════════════