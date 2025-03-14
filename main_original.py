import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Battery modeling section
def battery_model(x):
    Nbat = x[2]  # no. of batteries that are selected by PSO
    uinv = 0.95
    dod = 0.8  # battery depth of discharge
    AD = 3
    EL = convert  # This variable should be defined elsewhere
    Vs = 48
    Bcap = AD * EL / uinv * n_bat * dod * Vs
    SOCmin = pd.read_excel('SOCmin.xlsx', sheet_name=0, header=None).values.flatten()
    SOCmax = pd.read_excel('SOCmax.xlsx', sheet_name=0, header=None, usecols=[1]).values.flatten()
    return Bcap, SOCmin, SOCmax

# PV modeling section
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

# Wind turbine modeling section
def wind_model():
    # Read wind speed data m/s
    wind = pd.read_excel('g.xlsx', sheet_name=0, usecols=[6], skiprows=18, nrows=8760).values.flatten()
    
    # Load wind turbine data from .mat file
    # Since we can't directly use .mat files in Python, we'll simulate this data
    # In a real scenario, you would use scipy.io.loadmat to load the MATLAB .mat file
    
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
    
    # Calculation of wind speed at HUB height
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

# Population and load demand plotting
def plot_population_load():
    Population_Number = pd.read_excel('book1.xlsx', sheet_name=0, usecols=[8], skiprows=236, nrows=22).values.flatten()
    POWER_DEMAND = pd.read_excel('book1.xlsx', sheet_name=0, usecols=[9], skiprows=236, nrows=22).values.flatten()
    
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax2.plot(Population_Number)
    ax2.set_ylabel('Population Number (Million)')
    ax1.plot(POWER_DEMAND)
    ax1.set_ylabel('Power demand (MW)')
    ax1.grid(True)
    ax1.set_xlabel('Years')
    plt.tight_layout()
    
    return Population_Number, POWER_DEMAND

# Battery charge function
def charge(Eb, Ebmax, Pl, t, Ech, Edch, Pw, Ps, n_bat, Egrid_s, Ev, car_av):
    uconv = 0.95  # CONVERTER efficiency
    uinv = 0.95  # inverter efficiency
    C_Rate = 7.2  # battery charge rate kw/h
    Evmax = 24  # capacity of EV BATTERY
    temp2 = 0  # temporary variable 2 STARTING CHARGING CASE
    
    Edch[t] = 0
    Egrid_s[t] = 0
    Pch = ((Pw[t] + Ps[t]) * uinv) - (Pl[t] / uinv)
    Ech[t] = Pch * n_bat * uconv  # The energy available to battery
    
    if Ech[t] <= Ebmax - Eb[t-1]:
        Eb[t] = Eb[t-1] + Ech[t]
        Ev[t] = Ev[t-1]
    else:
        Eb[t] = Ebmax  # max SOC constraint
        Egrid_s[t] = (Ech[t] - (Ebmax - Eb[t-1])) / (n_bat)  # energy supplied to grid
        Ech[t] = Ebmax - Eb[t-1]
        
        if Egrid_s[t] > C_Rate:
            temp1 = C_Rate
        else:
            temp1 = Egrid_s[t]
        
        Ev[t] = Ev[t-1]
        
        if (Ev[t-1] <= Evmax) and (car_av[t] == 1):
            if (temp1 + Ev[t-1]) > Evmax:
                Ev[t] = Evmax
                temp2 = (Evmax - Ev[t-1])
                Ech[t] = Ech[t] + temp2
                Egrid_s[t] = Egrid_s[t] - temp2
            else:
                Ev[t] = Ev[t-1] + temp1
                temp2 = temp1
                Ech[t] = Ech[t] + temp1
                Egrid_s[t] = Egrid_s[t] - temp1
    
    return Eb, Ech, Edch, Egrid_s, Ev

# Battery discharge function
def discharge(Pw, Ps, Eb, Ebmax, Pl, t, Ebmin, Edch, Ech, Egrid_p, Ev, car_av):
    uconv = 0.95
    uinv = 0.95
    
    Pdch = (Pl[t] / uinv) - ((Pw[t] + Ps[t]) * uconv)
    Edch[t] = Pdch * 1  # one hour iteration time
    Ech[t] = 0
    Egrid_p[t] = 0
    D_Rate = 7.2  # battery discharge rate
    Evmax = 24
    temp1 = 0
    
    if (Ev[t-1] < (Evmax * 0.2)) and (car_av[t] == 1):
        Ev, Egrid_p = charge_Ev(Ev, Egrid_p, t)
    
    if (Eb[t-1] - Ebmin) >= (Edch[t] / uconv):
        Eb[t] = Eb[t-1] - (Edch[t] / uconv)
        Egrid_p[t] = 0  # no energy taken from grid
        Ev[t] = Ev[t-1]
    else:
        if ((Ev[t-1] - (Edch[t] - Eb[t-1] + Ebmin)) > Evmax * 0.2) and (car_av[t] == 1) and ((D_Rate) + Eb[t-1] - Ebmin >= Edch[t]):
            Eb[t] = Ebmin
            Ev[t] = Ev[t-1] - (Edch[t] - Eb[t-1] + Ebmin)
            Edch[t] = Eb[t-1] - Ebmin
        else:
            temp = Eb[t-1] - Ebmin
            Eb[t] = Eb[t-1]
            Ev[t] = Ev[t-1]
            Egrid_p[t] = Edch[t]
            Edch[t] = 0
    
    return Eb, Edch, Ech, Egrid_p, Ev

