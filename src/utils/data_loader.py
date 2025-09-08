# utils/data_loader.py
import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
from typing import Dict, Union, Optional

class DataLoader:
    """
    Data loading utility for V2G microgrid optimization pipeline
    Handles weather data, load profiles, and EV data based on thesis requirements
    """
    
    def __init__(self, config: Dict):
        """
        Initialize data loader with configuration
        
        Args:
            config: Configuration dictionary containing file paths and parameters
        """
        self.config = config
        self.data_dir = Path(config.get('data_dir', 'data/'))
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        
        logging.info(f"DataLoader initialized with data directory: {self.data_dir}")
    
    def load_weather_data(self, filepath: str = None) -> pd.DataFrame:
        """
        Load weather data (solar irradiance, wind speed, temperature)
        Based on MATLAB data structure: solar, temp, wind arrays
        
        Args:
            filepath: Optional custom filepath
            
        Returns:
            DataFrame with weather data
        """
        if filepath is None:
            filepath = self.config.get('weather_data_path', 'data/weather_data.csv')
        
        try:
            # Try to load existing file
            weather_data = pd.read_csv(filepath)
            
            # Validate required columns
            required_columns = ['solar_irradiance', 'ambient_temp', 'wind_speed']
            missing_columns = [col for col in required_columns if col not in weather_data.columns]
            
            if missing_columns:
                logging.warning(f"Missing columns in weather data: {missing_columns}")
                return self._generate_synthetic_weather_data()
            
            logging.info(f"Loaded weather data from {filepath}: {len(weather_data)} records")
            
        except FileNotFoundError:
            logging.warning(f"Weather data file not found: {filepath}. Generating synthetic data.")
            weather_data = self._generate_synthetic_weather_data()
            weather_data.to_csv(filepath, index=False)
            logging.info(f"Synthetic weather data saved to {filepath}")
        
        return weather_data
    
    def _generate_synthetic_weather_data(self, hours: int = 8760) -> pd.DataFrame:
        """
        Generate synthetic weather data based on Tripoli, Libya patterns
        Based on thesis location and MATLAB data ranges
        """
        # Create hourly timestamps for one year
        timestamps = pd.date_range(start='2024-01-01', periods=hours, freq='h')
        
        weather_data = pd.DataFrame({'timestamp': timestamps})
        weather_data['hour'] = weather_data['timestamp'].dt.hour
        weather_data['day_of_year'] = weather_data['timestamp'].dt.dayofyear
        
        # Solar irradiance (W/m²) - Based on MATLAB solar data patterns
        # Peak around noon, seasonal variation, clear sky model
        solar_peak = 1000  # W/m² at solar noon
        
        # Seasonal variation (higher in summer)
        seasonal_factor = 0.8 + 0.4 * np.cos(2 * np.pi * (weather_data['day_of_year'] - 172) / 365)
        
        # Diurnal variation (cosine function centered at noon)
        hour_angle = (weather_data['hour'] - 12) * 15  # degrees
        solar_elevation = np.maximum(0, np.cos(np.radians(hour_angle)))
        
        # Cloud factor (random variation)
        cloud_factor = np.random.uniform(0.7, 1.0, hours)
        
        weather_data['solar_irradiance'] = solar_peak * seasonal_factor * solar_elevation * cloud_factor
        weather_data['solar_irradiance'] = np.maximum(0, weather_data['solar_irradiance'])
        
        # Ambient temperature (°C) - Based on Tripoli climate
        temp_mean = 22  # Annual mean temperature
        temp_seasonal_amplitude = 12  # Seasonal variation
        temp_daily_amplitude = 8   # Daily variation
        
        # Seasonal temperature variation
        seasonal_temp = temp_seasonal_amplitude * np.cos(2 * np.pi * (weather_data['day_of_year'] - 200) / 365)
        
        # Daily temperature variation (peak around 2 PM)
        daily_temp = temp_daily_amplitude * np.cos(2 * np.pi * (weather_data['hour'] - 14) / 24)
        
        # Random variation
        temp_noise = np.random.normal(0, 2, hours)
        
        weather_data['ambient_temp'] = temp_mean + seasonal_temp + daily_temp + temp_noise
        
        # Wind speed (m/s) - Based on MATLAB wind data patterns
        # Higher winds in winter, diurnal variation
        wind_mean = 6.5  # Mean wind speed
        wind_seasonal = 2 * np.cos(2 * np.pi * (weather_data['day_of_year'] - 45) / 365)  # Higher in winter
        wind_daily = 1.5 * np.cos(2 * np.pi * (weather_data['hour'] - 15) / 24)  # Afternoon winds
        wind_noise = np.random.weibull(2, hours) * 2  # Weibull distribution for wind
        
        weather_data['wind_speed'] = np.maximum(0, wind_mean + wind_seasonal + wind_daily + wind_noise)
        
        # Keep only required columns
        return weather_data[['solar_irradiance', 'ambient_temp', 'wind_speed']]
    
    def load_load_profile(self, filepath: str = None) -> pd.DataFrame:
        """
        Load residential load demand profile
        Based on MATLAB load data (convert variable)
        """
        if filepath is None:
            filepath = self.config.get('load_data_path', 'data/load_data.csv')
        
        try:
            load_data = pd.read_csv(filepath)
            
            if 'load_demand' not in load_data.columns:
                logging.warning("Load demand column not found. Generating synthetic data.")
                return self._generate_synthetic_load_data()
            
            logging.info(f"Loaded load data from {filepath}: {len(load_data)} records")
            
        except FileNotFoundError:
            logging.warning(f"Load data file not found: {filepath}. Generating synthetic data.")
            load_data = self._generate_synthetic_load_data()
            load_data.to_csv(filepath, index=False)
            logging.info(f"Synthetic load data saved to {filepath}")
        
        return load_data
    
    def _generate_synthetic_load_data(self, hours: int = 8760) -> pd.DataFrame:
        """
        Generate synthetic residential load profile
        Based on typical residential consumption patterns
        """
        timestamps = pd.date_range(start='2024-01-01', periods=hours, freq='h')
        load_data = pd.DataFrame({'timestamp': timestamps})
        load_data['hour'] = load_data['timestamp'].dt.hour
        load_data['day_of_week'] = load_data['timestamp'].dt.dayofweek
        load_data['month'] = load_data['timestamp'].dt.month
        
        # Base load (kW) - continuous consumption
        base_load = 1.5
        
        # Diurnal pattern - higher consumption in evening
        diurnal_pattern = np.array([
            0.6, 0.5, 0.5, 0.5, 0.6, 0.8,  # 00:00-05:00 (night)
            1.2, 1.8, 2.0, 1.5, 1.2, 1.0,  # 06:00-11:00 (morning)
            1.1, 1.2, 1.3, 1.5, 2.0, 2.5,  # 12:00-17:00 (afternoon)
            3.0, 3.5, 3.2, 2.5, 1.8, 1.0   # 18:00-23:00 (evening)
        ])
        
        hourly_multiplier = np.tile(diurnal_pattern, hours // 24 + 1)[:hours]
        
        # Weekly pattern - higher on weekends
        weekend_factor = np.where((load_data['day_of_week'] == 5) | (load_data['day_of_week'] == 6), 1.2, 1.0)
        
        # Seasonal pattern - higher in summer (air conditioning)
        seasonal_factor = 1 + 0.5 * np.cos(2 * np.pi * (load_data['month'] - 7) / 12)
        
        # Random variation
        random_factor = np.random.normal(1.0, 0.1, hours)
        
        load_data['load_demand'] = base_load * hourly_multiplier * weekend_factor * seasonal_factor * random_factor
        load_data['load_demand'] = np.maximum(0.5, load_data['load_demand'])  # Minimum load
        
        return load_data[['load_demand']]
    
    def load_ev_data(self, filepath: str = None) -> pd.DataFrame:
        """
        Load EV behavior data (arrival/departure patterns, SOC)
        """
        if filepath is None:
            filepath = self.config.get('ev_data_path', 'data/ev_data.csv')
        
        try:
            ev_data = pd.read_csv(filepath)
            logging.info(f"Loaded EV data from {filepath}: {len(ev_data)} records")
            
        except FileNotFoundError:
            logging.warning(f"EV data file not found: {filepath}. Generating synthetic data.")
            ev_data = self._generate_synthetic_ev_data()
            ev_data.to_csv(filepath, index=False)
            logging.info(f"Synthetic EV data saved to {filepath}")
        
        return ev_data
    
    def _generate_synthetic_ev_data(self, num_profiles: int = 100) -> pd.DataFrame:
        """
        Generate synthetic EV behavior profiles
        Based on typical commuter patterns
        """
        ev_profiles = []
        
        for i in range(num_profiles):
            profile = {
                'profile_id': i,
                'arrival_time_mean': np.random.normal(18, 2),  # Around 6 PM
                'arrival_time_std': np.random.uniform(0.5, 1.5),
                'departure_time_mean': np.random.normal(7.5, 1.5),  # Around 7:30 AM
                'departure_time_std': np.random.uniform(0.3, 1.0),
                'soc_arrival_mean': np.random.uniform(0.3, 0.8),  # SOC upon arrival
                'soc_arrival_std': np.random.uniform(0.1, 0.2),
                'daily_consumption_mean': np.random.uniform(8, 20),  # kWh per day
                'daily_consumption_std': np.random.uniform(2, 5),
                'charging_preference': np.random.choice(['immediate', 'delayed', 'smart'], p=[0.4, 0.3, 0.3])
            }
            ev_profiles.append(profile)
        
        return pd.DataFrame(ev_profiles)
    
    def load_economic_parameters(self, filepath: str = None) -> Dict:
        """
        Load economic parameters from JSON file
        """
        if filepath is None:
            filepath = self.config.get('economic_parameters_path', 'data/economic_parameters.json')
        
        try:
            with open(filepath, 'r') as f:
                economic_params = json.load(f)
            logging.info(f"Loaded economic parameters from {filepath}")
            
        except FileNotFoundError:
            logging.warning(f"Economic parameters file not found: {filepath}. Using defaults.")
            economic_params = self._get_default_economic_parameters()
            
            # Save default parameters
            with open(filepath, 'w') as f:
                json.dump(economic_params, f, indent=2)
            logging.info(f"Default economic parameters saved to {filepath}")
        
        return economic_params
    
    def _get_default_economic_parameters(self) -> Dict:
        """Get default economic parameters based on MATLAB code"""
        return {
            "interest_rate": 0.03,
            "project_lifetime": 20,
            "grid_buy_price": 0.023,
            "grid_sell_price": 0.015,
            "component_costs": {
                "pv_panel_cost": 200,
                "wind_turbine_cost_per_kw": 2000,
                "battery_cost_per_kwh": 300,
                "converter_cost_per_kw": 150,
                "inverter_cost_per_kw": 100,
                "installation_factor": 0.2,
                "maintenance_factor": 0.02
            },
            "inflation_rate": 0.025,
            "discount_rate": 0.05
        }
    
    def validate_data_consistency(self, 
                                weather_data: pd.DataFrame,
                                load_data: pd.DataFrame) -> bool:
        """
        Validate that weather and load data have consistent time periods
        """
        if len(weather_data) != len(load_data):
            logging.warning(f"Data length mismatch: weather={len(weather_data)}, load={len(load_data)}")
            return False
        
        # Check for missing values
        weather_missing = weather_data.isnull().sum().sum()
        load_missing = load_data.isnull().sum().sum()
        
        if weather_missing > 0:
            logging.warning(f"Weather data has {weather_missing} missing values")
        
        if load_missing > 0:
            logging.warning(f"Load data has {load_missing} missing values")
        
        return True
    
    def get_data_statistics(self, 
                           weather_data: pd.DataFrame,
                           load_data: pd.DataFrame) -> Dict:
        """
        Get statistical summary of loaded data
        """
        stats = {
            'data_period': {
                'total_hours': len(weather_data),
                'total_days': len(weather_data) / 24,
                'total_years': len(weather_data) / 8760
            },
            'weather_statistics': {
                'solar_irradiance': {
                    'mean': weather_data['solar_irradiance'].mean(),
                    'max': weather_data['solar_irradiance'].max(),
                    'std': weather_data['solar_irradiance'].std()
                },
                'ambient_temp': {
                    'mean': weather_data['ambient_temp'].mean(),
                    'max': weather_data['ambient_temp'].max(),
                    'min': weather_data['ambient_temp'].min(),
                    'std': weather_data['ambient_temp'].std()
                },
                'wind_speed': {
                    'mean': weather_data['wind_speed'].mean(),
                    'max': weather_data['wind_speed'].max(),
                    'std': weather_data['wind_speed'].std()
                }
            },
            'load_statistics': {
                'mean_demand': load_data['load_demand'].mean(),
                'peak_demand': load_data['load_demand'].max(),
                'min_demand': load_data['load_demand'].min(),
                'total_annual_energy': load_data['load_demand'].sum(),
                'load_factor': load_data['load_demand'].mean() / load_data['load_demand'].max()
            }
        }
        
        return stats


# utils/visualization.py
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging

class Visualizer:
    """
    Visualization utilities for V2G microgrid optimization results
    """
    
    def __init__(self, style: str = 'seaborn-v0_8', figsize: Tuple[int, int] = (12, 8)):
        """
        Initialize visualizer with plotting style
        """
        plt.style.use('default')  # Use default since seaborn styles may not be available
        sns.set_palette("husl")
        self.figsize = figsize
        
        # Color scheme for different components
        self.colors = {
            'pv': '#FF6B35',           # Orange
            'wind': '#4ECDC4',         # Teal
            'battery': '#45B7D1',      # Blue
            'ev': '#96CEB4',           # Green
            'grid': '#FF6B9D',         # Pink
            'load': '#C44569'          # Purple
        }
        
        logging.info("Visualizer initialized")
    
    def plot_convergence(self, 
                        convergence_history: List[float],
                        title: str = "Optimization Convergence",
                        save_path: str = None):
        """
        Plot optimization convergence history
        """
        plt.figure(figsize=self.figsize)
        plt.plot(convergence_history, linewidth=2, color=self.colors['battery'])
        plt.title(title, fontsize=16, fontweight='bold')
        plt.xlabel('Iteration', fontsize=12)
        plt.ylabel('Objective Function Value', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logging.info(f"Convergence plot saved to {save_path}")
        
        plt.show()
    
    def plot_energy_flows(self, 
                         simulation_results: pd.DataFrame,
                         time_range: Tuple[int, int] = None,
                         save_path: str = None):
        """
        Plot energy flows over time (similar to MATLAB plotting section)
        """
        if time_range is None:
            # Plot first week by default
            time_range = (0, min(168, len(simulation_results)))
        
        start_idx, end_idx = time_range
        data_subset = simulation_results.iloc[start_idx:end_idx]
        hours = range(len(data_subset))
        
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12))
        
        # Plot 1: Power Generation and Load
        ax1.plot(hours, data_subset['pv_power'], label='PV Power', 
                color=self.colors['pv'], linewidth=2)
        ax1.plot(hours, data_subset['wt_power'], label='Wind Power', 
                color=self.colors['wind'], linewidth=2)
        ax1.plot(hours, data_subset['load_demand'], label='Load Demand', 
                color=self.colors['load'], linewidth=2, linestyle='--')
        ax1.set_title('Renewable Generation and Load Demand', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Power (kW)', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Energy Storage (Battery and EV)
        ax2.plot(hours, data_subset['battery_charge'], label='Battery Charge', 
                color=self.colors['battery'], linewidth=2)
        ax2.plot(hours, -data_subset['battery_discharge'], label='Battery Discharge', 
                color=self.colors['battery'], linewidth=2, alpha=0.7)
        ax2.plot(hours, data_subset['ev_charge'], label='EV Charge (G2V)', 
                color=self.colors['ev'], linewidth=2)
        ax2.plot(hours, -data_subset['ev_discharge'], label='EV Discharge (V2G)', 
                color=self.colors['ev'], linewidth=2, alpha=0.7)
        ax2.set_title('Energy Storage Operations', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Energy (kWh)', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Grid Interactions and SOC
        ax3_twin = ax3.twinx()
        ax3.plot(hours, data_subset['grid_purchase'], label='Grid Purchase', 
                color=self.colors['grid'], linewidth=2)
        ax3.plot(hours, -data_subset['grid_sale'], label='Grid Sale', 
                color=self.colors['grid'], linewidth=2, alpha=0.7)
        ax3.set_ylabel('Grid Energy (kWh)', fontsize=12)
        ax3.set_xlabel('Time (Hours)', fontsize=12)
        
        # SOC on secondary y-axis
        ax3_twin.plot(hours, data_subset['battery_soc'] * 100, label='Battery SOC', 
                     color='red', linewidth=2, linestyle=':')
        ax3_twin.plot(hours, data_subset['ev_mean_soc'] * 100, label='EV Mean SOC', 
                     color='orange', linewidth=2, linestyle=':')
        ax3_twin.set_ylabel('State of Charge (%)', fontsize=12)
        ax3_twin.set_ylim([0, 100])
        
        ax3.set_title('Grid Interactions and State of Charge', fontsize=14, fontweight='bold')
        ax3.legend(loc='upper left')
        ax3_twin.legend(loc='upper right')
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logging.info(f"Energy flows plot saved to {save_path}")
        
        plt.show()
    
    def plot_monte_carlo_results(self, 
                                monte_carlo_results: Dict,
                                save_path: str = None):
        """
        Plot Monte Carlo simulation results
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        scenarios = list(monte_carlo_results.keys())
        
        # Collect data for all scenarios
        coe_data = []
        lpsp_data = []
        ref_data = []
        v2g_data = []
        scenario_labels = []
        
        for scenario in scenarios:
            results = monte_carlo_results[scenario]['detailed_results']
            scenario_labels.extend([scenario.replace('_', ' ').title()] * len(results))
            coe_data.extend(results['coe'].tolist())
            lpsp_data.extend(results['lpsp'].tolist())
            ref_data.extend(results['ref'].tolist())
            v2g_data.extend(results['total_v2g_energy'].tolist())
        
        # COE distribution
        data_df = pd.DataFrame({
            'COE': coe_data,
            'LPSP': lpsp_data,
            'REF': ref_data,
            'V2G Energy': v2g_data,
            'Scenario': scenario_labels
        })
        
        # Plot distributions
        sns.boxplot(data=data_df, x='Scenario', y='COE', ax=axes[0,0])
        axes[0,0].set_title('Cost of Energy Distribution', fontweight='bold')
        axes[0,0].set_ylabel('COE ($/kWh)')
        
        sns.boxplot(data=data_df, x='Scenario', y='LPSP', ax=axes[0,1])
        axes[0,1].set_title('Loss of Power Supply Probability', fontweight='bold')
        axes[0,1].set_ylabel('LPSP')
        
        sns.boxplot(data=data_df, x='Scenario', y='REF', ax=axes[1,0])
        axes[1,0].set_title('Renewable Energy Fraction', fontweight='bold')
        axes[1,0].set_ylabel('REF')
        
        sns.boxplot(data=data_df, x='Scenario', y='V2G Energy', ax=axes[1,1])
        axes[1,1].set_title('V2G Energy Contribution', fontweight='bold')
        axes[1,1].set_ylabel('V2G Energy (kWh)')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logging.info(f"Monte Carlo results plot saved to {save_path}")
        
        plt.show()
    
    def plot_economic_analysis(self, 
                              economic_results: Dict,
                              save_path: str = None):
        """
        Plot economic analysis results
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Economic metrics
        metrics = ['COE', 'LPSP', 'REF', 'NPC']
        values = [economic_results['coe'], economic_results['lpsp'], 
                 economic_results['ref'], economic_results['npc']]
        
        # COE breakdown (if available)
        if 'cost_breakdown' in economic_results:
            breakdown = economic_results['cost_breakdown']
            ax1.pie(breakdown.values(), labels=breakdown.keys(), autopct='%1.1f%%')
            ax1.set_title('Cost Breakdown', fontweight='bold')
        else:
            ax1.bar(['COE'], [economic_results['coe']], color=self.colors['battery'])
            ax1.set_title('Cost of Energy', fontweight='bold')
            ax1.set_ylabel('$/kWh')
        
        # Reliability metrics
        reliability_metrics = ['LPSP', 'REF']
        reliability_values = [economic_results['lpsp'], economic_results['ref']]
        bars = ax2.bar(reliability_metrics, reliability_values, 
                      color=[self.colors['grid'], self.colors['pv']])
        ax2.set_title('Reliability Metrics', fontweight='bold')
        ax2.set_ylabel('Value')
        
        # Add value labels on bars
        for bar, value in zip(bars, reliability_values):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{value:.3f}', ha='center', va='bottom')
        
        # Economic comparison (dummy data for demonstration)
        scenarios = ['Baseline', 'With V2G', 'Optimized']
        coe_comparison = [economic_results['coe'] * 1.2, economic_results['coe'], 
                         economic_results['coe'] * 0.9]
        
        ax3.bar(scenarios, coe_comparison, color=self.colors['battery'], alpha=0.7)
        ax3.set_title('COE Comparison', fontweight='bold')
        ax3.set_ylabel('COE ($/kWh)')
        
        # NPC visualization
        ax4.bar(['Net Present Cost'], [economic_results['npc']], 
               color=self.colors['load'], alpha=0.7)
        ax4.set_title('Net Present Cost', fontweight='bold')
        ax4.set_ylabel('Cost ($)')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logging.info(f"Economic analysis plot saved to {save_path}")
        
        plt.show()
    
    def plot_component_sizing(self, 
                             component_sizing: Dict,
                             save_path: str = None):
        """
        Plot optimal component sizing results
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Component counts
        components = ['PV Panels', 'Wind Turbines', 'Batteries']
        counts = [component_sizing['n_pv'], component_sizing['n_wt'], component_sizing['n_bt']]
        colors_list = [self.colors['pv'], self.colors['wind'], self.colors['battery']]
        
        bars1 = ax1.bar(components, counts, color=colors_list, alpha=0.7)
        ax1.set_title('Optimal Component Sizing', fontweight='bold')
        ax1.set_ylabel('Number of Units')
        
        # Add value labels
        for bar, count in zip(bars1, counts):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(count)}', ha='center', va='bottom', fontweight='bold')
        
        # Capacity breakdown
        capacities = {
            'PV Capacity (kW)': component_sizing['n_pv'] * 0.325,  # Assuming 325W panels
            'Wind Capacity (kW)': component_sizing['n_wt'] * 5,    # Assuming 5kW turbines
            'Battery Capacity (kWh)': component_sizing['n_bt'] * 35.38  # From MATLAB
        }
        
        wedges, texts, autotexts = ax2.pie(capacities.values(), 
                                          labels=capacities.keys(), 
                                          autopct='%1.1f%%',
                                          colors=colors_list)
        ax2.set_title('System Capacity Distribution', fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logging.info(f"Component sizing plot saved to {save_path}")
        
        plt.show()


# Example usage
if __name__ == "__main__":
    # Test data loader
    config = {
        'data_dir': 'data/',
        'weather_data_path': 'data/weather_data.csv',
        'load_data_path': 'data/load_data.csv'
    }
    
    loader = DataLoader(config)
    weather_data = loader.load_weather_data()
    load_data = loader.load_load_profile()
    
    print(f"Weather data shape: {weather_data.shape}")
    print(f"Load data shape: {load_data.shape}")
    
    # Test visualizer
    vis = Visualizer()
    convergence_test = [100, 50, 25, 12, 8, 5, 3, 2, 1.5, 1.2, 1.0]
    vis.plot_convergence(convergence_test, title="Test Convergence")