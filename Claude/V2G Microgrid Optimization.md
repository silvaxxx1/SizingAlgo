# V2G Microgrid Optimization Pipeline

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
