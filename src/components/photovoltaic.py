

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

    # ===========================
    # New method to update panel count
    # ===========================
    def set_count(self, num_panels: int):
        """Set the number of PV panels and update total rated power"""
        self.num_panels = num_panels
        self.total_rated_power = self.rated_power * self.num_panels / 1000
    
    # ===========================
    # Cell temperature calculation
    # ===========================
    def calculate_cell_temperature(self, 
                                 ambient_temp: Union[float, np.ndarray], 
                                 solar_irradiance: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate cell temperature using Eq.(3.2)
        
        Tc = Tamb + G(t) × ((NOCT - 20) / 800)
        """
        return ambient_temp + solar_irradiance * ((self.noct - 20) / 800)
    
    # ===========================
    # PV output power calculation
    # ===========================
    def calculate_output_power(self, 
                             solar_irradiance: Union[float, np.ndarray], 
                             ambient_temp: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate PV output power using Eq.(3.1)
        
        Ppv(t) = P(PVrated) × (G(t)/1000) × [1 + αt(Tc - TcSTC)]
        """
        cell_temp = self.calculate_cell_temperature(ambient_temp, solar_irradiance)
        power_per_panel = self.rated_power * (solar_irradiance / self.stc_irradiance) * \
                         (1 + self.temp_coefficient * (cell_temp - self.stc_temperature))
        total_power = (power_per_panel * self.num_panels * self.efficiency) / 1000
        return np.maximum(0, total_power)
    
    # ===========================
    # Yearly simulation
    # ===========================
    def simulate_year(self, weather_data: pd.DataFrame) -> pd.DataFrame:
        results = pd.DataFrame(index=weather_data.index)
        results['cell_temperature'] = self.calculate_cell_temperature(
            weather_data['ambient_temp'].values,
            weather_data['solar_irradiance'].values
        )
        results['pv_power'] = self.calculate_output_power(
            weather_data['solar_irradiance'].values,
            weather_data['ambient_temp'].values
        )
        results['efficiency_factor'] = 1 + self.temp_coefficient * \
                                      (results['cell_temperature'] - self.stc_temperature)
        results['energy_hourly'] = results['pv_power']
        return results
    
    # ===========================
    # Get system specifications
    # ===========================
    def get_specifications(self) -> dict:
        return {
            'num_panels': self.num_panels,
            'rated_power_per_panel': self.rated_power,
            'total_rated_power': self.total_rated_power,
            'temp_coefficient': self.temp_coefficient,
            'noct': self.noct,
            'efficiency': self.efficiency
        }
    
    # ===========================
    # Daily and monthly energy
    # ===========================
    def calculate_daily_energy(self, hourly_power: np.ndarray) -> np.ndarray:
        daily_energy = hourly_power.reshape(-1, 24).sum(axis=1)
        return daily_energy
    
    def calculate_monthly_energy(self, hourly_power: np.ndarray) -> np.ndarray:
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        monthly_energy = []
        start_hour = 0
        for days in days_in_month:
            end_hour = start_hour + days * 24
            monthly_energy.append(hourly_power[start_hour:end_hour].sum())
            start_hour = end_hour
        return np.array(monthly_energy)

# ===========================
# Example usage
# ===========================
if __name__ == "__main__":
    pv_system = PhotovoltaicSystem(
        rated_power=325,
        temp_coefficient=-3.7e-3,
        noct=45,
        efficiency=0.95,
        num_panels=50
    )
    
    solar_irradiance = 800
    ambient_temp = 30
    
    output_power = pv_system.calculate_output_power(solar_irradiance, ambient_temp)
    print(f"PV Output Power: {output_power:.2f} kW")
    
    specs = pv_system.get_specifications()
    print(f"\nPV System Specifications:")
    for key, value in specs.items():
        print(f"  {key}: {value}")
