# utils/constants.py
"""
Constants and physical parameters for V2G microgrid optimization
Based on MATLAB code parameters and physical constants
"""

# Physical constants
STANDARD_TEST_CONDITIONS = {
    'irradiance': 1000,  # W/m² (Gref in MATLAB)
    'temperature': 25,   # °C (Tref in MATLAB)
    'air_mass': 1.5     # Standard air mass
}

# PV system parameters (from MATLAB)
PV_PARAMETERS = {
    'temp_coefficient': -3.7e-3,  # 1/°C (kt in MATLAB)
    'noct': 45,                   # °C (NOCT in MATLAB)
    'reference_efficiency': 0.15, # Typical silicon PV efficiency
    'system_losses': 0.14        # System losses (inverter, wiring, etc.)
}

# Wind turbine parameters (from MATLAB)
WIND_PARAMETERS = {
    'power_law_exponent': 0.25,   # alfa in MATLAB (heavily forested)
    'cut_in_speed': 2.5,          # m/s (vin in MATLAB)
    'rated_speed': 9.5,           # m/s (vr in MATLAB)  
    'cut_out_speed': 40,          # m/s (vcut in MATLAB)
    'air_density': 1.225         # kg/m³ at sea level
}

# Battery parameters (from MATLAB)
BATTERY_PARAMETERS = {
    'nominal_voltage': 48,        # V (Vs in MATLAB)
    'depth_of_discharge': 0.8,    # dod in MATLAB
    'round_trip_efficiency': 0.85, # n_bat in MATLAB
    'self_discharge_rate': 0.05,  # %/month
    'cycle_life': 5000,          # cycles at rated DOD
    'temperature_coefficient': -0.5 # %/°C
}

# EV parameters (from MATLAB)
EV_PARAMETERS = {
    'battery_capacity': 24000,    # Wh (Evmax in MATLAB - 24kWh option)
    'charge_rate': 7.2,          # kW (C_Rate in MATLAB)
    'discharge_rate': 7.2,       # kW (D_Rate in MATLAB)
    'charging_efficiency': 0.9,   # Bidirectional charging efficiency
    'critical_soc': 0.2,         # Critical SOC threshold
    'energy_consumption': 0.2    # kWh/km average consumption
}

# Economic parameters (from MATLAB)
ECONOMIC_PARAMETERS = {
    'interest_rate': 0.03,        # Real interest rate (REAL_INTREST/100)
    'project_lifetime': 20,       # Years
    'grid_buy_price': 0.023,     # $/kWh (Grid_p in MATLAB)
    'grid_sell_price': 0.015,    # $/kWh (Grid_sale in MATLAB)
    'inflation_rate': 0.025,     # Annual inflation
    'discount_rate': 0.05        # Discount rate for NPV
}

# Power electronics parameters
POWER_ELECTRONICS = {
    'inverter_efficiency': 0.95,  # uinv in MATLAB
    'converter_efficiency': 0.95, # uconv in MATLAB
    'mppt_efficiency': 0.98,     # Maximum power point tracking
    'transformer_efficiency': 0.98
}

# System reliability parameters
RELIABILITY_PARAMETERS = {
    'lpsp_target': 0.01,         # Maximum acceptable LPSP (1%)
    'ref_minimum': 0.5,          # Minimum renewable energy fraction
    'availability_target': 0.95, # System availability target
    'maintenance_hours': 48      # Annual maintenance hours
}

# Weather and location parameters (Tripoli, Libya)
LOCATION_PARAMETERS = {
    'latitude': 32.8872,
    'longitude': 13.1913,
    'altitude': 81,              # meters above sea level
    'timezone': 2,               # UTC+2
    'annual_irradiation': 2200,  # kWh/m²/year
    'average_wind_speed': 6.5,   # m/s
    'average_temperature': 22    # °C
}

# Optimization parameters
OPTIMIZATION_PARAMETERS = {
    'population_size': 50,
    'max_iterations': 100,
    'convergence_tolerance': 1e-6,
    'constraint_penalty': 1000,   # gamma in MATLAB
    'levy_flight_probability': 0.3,
    'elite_ratio': 0.1
}

# Units and conversions
UNIT_CONVERSIONS = {
    'W_to_kW': 1e-3,
    'Wh_to_kWh': 1e-3,
    'hours_per_year': 8760,
    'days_per_year': 365,
    'seconds_per_hour': 3600
}
