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
        self.capacity = capacity
        self.soc_min = soc_min
        self.soc_max = soc_max
        self.charge_rate = charge_rate
        self.discharge_rate = discharge_rate
        self.efficiency = efficiency
        self.num_vehicles = num_vehicles
        
        self.fleet_soc = np.full(num_vehicles, 0.5)  # Start at 50% SOC
        self.fleet_availability = np.ones(num_vehicles, dtype=bool)
        
        self.charge_history = []
        self.discharge_history = []
        self.v2g_energy = []
        self.g2v_energy = []
    
    def set_availability_pattern(self, availability_schedule: np.ndarray):
        if availability_schedule.shape[1] != self.num_vehicles:
            raise ValueError("Availability schedule must match number of vehicles")
        self.availability_schedule = availability_schedule
    
    def generate_availability_pattern(self, 
                                      hours: int = 8760,
                                      arrival_mean: float = 18.0,
                                      arrival_std: float = 2.0,
                                      departure_mean: float = 7.0,
                                      departure_std: float = 2.0) -> np.ndarray:
        availability = np.zeros((hours, self.num_vehicles))
        
        for vehicle in range(self.num_vehicles):
            for day in range(hours // 24):
                arrival_hour = np.clip(np.random.normal(arrival_mean, arrival_std), 0, 23)
                departure_hour = np.clip(np.random.normal(departure_mean, departure_std), 0, 23)
                
                if departure_hour < arrival_hour:
                    start_idx = day * 24 + int(arrival_hour)
                    end_idx = (day + 1) * 24
                    if start_idx < hours and end_idx <= hours:
                        availability[start_idx:end_idx, vehicle] = 1
                    start_idx = (day + 1) * 24
                    end_idx = (day + 1) * 24 + int(departure_hour)
                    if start_idx < hours and end_idx <= hours:
                        availability[start_idx:end_idx, vehicle] = 1
                else:
                    start_idx = day * 24 + int(arrival_hour)
                    end_idx = day * 24 + int(departure_hour)
                    if start_idx < hours and end_idx <= hours:
                        availability[start_idx:end_idx, vehicle] = 1
        
        self.availability_schedule = availability
        return availability
    
    def get_available_vehicles(self, time_step: int) -> np.ndarray:
        if hasattr(self, 'availability_schedule'):
            available_mask = self.availability_schedule[time_step, :] == 1
            return np.where(available_mask)[0]
        else:
            return np.arange(self.num_vehicles)
    
    def get_fleet_capacity(self, time_step: int) -> Dict[str, float]:
        available_vehicles = self.get_available_vehicles(time_step)
        
        # FIX: Always include 'available_vehicles' key
        if len(available_vehicles) == 0:
            return {'charge_capacity': 0.0, 'discharge_capacity': 0.0, 'available_vehicles': 0}
        
        available_socs = self.fleet_soc[available_vehicles]
        
        charge_capacity = 0.0
        for i, soc in enumerate(available_socs):
            if soc < self.soc_max:
                max_energy = (self.soc_max - soc) * self.capacity / 1000
                max_power = min(self.charge_rate, max_energy)
                charge_capacity += max_power
        
        discharge_capacity = 0.0
        for i, soc in enumerate(available_socs):
            if soc > self.soc_min:
                max_energy = (soc - self.soc_min) * self.capacity / 1000
                max_power = min(self.discharge_rate, max_energy)
                discharge_capacity += max_power
        
        return {
            'charge_capacity': charge_capacity,
            'discharge_capacity': discharge_capacity,
            'available_vehicles': len(available_vehicles)
        }
    
    def charge_fleet(self, energy_available: float, time_step: int) -> Tuple[float, float]:
        if energy_available <= 0:
            return 0.0, energy_available
        
        available_vehicles = self.get_available_vehicles(time_step)
        if len(available_vehicles) == 0:
            return 0.0, energy_available
        
        energy_used = 0.0
        remaining_energy = energy_available
        
        for vehicle_idx in available_vehicles:
            if remaining_energy <= 0:
                break
            current_soc = self.fleet_soc[vehicle_idx]
            if current_soc >= self.soc_max:
                continue
            
            max_energy_capacity = (self.soc_max - current_soc) * self.capacity / 1000
            max_power_capacity = self.charge_rate
            energy_to_charge = min(max_energy_capacity, max_power_capacity, remaining_energy)
            energy_to_charge *= self.efficiency
            
            energy_stored = energy_to_charge * 1000
            new_soc = current_soc + (energy_stored / self.capacity)
            self.fleet_soc[vehicle_idx] = min(new_soc, self.soc_max)
            
            energy_used += energy_to_charge
            remaining_energy -= energy_to_charge
        
        self.g2v_energy.append(energy_used)
        return energy_used, remaining_energy
    
    def discharge_fleet(self, energy_demand: float, time_step: int) -> Tuple[float, float]:
        if energy_demand <= 0:
            return 0.0, 0.0
        
        available_vehicles = self.get_available_vehicles(time_step)
        if len(available_vehicles) == 0:
            return 0.0, energy_demand
        
        energy_provided = 0.0
        remaining_demand = energy_demand
        
        for vehicle_idx in available_vehicles:
            if remaining_demand <= 0:
                break
            current_soc = self.fleet_soc[vehicle_idx]
            critical_soc = self.soc_max * 0.2
            if current_soc <= critical_soc:
                continue
            
            max_energy_capacity = (current_soc - self.soc_min) * self.capacity / 1000
            max_power_capacity = self.discharge_rate
            energy_to_discharge = min(max_energy_capacity, max_power_capacity, remaining_demand)
            energy_to_discharge *= self.efficiency
            
            energy_removed = energy_to_discharge * 1000
            new_soc = current_soc - (energy_removed / self.capacity)
            self.fleet_soc[vehicle_idx] = max(new_soc, self.soc_min)
            
            energy_provided += energy_to_discharge
            remaining_demand -= energy_to_discharge
        
        self.v2g_energy.append(energy_provided)
        return energy_provided, remaining_demand
    
    def get_fleet_statistics(self) -> Dict[str, float]:
        return {
            'mean_soc': np.mean(self.fleet_soc),
            'min_soc': np.min(self.fleet_soc),
            'max_soc': np.max(self.fleet_soc),
            'total_energy_stored': np.sum(self.fleet_soc) * self.capacity / 1000,
            'vehicles_below_critical': np.sum(self.fleet_soc < (self.soc_max * 0.2)),
            'vehicles_fully_charged': np.sum(self.fleet_soc >= self.soc_max)
        }
    
    def reset_fleet_state(self, initial_soc: Union[float, np.ndarray] = 0.5):
        if isinstance(initial_soc, float):
            self.fleet_soc = np.full(self.num_vehicles, initial_soc)
        else:
            if len(initial_soc) != self.num_vehicles:
                raise ValueError("Initial SOC array must match number of vehicles")
            self.fleet_soc = initial_soc.copy()
        self.charge_history = []
        self.discharge_history = []
        self.v2g_energy = []
        self.g2v_energy = []
    
    def set_count(self, num_vehicles: int):
        """
        Update number of vehicles (for optimization)
        """
        old_soc = self.fleet_soc.copy()
        self.num_vehicles = num_vehicles
        # Reset fleet SOC array with old SOC where possible
        if len(old_soc) >= num_vehicles:
            self.fleet_soc = old_soc[:num_vehicles]
        else:
            # Fill new vehicles with initial 50% SOC
            self.fleet_soc = np.concatenate([old_soc, np.full(num_vehicles - len(old_soc), 0.5)])
        
        # Reset availability if already set
        if hasattr(self, 'availability_schedule'):
            hours = self.availability_schedule.shape[0]
            if self.availability_schedule.shape[1] >= num_vehicles:
                self.availability_schedule = self.availability_schedule[:, :num_vehicles]
            else:
                extra_columns = np.ones((hours, num_vehicles - self.availability_schedule.shape[1]))
                self.availability_schedule = np.hstack([self.availability_schedule, extra_columns])


    def get_specifications(self) -> Dict[str, Union[float, int]]:
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
    ev_fleet = ElectricVehicle(capacity=24000, soc_min=0.2, soc_max=0.95,
                               charge_rate=7.2, discharge_rate=7.2, efficiency=0.9,
                               num_vehicles=30)
    
    availability = ev_fleet.generate_availability_pattern(hours=168, arrival_mean=18.0, departure_mean=7.0)
    
    specs = ev_fleet.get_specifications()
    print("EV Fleet Specifications:")
    for key, value in specs.items():
        print(f"  {key}: {value}")
    
    energy_used, remaining = ev_fleet.charge_fleet(50.0, 0)
    print(f"\nCharge test: Used {energy_used:.2f} kWh, Remaining {remaining:.2f} kWh")
    
    stats = ev_fleet.get_fleet_statistics()
    print("\nFleet Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value:.3f}")
    
    v2g_potential = ev_fleet.calculate_v2g_potential(24)
    print(f"\nV2G Potential calculated for {len(v2g_potential)} time steps")
