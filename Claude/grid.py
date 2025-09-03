# grid.py
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Union, List
from enum import Enum

class OperationMode(Enum):
    """Energy Management System operation modes based on MATLAB code"""
    MODE_1_RENEWABLE_SUPPLY = 1  # Renewable sources meet load directly
    MODE_2_BATTERY_DISCHARGE = 2  # Battery discharges to meet deficit
    MODE_3_GRID_TO_VEHICLE = 3    # Grid supplies energy for EV charging
    MODE_4_VEHICLE_TO_GRID = 4    # V2G operation to support grid

class Grid:
    """
    Grid interface component for microgrid system
    Based on MATLAB grid interaction logic
    """
    
    def __init__(self, 
                 buy_price: float = 0.023,  # $/kWh - Grid_p in MATLAB
                 sell_price: float = 0.015,  # $/kWh - Grid_sale in MATLAB  
                 max_import_power: float = None,  # kW
                 max_export_power: float = None):  # kW
        """
        Initialize grid parameters based on MATLAB economic parameters
        
        Args:
            buy_price: Price for purchasing electricity from grid ($/kWh)
            sell_price: Price for selling electricity to grid ($/kWh)
            max_import_power: Maximum import power limit (kW)
            max_export_power: Maximum export power limit (kW)
        """
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.max_import_power = max_import_power
        self.max_export_power = max_export_power
        
        # Energy tracking
        self.energy_purchased = []  # Egrid_p in MATLAB
        self.energy_sold = []       # Egrid_s in MATLAB
        self.costs = []
        self.revenues = []
        
    def purchase_energy(self, energy_demand: float) -> Tuple[float, float]:
        """
        Purchase energy from grid to meet demand
        
        Args:
            energy_demand: Energy needed from grid (kWh)
            
        Returns:
            Tuple of (energy_purchased, cost)
        """
        if energy_demand <= 0:
            return 0.0, 0.0
        
        # Apply power limit if specified
        if self.max_import_power is not None:
            energy_purchased = min(energy_demand, self.max_import_power)
        else:
            energy_purchased = energy_demand
        
        cost = energy_purchased * self.buy_price
        
        # Update tracking
        self.energy_purchased.append(energy_purchased)
        self.costs.append(cost)
        
        return energy_purchased, cost
    
    def sell_energy(self, energy_surplus: float) -> Tuple[float, float]:
        """
        Sell surplus energy to grid
        
        Args:
            energy_surplus: Surplus energy to sell (kWh)
            
        Returns:
            Tuple of (energy_sold, revenue)
        """
        if energy_surplus <= 0:
            return 0.0, 0.0
        
        # Apply power limit if specified
        if self.max_export_power is not None:
            energy_sold = min(energy_surplus, self.max_export_power)
        else:
            energy_sold = energy_surplus
        
        revenue = energy_sold * self.sell_price
        
        # Update tracking
        self.energy_sold.append(energy_sold)
        self.revenues.append(revenue)
        
        return energy_sold, revenue
    
    def calculate_net_cost(self) -> Dict[str, float]:
        """Calculate net grid interaction costs"""
        total_purchased = sum(self.energy_purchased)
        total_sold = sum(self.energy_sold)
        total_cost = sum(self.costs)
        total_revenue = sum(self.revenues)
        
        return {
            'total_energy_purchased': total_purchased,
            'total_energy_sold': total_sold,
            'total_cost': total_cost,
            'total_revenue': total_revenue,
            'net_cost': total_cost - total_revenue,
            'net_energy': total_purchased - total_sold
        }
    
    def reset_tracking(self):
        """Reset energy and cost tracking"""
        self.energy_purchased = []
        self.energy_sold = []
        self.costs = []
        self.revenues = []


