#!/usr/bin/env python3
# Complete reproduction test using original app.py logic

import sys
import os
import tempfile
import traceback
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.getcwd())

print("=== Complete Reproduction Test ===")

try:
    import pandas as pd
    print("OK: Pandas imported")
    
    # Import main functions from shift_suite
    from shift_suite.tasks.io_excel import ingest_excel
    from shift_suite.tasks.heatmap import build_heatmap
    from shift_suite.tasks.shortage import shortage_and_brief
    from shift_suite.tasks.build_stats import build_stats
    from shift_suite.tasks.anomaly import detect_anomaly
    from shift_suite.tasks.fatigue import train_fatigue
    from shift_suite.tasks.cluster import cluster_staff
    from shift_suite.tasks.skill_nmf import build_skill_matrix
    from shift_suite.tasks.fairness import run_fairness
    from shift_suite.tasks.forecast import build_demand_series, forecast_need
    print("OK: All main modules imported successfully")
    
    # Test data file
    excel_path = Path("デイ_テスト用データ_休日精緻.xlsx")
    if not excel_path.exists():
        print(f"ERROR: Excel file not found: {excel_path}")
        exit(1)
    
    print(f"OK: Excel file found: {excel_path}")
    
    # Get sheet info
    sheets = pd.ExcelFile(excel_path, engine="openpyxl").sheet_names
    master_sheet = next((s for s in sheets if "勤務" in s), None)
    shift_sheets = [s for s in sheets if s != master_sheet]
    
    print(f"OK: Master sheet: {master_sheet}")
    print(f"OK: Shift sheets: {shift_sheets}")
    
    # Create temporary work directory
    work_root = Path(tempfile.mkdtemp())
    out_dir = work_root / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"OK: Work directory: {out_dir}")
    
    # Test parameters matching original app.py logic
    slot = 30
    min_method = "p25"
    ext_opts = ["Stats", "Anomaly", "Fatigue", "Cluster", "Skill", "Fairness", "Need forecast"]
    
    # 1. Ingest
    print("STEP 1/8: Ingest...")
    long_df, wt_df, unknown_codes = ingest_excel(
        excel_path,
        shift_sheets=shift_sheets,
        header_row=3
    )
    print(f"OK: Ingest completed. long_df: {long_df.shape}, wt_df: {wt_df.shape}")
    if unknown_codes:
        print(f"Warning: Unknown codes found: {unknown_codes}")
    
    # 2. Heatmap
    print("STEP 2/8: Heatmap...")
    build_heatmap(long_df, wt_df, out_dir, slot, min_method=min_method)
    print("OK: Heatmap completed")
    
    # 3. Shortage
    print("STEP 3/8: Shortage...")
    shortage_and_brief(out_dir, slot, min_method=min_method)
    print("OK: Shortage completed")
    
    # 4. Stats (optional)
    if "Stats" in ext_opts:
        print("STEP 4/8: Stats...")
        build_stats(out_dir)
        print("OK: Stats completed")
    
    # 5. Anomaly
    if "Anomaly" in ext_opts:
        print("STEP 5/8: Anomaly...")
        detect_anomaly(out_dir)
        print("OK: Anomaly completed")
    
    # 6. Fatigue
    if "Fatigue" in ext_opts:
        print("STEP 6/8: Fatigue...")
        train_fatigue(long_df, out_dir)
        print("OK: Fatigue completed")
    
    # 7. Cluster
    if "Cluster" in ext_opts:
        print("STEP 7/8: Cluster...")
        cluster_staff(long_df, out_dir)
        print("OK: Cluster completed")
    
    # 8. Skill
    if "Skill" in ext_opts:
        print("STEP 8/8: Skill...")
        build_skill_matrix(long_df, out_dir)
        print("OK: Skill completed")
    
    # Fairness
    if "Fairness" in ext_opts:
        print("Extra: Fairness...")
        run_fairness(long_df, out_dir)
        print("OK: Fairness completed")
    
    # Need forecast
    if "Need forecast" in ext_opts:
        print("Extra: Need forecast...")
        csv = build_demand_series(out_dir / "heat_ALL.xlsx", out_dir / "demand_series.csv")
        forecast_need(csv, out_dir / "forecast.xlsx", choose="auto")
        print("OK: Need forecast completed")
    
    print("=== Analysis completed successfully! ===")
    
    # List all output files
    output_files = list(out_dir.glob("*.xlsx")) + list(out_dir.glob("*.parquet")) + list(out_dir.glob("*.csv"))
    print(f"\nGenerated {len(output_files)} output files:")
    for f in sorted(output_files):
        size_kb = f.stat().st_size / 1024
        print(f"  - {f.name} ({size_kb:.1f} KB)")
    
    print(f"\nOutput directory: {out_dir}")
    print("=== Test completed successfully! ===")
    
except Exception as e:
    print(f"ERROR: Test failed: {e}")
    traceback.print_exc()