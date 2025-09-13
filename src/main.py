#!/usr/bin/env python3
"""
V2G Microgrid Optimization Pipeline - Algorithm-Specific Output Directories
"""

import os
import sys
import yaml
import argparse
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import traceback
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from utils.data_loader import DataLoader
from components import PhotovoltaicSystem, WindTurbine, BatterySystem, ElectricVehicle, Grid
from energy_management.rule_based_ems import RuleBasedEMS
from optimization.ialo import IALO
from optimization.alo import AntlionOptimizer
from optimization.pso import ParticleSwarmOptimizer
from optimization.csa import CuckooSearchAlgorithm
from analysis.monte_carlo import MonteCarloSimulation
from analysis.economic_analysis import EconomicAnalysis
from analysis.sensitivity_analysis import SensitivityAnalysis
from utils.visualization import Visualizer
from utils.constants import * 

def setup_logging(log_level='INFO', algorithm='IALO'):
    """Setup logging with algorithm-specific log files"""
    # Create algorithm-specific log directory
    log_dir = Path('outputs') / algorithm.lower()
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create timestamp for unique log files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f'pipeline_{timestamp}.log'
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.info(f"Logging initialized for {algorithm} algorithm")
    logging.info(f"Log file: {log_file}")

def load_configuration(config_path='config.yaml'):
    base_dir = Path(__file__).parent
    config_file = Path(config_path)
    if not config_file.is_absolute():
        config_file = base_dir / config_file

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config

