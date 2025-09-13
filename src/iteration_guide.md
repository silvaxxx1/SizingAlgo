# ⚡ V2G Microgrid Optimization – Parallel Pipeline & Iteration Guide

This guide provides **everything you need** to:

1. Run **multiple algorithms in parallel** for Vehicle-to-Grid (V2G) microgrid optimization.
2. Tune **iteration counts, population sizes, and convergence criteria** for best results.
3. Analyze and **compare algorithms** with a structured output directory.

---

## 🗂️ Enhanced Output Directory Structure

When you run the parallel version, a well-organized directory structure is created automatically:

```
outputs/
├── comparison/                    # Master comparison results
│   └── run_20241215_143052/
│       ├── comparison_results/
│       │   ├── algorithm_comparison.csv
│       │   └── monte_carlo_summary.csv
│       ├── comparison_figures/
│       │   ├── algorithm_convergence_comparison.png
│       │   ├── fitness_comparison.png
│       │   └── time_comparison.png
│       └── comparison_reports/
│           └── master_comparison_report.txt
├── ialo/                          # Individual algorithm results
│   └── run_20241215_143052/
│       ├── optimization_results/
│       ├── figures/
│       ├── reports/
│       └── raw_data/
├── alo/
│   └── run_20241215_143052/
├── pso/
│   └── run_20241215_143052/
└── csa/
    └── run_20241215_143052/
```

---

## 🚀 How to Run the Parallel Version

### **Basic Commands**

```bash
# Run all algorithms in parallel
uv run parallel_main.py --algorithms=IALO,ALO,PSO,CSA

# Run with specific number of workers
uv run parallel_main.py --algorithms=IALO,ALO,PSO --max-workers=2

# Run sequentially
uv run parallel_main.py --algorithms=IALO,ALO,PSO,CSA --sequential

# Run with debug logging
uv run parallel_main.py --algorithms=IALO,ALO --log-level=DEBUG
```

### **Advanced Options**

```bash
# Custom output directory
uv run parallel_main.py --algorithms=IALO,ALO --output-base=my_results

# Run only specific phases
uv run parallel_main.py --algorithms=IALO,ALO --phases=optimization

# Include Monte Carlo analysis
uv run parallel_main.py --algorithms=IALO,ALO,PSO --phases=all
```

---

## 🆕 Key Features

### **1. Dual Output System**

* **Algorithm Outputs**: Each algorithm has its own timestamped directory.
* **Master Comparison**: A centralized location to compare all algorithms.

### **2. Real-time Results**

* Results are saved **immediately** after each algorithm finishes.
* If one algorithm fails, others continue running.

### **3. Comprehensive Comparison**

* Performance tables
* Side-by-side convergence plots
* Execution time breakdowns
* Best/worst performer identification

### **4. Reporting**

* **Per-algorithm reports** for detailed insights.
* **Master comparison report** for a full overview.

### **5. Parallel Safety**

* Thread-safe execution
* Robust error handling
* Fully independent outputs

---

## 📊 Output Files Explained

### **Individual Algorithm Outputs**

Each algorithm generates:

* `*_best_solution.csv` – Best sizing results
* `*_economic_analysis.csv` – Cost and performance metrics
* `*_convergence.png` – Convergence behavior visualization
* `*_energy_flows.png` – Energy flow breakdown
* `*_summary_report.txt` – Detailed algorithm report

### **Master Comparison Outputs**

* `algorithm_comparison.csv` – Summary of all algorithms
* `algorithm_convergence_comparison.png` – Convergence comparison chart
* `fitness_comparison.png` – Performance bar chart
* `time_comparison.png` – Time comparison chart
* `master_comparison_report.txt` – Detailed performance analysis

---

## 📈 Iteration Guidelines

Optimizing iteration counts and population sizes is crucial for balancing **speed** and **solution quality**.

### **Quick Recommendations by Use Case**

