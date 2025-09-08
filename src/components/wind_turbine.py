# wind_turbine.py
import numpy as np
import pandas as pd
from typing import Union, List

class WindTurbine:
    """
    Wind Turbine (WT) system model based on Eq.(3.3) from the thesis
    Implements the piecewise linear power curve model
    """
    
    def __init__(self, 
                 rated_power: float = 5000,  # W per turbine
                 cut_in_speed: float = 2.8,  # m/s
                 cut_out_speed: float = 20,  # m/s
                 rated_speed: float = 7.5,  # m/s
                 hub_height: float = 50,  # m
                 efficiency: float = 0.95,  # System efficiency
                 num_turbines: int = 1):
        """
        Initialize wind turbine parameters
        """
        self.rated_power = rated_power
        self.cut_in_speed = cut_in_speed
        self.cut_out_speed = cut_out_speed
        self.rated_speed = rated_speed
        self.hub_height = hub_height
        self.efficiency = efficiency
        self.num_turbines = num_turbines
        self.total_rated_power = rated_power * num_turbines / 1000  # kW
    
    # ===========================
    # Add this method for optimization
    # ===========================
    def set_count(self, num_turbines: int):
        """Set number of turbines dynamically and update total rated power"""
        self.num_turbines = num_turbines
        self.total_rated_power = self.rated_power * self.num_turbines / 1000

    # ===========================
    # Existing methods
    # ===========================
    def adjust_wind_speed_for_height(self, wind_speed: Union[float, np.ndarray], reference_height: float = 43.6) -> Union[float, np.ndarray]:
        alpha = 0.25
        return wind_speed * (self.hub_height / reference_height) ** alpha
    
    def calculate_output_power(self, wind_speed: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        if isinstance(wind_speed, np.ndarray):
            power_per_turbine = np.zeros_like(wind_speed)
            mask1 = (wind_speed < self.cut_in_speed) | (wind_speed >= self.cut_out_speed)
            power_per_turbine[mask1] = 0
            mask2 = (wind_speed >= self.cut_in_speed) & (wind_speed < self.rated_speed)
            power_per_turbine[mask2] = self.rated_power * (wind_speed[mask2] - self.cut_in_speed) / (self.rated_speed - self.cut_in_speed)
            mask3 = (wind_speed >= self.rated_speed) & (wind_speed < self.cut_out_speed)
            power_per_turbine[mask3] = self.rated_power
        else:
            if wind_speed < self.cut_in_speed or wind_speed >= self.cut_out_speed:
                power_per_turbine = 0
            elif self.cut_in_speed <= wind_speed < self.rated_speed:
                power_per_turbine = self.rated_power * (wind_speed - self.cut_in_speed) / (self.rated_speed - self.cut_in_speed)
            else:
                power_per_turbine = self.rated_power
        
        total_power = (power_per_turbine * self.num_turbines * self.efficiency) / 1000
        return np.maximum(0, total_power)
    
    def simulate_year(self, weather_data: pd.DataFrame) -> pd.DataFrame:
        results = pd.DataFrame(index=weather_data.index)
        results['wind_speed_hub'] = self.adjust_wind_speed_for_height(weather_data['wind_speed'].values)
        results['wt_power'] = self.calculate_output_power(results['wind_speed_hub'].values)
        results['capacity_factor'] = results['wt_power'] / self.total_rated_power
        results['energy_hourly'] = results['wt_power']
        return results
    
    def calculate_capacity_factor(self, wind_speed_data: np.ndarray) -> float:
        hub_wind_speed = self.adjust_wind_speed_for_height(wind_speed_data)
        power_output = self.calculate_output_power(hub_wind_speed)
        return np.mean(power_output) / self.total_rated_power
    
    def get_specifications(self) -> dict:
        return {
            'num_turbines': self.num_turbines,
            'rated_power_per_turbine': self.rated_power,
            'total_rated_power': self.total_rated_power,
            'cut_in_speed': self.cut_in_speed,
            'cut_out_speed': self.cut_out_speed,
            'rated_speed': self.rated_speed,
            'hub_height': self.hub_height,
            'efficiency': self.efficiency
        }
    
    def calculate_power_curve(self, wind_speeds: np.ndarray) -> np.ndarray:
        return self.calculate_output_power(wind_speeds)
    
    def calculate_wind_statistics(self, wind_speed_data: np.ndarray) -> dict:
        hub_wind_speed = self.adjust_wind_speed_for_height(wind_speed_data)
        return {
            'mean_wind_speed': np.mean(hub_wind_speed),
            'std_wind_speed': np.std(hub_wind_speed),
            'max_wind_speed': np.max(hub_wind_speed),
            'min_wind_speed': np.min(hub_wind_speed),
            'hours_above_cut_in': np.sum(hub_wind_speed >= self.cut_in_speed),
            'hours_above_rated': np.sum(hub_wind_speed >= self.rated_speed),
            'hours_above_cut_out': np.sum(hub_wind_speed >= self.cut_out_speed)
        }

# ===========================
# Example usage
# ===========================
if __name__ == "__main__":
    wind_turbine = WindTurbine(num_turbines=1)
    wind_speed = 10
    output_power = wind_turbine.calculate_output_power(wind_speed)
    print(f"Wind Turbine Output Power: {output_power:.2f} kW")
    specs = wind_turbine.get_specifications()
    print("\nWind Turbine Specifications:")
    for key, value in specs.items():
        print(f"  {key}: {value}")