# Function to charge EV (placeholder, not defined in the original code)
def charge_Ev(Ev, Egrid_p, t):
    # Placeholder for EV charging function
    return Ev, Egrid_p

# Plotting section
def plot_results(Ps, Pw, convert, Edch, Egrid_p, Ech, Eb, Ebmax, SOCmin, SOCmax, pp, pwg, grids, Egrid_s, uinv):
    # Plotting PV and Wind output
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax2.plot(Ps, label='PV')
    ax2.set_ylabel('PV output power (kW)')
    ax1.plot(Pw, label='Wind')
    ax1.set_ylabel('Wind turbine output (kW)')
    ax1.set_xlabel('Time (hours)')
    ax1.set_title('P_pv & P_wt')
    plt.tight_layout()
    
    # Weekly plots
    m1 = 0
    m2 = m1 + 167
    t1 = np.arange(1, 169)
    
    plt.figure()
    plt.plot(t1, convert[m1:m2+1], label='Load', linestyle='--')
    plt.plot(t1, Edch[m1:m2+1], label='Bat_out')
    plt.plot(t1, Pw[m1:m2+1], label='P_WT')
    plt.plot(t1, Egrid_p[m1:m2+1], label='Grid_Purchase')
    plt.ylabel('Energy(KW)')
    plt.xlabel('Time (Hours)')
    plt.grid(True)
    plt.axis('tight')
    plt.legend()
    
    plt.figure()
    plt.fill_between(t1, 0, convert[m1:m2+1], label='Load', color='magenta')
    plt.plot(Ech[m1:m2+1], label='Bat_in', color='red')
    temp = Egrid_p[m1:m2+1] + Pw[m1:m2+1] + Ps[m1:m2+1] + Edch[m1:m2+1] * uinv
    plt.fill_between(t1, 0, temp, label='P_L+ Bat_out+Grid_P', color='blue')
    plt.ylabel('Energy(KW)')
    plt.xlabel('Time (Hours)')
    plt.axis('tight')
    plt.legend()
    plt.grid(True)
    
    # Grid sales and purchases
    plt.figure()
    plt.plot(t1, -Egrid_s[m1:m2+1], label='Grid_sales')
    plt.plot(t1, Egrid_p[m1:m2+1], label='Grid_purchase')
    plt.ylabel('Energy(kW)')
    plt.xlabel('Time (Hours)')
    plt.axis('tight')
    plt.legend()
    plt.grid(True)
    
    # Load, Wind, Battery output, and SOC
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax1.plot(convert[m1:m2+1], label='Load', linewidth=1, linestyle='--', color='cyan')
    ax1.plot(Pw[m1:m2+1], label='P_WT', linewidth=1, linestyle='--', color='blue')
    ax1.plot(Edch[m1:m2+1], label='B_out')
    ax1.set_ylabel('Energy(kW)')
    ax1.set_xlabel('Time (Hours)')
    ax1.grid(True)
    
    ax2.plot(t1, Eb[m1:m2+1] * 100 / Ebmax, label='SOC')
    ax2.set_ylabel('SOC(%)')
    plt.axis('tight')
    plt.legend()
    plt.grid(True)
    
    # Battery charge and discharge
    plt.figure()
    plt.plot(t1, -Ech[m1:m2+1], label='Bat_in')
    plt.plot(t1, Edch[m1:m2+1], label='Bat_out')
    plt.ylabel('Energy(kW)')
    plt.xlabel('Time (Hours)')
    plt.legend()
    plt.grid(True)
    
    plt.figure()
    plt.plot(-Ech, label='Bat_in')
    plt.plot(Edch, label='Bat_out')
    plt.ylabel('Energy(KW)')
    plt.xlabel('Time (Hours)')
    plt.legend()
    plt.grid(True)
    
    # Battery SOC
    plt.figure()
    plt.plot(Eb * 100 / Ebmax, label='SOC')
    plt.ylabel('SOC(%)')
    plt.xlabel('Time (Hours)')
    plt.legend()
    plt.grid(True)
    
    # Load demand
    plt.figure()
    plt.plot(convert, label='load')
    plt.ylabel('Load Demand (KW)')
    plt.xlabel('Time (Hours)')
    plt.axis('tight')
    plt.legend()
    plt.grid(True)
    
    # Wind power
    plt.figure()
    plt.plot(Pw, label='P_WT')
    plt.ylabel('Wind Power (KW)')
    plt.xlabel('Time (Hours)')
    plt.axis('tight')
    plt.legend()
    plt.grid(True)
    
    # Solar power
    plt.figure()
    plt.plot(Ps, label='P_PV')
    plt.ylabel('Solar Power (KW)')
    plt.xlabel('Time (Hours)')
    plt.axis('tight')
    plt.legend()
    plt.grid(True)
    
    # Four seasons SOC
    # 1st season - Spring (Mar-Apr-May)
    m1 = 1417
    m2 = m1 + 167
    plt.figure()
    plt.plot(t1, Eb[m1:m2+1] * 100 / Ebmax, '--', label='SOC')
    plt.plot(SOCmin, 'c-.', linewidth=3)
    plt.plot(SOCmax, 'g-.', linewidth=3)
    plt.axis('tight')
    plt.grid(True)
    plt.ylabel('SOC(%)')
    plt.xlabel('Time (Hours)')
    plt.title('Spring (Mar-Apr-May)')
    plt.legend(['SOC_Spring', 'SOC_min', 'SOC_max'])
    
    # 2nd season - Summer (Jun-Jul-Aug)
    m1 = 3625
    m2 = m1 + 167
    plt.figure()
    plt.plot(t1, Eb[m1:m2+1] * 100 / Ebmax, '--', label='SOC')
    plt.plot(SOCmin, 'c-.', linewidth=3)
    plt.plot(SOCmax, 'g-.', linewidth=3)
    plt.axis('tight')
    plt.ylabel('SOC(%)')
    plt.xlabel('Time (Hours)')
    plt.title('Summer (Jun-Jul-Aug)')
    plt.grid(True)
    plt.legend(['SOC_Summer', 'SOC_min', 'SOC_max'])
    
    # 3rd season - Autumn (Sep-Oct-Nov)
    m1 = 5833
    m2 = m1 + 167
    plt.figure()
    plt.plot(t1, Eb[m1:m2+1] * 100 / Ebmax, '--', label='SOC')
    plt.plot(SOCmin, 'c-.')
    plt.plot(SOCmax, 'g-.')
    plt.axis('tight')
    plt.ylabel('SOC(%)')
    plt.xlabel('Time (Hours)')
    plt.title('Autumn (Sep-Oct-Nov)')
    plt.grid(True)
    plt.legend(['SOC_Autumn', 'SOC_min', 'SOC_max'])
    
    # 4th season - Winter (Dec-Jan-Feb)
    m1 = 8017
    m2 = m1 + 167
    plt.figure()
    plt.plot(t1, Eb[m1:m2+1] * 100 / Ebmax, '--', label='SOC')
    plt.plot(SOCmin, 'c-.')
    plt.plot(SOCmax, 'g-.')
    plt.axis('tight')
    plt.ylabel('SOC(%)')
    plt.xlabel('Time (Hours)')
    plt.grid(True)
    plt.title('Winter (Dec-Jan-Feb)')
    plt.legend(['SOC_Winter', 'SOC_min', 'SOC_max'])
    
    # All in one plot
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    
    ax1.plot(pp, label='P_PV')
    ax1.plot(pwg, label='P_WT')
    ax1.plot(convert, label='load')
    ax1.plot(grids, label='Grid_supply')
    ax1.set_ylabel('Power(KW)')
    ax1.set_xlabel('Time (Hours)')
    ax1.axis('tight')
    ax1.grid(True)
    ax1.legend(['P_PV', 'P_WT', 'P_L', 'Grid_supply', 'Bat_in', 'Bat_out'])
    
    ax2.plot(-Ech, label='Bat_in')
    ax2.plot(Edch, label='Bat_out')
    ax2.set_ylabel('Bat_in&Bat_out')
    ax2.axis('tight')
    ax2.grid(True)
    plt.legend()
    
    plt.tight_layout()

