import pandas as pd

def battery_model(x):
    Nbat = x[2]  # no. of batteries selected by PSO
    uinv = 0.95
    dod = 0.8  # battery depth of discharge
    AD = 3
    EL = convert  # This variable should be defined elsewhere
    Vs = 48
    Bcap = AD * EL / uinv * n_bat * dod * Vs
    SOCmin = pd.read_excel('SOCmin.xlsx', sheet_name=0, header=None).values.flatten()
    SOCmax = pd.read_excel('SOCmax.xlsx', sheet_name=0, usecols=[1]).values.flatten()
    return Bcap, SOCmin, SOCmax
