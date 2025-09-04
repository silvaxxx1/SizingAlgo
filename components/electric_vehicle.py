# electric_vehicle.py
import numpy as np
import pandas as pd
from typing import Union, List, Tuple, Dict

class ElectricVehicle:
    """
    Electric Vehicle (EV) model for V2G integration
    Based on the thesis MATLAB code EV modeling section
    """
    
    def __init__(self, 
                 capacity: float = 24000,  # Wh - Evmax in MATLAB (24kWh or 75kWh)
                 soc_min: float = 0.2,  # Minimum SOC (20%)
                 soc_max: float = 0.95,  # Maximum SOC (95%)
                 charge_rate: float = 7.2,  # kW - C_Rate in MATLAB
                 discharge_rate: float = 7.2,  # kW - D_Rate in MATLAB  
                 efficiency: float = 0.9,  # Charging/discharging efficiency
                 num_vehicles: int = 1):
        """
        Initialize EV system parameters based on MATLAB code
        
        Args:
            capacity: Battery capacity per EV (Wh) - Evmax in MATLAB
            soc_min: Minimum allowed SOC
            soc_max: Maximum allowed SOC  
            charge_rate: Maximum charging rate (kW) - C_Rate in MATLAB
            discharge_rate: Maximum discharging rate (kW) - D_Rate in MATLAB
            efficiency: Round-trip efficiency
            num_vehicles: Number of EVs in fleet
        """
        self.capacity = capacity
        self.soc_min = soc_min
        self.soc_max = soc_max
        self.charge_rate = charge_rate  # kW
        self.discharge_rate = discharge_rate  # kW
        self.efficiency = efficiency
        self.num_vehicles = num_vehicles
        
        # Initialize fleet state
        self.fleet_soc = np.full(num_vehicles, 0.5)  # Start at 50% SOC
        self.fleet_availability = np.ones(num_vehicles, dtype=bool)  # All available initially
        
        # Energy tracking
        self.charge_history = []
        self.discharge_history = []
        self.v2g_energy = []
        self.g2v_energy = []
    
    def set_availability_pattern(self, availability_schedule: np.ndarray):
        """
        Set EV availability pattern based on arrival/departure times
        Based on MATLAB car_av variable
        
        Args:
            availability_schedule: 2D array [time_steps, num_vehicles] 
                                 1 if available, 0 if not available
        """
        if availability_schedule.shape[1] != self.num_vehicles:
            raise ValueError("Availability schedule must match number of vehicles")
        
        self.availability_schedule = availability_schedule
    
    def generate_availability_pattern(self, 
                                    hours: int = 8760,
                                    arrival_mean: float = 18.0,  # 6 PM
                                    arrival_std: float = 2.0,
                                    departure_mean: float = 7.0,  # 7 AM  
                                    departure_std: float = 2.0) -> np.ndarray:
        """
        Generate realistic EV availability pattern
        Based on typical commuter behavior
        
        Args:
            hours: Number of hours to simulate
            arrival_mean: Mean arrival time (hour of day)
            arrival_std: Standard deviation of arrival time
            departure_mean: Mean departure time (hour of day)
            departure_std: Standard deviation of departure time
            
        Returns:
            2D array [hours, num_vehicles] of availability (1=available, 0=not available)
        """
        availability = np.zeros((hours, self.num_vehicles))
        
        for vehicle in range(self.num_vehicles):
            for day in range(hours // 24):
                # Generate arrival and departure times for this day
                arrival_hour = np.random.normal(arrival_mean, arrival_std)
                departure_hour = np.random.normal(departure_mean, departure_std)
                
                # Ensure times are within valid range
                arrival_hour = np.clip(arrival_hour, 0, 23)
                departure_hour = np.clip(departure_hour, 0, 23)
                
                # Handle overnight parking (most common case)
                if departure_hour < arrival_hour:
                    # Available from arrival to midnight
                    start_idx = day * 24 + int(arrival_hour)
                    end_idx = (day + 1) * 24
                    if start_idx < hours and end_idx <= hours:
                        availability[start_idx:end_idx, vehicle] = 1
                    
                    # Available from midnight to departure
                    start_idx = (day + 1) * 24
                    end_idx = (day + 1) * 24 + int(departure_hour)
                    if start_idx < hours and end_idx <= hours:
                        availability[start_idx:end_idx, vehicle] = 1
                else:
                    # Available during the day (less common)
                    start_idx = day * 24 + int(arrival_hour)
                    end_idx = day * 24 + int(departure_hour)
                    if start_idx < hours and end_idx <= hours:
                        availability[start_idx:end_idx, vehicle] = 1
        
        self.availability_schedule = availability
        return availability
    
    def get_available_vehicles(self, time_step: int) -> np.ndarray:
        """Get indices of available vehicles at given time step"""
        if hasattr(self, 'availability_schedule'):
            available_mask = self.availability_schedule[time_step, :] == 1
            return np.where(available_mask)[0]
        else:
            # If no schedule set, assume all vehicles available
            return np.arange(self.num_vehicles)
    
    def get_fleet_capacity(self, time_step: int) -> Dict[str, float]:
        """
        Get total fleet charging/discharging capacity at given time step
        
        Returns:
            Dictionary with charging and discharging capacities (kW)
        """
        available_vehicles = self.get_available_vehicles(time_step)
        
        if len(available_vehicles) == 0:
            return {'charge_capacity': 0.0, 'discharge_capacity': 0.0}
        
        # Calculate available capacities
        available_socs = self.fleet_soc[available_vehicles]
        
        # Charging capacity (limited by max SOC and charge rate)
        charge_capacity = 0.0
        for i, vehicle_idx in enumerate(available_vehicles):
            soc = available_socs[i]
            if soc < self.soc_max:
                max_energy = (self.soc_max - soc) * self.capacity / 1000  # kWh
                max_power = min(self.charge_rate, max_energy)  # kW
                charge_capacity += max_power
        
        # Discharging capacity (limited by min SOC and discharge rate)
        discharge_capacity = 0.0
        for i, vehicle_idx in enumerate(available_vehicles):
            soc = available_socs[i]
            if soc > self.soc_min:
                max_energy = (soc - self.soc_min) * self.capacity / 1000  # kWh
                max_power = min(self.discharge_rate, max_energy)  # kW
                discharge_capacity += max_power
        
        return {
            'charge_capacity': charge_capacity,
            'discharge_capacity': discharge_capacity,
            'available_vehicles': len(available_vehicles)
        }
    
    def charge_fleet(self, 
                    energy_available: float, 
                    time_step: int) -> Tuple[float, float]:
        """
        Charge available EVs with surplus energy
        Based on MATLAB charge_Ev function logic
        
        Args:
            energy_available: Available energy for charging (kWh)
            time_step: Current time step
            
        Returns:
            Tuple of (energy_used, energy_remaining)
        """
        if energy_available <= 0:
            return 0.0, energy_available
        
        available_vehicles = self.get_available_vehicles(time_step)
        if len(available_vehicles) == 0:
            return 0.0, energy_available
        
        energy_used = 0.0
        remaining_energy = energy_available
        
        # Distribute energy among available vehicles
        for vehicle_idx in available_vehicles:
            if remaining_energy <= 0:
                break
            
            current_soc = self.fleet_soc[vehicle_idx]
            if current_soc >= self.soc_max:
                continue  # Vehicle already full
            
            # Calculate maximum energy this vehicle can accept
            max_energy_capacity = (self.soc_max - current_soc) * self.capacity / 1000  # kWh
            max_power_capacity = self.charge_rate  # kW (for 1 hour)
            
            # Actual energy to charge (limited by capacity, power, and available energy)
            energy_to_charge = min(max_energy_capacity, max_power_capacity, remaining_energy)
            energy_to_charge *= self.efficiency  # Apply charging efficiency
            
            # Update vehicle SOC
            energy_stored = energy_to_charge * 1000  # Convert to Wh
            new_soc = current_soc + (energy_stored / self.capacity)
            self.fleet_soc[vehicle_idx] = min(new_soc, self.soc_max)
            
            # Update energy tracking
            energy_used += energy_to_charge
            remaining_energy -= energy_to_charge
        
        self.g2v_energy.append(energy_used)
        return energy_used, remaining_energy
    
    def discharge_fleet(self, 
                       energy_demand: float, 
                       time_step: int) -> Tuple[float, float]:
        """
        Discharge available EVs to meet energy demand (V2G)
        Based on MATLAB discharge EV logic
        
        Args:
            energy_demand: Energy demand to be met (kWh)
            time_step: Current time step
            
        Returns:
            Tuple of (energy_provided, energy_deficit)
        """
        if energy_demand <= 0:
            return 0.0, 0.0
        
        available_vehicles = self.get_available_vehicles(time_step)
        if len(available_vehicles) == 0:
            return 0.0, energy_demand
        
        energy_provided = 0.0
        remaining_demand = energy_demand
        
        # Get energy from available vehicles
        for vehicle_idx in available_vehicles:
            if remaining_demand <= 0:
                break
            
            current_soc = self.fleet_soc[vehicle_idx]
            
            # Check if vehicle SOC is above critical level (from MATLAB: Ev<Evmax*.2)
            critical_soc = self.soc_max * 0.2  # 20% of max SOC
            if current_soc <= critical_soc:
                continue  # Don't discharge below critical level
            
            # Calculate maximum energy this vehicle can provide
            max_energy_capacity = (current_soc - self.soc_min) * self.capacity / 1000  # kWh
            max_power_capacity = self.discharge_rate  # kW (for 1 hour)
            
            # Actual energy to discharge
            energy_to_discharge = min(max_energy_capacity, max_power_capacity, remaining_demand)
            energy_to_discharge *= self.efficiency  # Apply discharging efficiency
            
            # Update vehicle SOC
            energy_removed = energy_to_discharge * 1000  # Convert to Wh
            new_soc = current_soc - (energy_removed / self.capacity)
            self.fleet_soc[vehicle_idx] = max(new_soc, self.soc_min)
            
            # Update energy tracking
            energy_provided += energy_to_discharge
            remaining_demand -= energy_to_discharge
        
        self.v2g_energy.append(energy_provided)
        return energy_provided, remaining_demand
    
    def simulate_daily_driving(self, 
                              vehicle_idx: int = None,
                              energy_consumption: float = None) -> float:
        """
        Simulate daily energy consumption from driving
        
        Args:
            vehicle_idx: Specific vehicle index (if None, applies to all)
            energy_consumption: Energy consumed (kWh), if None uses default
            
        Returns:
            Total energy consumed (kWh)
        """
        if energy_consumption is None:
            # Default daily consumption (30-50 kWh for typical EV)
            energy_consumption = np.random.uniform(8, 15)  # kWh
        
        if vehicle_idx is None:
            # Apply to all vehicles
            for i in range(self.num_vehicles):
                energy_wh = energy_consumption * 1000  # Convert to Wh
                new_soc = self.fleet_soc[i] - (energy_wh / self.capacity)
                self.fleet_soc[i] = max(new_soc, 0.0)  # Don't go below 0%
            total_consumption = energy_consumption * self.num_vehicles
        else:
            # Apply to specific vehicle
            energy_wh = energy_consumption * 1000
            new_soc = self.fleet_soc[vehicle_idx] - (energy_wh / self.capacity)
            self.fleet_soc[vehicle_idx] = max(new_soc, 0.0)
            total_consumption = energy_consumption
        
        return total_consumption
    
    def get_fleet_statistics(self) -> Dict[str, float]:
        """Get current fleet statistics"""
        return {
            'mean_soc': np.mean(self.fleet_soc),
            'min_soc': np.min(self.fleet_soc),
            'max_soc': np.max(self.fleet_soc),
            'total_energy_stored': np.sum(self.fleet_soc) * self.capacity * self.num_vehicles / 1000,  # kWh
            'vehicles_below_critical': np.sum(self.fleet_soc < (self.soc_max * 0.2)),
            'vehicles_fully_charged': np.sum(self.fleet_soc >= self.soc_max)
        }
    
    def reset_fleet_state(self, initial_soc: Union[float, np.ndarray] = 0.5):
        """Reset fleet to initial state"""
        if isinstance(initial_soc, float):
            self.fleet_soc = np.full(self.num_vehicles, initial_soc)
        else:
            if len(initial_soc) != self.num_vehicles:
                raise ValueError("Initial SOC array must match number of vehicles")
            self.fleet_soc = initial_soc.copy()
        
        # Reset tracking arrays
        self.charge_history = []
        self.discharge_history = []
        self.v2g_energy = []
        self.g2v_energy = []
    
    def get_specifications(self) -> Dict[str, Union[float, int]]:
        """Get EV fleet specifications"""
        return {
            'num_vehicles': self.num_vehicles,
            'capacity_per_vehicle': self.capacity,
            'total_fleet_capacity': self.capacity * self.num_vehicles,
            'soc_min': self.soc_min,
            'soc_max': self.soc_max,
            'charge_rate': self.charge_rate,
            'discharge_rate': self.discharge_rate,
            'efficiency': self.efficiency,
            'total_charge_power': self.charge_rate * self.num_vehicles,
            'total_discharge_power': self.discharge_rate * self.num_vehicles
        }
    
    def calculate_v2g_potential(self, time_steps: int) -> pd.DataFrame:
        """Calculate V2G potential over time based on availability"""
        if not hasattr(self, 'availability_schedule'):
            raise ValueError("Availability schedule must be set first")
        
        results = []
        
        for t in range(min(time_steps, len(self.availability_schedule))):
            fleet_capacity = self.get_fleet_capacity(t)
            fleet_stats = self.get_fleet_statistics()
            
            results.append({
                'time_step': t,
                'available_vehicles': fleet_capacity['available_vehicles'],
                'charge_capacity_kw': fleet_capacity['charge_capacity'],
                'discharge_capacity_kw': fleet_capacity['discharge_capacity'],
                'fleet_energy_stored_kwh': fleet_stats['total_energy_stored'],
                'mean_soc': fleet_stats['mean_soc']
            })
        
        return pd.DataFrame(results)


# Example usage
if __name__ == "__main__":
    # Create EV fleet with MATLAB-based parameters
    ev_fleet = ElectricVehicle(
        capacity=24000,  # 24 kWh per vehicle (Evmax in MATLAB)
        soc_min=0.2,
        soc_max=0.95,
        charge_rate=7.2,  # C_Rate in MATLAB
        discharge_rate=7.2,  # D_Rate in MATLAB
        efficiency=0.9,
        num_vehicles=30
    )
    
    # Generate availability pattern
    availability = ev_fleet.generate_availability_pattern(
        hours=168,  # One week
        arrival_mean=18.0,  # 6 PM
        departure_mean=7.0   # 7 AM
    )
    
    # Get specifications
    specs = ev_fleet.get_specifications()
    print("EV Fleet Specifications:")
    for key, value in specs.items():
        print(f"  {key}: {value}")
    
    # Test charging
    energy_used, remaining = ev_fleet.charge_fleet(50.0, 0)  # 50 kWh available at time 0
    print(f"\nCharge test: Used {energy_used:.2f} kWh, Remaining {remaining:.2f} kWh")
    
    # Get fleet statistics
    stats = ev_fleet.get_fleet_statistics()
    print("\nFleet Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value:.3f}")
    
    # Calculate V2G potential
    v2g_potential = ev_fleet.calculate_v2g_potential(24)  # First 24 hours
    print(f"\nV2G Potential calculated for {len(v2g_potential)} time steps")