# iDoE Visualization and Reporting Guide

## Overview

The iDoE project includes comprehensive visualization and documentation tools that generate:
1. **Publication-quality plots** (PNG, 300 dpi) showing design space coverage and experimental paths
2. **Bench-ready tables** (CSV, Excel) with complete parameter schedules for laboratory implementation

All outputs are scientist-friendly with proper units, large readable fonts, and clear formatting suitable for print publication and laboratory use.

---

## Quick Start

### Using Docker (Recommended)
```bash
# Generate all plots and tables
docker-compose up reports

# View outputs
ls reports/plots/    # 8 PNG files
ls reports/tables/   # CSV and Excel files
```

### Using Python Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Generate all reports
python -m src.generate_reports --output-dir reports

# Options:
python -m src.generate_reports --no-plots    # Tables only
python -m src.generate_reports --no-tables   # Plots only
python -m src.generate_reports --total-hours 36.0  # Custom run duration
```

---

## Generated Plots

### Plot A: Heatmap of Combo Usage in iDoE Plan
**File:** `heatmap_usage.png` (163 KB)

**Purpose:** Shows usage count (0, 1, or 2) for each design combination across all experiments.

**Validates:**
- Constraint C3: Each combo used ≤2 times per experiment
- Constraint C4: Each combo used ≤2 times globally
- Constraint C5: All combos covered at least once

**Format:**
- Rows: Combo1 through Combo9
- Columns: Exp1 through ExpN
- Colorbar: Usage count (0-2)
- Colormap: Blues (clear distinction between 0, 1, 2)

---

### Plot B: Doehlert Design and iDoE Experimental Paths
**File:** `design_paths.png` (304 KB)

**Purpose:** Visualizes the 2-factor design space (μ_set vs Temperature) and shows how each experiment navigates through the design points across 3 stages.

**Features:**
- All 9 design points shown as diamond markers
- Each point annotated with combo ID (1-9)
- Center-point replicates (1, 2, 3) shown as "1,2,3"
- Each experiment drawn as a polyline: Stage1 → Stage2 → Stage3
- Legend shows one entry per experiment

**Axes:**
- X: Specific Growth Rate μ_set (h⁻¹)
- Y: Temperature (°C)

---

### Plot C: Combo Usage Heatmap (Alternative)
**File:** `heatmap_usage_alt.png` (163 KB)

**Purpose:** Same data as Plot A but with different terminology and colormap for presentations.

**Differences from Plot A:**
- Axes labeled "Runs" and "Combos" (not "Experiments" and "Design Combination")
- Tick labels: "Run 1", "Combo 1" format
- Colormap: viridis (perceptually uniform)
- Colorbar: "Times used in Run"

---

### Plots D: Run N Timeline (5 files)
**Files:** `run_1_timeline.png` through `run_5_timeline.png` (142-156 KB each)

**Purpose:** Per-run timeline showing step profiles of μ_set and Temperature across the 3 stages.

**Features:**
- Dual y-axis plot:
  - Left axis: μ_set (h⁻¹) in blue
  - Right axis: Temperature (°C) in orange
- X-axis: Time (h) from 0 to total_run_hours (default 30.0)
- Step functions: Exactly 3 flat steps per trace
- Breakpoints at stage boundaries only (10h, 20h for 30h runs)
- Combined legend showing both parameters

**Use case:** Bench scientists can see exact parameter changes and when they occur during each experimental run.

---

## Generated Tables

### Combined Summary Table
**File:** `idoe_plan_combined.csv` (645 bytes)

**Format:** CSV with 6 columns, 15 rows (header + 5 experiments × 3 stages)

**Columns:**
1. **Run** - "Run 1" through "Run 5"
2. **Stage** - "Stage 1", "Stage 2", "Stage 3"
3. **Time (h)** - "0.0–10.0", "10.0–20.0", "20.0–30.0"
4. **Combo #** - Integer 1-9
5. **μ_set (h⁻¹)** - Float with ≤4 decimals (e.g., 0.1475)
6. **Temperature (°C)** - Float with 1 decimal (e.g., 31.0)

**Example rows:**
```csv
Run,Stage,Time (h),Combo #,μ_set (h⁻¹),Temperature (°C)
Run 1,Stage 1,0.0–10.0,9,0.1225,33.0
Run 1,Stage 2,10.0–20.0,6,0.11,31.0
Run 1,Stage 3,20.0–30.0,6,0.11,31.0
...
```

---

### Excel Workbook
**File:** `idoe_plan_workbook.xlsx` (8.8 KB)

**Sheets:**
1. **Summary** - Combined table with all runs (15 rows)
2. **Run_1** through **Run_5** - Individual run sheets (3 rows each)

**Use case:**
- Import into LIMS systems
- Print individual run sheets for technicians
- Integrate with automated bioreactor control systems

---

## Validation

The table generator includes automatic validation that checks:

✅ **Row count:** Exactly `num_experiments × 3` rows
✅ **Combo numbers:** All in range [1, 9]
✅ **No missing values:** All cells populated
✅ **Time windows:** Partition total hours with no gaps/overlaps
✅ **Parameter values:** Match combo definitions from FACTOR_VALUES

Example output:
```
Validating tables...
✓ Row count correct: 15 rows
✓ All combo numbers in valid range [1, 9]
✓ No missing values
✓ Time windows partition 30.0 hours correctly
✓ All parameter values match combo definitions

