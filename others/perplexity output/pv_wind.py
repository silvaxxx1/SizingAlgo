import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm
import random

class PVSystem:
    def __init__(self, area, efficiency, derating_factor=0.9):
        self.area = area
        self.efficiency = efficiency
        self.derating_factor = derating_factor
        
    def calculate_power(self, irradiance, ambient_temp):
        # Implementation of Eqs. (3.1) and (3.2)
        power = self.area * irradiance * self.efficiency * self.derating_factor / 1000
        
        # Temperature effect on performance
        temp_coefficient = -0.005
        power = power * (1 + temp_coefficient * (ambient_temp - 25))
        
        return max(0, power)  # Ensure non-negative power output

class WindTurbine:
    def __init__(self, rated_power, cut_in_speed, rated_speed, cut_out_speed):
        self.rated_power = rated_power
        self.cut_in_speed = cut_in_speed
        self.rated_speed = rated_speed
        self.cut_out_speed = cut_out_speed
        
    def calculate_power(self, wind_speed):
        # Implementation of Eqs. (3.3) and (3.4)
        if wind_speed < self.cut_in_speed or wind_speed > self.cut_out_speed:
            return 0
        elif wind_speed < self.rated_speed:
            return self.rated_power * (wind_speed - self.cut_in_speed) / (self.rated_speed - self.cut_in_speed)
        else:
            return self.rated_power
