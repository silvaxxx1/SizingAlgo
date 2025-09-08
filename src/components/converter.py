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



# ================================
# Example usage for quick testing
# ================================
if __name__ == "__main__":
    # Create a converter instance
    converter = Converter()

    print("=== Converter Specifications ===")
    print(converter.get_specifications())
    print()

    # Example scenarios
    scenarios = [
        {"input_power": 3000, "direction": "boost", "description": "Normal boost conversion"},
        {"input_power": 3000, "direction": "buck", "description": "Normal buck conversion"},
        {"input_power": 6000, "direction": "boost", "description": "Exceeding rated power (limit check)"},
        {"input_power": 0, "direction": "boost", "description": "Zero power input"},
        {"input_power": -500, "direction": "buck", "description": "Negative power input (invalid case)"},
    ]

    for case in scenarios:
        input_power = case["input_power"]
        direction = case["direction"]
        description = case["description"]

        output_power = converter.convert_power(input_power, direction=direction)
        print(f"{description}:")
        print(f"  Input Power: {input_power} W | Direction: {direction}")
        print(f"  Output Power: {output_power:.2f} W")
        print("-" * 50)

    # Extra example: simulate random power inputs
    print("\n=== Random Power Simulation ===")
    np.random.seed(42)
    random_inputs = np.random.randint(-1000, 7000, size=5)  # some negative, some above rated

    for i, p in enumerate(random_inputs, start=1):
        out_boost = converter.convert_power(p, direction="boost")
        out_buck = converter.convert_power(p, direction="buck")
        print(f"Test {i}: Input = {p} W")
        print(f"  Boost Output: {out_boost:.2f} W")
        print(f"  Buck Output: {out_buck:.2f} W")
        print("-" * 30)