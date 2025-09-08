# analysis/sensitivity_analysis.py
"""
Sensitivity Analysis for V2G Microgrid Optimization Parameters
Implements parameter sensitivity testing and tornado diagrams
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Callable, Optional, Tuple
import logging
from copy import deepcopy
import itertools
from concurrent.futures import ProcessPoolExecutor
import warnings

warnings.filterwarnings('ignore', category=RuntimeWarning)

class SensitivityAnalysis:
    """
    Comprehensive sensitivity analysis for microgrid optimization parameters
    Supports one-at-a-time (OAT) and global sensitivity analysis methods
    """
    
    def __init__(self, 
                 num_samples: int = 100,
                 confidence_level: float = 0.95,
                 parallel: bool = True,
                 max_workers: Optional[int] = None):
        """
        Initialize sensitivity analysis
        
        Args:
            num_samples: Number of samples for global sensitivity analysis
            confidence_level: Confidence level for uncertainty bounds
            parallel: Whether to use parallel processing
            max_workers: Maximum number of worker processes
        """
        self.num_samples = num_samples
        self.confidence_level = confidence_level
        self.parallel = parallel
        self.max_workers = max_workers
        self.results = []
        
        logging.info(f"Sensitivity analysis initialized with {num_samples} samples")
    
    def analyze_parameters(self, 
                          parameters: Dict[str, List[float]], 
                          base_case: Dict,
                          evaluate_system: Callable,
                          output_metrics: List[str] = None) -> pd.DataFrame:
        """
        Perform one-at-a-time sensitivity analysis on specified parameters
        
        Args:
            parameters: Dict of parameter names and their variation values (multipliers)
            base_case: Base case system configuration
            evaluate_system: Function that evaluates the system and returns metrics
            output_metrics: List of output metrics to analyze
            
        Returns:
            DataFrame with sensitivity analysis results
        """
        if output_metrics is None:
            output_metrics = ['coe', 'lpsp', 'ref', 'npc']
        
        results = []
        total_runs = sum(len(values) for values in parameters.values())
        run_count = 0
        
        logging.info(f"Starting parameter sensitivity analysis with {total_runs} total runs")
        
        # Evaluate base case first
        base_results = self._safe_evaluate_system(base_case, evaluate_system)
        base_run = {
            'parameter': 'base_case',
            'multiplier': 1.0,
            'parameter_value': 'baseline'
        }
        base_run.update(base_results)
        results.append(base_run)
        
        # Analyze each parameter
        for param_name, multipliers in parameters.items():
            logging.info(f"Analyzing sensitivity for parameter: {param_name}")
            
            for multiplier in multipliers:
                run_count += 1
                
                # Create modified case
                modified_case = self._modify_parameter(base_case, param_name, multiplier)
                
                # Evaluate system with modified parameters
                evaluation_results = self._safe_evaluate_system(modified_case, evaluate_system)
                
                # Store results
                result = {
                    'parameter': param_name,
                    'multiplier': multiplier,
                    'parameter_value': f"{multiplier:.2f}x baseline",
                    'run_id': run_count
                }
                result.update(evaluation_results)
                results.append(result)
                
                # Log progress
                if run_count % 10 == 0:
                    logging.info(f"Sensitivity analysis progress: {run_count}/{total_runs} runs completed")
        
        results_df = pd.DataFrame(results)
        self.results = results_df
        
        logging.info("Parameter sensitivity analysis completed")
        return results_df
    
    def _modify_parameter(self, base_case: Dict, param_name: str, multiplier: float) -> Dict:
        """
        Modify a specific parameter in the base case configuration
        
        Args:
            base_case: Base case configuration
            param_name: Parameter name to modify
            multiplier: Multiplication factor
            
        Returns:
            Modified configuration dictionary
        """
        modified_case = deepcopy(base_case)
        
        # Handle different parameter types
        if param_name == 'solar_irradiance':
            if 'weather' in modified_case and 'solar_irradiance' in modified_case['weather'].columns:
                modified_case['weather']['solar_irradiance'] *= multiplier
            
        elif param_name == 'wind_speed':
            if 'weather' in modified_case and 'wind_speed' in modified_case['weather'].columns:
                modified_case['weather']['wind_speed'] *= multiplier
                
        elif param_name == 'load_demand':
            if 'load' in modified_case and 'load_demand' in modified_case['load'].columns:
                modified_case['load']['load_demand'] *= multiplier
                
        elif param_name == 'battery_cost':
            if 'economic' in modified_case and 'component_costs' in modified_case['economic']:
                modified_case['economic']['component_costs']['battery'] *= multiplier
                
        elif param_name == 'pv_cost':
            if 'economic' in modified_case and 'component_costs' in modified_case['economic']:
                modified_case['economic']['component_costs']['pv_panel'] *= multiplier
                
        elif param_name == 'wind_cost':
            if 'economic' in modified_case and 'component_costs' in modified_case['economic']:
                modified_case['economic']['component_costs']['wind_turbine'] *= multiplier
                
        elif param_name == 'grid_buy_price':
            if 'economic' in modified_case:
                modified_case['economic']['grid_buy_price'] *= multiplier
                
        elif param_name == 'grid_sell_price':
            if 'economic' in modified_case:
                modified_case['economic']['grid_sell_price'] *= multiplier
                
        elif param_name == 'interest_rate':
            if 'economic' in modified_case:
                modified_case['economic']['interest_rate'] *= multiplier
                
        elif param_name == 'project_lifetime':
            if 'economic' in modified_case:
                modified_case['economic']['project_lifetime'] = int(
                    modified_case['economic']['project_lifetime'] * multiplier
                )
        
        # Handle component efficiency parameters
        elif param_name == 'pv_efficiency':
            if 'components' in modified_case and 'photovoltaic' in modified_case['components']:
                # This would affect the PV system efficiency
                modified_case['components']['photovoltaic']['system_efficiency'] = min(
                    1.0, modified_case['components']['photovoltaic'].get('system_efficiency', 0.95) * multiplier
                )
                
        elif param_name == 'battery_efficiency':
            if 'components' in modified_case and 'battery' in modified_case['components']:
                modified_case['components']['battery']['round_trip_efficiency'] = min(
                    1.0, modified_case['components']['battery']['round_trip_efficiency'] * multiplier
                )
        
        return modified_case
    
    def _safe_evaluate_system(self, 
                             case_config: Dict, 
                             evaluate_system: Callable,
                             max_retries: int = 3) -> Dict:
        """
        Safely evaluate system with error handling and retries
        
        Args:
            case_config: System configuration to evaluate
            evaluate_system: Evaluation function
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary with evaluation results
        """
        for attempt in range(max_retries):
            try:
                results = evaluate_system(case_config)
                
                # Ensure results contain expected metrics
                expected_metrics = ['coe', 'lpsp', 'ref', 'npc']
                for metric in expected_metrics:
                    if metric not in results:
                        results[metric] = np.nan
                
                # Validate results
                for key, value in results.items():
                    if isinstance(value, (int, float)):
                        if np.isnan(value) or np.isinf(value):
                            results[key] = np.nan
                        elif value < 0 and key in ['coe', 'npc']:
                            results[key] = np.nan
                        elif key in ['lpsp', 'ref'] and not (0 <= value <= 1):
                            results[key] = np.nan
                
                return results
                
            except Exception as e:
                logging.warning(f"Evaluation attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    # Return NaN values if all attempts fail
                    return {
                        'coe': np.nan,
                        'lpsp': np.nan,
                        'ref': np.nan,
                        'npc': np.nan,
                        'error': str(e)
                    }
        
        return {'coe': np.nan, 'lpsp': np.nan, 'ref': np.nan, 'npc': np.nan}
    
    def calculate_sensitivity_indices(self, 
                                    results_df: Optional[pd.DataFrame] = None,
                                    base_case_values: Optional[Dict[str, float]] = None) -> Dict:
        """
        Calculate sensitivity indices (elasticity) for each parameter
        
        Args:
            results_df: Results DataFrame (uses self.results if None)
            base_case_values: Base case values for normalization
            
        Returns:
            Dictionary with sensitivity indices for each parameter and metric
        """
        if results_df is None:
            results_df = self.results
        
        if results_df.empty:
            logging.warning("No sensitivity analysis results available")
            return {}
        
        # Get base case values
        if base_case_values is None:
            base_case = results_df[results_df['parameter'] == 'base_case']
            if base_case.empty:
                base_case = results_df[results_df['multiplier'] == 1.0].iloc[0:1]
            
            if not base_case.empty:
                base_case_values = {
                    'coe': base_case['coe'].iloc[0],
                    'lpsp': base_case['lpsp'].iloc[0],
                    'ref': base_case['ref'].iloc[0],
                    'npc': base_case['npc'].iloc[0]
                }
            else:
                # Use median values as baseline
                base_case_values = {
                    'coe': results_df['coe'].median(),
                    'lpsp': results_df['lpsp'].median(),
                    'ref': results_df['ref'].median(),
                    'npc': results_df['npc'].median()
                }
        
        indices = {}
        
        for param in results_df['parameter'].unique():
            if param == 'base_case':
                continue
                
            param_data = results_df[results_df['parameter'] == param].copy()
            param_data = param_data.sort_values('multiplier')
            
            if len(param_data) < 2:
                continue
            
            indices[param] = {}
            
            for objective in ['coe', 'lpsp', 'ref', 'npc']:
                base_val = base_case_values.get(objective, 1.0)
                
                if base_val == 0 or np.isnan(base_val):
                    indices[param][objective] = 0.0
                    continue
                
                # Calculate percentage changes
                param_changes = (param_data['multiplier'] - 1.0) * 100
                obj_changes = ((param_data[objective] - base_val) / base_val) * 100
                
                # Remove NaN values
                valid_mask = ~(np.isnan(param_changes) | np.isnan(obj_changes))
                param_changes = param_changes[valid_mask]
                obj_changes = obj_changes[valid_mask]
                
                if len(param_changes) > 1:
                    try:
                        # Calculate sensitivity index (elasticity) using linear fit
                        sensitivity_index = np.polyfit(param_changes, obj_changes, 1)[0]
                        indices[param][objective] = sensitivity_index
                    except (np.linalg.LinAlgError, ValueError):
                        indices[param][objective] = 0.0
                else:
                    indices[param][objective] = 0.0
        
        return indices
    
    def prepare_tornado_data(self, 
                           results_df: Optional[pd.DataFrame] = None,
                           objective: str = 'coe',
                           base_case_values: Optional[Dict[str, float]] = None) -> pd.DataFrame:
        """
        Prepare data for tornado diagram visualization
        
        Args:
            results_df: Results DataFrame
            objective: Objective function to analyze
            base_case_values: Base case values
            
        Returns:
            DataFrame with tornado diagram data
        """
        if results_df is None:
            results_df = self.results
        
        # Get base case value
        if base_case_values is None:
            base_case = results_df[results_df['parameter'] == 'base_case']
            if not base_case.empty:
                base_value = base_case[objective].iloc[0]
            else:
                base_value = results_df[objective].median()
        else:
            base_value = base_case_values.get(objective, results_df[objective].median())
        
        tornado_data = []
        
        for param in results_df['parameter'].unique():
            if param == 'base_case':
                continue
                
            param_data = results_df[results_df['parameter'] == param]
            
            if len(param_data) > 1 and objective in param_data.columns:
                obj_values = param_data[objective].dropna()
                
                if len(obj_values) > 0:
                    min_val = obj_values.min()
                    max_val = obj_values.max()
                    range_val = max_val - min_val
                    
                    # Calculate impact relative to base case
                    low_impact = base_value - min_val
                    high_impact = max_val - base_value
                    
                    tornado_data.append({
                        'parameter': param.replace('_', ' ').title(),
                        'parameter_key': param,
                        'base_value': base_value,
                        'min_value': min_val,
                        'max_value': max_val,
                        'range': range_val,
                        'low_impact': low_impact,
                        'high_impact': high_impact,
                        'total_impact': abs(low_impact) + abs(high_impact),
                        'relative_range': range_val / base_value if base_value != 0 else 0
                    })
        
        # Sort by total impact (most sensitive parameters first)
        tornado_df = pd.DataFrame(tornado_data)
        if not tornado_df.empty:
            tornado_df = tornado_df.sort_values('total_impact', ascending=False)
        
        return tornado_df
    
    def monte_carlo_sensitivity(self, 
                               parameters: Dict[str, Tuple[float, float]],
                               base_case: Dict,
                               evaluate_system: Callable,
                               n_samples: Optional[int] = None) -> pd.DataFrame:
        """
        Perform Monte Carlo sensitivity analysis with random parameter sampling
        
        Args:
            parameters: Dict of parameter names with (min, max) ranges
            base_case: Base case system configuration
            evaluate_system: System evaluation function
            n_samples: Number of Monte Carlo samples (uses self.num_samples if None)
            
        Returns:
            DataFrame with Monte Carlo sensitivity results
        """
        if n_samples is None:
            n_samples = self.num_samples
        
        logging.info(f"Starting Monte Carlo sensitivity analysis with {n_samples} samples")
        
        results = []
        
        for sample in range(n_samples):
            # Generate random parameter values
            modified_case = deepcopy(base_case)
            sample_params = {}
            
            for param_name, (min_val, max_val) in parameters.items():
                # Use uniform distribution for parameter sampling
                param_value = np.random.uniform(min_val, max_val)
                sample_params[param_name] = param_value
                
                # Apply parameter modification
                modified_case = self._modify_parameter(modified_case, param_name, param_value)
            
            # Evaluate system
            evaluation_results = self._safe_evaluate_system(modified_case, evaluate_system)
            
            # Store results
            result = {'sample_id': sample}
            result.update(sample_params)
            result.update(evaluation_results)
            results.append(result)
            
            # Log progress
            if sample % (n_samples // 10) == 0:
                logging.info(f"Monte Carlo progress: {sample}/{n_samples} samples completed")
        
        mc_results = pd.DataFrame(results)
        
        logging.info("Monte Carlo sensitivity analysis completed")
        return mc_results
    
    def calculate_sobol_indices(self, 
                               mc_results: pd.DataFrame,
                               parameters: List[str],
                               objective: str = 'coe') -> Dict:
        """
        Calculate Sobol sensitivity indices from Monte Carlo results
        
        Args:
            mc_results: Monte Carlo results DataFrame
            parameters: List of parameter names
            objective: Objective function to analyze
            
        Returns:
            Dictionary with first-order and total-order Sobol indices
        """
        try:
            # This is a simplified Sobol index calculation
            # For more accurate results, consider using SALib library
            
            sobol_indices = {}
            
            # Total variance of the objective
            total_variance = mc_results[objective].var()
            
            if total_variance == 0:
                logging.warning("Zero variance in objective function")
                return {}
            
            # Calculate first-order indices (main effects)
            for param in parameters:
                if param in mc_results.columns:
                    # Group by parameter quantiles and calculate variance
                    param_quantiles = pd.qcut(mc_results[param], q=10, duplicates='drop')
                    grouped_means = mc_results.groupby(param_quantiles)[objective].mean()
                    
                    # Variance of conditional means
                    conditional_variance = grouped_means.var()
                    
                    # First-order Sobol index
                    first_order = conditional_variance / total_variance
                    sobol_indices[param] = {
                        'first_order': first_order,
                        'main_effect': first_order
                    }
            
            return sobol_indices
            
        except Exception as e:
            logging.error(f"Error calculating Sobol indices: {str(e)}")
            return {}
    
    def correlation_analysis(self, 
                           results_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Perform correlation analysis between parameters and objectives
        
        Args:
            results_df: Results DataFrame
            
        Returns:
            Correlation matrix as DataFrame
        """
        if results_df is None:
            results_df = self.results
        
        if results_df.empty:
            logging.warning("No results available for correlation analysis")
            return pd.DataFrame()
        
        # Select numeric columns only
        numeric_cols = results_df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            logging.warning("Insufficient numeric columns for correlation analysis")
            return pd.DataFrame()
        
        # Calculate correlation matrix
        correlation_matrix = results_df[numeric_cols].corr()
        
        # Focus on correlations with objective functions
        objectives = ['coe', 'lpsp', 'ref', 'npc']
        available_objectives = [obj for obj in objectives if obj in correlation_matrix.columns]
        
        if available_objectives:
            # Extract correlations with objectives
            objective_correlations = correlation_matrix[available_objectives]
            return objective_correlations
        
        return correlation_matrix
    
    def generate_sensitivity_report(self, 
                                  results_df: Optional[pd.DataFrame] = None,
                                  save_path: Optional[str] = None) -> Dict:
        """
        Generate comprehensive sensitivity analysis report
        
        Args:
            results_df: Results DataFrame
            save_path: Path to save report CSV
            
        Returns:
            Dictionary with comprehensive sensitivity analysis
        """
        if results_df is None:
            results_df = self.results
        
        if results_df.empty:
            logging.warning("No results available for sensitivity report")
            return {}
        
        logging.info("Generating sensitivity analysis report")
        
        # Calculate sensitivity indices
        sensitivity_indices = self.calculate_sensitivity_indices(results_df)
        
        # Prepare tornado data for each objective
        tornado_data = {}
        objectives = ['coe', 'lpsp', 'ref', 'npc']
        
        for obj in objectives:
            if obj in results_df.columns:
                tornado_data[obj] = self.prepare_tornado_data(results_df, obj)
        
        # Correlation analysis
        correlations = self.correlation_analysis(results_df)
        
        # Parameter ranking by sensitivity
        parameter_ranking = {}
        for obj in objectives:
            if obj in sensitivity_indices:
                param_impacts = []
                for param, indices in sensitivity_indices.items():
                    if obj in indices:
                        param_impacts.append({
                            'parameter': param,
                            'sensitivity_index': abs(indices[obj]),
                            'impact': indices[obj]
                        })
                
                param_impacts.sort(key=lambda x: x['sensitivity_index'], reverse=True)
                parameter_ranking[obj] = param_impacts
        
        # Summary statistics
        summary_stats = {}
        for obj in objectives:
            if obj in results_df.columns:
                obj_data = results_df[obj].dropna()
                if len(obj_data) > 0:
                    summary_stats[obj] = {
                        'mean': obj_data.mean(),
                        'std': obj_data.std(),
                        'min': obj_data.min(),
                        'max': obj_data.max(),
                        'cv': obj_data.std() / obj_data.mean() if obj_data.mean() != 0 else 0,
                        'range': obj_data.max() - obj_data.min()
                    }
        
        # Compile comprehensive report
        report = {
            'sensitivity_indices': sensitivity_indices,
            'tornado_data': tornado_data,
            'correlations': correlations.to_dict() if not correlations.empty else {},
            'parameter_ranking': parameter_ranking,
            'summary_statistics': summary_stats,
            'analysis_info': {
                'total_runs': len(results_df),
                'parameters_analyzed': len(results_df['parameter'].unique()) - 1,  # Exclude base case
                'objectives_analyzed': len([obj for obj in objectives if obj in results_df.columns]),
                'completion_rate': (len(results_df.dropna()) / len(results_df)) * 100
            }
        }
        
        # Save detailed results if path provided
        if save_path:
            try:
                results_df.to_csv(save_path, index=False)
                logging.info(f"Detailed sensitivity results saved to {save_path}")
            except Exception as e:
                logging.error(f"Error saving sensitivity results: {str(e)}")
        
        logging.info("Sensitivity analysis report generated successfully")
        return report
    
    def plot_sensitivity_results(self, 
                                results_df: Optional[pd.DataFrame] = None,
                                objective: str = 'coe',
                                save_path: Optional[str] = None):
        """
        Create sensitivity analysis plots
        
        Note: This method requires the visualization module to be available
        """
        try:
            from ..utils.visualization import Visualizer
            
            if results_df is None:
                results_df = self.results
            
            viz = Visualizer()
            viz.plot_sensitivity_analysis(results_df, save_path=save_path, show_plot=True)
            
        except ImportError:
            logging.warning("Visualization module not available. Skipping plot generation.")
        except Exception as e:
            logging.error(f"Error creating sensitivity plots: {str(e)}")


