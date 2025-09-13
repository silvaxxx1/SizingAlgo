import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Union
import logging


class MonteCarloSimulation:
    """
    Monte Carlo simulation for EV behavior analysis
    Based on MATLAB Stochastic Multi-Criteria Model (SMCM)
    """
    
    def __init__(self, num_simulations: int = 1000):
        """
        Initialize Monte Carlo simulation
        
        Args:
            num_simulations: Number of simulation runs
        """
        self.num_simulations = num_simulations
        self.results = []
        
        logging.info(f"Monte Carlo simulation initialized with {num_simulations} runs")
    
    def generate_ev_arrival_departure(self, 
                                    num_evs: int,
                                    arrival_mean: float = 18.0,
                                    arrival_std: float = 2.0,
                                    departure_mean: float = 7.0,
                                    departure_std: float = 2.0) -> Dict:
        """
        Generate EV arrival and departure times using normal distribution
        
        Returns:
            Dictionary with arrival/departure patterns
        """
        arrival_times = np.random.normal(arrival_mean, arrival_std, num_evs)
        departure_times = np.random.normal(departure_mean, departure_std, num_evs)
        
        # Ensure times are within valid range (0-24 hours)
        arrival_times = np.clip(arrival_times, 0, 23)
        departure_times = np.clip(departure_times, 0, 23)
        
        return {
            'arrival_times': arrival_times,
            'departure_times': departure_times
        }
    
    def generate_ev_soc_profile(self, num_evs: int) -> Dict:
        """
        Generate EV SOC profiles based on driving patterns
        
        Returns:
            Dictionary with SOC arrival patterns
        """
        # SOC upon arrival (typically between 20% and 95%)
        soc_arrival = np.random.uniform(0.2, 0.95, num_evs)
        
        # Daily energy consumption (varies by driving pattern)
        daily_consumption_kwh = np.random.normal(12, 4, num_evs)  # Mean 12 kWh, std 4 kWh
        daily_consumption_kwh = np.clip(daily_consumption_kwh, 5, 25)  # Reasonable limits
        
        return {
            'soc_arrival': soc_arrival,
            'daily_consumption_kwh': daily_consumption_kwh
        }
    
    def simulate_ev_behavior(self, 
                           num_evs: int,
                           data: Dict,
                           components: Dict,
                           solution: np.ndarray) -> Dict:
        """
        Run Monte Carlo simulation for EV behavior
        
        Args:
            num_evs: Number of EVs to simulate
            data: Weather and load data
            components: System components
            solution: Optimization solution [n_pv, n_wt, n_bt, autonomy_days]
            
        Returns:
            Dictionary with simulation results
        """
        simulation_results = []
        
        for sim in range(self.num_simulations):
            # Generate EV patterns for this simulation
            arrival_departure = self.generate_ev_arrival_departure(num_evs)
            soc_profile = self.generate_ev_soc_profile(num_evs)
            
            # Set up components with current solution
            components['pv'].set_count(int(solution[0]))
            components['wt'].set_count(int(solution[1]))
            components['bt'].set_count(int(solution[2]))
            components['ev'].num_vehicles = num_evs
            
            # Reset EV fleet with generated SOC profile
            components['ev'].reset_fleet_state(soc_profile['soc_arrival'])
            
            # Generate availability schedule based on arrival/departure times
            hours = len(data['weather'])
            availability = np.zeros((hours, num_evs))
            
            for vehicle in range(num_evs):
                arrival_hour = int(arrival_departure['arrival_times'][vehicle])
                departure_hour = int(arrival_departure['departure_times'][vehicle])
                
                # Create daily patterns (overnight parking most common)
                for day in range(hours // 24):
                    if departure_hour < arrival_hour:  # Overnight parking
                        # Available from arrival to midnight
                        start = day * 24 + arrival_hour
                        end = (day + 1) * 24
                        if start < hours and end <= hours:
                            availability[start:end, vehicle] = 1
                        
                        # Available from midnight to departure  
                        start = (day + 1) * 24
                        end = (day + 1) * 24 + departure_hour
                        if start < hours and end <= hours:
                            availability[start:end, vehicle] = 1
            
            components['ev'].availability_schedule = availability
            
            # Run simulation with current EV configuration
            from energy_management.rule_based_ems import RuleBasedEMS
            
            ems = RuleBasedEMS(components)
            
            # Simulate shorter period for Monte Carlo (e.g., one week)
            sim_hours = min(168, hours)  # One week or available data
            weather_subset = data['weather'].iloc[:sim_hours]
            load_subset = data['load'].iloc[:sim_hours]
            
            sim_data = {"weather": weather_subset, "load": load_subset}
            sim_result = ems.simulate_year(sim_data, hours=sim_hours)
            
            # Calculate metrics for this simulation
            from . import EconomicAnalysis
            economic = EconomicAnalysis({'interest_rate': 0.03, 'project_lifetime': 20,
                                       'grid_buy_price': 0.023, 'grid_sell_price': 0.015})
            
            metrics = economic.calculate_all_objectives(components, sim_result)
            
            # Add simulation-specific data
            metrics['simulation_id'] = sim
            metrics['num_evs'] = num_evs
            metrics['mean_arrival_time'] = np.mean(arrival_departure['arrival_times'])
            metrics['mean_departure_time'] = np.mean(arrival_departure['departure_times'])
            metrics['mean_soc_arrival'] = np.mean(soc_profile['soc_arrival'])
            metrics['total_v2g_energy'] = sim_result['ev_discharge'].sum()
            metrics['total_g2v_energy'] = sim_result['ev_charge'].sum()
            
            simulation_results.append(metrics)
            
            if (sim + 1) % 100 == 0:
                logging.info(f"Monte Carlo progress: {sim + 1}/{self.num_simulations} simulations completed")
        
        # Analyze results
        df_results = pd.DataFrame(simulation_results)
        
        summary_stats = {
            'num_simulations': self.num_simulations,
            'num_evs': num_evs,
            'mean_coe': df_results['coe'].mean(),
            'std_coe': df_results['coe'].std(),
            'mean_lpsp': df_results['lpsp'].mean(),
            'std_lpsp': df_results['lpsp'].std(),
            'mean_ref': df_results['ref'].mean(),
            'std_ref': df_results['ref'].std(),
            'mean_v2g_energy': df_results['total_v2g_energy'].mean(),
            'std_v2g_energy': df_results['total_v2g_energy'].std(),
            'confidence_intervals': {
                'coe_95ci': [df_results['coe'].quantile(0.025), df_results['coe'].quantile(0.975)],
                'lpsp_95ci': [df_results['lpsp'].quantile(0.025), df_results['lpsp'].quantile(0.975)],
                'ref_95ci': [df_results['ref'].quantile(0.025), df_results['ref'].quantile(0.975)]
            }
        }
        
        return {
            'summary_statistics': summary_stats,
            'detailed_results': df_results,
            'simulation_parameters': {
                'num_simulations': self.num_simulations,
                'num_evs': num_evs,
                'solution': solution
            }
        } 
    

    # Example usage
if __name__ == "__main__":
    # Example economic analysis
    economic_params = {
        'interest_rate': 0.03,
        'project_lifetime': 20,
        'grid_buy_price': 0.023,
        'grid_sell_price': 0.015
    }

    # Example Monte Carlo setup
    mc_sim = MonteCarloSimulation(num_simulations=100)
    print(f"Monte Carlo simulation setup for {mc_sim.num_simulations} runs")
