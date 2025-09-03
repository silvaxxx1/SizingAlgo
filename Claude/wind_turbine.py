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
        
        Args:
            rated_power: Rated power per turbine (W)
            cut_in_speed: Cut-in wind speed (m/s)
            cut_out_speed: Cut-out wind speed (m/s)
            rated_speed: Rated wind speed (m/s)
            hub_height: Hub height (m)
            efficiency: System efficiency
            num_turbines: Number of wind turbines
        """
        self.rated_power = rated_power
        self.cut_in_speed = cut_in_speed
        self.cut_out_speed = cut_out_speed
        self.rated_speed = rated_speed
        self.hub_height = hub_height
        self.efficiency = efficiency
        self.num_turbines = num_turbines
        self.total_rated_power = rated_power * num_turbines / 1000  # Convert to kW
    
    def adjust_wind_speed_for_height(self, 
                                   wind_speed: Union[float, np.ndarray], 
                                   reference_height: float = 43.6) -> Union[float, np.ndarray]:
        """
        Adjust wind speed from reference height to hub height using power law
        Based on MATLAB code: V2=V1*(h2/h1)^(alfa)
        
        Args:
            wind_speed: Wind speed at reference height (m/s) - V1 in MATLAB
            reference_height: Reference height (m) - h1 in MATLAB (43.6m)
        
        Returns:
            Wind speed at hub height (m/s) - V2 in MATLAB
        """
        alpha = 0.25  # For heavily forested landscape (from MATLAB: alfa=0.25)
        return wind_speed * (self.hub_height / reference_height) ** alpha
    
    def calculate_output_power(self, wind_speed: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate wind turbine output power using Eq.(3.3)
        
        Pwt(t) = {
            0,                                           if v < vci or v ≥ vco
            Prated × (v - vci)/(vr - vci),              if vci ≤ v < vr
            Prated,                                      if vr ≤ v < vco
        }
        
        Args:
            wind_speed: Wind speed at hub height (m/s)
            
        Returns:
            Wind turbine output power (kW)
        """
        # Initialize output power array
        if isinstance(wind_speed, np.ndarray):
            power_per_turbine = np.zeros_like(wind_speed)
        else:
            power_per_turbine = 0.0
        
        # Apply piecewise linear power curve
        if isinstance(wind_speed, np.ndarray):
            # Region 1: Below cut-in or above cut-out (power = 0)
            mask1 = (wind_speed < self.cut_in_speed) | (wind_speed >= self.cut_out_speed)
            power_per_turbine[mask1] = 0
            
            # Region 2: Between cut-in and rated speed (linear increase)
            mask2 = (wind_speed >= self.cut_in_speed) & (wind_speed < self.rated_speed)
            power_per_turbine[mask2] = self.rated_power * \
                                      (wind_speed[mask2] - self.cut_in_speed) / \
                                      (self.rated_speed - self.cut_in_speed)
            
            # Region 3: Between rated and cut-out speed (constant rated power)
            mask3 = (wind_speed >= self.rated_speed) & (wind_speed < self.cut_out_speed)
            power_per_turbine[mask3] = self.rated_power
        else:
            # Single value calculation
            if wind_speed < self.cut_in_speed or wind_speed >= self.cut_out_speed:
                power_per_turbine = 0
            elif self.cut_in_speed <= wind_speed < self.rated_speed:
                power_per_turbine = self.rated_power * \
                                  (wind_speed - self.cut_in_speed) / \
                                  (self.rated_speed - self.cut_in_speed)
            else:  # rated_speed <= wind_speed < cut_out_speed
                power_per_turbine = self.rated_power
        
        # Apply efficiency and convert to kW
        total_power = (power_per_turbine * self.num_turbines * self.efficiency) / 1000
        
        return np.maximum(0, total_power)
    
    def simulate_year(self, weather_data: pd.DataFrame) -> pd.DataFrame:
        """
        Simulate wind turbine output for a full year
        
        Args:
            weather_data: DataFrame with column 'wind_speed'
            
        Returns:
            DataFrame with wind turbine output power and related parameters
        """
        results = pd.DataFrame(index=weather_data.index)
        
        # Adjust wind speed for hub height
        results['wind_speed_hub'] = self.adjust_wind_speed_for_height(
            weather_data['wind_speed'].values
        )
        
        # Calculate output power
        results['wt_power'] = self.calculate_output_power(
            results['wind_speed_hub'].values
        )
        
        # Add additional metrics
        results['capacity_factor'] = results['wt_power'] / self.total_rated_power
        results['energy_hourly'] = results['wt_power']  # kWh (assuming hourly data)
        
        return results
    
    def calculate_capacity_factor(self, wind_speed_data: np.ndarray) -> float:
        """Calculate annual capacity factor"""
        hub_wind_speed = self.adjust_wind_speed_for_height(wind_speed_data)
        power_output = self.calculate_output_power(hub_wind_speed)
        capacity_factor = np.mean(power_output) / self.total_rated_power
        return capacity_factor
    
    def get_specifications(self) -> dict:
        """Get wind turbine specifications"""
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
        """Generate power curve for plotting"""
        return self.calculate_output_power(wind_speeds)
    
    def calculate_wind_statistics(self, wind_speed_data: np.ndarray) -> dict:
        """Calculate wind resource statistics"""
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

# Example usage 
if __name__ == "__main__":
    # Create a wind turbine
    wind_turbine = WindTurbine(
        rated_power=5000,  # W per turbine
        cut_in_speed=2.8,  # m/s
        cut_out_speed=20,  # m/s
        rated_speed=7.5,  # m/s
        hub_height=50,  # m
        efficiency=0.95,  # System efficiency
        num_turbines=1
    )
    
    # Example calculation for a single hour
    wind_speed = 10  # m/s
    output_power = wind_turbine.calculate_output_power(wind_speed)
    print(f"Wind Turbine Output Power: {output_power:.2f} kW")
    
    # Get specifications
    specs = wind_turbine.get_specifications()
    print(f"\nWind Turbine Specifications:")
    for key, value in specs.items():
        print(f"  {key}: {value}")

    import matplotlib.pyplot as plt
    # Plot power curve
    wind_speeds = np.linspace(0, 25, 100)
    power_curve = wind_turbine.calculate_power_curve(wind_speeds)
    plt.plot(wind_speeds, power_curve)
    plt.xlabel('Wind Speed (m/s)')
    plt.ylabel('Power (kW)')
    plt.title('Wind Turbine Power Curve')
    plt.show()