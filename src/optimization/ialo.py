import numpy as np
import math
import random

class IALO:
    def __init__(self, obj_func, dim, bounds, population_size=30, max_iter=100, beta=1.5):
        self.obj_func = obj_func
        self.dim = dim
        self.lower_bound, self.upper_bound = bounds
        self.population_size = population_size
        self.max_iter = max_iter
        self.beta = beta
        self.history = []

    # ===========================
    # Levy Flight Helpers
    # ===========================
    def calculate_sigma(self, beta):
        """
        Calculate sigma for Levy Flight using Mantegna's algorithm.
        """
        numerator = math.gamma(1 + beta) * math.sin(math.pi * beta / 2)
        denominator = math.gamma((1 + beta) / 2) * beta * (2 ** ((beta - 1) / 2))
        return (numerator / denominator) ** (1 / beta)

    def levy_flight(self, position):
        """
        Generate a new position using Levy Flight.
        """
        sigma = self.calculate_sigma(self.beta)
        u = np.random.normal(0, sigma, size=self.dim)
        v = np.random.normal(0, 1, size=self.dim)
        step = u / (np.abs(v) ** (1 / self.beta))
        step_size = 0.01 * step * (position - np.random.uniform(self.lower_bound, self.upper_bound, self.dim))
        return np.clip(position + step_size, self.lower_bound, self.upper_bound)

    # ===========================
    # Initialization
    # ===========================
    def initialize_population(self):
        population = []
        for _ in range(self.population_size):
            individual = np.random.uniform(self.lower_bound, self.upper_bound, self.dim)
            population.append(individual)
        return np.array(population)

    # ===========================
    # Main Optimization Loop
    # ===========================
    def optimize(self):
        population = self.initialize_population()
        fitness = np.array([self.obj_func(ind) for ind in population])

        best_index = np.argmin(fitness)
        best_solution = population[best_index]
        best_fitness = fitness[best_index]

        for iteration in range(self.max_iter):
            new_population = []

            for i in range(self.population_size):
                new_position = self.levy_flight(population[i])
                new_population.append(new_position)

            new_population = np.array(new_population)
            new_fitness = np.array([self.obj_func(ind) for ind in new_population])

            # Combine old and new
            combined_population = np.vstack((population, new_population))
            combined_fitness = np.hstack((fitness, new_fitness))

            # Select the top N individuals
            idx = np.argsort(combined_fitness)
            population = combined_population[idx[:self.population_size]]
            fitness = combined_fitness[idx[:self.population_size]]

            # Update best solution
            if fitness[0] < best_fitness:
                best_fitness = fitness[0]
                best_solution = population[0]

            self.history.append(best_fitness)

            print(f"Iteration {iteration + 1}/{self.max_iter} | Best Fitness: {best_fitness:.6f}")

        return best_solution, best_fitness, self.history

# ===========================
# Example Usage
# ===========================
if __name__ == "__main__":
    # Objective function: Sphere
    def sphere(x):
        return np.sum(x**2)

    dim = 5
    bounds = (-10, 10)
    ialo = IALO(obj_func=sphere, dim=dim, bounds=bounds, population_size=20, max_iter=50)
    best_solution, best_fitness, history = ialo.optimize()

    print("\nBest Solution:", best_solution)
    print("Best Fitness:", best_fitness)
