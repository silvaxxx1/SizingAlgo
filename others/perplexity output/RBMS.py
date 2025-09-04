class RuleBasedEMS:
    def __init__(self, pv_system, wind_turbine, battery, ev, grid, load):
        self.pv_system = pv_system
        self.wind_turbine = wind_turbine
        self.battery = battery
        self.ev = ev
        self.grid = grid
        self.load = load
        
    def manage_energy(self, hour, irradiance, ambient_temp, wind_speed, grid_available=True):
        # Calculate power from renewable sources
        pv_power = self.pv_system.calculate_power(irradiance, ambient_temp)
        wt_power = self.wind_turbine.calculate_power(wind_speed)
        res_power = pv_power + wt_power
        
        # Get load demand
        load_demand = self.load.get_demand(hour)
        
        # Initialize result dictionary
        result = {
            "hour": hour,
            "pv_power": pv_power,
            "wt_power": wt_power,
            "res_power": res_power,
            "load_demand": load_demand,
            "battery_power": 0,
            "ev_power": 0,
            "grid_power": 0,
            "grid_cost": 0,
            "grid_revenue": 0,
            "net_cost": 0,
            "mode": 0
        }
        
        # Apply RB-EMS algorithm
        power_balance = res_power - load_demand
        
        # Mode 1: Power from RESs (priority)
        if power_balance >= 0:
            result["mode"] = 1
            excess_power = power_balance
            
            # Charge battery first if not full
            if self.battery.soc < self.battery.max_soc:
                battery_charge = self.battery.charge(excess_power)
                result["battery_power"] = battery_charge
                excess_power -= battery_charge
            
            # Then charge EV if connected and not full
            if self.ev.is_connected and self.ev.soc < self.ev.max_soc and excess_power > 0:
                ev_charge = self.ev.charge(excess_power)
                result["ev_power"] = ev_charge
                excess_power -= ev_charge
            
            # If there's still excess power and grid is available, export to grid
            if excess_power > 0 and grid_available:
                grid_export, grid_revenue = self.grid.export_power(excess_power)
                result["grid_power"] = -grid_export  # Negative means export
                result["grid_revenue"] = grid_revenue
                result["net_cost"] = -grid_revenue
                
        # Implement remaining modes (Mode 2, 3, and 4) as described in the chapter
        # Mode 2: Use battery when RESs are not sufficient
        elif not grid_available and self.battery.soc > self.battery.min_soc:
            result["mode"] = 2
            # Implementation continues with battery discharge logic
            
        # Mode 3: Use grid (G2V)
        elif grid_available:
            result["mode"] = 3
            # Implementation continues with grid import logic
            
        # Mode 4: Use EV battery (V2G)
        elif self.ev.is_connected and self.ev.soc > self.ev.min_soc:
            result["mode"] = 4
            # Implementation continues with EV discharge logic
            
        return result
