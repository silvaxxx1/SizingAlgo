# optimization/benchmark_functions.py
import numpy as np
from typing import Callable, Dict, List, Tuple

class BenchmarkFunctions:
    """
    Collection of benchmark optimization functions for testing algorithms
    """
    
    @staticmethod
    def sphere(x: np.ndarray) -> float:
        """Sphere function - unimodal, convex"""
        return np.sum(x**2)
    
    @staticmethod
    def rosenbrock(x: np.ndarray) -> float:
        """Rosenbrock function - non-convex, valley-shaped"""
        return np.sum(100 * (x[1:] - x[:-1]**2)**2 + (1 - x[:-1])**2)
    
    @staticmethod
    def ackley(x: np.ndarray) -> float:
        """Ackley function - multimodal, many local optima"""
        n = len(x)
        return (-20 * np.exp(-0.2 * np.sqrt(np.sum(x**2) / n)) - 
                np.exp(np.sum(np.cos(2 * np.pi * x)) / n) + 20 + np.e)
    
    @staticmethod
    def rastrigin(x: np.ndarray) -> float:
        """Rastrigin function - multimodal, many local optima"""
        return 10 * len(x) + np.sum(x**2 - 10 * np.cos(2 * np.pi * x))
    
    @staticmethod
    def schwefel(x: np.ndarray) -> float:
        """Schwefel function - multimodal, deceptive"""
        return 418.9829 * len(x) - np.sum(x * np.sin(np.sqrt(np.abs(x))))
    
    @classmethod
    def get_function_bounds(cls) -> Dict[str, List[Tuple[float, float]]]:
        """Get typical bounds for benchmark functions"""
        return {
            'sphere': [(-5.12, 5.12)] * 10,
            'rosenbrock': [(-2.048, 2.048)] * 10,
            'ackley': [(-32.768, 32.768)] * 10,
            'rastrigin': [(-5.12, 5.12)] * 10,
            'schwefel': [(-500, 500)] * 10
        }
    
    @classmethod
    def get_global_optimum(cls) -> Dict[str, float]:
        """Get global optimum values for benchmark functions"""
        return {
            'sphere': 0.0,
            'rosenbrock': 0.0,
            'ackley': 0.0,
            'rastrigin': 0.0,
            'schwefel': 0.0
        }
    
    @classmethod
    def run_benchmark_test(cls, optimizer_class, function_name: str, **kwargs):
        """Run benchmark test for given optimizer and function"""
        functions = {
            'sphere': cls.sphere,
            'rosenbrock': cls.rosenbrock,
            'ackley': cls.ackley,
            'rastrigin': cls.rastrigin,
            'schwefel': cls.schwefel
        }
        
        if function_name not in functions:
            raise ValueError(f"Unknown function: {function_name}")
        
        bounds = cls.get_function_bounds()[function_name]
        target = cls.get_global_optimum()[function_name]
        
        optimizer = optimizer_class(
            objective_function=functions[function_name],
            bounds=bounds,
            **kwargs
        )
        
        best_solution, best_fitness, history = optimizer.optimize()
        
        return {
            'function': function_name,
            'optimizer': optimizer_class.__name__,
            'best_solution': best_solution,
            'best_fitness': best_fitness,
            'target_fitness': target,
            'error': abs(best_fitness - target),
            'convergence_history': history
        }
