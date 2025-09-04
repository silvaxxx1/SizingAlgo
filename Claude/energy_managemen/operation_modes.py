
# energy_management/operation_modes.py
from enum import Enum
from typing import Dict, Any

class OperationMode(Enum):
    """
    Energy Management System operation modes
    Based on MATLAB EMS logic
    """
    MODE_1_RENEWABLE_DIRECT = "renewable_direct_supply"
    MODE_2_BATTERY_DISCHARGE = "battery_discharge"
    MODE_3_GRID_PURCHASE = "grid_purchase"
    MODE_4_V2G_DISCHARGE = "vehicle_to_grid"
    MODE_5_SURPLUS_STORAGE = "surplus_storage"
    MODE_6_SURPLUS_EXPORT = "surplus_export"


class OperationModeManager:
    """
    Manages operation mode transitions and logic
    """
    
    def __init__(self):
        self.current_mode = None
        self.mode_history = []
        self.transition_rules = self._define_transition_rules()
    
    def _define_transition_rules(self) -> Dict:
        """Define rules for mode transitions"""
        return {
            'renewable_surplus': {
                'battery_not_full': OperationMode.MODE_5_SURPLUS_STORAGE,
                'battery_full_grid_available': OperationMode.MODE_6_SURPLUS_EXPORT,
                'battery_full_no_grid': OperationMode.MODE_1_RENEWABLE_DIRECT
            },
            'renewable_deficit': {
                'battery_available': OperationMode.MODE_2_BATTERY_DISCHARGE,
                'ev_available': OperationMode.MODE_4_V2G_DISCHARGE,
                'grid_available': OperationMode.MODE_3_GRID_PURCHASE
            }
        }
    
    def determine_mode(self, system_state: Dict[str, Any]) -> OperationMode:
        """
        Determine optimal operation mode based on system state
        
        Args:
            system_state: Dictionary with current system conditions
            
        Returns:
            Recommended operation mode
        """
        renewable_power = system_state.get('renewable_power', 0)
        load_demand = system_state.get('load_demand', 0)
        battery_soc = system_state.get('battery_soc', 0.5)
        ev_available = system_state.get('ev_available', False)
        grid_available = system_state.get('grid_available', True)
        
        net_power = renewable_power - load_demand
        
        if net_power > 0:  # Surplus power
            if battery_soc < 0.95:  # Battery not full
                mode = OperationMode.MODE_5_SURPLUS_STORAGE
            elif grid_available:
                mode = OperationMode.MODE_6_SURPLUS_EXPORT
            else:
                mode = OperationMode.MODE_1_RENEWABLE_DIRECT
        else:  # Power deficit
            if battery_soc > 0.25:  # Battery has energy
                mode = OperationMode.MODE_2_BATTERY_DISCHARGE
            elif ev_available and system_state.get('ev_soc', 0) > 0.3:
                mode = OperationMode.MODE_4_V2G_DISCHARGE
            elif grid_available:
                mode = OperationMode.MODE_3_GRID_PURCHASE
            else:
                mode = OperationMode.MODE_2_BATTERY_DISCHARGE  # Emergency
        
        self.current_mode = mode
        self.mode_history.append(mode)
        return mode
