# analysis/economic_analysis.py
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Union
import logging

class EconomicAnalysis:
    """
    Economic analysis module based on MATLAB objective functions
    Calculates COE, LPSP, REF, and NPC based on thesis equations
    """
    
    def __init__(self, economic_params: Dict):
        """
        Initialize economic analysis parameters from MATLAB code
        
        Args:
            economic_params: Dictionary containing economic parameters
        """
        self.interest_rate = economic_params.get('interest_rate', 0.03)  # ir in MATLAB
        self.project_lifetime = economic_params.get('project_lifetime', 20)  # 20 years in MATLAB
        self.grid_buy_price = economic_params.get('grid_buy_price', 0.023)  # Grid_p in MATLAB
        self.grid_sell_price = economic_params.get('grid_sell_price', 0.015)  # Grid_sale in MATLAB
        
        # Component costs ($/unit) - can be updated based on market data
        self.component_costs = {
            'pv_panel': 200,      # $ per panel
            'wind_turbine': 2000, # $ per kW
            'battery': 300,       # $ per kWh
            'converter': 150,     # $ per kW
            'inverter': 100,      # $ per kW
            'installation': 0.2   # 20% of equipment cost
        }
        
        # Calculate Capital Recovery Factor (CRF)
        self.crf = self.calculate_crf()
        
        logging.info(f"Economic analysis initialized with {self.project_lifetime} year lifetime")
    
    def calculate_crf(self) -> float:
        """
        Calculate Capital Recovery Factor based on MATLAB code
        CRF = ir * (1+ir)^n / ((1+ir)^n - 1)
        """
        ir = self.interest_rate
        n = self.project_lifetime
        
        if ir == 0:
            return 1.0 / n
        
        crf = (ir * (1 + ir) ** n) / ((1 + ir) ** n - 1)
        return crf
    
    def calculate_component_costs(self, components: Dict) -> Dict[str, float]:
        """
        Calculate total component costs based on sizing
        
        Args:
            components: Dictionary with component objects
            
        Returns:
            Dictionary with cost breakdown
        """
        costs = {}
        
        # PV system cost
        if 'pv' in components:
            pv = components['pv']
            pv_cost = pv.num_panels * self.component_costs['pv_panel']
            costs['pv_cost'] = pv_cost
        
        # Wind turbine cost
        if 'wt' in components:
            wt = components['wt']
            wt_cost = wt.num_turbines * wt.rated_power / 1000 * self.component_costs['wind_turbine']
            costs['wt_cost'] = wt_cost
        
        # Battery cost
        if 'bt' in components:
            battery = components['bt']
            battery_cost = battery.num_batteries * battery.capacity / 1000 * self.component_costs['battery']
            costs['battery_cost'] = battery_cost
        
        # Power electronics cost (converter + inverter)
        total_renewable_power = 0
        if 'pv' in components:
            total_renewable_power += components['pv'].total_rated_power
        if 'wt' in components:
            total_renewable_power += components['wt'].total_rated_power
        
        converter_cost = total_renewable_power * self.component_costs['converter']
        inverter_cost = total_renewable_power * self.component_costs['inverter']
        
        costs['converter_cost'] = converter_cost
        costs['inverter_cost'] = inverter_cost
        
        # Installation and miscellaneous costs
        equipment_cost = sum(costs.values())
        installation_cost = equipment_cost * self.component_costs['installation']
        costs['installation_cost'] = installation_cost
        
        # Total capital cost
        costs['total_capital_cost'] = sum(costs.values())
        
        return costs
    
    def calculate_npc(self, components: Dict) -> float:
        """
        Calculate Net Present Cost (NPC) based on MATLAB code
        NPC = ASC / CRF where ASC is Annual System Cost
        """
        # Get component costs
        costs = self.calculate_component_costs(components)
        
        # Annual system cost (ASC) is the annualized capital cost
        asc = costs['total_capital_cost'] * self.crf
        
        # Net Present Cost
        npc = asc / self.crf  # This simplifies to total_capital_cost, but kept for clarity
        
        return npc
    
    def calculate_coe(self, 
                     components: Dict, 
                     simulation_results: pd.DataFrame) -> float:
        """
        Calculate Cost of Energy (COE) based on MATLAB objective function
        COE = ((CRF * NPC) + grid_cost - R_grid) / total_load
        """
        # Calculate NPC and annualized cost
        npc = self.calculate_npc(components)
        annualized_capital_cost = self.crf * npc
        
        # Calculate grid interaction costs from simulation results
        total_grid_purchase = simulation_results['grid_purchase'].sum()
        total_grid_sale = simulation_results['grid_sale'].sum()
        
        grid_cost = total_grid_purchase * self.grid_buy_price
        grid_revenue = total_grid_sale * self.grid_sell_price  # R_grid in MATLAB
        
        # Total annual load
        total_load = simulation_results['load_demand'].sum()
        
        if total_load == 0:
            return float('inf')
        
        # COE calculation
        coe = (annualized_capital_cost + grid_cost - grid_revenue) / total_load
        
        return coe
    
    def calculate_lpsp(self, simulation_results: pd.DataFrame) -> float:
        """
        Calculate Loss of Power Supply Probability (LPSP) based on MATLAB code
        LPSP = sum(LPS) / sum(total_load)
        where LPS = load - (renewable_power - grid_purchase)
        """
        total_load = simulation_results['load_demand'].sum()
        
        if total_load == 0:
            return 0.0
        
        # Calculate Load Power Shortage (LPS) for each time step
        renewable_power = simulation_results['pv_power'] + simulation_results['wt_power']
        battery_discharge = simulation_results['battery_discharge'] 
        ev_discharge = simulation_results['ev_discharge']
        grid_purchase = simulation_results['grid_purchase']
        
        # Total power supply
        total_supply = renewable_power + battery_discharge + ev_discharge + grid_purchase
        
        # Power shortage occurs when supply < demand
        power_shortage = np.maximum(0, simulation_results['load_demand'] - total_supply)
        
        # LPSP is the ratio of total shortage to total load
        lpsp = power_shortage.sum() / total_load
        
        return lpsp
    
    def calculate_ref(self, simulation_results: pd.DataFrame) -> float:
        """
        Calculate Renewable Energy Fraction (REF) based on MATLAB code
        REF = sum(renewable_power) / sum(renewable_power + grid_purchase)
        """
        renewable_power = simulation_results['pv_power'] + simulation_results['wt_power']
        grid_purchase = simulation_results['grid_purchase']
        
        total_renewable = renewable_power.sum()
        total_energy_supply = total_renewable + grid_purchase.sum()
        
        if total_energy_supply == 0:
            return 0.0
        
        ref = total_renewable / total_energy_supply
        return ref
    
    def calculate_all_objectives(self, 
                               components: Dict, 
                               simulation_results: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate all economic objectives (COE, LPSP, REF, NPC)
        
        Returns:
            Dictionary with all calculated metrics
        """
        results = {
            'coe': self.calculate_coe(components, simulation_results),
            'lpsp': self.calculate_lpsp(simulation_results),
            'ref': self.calculate_ref(simulation_results),
            'npc': self.calculate_npc(components)
        }
        
        # Additional metrics
        results['total_grid_cost'] = (simulation_results['grid_purchase'].sum() * self.grid_buy_price - 
                                    simulation_results['grid_sale'].sum() * self.grid_sell_price)
        results['renewable_penetration'] = results['ref'] * 100  # Percentage
        results['lpsp_percentage'] = results['lpsp'] * 100  # Percentage
        
        return results


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
            from ..energy_management.rule_based_ems import RuleBasedEMS
            ems = RuleBasedEMS(components)
            
            # Simulate shorter period for Monte Carlo (e.g., one week)
            sim_hours = min(168, hours)  # One week or available data
            weather_subset = data['weather'].iloc[:sim_hours]
            load_subset = data['load'].iloc[:sim_hours]
            
            sim_result = ems.simulate_year(weather_subset, load_subset)
            
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
    
    economic = EconomicAnalysis(economic_params)
    print(f"Capital Recovery Factor: {economic.crf:.4f}")
    
    # Example Monte Carlo setup
    mc_sim = MonteCarloSimulation(num_simulations=100)
    print(f"Monte Carlo simulation setup for {mc_sim.num_simulations} runs")