#!/usr/bin/env python3
# Simple test to check if need_per_date_slot files are created

import sys
import os
import tempfile
from pathlib import Path
import logging

# Suppress debug logs
logging.getLogger().setLevel(logging.WARNING)

# Add current directory to path
sys.path.insert(0, os.getcwd())

print("=== Testing Need Files Creation ===")

try:
    import pandas as pd
    from shift_suite.tasks.io_excel import ingest_excel
    from shift_suite.tasks.heatmap import build_heatmap
    
    # Test data file
    excel_path = Path("デイ_テスト用データ_休日精緻.xlsx")
    
    # Get sheet info
    sheets = pd.ExcelFile(excel_path, engine="openpyxl").sheet_names
    master_sheet = next((s for s in sheets if "勤務" in s), None)
    shift_sheets = [s for s in sheets if s != master_sheet]
    
    # Create temporary work directory
    work_root = Path(tempfile.mkdtemp())
    out_dir = work_root / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Output directory: {out_dir}")
    
    # Ingest
    print("Step 1: Ingest...")
    long_df, wt_df, unknown_codes = ingest_excel(
        excel_path,
        shift_sheets=shift_sheets,
        header_row=3
    )
    
    # Heatmap
    print("Step 2: Heatmap...")
    build_heatmap(long_df, wt_df, out_dir, 30, min_method="p25")
    
    # Check need_per_date_slot files
    need_files = list(out_dir.glob("need_per_date_slot*.parquet"))
    
    print(f"\nFound {len(need_files)} need_per_date_slot files:")
    for f in sorted(need_files):
        size_kb = f.stat().st_size / 1024
        print(f"  ✓ {f.name} ({size_kb:.1f} KB)")
    
    # Check for specific patterns
    general_need = [f for f in need_files if f.name == "need_per_date_slot.parquet"]
    role_need = [f for f in need_files if "role_" in f.name]
    emp_need = [f for f in need_files if "emp_" in f.name]
    
    print(f"\nBreakdown:")
    print(f"  - General need file: {len(general_need)}")
    print(f"  - Role-specific files: {len(role_need)}")
    print(f"  - Employment-specific files: {len(emp_need)}")
    
    if len(need_files) >= 3:  # Should have general + role + employment files
        print("\n✅ SUCCESS: Multiple need_per_date_slot files generated!")
        print("The fix is working correctly.")
    else:
        print("\n❌ ISSUE: Not enough need_per_date_slot files generated.")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()