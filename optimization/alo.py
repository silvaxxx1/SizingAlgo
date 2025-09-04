# optimization/alo.py
import numpy as np
from typing import Callable, List, Tuple
import logging

class AntlionOptimizer:
    """
    Standard Antlion Optimizer (ALO) implementation
    Based on original ALO algorithm by Mirjalili (2015)
    """
    
    def __init__(self, 
                 objective_function: Callable,
                 bounds: List[Tuple[float, float]],
                 population_size: int = 50,
                 max_iterations: int = 100):
        
        self.objective_function = objective_function
        self.bounds = np.array(bounds)
        self.population_size = population_size
        self.max_iterations = max_iterations
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
        
        # Elite antlion
        self.elite_antlion = None
        self.elite_fitness = float('inf')
        
        logging.info(f"ALO initialized: pop_size={population_size}, max_iter={max_iterations}")
    
    def initialize_population(self):
        """Initialize ant and antlion populations"""
        self.ants = np.random.uniform(
            self.bounds[:, 0], self.bounds[:, 1], 
            (self.population_size, self.dimensions)
        )
        self.antlions = np.random.uniform(
            self.bounds[:, 0], self.bounds[:, 1], 
            (self.population_size, self.dimensions)
        )
        
        # Evaluate initial fitness
        self.ant_fitness = np.array([self.objective_function(ant) for ant in self.ants])
        self.antlion_fitness = np.array([self.objective_function(antlion) for antlion in self.antlions])
        
        # Find initial best
        self._update_best_solution()
        self.convergence_history.append(self.best_fitness)
    
    def _update_best_solution(self):
        """Update best solution from current populations"""
        all_solutions = np.vstack([self.ants, self.antlions])
        all_fitness = np.hstack([self.ant_fitness, self.antlion_fitness])
        
        best_idx = np.argmin(all_fitness)
        if all_fitness[best_idx] < self.best_fitness:
            self.best_solution = all_solutions[best_idx].copy()
            self.best_fitness = all_fitness[best_idx]
        
        # Update elite antlion
        elite_idx = np.argmin(self.antlion_fitness)
        if self.antlion_fitness[elite_idx] < self.elite_fitness:
            self.elite_antlion = self.antlions[elite_idx].copy()
            self.elite_fitness = self.antlion_fitness[elite_idx]
    
    def roulette_wheel_selection(self, fitness_values: np.ndarray) -> int:
        """Roulette wheel selection for antlion selection"""
        if np.all(fitness_values == fitness_values[0]):
            return np.random.randint(0, len(fitness_values))
        
        max_fitness = np.max(fitness_values)
        inverted_fitness = max_fitness - fitness_values + 1e-10
        probabilities = inverted_fitness / np.sum(inverted_fitness)
        
        return np.random.choice(len(fitness_values), p=probabilities)
    
    def random_walk(self, antlion_pos: np.ndarray, iteration: int) -> np.ndarray:
        """Perform random walk around antlion with shrinking boundaries"""
        I = 1 / (2 ** (iteration / self.max_iterations))
        
        # Calculate bounds around antlion
        c = antlion_pos + I * (self.bounds[:, 1] - self.bounds[:, 0]) / 2
        d = antlion_pos - I * (self.bounds[:, 1] - self.bounds[:, 0]) / 2
        
        # Ensure within original bounds
        c = np.minimum(c, self.bounds[:, 1])
        d = np.maximum(d, self.bounds[:, 0])
        
        return np.random.uniform(d, c)
    
    def optimize(self) -> Tuple[np.ndarray, float, List[float]]:
        """Main ALO optimization loop"""
        logging.info("Starting ALO optimization")
        self.initialize_population()
        
        for iteration in range(self.max_iterations):
            for i in range(self.population_size):
                # Select antlion using roulette wheel
                selected_antlion = self.roulette_wheel_selection(self.antlion_fitness)
                
                # Random walk around selected antlion
                RA = self.random_walk(self.antlions[selected_antlion], iteration)
                
                # Random walk around elite antlion
                RE = self.random_walk(self.elite_antlion, iteration)
                
                # Combine walks
                self.ants[i] = (RA + RE) / 2
                
                # Evaluate new position
                self.ant_fitness[i] = self.objective_function(self.ants[i])
            
            # Update antlions (ants with better fitness replace antlions)
            for i in range(self.population_size):
                if self.ant_fitness[i] < self.antlion_fitness[i]:
                    self.antlions[i] = self.ants[i].copy()
                    self.antlion_fitness[i] = self.ant_fitness[i]
            
            self._update_best_solution()
            self.convergence_history.append(self.best_fitness)
            
            if iteration % 20 == 0:
                logging.info(f"ALO Iteration {iteration+1}, Best fitness: {self.best_fitness:.6f}")
        
        return self.best_solution, self.best_fitness, self.convergence_history