# Objective functions
def calculate_objectives(ASC, Grid_p, Grid_sale, Pw, Ps, Grid_purchased, Egrid_s, convert):
    # Capital Recovery Factor
    REAL_INTREST = 3
    ir = REAL_INTREST / 100
    CRF = ir * (1 + ir)**20 / ((1 + ir)**20 - 1)  # capital recovery factor
    
    # Net Present Cost
    NPC = ASC / CRF
    
    plt.figure()
    plt.plot(NPC)
    plt.axis('tight')
    plt.grid(True)
    plt.xlabel('Renewable electricity fraction')
    plt.ylabel('NPC ($)')
    plt.title('Total NPC')
    
    print(f"The value of NPC is: {NPC}")
    
    # Grid costs
    grid_cost = sum(Grid_p) * 0.023 - sum(Grid_sale) * 0.015
    Grid_purchased_total = sum(Grid_p)
    Grid_sale_total = sum(Grid_sale)
    
    Cgrid = 0.0425 * Grid_p  # 0.023 is the buying price, Cgrid is cost of buying electricity
    print(f"The value of Cgrid is: {Cgrid}")
    
    # Renewable Energy Fraction
    REF = sum(Pw + Ps) / sum(Pw + Ps + Grid_purchased)  # ≈ 0.980932456190068
    ref_percent = REF * 100
    GCF = 1 - REF
    
    print(f"The value of REF is: {REF}")
    print(f"The value of GCF is: {GCF}")
    
    ob = min(GCF)
    
    # Grid revenue
    R_grid = sum(0.02) * Egrid_s  # ≈ 0.0003
    print(f"The value of R_grid is: {R_grid}")
    
    # Cost of Energy
    COE = ((CRF * sum(NPC)) + grid_cost - R_grid / convert + Grid_sale)  # COE in $/kWh
    
    # Plot LCOE vs efficiency
    plt.figure()
    ef = [0.8, 0.85, 0.9, 0.95, 1]
    lcoe_value = [0.2351, 0.2212, 0.2089, 0.1980, 0.1881]
    plt.plot(ef, lcoe_value, marker='*', color='magenta', label='LCOE')
    plt.ylabel('LCOE($/KWh)')
    plt.xlabel('Round trip efficiency')
    plt.grid(True)
    plt.axis('tight')
    plt.legend()
    
    # LPSP (Loss of Power Supply Probability)
    LPS = (convert - (pp + pwg) + R_grid)
    LPSP = sum(LPS) / sum(convert)
    print(f"The value of LPSP is: {LPSP}")  # ≈ 0.49854
    lpsp_percent = LPSP * 100
    
    return NPC, REF, GCF, LPSP, COE