✅ All validations passed!
```

---

## Customization

### Changing Run Duration
```bash
# 36-hour runs (12h per stage)
python -m src.generate_reports --total-hours 36.0

# Results in time windows:
# Stage 1: 0.0–12.0
# Stage 2: 12.0–24.0
# Stage 3: 24.0–30.0
```

### Using in Your Code
```python
from src.optimizer import IDOEOptimizer
from src.visualization import IDOEVisualizer
from src.tables import IDOETableGenerator
from src.config import FACTOR_VALUES

# Run optimization
optimizer = IDOEOptimizer()
result = optimizer.optimize()

# Generate plots
visualizer = IDOEVisualizer(
    result=result,
    combos=FACTOR_VALUES,
    total_run_hours=30.0,
    output_dir="my_plots"
)
visualizer.generate_all_plots()

# Generate tables
table_gen = IDOETableGenerator(
    result=result,
    combos=FACTOR_VALUES,
    total_run_hours=30.0,
    output_dir="my_tables"
)
table_gen.generate_all_outputs()
```

---

## File Specifications

### Plot Settings
- Format: PNG
- DPI: 300 (publication quality)
- Font sizes: 11-16 pt (readable on A4/Letter)
- Color: Matplotlib defaults (no hard-coded colors)
- Backend: Agg (works in Docker without display)

### Table Settings
- CSV: UTF-8 encoding, comma-separated
- Excel: XLSX format, multiple sheets
- Time format: "start–end" with 1 decimal place
- μ_set precision: ≤4 decimals
- Temperature precision: 1 decimal

---

## Troubleshooting

### "No display name and no $DISPLAY environment variable"
**Solution:** The code sets `MPLBACKEND=Agg` automatically. If running manually:
```bash
export MPLBACKEND=Agg
python -m src.generate_reports
```

### Plots are blank or not saving
**Check:**
1. Output directory exists and is writable
2. All dependencies installed: `pip install matplotlib pandas openpyxl`
3. No errors in console output

### Excel file won't open
**Check:**
1. openpyxl is installed: `pip install openpyxl`
2. File permissions are correct
3. Excel version supports .xlsx format

---

## Integration with CI/CD

The report generation can be integrated into automated workflows:

```yaml
# Example GitHub Actions
- name: Generate iDoE Reports
  run: docker-compose up reports

- name: Upload Reports
  uses: actions/upload-artifact@v3
  with:
    name: idoe-reports
    path: reports/
```

---

## References

All plots and tables follow the methodology from:

> von Stosch, M., & Willis, M. J. (2017). Intensified Design of Experiments for Upstream Bioreactors. *Engineering in Life Sciences*, 17(11), 1173-1184.

---

## Support

For questions or issues with visualization/reporting:
1. Check this guide
2. Review the [README.md](README.md) for general usage
3. Examine the [SUMMARY.md](SUMMARY.md) for project overview
4. Open an issue on GitHub with:
   - Command used
   - Error messages
   - Expected vs actual output
