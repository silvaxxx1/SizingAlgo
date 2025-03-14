import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def wind_model():
    # Read wind speed data m/s
    wind = pd.read_excel('g.xlsx', sheet_name=0, usecols=[6], skiprows=18, nrows=8760).values.flatten()
    
    # Simulated wind turbine parameters
    WindTurbines = {
        'bd': 6.4,  # Blades diameter(m)
        'as': np.pi * (6.4/2)**2,  # Area swept by blade(m)
        'eff': 0.95,  # Efficiency
        'vcut': 40,  # cut out speed m/s
        'vin': 2.5,  # cut in speed m/s
        'vr': 9.5,  # rated speed m/s
        'pr': 5,  # rated power pr=5kw
        'pcut': 4,  # output power at cut-out speed
        'pmax': 5.5  # maximum output power
    }
    
    # Wind speed calculation at HUB height
    V1 = wind  # wind speed
    h2 = 70  # Wind turbine at hub height
    h1 = 43.6  # Reference height
    alfa = 0.25  # for heavily forested landscape (power law exponential)
    V2 = V1 * (h2/h1)**alfa  # Wind speed at hub height
    
    # Wind turbine model
    WTM = 4  # Chosen wind turbine model
    bd = WindTurbines['bd']
    as_val = WindTurbines['as']
    eff = WindTurbines['eff']
    vcut = WindTurbines['vcut']
    vin = WindTurbines['vin']
    vr = WindTurbines['vr']
    pr = WindTurbines['pr']
    pcut = WindTurbines['pcut']
    pmax = WindTurbines['pmax']
    
    pwt = np.zeros(8760)
    for t in range(8760):
        if V2[t] < vin:
            pwt[t] = 0
        elif vin <= V2[t] and V2[t] <= vr:
            pwt[t] = ((V2[t])**3 * (pr/((vr)**3-(vin)**3))) - pr*((vin)**3/((vr)**3-(vin)**3))
        elif vr < V2[t] and V2[t] < vcut:
            pwt[t] = pr
        else:
            pwt[t] = 0
    
    pwg = pwt * eff  # Electric power from wind turbine
    Nwt = np.sum(wind) / np.sum(pwg)
    
    # Plotting
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax2.plot(pp, label='PV')
    ax2.set_ylabel('PV output power (kW)')
    ax1.plot(pwg, label='Wind')
    ax1.set_ylabel('Wind turbine output (kW)')
    ax1.set_xlabel('Time (hours)')
    ax1.set_title('P_pv & P_wt')
    plt.tight_layout()
    
    plt.figure()
    plt.plot(pwg)
    plt.grid(True)
    plt.axis('tight')
    plt.box(True)
    plt.xlabel('Time (hours)')
    plt.ylabel('Wind Turbine output (kW)')
    plt.title('Output power generated from wind')
    
    return pwg, wind, Nwt
