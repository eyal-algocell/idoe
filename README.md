
# 🧬 iDoE Planner – Intensified Design of Experiments for Bioprocess Optimization

## 📘 Overview

This repository presents an implementation of an **Intensified Design of Experiments (iDoE)** planner in Python.
The project models and optimizes **E. coli fermentation processes** by exploring a multidimensional design space defined by **growth rate (μ)** and **temperature (°C)**, across **multiple fermentation stages**.

The approach is based on the scientific methodology introduced by
**von Stosch and Willis (2017)** — *"Intensified Design of Experiments for Upstream Bioreactors"*.

---

## 🧠 Scientific Background

### Design of Experiments (DoE)

Design of Experiments (DoE) is a **statistical optimization framework** that identifies the influence of process variables (factors) on measurable outcomes (responses).
It is a cornerstone of **Quality by Design (QbD)** in bioprocess engineering.

Traditional DoE explores a design space by running multiple experiments for every possible combination of factors.
However, this is costly and time-consuming — especially in **bioprocesses** like fermentation.

### Intensified DoE (iDoE)

**iDoE** extends traditional DoE by allowing **multiple parameter changes within a single experimental run**, distributed across several **stages**.
For example, a fermentation may include:

* Stage 1: Adaptation
* Stage 2: Exponential Growth
* Stage 3: Product Induction

By varying parameters dynamically, iDoE reduces total experimental load by **up to 40%** while maintaining statistical validity.

---

## ⚙️ Objective

The iDoE planner aims to:

1. **Minimize total cost and experiment count.**
2. **Maximize design space exploration** (growth rate and temperature).
3. **Enforce biological and operational constraints (C1–C8).**
4. **Produce a visualized 2-factor Doehlert design layout.**

---

## 🧩 Model and Methodology

### 1. Decision Variables

Binary decision variables are defined as:

```
x[i][j][k] = 1 if combination j is used at stage k of run i, else 0
```

Where:

* `i`: experiment (run)
* `j`: parameter combination (growth rate, temperature)
* `k`: stage number

### 2. Optimization Framework

The problem is formulated as a **Mixed Integer Linear Programming (MILP)** model using the `pulp` library.

**Objective:**
Minimize total cost = ∑ (weights × experiments),
subject to design validity and biological feasibility.

### 3. Constraints (C1–C8)

| ID     | Constraint                          | Description                                                                          |
| ------ | ----------------------------------- | ------------------------------------------------------------------------------------ |
| **C1** | One combination per stage           | Prevents simultaneous conflicting parameters (e.g., two temperatures).               |
| **C2** | No duplicate combinations per stage | Ensures full exploration of the design space.                                        |
| **C3** | Max two repeats per experiment      | Avoids intra-run redundancy.                                                         |
| **C4** | Max two global repeats              | Prevents global overrepresentation.                                                  |
| **C5** | All combinations appear once        | Guarantees coverage of the full design space.                                        |
| **C6** | Weighted stage control              | Adjusts flexibility using stage-specific weights *(Sₖ)* and thresholds *(tⱼ)*.       |
| **C7** | Limit extreme changes               | Caps temperature and μ variation to prevent biological shock (e.g., HSP activation). |
| **C8** | Limit minimal changes               | Forces diversity between consecutive stages using the Big-M method.                  |

---

## 🧪 Implementation Guide

### 🔧 Requirements

Create a `requirements.txt` file with:

```
numpy
pulp
```

Then install dependencies with:

```bash
pip install -r requirements.txt
```

---

### 🚀 How to Run

1. **Define the Design Space**

   Modify the `factor_values` array in the notebook:

   ```python
   factor_values = np.array([
       [0.135, 31],
       [0.16, 31],
       [0.11, 31],
       [0.1225, 29],
       # ...
   ])
   ```

   Each entry represents a `(μ, temperature)` combination.

2. **Set Experiment Parameters**

   ```python
   nStages = 3  # e.g., adaptation, log, induction
   delta_f_max_mu   = 0.03
   delta_f_max_temp = 2
   delta_f_min_mu   = 0.01
   delta_f_min_temp = 1
   ```

3. **Define Stage Weights and Thresholds**

   ```python
   Sk = [1, 1.5, 2]  # Stage costs
   tj = [3, 2, 1]    # Experiment allowances
   ```

4. **Run the Optimization**

   Execute all cells in the Jupyter notebook.
   The output will include:

   * Optimized stage combinations per experiment
   * A 2-factor Doehlert design visualization chart

---

## 📊 Results Summary

**Optimized Experimental Layout**

| Experiment | Stage 1 | Stage 2 | Stage 3 |
| ---------- | ------- | ------- | ------- |
| 1          | Combo 9 | Combo 6 | Combo 6 |
| 2          | Combo 7 | Combo 1 | Combo 8 |
| 3          | Combo 5 | Combo 2 | Combo 7 |
| 4          | Combo 3 | Combo 9 | Combo 5 |
| 5          | Combo 4 | Combo 8 | Combo 4 |

Each combination defines a `(μ, Temp)` pair, e.g.:

* Combo 4 → μ = 0.16 h⁻¹, Temp = 31 °C
* Combo 9 → μ = 0.1225 h⁻¹, Temp = 33 °C

The **Doehlert chart** visualizes the design space coverage using only five runs — demonstrating efficient, constraint-compliant optimization.

---

## 🔬 Discussion and Insights

* Relaxing constraint **C4** (global repetition limit) from 2→3 significantly increases computational time (seconds → 30 min).
* Biological constraints (e.g. heat shock avoidance, oxygen limits) play a key role in feasible iDoE planning.
* The iDoE planner balances **statistical design**, **biological feasibility**, and **cost efficiency**, showcasing the power of **computational experiment design** in biotechnology.



