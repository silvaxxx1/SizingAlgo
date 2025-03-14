from battery_model import battery_model
from pv_model import pv_model
from wind_model import wind_model
from charge_discharge import charge, discharge
from plotting import plot_results

def main():
    # Call the functions and get results
    Bcap, SOCmin, SOCmax = battery_model(x)
    pp, solar = pv_model()
    pwg, wind, Nwt = wind_model()
    
    # Further logic to perform simulation, charge, and discharge
    
    plot_results()  # Generate all your plots here

if __name__ == '__main__':
    main()
