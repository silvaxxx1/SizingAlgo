#!/usr/bin/env python3
"""
V2G Microgrid Optimization Pipeline - Parallel Processing with Algorithm-Specific Outputs
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
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import time
from functools import partial
import pickle
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

# -------------------- Logging & Config -------------------- #
def setup_logging(log_level='INFO', log_file=None):
    """Setup logging with optional file output"""
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(processName)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

def load_configuration(config_path='config.yaml'):
    base_dir = Path(__file__).parent
    config_file = Path(config_path)
    if not config_file.is_absolute():
        config_file = base_dir / config_file

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config

def create_algorithm_output_directory(base_output_dir, algorithm, timestamp=None):
    """Create algorithm-specific output directory structure"""
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    algorithm_dir = Path(base_output_dir) / algorithm.lower() / f"run_{timestamp}"
    
    # Create subdirectories
    (algorithm_dir / 'optimization_results').mkdir(parents=True, exist_ok=True)
    (algorithm_dir / 'figures').mkdir(parents=True, exist_ok=True)
    (algorithm_dir / 'reports').mkdir(parents=True, exist_ok=True)
    (algorithm_dir / 'raw_data').mkdir(parents=True, exist_ok=True)
    (algorithm_dir / 'logs').mkdir(parents=True, exist_ok=True)
    
    return algorithm_dir

def create_master_output_directory(base_output_dir, timestamp=None):
    """Create master output directory for comparison results"""
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    master_dir = Path(base_output_dir) / 'comparison' / f"run_{timestamp}"
    
    # Create subdirectories
    (master_dir / 'comparison_results').mkdir(parents=True, exist_ok=True)
    (master_dir / 'comparison_figures').mkdir(parents=True, exist_ok=True)
    (master_dir / 'comparison_reports').mkdir(parents=True, exist_ok=True)
    (master_dir / 'logs').mkdir(parents=True, exist_ok=True)
    
    return master_dir

# -------------------- Components -------------------- #
def initialize_components(config):
    """Initialize components - must be pickleable for multiprocessing"""
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
    
    return components

# -------------------- Objectives -------------------- #
def calculate_objectives(solution, data, components, config):
    """Calculate objectives with error handling and validation"""
    try:
        n_pv, n_wt, n_bt, autonomy_days = solution
        
        # Validate solution bounds
        n_pv = max(0, int(n_pv))
        n_wt = max(0, int(n_wt))
        n_bt = max(0, int(n_bt))
        autonomy_days = max(0.1, float(autonomy_days))
        
        # Update component counts (create copies to avoid shared state issues)
        components_copy = {
            'pv': PhotovoltaicSystem(components['pv'].rated_power, components['pv'].temp_coefficient, components['pv'].noct),
            'wt': WindTurbine(components['wt'].rated_power, components['wt'].cut_in_speed, components['wt'].cut_out_speed, components['wt'].rated_speed),
            'bt': BatterySystem(components['bt'].capacity, components['bt'].soc_min, components['bt'].soc_max, components['bt'].efficiency),
            'ev': ElectricVehicle(components['ev'].capacity, components['ev'].soc_min, components['ev'].soc_max),
            'grid': Grid(components['grid'].buy_price, components['grid'].sell_price)
        }
        
        components_copy['pv'].set_count(n_pv)
        components_copy['wt'].set_count(n_wt)
        components_copy['bt'].set_count(n_bt)
        components_copy['bt'].set_autonomy_days(autonomy_days)
        
        # Initialize EMS
        ems = RuleBasedEMS(components_copy)
        results = ems.simulate_year(data)
        
        # Economic analysis
        economic_analysis = EconomicAnalysis(config['economic'])
        coe = economic_analysis.calculate_coe(components_copy, results)
        lpsp = economic_analysis.calculate_lpsp(results)
        ref = economic_analysis.calculate_ref(results)
        
        return coe, lpsp, ref
        
    except Exception as e:
        # Return penalty values
        return 1e6, 1.0, 0.0

def create_objective_function(data, components, config):
    """Create a properly encapsulated objective function"""
    
    def objective_function(solution):
        """Objective function with proper error handling"""
        try:
            # Validate input
            if not isinstance(solution, (list, np.ndarray)) or len(solution) != 4:
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
                
            return float(fitness)
            
        except Exception as e:
            return 1e6
    
    return objective_function

def is_data_valid(data, data_name):
    """
    Safely check if data is valid (non-empty dict, list, or DataFrame)
    This function avoids the DataFrame ambiguity error
    """
    try:
        if data is None:
            return False
        
        if isinstance(data, dict):
            return len(data) > 0
        
        if isinstance(data, (list, tuple)):
            return len(data) > 0
        
        if isinstance(data, pd.DataFrame):
            return not data.empty
        
        if isinstance(data, np.ndarray):
            return data.size > 0
        
        try:
            return bool(data)
        except ValueError:
            return False
        
    except Exception as e:
        return False

# -------------------- Parallel Optimization Functions -------------------- #
def run_single_optimization(algorithm_data):
    """Run a single optimization algorithm - designed for parallel execution with algorithm-specific outputs"""
    algorithm, config, data, components, process_id, timestamp = algorithm_data
    
    # Create algorithm-specific output directory
    algorithm_dir = create_algorithm_output_directory('outputs', algorithm, timestamp)
    
    # Setup logging for this process
    log_file = algorithm_dir / 'logs' / f'{algorithm.lower()}_optimization.log'
    setup_logging(config.get('log_level', 'INFO'), log_file)
    
    logger = logging.getLogger(f'optimizer_{algorithm}')
    logger.info(f"Starting {algorithm} optimization in process {process_id}")
    logger.info(f"Algorithm output directory: {algorithm_dir}")
    
    start_time = time.time()
    
    try:
        # Save configuration copy to algorithm directory
        config_copy_path = algorithm_dir / f'{algorithm.lower()}_config_used.yaml'
        with open(config_copy_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        logger.info(f"Saved configuration copy to: {config_copy_path}")
        
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
        
        dim = 4
        bounds_tuple = (lower_bounds, upper_bounds)
        bounds_list = [(lb, ub) for lb, ub in zip(lower_bounds, upper_bounds)]

        # Create objective function
        objective_function = create_objective_function(data, components, config)
        
        # Test objective function
        test_solution = (lower_bounds + upper_bounds) / 2
        test_fitness = objective_function(test_solution)
        logger.info(f"{algorithm} objective function test: {test_fitness}")

        # Initialize optimizer
        opt_config = config['optimization']

        if algorithm == 'IALO':
            optimizer = IALO(
                obj_func=objective_function,
                dim=dim,
                bounds=bounds_tuple,
                population_size=opt_config['population_size'],
                max_iter=opt_config['max_iterations']
            )

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

        # Verify optimizer
        if not hasattr(optimizer, 'optimize') or not callable(getattr(optimizer, 'optimize')):
            raise AttributeError(f"{algorithm} optimizer does not have a callable 'optimize' method")

        # Run optimization
        logger.info(f"Running {algorithm} optimization...")
        best_solution, best_fitness, convergence_history = optimizer.optimize()
        
        elapsed_time = time.time() - start_time
        logger.info(f"{algorithm} completed in {elapsed_time:.2f}s - Best fitness: {best_fitness:.6f}")
        
        # Generate algorithm-specific outputs immediately
        generate_algorithm_outputs(
            algorithm, 
            best_solution, 
            best_fitness, 
            convergence_history, 
            data, 
            components, 
            config, 
            algorithm_dir,
            elapsed_time
        )
        
        return {
            'algorithm': algorithm,
            'best_solution': best_solution,
            'best_fitness': best_fitness,
            'convergence_history': convergence_history,
            'execution_time': elapsed_time,
            'success': True,
            'process_id': process_id,
            'output_directory': str(algorithm_dir)
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"{algorithm} failed after {elapsed_time:.2f}s: {str(e)}")
        
        # Return default values
        default_solution = (lower_bounds + upper_bounds) / 2 if 'lower_bounds' in locals() else [1, 1, 1, 1]
        default_fitness = 1e6
        default_history = [default_fitness] * opt_config.get('max_iterations', 100)
        
        return {
            'algorithm': algorithm,
            'best_solution': default_solution,
            'best_fitness': default_fitness,
            'convergence_history': default_history,
            'execution_time': elapsed_time,
            'success': False,
            'error': str(e),
            'process_id': process_id,
            'output_directory': str(algorithm_dir)
        }

def generate_algorithm_outputs(algorithm, best_solution, best_fitness, convergence_history, 
                             data, components, config, algorithm_dir, execution_time):
    """Generate algorithm-specific outputs"""
    try:
        logger = logging.getLogger(f'output_generator_{algorithm}')
        logger.info(f"Generating outputs for {algorithm}")
        
        # Component sizing results
        component_sizing = {
            'n_pv': int(best_solution[0]),
            'n_wt': int(best_solution[1]),
            'n_bt': int(best_solution[2]),
            'autonomy_days': float(best_solution[3])
        }
        
        # Save component sizing results
        if is_data_valid(component_sizing, "component_sizing"):
            df_components = pd.DataFrame([component_sizing])
            df_components.to_csv(
                algorithm_dir / 'optimization_results' / f'{algorithm.lower()}_best_solution.csv', 
                index=False
            )
            logger.info(f"Saved {algorithm} component sizing results")
        
        # Economic analysis
        try:
            # Update components with best solution
            components_copy = initialize_components(config)
            components_copy['pv'].set_count(int(best_solution[0]))
            components_copy['wt'].set_count(int(best_solution[1]))
            components_copy['bt'].set_count(int(best_solution[2]))
            components_copy['bt'].set_autonomy_days(float(best_solution[3]))
            
            # Run EMS simulation
            ems = RuleBasedEMS(components_copy)
            simulation_results = ems.simulate_year(data)
            
            # Calculate economic metrics
            economic_analysis = EconomicAnalysis(config['economic'])
            economic_data = {
                'coe': float(economic_analysis.calculate_coe(components_copy, simulation_results)),
                'lpsp': float(economic_analysis.calculate_lpsp(simulation_results)),
                'ref': float(economic_analysis.calculate_ref(simulation_results)),
                'npc': float(economic_analysis.calculate_npc(components_copy)),
                'best_fitness': float(best_fitness),
                'execution_time': float(execution_time)
            }
            
            # Save economic analysis
            if is_data_valid(economic_data, "economic_data"):
                df_economic = pd.DataFrame([economic_data])
                df_economic.to_csv(
                    algorithm_dir / 'optimization_results' / f'{algorithm.lower()}_economic_analysis.csv', 
                    index=False
                )
                logger.info(f"Saved {algorithm} economic analysis results")
            
        except Exception as e:
            logger.error(f"Economic analysis failed for {algorithm}: {e}")
            economic_data = {}
            simulation_results = {}
        
        # Save raw convergence data
        if is_data_valid(convergence_history, f"{algorithm}_convergence_history"):
            df_convergence = pd.DataFrame({
                'iteration': range(1, len(convergence_history) + 1),
                'fitness': convergence_history
            })
            df_convergence.to_csv(
                algorithm_dir / 'raw_data' / f'{algorithm.lower()}_convergence.csv', 
                index=False
            )
            logger.info(f"Saved {algorithm} convergence data")
        
        # Save energy flows data
        if 'simulation_results' in locals() and is_data_valid(simulation_results, "energy_flows"):
            try:
                if isinstance(simulation_results, dict) and 'hourly_data' in simulation_results:
                    df_energy = pd.DataFrame(simulation_results['hourly_data'])
                    df_energy.to_csv(
                        algorithm_dir / 'raw_data' / f'{algorithm.lower()}_energy_flows.csv', 
                        index=False
                    )
                    logger.info(f"Saved {algorithm} energy flows data")
            except Exception as e:
                logger.error(f"Failed to save energy flows data for {algorithm}: {e}")
        
        # Generate visualizations
        try:
            visualizer = Visualizer()
            figures_dir = algorithm_dir / 'figures'
            
            # Convergence plot
            if is_data_valid(convergence_history, f"{algorithm}_convergence_history"):
                visualizer.plot_convergence(
                    convergence_history, 
                    title=f'{algorithm} Convergence Analysis',
                    save_path=figures_dir / f'{algorithm.lower()}_convergence.png'
                )
                logger.info(f"Generated {algorithm} convergence plot")
            
            # Energy flows plot
            if 'simulation_results' in locals() and is_data_valid(simulation_results, "energy_flows"):
                visualizer.plot_energy_flows(
                    simulation_results, 
                    save_path=figures_dir / f'{algorithm.lower()}_energy_flows.png'
                )
                logger.info(f"Generated {algorithm} energy flows plot")
            
            # Component sizing plot
            if is_data_valid(component_sizing, "component_sizing_plot"):
                visualizer.plot_component_sizing(
                    component_sizing, 
                    save_path=figures_dir / f'{algorithm.lower()}_component_sizing.png'
                )
                logger.info(f"Generated {algorithm} component sizing plot")
            
            # Economic analysis plot
            if 'economic_data' in locals() and is_data_valid(economic_data, "economic_data_plot"):
                visualizer.plot_economic_analysis(
                    economic_data, 
                    save_path=figures_dir / f'{algorithm.lower()}_economic_analysis.png'
                )
                logger.info(f"Generated {algorithm} economic analysis plot")
        
        except Exception as e:
            logger.error(f"Visualization generation failed for {algorithm}: {e}")
        
        # Create algorithm summary report
        create_algorithm_summary_report(
            algorithm, 
            best_solution, 
            best_fitness, 
            execution_time,
            component_sizing,
            economic_data if 'economic_data' in locals() else {},
            algorithm_dir
        )
        
        logger.info(f"Output generation completed for {algorithm}")
        
    except Exception as e:
        logger = logging.getLogger(f'output_generator_{algorithm}')
        logger.error(f"Output generation failed for {algorithm}: {e}")

def create_algorithm_summary_report(algorithm, best_solution, best_fitness, execution_time,
                                  component_sizing, economic_data, algorithm_dir):
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
            f.write(f"Best Fitness: {best_fitness:.6f}\n")
            f.write(f"Execution Time: {execution_time:.2f} seconds\n\n")
            
            if component_sizing:
                f.write(f"COMPONENT SIZING:\n")
                f.write(f"{'='*30}\n")
                f.write(f"PV Panels: {component_sizing.get('n_pv', 'N/A')}\n")
                f.write(f"Wind Turbines: {component_sizing.get('n_wt', 'N/A')}\n")
                f.write(f"Battery Units: {component_sizing.get('n_bt', 'N/A')}\n")
                f.write(f"Autonomy Days: {component_sizing.get('autonomy_days', 'N/A'):.2f}\n\n")
            
            # Economic Analysis
            if economic_data:
                f.write(f"ECONOMIC ANALYSIS:\n")
                f.write(f"{'='*30}\n")
                f.write(f"Cost of Energy (COE): ${economic_data.get('coe', 'N/A'):.4f}/kWh\n")
                f.write(f"Loss of Power Supply Probability (LPSP): {economic_data.get('lpsp', 'N/A'):.4f}\n")
                f.write(f"Renewable Energy Fraction (REF): {economic_data.get('ref', 'N/A'):.4f}\n")
                f.write(f"Net Present Cost (NPC): ${economic_data.get('npc', 'N/A'):.2f}\n\n")
            
            # File Locations
            f.write(f"OUTPUT FILES:\n")
            f.write(f"{'='*30}\n")
            f.write(f"Best Solution: optimization_results/{algorithm.lower()}_best_solution.csv\n")
            f.write(f"Economic Analysis: optimization_results/{algorithm.lower()}_economic_analysis.csv\n")
            f.write(f"Convergence Plot: figures/{algorithm.lower()}_convergence.png\n")
            f.write(f"Energy Flows Plot: figures/{algorithm.lower()}_energy_flows.png\n")
            f.write(f"Component Sizing Plot: figures/{algorithm.lower()}_component_sizing.png\n")
            f.write(f"Raw Convergence Data: raw_data/{algorithm.lower()}_convergence.csv\n")
            f.write(f"Raw Energy Flow Data: raw_data/{algorithm.lower()}_energy_flows.csv\n")
            f.write(f"Configuration Used: {algorithm.lower()}_config_used.yaml\n")
        
        logger = logging.getLogger(f'summary_{algorithm}')
        logger.info(f"Created summary report: {report_path}")
        
    except Exception as e:
        logger = logging.getLogger(f'summary_{algorithm}')
        logger.error(f"Failed to create summary report for {algorithm}: {e}")

def run_parallel_optimization(config, data, components, algorithms, max_workers=None):
    """Run multiple optimization algorithms in parallel with algorithm-specific outputs"""
    
    if max_workers is None:
        max_workers = min(len(algorithms), mp.cpu_count())
    
    logger = logging.getLogger('parallel_optimizer')
    logger.info(f"Starting parallel optimization with {len(algorithms)} algorithms using {max_workers} workers")
    logger.info(f"Available CPU cores: {mp.cpu_count()}")
    
    # Create shared timestamp for this run
    shared_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Prepare algorithm data for parallel execution
    algorithm_data = [
        (algorithm, config, data, components, i, shared_timestamp) 
        for i, algorithm in enumerate(algorithms)
    ]
    
    results = {}
    start_time = time.time()
    
    # Use ProcessPoolExecutor for CPU-intensive tasks
    try:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all optimization tasks
            future_to_algorithm = {
                executor.submit(run_single_optimization, data): data[0] 
                for data in algorithm_data
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_algorithm):
                algorithm = future_to_algorithm[future]
                try:
                    result = future.result()
                    results[result['algorithm']] = result
                    
                    if result['success']:
                        logger.info(f"✓ {result['algorithm']} completed: "
                                  f"fitness={result['best_fitness']:.6f}, "
                                  f"time={result['execution_time']:.2f}s, "
                                  f"output={result['output_directory']}")
                    else:
                        logger.warning(f"✗ {result['algorithm']} failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logger.error(f"✗ {algorithm} process failed: {str(e)}")
                    results[algorithm] = {
                        'algorithm': algorithm,
                        'success': False,
                        'error': str(e),
                        'execution_time': 0
                    }
    
    except Exception as e:
        logger.error(f"Parallel execution failed: {str(e)}")
        # Fallback to sequential execution
        logger.info("Falling back to sequential execution...")
        return run_sequential_optimization(config, data, components, algorithms)
    
    total_time = time.time() - start_time
    successful_runs = sum(1 for r in results.values() if r.get('success', False))
    
    logger.info(f"Parallel optimization completed in {total_time:.2f}s")
    logger.info(f"Successful runs: {successful_runs}/{len(algorithms)}")
    
    return results, shared_timestamp

def run_sequential_optimization(config, data, components, algorithms):
    """Fallback sequential optimization with algorithm-specific outputs"""
    logger = logging.getLogger('sequential_optimizer')
    logger.info("Running sequential optimization...")
    
    # Create shared timestamp for this run
    shared_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    results = {}
    for i, algorithm in enumerate(algorithms):
        algorithm_data = (algorithm, config, data, components, i, shared_timestamp)
        result = run_single_optimization(algorithm_data)
        results[algorithm] = result
    
    return results, shared_timestamp

# -------------------- Analysis Functions -------------------- #
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

def generate_comparison_outputs(optimization_results, master_dir, shared_timestamp):
    """Generate comparison outputs across all algorithms"""
    logger = logging.getLogger('comparison_generator')
    logger.info(f"Generating comparison outputs in {master_dir}")
    
    try:
        # Algorithm comparison summary
        optimization_summary = []
        convergence_histories = {}
        
        for algo, result in optimization_results.items():
            if result.get('success', False):
                optimization_summary.append({
                    'algorithm': algo,
                    'best_fitness': result['best_fitness'],
                    'execution_time': result['execution_time'],
                    'n_pv': int(result['best_solution'][0]),
                    'n_wt': int(result['best_solution'][1]),
                    'n_bt': int(result['best_solution'][2]),
                    'autonomy_days': result['best_solution'][3],
                    'success': True,
                    'output_directory': result.get('output_directory', 'N/A')
                })
                convergence_histories[algo] = result['convergence_history']
            else:
                optimization_summary.append({
                    'algorithm': algo,
                    'best_fitness': float('inf'),
                    'execution_time': result.get('execution_time', 0),
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'output_directory': result.get('output_directory', 'N/A')
                })
        
        # Save algorithm comparison summary
        if optimization_summary:
            df_comparison = pd.DataFrame(optimization_summary)
            df_comparison.to_csv(
                master_dir / 'comparison_results' / 'algorithm_comparison.csv', 
                index=False
            )
            logger.info("Saved algorithm comparison results")
        
        # Generate comparison visualizations
        try:
            visualizer = Visualizer()
            figures_dir = master_dir / 'comparison_figures'
            
            # Algorithm comparison plot
            if convergence_histories:
                visualizer.plot_algorithm_comparison(
                    convergence_histories,
                    save_path=figures_dir / 'algorithm_convergence_comparison.png'
                )
                logger.info("Generated algorithm comparison plot")
            
            # Performance comparison bar chart
            if optimization_summary:
                successful_results = [r for r in optimization_summary if r.get('success', False)]
                if successful_results:
                    algorithms = [r['algorithm'] for r in successful_results]
                    fitness_values = [r['best_fitness'] for r in successful_results]
                    execution_times = [r['execution_time'] for r in successful_results]
                    
                    # Create performance comparison plots
                    import matplotlib.pyplot as plt
                    
                    # Fitness comparison
                    plt.figure(figsize=(10, 6))
                    plt.bar(algorithms, fitness_values)
                    plt.xlabel('Algorithm')
                    plt.ylabel('Best Fitness')
                    plt.title('Algorithm Performance Comparison - Best Fitness')
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    plt.savefig(figures_dir / 'fitness_comparison.png', dpi=300, bbox_inches='tight')
                    plt.close()
                    
                    # Execution time comparison
                    plt.figure(figsize=(10, 6))
                    plt.bar(algorithms, execution_times)
                    plt.xlabel('Algorithm')
                    plt.ylabel('Execution Time (seconds)')
                    plt.title('Algorithm Performance Comparison - Execution Time')
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    plt.savefig(figures_dir / 'time_comparison.png', dpi=300, bbox_inches='tight')
                    plt.close()
                    
                    logger.info("Generated performance comparison plots")
        
        except Exception as e:
            logger.error(f"Comparison visualization generation failed: {e}")
        
        # Create master comparison report
        create_master_comparison_report(optimization_results, master_dir, shared_timestamp)
        
        logger.info("Comparison output generation completed")
        
    except Exception as e:
        logger.error(f"Comparison output generation failed: {e}")

def create_master_comparison_report(optimization_results, master_dir, timestamp):
    """Create master comparison report across all algorithms"""
    try:
        report_path = master_dir / 'comparison_reports' / 'master_comparison_report.txt'
        
        with open(report_path, 'w') as f:
            f.write(f"V2G MICROGRID OPTIMIZATION - MASTER COMPARISON REPORT\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Run ID: {timestamp}\n")
            f.write(f"{'='*60}\n\n")
            
            # Algorithm Performance Summary
            f.write(f"ALGORITHM PERFORMANCE SUMMARY:\n")
            f.write(f"{'='*40}\n")
            
            successful_results = {k: v for k, v in optimization_results.items() 
                                if v.get('success', False)}
            failed_results = {k: v for k, v in optimization_results.items() 
                            if not v.get('success', False)}
            
            f.write(f"Total Algorithms: {len(optimization_results)}\n")
            f.write(f"Successful Runs: {len(successful_results)}\n")
            f.write(f"Failed Runs: {len(failed_results)}\n\n")
            
            if successful_results:
                # Best performing algorithm
                best_algorithm = min(successful_results.keys(), 
                                   key=lambda k: successful_results[k]['best_fitness'])
                best_result = successful_results[best_algorithm]
                
                f.write(f"BEST PERFORMING ALGORITHM: {best_algorithm}\n")
                f.write(f"{'='*40}\n")
                f.write(f"Best Fitness: {best_result['best_fitness']:.6f}\n")
                f.write(f"Execution Time: {best_result['execution_time']:.2f} seconds\n")
                f.write(f"PV Panels: {int(best_result['best_solution'][0])}\n")
                f.write(f"Wind Turbines: {int(best_result['best_solution'][1])}\n")
                f.write(f"Battery Units: {int(best_result['best_solution'][2])}\n")
                f.write(f"Autonomy Days: {best_result['best_solution'][3]:.2f}\n")
                f.write(f"Output Directory: {best_result.get('output_directory', 'N/A')}\n\n")
                
                # Detailed comparison table
                f.write(f"DETAILED COMPARISON TABLE:\n")
                f.write(f"{'='*40}\n")
                f.write(f"{'Algorithm':<10} {'Fitness':<12} {'Time(s)':<10} {'PV':<5} {'WT':<5} {'BT':<5} {'AD':<6}\n")
                f.write(f"{'-'*60}\n")
                
                for algo, result in successful_results.items():
                    f.write(f"{algo:<10} "
                           f"{result['best_fitness']:<12.6f} "
                           f"{result['execution_time']:<10.2f} "
                           f"{int(result['best_solution'][0]):<5} "
                           f"{int(result['best_solution'][1]):<5} "
                           f"{int(result['best_solution'][2]):<5} "
                           f"{result['best_solution'][3]:<6.2f}\n")
                f.write(f"\n")
            
            # Failed algorithms
            if failed_results:
                f.write(f"FAILED ALGORITHMS:\n")
                f.write(f"{'='*40}\n")
                for algo, result in failed_results.items():
                    f.write(f"{algo}: {result.get('error', 'Unknown error')}\n")
                f.write(f"\n")
            
            # Output directories
            f.write(f"OUTPUT DIRECTORIES:\n")
            f.write(f"{'='*40}\n")
            f.write(f"Master Comparison: {master_dir}\n")
            for algo, result in optimization_results.items():
                output_dir = result.get('output_directory', 'N/A')
                status = "✓" if result.get('success', False) else "✗"
                f.write(f"{algo} {status}: {output_dir}\n")
            f.write(f"\n")
            
            # Comparison files
            f.write(f"COMPARISON FILES:\n")
            f.write(f"{'='*40}\n")
            f.write(f"Algorithm Comparison: comparison_results/algorithm_comparison.csv\n")
            f.write(f"Convergence Comparison: comparison_figures/algorithm_convergence_comparison.png\n")
            f.write(f"Fitness Comparison: comparison_figures/fitness_comparison.png\n")
            f.write(f"Time Comparison: comparison_figures/time_comparison.png\n")
        
        logger = logging.getLogger('master_report')
        logger.info(f"Created master comparison report: {report_path}")
        
    except Exception as e:
        logger = logging.getLogger('master_report')
        logger.error(f"Failed to create master comparison report: {e}")

# -------------------- Main Function -------------------- #
def main():
    parser = argparse.ArgumentParser(description='V2G Microgrid Optimization Pipeline - Parallel Processing with Algorithm-Specific Outputs')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--phases', default='all', help='Phases to run (comma-separated)')
    parser.add_argument('--algorithms', default='IALO,ALO,PSO,CSA', help='Optimization algorithms to compare')
    parser.add_argument('--log-level', default='INFO', help='Logging level')
    parser.add_argument('--parallel', action='store_true', default=True, help='Run algorithms in parallel')
    parser.add_argument('--max-workers', type=int, default=None, help='Maximum number of parallel workers')
    parser.add_argument('--sequential', action='store_true', help='Force sequential execution')
    parser.add_argument('--output-base', default='outputs', help='Base output directory')
    
    args = parser.parse_args()
    
    # Override parallel setting if sequential is explicitly requested
    if args.sequential:
        args.parallel = False
    
    setup_logging(args.log_level)
    logger = logging.getLogger('main')
    logger.info("Starting V2G Microgrid Optimization Pipeline - Parallel Processing with Algorithm-Specific Outputs")
    
    try:
        # Load configuration and data
        config = load_configuration(args.config)
        config['log_level'] = args.log_level  # Add log level to config
        
        data_loader = DataLoader(config)
        data = {
            'weather': data_loader.load_weather_data(),
            'load': data_loader.load_load_profile(),
            'ev': data_loader.load_ev_data()
        }
        
        components = initialize_components(config)
        
        # Optimization phase
        algorithms = [alg.strip() for alg in args.algorithms.split(',')]
        logger.info(f"Running optimization with algorithms: {algorithms}")
        logger.info(f"Parallel execution: {args.parallel}")
        logger.info(f"Base output directory: {args.output_base}")
        
        start_time = time.time()
        
        if args.parallel and len(algorithms) > 1:
            optimization_results, shared_timestamp = run_parallel_optimization(
                config, data, components, algorithms, args.max_workers
            )
        else:
            optimization_results, shared_timestamp = run_sequential_optimization(
                config, data, components, algorithms
            )
        
        optimization_time = time.time() - start_time
        
        # Filter successful results
        successful_results = {k: v for k, v in optimization_results.items() 
                            if v.get('success', False)}
        
        if not successful_results:
            raise RuntimeError("All optimization algorithms failed")
        
        # Create master comparison directory and generate comparison outputs
        master_dir = create_master_output_directory(args.output_base, shared_timestamp)
        generate_comparison_outputs(optimization_results, master_dir, shared_timestamp)
        
        # Select best algorithm result for additional analysis
        best_algorithm = min(successful_results.keys(), 
                           key=lambda k: successful_results[k]['best_fitness'])
        best_solution = successful_results[best_algorithm]['best_solution']
        
        logger.info(f"Optimization completed in {optimization_time:.2f}s")
        logger.info(f"Selected best algorithm: {best_algorithm}")
        logger.info(f"Best fitness: {successful_results[best_algorithm]['best_fitness']:.6f}")
        logger.info(f"Master comparison directory: {master_dir}")
        
        # Monte Carlo analysis (optional, using best solution)
        ev_scenarios = {}
        if 'monte_carlo' in args.phases or args.phases == 'all':
            logger.info("Running Monte Carlo analysis with best solution")
            ev_scenarios = run_monte_carlo_analysis(config, best_solution, data, components)
            
            # Save Monte Carlo results to master directory
            if ev_scenarios:
                mc_summary = []
                for scenario, data in ev_scenarios.items():
                    if isinstance(data, dict):
                        mc_summary.append({
                            'scenario': scenario,
                            'mean_fitness': data.get('mean_fitness', 0),
                            'std_fitness': data.get('std_fitness', 0),
                            'simulations': data.get('num_simulations', 0)
                        })
                
                if mc_summary:
                    pd.DataFrame(mc_summary).to_csv(
                        master_dir / 'comparison_results' / 'monte_carlo_summary.csv', 
                        index=False
                    )
                    logger.info("Saved Monte Carlo analysis summary")
        
        # Final summary
        logger.info("\n" + "="*70)
        logger.info("PARALLEL PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("="*70)
        logger.info(f"Total execution time: {time.time() - start_time:.2f}s")
        logger.info(f"Optimization time: {optimization_time:.2f}s")
        logger.info(f"Best algorithm: {best_algorithm}")
        logger.info(f"Best solution: PV={int(best_solution[0])}, WT={int(best_solution[1])}, "
                     f"BT={int(best_solution[2])}, AD={best_solution[3]:.2f}")
        
        # Algorithm performance summary
        logger.info(f"\nAlgorithm Performance Summary:")
        logger.info(f"{'Algorithm':<8} {'Status':<8} {'Fitness':<12} {'Time(s)':<8} {'Output Directory'}")
        logger.info(f"{'-'*80}")
        
        for algo, result in optimization_results.items():
            if result.get('success', False):
                status = "SUCCESS"
                fitness = f"{result['best_fitness']:8.4f}"
                exec_time = f"{result['execution_time']:6.2f}"
                output_dir = Path(result['output_directory']).name
                logger.info(f"{algo:<8} {status:<8} {fitness:<12} {exec_time:<8} {output_dir}")
            else:
                status = "FAILED"
                error = result.get('error', 'Unknown')[:30] + "..." if len(result.get('error', '')) > 30 else result.get('error', 'Unknown')
                logger.info(f"{algo:<8} {status:<8} {'N/A':<12} {'N/A':<8} {error}")
        
        logger.info(f"\nOutput Directories:")
        logger.info(f"Master Comparison: {master_dir}")
        for algo, result in optimization_results.items():
            if result.get('success', False):
                logger.info(f"{algo}: {result['output_directory']}")
        
        logger.info("="*70)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()