class RuleBasedEMS:
    """
    Rule-Based Energy Management System
    Based on the charge/discharge functions in MATLAB code
    """
    
    def __init__(self, components: Dict):
        """
        Initialize EMS with system components
        
        Args:
            components: Dictionary containing 'pv', 'wt', 'bt', 'ev', 'grid' components
        """
        self.pv = components['pv']
        self.wt = components['wt'] 
        self.battery = components['bt']
        self.ev = components['ev']
        self.grid = components['grid']
        
        # Operation mode tracking
        self.operation_modes = []
        self.power_flows = []
        
    def execute_time_step(self, 
                         time_step: int,
                         load_demand: float,
                         pv_power: float,
                         wt_power: float) -> Dict[str, float]:
        """
        Execute EMS logic for one time step
        Based on MATLAB charge/discharge functions
        
        Args:
            time_step: Current time step
            load_demand: Load demand (kWh)
            pv_power: PV power available (kWh) 
            wt_power: Wind turbine power available (kWh)
            
        Returns:
            Dictionary with power flows and operation details
        """
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
            'ev_mean_soc': np.mean(self.ev.fleet_soc) if self.ev.num_vehicles > 0 else 0
        }
        
        # Calculate net power balance
        net_power = renewable_power - load_demand
        
        if net_power > 0:
            # Surplus power available - Execute charging sequence
            result = self._handle_surplus_power(net_power, time_step, result)
        else:
            # Power deficit - Execute discharging sequence  
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
        """
        remaining_surplus = surplus_power
        
        # Priority 1: Charge battery if below maximum SOC
        if self.battery.get_soc() < self.battery.soc_max and remaining_surplus > 0:
            energy_charged, energy_surplus = self.battery.charge(remaining_surplus)
            result['battery_charge'] = energy_charged
            remaining_surplus = energy_surplus
            
            if energy_charged > 0:
                result['operation_mode'] = OperationMode.MODE_1_RENEWABLE_SUPPLY
        
        # Priority 2: Charge EVs if available and below maximum SOC
        if remaining_surplus > 0:
            ev_energy_used, ev_remaining = self.ev.charge_fleet(remaining_surplus, time_step)
            result['ev_charge'] = ev_energy_used
            remaining_surplus = ev_remaining
            
            if ev_energy_used > 0 and result['operation_mode'] is None:
                result['operation_mode'] = OperationMode.MODE_3_GRID_TO_VEHICLE
        
        # Priority 3: Sell surplus to grid
        if remaining_surplus > 0:
            energy_sold, revenue = self.grid.sell_energy(remaining_surplus)
            result['grid_sale'] = energy_sold
            
            if result['operation_mode'] is None:
                result['operation_mode'] = OperationMode.MODE_1_RENEWABLE_SUPPLY
        
        return result
    
    def _handle_power_deficit(self, 
                             deficit_power: float, 
                             time_step: int,
                             result: Dict) -> Dict:
        """
        Handle power deficit according to MATLAB discharge function logic
        """
        remaining_deficit = deficit_power
        
        # Priority 1: Discharge battery if above minimum SOC
        if self.battery.get_soc() > self.battery.soc_min and remaining_deficit > 0:
            energy_discharged, energy_deficit = self.battery.discharge(remaining_deficit)
            result['battery_discharge'] = energy_discharged
            remaining_deficit = energy_deficit
            
            if energy_discharged > 0:
                result['operation_mode'] = OperationMode.MODE_2_BATTERY_DISCHARGE
        
        # Priority 2: V2G discharge if EVs available and above critical SOC
        if remaining_deficit > 0:
            ev_energy_provided, ev_deficit = self.ev.discharge_fleet(remaining_deficit, time_step)
            result['ev_discharge'] = ev_energy_provided  
            remaining_deficit = ev_deficit
            
            if ev_energy_provided > 0 and result['operation_mode'] is None:
                result['operation_mode'] = OperationMode.MODE_4_VEHICLE_TO_GRID
        
        # Priority 3: Purchase from grid
        if remaining_deficit > 0:
            energy_purchased, cost = self.grid.purchase_energy(remaining_deficit)
            result['grid_purchase'] = energy_purchased
            
            if result['operation_mode'] is None:
                result['operation_mode'] = OperationMode.MODE_3_GRID_TO_VEHICLE
        
        return result
    
    def simulate_year(self, 
                     weather_data: pd.DataFrame,
                     load_data: pd.DataFrame) -> pd.DataFrame:
        """
        Simulate full year operation (8760 hours)
        
        Args:
            weather_data: DataFrame with solar irradiance, wind speed, temperature
            load_data: DataFrame with hourly load demand
            
        Returns:
            DataFrame with complete simulation results
        """
        results = []
        
        # Reset all components
        self.battery.reset_state(0.5)  # Start at 50% SOC
        self.ev.reset_fleet_state(0.5)  # Start fleet at 50% SOC
        self.grid.reset_tracking()
        
        # Generate EV availability pattern
        self.ev.generate_availability_pattern(len(weather_data))
        
        for hour in range(len(weather_data)):
            # Get PV power output
            pv_power = self.pv.calculate_output_power(
                weather_data.iloc[hour]['solar_irradiance'],
                weather_data.iloc[hour]['ambient_temp']
            )
            
            # Get wind turbine power output  
            wt_power = self.wt.calculate_output_power(
                weather_data.iloc[hour]['wind_speed']
            )
            
            # Get load demand
            load_demand = load_data.iloc[hour]['load_demand']
            
            # Execute EMS for this time step
            result = self.execute_time_step(
                time_step=hour,
                load_demand=load_demand,
                pv_power=pv_power,
                wt_power=wt_power
            )
            
            results.append(result)
            
            # Simulate daily EV driving (once per day at hour 6)
            if hour % 24 == 6:  # 6 AM
                self.ev.simulate_daily_driving()
        
        return pd.DataFrame(results)
    
    def get_operation_statistics(self) -> Dict[str, Union[float, int]]:
        """Get statistics about operation modes"""
        if not self.operation_modes:
            return {}
        
        mode_counts = {}
        for mode in OperationMode:
            count = sum(1 for m in self.operation_modes if m == mode)
            mode_counts[mode.name] = count
        
        total_hours = len(self.operation_modes)
        
        return {
            'total_hours': total_hours,
            'mode_counts': mode_counts,
            'mode_percentages': {k: (v/total_hours)*100 for k, v in mode_counts.items()}
        }


# Example usage
if __name__ == "__main__":
    # This would typically be imported and used with actual components
    print("Grid and EMS components implemented successfully")
    
    # Example grid calculations
    grid = Grid(buy_price=0.023, sell_price=0.015)
    
    # Example transactions
    purchased, cost = grid.purchase_energy(100)  # Buy 100 kWh
    sold, revenue = grid.sell_energy(50)         # Sell 50 kWh
    
    net_cost = grid.calculate_net_cost()
    print(f"Net grid cost: ${net_cost['net_cost']:.2f}")