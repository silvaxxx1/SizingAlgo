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
    # Calculate the cost of energy before running the AL ALgorithms (COE)
    # compare the results of multiple algos : 
    # 1- ANt Lion 
    # 2- PSO
    # 3- Cuso nest ... 

    # WE WILL USE ONE TYPE OF VECHICLE IN THIS SIMULATION (TESLA MODEL 3) / (NESSAN)


    # CHANGEING THE DATA LOCATION OF THE DATA :
    # NASA OR REAL LIFE DATA FROM THE LOCATION 
    

    plot_results()  # Generate all your plots here

if __name__ == '__main__':
    main()
