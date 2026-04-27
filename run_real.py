"""
run_real.py
Runs one real PSO and one ALO pass against the full 8,760-hour simulation
and saves the results to outputs/pso_alo_comparison/real_results.json.

After this completes, run generate_comparison.py to produce the polished
figures using the real numbers.

Usage:
    python3 run_real.py                      # pop=30, iters=100 (from config)
    python3 run_real.py --iters 50           # faster debug run
    python3 run_real.py --pop 20 --iters 50  # override both
"""

import sys
import time
import json
import yaml
import argparse
import numpy as np
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'src'))

from utils.data_loader import DataLoader
from components import PhotovoltaicSystem, WindTurbine, BatterySystem, ElectricVehicle, Grid
from energy_management.rule_based_ems import RuleBasedEMS
from optimization.pso import ParticleSwarmOptimizer
from optimization.alo import AntlionOptimizer
from analysis.economic_analysis import EconomicAnalysis


def load_config(iters_override=None, pop_override=None):
    for name in ('config.yml', 'config.yaml'):
        p = ROOT / name
        if p.exists():
            with open(p) as f:
                cfg = yaml.safe_load(f)
            if iters_override:
                cfg['optimization']['max_iterations'] = iters_override
            if pop_override:
                cfg['optimization']['population_size'] = pop_override
            return cfg
    raise FileNotFoundError("config.yml not found")


def init_components(cfg):
    pv_c = cfg['components']['pv']
    wt_c = cfg['components']['wind_turbine']
    bt_c = cfg['components']['battery']
    ev_c = cfg['components']['ev']
    ec   = cfg['economic']
    return {
        'pv':   PhotovoltaicSystem(pv_c['rated_power'], pv_c['temp_coefficient'], pv_c['noct']),
        'wt':   WindTurbine(wt_c['rated_power'], wt_c['cut_in_speed'],
                            wt_c['cut_out_speed'], wt_c['rated_speed']),
        'bt':   BatterySystem(bt_c['capacity'], bt_c['soc_min'],
                              bt_c['soc_max'], bt_c['efficiency']),
        'ev':   ElectricVehicle(ev_c['capacity'], ev_c['soc_min'], ev_c['soc_max']),
        'grid': Grid(ec['grid_buy_price'], ec['grid_sell_price']),
    }


def make_objective(data, components, cfg):
    economic    = EconomicAnalysis(cfg['economic'])
    constraints = cfg['constraints']

    def objective(solution):
        try:
            n_pv, n_wt, n_bt, ad = solution
            n_pv = max(1, int(n_pv));  n_wt = max(1, int(n_wt))
            n_bt = max(1, int(n_bt));  ad   = max(0.1, float(ad))
            components['pv'].set_count(n_pv)
            components['wt'].set_count(n_wt)
            components['bt'].set_count(n_bt)
            components['bt'].set_autonomy_days(ad)
            ems = RuleBasedEMS(components)
            sim = ems.simulate_year(data)
            coe  = economic.calculate_coe(components, sim)
            lpsp = economic.calculate_lpsp(sim)
            ref  = economic.calculate_ref(sim)
            fitness = 0.5 * coe + 0.5 * 1000 * lpsp - 0.5 * ref
            if lpsp > constraints['lpsp_max']:
                fitness += 1000
            if ref < constraints['ref_min']:
                fitness += 1000
            return float(fitness)
        except Exception:
            return 1e6

    return objective


def evaluate_kpis(solution, data, components, cfg):
    economic = EconomicAnalysis(cfg['economic'])
    n_pv, n_wt, n_bt, ad = solution
    components['pv'].set_count(max(1, int(n_pv)))
    components['wt'].set_count(max(1, int(n_wt)))
    components['bt'].set_count(max(1, int(n_bt)))
    components['bt'].set_autonomy_days(max(0.1, float(ad)))
    ems = RuleBasedEMS(components)
    sim = ems.simulate_year(data)
    return {
        'coe':  round(economic.calculate_coe(components, sim),  6),
        'lpsp': round(economic.calculate_lpsp(sim),             6),
        'ref':  round(economic.calculate_ref(sim),              6),
        'npc':  round(economic.calculate_npc(components),       2),
    }


def run_algorithm(name, objective, bounds, cfg):
    pop   = cfg['optimization']['population_size']
    iters = cfg['optimization']['max_iterations']
    np.random.seed(42)
    t0 = time.time()
    if name == 'PSO':
        opt = ParticleSwarmOptimizer(
            objective_function=objective,
            bounds=bounds,
            swarm_size=pop,
            max_iterations=iters,
        )
    else:
        opt = AntlionOptimizer(
            objective_function=objective,
            bounds=bounds,
            population_size=pop,
            max_iterations=iters,
        )
    sol, fit, hist = opt.optimize()
    elapsed = time.time() - t0
    return sol, float(fit), [float(v) for v in hist], elapsed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--iters', type=int, default=None)
    parser.add_argument('--pop',   type=int, default=None)
    args = parser.parse_args()

    cfg = load_config(iters_override=args.iters, pop_override=args.pop)
    pop   = cfg['optimization']['population_size']
    iters = cfg['optimization']['max_iterations']

    print(f"\n{'='*60}")
    print(f"  PSO vs ALO — Real Algorithm Run")
    print(f"  population={pop}   iterations={iters}")
    print(f"{'='*60}\n")

    print("Loading data (weather, load, EV)...")
    loader = DataLoader(cfg)
    data = {
        'weather': loader.load_weather_data(),
        'load':    loader.load_load_profile(),
        'ev':      loader.load_ev_data(),
    }
    components = init_components(cfg)
    bounds = [
        (cfg['bounds']['n_pv'][0],          cfg['bounds']['n_pv'][1]),
        (cfg['bounds']['n_wt'][0],          cfg['bounds']['n_wt'][1]),
        (cfg['bounds']['n_bt'][0],          cfg['bounds']['n_bt'][1]),
        (cfg['bounds']['autonomy_days'][0], cfg['bounds']['autonomy_days'][1]),
    ]
    print("Data loaded.\n")

    output = {}
    for name in ('PSO', 'ALO'):
        print(f"Running {name}  (pop={pop}, iters={iters}) ...")
        objective = make_objective(data, components, cfg)
        sol, fit, hist, elapsed = run_algorithm(name, objective, bounds, cfg)
        kpis = evaluate_kpis(sol, data, components, cfg)

        print(f"  {name} finished in {elapsed:.1f}s")
        print(f"  Solution : PV={int(sol[0])}  WT={int(sol[1])}  "
              f"BT={int(sol[2])}  AD={sol[3]:.2f}")
        print(f"  COE=${kpis['coe']:.4f}  LPSP={kpis['lpsp']:.4f}  "
              f"REF={kpis['ref']:.4f}  NPC=${kpis['npc']:,.0f}\n")

        output[name] = {
            'solution': [float(v) for v in sol],
            'fitness':  fit,
            'history':  hist,
            'kpis':     kpis,
            'elapsed':  round(elapsed, 2),
        }

    out_path = ROOT / 'outputs' / 'pso_alo_comparison' / 'real_results.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"{'='*60}")
    print(f"  Real results saved to:")
    print(f"  {out_path}")
    print(f"\n  Next step:")
    print(f"  python3 generate_comparison.py")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
