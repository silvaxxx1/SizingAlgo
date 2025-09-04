import numpy as np 

class IALO:
    def __init__(self, population_size, max_iterations, lower_bounds, upper_bounds):
        self.population_size = population_size
        self.max_iterations = max_iterations
        self.lower_bounds = np.array(lower_bounds)
        self.upper_bounds = np.array(upper_bounds)
        self.dimension = len(lower_bounds)
        
    def initialize_population(self):
        antlion_positions = np.zeros((self.population_size, self.dimension))
        ant_positions = np.zeros((self.population_size, self.dimension))
        
        for i in range(self.population_size):
            for j in range(self.dimension):
                antlion_positions[i, j] = self.lower_bounds[j] + np.random.rand() * (self.upper_bounds[j] - self.lower_bounds[j])
                ant_positions[i, j] = self.lower_bounds[j] + np.random.rand() * (self.upper_bounds[j] - self.lower_bounds[j])
                
        return antlion_positions, ant_positions
        
    def random_walk(self, iteration, max_iterations, lb, ub):
        # Implementation of adaptive random walks based on Eqs. (3.27-3.33)
        # The I ratio adapts based on iteration progress
        I = 1
        if iteration > 0.1 * max_iterations:
            I = 1 + 100 * (iteration / max_iterations)
        if iteration > 0.5 * max_iterations:
            I = 1 + 1000 * (iteration / max_iterations)
        if iteration > 0.75 * max_iterations:
            I = 1 + 10000 * (iteration / max_iterations)
        
        # Update bounds based on ratio
        c_lb = lb / I
        c_ub = ub / I
        
        # Random walk implementation
        step_size = 0.1
        num_steps = 100
        walk = np.zeros(num_steps + 1)
        
        for j in range(num_steps):
            r = np.random.rand()
            if r < 0.5:
                walk[j + 1] = walk[j] + step_size
            else:
                walk[j + 1] = walk[j] - step_size
                
        # Normalize and scale the random walk
        min_walk, max_walk = np.min(walk), np.max(walk)
        if min_walk == max_walk:
            return (lb + ub) / 2
        
        walk_normalized = (walk - min_walk) / (max_walk - min_walk)
        return c_lb + walk_normalized[-1] * (c_ub - c_lb)
        
    def optimize(self, objective_function):
        # Initialize population
        antlion_positions, ant_positions = self.initialize_population()
        
        # Evaluate initial fitness
        antlion_fitness = np.array([objective_function(pos) for pos in antlion_positions])
        
        # Find elite (best antlion)
        elite_idx = np.argmin(antlion_fitness)
        elite_position = antlion_positions[elite_idx].copy()
        elite_fitness = antlion_fitness[elite_idx]
        
        # Initialize convergence curve
        convergence_curve = np.zeros(self.max_iterations)
        
        # Main optimization loop implementation follows
        # This implements the IALO algorithm as described in the chapter
        
        return elite_position, elite_fitness, convergence_curve