# Main function to run the simulation
def main():
    # Initialize parameters
    x = [0, 0, 3]  # Example parameters where Nbat = 3
    n_bat = 0.9  # Battery efficiency
    
    # Read load data
    convert = np.ones(8760) * 5  # Example load data, should be replaced with actual data
    
    # Initialize storage arrays
    Eb = np.zeros(8761)
    Ech = np.zeros(8761)
    Edch = np.zeros(8761)
    Egrid_s = np.zeros(8761)
    Egrid_p = np.zeros(8761)
    Ev = np.zeros(8761)
    
    # Ebmax is maximum battery capacity
    Ebmax = 100  # Example value
    Ebmin = 0.2 * Ebmax  # Minimum battery capacity
    
    # EV availability (1 = available, 0 = not available)
    car_av = np.random.randint(0, 2, size=8761)
    
    # Run battery model
    Bcap, SOCmin, SOCmax = battery_model(x)
    
    # Run PV model
    pp, solar = pv_model()
    
    # Run wind model
    pwg, wind, Nwt = wind_model()
    
    # Simulate the system for 8760 hours (1 year)
    for t in range(1, 8761):
        # Check if load demand is greater than generation
        if convert[t-1] > (pp[t-1] + pwg[t-1]):
            # Discharge battery or use grid
            Eb, Edch, Ech, Egrid_p, Ev = discharge(pp, pwg, Eb, Ebmax, convert, t, Ebmin, Edch, Ech, Egrid_p, Ev, car_av)
        else:
            # Charge battery or sell to grid
            Eb, Ech, Edch, Egrid_s, Ev = charge(Eb, Ebmax, convert, t, Ech, Edch, pp, pwg, n_bat, Egrid_s, Ev, car_av)
    
    # Calculate grid supply
    grids = Egrid_p - Egrid_s
    
    # Plot results
    plot_results(pp, pwg, convert, Edch, Egrid_p, Ech, Eb, Ebmax, SOCmin, SOCmax, pp, pwg, grids, Egrid_s, 0.95)
    
    # Calculate and plot objective functions
    ASC = 10000  # Example Annual System Cost
    Grid_p = Egrid_p[1:]  # Remove first element (initialization)
    Grid_sale = Egrid_s[1:]  # Remove first element (initialization)
    Grid_purchased = sum(Grid_p)
    
    NPC, REF, GCF, LPSP, COE = calculate_objectives(ASC, Grid_p, Grid_sale, pwg, pp, Grid_purchased, Egrid_s[1:], convert)
    
    return Eb, Ech, Edch, Egrid_p, Egrid_s, NPC, REF, GCF, LPSP, COE

if __name__ == "__main__":
    main()