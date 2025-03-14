class Grid:
    def __init__(self, max_power_import, max_power_export, import_tariff, export_tariff):
        self.max_power_import = max_power_import
        self.max_power_export = max_power_export
        self.import_tariff = import_tariff
        self.export_tariff = export_tariff
        
    def import_power(self, power, time_step=1.0):
        # Implementation of Eqs. (3.11) and (3.12)
        actual_power = min(power, self.max_power_import)
        cost = actual_power * time_step * self.import_tariff
        return actual_power, cost
    
    def export_power(self, power, time_step=1.0):
        actual_power = min(power, self.max_power_export)
        revenue = actual_power * time_step * self.export_tariff
        return actual_power, revenue

class Load:
    def __init__(self, load_profile):
        self.load_profile = load_profile
        
    def get_demand(self, hour):
        return self.load_profile[hour % len(self.load_profile)]