# Helper functions for common sensitivity analysis patterns
def create_parameter_ranges(base_values: Dict[str, float], 
                          variation_percent: float = 20) -> Dict[str, List[float]]:
    """
    Create parameter variation ranges around base values
    
    Args:
        base_values: Dictionary of base parameter values
        variation_percent: Percentage variation around base values
        
    Returns:
        Dictionary with parameter ranges for sensitivity analysis
    """
    ranges = {}
    variation_factor = variation_percent / 100
    
    for param, base_val in base_values.items():
        # Create 5 points around base value
        multipliers = np.linspace(1 - variation_factor, 1 + variation_factor, 5)
        ranges[param] = multipliers.tolist()
    
    return ranges

def quick_sensitivity_test(evaluate_system: Callable,
                          base_case: Dict,
                          key_parameters: List[str] = None) -> pd.DataFrame:
    """
    Quick sensitivity test for key parameters
    
    Args:
        evaluate_system: System evaluation function
        base_case: Base case configuration
        key_parameters: List of key parameters to test
        
    Returns:
        DataFrame with quick sensitivity results
    """
    if key_parameters is None:
        key_parameters = ['solar_irradiance', 'wind_speed', 'load_demand', 
                         'battery_cost', 'grid_buy_price']
    
    # Create ±20% variation for each parameter
    parameter_ranges = {}
    for param in key_parameters:
        parameter_ranges[param] = [0.8, 0.9, 1.0, 1.1, 1.2]
    
    # Run sensitivity analysis
    sensitivity = SensitivityAnalysis()
    results = sensitivity.analyze_parameters(
        parameters=parameter_ranges,
        base_case=base_case,
        evaluate_system=evaluate_system
    )
    
    return results


