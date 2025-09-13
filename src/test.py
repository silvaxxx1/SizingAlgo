#!/usr/bin/env python3
"""
Minimal IALO Optimizer Test
"""

import sys
import numpy as np
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from optimization.ialo import IALO

# Setup logging
logging.basicConfig(level=logging.DEBUG)

def simple_objective(x):
    """Simple test objective function"""
    print(f"Objective called with: {x}, type: {type(x)}")
    return sum(xi**2 for xi in x)

def test_ialo():
    """Test IALO optimizer with minimal setup"""
    
    # Define bounds
    lower_bounds = np.array([0, 0, 0, 0])
    upper_bounds = np.array([10, 10, 10, 10])
    bounds = (lower_bounds, upper_bounds)
    
    print("Creating IALO optimizer...")
    
    try:
        optimizer = IALO(
            obj_func=simple_objective,
            dim=4,
            bounds=bounds,
            population_size=5,
            max_iter=3
        )
        
        print("IALO created successfully!")
        print(f"Optimizer type: {type(optimizer)}")
        print(f"Optimizer attributes: {[attr for attr in dir(optimizer) if not attr.startswith('_')]}")
        
        # Check objective function storage
        if hasattr(optimizer, 'obj_func'):
            print(f"obj_func type: {type(optimizer.obj_func)}")
            print(f"obj_func callable: {callable(optimizer.obj_func)}")
        
        if hasattr(optimizer, 'objective_function'):
            print(f"objective_function type: {type(optimizer.objective_function)}")
            print(f"objective_function callable: {callable(optimizer.objective_function)}")
        
        # Test direct call
        test_solution = [1, 2, 3, 4]
        if hasattr(optimizer, 'obj_func') and callable(optimizer.obj_func):
            result = optimizer.obj_func(test_solution)
            print(f"Direct objective function call result: {result}")
        
        print("Running optimization...")
        best_solution, best_fitness, convergence_history = optimizer.optimize()
        
        print(f"Success! Best solution: {best_solution}")
        print(f"Best fitness: {best_fitness}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ialo()