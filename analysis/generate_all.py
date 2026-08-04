"""
Orchestrator — runs all five analysis scripts in sequence.

Called during Docker build to pre-generate all charts and JSON outputs.
Output directories are created automatically.

Note: analysis scripts are numbered (01_–05_) for readability and ordering.
Python cannot import them by name directly, so importlib is used.

Usage:
  python analysis/generate_all.py
"""

import importlib.util
import os
import sys
import time

# Ensure the analysis directory is on the path
ANALYSIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ANALYSIS_DIR)

from data_loader import load_data
from validate_data import validate, DataValidationError
from _chart_style import apply_brand_style


def _load_script(filename):
    """Load a numbered analysis script as a module via importlib."""
    path = os.path.join(ANALYSIS_DIR, filename)
    spec = importlib.util.spec_from_file_location(filename, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    print("=" * 55)
    print("  Marketing Campaign Analysis — Generating outputs")
    print("=" * 55)

    t0 = time.time()
    apply_brand_style()

    print("\n[0] Loading and validating dataset...")
    df_full, df_conv = load_data()
    print(f"    Full dataset: {len(df_full):,} rows")
    print(f"    Conversion dataset: {len(df_conv):,} rows")
    try:
        validate(df_full)
    except DataValidationError as e:
        print(str(e))
        sys.exit(1)

    scripts = [
        ("01_executive_summary.py",   "[1] Executive Summary"),
        ("02_recommendations.py",     "[2] Recommendations & Visualizations"),
        ("03_budget_allocation.py",   "[3] Budget Allocation Hypotheses"),
        ("04_patterns_anomalies.py",  "[4] Key Patterns & Anomalies"),
        ("05_data_gaps.py",           "[5] Data Gaps & Additional Inputs"),
        ("dashboard_data.py",         "[+] Dashboard data (KPIs, channels, markets)"),
    ]

    for filename, label in scripts:
        print(f"\n{label}...")
        mod = _load_script(filename)
        mod.run(df_full, df_conv)

    elapsed = round(time.time() - t0, 1)
    print(f"\n{'='*55}")
    print(f"  All outputs generated in {elapsed}s")
    print(f"  Charts  -> output/charts/")
    print(f"  Data    -> output/data/")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
