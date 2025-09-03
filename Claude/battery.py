# battery.py
import numpy as np
import pandas as pd
from typing import Union, List, Tuple

class BatterySystem:
    """
    Battery Energy Storage System (BESS) model based on thesis MATLAB code
    Implements charge/discharge operations with SOC constraints
    """
    
    def __init__(self, 
                 capacity: float = 35380,  # Wh - Battery capacity
                 voltage: float = 48,  # V - Battery voltage (Vs in MATLAB)
                 depth_of_discharge: float = 0.8,  # DOD (dod in MATLAB)
                 soc_min: float = 0.2,  # Minimum SOC
                 soc_max: float = 1.0,  # Maximum SOC
                 efficiency: float = 0.85,  # Round trip efficiency (n_bat in MATLAB)
                 inverter_efficiency: float = 0.95,  # uinv in MATLAB
                 converter_efficiency: float = 0.95,  # uconv in MATLAB
                 autonomy_days: float = 3,  # AD in MATLAB
                 num_batteries: int = 1):
        """
        Initialize battery system based on MATLAB parameters
        
        Args:
            capacity: Battery capacity per unit (Wh)
            voltage: Battery voltage (V)
            depth_of_discharge: Maximum allowable DOD
            soc_min: Minimum state of charge
            soc_max: Maximum state of charge  
            efficiency: Battery round trip efficiency
            inverter_efficiency: Inverter efficiency
            converter_efficiency: Converter efficiency
            autonomy_days: Days of autonomy
            num_batteries: Number of battery units
        """
        self.capacity = capacity  # Wh per battery
        self.voltage = voltage
        self.dod = depth_of_discharge
        self.soc_min = soc_min
        self.soc_max = soc_max
        self.efficiency = efficiency
        self.inverter_efficiency = inverter_efficiency
        self.converter_efficiency = converter_efficiency
        self.autonomy_days = autonomy_days
        self.num_batteries = num_batteries
        
        # Calculate total system parameters
        self.total_capacity = capacity * num_batteries  # Total Wh
        self.usable_capacity = self.total_capacity * self.dod  # Usable Wh
        
        # Initialize state variables
        self.soc = 0.5  # Start at 50% SOC
        self.energy_stored = self.soc * self.total_capacity  # Wh
        
        # Energy tracking arrays
        self.charge_history = []
        self.discharge_history = []
        self.soc_history = []
        
    def get_energy_stored(self) -> float:
        """Get current energy stored in Wh"""
        return self.energy_stored
    
    def get_soc(self) -> float:
        """Get current state of charge (0-1)"""
        return self.soc
    
    def get_available_charge_capacity(self) -> float:
        """Get available charging capacity in Wh"""
        return (self.soc_max * self.total_capacity) - self.energy_stored
    
    def get_available_discharge_capacity(self) -> float:
        """Get available discharging capacity in Wh"""
        return self.energy_stored - (self.soc_min * self.total_capacity)
    
    def charge(self, energy_available: float) -> Tuple[float, float]:
        """
        Charge battery with available energy
        Based on MATLAB charge function
        
        Args:
            energy_available: Energy available for charging (Wh)
            
        Returns:
            Tuple of (energy_charged, energy_surplus)
        """
        if energy_available <= 0:
            return 0.0, 0.0
        
        # Apply converter and battery efficiency
        energy_to_battery = energy_available * self.converter_efficiency * self.efficiency
        
        # Check available charging capacity
        max_charge = self.get_available_charge_capacity()
        
        if energy_to_battery <= max_charge:
            # Can charge all available energy
            self.energy_stored += energy_to_battery
            self.soc = self.energy_stored / self.total_capacity
            energy_charged = energy_to_battery
            energy_surplus = 0.0
        else:
            # Battery reaches maximum SOC
            energy_charged = max_charge
            self.energy_stored = self.soc_max * self.total_capacity
            self.soc = self.soc_max
            # Calculate surplus considering efficiency losses
            energy_surplus = energy_available - (energy_charged / (self.converter_efficiency * self.efficiency))
        
        # Update history
        self.charge_history.append(energy_charged)
        self.soc_history.append(self.soc)
        
        return energy_charged, energy_surplus
    
    def discharge(self, energy_demand: float) -> Tuple[float, float]:
        """
        Discharge battery to meet energy demand
        Based on MATLAB discharge function
        
        Args:
            energy_demand: Energy demand to be met (Wh)
            
        Returns:
            Tuple of (energy_discharged, energy_deficit)
        """
        if energy_demand <= 0:
            return 0.0, 0.0
        
        # Check available discharge capacity
        max_discharge = self.get_available_discharge_capacity()
        
        # Apply inverter efficiency to energy demand
        energy_needed_from_battery = energy_demand / self.inverter_efficiency
        
        if max_discharge >= energy_needed_from_battery:
            # Can discharge required energy
            self.energy_stored -= energy_needed_from_battery
            self.soc = self.energy_stored / self.total_capacity
            energy_discharged = energy_demand  # What's actually delivered to load
            energy_deficit = 0.0
        else:
            # Battery reaches minimum SOC
            energy_discharged = max_discharge * self.inverter_efficiency
            self.energy_stored = self.soc_min * self.total_capacity
            self.soc = self.soc_min
            energy_deficit = energy_demand - energy_discharged
        
        # Update history
        self.discharge_history.append(energy_discharged)
        self.soc_history.append(self.soc)
        
        return energy_discharged, energy_deficit
    
    def reset_state(self, initial_soc: float = 0.5):
        """Reset battery to initial state"""
        self.soc = np.clip(initial_soc, self.soc_min, self.soc_max)
        self.energy_stored = self.soc * self.total_capacity
        self.charge_history = []
        self.discharge_history = []
        self.soc_history = []
    
    def simulate_operation(self, 
                          energy_available: np.ndarray, 
                          energy_demand: np.ndarray,
                          initial_soc: float = 0.5) -> pd.DataFrame:
        """
        Simulate battery operation over time period
        
        Args:
            energy_available: Array of available energy for charging (Wh)
            energy_demand: Array of energy demand (Wh)
            initial_soc: Initial state of charge
            
        Returns:
            DataFrame with simulation results
        """
        self.reset_state(initial_soc)
        
        results = {
            'time': [],
            'soc': [],
            'energy_stored': [],
            'energy_charged': [],
            'energy_discharged': [],
            'energy_surplus': [],
            'energy_deficit': []
        }
        
        for t, (available, demand) in enumerate(zip(energy_available, energy_demand)):
            net_energy = available - demand
            
            if net_energy > 0:
                # Excess energy - charge battery
                energy_charged, energy_surplus = self.charge(net_energy)
                energy_discharged = 0.0
                energy_deficit = 0.0
            else:
                # Energy deficit - discharge battery
                energy_discharged, energy_deficit = self.discharge(-net_energy)
                energy_charged = 0.0
                energy_surplus = 0.0
            
            # Store results
            results['time'].append(t)
            results['soc'].append(self.soc)
            results['energy_stored'].append(self.energy_stored)
            results['energy_charged'].append(energy_charged)
            results['energy_discharged'].append(energy_discharged)
            results['energy_surplus'].append(energy_surplus)
            results['energy_deficit'].append(energy_deficit)
        
        return pd.DataFrame(results)
    
    def calculate_battery_capacity_from_load(self, 
                                           annual_load: float, 
                                           autonomy_days: float = None) -> float:
        """
        Calculate required battery capacity based on load and autonomy days
        From MATLAB: Bcap=AD*EL/uinv*n_bat*dod*Vs
        
        Args:
            annual_load: Annual energy load (kWh)
            autonomy_days: Days of autonomy (if None, use self.autonomy_days)
            
        Returns:
            Required battery capacity (Wh)
        """
        if autonomy_days is None:
            autonomy_days = self.autonomy_days
        
        daily_load = annual_load / 365  # kWh/day
        # Convert to Wh and apply efficiency factors
        required_capacity = (autonomy_days * daily_load * 1000) / \
                           (self.inverter_efficiency * self.efficiency * self.dod)
        
        return required_capacity
    
    def get_specifications(self) -> dict:
        """Get battery system specifications"""
        return {
            'num_batteries': self.num_batteries,
            'capacity_per_battery': self.capacity,
            'total_capacity': self.total_capacity,
            'usable_capacity': self.usable_capacity,
            'voltage': self.voltage,
            'depth_of_discharge': self.dod,
            'soc_min': self.soc_min,
            'soc_max': self.soc_max,
            'efficiency': self.efficiency,
            'inverter_efficiency': self.inverter_efficiency,
            'converter_efficiency': self.converter_efficiency,
            'autonomy_days': self.autonomy_days
        }
    
    def calculate_lifetime_throughput(self, 
                                    charge_energy: np.ndarray,
                                    discharge_energy: np.ndarray) -> dict:
        """Calculate battery lifetime and throughput metrics"""
        total_charge = np.sum(charge_energy)
        total_discharge = np.sum(discharge_energy)
        total_throughput = (total_charge + total_discharge) / 2
        
        # Typical battery cycle life (can be parameterized)
        cycle_life = 5000  # cycles at rated DOD
        annual_cycles = total_throughput / self.usable_capacity
        estimated_lifetime = cycle_life / annual_cycles
        
        return {
            'total_charge_energy': total_charge,
            'total_discharge_energy': total_discharge,
            'total_throughput': total_throughput,
            'annual_cycles': annual_cycles,
            'estimated_lifetime_years': estimated_lifetime
        }
    
    def set_count(self, num_batteries: int):
        """Update number of batteries (for optimization)"""
        old_soc = self.soc
        self.num_batteries = num_batteries
        self.total_capacity = self.capacity * num_batteries
        self.usable_capacity = self.total_capacity * self.dod
        self.energy_stored = old_soc * self.total_capacity
    
    def set_autonomy_days(self, autonomy_days: float):
        """Update autonomy days (for optimization)"""
        self.autonomy_days = autonomy_days


# Example usage
if __name__ == "__main__":
    # Create battery system with MATLAB-based parameters
    battery = BatterySystem(
        capacity=35380,  # Wh per battery
        voltage=48,
        depth_of_discharge=0.8,
        soc_min=0.2,
        soc_max=1.0,
        efficiency=0.85,
        inverter_efficiency=0.95,
        converter_efficiency=0.95,
        autonomy_days=3,
        num_batteries=10
    )
    
    # Example simulation
    time_hours = 24
    energy_available = np.random.normal(2000, 500, time_hours)  # Wh
    energy_demand = np.random.normal(1500, 300, time_hours)     # Wh
    
    results = battery.simulate_operation(energy_available, energy_demand)
    
    print("Battery System Specifications:")
    specs = battery.get_specifications()
    for key, value in specs.items():
        print(f"  {key}: {value}")
    
    print(f"\nFinal SOC: {battery.get_soc():.2f}")
    print(f"Final Energy Stored: {battery.get_energy_stored():.0f} Wh")