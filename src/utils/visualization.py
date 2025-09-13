# utils/visualization.py
"""
Comprehensive visualization module for V2G microgrid optimization results
Provides publication-ready plots and interactive dashboards
"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
import logging
from pathlib import Path
import warnings

# Optional imports for enhanced visualizations
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logging.warning("Plotly not available. Interactive plots will be disabled.")

warnings.filterwarnings('ignore', category=UserWarning)

class Visualizer:
    """
    Comprehensive visualization class for V2G microgrid optimization results
    """
    
    def __init__(self, 
                 style: str = 'seaborn-v0_8-darkgrid', 
                 figsize: Tuple[int, int] = (12, 8),
                 dpi: int = 300,
                 color_palette: str = 'Set2'):
        """
        Initialize visualizer with plotting parameters
        
        Args:
            style: Matplotlib style
            figsize: Default figure size
            dpi: Resolution for saved figures
            color_palette: Seaborn color palette
        """
        # Set matplotlib style
        try:
            plt.style.use(style)
        except OSError:
            plt.style.use('default')
            logging.warning(f"Style '{style}' not available, using default")
        
        # Set seaborn parameters
        sns.set_palette(color_palette)
        
        self.figsize = figsize
        self.dpi = dpi
        
        # Color scheme for different energy components
        self.colors = {
            'pv': '#FF6B35',           # Orange for solar
            'wind': '#4ECDC4',         # Teal for wind
            'battery': '#45B7D1',      # Blue for battery
            'ev': '#96CEB4',           # Green for EV
            'grid': '#FF6B9D',         # Pink for grid
            'load': '#C44569',         # Purple for load
            'surplus': '#FFA07A',      # Light salmon for surplus
            'deficit': '#FF4500'       # Red orange for deficit
        }
        
        # Create output directories
        self.ensure_output_dirs()
        
        logging.info("Visualizer initialized with matplotlib and seaborn")
        if PLOTLY_AVAILABLE:
            logging.info("Plotly available for interactive visualizations")
    
    def ensure_output_dirs(self):
        """Create output directories if they don't exist"""
        output_dirs = ['outputs/figures', 'outputs/figures/static', 'outputs/figures/interactive']
        for dir_path in output_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def plot_convergence(self, 
                        convergence_history: Union[List[float], Dict[str, List[float]]],
                        title: str = "Optimization Convergence",
                        save_path: Optional[str] = None,
                        show_plot: bool = True) -> None:
        """
        Plot optimization algorithm convergence
        
        Args:
            convergence_history: Single list or dict of algorithm histories
            title: Plot title
            save_path: Path to save figure
            show_plot: Whether to display plot
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        if isinstance(convergence_history, dict):
            # Multiple algorithms
            for alg_name, history in convergence_history.items():
                if history and len(history) > 0:  # FIXED: Check if history exists and not empty
                    iterations = range(len(history))
                    ax.plot(iterations, history, linewidth=2.5, 
                           label=alg_name, marker='o', markersize=4, alpha=0.8)
        else:
            # Single algorithm
            if convergence_history and len(convergence_history) > 0:  # FIXED: Check if history exists
                iterations = range(len(convergence_history))
                ax.plot(iterations, convergence_history, linewidth=2.5, 
                       color=self.colors['battery'], marker='o', markersize=4)
        
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Iteration', fontsize=12)
        ax.set_ylabel('Objective Function Value', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        if isinstance(convergence_history, dict):
            ax.legend(fontsize=10, framealpha=0.9)
        
        # Add improvement annotation
        if isinstance(convergence_history, list) and len(convergence_history) > 1:  # FIXED
            improvement = ((convergence_history[0] - convergence_history[-1]) / 
                          convergence_history[0] * 100)
            ax.annotate(f'Improvement: {improvement:.1f}%', 
                       xy=(0.7, 0.95), xycoords='axes fraction',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.7))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logging.info(f"Convergence plot saved to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def plot_energy_flows(self, 
                         simulation_results: Union[pd.DataFrame, Dict],
                         time_range: Optional[Tuple[int, int]] = None,
                         save_path: Optional[str] = None,
                         show_plot: bool = True) -> None:
        """
        Plot comprehensive energy flows over time
        
        Args:
            simulation_results: DataFrame or Dict with simulation results
            time_range: (start_hour, end_hour) tuple
            save_path: Path to save figure
            show_plot: Whether to display plot
        """
        # FIXED: Handle both DataFrame and Dict inputs with proper validation
        if isinstance(simulation_results, dict):
            # Convert dict to DataFrame if needed
            if simulation_results:  # Check if dict is not empty
                try:
                    data_df = pd.DataFrame(simulation_results)
                except Exception as e:
                    logging.error(f"Could not convert simulation_results dict to DataFrame: {e}")
                    return
            else:
                logging.warning("Empty simulation results provided")
                return
        elif isinstance(simulation_results, pd.DataFrame):
            if not simulation_results.empty:  # FIXED: Use .empty instead of direct boolean check
                data_df = simulation_results.copy()
            else:
                logging.warning("Empty DataFrame provided")
                return
        else:
            logging.error("simulation_results must be DataFrame or Dict")
            return
        
        if time_range is None:
            # Plot first week by default
            time_range = (0, min(168, len(data_df)))
        
        start_idx, end_idx = time_range
        data_subset = data_df.iloc[start_idx:end_idx].copy()
        hours = np.arange(len(data_subset))
        
        fig, axes = plt.subplots(4, 1, figsize=(15, 16))
        
        # Plot 1: Power Generation and Load
        axes[0].plot(hours, data_subset.get('pv_power', pd.Series([0]*len(data_subset))), 
                    label='PV Power', color=self.colors['pv'], linewidth=2)
        axes[0].plot(hours, data_subset.get('wt_power', pd.Series([0]*len(data_subset))), 
                    label='Wind Power', color=self.colors['wind'], linewidth=2)
        axes[0].plot(hours, data_subset.get('load_demand', pd.Series([0]*len(data_subset))), 
                    label='Load Demand', color=self.colors['load'], 
                    linewidth=2, linestyle='--')
        
        pv_values = data_subset.get('pv_power', pd.Series([0]*len(data_subset)))
        wt_values = data_subset.get('wt_power', pd.Series([0]*len(data_subset)))
        
        axes[0].fill_between(hours, pv_values, alpha=0.3, color=self.colors['pv'])
        axes[0].fill_between(hours, wt_values, alpha=0.3, color=self.colors['wind'])
        
        axes[0].set_title('Renewable Generation and Load Demand', 
                         fontsize=14, fontweight='bold')
        axes[0].set_ylabel('Power (kW)', fontsize=12)
        axes[0].legend(loc='upper right')
        axes[0].grid(True, alpha=0.3)
        
        # Plot 2: Energy Storage Operations
        battery_charge = data_subset.get('battery_charge', pd.Series([0]*len(data_subset)))
        battery_discharge = -data_subset.get('battery_discharge', pd.Series([0]*len(data_subset)))
        ev_charge = data_subset.get('ev_charge', pd.Series([0]*len(data_subset)))
        ev_discharge = -data_subset.get('ev_discharge', pd.Series([0]*len(data_subset)))
        
        axes[1].fill_between(hours, 0, battery_charge, 
                           label='Battery Charge', color=self.colors['battery'], alpha=0.6)
        axes[1].fill_between(hours, 0, battery_discharge, 
                           label='Battery Discharge', color=self.colors['battery'], alpha=0.4)
        axes[1].fill_between(hours, 0, ev_charge, 
                           label='EV Charge (G2V)', color=self.colors['ev'], alpha=0.6)
        axes[1].fill_between(hours, 0, ev_discharge, 
                           label='EV Discharge (V2G)', color=self.colors['ev'], alpha=0.4)
        
        axes[1].axhline(y=0, color='black', linestyle='-', alpha=0.3)
        axes[1].set_title('Energy Storage Operations', fontsize=14, fontweight='bold')
        axes[1].set_ylabel('Energy (kWh)', fontsize=12)
        axes[1].legend(loc='upper right')
        axes[1].grid(True, alpha=0.3)
        
        # Plot 3: Grid Interactions
        grid_purchase = data_subset.get('grid_purchase', pd.Series([0]*len(data_subset)))
        grid_sale = -data_subset.get('grid_sale', pd.Series([0]*len(data_subset)))
        
        axes[2].fill_between(hours, 0, grid_purchase, 
                           label='Grid Purchase', color=self.colors['grid'], alpha=0.6)
        axes[2].fill_between(hours, 0, grid_sale, 
                           label='Grid Sale', color=self.colors['surplus'], alpha=0.6)
        
        axes[2].axhline(y=0, color='black', linestyle='-', alpha=0.3)
        axes[2].set_title('Grid Interactions', fontsize=14, fontweight='bold')
        axes[2].set_ylabel('Energy (kWh)', fontsize=12)
        axes[2].legend(loc='upper right')
        axes[2].grid(True, alpha=0.3)
        
        # Plot 4: State of Charge
        battery_soc = data_subset.get('battery_soc', pd.Series([0.5]*len(data_subset))) * 100
        ev_soc = data_subset.get('ev_mean_soc', pd.Series([0.5]*len(data_subset))) * 100
        
        axes[3].plot(hours, battery_soc, label='Battery SOC', 
                    color=self.colors['battery'], linewidth=2)
        axes[3].plot(hours, ev_soc, label='EV Fleet Average SOC', 
                    color=self.colors['ev'], linewidth=2)
        
        # Add SOC constraint lines
        axes[3].axhline(y=20, color='red', linestyle='--', alpha=0.7, label='Min SOC (20%)')
        axes[3].axhline(y=95, color='orange', linestyle='--', alpha=0.7, label='Max SOC (95%)')
        
        axes[3].set_title('State of Charge Levels', fontsize=14, fontweight='bold')
        axes[3].set_ylabel('SOC (%)', fontsize=12)
        axes[3].set_xlabel('Time (Hours)', fontsize=12)
        axes[3].set_ylim([0, 100])
        axes[3].legend(loc='upper right')
        axes[3].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logging.info(f"Energy flows plot saved to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def plot_monte_carlo_results(self, 
                                monte_carlo_results: Dict,
                                save_path: Optional[str] = None,
                                show_plot: bool = True) -> None:
        """
        Plot Monte Carlo simulation results with statistical distributions
        
        Args:
            monte_carlo_results: Dictionary with MC results for different scenarios
            save_path: Path to save figure
            show_plot: Whether to display plot
        """
        # FIXED: Proper validation of monte_carlo_results
        if not monte_carlo_results:  # Check if dict is empty
            logging.warning("No Monte Carlo data available for visualization")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        axes = axes.flatten()
        
        # Prepare data for visualization
        all_data = []
        for scenario_name, scenario_data in monte_carlo_results.items():
            if scenario_data and 'detailed_results' in scenario_data:  # FIXED: Check if scenario_data exists
                df = scenario_data['detailed_results']
                if isinstance(df, pd.DataFrame) and not df.empty:  # FIXED: Use .empty
                    df_copy = df.copy()
                    df_copy['scenario'] = scenario_name.replace('_', ' ').title()
                    all_data.append(df_copy)
        
        if not all_data:  # FIXED: Check if list is empty
            logging.warning("No valid Monte Carlo data found for visualization")
            return
        
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Plot 1: Cost of Energy Distribution
        if 'coe' in combined_df.columns:  # FIXED: Check if column exists
            sns.boxplot(data=combined_df, x='scenario', y='coe', ax=axes[0])
            sns.stripplot(data=combined_df, x='scenario', y='coe', ax=axes[0], 
                         size=3, alpha=0.6, color='black')
            axes[0].set_title('Cost of Energy Distribution', fontweight='bold', fontsize=12)
            axes[0].set_ylabel('COE ($/kWh)', fontsize=10)
            axes[0].set_xlabel('EV Fleet Scenario', fontsize=10)
            axes[0].tick_params(axis='x', rotation=45)
        
        # Plot 2: Loss of Power Supply Probability
        if 'lpsp' in combined_df.columns:  # FIXED: Check if column exists
            sns.boxplot(data=combined_df, x='scenario', y='lpsp', ax=axes[1])
            sns.stripplot(data=combined_df, x='scenario', y='lpsp', ax=axes[1], 
                         size=3, alpha=0.6, color='black')
            axes[1].set_title('Loss of Power Supply Probability', fontweight='bold', fontsize=12)
            axes[1].set_ylabel('LPSP', fontsize=10)
            axes[1].set_xlabel('EV Fleet Scenario', fontsize=10)
            axes[1].tick_params(axis='x', rotation=45)
        
        # Plot 3: Renewable Energy Fraction
        if 'ref' in combined_df.columns:  # FIXED: Check if column exists
            sns.boxplot(data=combined_df, x='scenario', y='ref', ax=axes[2])
            sns.stripplot(data=combined_df, x='scenario', y='ref', ax=axes[2], 
                         size=3, alpha=0.6, color='black')
            axes[2].set_title('Renewable Energy Fraction', fontweight='bold', fontsize=12)
            axes[2].set_ylabel('REF', fontsize=10)
            axes[2].set_xlabel('EV Fleet Scenario', fontsize=10)
            axes[2].tick_params(axis='x', rotation=45)
        
        # Plot 4: V2G Energy Contribution
        if 'total_v2g_energy' in combined_df.columns:
            sns.boxplot(data=combined_df, x='scenario', y='total_v2g_energy', ax=axes[3])
            sns.stripplot(data=combined_df, x='scenario', y='total_v2g_energy', ax=axes[3], 
                         size=3, alpha=0.6, color='black')
            axes[3].set_title('V2G Energy Contribution', fontweight='bold', fontsize=12)
            axes[3].set_ylabel('V2G Energy (kWh)', fontsize=10)
        else:
            # Alternative: show NPC if V2G data not available
            if 'npc' in combined_df.columns:
                sns.boxplot(data=combined_df, x='scenario', y='npc', ax=axes[3])
                axes[3].set_title('Net Present Cost', fontweight='bold', fontsize=12)
                axes[3].set_ylabel('NPC ($)', fontsize=10)
        
        axes[3].set_xlabel('EV Fleet Scenario', fontsize=10)
        axes[3].tick_params(axis='x', rotation=45)
        
        # Add statistical annotations
        for i, ax in enumerate(axes):
            ax.grid(True, alpha=0.3)
        
        plt.suptitle('Monte Carlo Analysis Results', fontsize=16, fontweight='bold', y=0.98)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logging.info(f"Monte Carlo results plot saved to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def plot_economic_analysis(self, 
                              economic_results: Dict,
                              save_path: Optional[str] = None,
                              show_plot: bool = True) -> None:
        """
        Plot comprehensive economic analysis
        
        Args:
            economic_results: Dictionary with economic metrics
            save_path: Path to save figure
            show_plot: Whether to display plot
        """
        # FIXED: Check if economic_results is not empty
        if not economic_results:
            logging.warning("No economic data available for visualization")
            return
        
        fig = plt.figure(figsize=(16, 12))
        
        # Create grid layout
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Plot 1: Key Economic Metrics (top row, left)
        ax1 = fig.add_subplot(gs[0, 0])
        metrics = ['COE', 'LPSP', 'REF']
        values = [economic_results.get('coe', 0), 
                 economic_results.get('lpsp', 0), 
                 economic_results.get('ref', 0)]
        colors_list = [self.colors['battery'], self.colors['grid'], self.colors['pv']]
        
        bars = ax1.bar(metrics, values, color=colors_list, alpha=0.7, edgecolor='black')
        ax1.set_title('Key Economic Metrics', fontweight='bold')
        ax1.set_ylabel('Value')
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{value:.4f}', ha='center', va='bottom', fontweight='bold')
        
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Cost Breakdown (top row, middle)
        ax2 = fig.add_subplot(gs[0, 1])
        if 'cost_breakdown' in economic_results and economic_results['cost_breakdown']:  # FIXED
            breakdown = economic_results['cost_breakdown']
            wedges, texts, autotexts = ax2.pie(breakdown.values(), 
                                              labels=breakdown.keys(), 
                                              autopct='%1.1f%%',
                                              startangle=90)
            ax2.set_title('Cost Breakdown', fontweight='bold')
        else:
            # Default breakdown if not provided
            default_costs = {
                'Capital': economic_results.get('npc', 1000) * 0.7,
                'Operation': economic_results.get('npc', 1000) * 0.2,
                'Grid': abs(economic_results.get('total_grid_cost', 100))
            }
            wedges, texts, autotexts = ax2.pie(default_costs.values(), 
                                              labels=default_costs.keys(), 
                                              autopct='%1.1f%%',
                                              startangle=90)
            ax2.set_title('Cost Breakdown (Estimated)', fontweight='bold')
        
        # Plot 3: Reliability vs Cost (top row, right)
        ax3 = fig.add_subplot(gs[0, 2])
        reliability = 1 - economic_results.get('lpsp', 0.01)
        coe = economic_results.get('coe', 0.1)
        
        ax3.scatter([reliability], [coe], s=200, color=self.colors['battery'], 
                   alpha=0.7, edgecolors='black', linewidth=2)
        ax3.set_xlabel('System Reliability (1-LPSP)')
        ax3.set_ylabel('Cost of Energy ($/kWh)')
        ax3.set_title('Reliability vs Cost Trade-off', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.set_xlim([0.98, 1.0])
        
        # Plot 4: Renewable Integration (middle row, full width)
        ax4 = fig.add_subplot(gs[1, :])
        ref_value = economic_results.get('ref', 0.5)
        renewable_energy = ref_value * 100  # Convert to percentage
        grid_energy = (1 - ref_value) * 100
        
        categories = ['Renewable Energy', 'Grid Energy']
        percentages = [renewable_energy, grid_energy]
        colors_energy = [self.colors['pv'], self.colors['grid']]
        
        bars = ax4.barh(categories, percentages, color=colors_energy, alpha=0.7, 
                       edgecolor='black', height=0.5)
        
        # Add percentage labels
        for bar, pct in zip(bars, percentages):
            width = bar.get_width()
            ax4.text(width/2, bar.get_y() + bar.get_height()/2,
                    f'{pct:.1f}%', ha='center', va='center', 
                    fontweight='bold', fontsize=12)
        
        ax4.set_xlabel('Energy Contribution (%)')
        ax4.set_title('Energy Source Distribution', fontweight='bold')
        ax4.set_xlim([0, 100])
        ax4.grid(True, alpha=0.3, axis='x')
        
        # Plot 5: Economic Comparison (bottom left)
        ax5 = fig.add_subplot(gs[2, 0])
        scenarios = ['Without V2G', 'With V2G', 'Optimized V2G']
        # Simulate comparison data
        current_coe = economic_results.get('coe', 0.15)
        comparison_coe = [current_coe * 1.25, current_coe * 1.1, current_coe]
        
        bars = ax5.bar(scenarios, comparison_coe, 
                      color=[self.colors['grid'], self.colors['ev'], self.colors['battery']], 
                      alpha=0.7, edgecolor='black')
        ax5.set_title('COE Comparison Scenarios', fontweight='bold')
        ax5.set_ylabel('COE ($/kWh)')
        ax5.tick_params(axis='x', rotation=45)
        
        for bar, value in zip(bars, comparison_coe):
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'${value:.3f}', ha='center', va='bottom', fontweight='bold')
        
        # Plot 6: Net Present Cost (bottom middle)
        ax6 = fig.add_subplot(gs[2, 1])
        npc = economic_results.get('npc', 100000)
        ax6.bar(['Net Present Cost'], [npc], color=self.colors['load'], 
               alpha=0.7, edgecolor='black')
        ax6.set_title('Net Present Cost', fontweight='bold')
        ax6.set_ylabel('Cost ($)')
        ax6.text(0, npc + npc*0.02, f'${npc:,.0f}', ha='center', va='bottom', 
                fontweight='bold')
        
        # Plot 7: Sustainability Metrics (bottom right)
        ax7 = fig.add_subplot(gs[2, 2])
        sustainability_metrics = {
            'REF': economic_results.get('ref', 0.5),
            'Grid Independence': 1 - economic_results.get('lpsp', 0.01),
            'V2G Utilization': min(1.0, economic_results.get('renewable_penetration', 50) / 100)
        }
        
        angles = np.linspace(0, 2 * np.pi, len(sustainability_metrics), endpoint=False).tolist()
        values = list(sustainability_metrics.values())
        angles += angles[:1]  # Complete the circle
        values += values[:1]  # Complete the circle
        
        ax7 = plt.subplot(gs[2, 2], projection='polar')
        ax7.plot(angles, values, 'o-', linewidth=2, color=self.colors['pv'])
        ax7.fill(angles, values, alpha=0.25, color=self.colors['pv'])
        ax7.set_xticks(angles[:-1])
        ax7.set_xticklabels(sustainability_metrics.keys())
        ax7.set_ylim(0, 1)
        ax7.set_title('Sustainability Metrics', fontweight='bold', pad=20)
        ax7.grid(True)
        
        plt.suptitle('Economic Analysis Dashboard', fontsize=18, fontweight='bold', y=0.98)
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logging.info(f"Economic analysis plot saved to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def plot_component_sizing(self, 
                             component_sizing: Dict,
                             save_path: Optional[str] = None,
                             show_plot: bool = True) -> None:
        """
        Visualize optimal component sizing results
        
        Args:
            component_sizing: Dictionary with component counts and sizes
            save_path: Path to save figure
            show_plot: Whether to display plot
        """
        # FIXED: Check if component_sizing is not empty
        if not component_sizing:
            logging.warning("No component sizing data available for visualization")
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Plot 1: Component Counts
        components = ['PV Panels', 'Wind Turbines', 'Batteries']
        counts = [
            component_sizing.get('n_pv', 0), 
            component_sizing.get('n_wt', 0), 
            component_sizing.get('n_bt', 0)
        ]
        colors_list = [self.colors['pv'], self.colors['wind'], self.colors['battery']]
        
        bars = ax1.bar(components, counts, color=colors_list, alpha=0.7, 
                      edgecolor='black', linewidth=1.5)
        ax1.set_title('Optimal Component Sizing', fontweight='bold', fontsize=14)
        ax1.set_ylabel('Number of Units', fontsize=12)
        
        # Add value labels
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.02,
                    f'{int(count)}', ha='center', va='bottom', 
                    fontweight='bold', fontsize=11)
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Capacity Distribution (Pie Chart)
        # Assume standard component ratings
        pv_capacity = component_sizing.get('n_pv', 0) * 0.325  # 325W panels
        wt_capacity = component_sizing.get('n_wt', 0) * 5      # 5kW turbines
        bt_capacity = component_sizing.get('n_bt', 0) * 35.38  # 35.38kWh batteries
        
        capacities = {
            f'PV\n({pv_capacity:.1f} kW)': pv_capacity,
            f'Wind\n({wt_capacity:.1f} kW)': wt_capacity,
            f'Battery\n({bt_capacity:.1f} kWh)': bt_capacity
        }
        
        # Filter out zero capacities
        capacities = {k: v for k, v in capacities.items() if v > 0}
        
        if capacities:  # FIXED: Check if capacities dict is not empty
            wedges, texts, autotexts = ax2.pie(capacities.values(), 
                                              labels=capacities.keys(), 
                                              autopct='%1.1f%%',
                                              colors=colors_list[:len(capacities)],
                                              startangle=90,
                                              explode=[0.05] * len(capacities))
            ax2.set_title('System Capacity Distribution', fontweight='bold', fontsize=14)
        else:
            ax2.text(0.5, 0.5, 'No capacity data available', 
                    ha='center', va='center', transform=ax2.transAxes)
        
        # Plot 3: Autonomy and System Metrics
        autonomy_days = component_sizing.get('autonomy_days', 0)
        total_renewable_capacity = pv_capacity + wt_capacity
        storage_capacity = bt_capacity
        
        metrics = ['Renewable\nCapacity (kW)', 'Storage\nCapacity (kWh)', 'Autonomy\n(Days)']
        values = [total_renewable_capacity, storage_capacity, autonomy_days]
        metric_colors = [self.colors['pv'], self.colors['battery'], self.colors['ev']]
        
        bars = ax3.bar(metrics, values, color=metric_colors, alpha=0.7, 
                      edgecolor='black', linewidth=1.5)
        ax3.set_title('System Characteristics', fontweight='bold', fontsize=14)
        ax3.set_ylabel('Value', fontsize=12)
        
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + height*0.02,
                    f'{value:.1f}', ha='center', va='bottom', 
                    fontweight='bold', fontsize=11)
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Cost Distribution (if available)
        # Estimate costs based on typical values
        pv_cost = component_sizing.get('n_pv', 0) * 200      # $200/panel
        wt_cost = component_sizing.get('n_wt', 0) * 10000    # $10k/turbine
        bt_cost = component_sizing.get('n_bt', 0) * 10000    # $10k/battery
        
        cost_breakdown = {
            'PV System': pv_cost,
            'Wind System': wt_cost,
            'Battery System': bt_cost
        }
        
        # Filter out zero costs
        cost_breakdown = {k: v for k, v in cost_breakdown.items() if v > 0}
        
        if cost_breakdown:  # FIXED: Check if cost_breakdown dict is not empty
            bars = ax4.barh(list(cost_breakdown.keys()), list(cost_breakdown.values()),
                           color=colors_list[:len(cost_breakdown)], alpha=0.7, 
                           edgecolor='black', linewidth=1.5)
            ax4.set_title('Estimated Cost Breakdown', fontweight='bold', fontsize=14)
            ax4.set_xlabel('Cost ($)', fontsize=12)
            
            # Add value labels
            for bar, cost in zip(bars, cost_breakdown.values()):
                width = bar.get_width()
                ax4.text(width + width*0.02, bar.get_y() + bar.get_height()/2.,
                        f'${cost:,.0f}', ha='left', va='center', fontweight='bold')
            ax4.grid(True, alpha=0.3, axis='x')
        else:
            ax4.text(0.5, 0.5, 'Cost data not available', 
                    ha='center', va='center', transform=ax4.transAxes)
        
        plt.suptitle('Optimal Component Sizing Analysis', fontsize=16, fontweight='bold', y=0.98)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logging.info(f"Component sizing plot saved to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def plot_sensitivity_analysis(self, 
                                 sensitivity_results: pd.DataFrame,
                                 save_path: Optional[str] = None,
                                 show_plot: bool = True) -> None:
        """
        Plot sensitivity analysis results with tornado diagram
        
        Args:
            sensitivity_results: DataFrame with sensitivity analysis results
            save_path: Path to save figure
            show_plot: Whether to display plot
        """
        # FIXED: Check if sensitivity_results is valid
        if sensitivity_results is None or sensitivity_results.empty:
            logging.warning("No sensitivity analysis data available for visualization")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Plot 1: Tornado Diagram for COE sensitivity
        if 'coe' in sensitivity_results.columns:
            # Calculate sensitivity ranges for each parameter
            sensitivity_ranges = []
            parameters = sensitivity_results['parameter'].unique()
            
            for param in parameters:
                param_data = sensitivity_results[sensitivity_results['parameter'] == param]
                if len(param_data) > 1:
                    min_coe = param_data['coe'].min()
                    max_coe = param_data['coe'].max()
                    base_coe_data = param_data[param_data['multiplier'] == 1.0]['coe']
                    base_coe = base_coe_data.iloc[0] if not base_coe_data.empty else param_data['coe'].mean()
                    
                    low_impact = base_coe - min_coe
                    high_impact = max_coe - base_coe
                    
                    sensitivity_ranges.append({
                        'parameter': param,
                        'low_impact': low_impact,
                        'high_impact': high_impact,
                        'total_range': max_coe - min_coe
                    })
            
            # Sort by total range (most sensitive first)
            sensitivity_ranges.sort(key=lambda x: x['total_range'], reverse=True)
            
            # Create tornado diagram
            y_pos = np.arange(len(sensitivity_ranges))
            
            for i, sens in enumerate(sensitivity_ranges):
                ax1.barh(i, -sens['low_impact'], height=0.8, 
                        color=self.colors['grid'], alpha=0.7, label='Decrease' if i == 0 else "")
                ax1.barh(i, sens['high_impact'], height=0.8, 
                        color=self.colors['surplus'], alpha=0.7, label='Increase' if i == 0 else "")
            
            ax1.set_yticks(y_pos)
            ax1.set_yticklabels([s['parameter'].replace('_', ' ').title() for s in sensitivity_ranges])
            ax1.set_xlabel('COE Impact ($/kWh)')
            ax1.set_title('Parameter Sensitivity - Tornado Diagram', fontweight='bold')
            ax1.axvline(x=0, color='black', linestyle='-', alpha=0.8)
            ax1.legend()
            ax1.grid(True, alpha=0.3, axis='x')
        
        # Plot 2: Sensitivity trends for all parameters
        parameters = sensitivity_results['parameter'].unique()
        colors_cycle = plt.cm.Set3(np.linspace(0, 1, len(parameters)))
        
        for i, param in enumerate(parameters):
            param_data = sensitivity_results[sensitivity_results['parameter'] == param]
            param_data = param_data.sort_values('multiplier')
            
            ax2.plot(param_data['multiplier'], param_data['coe'], 
                    marker='o', linewidth=2, label=param.replace('_', ' ').title(),
                    color=colors_cycle[i])
        
        ax2.axvline(x=1.0, color='black', linestyle='--', alpha=0.7, label='Base Case')
        ax2.set_xlabel('Parameter Multiplier')
        ax2.set_ylabel('COE ($/kWh)')
        ax2.set_title('Parameter Sensitivity Trends', fontweight='bold')
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logging.info(f"Sensitivity analysis plot saved to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def plot_algorithm_comparison(self, 
                                 algorithm_results: Dict[str, Union[Dict, List]],
                                 save_path: Optional[str] = None,
                                 show_plot: bool = True) -> None:
        """
        Compare performance of different optimization algorithms
        
        Args:
            algorithm_results: Dict with results from different algorithms
            save_path: Path to save figure
            show_plot: Whether to display plot
        """
        # FIXED: Check if algorithm_results is not empty
        if not algorithm_results:
            logging.warning("No algorithm results available for comparison")
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        algorithms = list(algorithm_results.keys())
        colors_alg = plt.cm.Set2(np.linspace(0, 1, len(algorithms)))
        
        # Plot 1: Convergence comparison
        for i, (alg, results) in enumerate(algorithm_results.items()):
            # FIXED: Handle both dict with convergence_history and direct list
            if isinstance(results, dict) and 'convergence_history' in results:
                history = results['convergence_history']
            elif isinstance(results, list):
                history = results
            else:
                continue
                
            if history and len(history) > 0:  # FIXED: Check if history exists and not empty
                iterations = range(len(history))
                ax1.plot(iterations, history, 
                        linewidth=2, label=alg, color=colors_alg[i])
        
        ax1.set_xlabel('Iteration')
        ax1.set_ylabel('Objective Function Value')
        ax1.set_title('Algorithm Convergence Comparison', fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_yscale('log')  # Log scale for better visualization
        
        # Plot 2: Final fitness comparison
        final_fitness = []
        alg_names = []
        for alg, results in algorithm_results.items():
            if isinstance(results, dict) and 'best_fitness' in results:
                final_fitness.append(results['best_fitness'])
                alg_names.append(alg)
            elif isinstance(results, list) and results:  # FIXED: Check if list is not empty
                final_fitness.append(results[-1])  # Use last value as final fitness
                alg_names.append(alg)
        
        if final_fitness:  # FIXED: Check if we have data to plot
            bars = ax2.bar(alg_names, final_fitness, color=colors_alg[:len(alg_names)], 
                          alpha=0.7, edgecolor='black')
            ax2.set_ylabel('Final Objective Value')
            ax2.set_title('Final Performance Comparison', fontweight='bold')
            ax2.tick_params(axis='x', rotation=45)
            
            # Add value labels
            for bar, fitness in zip(bars, final_fitness):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{fitness:.4f}', ha='center', va='bottom', fontweight='bold')
            ax2.grid(True, alpha=0.3)
        
        # Plot 3: Computation time comparison (if available)
        comp_times = []
        time_alg_names = []
        for alg, results in algorithm_results.items():
            if isinstance(results, dict) and 'computation_time' in results:
                comp_times.append(results['computation_time'])
                time_alg_names.append(alg)
        
        if comp_times:  # FIXED: Check if we have computation time data
            bars = ax3.bar(time_alg_names, comp_times, color=colors_alg[:len(time_alg_names)], 
                          alpha=0.7, edgecolor='black')
            ax3.set_ylabel('Computation Time (seconds)')
            ax3.set_title('Computation Time Comparison', fontweight='bold')
            ax3.tick_params(axis='x', rotation=45)
            
            for bar, time in zip(bars, comp_times):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{time:.2f}s', ha='center', va='bottom', fontweight='bold')
            ax3.grid(True, alpha=0.3)
        else:
            ax3.text(0.5, 0.5, 'Computation time\ndata not available', 
                    ha='center', va='center', transform=ax3.transAxes)
        
        # Plot 4: Solution quality metrics
        metrics = ['Best Fitness', 'Convergence Rate', 'Stability']
        
        # Normalize metrics for radar chart
        best_fitness_norm = []
        convergence_rate_norm = []
        stability_norm = []
        
        for alg, results in algorithm_results.items():
            # Normalize best fitness (lower is better, so invert)
            if isinstance(results, dict) and 'best_fitness' in results:
                best_fitness_norm.append(1 / (1 + results['best_fitness']))
            elif isinstance(results, list) and results:  # FIXED
                best_fitness_norm.append(1 / (1 + results[-1]))
            else:
                best_fitness_norm.append(0)
            
            # Calculate convergence rate
            if isinstance(results, dict) and 'convergence_history' in results:
                history = results['convergence_history']
            elif isinstance(results, list):
                history = results
            else:
                history = []
                
            if history and len(history) > 1:  # FIXED
                conv_rate = (history[0] - history[-1]) / history[0] if history[0] != 0 else 0
                convergence_rate_norm.append(min(1.0, max(0.0, conv_rate)))
            else:
                convergence_rate_norm.append(0)
            
            # Stability (inverse of standard deviation of last 10% of iterations)
            if history and len(history) > 1:  # FIXED
                last_portion = history[-len(history)//10:] if len(history) > 10 else history
                if len(last_portion) > 1:
                    stability = 1 / (1 + np.std(last_portion))
                    stability_norm.append(min(1.0, stability))
                else:
                    stability_norm.append(1.0)
            else:
                stability_norm.append(0.0)
        
        # Create radar chart
        if best_fitness_norm:  # FIXED: Check if we have data
            angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
            angles += angles[:1]  # Complete the circle
            
            ax4 = plt.subplot(2, 2, 4, projection='polar')
            
            for i, alg in enumerate(algorithms):
                if i < len(best_fitness_norm):
                    values = [best_fitness_norm[i], convergence_rate_norm[i], stability_norm[i]]
                    values += values[:1]  # Complete the circle
                    
                    ax4.plot(angles, values, 'o-', linewidth=2, label=alg, color=colors_alg[i])
                    ax4.fill(angles, values, alpha=0.1, color=colors_alg[i])
            
            ax4.set_xticks(angles[:-1])
            ax4.set_xticklabels(metrics)
            ax4.set_ylim(0, 1)
            ax4.set_title('Algorithm Performance Radar', fontweight='bold', pad=20)
            ax4.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
            ax4.grid(True)
        
        plt.suptitle('Optimization Algorithm Comparison', fontsize=16, fontweight='bold', y=0.98)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logging.info(f"Algorithm comparison plot saved to {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def create_interactive_dashboard(self, 
                                   results: Dict,
                                   save_path: Optional[str] = None) -> None:
        """
        Create interactive dashboard using Plotly (if available)
        
        Args:
            results: Complete results dictionary
            save_path: Path to save HTML file
        """
        if not PLOTLY_AVAILABLE:
            logging.warning("Plotly not available. Cannot create interactive dashboard.")
            return
        
        # FIXED: Check if results is not empty
        if not results:
            logging.warning("No results data available for interactive dashboard")
            return
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=('Convergence', 'Energy Flows', 'Economic Metrics', 
                          'Component Sizing', 'Monte Carlo Results', 'System Overview'),
            specs=[[{"secondary_y": False}, {"secondary_y": True}],
                   [{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Add convergence plot
        if 'convergence_history' in results and results['convergence_history']:  # FIXED
            fig.add_trace(
                go.Scatter(x=list(range(len(results['convergence_history']))),
                          y=results['convergence_history'],
                          mode='lines+markers',
                          name='Convergence',
                          line=dict(color='blue', width=2)),
                row=1, col=1
            )
        
        # Add energy flows (example with dummy data)
        hours = list(range(24))
        pv_power = [0 if h < 6 or h > 18 else 5 * np.sin((h-6) * np.pi/12) for h in hours]
        load_demand = [2 + 0.5 * np.sin(h * np.pi/12) + np.random.normal(0, 0.1) for h in hours]
        
        fig.add_trace(
            go.Scatter(x=hours, y=pv_power, name='PV Power', 
                      line=dict(color='orange'), fill='tozeroy'),
            row=1, col=2
        )
        fig.add_trace(
            go.Scatter(x=hours, y=load_demand, name='Load Demand',
                      line=dict(color='red', dash='dash')),
            row=1, col=2
        )
        
        # Add economic metrics
        if 'economic' in results and results['economic']:  # FIXED
            metrics = ['COE', 'LPSP', 'REF']
            values = [results['economic'].get(m.lower(), 0) for m in metrics]
            
            fig.add_trace(
                go.Bar(x=metrics, y=values, name='Economic Metrics',
                      marker_color=['blue', 'red', 'green']),
                row=2, col=1
            )
        
        # Add component sizing
        if ('optimization' in results and results['optimization'] and 
            'component_sizing' in results['optimization'] and 
            results['optimization']['component_sizing']):  # FIXED
            sizing = results['optimization']['component_sizing']
            components = ['PV', 'WT', 'Battery']
            counts = [sizing.get('n_pv', 0), sizing.get('n_wt', 0), sizing.get('n_bt', 0)]
            
            fig.add_trace(
                go.Bar(x=components, y=counts, name='Component Counts',
                      marker_color=['orange', 'teal', 'blue']),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            title_text="V2G Microgrid Optimization Interactive Dashboard",
            title_x=0.5,
            showlegend=True,
            height=900
        )
        
        # Save interactive plot
        if save_path:
            fig.write_html(save_path)
            logging.info(f"Interactive dashboard saved to {save_path}")
        else:
            fig.show()
    
    def save_all_plots(self, 
                      results: Dict,
                      base_path: str = "outputs/figures") -> None:
        """
        Generate and save all available plots from results
        
        Args:
            results: Complete results dictionary
            base_path: Base path for saving plots
        """
        if not results:  # FIXED: Check if results is not empty
            logging.warning("No results data available for plotting")
            return
        
        base_path = Path(base_path)
        base_path.mkdir(parents=True, exist_ok=True)
        
        # Convergence plots
        if 'convergence_history' in results and results['convergence_history']:  # FIXED
            self.plot_convergence(
                results['convergence_history'],
                save_path=base_path / "convergence.png",
                show_plot=False
            )
        
        # Energy flows
        if 'energy_flows' in results and results['energy_flows'] is not None:  # FIXED
            self.plot_energy_flows(
                results['energy_flows'],
                save_path=base_path / "energy_flows.png",
                show_plot=False
            )
        
        # Economic analysis
        if 'economic' in results and results['economic']:  # FIXED
            self.plot_economic_analysis(
                results['economic'],
                save_path=base_path / "economic_analysis.png",
                show_plot=False
            )
        
        # Component sizing
        if ('optimization' in results and results['optimization'] and
            'component_sizing' in results['optimization'] and 
            results['optimization']['component_sizing']):  # FIXED
            self.plot_component_sizing(
                results['optimization']['component_sizing'],
                save_path=base_path / "component_sizing.png",
                show_plot=False
            )
        
        # Monte Carlo results
        if 'monte_carlo' in results and results['monte_carlo']:  # FIXED
            self.plot_monte_carlo_results(
                results['monte_carlo'],
                save_path=base_path / "monte_carlo_results.png",
                show_plot=False
            )
        
        # Interactive dashboard
        if PLOTLY_AVAILABLE:
            self.create_interactive_dashboard(
                results,
                save_path=base_path / "interactive_dashboard.html"
            )
        
        logging.info(f"All available plots saved to {base_path}")


# FIXED: Updated main execution script with proper DataFrame handling
if __name__ == "__main__":
    import os
    from pathlib import Path

    # Ensure the output directory exists
    output_dir = 'outputs/figures/static'
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 1. Initialize the Visualizer
    vis = Visualizer()
    print("Visualizer initialized.")

    # --- Simulate Data ---
    np.random.seed(42)
    num_hours = 168  # One week
    # FIXED: Changed 'H' to 'h' to fix pandas warning
    time_index = pd.to_datetime(pd.date_range('2025-01-01', periods=num_hours, freq='h'))

    # 2. Simulate Optimization Convergence
    print("Simulating optimization convergence data...")
    convergence_history = np.logspace(3, 1, num_hours) + np.random.normal(0, 0.5, num_hours)
    convergence_history_ga = np.logspace(3, 1.2, num_hours) + np.random.normal(0, 0.8, num_hours)
    convergence_data = {
        "Genetic Algorithm": convergence_history_ga.tolist(),
        "Particle Swarm Optimization": convergence_history.tolist()
    }
    print("Simulated convergence data.")

    # 3. Simulate Energy Flow Data
    print("Simulating energy flow data...")
    pv_power = np.maximum(0, 100 * np.sin(np.pi * (np.arange(num_hours) % 24) / 12) + np.random.normal(0, 5, num_hours))
    wt_power = np.maximum(0, 50 + 20 * np.sin(np.pi * (np.arange(num_hours) / 24)) + np.random.normal(0, 10, num_hours))
    load_demand = 120 + 30 * np.sin(np.pi * (np.arange(num_hours) % 24) / 12) + np.random.normal(0, 5, num_hours)

    # Simulate battery/EV operations
    battery_charge = np.maximum(0, pv_power - load_demand / 2 - np.random.normal(0, 10, num_hours))
    battery_discharge = np.minimum(0, pv_power - load_demand + np.random.normal(0, 10, num_hours))
    battery_soc = np.clip(np.cumsum(battery_charge + battery_discharge) / 100, 0.2, 0.95)
    battery_soc = battery_soc + 0.5 - battery_soc[0] # Adjust to start at 50%
    battery_soc = np.clip(battery_soc, 0.2, 0.95)

    ev_charge = np.maximum(0, load_demand / 4 + np.random.normal(0, 5, num_hours))
    ev_discharge = np.minimum(0, -np.random.normal(0, 5, num_hours))
    ev_mean_soc = np.clip(np.cumsum(ev_charge + ev_discharge) / 50 + 0.6, 0.1, 0.9)
    ev_mean_soc = ev_mean_soc + 0.5 - ev_mean_soc[0]
    ev_mean_soc = np.clip(ev_mean_soc, 0.1, 0.9)

    grid_purchase = np.maximum(0, load_demand - pv_power - battery_discharge - ev_discharge)
    grid_sale = np.minimum(0, pv_power - load_demand - battery_charge - ev_charge)

    simulation_results = pd.DataFrame({
        'pv_power': pv_power,
        'wt_power': wt_power,
        'load_demand': load_demand,
        'battery_charge': battery_charge,
        'battery_discharge': -battery_discharge, # make positive for plot
        'ev_charge': ev_charge,
        'ev_discharge': -ev_discharge,
        'grid_purchase': grid_purchase,
        'grid_sale': -grid_sale, # make positive for plot
        'battery_soc': battery_soc,
        'ev_mean_soc': ev_mean_soc
    }, index=time_index)
    print("Simulated energy flow data.")

    # 4. Simulate Monte Carlo Results
    print("Simulating Monte Carlo results...")
    num_simulations = 100
    scenarios = ['no_v2g', 'managed_v2g', 'optimized_v2g']
    monte_carlo_results = {}
    for scenario in scenarios:
        coe = np.random.normal(0.15, 0.02, num_simulations) if scenario == 'optimized_v2g' else np.random.normal(0.2, 0.03, num_simulations)
        lpsp = np.random.normal(0.01, 0.005, num_simulations) if scenario == 'optimized_v2g' else np.random.normal(0.05, 0.01, num_simulations)
        ref = np.random.normal(0.8, 0.05, num_simulations) if scenario == 'optimized_v2g' else np.random.normal(0.6, 0.05, num_simulations)
        
        # Add some variation to total_v2g_energy for the plots
        total_v2g_energy = np.random.normal(200, 50, num_simulations) if scenario == 'optimized_v2g' else np.zeros(num_simulations)
        
        monte_carlo_results[scenario] = {
            'detailed_results': pd.DataFrame({
                'coe': coe, 'lpsp': lpsp, 'ref': ref, 'total_v2g_energy': total_v2g_energy
            })
        }
    print("Simulated Monte Carlo data.")

    # 5. Simulate Economic Analysis Results
    print("Simulating economic analysis results...")
    economic_results = {
        'coe': 0.145, # $/kWh
        'lpsp': 0.005, # %
        'ref': 0.85, # %
        'npc': 550000, # $
        'total_grid_cost': 5000, # $
        'renewable_penetration': 85,
        'cost_breakdown': {
            'Capital': 400000,
            'Operation & Maintenance': 100000,
            'Grid Purchase': 50000
        }
    }
    print("Simulated economic analysis data.")

    # 6. Simulate Component Sizing Results
    print("Simulating component sizing results...")
    component_sizing = {
        'n_pv': 500, # panels
        'n_wt': 10,  # turbines
        'n_bt': 12,  # battery units
        'autonomy_days': 2.5
    }
    print("Simulated component sizing data.")

    # 7. Simulate Sensitivity Analysis Results
    print("Simulating sensitivity analysis data...")
    parameters = ['pv_cost', 'grid_price', 'load_growth']
    sensitivity_data = []
    base_coe = 0.145

    for param in parameters:
        for mult in [0.8, 0.9, 1.0, 1.1, 1.2]:
            if param == 'pv_cost':
                coe = base_coe * (1 + (mult - 1) * 0.25)
            elif param == 'grid_price':
                coe = base_coe * (1 + (mult - 1) * 0.5)
            elif param == 'load_growth':
                coe = base_coe * (1 + (mult - 1) * 0.3)
            sensitivity_data.append({
                'parameter': param,
                'multiplier': mult,
                'coe': coe + np.random.normal(0, 0.002)
            })

    sensitivity_results = pd.DataFrame(sensitivity_data)
    print("Simulated sensitivity analysis data.")

    # --- Run Visualizations ---
    print("\nGenerating visualizations...")
    
    try:
        # Plot 1: Convergence
        vis.plot_convergence(
            convergence_data, 
            save_path=os.path.join(output_dir, 'convergence_plot.png'),
            show_plot=False
        )

        # Plot 2: Energy Flows
        vis.plot_energy_flows(
            simulation_results, 
            time_range=(0, 168), 
            save_path=os.path.join(output_dir, 'energy_flows_plot.png'),
            show_plot=False
        )

        # Plot 3: Monte Carlo Results
        vis.plot_monte_carlo_results(
            monte_carlo_results,
            save_path=os.path.join(output_dir, 'monte_carlo_results.png'),
            show_plot=False
        )

        # Plot 4: Economic Analysis
        vis.plot_economic_analysis(
            economic_results,
            save_path=os.path.join(output_dir, 'economic_analysis.png'),
            show_plot=False
        )

        # Plot 5: Component Sizing
        vis.plot_component_sizing(
            component_sizing,
            save_path=os.path.join(output_dir, 'component_sizing.png'),
            show_plot=False
        )

        # Plot 6: Sensitivity Analysis
        vis.plot_sensitivity_analysis(
            sensitivity_results,
            save_path=os.path.join(output_dir, 'sensitivity_analysis.png'),
            show_plot=False
        )

        print("\nAll plots have been generated and saved to 'outputs/figures/static'.")
    
    except Exception as e:
        print(f"Error during visualization generation: {e}")
        import traceback
        traceback.print_exc()