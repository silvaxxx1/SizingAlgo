class Battery:
    def __init__(self, capacity, max_soc=1.0, min_soc=0.2, 
                 charge_efficiency=0.9, discharge_efficiency=0.9):
        self.capacity = capacity
        self.max_soc = max_soc
        self.min_soc = min_soc
        self.charge_efficiency = charge_efficiency
        self.discharge_efficiency = discharge_efficiency
        self.soc = 0.5  # Initialize at 50%
        
    def charge(self, power, time_step=1.0):
        # Implementation based on Eqs. (3.5)-(3.8)
        energy_to_charge = power * time_step
        energy_can_be_stored = (self.max_soc - self.soc) * self.capacity
        actual_energy = min(energy_to_charge * self.charge_efficiency, energy_can_be_stored)
        
        self.soc += actual_energy / self.capacity
        return actual_energy / time_step
    
    def discharge(self, power, time_step=1.0):
        energy_to_discharge = power * time_step
        energy_available = (self.soc - self.min_soc) * self.capacity
        actual_energy = min(energy_to_discharge, energy_available * self.discharge_efficiency)
        
        self.soc -= actual_energy / (self.capacity * self.discharge_efficiency)
        return actual_energy / time_step

class ElectricVehicle:
    def __init__(self, battery_capacity, max_soc=0.95, min_soc=0.2,
                 charge_efficiency=0.9, discharge_efficiency=0.9):
        self.battery_capacity = battery_capacity
        self.max_soc = max_soc
        self.min_soc = min_soc
        self.charge_efficiency = charge_efficiency
        self.discharge_efficiency = discharge_efficiency
        self.soc = 0.5  # Initialize at 50%
        self.is_connected = False
        
    def connect(self):
        self.is_connected = True
        
    def disconnect(self):
        self.is_connected = False
        
    def charge(self, power, time_step=1.0):
        # Implementation of Eq. (3.10)
        if not self.is_connected:
            return 0
            
        energy_to_charge = power * time_step
        energy_can_be_stored = (self.max_soc - self.soc) * self.battery_capacity
        actual_energy = min(energy_to_charge * self.charge_efficiency, energy_can_be_stored)
        
        self.soc += actual_energy / self.battery_capacity
        return actual_energy / time_step
    
    def discharge(self, power, time_step=1.0):
        if not self.is_connected:
            return 0
            
        energy_to_discharge = power * time_step
        energy_available = (self.soc - self.min_soc) * self.battery_capacity
        actual_energy = min(energy_to_discharge, energy_available * self.discharge_efficiency)
        
        self.soc -= actual_energy / (self.battery_capacity * self.discharge_efficiency)
        return actual_energy / time_step
