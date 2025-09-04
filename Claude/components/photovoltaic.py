# photovoltaic.py
import numpy as np
import pandas as pd
from typing import Union, List

class PhotovoltaicSystem:
    """
    Photovoltaic (PV) system model based on the equations from Chapter 3
    Implements Eq.(3.1) and Eq.(3.2) from the thesis
    """
    
    def __init__(self, 
                 rated_power: float = 325,  # W per panel
                 temp_coefficient: float = -3.7e-3,  # 1/°C
                 noct: float = 45,  # °C
                 efficiency: float = 0.95,  # Inverter efficiency
                 num_panels: int = 1):
        """
        Initialize PV system parameters
        
        Args:
            rated_power: Rated power per panel at STC (W)
            temp_coefficient: Temperature coefficient (1/°C)
            noct: Nominal Operating Cell Temperature (°C)
            efficiency: System efficiency including inverter
            num_panels: Number of PV panels
        """
        self.rated_power = rated_power
        self.temp_coefficient = temp_coefficient
        self.noct = noct
        self.efficiency = efficiency
        self.num_panels = num_panels
        self.total_rated_power = rated_power * num_panels / 1000  # Convert to kW
        
        # Standard Test Conditions
        self.stc_irradiance = 1000  # W/m²
        self.stc_temperature = 25  # °C
        
    def calculate_cell_temperature(self, 
                                 ambient_temp: Union[float, np.ndarray], 
                                 solar_irradiance: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate cell temperature using Eq.(3.2)
        
        Tc = Tamb + G(t) × ((NOCT - 20) / 800)
        """
        return ambient_temp + solar_irradiance * ((self.noct - 20) / 800)
    
    def calculate_output_power(self, 
                             solar_irradiance: Union[float, np.ndarray], 
                             ambient_temp: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate PV output power using Eq.(3.1)
        
        Ppv(t) = P(PVrated) × (G(t)/1000) × [1 + αt(Tc - TcSTC)]
        
        Args:
            solar_irradiance: Solar irradiance (W/m²)
            ambient_temp: Ambient temperature (°C)
            
        Returns:
            PV output power (kW)
        """
        # Calculate cell temperature
        cell_temp = self.calculate_cell_temperature(ambient_temp, solar_irradiance)
        
        # Calculate output power per panel
        power_per_panel = self.rated_power * (solar_irradiance / self.stc_irradiance) * \
                         (1 + self.temp_coefficient * (cell_temp - self.stc_temperature))
        
        # Apply efficiency and convert to kW
        total_power = (power_per_panel * self.num_panels * self.efficiency) / 1000
        
        # Ensure non-negative power
        return np.maximum(0, total_power)
    
    def simulate_year(self, weather_data: pd.DataFrame) -> pd.DataFrame:
        """
        Simulate PV output for a full year (8760 hours)
        
        Args:
            weather_data: DataFrame with columns 'solar_irradiance' and 'ambient_temp'
            
        Returns:
            DataFrame with PV output power and related parameters
        """
        results = pd.DataFrame(index=weather_data.index)
        
        # Calculate cell temperature
        results['cell_temperature'] = self.calculate_cell_temperature(
            weather_data['ambient_temp'].values,
            weather_data['solar_irradiance'].values
        )
        
        # Calculate output power
        results['pv_power'] = self.calculate_output_power(
            weather_data['solar_irradiance'].values,
            weather_data['ambient_temp'].values
        )
        
        # Add additional metrics
        results['efficiency_factor'] = 1 + self.temp_coefficient * \
                                      (results['cell_temperature'] - self.stc_temperature)
        results['energy_hourly'] = results['pv_power']  # kWh (assuming hourly data)
        
        return results
    
    def get_specifications(self) -> dict:
        """Get PV system specifications"""
        return {
            'num_panels': self.num_panels,
            'rated_power_per_panel': self.rated_power,
            'total_rated_power': self.total_rated_power,
            'temp_coefficient': self.temp_coefficient,
            'noct': self.noct,
            'efficiency': self.efficiency
        }
    
    def calculate_daily_energy(self, hourly_power: np.ndarray) -> np.ndarray:
        """Calculate daily energy production from hourly power data"""
        # Reshape to (365, 24) and sum along hours
        daily_energy = hourly_power.reshape(-1, 24).sum(axis=1)
        return daily_energy
    
    def calculate_monthly_energy(self, hourly_power: np.ndarray) -> np.ndarray:
        """Calculate monthly energy production"""
        # Days in each month (non-leap year)
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        monthly_energy = []
        
        start_hour = 0
        for days in days_in_month:
            end_hour = start_hour + days * 24
            monthly_energy.append(hourly_power[start_hour:end_hour].sum())
            start_hour = end_hour
            
        return np.array(monthly_energy)


# Example usage
if __name__ == "__main__":
    # Create a PV system with 50 panels
    pv_system = PhotovoltaicSystem(
        rated_power=325,  # W per panel
        temp_coefficient=-3.7e-3,
        noct=45,
        efficiency=0.95,
        num_panels=50
    )
    
    # Example calculation for a single hour
    solar_irradiance = 800  # W/m²
    ambient_temp = 30  # °C
    
    output_power = pv_system.calculate_output_power(solar_irradiance, ambient_temp)
    print(f"PV Output Power: {output_power:.2f} kW")
    
    # Get specifications
    specs = pv_system.get_specifications()
    print(f"\nPV System Specifications:")
    for key, value in specs.items():
        print(f"  {key}: {value}")