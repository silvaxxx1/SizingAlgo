# energy_management/rule_based_ems.py
"""
Rule-Based Energy Management System (RB-EMS)
Based on the MATLAB charge/discharge functions and operation modes
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from enum import Enum

import sys
from pathlib import Path

# Add src folder to Python path
sys.path.append(str(Path(__file__).parent.parent))


# Import operation modes from the operation_modes module
try:
    from .operation_modes import OperationMode, OperationModeManager
except ImportError:
    # Fallback if operation_modes not available
    from enum import Enum
    class OperationMode(Enum):
        MODE_1_RENEWABLE_DIRECT = "renewable_direct_supply"
        MODE_2_BATTERY_DISCHARGE = "battery_discharge"
        MODE_3_GRID_PURCHASE = "grid_purchase"
        MODE_4_V2G_DISCHARGE = "vehicle_to_grid"
        MODE_5_SURPLUS_STORAGE = "surplus_storage"
        MODE_6_SURPLUS_EXPORT = "surplus_export"

class RuleBasedEMS:
    """
    Rule-Based Energy Management System
    Implements the charge/discharge logic from MATLAB code
    """
    
    def __init__(self, components: Dict):
        """
        Initialize EMS with system components
        
        Args:
            components: Dictionary containing 'pv', 'wt', 'bt', 'ev', 'grid' components
        """
        self.pv = components.get('pv')
        self.wt = components.get('wt') 
        self.battery = components.get('bt')
        self.ev = components.get('ev')
        self.grid = components.get('grid')
        
        if not all([self.pv, self.wt, self.battery, self.ev, self.grid]):
            missing = [k for k, v in components.items() if v is None]
            raise ValueError(f"Missing components: {missing}")
        
        # Operation tracking
        self.operation_modes = []
        self.power_flows = []
        self.time_step = 0
        
        # EMS parameters based on MATLAB code
        self.converter_efficiency = 0.95  # uconv in MATLAB
        self.inverter_efficiency = 0.95   # uinv in MATLAB
        
        logging.info("Rule-Based EMS initialized successfully")
    
    def execute_time_step(self, 
                         time_step: int,
                         weather_data: Dict,
                         load_demand: float) -> Dict[str, float]:
        """
        Execute EMS logic for one time step
        Based on MATLAB charge/discharge functions
        
        Args:
            time_step: Current time step (hour)
            weather_data: Weather data dict with 'solar_irradiance', 'ambient_temp', 'wind_speed'
            load_demand: Load demand (kWh)
            
        Returns:
            Dictionary with power flows and operation details
        """
        self.time_step = time_step
        
        # Calculate renewable power generation
        pv_power = self.pv.calculate_output_power(
            weather_data['solar_irradiance'],
            weather_data['ambient_temp']
        )
        
        wt_power = self.wt.calculate_output_power(
            weather_data['wind_speed']
        )
        
        # Total renewable power available
        renewable_power = pv_power + wt_power
        
        # Initialize result dictionary
        result = {
            'time_step': time_step,
            'load_demand': load_demand,
            'pv_power': pv_power,
            'wt_power': wt_power,
            'renewable_power': renewable_power,
            'battery_charge': 0.0,
            'battery_discharge': 0.0,
            'ev_charge': 0.0,
            'ev_discharge': 0.0,
            'grid_purchase': 0.0,
            'grid_sale': 0.0,
            'operation_mode': None,
            'battery_soc': self.battery.get_soc(),
            'ev_mean_soc': np.mean(self.ev.fleet_soc) if hasattr(self.ev, 'fleet_soc') else 0.5
        }
        
        # Calculate net power balance
        net_power = renewable_power - load_demand
        
        if net_power > 0:
            # Surplus power available - Execute charging sequence (MATLAB charge function)
            result = self._handle_surplus_power(net_power, time_step, result)
        else:
            # Power deficit - Execute discharging sequence (MATLAB discharge function)
            result = self._handle_power_deficit(-net_power, time_step, result)
        
        # Update tracking
        self.operation_modes.append(result['operation_mode'])
        self.power_flows.append(result)
        
        return result
    
    def _handle_surplus_power(self, 
                             surplus_power: float, 
                             time_step: int,
                             result: Dict) -> Dict:
        """
        Handle surplus power according to MATLAB charge function logic
        
        This implements the charging sequence from the MATLAB code:
        1. Check if battery can be charged
        2. Charge EVs if available and needed
        3. Export surplus to grid
        """
        remaining_surplus = surplus_power
        
        # Apply inverter efficiency to surplus power (from MATLAB: *uinv)
        available_power = remaining_surplus * self.inverter_efficiency
        
        # Priority 1: Charge battery if below maximum SOC
        if self.battery.get_soc() < self.battery.soc_max and available_power > 0:
            # Calculate power available for charging after load is met
            power_for_charge = available_power
            
            # Apply converter efficiency (from MATLAB: *uconv*n_bat)
            energy_to_battery = power_for_charge * self.converter_efficiency * self.battery.efficiency
            
            energy_charged, energy_surplus = self.battery.charge(energy_to_battery)
            result['battery_charge'] = energy_charged
            
            # Update remaining surplus
            if energy_charged > 0:
                used_power = energy_charged / (self.converter_efficiency * self.battery.efficiency)
                available_power -= used_power
                result['operation_mode'] = OperationMode.MODE_5_SURPLUS_STORAGE
        
        # Priority 2: Charge EVs if available and below critical SOC
        if available_power > 0 and hasattr(self.ev, 'get_available_vehicles'):
            available_vehicles = self.ev.get_available_vehicles(time_step)
            
            if len(available_vehicles) > 0:
                # Check if any EV needs charging (below critical SOC)
                critical_soc = self.ev.soc_max * 0.2  # 20% of max SOC (from MATLAB)
                vehicles_needing_charge = [v for v in available_vehicles 
                                         if self.ev.fleet_soc[v] < critical_soc]
                
                if vehicles_needing_charge or available_power > self.ev.charge_rate:
                    ev_energy_used, ev_remaining = self.ev.charge_fleet(available_power, time_step)
                    result['ev_charge'] = ev_energy_used
                    available_power = ev_remaining
                    
                    if ev_energy_used > 0:
                        if result['operation_mode'] is None:
                            result['operation_mode'] = OperationMode.MODE_3_GRID_PURCHASE  # G2V mode
        
        # Priority 3: Export surplus to grid
        if available_power > 0:
            energy_sold, revenue = self.grid.sell_energy(available_power)
            result['grid_sale'] = energy_sold
            
            if result['operation_mode'] is None:
                result['operation_mode'] = OperationMode.MODE_6_SURPLUS_EXPORT
        
        return result
    
    def _handle_power_deficit(self, 
                             deficit_power: float, 
                             time_step: int,
                             result: Dict) -> Dict:
        """
        Handle power deficit according to MATLAB discharge function logic
        
        This implements the discharging sequence from the MATLAB code:
        1. Try to discharge battery if above minimum SOC
        2. Try V2G discharge if EVs available and above critical SOC
        3. Purchase remaining deficit from grid
        """
        remaining_deficit = deficit_power
        
        # Apply inverter efficiency to demand (load/uinv in MATLAB)
        required_power = remaining_deficit / self.inverter_efficiency
        
        # Priority 1: Discharge battery if above minimum SOC
        if self.battery.get_soc() > self.battery.soc_min and required_power > 0:
            # Try to discharge from battery
            energy_discharged, energy_deficit = self.battery.discharge(required_power)
            result['battery_discharge'] = energy_discharged
            
            if energy_discharged > 0:
                # Update remaining deficit
                remaining_deficit -= energy_discharged
                result['operation_mode'] = OperationMode.MODE_2_BATTERY_DISCHARGE
        
        # Priority 2: V2G discharge if EVs available and above critical SOC
        if remaining_deficit > 0 and hasattr(self.ev, 'get_available_vehicles'):
            available_vehicles = self.ev.get_available_vehicles(time_step)
            
            if len(available_vehicles) > 0:
                # Check if any EV can discharge (above critical SOC)
                critical_soc = self.ev.soc_max * 0.2  # From MATLAB: Evmax*.2
                vehicles_can_discharge = [v for v in available_vehicles 
                                        if self.ev.fleet_soc[v] > critical_soc]
                
                if vehicles_can_discharge:
                    # Check discharge rate constraint (from MATLAB: D_Rate)
                    available_discharge_power = min(remaining_deficit, 
                                                  len(vehicles_can_discharge) * self.ev.discharge_rate)
                    
                    ev_energy_provided, ev_deficit = self.ev.discharge_fleet(
                        available_discharge_power, time_step)
                    result['ev_discharge'] = ev_energy_provided
                    remaining_deficit -= ev_energy_provided
                    
                    if ev_energy_provided > 0:
                        if result['operation_mode'] is None:
                            result['operation_mode'] = OperationMode.MODE_4_V2G_DISCHARGE
        
        # Priority 3: Purchase remaining deficit from grid
        if remaining_deficit > 0:
            energy_purchased, cost = self.grid.purchase_energy(remaining_deficit)
            result['grid_purchase'] = energy_purchased
            
            if result['operation_mode'] is None:
                result['operation_mode'] = OperationMode.MODE_3_GRID_PURCHASE
        
        return result
    
    def simulate_year(self, 
                     data: Dict,
                     hours: int = 8760) -> pd.DataFrame:
        """
        Simulate full year operation (8760 hours)
        
        Args:
            data: Dictionary with 'weather' and 'load' DataFrames
            hours: Number of hours to simulate
            
        Returns:
            DataFrame with complete simulation results
        """
        results = []
        
        # Reset all components to initial state
        self.battery.reset_state(0.5)  # Start at 50% SOC
        if hasattr(self.ev, 'reset_fleet_state'):
            self.ev.reset_fleet_state(0.5)  # Start fleet at 50% SOC
        if hasattr(self.grid, 'reset_tracking'):
            self.grid.reset_tracking()
        
        # Generate EV availability pattern if not already set
        if hasattr(self.ev, 'generate_availability_pattern'):
            self.ev.generate_availability_pattern(hours)
        
        weather_data = data['weather']
        load_data = data['load']
        
        # Ensure we don't exceed available data
        sim_hours = min(hours, len(weather_data), len(load_data))
        
        logging.info(f"Starting EMS simulation for {sim_hours} hours")
        
        for hour in range(sim_hours):
            # Get weather conditions
            weather_conditions = {
                'solar_irradiance': weather_data.iloc[hour].get('solar_irradiance', 0),
                'ambient_temp': weather_data.iloc[hour].get('ambient_temp', 25),
                'wind_speed': weather_data.iloc[hour].get('wind_speed', 0)
            }
            
            # Get load demand
            load_demand = load_data.iloc[hour].get('load_demand', 1.0)
            
            # Execute EMS for this time step
            result = self.execute_time_step(
                time_step=hour,
                weather_data=weather_conditions,
                load_demand=load_demand
            )
            
            results.append(result)
            
            # Simulate daily EV driving (once per day at 6 AM)
            if hour % 24 == 6 and hasattr(self.ev, 'simulate_daily_driving'):
                self.ev.simulate_daily_driving()
            
            # Log progress periodically
            if hour % 1000 == 0:
                logging.info(f"EMS simulation progress: {hour}/{sim_hours} hours completed")
        
        logging.info("EMS simulation completed successfully")
        return pd.DataFrame(results)
    
    def get_operation_statistics(self) -> Dict:
        """Get statistics about operation modes and system performance"""
        if not self.operation_modes:
            return {}
        
        # Count operation modes
        mode_counts = {}
        for mode in OperationMode:
            count = sum(1 for m in self.operation_modes if m == mode)
            mode_counts[mode.name] = count
        
        total_hours = len(self.operation_modes)
        
        # Calculate energy flows
        if self.power_flows:
            power_df = pd.DataFrame(self.power_flows)
            
            total_renewable = power_df['renewable_power'].sum()
            total_load = power_df['load_demand'].sum()
            total_battery_charge = power_df['battery_charge'].sum()
            total_battery_discharge = power_df['battery_discharge'].sum()
            total_grid_purchase = power_df['grid_purchase'].sum()
            total_grid_sale = power_df['grid_sale'].sum()
            total_v2g = power_df['ev_discharge'].sum()
            total_g2v = power_df['ev_charge'].sum()
            
            return {
                'total_hours': total_hours,
                'mode_counts': mode_counts,
                'mode_percentages': {k: (v/total_hours)*100 for k, v in mode_counts.items()},
                'energy_flows': {
                    'total_renewable_energy': total_renewable,
                    'total_load_energy': total_load,
                    'total_battery_charge': total_battery_charge,
                    'total_battery_discharge': total_battery_discharge,
                    'total_grid_purchase': total_grid_purchase,
                    'total_grid_sale': total_grid_sale,
                    'total_v2g_energy': total_v2g,
                    'total_g2v_energy': total_g2v,
                    'renewable_fraction': total_renewable / total_load if total_load > 0 else 0,
                    'grid_independence': 1 - (total_grid_purchase / total_load) if total_load > 0 else 0
                }
            }
        
        return {
            'total_hours': total_hours,
            'mode_counts': mode_counts,
            'mode_percentages': {k: (v/total_hours)*100 for k, v in mode_counts.items()}
        }
    
    def reset_ems(self):
        """Reset EMS state for new simulation"""
        self.operation_modes = []
        self.power_flows = []
        self.time_step = 0
        logging.info("EMS state reset")

from components import PhotovoltaicSystem, WindTurbine, BatterySystem, ElectricVehicle, Grid

# --------------------------
# 1. Initialize Components
# --------------------------

pv = PhotovoltaicSystem(rated_power=50, temp_coefficient=-0.5, noct=45)
wt = WindTurbine(rated_power=30, cut_in_speed=3, cut_out_speed=25, rated_speed=12)
bt = BatterySystem(capacity=100, soc_min=0.2, soc_max=0.95, efficiency=0.9)
ev = ElectricVehicle(capacity=40, soc_min=0.2, soc_max=0.9)
grid = Grid(buy_price=0.15, sell_price=0.10)

components = {'pv': pv, 'wt': wt, 'bt': bt, 'ev': ev, 'grid': grid}

# --------------------------
# 2. Initialize EMS
# --------------------------

ems = RuleBasedEMS(components)

# --------------------------
# 3. Generate Dummy Data
# --------------------------

hours = 24
weather_data = pd.DataFrame({
    'solar_irradiance': np.random.uniform(0, 1, hours),  # kW/m^2
    'ambient_temp': np.random.uniform(15, 35, hours),    # Celsius
    'wind_speed': np.random.uniform(0, 12, hours)        # m/s
})

load_data = pd.DataFrame({
    'load_demand': np.random.uniform(10, 30, hours)      # kWh
})

data = {'weather': weather_data, 'load': load_data}

# --------------------------
# 4. Simulate EMS
# --------------------------

results = ems.simulate_year(data, hours=hours)

# --------------------------
# 5. Analyze Results
# --------------------------

stats = ems.get_operation_statistics()

print("Operation Mode Statistics:")
print(stats['mode_percentages'])

print("\nEnergy Flows Summary:")
for key, val in stats['energy_flows'].items():
    print(f"{key}: {val:.2f}")