# Example usage
if __name__ == "__main__":
    print("Sensitivity Analysis Module")
    print("Features:")
    print("  - One-at-a-time (OAT) sensitivity analysis")
    print("  - Monte Carlo sensitivity analysis") 
    print("  - Sobol sensitivity indices")
    print("  - Tornado diagram data preparation")
    print("  - Correlation analysis")
    print("  - Comprehensive sensitivity reporting")
    print("  - Parameter ranking by impact")
    print("  - Integration with visualization module")
    
    # Example of creating a sensitivity analysis instance
    # sa = SensitivityAnalysis(num_samples=100)
    # print(f"Sensitivity Analysis initialized with {sa.num_samples} samples")

    import logging

    logging.basicConfig(level=logging.INFO)

    # Example system evaluation function
    def mock_evaluate_system(case_config: Dict) -> Dict[str, float]:
        """
        Mock evaluation function for testing sensitivity analysis
        Returns simple relationships with some randomness
        """
        coe = 100 / (case_config.get('components', {}).get('photovoltaic', {}).get('system_efficiency', 0.95) + 0.1)
        lpsp = np.clip(0.05 * (1 - case_config.get('components', {}).get('battery', {}).get('round_trip_efficiency', 0.9)), 0, 1)
        ref = np.clip(0.1 * np.random.rand(), 0, 1)
        npc = 1000 * (case_config.get('economic', {}).get('battery_cost', 500) / 500)
        return {'coe': coe, 'lpsp': lpsp, 'ref': ref, 'npc': npc}

    # Example base case configuration
    base_case_example = {
        'weather': pd.DataFrame({
            'solar_irradiance': [800, 850, 900],
            'wind_speed': [5, 6, 7]
        }),
        'load': pd.DataFrame({
            'load_demand': [50, 55, 60]
        }),
        'economic': {
            'battery_cost': 500,
            'pv_cost': 400,
            'wind_cost': 600,
            'grid_buy_price': 0.15,
            'grid_sell_price': 0.1,
            'interest_rate': 0.05,
            'project_lifetime': 20,
            'component_costs': {'battery': 500, 'pv_panel': 400, 'wind_turbine': 600}
        },
        'components': {
            'photovoltaic': {'system_efficiency': 0.95},
            'battery': {'round_trip_efficiency': 0.9}
        }
    }

    # Define key parameters to test
    key_params = ['solar_irradiance', 'wind_speed', 'load_demand', 'battery_cost', 'pv_efficiency']

    # Run quick sensitivity test
    logging.info("Running quick sensitivity test...")
    results_df = quick_sensitivity_test(mock_evaluate_system, base_case_example, key_params)
    print("\n=== Sensitivity Analysis Results ===")
    print(results_df)

    # Optional: calculate sensitivity indices
    sa = SensitivityAnalysis()
    sa.results = results_df
    indices = sa.calculate_sensitivity_indices()
    print("\n=== Sensitivity Indices ===")
    print(indices)


