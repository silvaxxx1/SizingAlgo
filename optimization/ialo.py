# optimization/ialo.py
import numpy as np
import pandas as pd
from typing import Callable, List, Tuple, Union
import logging

class ImprovedAntlionOptimizer:
    """
    Improved Antlion Optimizer (IALO) based on thesis implementation
    Incorporates Lévy flight for enhanced exploration and convergence
    """
    
    def __init__(self, 
                 objective_function: Callable,
                 bounds: List[Tuple[float, float]],
                 population_size: int = 50,
                 max_iterations: int = 100,
                 alpha: float = 0.01,  # Lévy flight step size parameter
                 beta: float = 1.5,    # Lévy flight distribution parameter
                 elite_ratio: float = 0.1):  # Ratio of elite antlions
        """
        Initialize IALO optimizer
        
        Args:
            objective_function: Function to minimize
            bounds: List of (min, max) bounds for each dimension
            population_size: Number of ants/antlions
            max_iterations: Maximum number of iterations
            alpha: Lévy flight step size parameter
            beta: Lévy flight distribution parameter  
            elite_ratio: Ratio of population considered as elite antlions
        """
        self.objective_function = objective_function
        self.bounds = np.array(bounds)
        self.population_size = population_size
        self.max_iterations = max_iterations
        self.alpha = alpha
        self.beta = beta
        self.elite_ratio = elite_ratio
        self.num_elites = max(1, int(elite_ratio * population_size))
        
        # Problem dimensions
        self.dimensions = len(bounds)
        
        # Population arrays
        self.ants = None
        self.antlions = None
        self.ant_fitness = None
        self.antlion_fitness = None
        
        # Best solution tracking
        self.best_solution = None
        self.best_fitness = float('inf')
        self.convergence_history = []
        
        # Elite antlion tracking
        self.elite_antlion = None
        self.elite_fitness = float('inf')
        
        logging.info(f"IALO initialized: pop_size={population_size}, max_iter={max_iterations}")
    
    def initialize_population(self):
        """Initialize ant and antlion populations"""
        # Initialize ants randomly within bounds
        self.ants = np.zeros((self.population_size, self.dimensions))
        self.antlions = np.zeros((self.population_size, self.dimensions))
        
        for i in range(self.population_size):
            for j in range(self.dimensions):
                self.ants[i, j] = np.random.uniform(self.bounds[j, 0], self.bounds[j, 1])
                self.antlions[i, j] = np.random.uniform(self.bounds[j, 0], self.bounds[j, 1])
        
        # Evaluate initial fitness
        self.ant_fitness = np.array([self.objective_function(ant) for ant in self.ants])
        self.antlion_fitness = np.array([self.objective_function(antlion) for antlion in self.antlions])
        
        # Find initial best solution
        best_ant_idx = np.argmin(self.ant_fitness)
        best_antlion_idx = np.argmin(self.antlion_fitness)
        
        if self.ant_fitness[best_ant_idx] < self.antlion_fitness[best_antlion_idx]:
            self.best_solution = self.ants[best_ant_idx].copy()
            self.best_fitness = self.ant_fitness[best_ant_idx]
        else:
            self.best_solution = self.antlions[best_antlion_idx].copy()
            self.best_fitness = self.antlion_fitness[best_antlion_idx]
        
        # Initialize elite antlion
        self.elite_antlion = self.best_solution.copy()
        self.elite_fitness = self.best_fitness
    
    def calculate_sigma(self, beta: float) -> float:
        """
        Calculate sigma parameter for Lévy flight
        Based on Eq.(3.30) from thesis
        """
        numerator = np.math.gamma(1 + beta) * np.sin(np.pi * beta / 2)
        denominator = np.math.gamma((1 + beta) / 2) * beta * (2 ** ((beta - 1) / 2))
        return (numerator / denominator) ** (1 / beta)
    
    def levy_flight(self, 
                   current_position: np.ndarray,
                   best_position: np.ndarray,
                   alpha: float = None) -> np.ndarray:
        """
        Generate Lévy flight step based on Eq.(3.28)-(3.33) from thesis
        
        Args:
            current_position: Current ant position
            best_position: Best known position (elite antlion)
            alpha: Step size parameter (if None, uses self.alpha)
            
        Returns:
            New position after Lévy flight step
        """
        if alpha is None:
            alpha = self.alpha
        
        # Calculate sigma for Lévy distribution
        sigma = self.calculate_sigma(self.beta)
        
        # Generate Lévy flight step
        u = np.random.normal(0, sigma, self.dimensions)
        v = np.random.normal(0, 1, self.dimensions)
        
        # Lévy flight formula
        step = u / (np.abs(v) ** (1 / self.beta))
        
        # Calculate new position
        new_position = current_position + alpha * step * (best_position - current_position)
        
        # Apply boundary constraints
        return self.apply_bounds(new_position)
    
    def apply_bounds(self, position: np.ndarray) -> np.ndarray:
        """Apply boundary constraints to position"""
        return np.clip(position, self.bounds[:, 0], self.bounds[:, 1])
    
    def roulette_wheel_selection(self, fitness_values: np.ndarray) -> int:
        """
        Perform roulette wheel selection based on fitness
        Lower fitness values have higher selection probability
        """
        # Convert minimization to maximization problem for selection
        if np.all(fitness_values == fitness_values[0]):
            # All fitness values are the same
            return np.random.randint(0, len(fitness_values))
        
        # Invert fitness for maximization (add small constant to avoid division by zero)
        max_fitness = np.max(fitness_values)
        inverted_fitness = max_fitness - fitness_values + 1e-10
        
        # Calculate probabilities
        probabilities = inverted_fitness / np.sum(inverted_fitness)
        
        # Roulette wheel selection
        cumulative_prob = np.cumsum(probabilities)
        rand = np.random.random()
        
        for i, cum_prob in enumerate(cumulative_prob):
            if rand <= cum_prob:
                return i
        
        return len(fitness_values) - 1  # Fallback
    
    def random_walk_around_antlion(self, 
                                  antlion_position: np.ndarray,
                                  iteration: int) -> np.ndarray:
        """
        Perform random walk around selected antlion with decreasing boundaries
        """
        # Calculate boundary reduction factor based on iteration
        I = 1 / (2 ** (iteration / self.max_iterations))
        
        # Calculate dynamic bounds around antlion
        c = antlion_position + I * (self.bounds[:, 1] - self.bounds[:, 0]) / 2
        d = antlion_position - I * (self.bounds[:, 1] - self.bounds[:, 0]) / 2
        
        # Ensure bounds are within original problem bounds
        c = np.minimum(c, self.bounds[:, 1])
        d = np.maximum(d, self.bounds[:, 0])
        
        # Generate random position within dynamic bounds
        new_position = np.random.uniform(d, c)
        
        return self.apply_bounds(new_position)
    
    def update_elite_antlion(self):
        """Update elite antlion based on current best fitness"""
        # Find best antlion
        best_idx = np.argmin(self.antlion_fitness)
        if self.antlion_fitness[best_idx] < self.elite_fitness:
            self.elite_antlion = self.antlions[best_idx].copy()
            self.elite_fitness = self.antlion_fitness[best_idx]
        
        # Update global best if elite is better
        if self.elite_fitness < self.best_fitness:
            self.best_solution = self.elite_antlion.copy()
            self.best_fitness = self.elite_fitness
    
    def optimize(self) -> Tuple[np.ndarray, float, List[float]]:
        """
        Main optimization loop
        
        Returns:
            Tuple of (best_solution, best_fitness, convergence_history)
        """
        logging.info("Starting IALO optimization")
        
        # Initialize population
        self.initialize_population()
        self.convergence_history.append(self.best_fitness)
        
        for iteration in range(self.max_iterations):
            # Update each ant
            for i in range(self.population_size):
                # Select antlion using roulette wheel selection
                selected_antlion_idx = self.roulette_wheel_selection(self.antlion_fitness)
                
                # Perform random walk around selected antlion
                RA = self.random_walk_around_antlion(
                    self.antlions[selected_antlion_idx], iteration
                )
                
                # Perform random walk around elite antlion  
                RE = self.random_walk_around_antlion(
                    self.elite_antlion, iteration
                )
                
                # Apply Lévy flight for enhanced exploration
                if np.random.random() < 0.3:  # 30% probability of Lévy flight
                    new_position = self.levy_flight(
                        self.ants[i], self.elite_antlion
                    )
                else:
                    # Combine random walks (original ALO approach)
                    new_position = (RA + RE) / 2
                
                # Evaluate new position
                new_fitness = self.objective_function(new_position)
                
                # Update ant if improvement found
                if new_fitness < self.ant_fitness[i]:
                    self.ants[i] = new_position
                    self.ant_fitness[i] = new_fitness
            
            # Update antlions based on ants (assume ants with better fitness catch antlions)
            for i in range(self.population_size):
                if self.ant_fitness[i] < self.antlion_fitness[i]:
                    self.antlions[i] = self.ants[i].copy()
                    self.antlion_fitness[i] = self.ant_fitness[i]
            
            # Update elite antlion and global best
            self.update_elite_antlion()
            
            # Record convergence
            self.convergence_history.append(self.best_fitness)
            
            # Log progress
            if iteration % 20 == 0 or iteration == self.max_iterations - 1:
                logging.info(f"IALO Iteration {iteration+1}/{self.max_iterations}, "
                           f"Best fitness: {self.best_fitness:.6f}")
        
        logging.info(f"IALO optimization completed. Final best fitness: {self.best_fitness:.6f}")
        return self.best_solution, self.best_fitness, self.convergence_history
    
    def get_optimization_statistics(self) -> dict:
        """Get detailed statistics about the optimization process"""
        return {
            'algorithm': 'IALO',
            'population_size': self.population_size,
            'max_iterations': self.max_iterations,
            'dimensions': self.dimensions,
            'final_fitness': self.best_fitness,
            'convergence_rate': (self.convergence_history[0] - self.best_fitness) / self.convergence_history[0],
            'iterations_completed': len(self.convergence_history) - 1
        }


# Example usage and testing
if __name__ == "__main__":
    # Test function (Sphere function)
    def sphere_function(x):
        return np.sum(x**2)
    
    # Define bounds
    bounds = [(-5, 5), (-5, 5), (-5, 5)]
    
    # Create optimizer
    ialo = ImprovedAntlionOptimizer(
        objective_function=sphere_function,
        bounds=bounds,
        population_size=30,
        max_iterations=50
    )
    
    # Optimize
    best_solution, best_fitness, history = ialo.optimize()
    
    print(f"Best solution: {best_solution}")
    print(f"Best fitness: {best_fitness}")
    print(f"Convergence in {len(history)} iterations")