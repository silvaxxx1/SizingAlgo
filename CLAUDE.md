# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

V2G Microgrid Optimization Pipeline — a research framework for optimizing Vehicle-to-Grid (V2G) integrated microgrids in Tripoli, Libya. It sizes hybrid renewable energy systems (PV + wind + battery + EV fleet) using metaheuristic optimization algorithms and evaluates them on economic (COE, NPC) and reliability (LPSP, REF) metrics.

## Commands

```bash
# Install dependencies
make install
# or: pip install -e ".[dev]"

# Run the main pipeline
make run-example
# or: python src/main.py

# Run Streamlit web dashboard
streamlit run streamlit.py

# Tests
make test
# Single test file: pytest src/test.py -v
# With coverage: pytest --cov=src --cov-report=html

# Linting and formatting
make lint       # flake8 + mypy
make format     # black (line-length 88)

# Algorithm benchmarking
make benchmark
```

## Architecture

The pipeline is organized into five layers:

### 1. Components (`src/components/`)
Physical models for each system element. Each class exposes a `calculate_power(hour_data)` method returning watts.
- `photovoltaic.py` — temperature-derated PV output (NOCT model)
- `wind_turbine.py` — piecewise power curve with hub-height wind scaling
- `battery.py` — SOC-bounded storage with 85% round-trip efficiency
- `electric_vehicle.py` — V2G-capable fleet; bidirectional 7.2 kW per EV
- `grid.py` — buy/sell price interface ($0.023/$0.015 per kWh)
- `converter.py` — 95% inverter efficiency applied to all AC/DC conversions

### 2. Optimization (`src/optimization/`)
All optimizers share the same call signature: `optimize(objective_fn, bounds, pop_size, max_iter)` and return `(best_solution, best_fitness, convergence_curve)`.

The 4-dimensional decision vector is:
```
x = [n_pv ∈ [10,100], n_wt ∈ [5,50], n_bt ∈ [10,100], autonomy_days ∈ [1,5]]
```

- `ialo.py` — Improved Antlion Optimizer (primary); adds Lévy-flight exploration (β=1.5, Mantegna's algorithm)
- `alo.py`, `pso.py`, `csa.py` — baseline comparators

### 3. Energy Management (`src/energy_management/`)
`rule_based_ems.py` dispatches energy across 6 hourly modes (direct RE supply → battery discharge → grid purchase → V2G discharge → surplus battery charge → surplus export). Runs 8,760 iterations per fitness evaluation.

### 4. Analysis (`src/analysis/`)
Post-optimization evaluation:
- `economic_analysis.py` — CRF, NPC, COE, LPSP, REF (see equations in `V2G Microgrid Optimization.md`)
- `monte_carlo.py` — 100-run stochastic robustness check
- `sensitivity_analysis.py` — one-at-a-time parameter sweeps

### 5. Utilities (`src/utils/`)
- `data_loader.py` — reads `data/*.csv` (8,760-row annual hourly series)
- `visualization.py` — matplotlib/plotly publication figures saved to `outputs/figures/`
- `constants.py` — all physical constants, economic parameters, location data

## Key Files

| File | Purpose |
|------|---------|
| `src/main.py` | Primary entry point; orchestrates full pipeline |
| `src/main_enhanced.py` | Extended version with extra reporting |
| `config.yml` | All tuneable parameters (algorithm, constraints, economics) |
| `streamlit.py` | Interactive web dashboard |
| `data/weather_data.csv` | Solar irradiance, ambient temp, wind speed (8,760 rows) |
| `data/load_data.csv` | Hourly residential demand |
| `data/ev_data.csv` | 10 EV behavioral profiles |

## Objective Function

```
f(x) = 0.5×COE + 0.5×1000×LPSP − 0.5×REF + constraint_penalties
```

Constraints: `LPSP ≤ 0.01`, `REF ≥ 0.5`. Violations add large penalty terms — see `create_objective_function_wrapper()` in `src/main.py`.

## Output Structure

Each run writes timestamped results under `outputs/{algorithm}/run_{timestamp}/`:
- Convergence curve, Pareto front, energy flow plots
- JSON/CSV with best solution vector and KPIs
- Summary report

## Configuration

`config.yml` controls everything. Key sections:

```yaml
optimization:
  algorithms: ["IALO", "ALO", "PSO", "CSA"]
  population_size: 30
  max_iterations: 100
  ialo:
    beta: 1.5          # Lévy flight exponent
    levy_probability: 0.3
constraints:
  lpsp_max: 0.01
  ref_min: 0.5
economic:
  interest_rate: 0.03
  project_lifetime: 20
```

## Adding a New Algorithm

1. Create `src/optimization/your_algo.py` with `optimize(objective_fn, bounds, pop_size, max_iter)` signature
2. Register it in `src/optimization/__init__.py`
3. Add its config block under `optimization:` in `config.yml`
4. Reference it in the `ALGORITHMS` dispatch dict in `src/main.py`