| Use Case        | Iterations | Population | Time Estimate |
| --------------- | ---------- | ---------- | ------------- |
| **Testing**     | 50-100     | 20         | 2-5 min       |
| **Development** | 200-300    | 30         | 10-20 min     |
| **Engineering** | 500-700    | 30-40      | 30-45 min     |
| **Research**    | 1000+      | 50         | 1-3 hours     |

---

## ⚡ Algorithm-Specific Recommendations

| Algorithm                | Iterations | Population | Notes                         |
| ------------------------ | ---------- | ---------- | ----------------------------- |
| **IALO** (Improved ALO)  | 500        | 30-50      | Fast convergence, stable      |
| **ALO** (Standard ALO)   | 700-1000   | 40-60      | Slower, needs more iterations |
| **PSO** (Particle Swarm) | 600-800    | 30-40      | Risk of premature convergence |
| **CSA** (Cuckoo Search)  | 800-1200   | 25-40      | Heavy exploration             |

---

## 🔬 Convergence Detection Methods

### **1. Visual Inspection**

* **Flat line for 50+ iterations** → Converged
* **Still improving** → Keep running
* **Oscillating** → Increase population or iterations

### **2. Improvement Threshold**

Stop when improvement < 0.001% for 20 consecutive iterations:

```python
if abs(current_best - previous_best) / previous_best < 0.00001:
    convergence_counter += 1
    if convergence_counter >= 20:
        break
```

### **3. Target Performance**

```python
target_coe = 0.15   # Cost of energy
target_lpsp = 0.05  # Loss of power supply probability
target_ref = 0.80   # Renewable energy fraction
```

---

## ⏱️ Time vs Quality Trade-offs

| Iterations | Solution Quality | Best For    |
| ---------- | ---------------- | ----------- |
| 50-100     | Basic            | Testing     |
| 200-300    | Good             | Development |
| 500-700    | Very Good        | Engineering |
| 1000+      | Excellent        | Research    |

---

## 🔧 Example Configurations

### **Quick Testing**

```yaml
optimization:
  population_size: 20
  max_iterations: 100
```

### **Engineering Use**

```yaml
optimization:
  population_size: 30
  max_iterations: 500
```

### **High-Quality Research**

```yaml
optimization:
  population_size: 50
  max_iterations: 1000
```

---

## 🏃 Performance Benefits of Parallel Execution

### **Speed Example**

| Mode       | Total Time (4 algorithms) |
| ---------- | ------------------------- |
| Sequential | \~20 min                  |
| Parallel   | \~5 min (with 4 cores)    |

**Sequential Example:**

```
IALO: 5 min → ALO: 5 min → PSO: 5 min → CSA: 5 min
```

**Parallel Example:**

```
IALO: 5 min
ALO:  5 min
PSO:  5 min
CSA:  5 min   # All run simultaneously
```

---

## 💡 Best Practices

### **Start Small, Scale Up**

```bash
uv run main.py --algorithms=IALO
# Then increase iterations/population in config.yaml
```

### **Multiple Short Runs > One Long Run**

* **5 runs @ 200 iterations** is better than **1 run @ 1000 iterations**.
* Helps identify variance and consistency.

### **Early Stopping Example**

```python
if convergence_detected:
    print(f"Converged after {iteration} iterations")
    break
```

---

## 🎯 Final Recommended Settings

| Scenario          | Iterations | Population | Notes                      |
| ----------------- | ---------- | ---------- | -------------------------- |
| **Quick Results** | 150        | 25         | Fast feedback (\~5 min)    |
| **Balanced Run**  | 500        | 30         | Good trade-off (\~30 min)  |
| **High Accuracy** | 1000       | 50         | Research-grade (\~2 hours) |

---

## 🔍 Quick Comparison After Run

```bash
# Master report
cat outputs/comparison/run_*/comparison_reports/master_comparison_report.txt

# Algorithm comparison table
cat outputs/comparison/run_*/comparison_results/algorithm_comparison.csv

# Compare convergence plots
ls outputs/*/run_*/figures/*_convergence.png
```