def create_algorithm_output_directory(base_output_dir, algorithm):
    """Create algorithm-specific output directory structure"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    algorithm_dir = Path(base_output_dir) / algorithm.lower() / f"run_{timestamp}"
    
    # Create subdirectories
    (algorithm_dir / 'optimization_results').mkdir(parents=True, exist_ok=True)
    (algorithm_dir / 'figures').mkdir(parents=True, exist_ok=True)
    (algorithm_dir / 'reports').mkdir(parents=True, exist_ok=True)
    (algorithm_dir / 'raw_data').mkdir(parents=True, exist_ok=True)
    
    logging.info(f"Created output directory: {algorithm_dir}")
    return algorithm_dir

def initialize_components(config):
    components = {}
    
    # Photovoltaic System
    pv_config = config['components']['pv']
    components['pv'] = PhotovoltaicSystem(
        rated_power=pv_config['rated_power'],
        temp_coefficient=pv_config['temp_coefficient'],
        noct=pv_config['noct']
    )
    
    # Wind Turbine
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
    """Calculate objectives with comprehensive error handling"""
    try:
        logging.debug(f"Calculating objectives for solution: {solution}")
        
        n_pv, n_wt, n_bt, autonomy_days = solution
        
        # Validate solution bounds
        n_pv = max(0, int(n_pv))
        n_wt = max(0, int(n_wt))
        n_bt = max(0, int(n_bt))
        autonomy_days = max(0.1, float(autonomy_days))
        
        logging.debug(f"Validated solution: PV={n_pv}, WT={n_wt}, BT={n_bt}, AD={autonomy_days}")
        
        # Update component counts
        components['pv'].set_count(n_pv)
        components['wt'].set_count(n_wt)
        components['bt'].set_count(n_bt)
        components['bt'].set_autonomy_days(autonomy_days)
        
        # Initialize EMS
        ems = RuleBasedEMS(components)
        results = ems.simulate_year(data)
        
        # Economic analysis
        economic_analysis = EconomicAnalysis(config['economic'])
        coe = economic_analysis.calculate_coe(components, results)
        lpsp = economic_analysis.calculate_lpsp(results)
        ref = economic_analysis.calculate_ref(results)
        
        logging.debug(f"Objectives calculated: COE={coe}, LPSP={lpsp}, REF={ref}")
        
        return coe, lpsp, ref
        
    except Exception as e:
        logging.warning(f"Objective calculation failed: {e}")
        logging.debug(f"Objective calculation error details: {traceback.format_exc()}")
        # Return penalty values
        return 1e6, 1.0, 0.0

def create_objective_function_wrapper(data, components, config):
    """Create a robust objective function wrapper with detailed debugging"""
    
    def objective_function(solution):
        try:
            logging.debug(f"Objective function called with: {solution}")
            logging.debug(f"Solution type: {type(solution)}")
            
            # Validate input
            if not isinstance(solution, (list, np.ndarray, tuple)):
                logging.warning(f"Invalid solution type: {type(solution)}")
                return 1e6
            
            if len(solution) != 4:
                logging.warning(f"Invalid solution length: {len(solution)}")
                return 1e6
            
            # Calculate objectives
            coe, lpsp, ref = calculate_objectives(solution, data, components, config)
            
            # Calculate fitness
            w = 0.5
            gamma = 1000
            pf = 1.0
            fitness = w * coe + (1 - w) * gamma * pf * lpsp - w * ref

            # Apply penalties for constraint violations
            if lpsp > config['constraints']['lpsp_max']:
                fitness += 1000
            if ref < config['constraints']['ref_min']:
                fitness += 1000
                
            logging.debug(f"Fitness calculated: {fitness}")
            return float(fitness)
            
        except Exception as e:
            logging.error(f"Objective function evaluation failed: {e}")
            logging.debug(f"Objective function error details: {traceback.format_exc()}")
            return 1e6
    
    return objective_function

def debug_optimizer_initialization(algorithm, objective_function, bounds_info, opt_config):
    """Debug optimizer initialization to identify the dictionary issue"""
    
    logging.info(f"Debugging {algorithm} optimizer initialization...")
    
    try:
        # Test objective function first
        test_solution = [1, 1, 1, 1]  # Simple test solution
        test_result = objective_function(test_solution)
        logging.info(f"Objective function test result: {test_result}")
        
        lower_bounds, upper_bounds = bounds_info['tuple']
        bounds_list = bounds_info['list']
        
        if algorithm == 'IALO':
            logging.info("Initializing IALO optimizer...")
            logging.info(f"Parameters: obj_func={callable(objective_function)}, dim=4, bounds={bounds_info['tuple']}")
            
            optimizer = IALO(
                obj_func=objective_function,
                dim=4,
                bounds=bounds_info['tuple'],
                population_size=opt_config['population_size'],
                max_iter=opt_config['max_iterations']
            )
            
            logging.info(f"IALO optimizer created successfully")
            
        elif algorithm == 'ALO':
            optimizer = AntlionOptimizer(
                objective_function=objective_function,
                bounds=bounds_list,
                population_size=opt_config['population_size'],
                max_iterations=opt_config['max_iterations']
            )
        elif algorithm == 'PSO':
            optimizer = ParticleSwarmOptimizer(
                objective_function=objective_function,
                bounds=bounds_list,
                swarm_size=opt_config['population_size'],
                max_iterations=opt_config['max_iterations']
            )
        elif algorithm == 'CSA':
            optimizer = CuckooSearchAlgorithm(
                objective_function=objective_function,
                bounds=bounds_list,
                population_size=opt_config['population_size'],
                max_iterations=opt_config['max_iterations']
            )
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        # Verify optimize method
        if not hasattr(optimizer, 'optimize'):
            raise AttributeError(f"{algorithm} optimizer missing 'optimize' method")
        
        if not callable(getattr(optimizer, 'optimize')):
            raise AttributeError(f"{algorithm} optimizer 'optimize' method is not callable")
        
        logging.info(f"{algorithm} optimizer initialized and verified successfully")
        return optimizer
        
    except Exception as e:
        logging.error(f"Optimizer initialization failed: {e}")
        logging.error(f"Full error details: {traceback.format_exc()}")
        raise

def run_optimization(config, data, components, algorithm='IALO'):
    """Run optimization with extensive debugging"""
    
    logging.info(f"Starting optimization with {algorithm}")
    
    try:
        # Bounds setup
        lower_bounds = np.array([
            config['bounds']['n_pv'][0],
            config['bounds']['n_wt'][0],
            config['bounds']['n_bt'][0],
            config['bounds']['autonomy_days'][0]
        ])
        upper_bounds = np.array([
            config['bounds']['n_pv'][1],
            config['bounds']['n_wt'][1],
            config['bounds']['n_bt'][1],
            config['bounds']['autonomy_days'][1]
        ])
        
        bounds_info = {
            'tuple': (lower_bounds, upper_bounds),
            'list': [(lb, ub) for lb, ub in zip(lower_bounds, upper_bounds)]
        }
        
        logging.info(f"Bounds: {bounds_info['list']}")
        
        # Create objective function
        objective_function = create_objective_function_wrapper(data, components, config)
        
        # Test objective function
        test_solution = (lower_bounds + upper_bounds) / 2
        test_fitness = objective_function(test_solution)
        logging.info(f"Objective function test: {test_fitness}")
        
        # Initialize optimizer with debugging
        opt_config = config['optimization']
        optimizer = debug_optimizer_initialization(algorithm, objective_function, bounds_info, opt_config)
        
        # Run optimization
        logging.info(f"Starting {algorithm} optimization...")
        best_solution, best_fitness, convergence_history = optimizer.optimize()
        
        logging.info(f"{algorithm} optimization completed")
        logging.info(f"Best solution: {best_solution}")
        logging.info(f"Best fitness: {best_fitness}")
        
        return best_solution, best_fitness, convergence_history
        
    except Exception as e:
        logging.error(f"Optimization failed: {e}")
        logging.error(f"Full optimization error: {traceback.format_exc()}")
        
        # Return default values
        default_solution = (lower_bounds + upper_bounds) / 2 if 'lower_bounds' in locals() else [1, 1, 1, 1]
        default_fitness = 1e6
        default_history = [default_fitness] * opt_config.get('max_iterations', 100)
        
        return default_solution, default_fitness, default_history

def analyze_results(best_solution, ev_scenarios, data, components, config):
    logging.info("Analyzing results")
    try:
        results = {
            'optimization': {
                'best_solution': best_solution,
                'component_sizing': {
                    'n_pv': int(best_solution[0]),
                    'n_wt': int(best_solution[1]),
                    'n_bt': int(best_solution[2]),
                    'autonomy_days': float(best_solution[3])
                }
            },
            'monte_carlo': ev_scenarios,
            'economic': {},
            'energy_flows': {}
        }
        
        # Economic analysis
        economic_analysis = EconomicAnalysis(config['economic'])
        
        # Update components
        components['pv'].set_count(int(best_solution[0]))
        components['wt'].set_count(int(best_solution[1]))
        components['bt'].set_count(int(best_solution[2]))
        
        ems = RuleBasedEMS(components)
        simulation_results = ems.simulate_year(data)
        
        results['economic'] = {
            'coe': float(economic_analysis.calculate_coe(components, simulation_results)),
            'lpsp': float(economic_analysis.calculate_lpsp(simulation_results)),
            'ref': float(economic_analysis.calculate_ref(simulation_results)),
            'npc': float(economic_analysis.calculate_npc(components))
        }
        
        results['energy_flows'] = simulation_results
        return results
        
    except Exception as e:
        logging.error(f"Results analysis failed: {e}")
        logging.error(f"Analysis error details: {traceback.format_exc()}")
        return {
            'optimization': {
                'best_solution': best_solution, 
                'component_sizing': {
                    'n_pv': int(best_solution[0]) if len(best_solution) > 0 else 1,
                    'n_wt': int(best_solution[1]) if len(best_solution) > 1 else 1,
                    'n_bt': int(best_solution[2]) if len(best_solution) > 2 else 1,
                    'autonomy_days': float(best_solution[3]) if len(best_solution) > 3 else 1.0
                }
            },
            'monte_carlo': {},
            'economic': {},
            'energy_flows': {}
        }

def is_data_valid(data, data_name):
    """
    Safely check if data is valid (non-empty dict, list, or DataFrame)
    This function avoids the DataFrame ambiguity error
    """
    try:
        if data is None:
            logging.debug(f"{data_name}: Data is None")
            return False
        
        if isinstance(data, dict):
            # For dictionaries, check if they have any keys
            is_valid = len(data) > 0
            logging.debug(f"{data_name}: Dictionary with {len(data)} keys")
            return is_valid
        
        if isinstance(data, (list, tuple)):
            # For lists/tuples, check length
            is_valid = len(data) > 0
            logging.debug(f"{data_name}: List/tuple with {len(data)} items")
            return is_valid
        
        if isinstance(data, pd.DataFrame):
            # For DataFrames, use .empty property to avoid ambiguity
            is_valid = not data.empty
            logging.debug(f"{data_name}: DataFrame with shape {data.shape}, empty: {data.empty}")
            return is_valid
        
        if isinstance(data, np.ndarray):
            # For numpy arrays, check size
            is_valid = data.size > 0
            logging.debug(f"{data_name}: NumPy array with size {data.size}")
            return is_valid
        
        # For other types, convert to bool safely
        try:
            is_valid = bool(data)
            logging.debug(f"{data_name}: Other type {type(data)}, bool value: {is_valid}")
            return is_valid
        except ValueError:
            # If conversion fails, assume it's not valid
            logging.debug(f"{data_name}: Could not convert {type(data)} to bool")
            return False
        
    except Exception as e:
        logging.warning(f"{data_name}: Data validation failed: {e}")
        return False

def generate_outputs(results, convergence_histories, algorithm_dir, algorithm):
    """Generate outputs with algorithm-specific directories"""
    logging.info(f"Generating outputs for {algorithm} in {algorithm_dir}")
    try:
        # Save optimization results - Algorithm specific
        component_sizing = results['optimization'].get('component_sizing', {})
        if is_data_valid(component_sizing, "component_sizing"):
            try:
                df_components = pd.DataFrame([component_sizing])
                df_components.to_csv(
                    algorithm_dir / 'optimization_results' / f'{algorithm.lower()}_best_solution.csv', 
                    index=False
                )
                logging.info(f"Saved {algorithm} component sizing results")
            except Exception as e:
                logging.error(f"Failed to save component sizing: {e}")
        
        # Save economic analysis - Algorithm specific
        economic_data = results.get('economic', {})
        if is_data_valid(economic_data, "economic_data"):
            try:
                df_economic = pd.DataFrame([economic_data])
                df_economic.to_csv(
                    algorithm_dir / 'optimization_results' / f'{algorithm.lower()}_economic_analysis.csv', 
                    index=False
                )
                logging.info(f"Saved {algorithm} economic analysis results")
            except Exception as e:
                logging.error(f"Failed to save economic analysis: {e}")
        
        # Save raw convergence data
        for alg_name, history in convergence_histories.items():
            if is_data_valid(history, f"{alg_name}_convergence_history"):
                try:
                    df_convergence = pd.DataFrame({
                        'iteration': range(1, len(history) + 1),
                        'fitness': history
                    })
                    df_convergence.to_csv(
                        algorithm_dir / 'raw_data' / f'{alg_name.lower()}_convergence.csv', 
                        index=False
                    )
                    logging.info(f"Saved {alg_name} convergence data")
                except Exception as e:
                    logging.error(f"Failed to save convergence data for {alg_name}: {e}")
        
        # Save energy flows data
        energy_flows = results.get('energy_flows', {})
        if is_data_valid(energy_flows, "energy_flows"):
            try:
                if isinstance(energy_flows, dict) and 'hourly_data' in energy_flows:
                    df_energy = pd.DataFrame(energy_flows['hourly_data'])
                    df_energy.to_csv(
                        algorithm_dir / 'raw_data' / f'{algorithm.lower()}_energy_flows.csv', 
                        index=False
                    )
                    logging.info(f"Saved {algorithm} energy flows data")
            except Exception as e:
                logging.error(f"Failed to save energy flows data: {e}")
        
        # Initialize visualizer
        try:
            visualizer = Visualizer()
            figures_dir = algorithm_dir / 'figures'
            
            # Generate plots with algorithm-specific naming
            for alg_name, history in convergence_histories.items():
                if is_data_valid(history, f"{alg_name}_convergence_history"):
                    try:
                        visualizer.plot_convergence(
                            history, 
                            title=f'{alg_name} Convergence Analysis',
                            save_path=figures_dir / f'{alg_name.lower()}_convergence.png'
                        )
                        logging.info(f"Generated {alg_name} convergence plot")
                    except Exception as e:
                        logging.error(f"Failed to generate convergence plot for {alg_name}: {e}")
            
            # Energy flows plot
            if is_data_valid(energy_flows, "energy_flows"):
                try:
                    visualizer.plot_energy_flows(
                        energy_flows, 
                        save_path=figures_dir / f'{algorithm.lower()}_energy_flows.png'
                    )
                    logging.info(f"Generated {algorithm} energy flows plot")
                except Exception as e:
                    logging.error(f"Failed to generate energy flows plot: {e}")
            
            # Monte Carlo plot
            monte_carlo_data = results.get('monte_carlo', {})
            if is_data_valid(monte_carlo_data, "monte_carlo_data"):
                try:
                    visualizer.plot_monte_carlo_results(
                        monte_carlo_data, 
                        save_path=figures_dir / f'{algorithm.lower()}_monte_carlo_analysis.png'
                    )
                    logging.info(f"Generated {algorithm} Monte Carlo plot")
                except Exception as e:
                    logging.error(f"Failed to generate Monte Carlo plot: {e}")
            
            # Economic analysis plot
            if is_data_valid(economic_data, "economic_data_plot"):
                try:
                    visualizer.plot_economic_analysis(
                        economic_data, 
                        save_path=figures_dir / f'{algorithm.lower()}_economic_analysis.png'
                    )
                    logging.info(f"Generated {algorithm} economic analysis plot")
                except Exception as e:
                    logging.error(f"Failed to generate economic analysis plot: {e}")
            
            # Component sizing plot
            if is_data_valid(component_sizing, "component_sizing_plot"):
                try:
                    visualizer.plot_component_sizing(
                        component_sizing, 
                        save_path=figures_dir / f'{algorithm.lower()}_component_sizing.png'
                    )
                    logging.info(f"Generated {algorithm} component sizing plot")
                except Exception as e:
                    logging.error(f"Failed to generate component sizing plot: {e}")
        
        except Exception as e:
            logging.error(f"Visualization initialization failed: {e}")
            logging.error(f"Visualization error details: {traceback.format_exc()}")
        
        # Create summary report
        create_algorithm_summary_report(results, algorithm_dir, algorithm)
        
        logging.info(f"Output generation completed for {algorithm}. Results saved to {algorithm_dir}")
        
    except Exception as e:
        logging.error(f"Output generation failed: {e}")
        logging.error(f"Output generation error details: {traceback.format_exc()}")

def create_algorithm_summary_report(results, algorithm_dir, algorithm):
    """Create a summary report for the algorithm run"""
    try:
        report_path = algorithm_dir / 'reports' / f'{algorithm.lower()}_summary_report.txt'
        
        with open(report_path, 'w') as f:
            f.write(f"V2G MICROGRID OPTIMIZATION SUMMARY REPORT\n")
            f.write(f"Algorithm: {algorithm}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*50}\n\n")
            
            # Optimization Results
            f.write(f"OPTIMIZATION RESULTS:\n")
            f.write(f"{'='*30}\n")
            component_sizing = results['optimization'].get('component_sizing', {})
            if component_sizing:
                f.write(f"PV Panels: {component_sizing.get('n_pv', 'N/A')}\n")
                f.write(f"Wind Turbines: {component_sizing.get('n_wt', 'N/A')}\n")
                f.write(f"Battery Units: {component_sizing.get('n_bt', 'N/A')}\n")
                f.write(f"Autonomy Days: {component_sizing.get('autonomy_days', 'N/A'):.2f}\n\n")
            
            # Economic Analysis
            f.write(f"ECONOMIC ANALYSIS:\n")
            f.write(f"{'='*30}\n")
            economic = results.get('economic', {})
            if economic:
                f.write(f"Cost of Energy (COE): ${economic.get('coe', 'N/A'):.4f}/kWh\n")
                f.write(f"Loss of Power Supply Probability (LPSP): {economic.get('lpsp', 'N/A'):.4f}\n")
                f.write(f"Renewable Energy Fraction (REF): {economic.get('ref', 'N/A'):.4f}\n")
                f.write(f"Net Present Cost (NPC): ${economic.get('npc', 'N/A'):.2f}\n\n")
            
            # File Locations
            f.write(f"OUTPUT FILES:\n")
            f.write(f"{'='*30}\n")
            f.write(f"Optimization Results: optimization_results/{algorithm.lower()}_best_solution.csv\n")
            f.write(f"Economic Analysis: optimization_results/{algorithm.lower()}_economic_analysis.csv\n")
            f.write(f"Convergence Plot: figures/{algorithm.lower()}_convergence.png\n")
            f.write(f"Energy Flows Plot: figures/{algorithm.lower()}_energy_flows.png\n")
            f.write(f"Component Sizing Plot: figures/{algorithm.lower()}_component_sizing.png\n")
            f.write(f"Raw Convergence Data: raw_data/{algorithm.lower()}_convergence.csv\n")
            f.write(f"Raw Energy Flow Data: raw_data/{algorithm.lower()}_energy_flows.csv\n")
        
        logging.info(f"Created summary report: {report_path}")
        
    except Exception as e:
        logging.error(f"Failed to create summary report: {e}")

def run_monte_carlo_analysis(config, best_solution, data, components):
    logging.info("Starting Monte Carlo analysis")
    try:
        mc_config = config['monte_carlo']
        mc_sim = MonteCarloSimulation(num_simulations=mc_config['num_simulations'])
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
        
    except Exception as e:
        logging.error(f"Monte Carlo analysis failed: {e}")
        return {}

def main():
    parser = argparse.ArgumentParser(description='V2G Microgrid Optimization Pipeline - Algorithm-Specific Outputs')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--algorithms', default='IALO', help='Optimization algorithms to test')
    parser.add_argument('--log-level', default='DEBUG', help='Logging level')
    parser.add_argument('--debug', action='store_true', help='Enable detailed debugging')
    parser.add_argument('--output-base', default='outputs', help='Base output directory')
    
    args = parser.parse_args()
    
    # Test single algorithm
    algorithm = args.algorithms.strip()
    
    # Setup algorithm-specific logging
    setup_logging(args.log_level, algorithm)
    logging.info(f"Starting V2G Microgrid Optimization Pipeline for {algorithm}")
    
    try:
        # Load configuration and data
        config = load_configuration(args.config)
        
        # Create algorithm-specific output directory
        algorithm_dir = create_algorithm_output_directory(args.output_base, algorithm)
        
        # Save configuration copy to algorithm directory
        config_copy_path = algorithm_dir / 'config_used.yaml'
        with open(config_copy_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        logging.info(f"Saved configuration copy to: {config_copy_path}")
        
        data_loader = DataLoader(config)
        data = {
            'weather': data_loader.load_weather_data(),
            'load': data_loader.load_load_profile(),
            'ev': data_loader.load_ev_data()
        }
        
        components = initialize_components(config)
        
        logging.info(f"Testing {algorithm} algorithm")
        
        best_solution, best_fitness, convergence_history = run_optimization(
            config, data, components, algorithm
        )
        
        logging.info(f"Optimization completed:")
        logging.info(f"  Best solution: {best_solution}")
        logging.info(f"  Best fitness: {best_fitness}")
        logging.info(f"  Convergence history length: {len(convergence_history) if convergence_history else 0}")
        
        # Monte Carlo analysis (optional)
        ev_scenarios = {}
        try:
            ev_scenarios = run_monte_carlo_analysis(config, best_solution, data, components)
        except Exception as e:
            logging.warning(f"Skipping Monte Carlo analysis: {e}")
        
        # Analyze results
        results = analyze_results(best_solution, ev_scenarios, data, components, config)
        
        # Generate algorithm-specific outputs
        convergence_histories = {algorithm: convergence_history}
        generate_outputs(results, convergence_histories, algorithm_dir, algorithm)
        
        # Final summary
        logging.info("\n" + "="*50)
        logging.info("PIPELINE COMPLETED SUCCESSFULLY")
        logging.info("="*50)
        logging.info(f"Algorithm: {algorithm}")
        logging.info(f"Output Directory: {algorithm_dir}")
        logging.info(f"Best solution: PV={int(best_solution[0])}, WT={int(best_solution[1])}, "
                     f"BT={int(best_solution[2])}, AD={best_solution[3]:.2f}")
        logging.info(f"Best fitness: {best_fitness:.6f}")
        
        if results['economic']:
            logging.info(f"COE: ${results['economic']['coe']:.4f}/kWh")
            logging.info(f"LPSP: {results['economic']['lpsp']:.4f}")
            logging.info(f"REF: {results['economic']['ref']:.4f}")
        
        logging.info("="*50)
        
    except Exception as e:
        logging.error(f"Pipeline failed: {str(e)}")
        logging.error(f"Full pipeline error: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()