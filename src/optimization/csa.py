# optimization/csa.py
import numpy as np
import math  # <-- FIX: use the standard math module
from typing import Callable, List, Tuple
import logging

class CuckooSearchAlgorithm:
    """
    Cuckoo Search Algorithm (CSA) implementation
    """
    
    def __init__(self,
                 objective_function: Callable,
                 bounds: List[Tuple[float, float]],
                 population_size: int = 50,
                 max_iterations: int = 100,
                 pa: float = 0.25,
                 step_size: float = 0.01):
        
        self.objective_function = objective_function
        self.bounds = np.array(bounds)
        self.population_size = population_size
        self.max_iterations = max_iterations
        self.dimensions = len(bounds)
        
        # CSA parameters
        self.pa = pa  # Discovery rate of alien eggs
        self.step_size = step_size
        
        # Population arrays
        self.nests = None
        self.fitness = None
        
        # Best solution
        self.best_nest = None
        self.best_fitness = float('inf')
        self.convergence_history = []
        
        logging.info(f"CSA initialized: pop_size={population_size}, max_iter={max_iterations}")
    
    def initialize_population(self):
        """Initialize nest population"""
        self.nests = np.random.uniform(
            self.bounds[:, 0], self.bounds[:, 1],
            (self.population_size, self.dimensions)
        )
        
        self.fitness = np.array([self.objective_function(nest) for nest in self.nests])
        
        # Find initial best
        best_idx = np.argmin(self.fitness)
        self.best_nest = self.nests[best_idx].copy()
        self.best_fitness = self.fitness[best_idx]
        
        self.convergence_history.append(self.best_fitness)
    
    def levy_flight(self, beta: float = 1.5) -> np.ndarray:
        """Generate Levy flight step"""
        # FIX: use math.gamma and math.sin instead of np.math
        sigma = (math.gamma(1 + beta) * math.sin(math.pi * beta / 2) / 
                (math.gamma((1 + beta) / 2) * beta * (2 ** ((beta - 1) / 2)))) ** (1 / beta)
        
        u = np.random.normal(0, sigma, self.dimensions)
        v = np.random.normal(0, 1, self.dimensions)
        
        return u / (np.abs(v) ** (1 / beta))
    
    def get_cuckoo(self, nest_idx: int) -> np.ndarray:
        """Generate new solution using Levy flight"""
        levy_step = self.levy_flight()
        new_nest = self.nests[nest_idx] + self.step_size * levy_step
        
        # Apply boundaries
        return np.clip(new_nest, self.bounds[:, 0], self.bounds[:, 1])
    
    def abandon_worse_nests(self):
        """Abandon worse nests (pa fraction of population)"""
        # Sort nests by fitness
        sorted_indices = np.argsort(self.fitness)
        n_abandon = int(self.pa * self.population_size)
        
        # Replace worst nests
        worst_indices = sorted_indices[-n_abandon:]
        
        for i in worst_indices:
            # Generate new random nest
            self.nests[i] = np.random.uniform(
                self.bounds[:, 0], self.bounds[:, 1], self.dimensions
            )
            self.fitness[i] = self.objective_function(self.nests[i])
    
    def optimize(self) -> Tuple[np.ndarray, float, List[float]]:
        """Main CSA optimization loop"""
        logging.info("Starting CSA optimization")
        self.initialize_population()
        
        for iteration in range(self.max_iterations):
            # Generate new solutions via Levy flights
            for i in range(self.population_size):
                new_nest = self.get_cuckoo(i)
                new_fitness = self.objective_function(new_nest)
                
                # Choose a random nest j
                j = np.random.randint(0, self.population_size)
                
                # If new solution is better, replace nest j
                if new_fitness < self.fitness[j]:
                    self.nests[j] = new_nest
                    self.fitness[j] = new_fitness
            
            # Abandon worse nests
            self.abandon_worse_nests()
            
            # Update best solution
            best_idx = np.argmin(self.fitness)
            if self.fitness[best_idx] < self.best_fitness:
                self.best_nest = self.nests[best_idx].copy()
                self.best_fitness = self.fitness[best_idx]
            
            self.convergence_history.append(self.best_fitness)
            
            if iteration % 20 == 0:
                logging.info(f"CSA Iteration {iteration+1}, Best fitness: {self.best_fitness:.6f}")
        
        return self.best_nest, self.best_fitness, self.convergence_history


# ============================
# Example usage
# ============================
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    # Define an example objective function (Sphere function)
    def sphere_function(x):
        return np.sum(x**2)

    # Define search space bounds for each dimension
    bounds = [(-10, 10), (-10, 10)]  # 2D optimization problem

    # Create CSA optimizer
    csa = CuckooSearchAlgorithm(
        objective_function=sphere_function,
        bounds=bounds,
        population_size=25,
        max_iterations=100,
        pa=0.25,
        step_size=0.01
    )

    # Run optimization
    best_solution, best_fitness, convergence_history = csa.optimize()

    # Print results
    print("Best solution found:", best_solution)
    print("Best fitness value:", best_fitness)

    # Plot convergence history
    plt.figure(figsize=(8, 5))
    plt.plot(convergence_history, marker='o')
    plt.xlabel('Iteration')
    plt.ylabel('Best Fitness Value')
    plt.title('CSA Convergence History')
    plt.grid(True)
    plt.show()
