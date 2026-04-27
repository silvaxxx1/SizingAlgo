"""
launch_comparison.py
V2G Microgrid Optimization — PSO vs ALO Full Comparison

Single entry point:
    python3 launch_comparison.py
    python3 launch_comparison.py --iters 50       # faster debug run
    python3 launch_comparison.py --pop 20 --iters 50
"""

import sys
import subprocess
import argparse
from pathlib import Path

ROOT = Path(__file__).parent


def main():
    parser = argparse.ArgumentParser(description='PSO vs ALO comparison pipeline')
    parser.add_argument('--iters', type=int, default=None, help='Iterations per algorithm')
    parser.add_argument('--pop',   type=int, default=None, help='Population size')
    args = parser.parse_args()

    python = sys.executable

    # ── Step 1: run real algorithms ───────────────────────────────────────────
    cmd1 = [python, str(ROOT / 'run_real.py')]
    if args.iters:
        cmd1 += ['--iters', str(args.iters)]
    if args.pop:
        cmd1 += ['--pop', str(args.pop)]

    print('\n' + '='*60)
    print('  STEP 1 / 2 — Running PSO and ALO algorithms')
    print('='*60 + '\n')
    result = subprocess.run(cmd1)
    if result.returncode != 0:
        print('\nERROR: algorithm run failed — aborting.')
        sys.exit(1)

    # ── Step 2: generate polished figures ─────────────────────────────────────
    cmd2 = [python, str(ROOT / 'generate_comparison.py')]

    print('\n' + '='*60)
    print('  STEP 2 / 2 — Generating comparison figures and reports')
    print('='*60 + '\n')
    result = subprocess.run(cmd2)
    if result.returncode != 0:
        print('\nERROR: figure generation failed.')
        sys.exit(1)

    print('\n' + '='*60)
    print('  DONE — all outputs saved to:')
    print(f'  {ROOT / "outputs" / "pso_alo_comparison"}')
    print('='*60 + '\n')


if __name__ == '__main__':
    main()
