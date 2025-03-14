import pandas as pd
import matplotlib.pyplot as plt

def pv_model():
    # Read solar irradiance data W/m^2
    solar = pd.read_excel('g.xlsx', sheet_name=0, usecols=[4], skiprows=18, nrows=8760).values.flatten()
    # Read temperature data °C
    temp = pd.read_excel('g.xlsx', sheet_name=0, usecols=[5], skiprows=18, nrows=8760).values.flatten()
    Tam = temp  # ambient temperature °C
    
    # Plotting of PV_out
    Gref = 1000  # reference solar radiation (W/m^2)
    NOCT = 45  # Nominal cell operating temperature
    kt = -3.7e-3  # Temperature coefficient
    Tref = 25  # Temperature at reference condition
    Tc = Tam + ((NOCT-20)/800) * solar  # cell temperature
    pv_eff = 7.3  # solar panels efficiency
    G = solar
    PV_out = (pv_eff * (G/Gref)) * (1 + kt * (Tc-Tref))  # PV output power
    pp = PV_out
    
    plt.figure()
    plt.plot(pp)
    plt.axis('tight')
    plt.box(True)
    plt.grid(True)
    plt.xlabel('Time (hours)')
    plt.ylabel('PV output power (kW)')
    plt.title('Output power generated from PV')
    
    return pp, solar
