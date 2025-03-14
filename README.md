# Hybrid Renewable Energy System Modeling

## Overview
This project models a **hybrid renewable energy system** combining **photovoltaic (PV) panels, wind turbines, and battery storage** to simulate energy generation and storage behavior over time. It includes key functionalities for system analysis, such as battery charge/discharge management, renewable power output estimation, and load demand plotting.

## Features
- **Photovoltaic (PV) Power Generation Modeling**
- **Wind Turbine Power Generation Modeling**
- **Battery Energy Storage System Simulation**
- **Load Demand and Population Data Visualization**
- **Energy Balance Analysis** (Charge/Discharge Cycles)
- **Data-Driven System Behavior** (Excel-based input support)

## Installation
Clone this repository and install the required dependencies:

```sh
git clone 
cd hybrid-energy-model https://github.com/silvaxxx1/SizingAlgo.git
pip install -r requirements.txt
```

## Dependencies
Ensure you have the following Python libraries installed:

```sh
pip install numpy pandas matplotlib openpyxl
```

## Usage
Run the main script to simulate the hybrid system:

```sh
python main.py
```

### Key Scripts
- **`battery_model.py`** - Implements the battery charge/discharge logic
- **`pv_model.py`** - Models the photovoltaic power generation
- **`wind_model.py`** - Simulates wind turbine power output
- **`plot_population_load.py`** - Visualizes load demand and population data

## Data Requirements
Ensure the following Excel files are present in the working directory:
- **`SOCmin.xlsx`** & **`SOCmax.xlsx`** - Battery state-of-charge limits
- **`g.xlsx`** - PV generation parameters
- **`book1.xlsx`** - Load demand and wind data

## Results
The project generates plots and data outputs representing energy generation, battery behavior, and demand-supply analysis.

## Future Improvements
- Implement **real-time energy dispatch algorithms**
- Add **economic feasibility analysis**
- Improve **optimization strategies** for renewable energy utilization

## Contributions
Contributions are welcome! Feel free to submit issues or pull requests.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author
Developed by [Your Name](https://github.com/yourusername)

