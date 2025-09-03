#!/usr/bin/env python3
"""
V2G Microgrid Optimization Pipeline - Main Execution Script
Based on the thesis framework for Vehicle-to-Grid integration with renewable energy sources

Author: V2G Research Team
Date: 2024
"""

import os
import sys
import yaml
import argparse
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from utils.data_loader import DataLoader
from components import PhotovoltaicSystem, WindTurbine, BatterySystem, ElectricVehicle, Grid
from energy_management.rule_based_ems import RuleBasedEMS
from optimization.ialo import ImprovedAntlionOptimizer
from optimization.alo import AntlionOptimizer
from optimization.pso import ParticleSwarmOptimizer
from optimization.csa import CuckooSearchAlgorithm
from analysis.monte_carlo import MonteCarloSimulation
from analysis.economic_analysis import EconomicAnalysis
from analysis.sensitivity_analysis import SensitivityAnalysis
from utils.visualization import Visualizer
from utils.constants import *

def setup_logging(log_level='INFO'):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('outputs/pipeline.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_configuration(config_path='config.yaml'):
    """Load pipeline configuration"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def initialize_components(config):
    """Initialize all microgrid components"""
    components = {}
    
    # Photovoltaic System
    pv_config = config['components']['pv']
    components['pv'] = PhotovoltaicSystem(
        rated_power=pv_config['rated_power'],
        temp_coefficient=pv_config['temp_coefficient'],
        noct=pv_config['noct']
    )
    
    # Wind Turbine System
    wt_config = config['components']['wind_turbine']
    components['wt'] = WindTurbine(
        rated_power=wt_config['rated_power'],
        cut_in_speed=wt_config['cut_in_speed'],
        cut_out_speed=wt_config['cut_out_speed'],
        rated_speed=wt_config['rated_speed']
    )
    
    # Battery System
    bt_config = config['components']['battery']
    components['bt'] = BatterySystem(
        capacity=bt_config['capacity'],
        soc_min=bt_config['soc_min'],
        soc_max=bt_config['soc_max'],
        efficiency=bt_config['efficiency']
    )
    
    # Electric Vehicle
    ev_config = config['components']['ev']
    components['ev'] = ElectricVehicle(
        capacity=ev_config['capacity'],
        soc_min=ev_config['soc_min'],
        soc_max=ev_config['soc_max']
    )
    
    # Grid
    economic_config = config['economic']
    components['grid'] = Grid(
        buy_price=economic_config['grid_buy_price'],
        sell_price=economic_config['grid_sell_price']
    )
    
    logging.info("All components initialized successfully")
    return components

def calculate_objectives(solution, data, components, config):
    """Calculate COE, LPSP, and REF objectives for a given solution"""
    # Extract solution parameters
    n_pv, n_wt, n_bt, autonomy_days = solution
    
    # Update component counts
    components['pv'].set_count(int(n_pv))
    components['wt'].set_count(int(n_wt))
    components['bt'].set_count(int(n_bt))
    components['bt'].set_autonomy_days(autonomy_days)
    
    # Initialize EMS
    ems = RuleBasedEMS(components)
    
    # Simulate one year operation
    results = ems.simulate_year(data)
    
    # Calculate objectives
    economic_analysis = EconomicAnalysis(config['economic'])
    
    # COE calculation
    coe = economic_analysis.calculate_coe(
        components, results, config['economic']['project_lifetime']
    )
    
    # LPSP calculation
    lpsp = economic_analysis.calculate_lpsp(results)
    
    # REF calculation
    ref = economic_analysis.calculate_ref(results)
    
    return coe, lpsp, ref

def run_optimization(config, data, components, algorithm='IALO'):
    """Run optimization with specified algorithm"""
    
    # Define bounds
    bounds = [
        (config['bounds']['n_pv'][0], config['bounds']['n_pv'][1]),
        (config['bounds']['n_wt'][0], config['bounds']['n_wt'][1]),
        (config['bounds']['n_bt'][0], config['bounds']['n_bt'][1]),
        (config['bounds']['autonomy_days'][0], config['bounds']['autonomy_days'][1])
    ]
    
    # Define objective function
    def objective_function(solution):
        coe, lpsp, ref = calculate_objectives(solution, data, components, config)
        
        # Multi-objective combination (Equation 3.25 from thesis)
        w = 0.5  # weighting factor
        gamma = 1000  # scaling factor
        pf = 1.0  # balancing factor
        
        # Combine objectives: minimize COE and LPSP, maximize REF
        fitness = w * coe + (1 - w) * gamma * pf * lpsp - w * ref
        
        # Apply constraints
        if lpsp > config['constraints']['lpsp_max']:
            fitness += 1000  # penalty
        if ref < config['constraints']['ref_min']:
            fitness += 1000  # penalty
            
        return fitness
    
    # Initialize optimizer
    opt_config = config['optimization']
    
    if algorithm == 'IALO':
        optimizer = ImprovedAntlionOptimizer(
            objective_function=objective_function,
            bounds=bounds,
            population_size=opt_config['population_size'],
            max_iterations=opt_config['max_iterations']
        )
    elif algorithm == 'ALO':
        optimizer = AntlionOptimizer(
            objective_function=objective_function,
            bounds=bounds,
            population_size=opt_config['population_size'],
            max_iterations=opt_config['max_iterations']
        )
    elif algorithm == 'PSO':
        optimizer = ParticleSwarmOptimizer(
            objective_function=objective_function,
            bounds=bounds,
            swarm_size=opt_config['population_size'],
            max_iterations=opt_config['max_iterations']
        )
    elif algorithm == 'CSA':
        optimizer = CuckooSearchAlgorithm(
            objective_function=objective_function,
            bounds=bounds,
            population_size=opt_config['population_size'],
            max_iterations=opt_config['max_iterations']
        )
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    
    logging.info(f"Running optimization with {algorithm}")
    best_solution, best_fitness, convergence_history = optimizer.optimize()
    
    return best_solution, best_fitness, convergence_history

def run_monte_carlo_analysis(config, best_solution, data, components):
    """Run Monte Carlo simulation for EV behavior analysis"""
    
    logging.info("Starting Monte Carlo analysis")
    
    mc_config = config['monte_carlo']
    mc_sim = MonteCarloSimulation(
        num_simulations=mc_config['num_simulations']
    )
    
    ev_scenarios = {}
    
    for num_evs in mc_config['ev_scenarios']:
        logging.info(f"Simulating scenario with {num_evs} EVs")
        
        scenarios = mc_sim.simulate_ev_behavior(
            num_evs=num_evs,
            data=data,
            components=components,
            solution=best_solution
        )
        
        ev_scenarios[f'{num_evs}_evs'] = scenarios
    
    return ev_scenarios

def analyze_results(best_solution, ev_scenarios, data, components, config):
    """Analyze optimization results and scenarios"""
    
    logging.info("Analyzing results")
    
    results = {
        'optimization': {
            'best_solution': best_solution,
            'component_sizing': {
                'n_pv': int(best_solution[0]),
                'n_wt': int(best_solution[1]),
                'n_bt': int(best_solution[2]),
                'autonomy_days': best_solution[3]
            }
        },
        'monte_carlo': ev_scenarios,
        'economic': {},
        'energy_flows': {}
    }
    
    # Economic analysis
    economic_analysis = EconomicAnalysis(config['economic'])
    
    # Update components with best solution
    components['pv'].set_count(int(best_solution[0]))
    components['wt'].set_count(int(best_solution[1]))
    components['bt'].set_count(int(best_solution[2]))
    
    # Calculate final metrics
    ems = RuleBasedEMS(components)
    simulation_results = ems.simulate_year(data)
    
    results['economic'] = {
        'coe': economic_analysis.calculate_coe(components, simulation_results, 
                                             config['economic']['project_lifetime']),
        'lpsp': economic_analysis.calculate_lpsp(simulation_results),
        'ref': economic_analysis.calculate_ref(simulation_results),
        'npc': economic_analysis.calculate_npc(components, 
                                              config['economic']['project_lifetime'],
                                              config['economic']['interest_rate'])
    }
    
    results['energy_flows'] = simulation_results
    
    return results

def generate_outputs(results, convergence_histories, config):
    """Generate reports and visualizations"""
    
    logging.info("Generating outputs")
    
    output_dir = Path(config['output_dir'])
    output_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    (output_dir / 'optimization_results').mkdir(exist_ok=True)
    (output_dir / 'figures').mkdir(exist_ok=True)
    (output_dir / 'reports').mkdir(exist_ok=True)
    
    # Initialize visualizer
    visualizer = Visualizer()
    
    # Save optimization results
    opt_results = pd.DataFrame([results['optimization']['component_sizing']])
    opt_results.to_csv(output_dir / 'optimization_results' / 'best_solution.csv', index=False)
    
    # Save economic results
    economic_results = pd.DataFrame([results['economic']])
    economic_results.to_csv(output_dir / 'optimization_results' / 'economic_analysis.csv', index=False)
    
    # Generate plots
    figures_dir = output_dir / 'figures'
    
    # Convergence plots for all algorithms
    for alg_name, history in convergence_histories.items():
        visualizer.plot_convergence(
            history, 
            title=f'{alg_name} Convergence',
            save_path=figures_dir / f'{alg_name.lower()}_convergence.png'
        )
    
    # Energy flow diagrams
    visualizer.plot_energy_flows(
        results['energy_flows'],
        save_path=figures_dir / 'energy_flows.png'
    )
    
    # Monte Carlo results
    visualizer.plot_monte_carlo_results(
        results['monte_carlo'],
        save_path=figures_dir / 'monte_carlo_analysis.png'
    )
    
    # Economic analysis plots
    visualizer.plot_economic_analysis(
        results['economic'],
        save_path=figures_dir / 'economic_analysis.png'
    )
    
    # Component sizing visualization
    visualizer.plot_component_sizing(
        results['optimization']['component_sizing'],
        save_path=figures_dir / 'component_sizing.png'
    )
    
    logging.info(f"All outputs saved to {output_dir}")

def run_sensitivity_analysis(config, data, components):
    """Run sensitivity analysis on key parameters"""
    
    logging.info("Running sensitivity analysis")
    
    sensitivity = SensitivityAnalysis()
    
    # Define parameters to analyze
    parameters = {
        'solar_irradiance': np.linspace(0.8, 1.2, 5),
        'wind_speed': np.linspace(0.8, 1.2, 5),
        'load_demand': np.linspace(0.8, 1.2, 5),
        'battery_cost': np.linspace(0.8, 1.2, 5)
    }
    
    sensitivity_results = sensitivity.analyze_parameters(
        parameters, data, components, config
    )
    
    # Save sensitivity results
    output_dir = Path(config['output_dir'])
    sensitivity_df = pd.DataFrame(sensitivity_results)
    sensitivity_df.to_csv(output_dir / 'reports' / 'sensitivity_analysis.csv', index=False)
    
    return sensitivity_results

def main():
    """Main pipeline execution"""
    
    parser = argparse.ArgumentParser(description='V2G Microgrid Optimization Pipeline')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--phases', default='all', help='Phases to run (comma-separated)')
    parser.add_argument('--algorithms', default='IALO,ALO,PSO,CSA', 
                       help='Optimization algorithms to compare')
    parser.add_argument('--log-level', default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logging.info("Starting V2G Microgrid Optimization Pipeline")
    
    try:
        # Phase 1: Load configuration and data
        logging.info("Phase 1: Loading configuration and data")
        config = load_configuration(args.config)
        
        data_loader = DataLoader(config)
        weather_data = data_loader.load_weather_data()
        load_profile = data_loader.load_load_profile()
        ev_data = data_loader.load_ev_data()
        
        # Combine all data
        data = {
            'weather': weather_data,
            'load': load_profile,
            'ev': ev_data
        }
        
        # Phase 2: Initialize components
        logging.info("Phase 2: Initializing components")
        components = initialize_components(config)
        
        # Phase 3: Run optimization with multiple algorithms
        logging.info("Phase 3: Running optimization")
        algorithms = args.algorithms.split(',')
        convergence_histories = {}
        best_solutions = {}
        
        for algorithm in algorithms:
            algorithm = algorithm.strip()
            best_solution, best_fitness, convergence_history = run_optimization(
                config, data, components, algorithm
            )
            
            convergence_histories[algorithm] = convergence_history
            best_solutions[algorithm] = {
                'solution': best_solution,
                'fitness': best_fitness
            }
            
            logging.info(f"{algorithm} - Best fitness: {best_fitness:.4f}")
            logging.info(f"{algorithm} - Best solution: {best_solution}")
        
        # Select best overall solution (IALO if available)
        best_algorithm = 'IALO' if 'IALO' in best_solutions else algorithms[0]
        best_solution = best_solutions[best_algorithm]['solution']
        
        # Phase 4: Monte Carlo analysis
        if 'monte_carlo' in args.phases or args.phases == 'all':
            logging.info("Phase 4: Running Monte Carlo analysis")
            ev_scenarios = run_monte_carlo_analysis(config, best_solution, data, components)
        else:
            ev_scenarios = {}
        
        # Phase 5: Sensitivity analysis
        if 'sensitivity' in args.phases or args.phases == 'all':
            logging.info("Phase 5: Running sensitivity analysis")
            sensitivity_results = run_sensitivity_analysis(config, data, components)
        
        # Phase 6: Results analysis
        logging.info("Phase 6: Analyzing results")
        results = analyze_results(best_solution, ev_scenarios, data, components, config)
        
        # Phase 7: Generate outputs
        logging.info("Phase 7: Generating outputs")
        generate_outputs(results, convergence_histories, config)
        
        # Print summary
        logging.info("\n" + "="*50)
        logging.info("PIPELINE COMPLETED SUCCESSFULLY")
        logging.info("="*50)
        logging.info(f"Best algorithm: {best_algorithm}")
        logging.info(f"Best solution: PV={int(best_solution[0])}, WT={int(best_solution[1])}, "
                    f"BT={int(best_solution[2])}, AD={best_solution[3]:.2f}")
        logging.info(f"COE: ${results['economic']['coe']:.4f}/kWh")
        logging.info(f"LPSP: {results['economic']['lpsp']:.4f}")
        logging.info(f"REF: {results['economic']['ref']:.4f}")
        logging.info("="*50)
        
    except Exception as e:
        logging.error(f"Pipeline failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()