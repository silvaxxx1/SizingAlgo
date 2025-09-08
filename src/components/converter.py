# components/converter.py
import numpy as np
from typing import Union

class Converter:
    """
    DC-DC Converter model for microgrid power electronics
    Based on MATLAB converter efficiency parameters
    """
    
    def __init__(self, 
                 rated_power: float = 5000,  # W
                 efficiency: float = 0.95,   # uconv in MATLAB
                 input_voltage: float = 48,  # V
                 output_voltage: float = 400): # V
        
        self.rated_power = rated_power
        self.efficiency = efficiency
        self.input_voltage = input_voltage
        self.output_voltage = output_voltage
        
    def convert_power(self, input_power: float, direction: str = 'boost') -> float:
        """
        Convert power with efficiency losses
        
        Args:
            input_power: Input power (W)
            direction: 'boost' or 'buck' conversion
            
        Returns:
            Output power after efficiency losses (W)
        """
        if input_power <= 0:
            return 0.0
        
        # Apply power rating limit
        limited_power = min(input_power, self.rated_power)
        
        # Apply efficiency
        if direction == 'boost':
            return limited_power * self.efficiency
        else:  # buck
            return limited_power * self.efficiency
    
    def get_specifications(self) -> dict:
        return {
            'rated_power': self.rated_power,
            'efficiency': self.efficiency,
            'input_voltage': self.input_voltage,
            'output_voltage': self.output_voltage
        }

