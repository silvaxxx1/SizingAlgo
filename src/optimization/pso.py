


# optimization/pso.py
import numpy as np
from typing import Callable, List, Tuple
import logging

class ParticleSwarmOptimizer:
    """
    Particle Swarm Optimization (PSO) implementation
    """
    
    def __init__(self,
                 objective_function: Callable,
                 bounds: List[Tuple[float, float]],
                 swarm_size: int = 50,
                 max_iterations: int = 100,
                 w: float = 0.9,
                 c1: float = 2.0,
                 c2: float = 2.0):
        
        self.objective_function = objective_function
        self.bounds = np.array(bounds)
        self.swarm_size = swarm_size
        self.max_iterations = max_iterations
        self.dimensions = len(bounds)
        
        # PSO parameters
        self.w = w  # Inertia weight
        self.c1 = c1  # Cognitive parameter
        self.c2 = c2  # Social parameter
        self.w_min = 0.4  # Minimum inertia weight
        
        # Swarm arrays
        self.particles = None
        self.velocities = None
        self.fitness = None
        self.personal_best = None
        self.personal_best_fitness = None
        
        # Global best
        self.global_best = None
        self.global_best_fitness = float('inf')
        self.convergence_history = []
        
        logging.info(f"PSO initialized: swarm_size={swarm_size}, max_iter={max_iterations}")
    
    def initialize_swarm(self):
        """Initialize particle swarm"""
        # Initialize positions randomly
        self.particles = np.random.uniform(
            self.bounds[:, 0], self.bounds[:, 1],
            (self.swarm_size, self.dimensions)
        )
        
        # Initialize velocities
        v_max = (self.bounds[:, 1] - self.bounds[:, 0]) * 0.1
        self.velocities = np.random.uniform(-v_max, v_max, (self.swarm_size, self.dimensions))
        
        # Evaluate initial fitness
        self.fitness = np.array([self.objective_function(particle) for particle in self.particles])
        
        # Initialize personal bests
        self.personal_best = self.particles.copy()
        self.personal_best_fitness = self.fitness.copy()
        
        # Find global best
        best_idx = np.argmin(self.fitness)
        self.global_best = self.particles[best_idx].copy()
        self.global_best_fitness = self.fitness[best_idx]
        
        self.convergence_history.append(self.global_best_fitness)
    
    def update_velocity_and_position(self, iteration: int):
        """Update particle velocities and positions"""
        # Update inertia weight linearly
        current_w = self.w - (self.w - self.w_min) * iteration / self.max_iterations
        
        for i in range(self.swarm_size):
            # Generate random coefficients
            r1 = np.random.random(self.dimensions)
            r2 = np.random.random(self.dimensions)
            
            # Update velocity
            cognitive = self.c1 * r1 * (self.personal_best[i] - self.particles[i])
            social = self.c2 * r2 * (self.global_best - self.particles[i])
            
            self.velocities[i] = current_w * self.velocities[i] + cognitive + social
            
            # Apply velocity limits
            v_max = (self.bounds[:, 1] - self.bounds[:, 0]) * 0.2
            self.velocities[i] = np.clip(self.velocities[i], -v_max, v_max)
            
            # Update position
            self.particles[i] += self.velocities[i]
            
            # Apply boundary constraints
            self.particles[i] = np.clip(self.particles[i], self.bounds[:, 0], self.bounds[:, 1])
    
    def optimize(self) -> Tuple[np.ndarray, float, List[float]]:
        """Main PSO optimization loop"""
        logging.info("Starting PSO optimization")
        self.initialize_swarm()
        
        for iteration in range(self.max_iterations):
            # Update velocities and positions
            self.update_velocity_and_position(iteration)
            
            # Evaluate new positions
            for i in range(self.swarm_size):
                self.fitness[i] = self.objective_function(self.particles[i])
                
                # Update personal best
                if self.fitness[i] < self.personal_best_fitness[i]:
                    self.personal_best[i] = self.particles[i].copy()
                    self.personal_best_fitness[i] = self.fitness[i]
                
                # Update global best
                if self.fitness[i] < self.global_best_fitness:
                    self.global_best = self.particles[i].copy()
                    self.global_best_fitness = self.fitness[i]
            
            self.convergence_history.append(self.global_best_fitness)
            
            if iteration % 20 == 0:
                logging.info(f"PSO Iteration {iteration+1}, Best fitness: {self.global_best_fitness:.6f}")
        
        return self.global_best, self.global_best_fitness, self.convergence_history



