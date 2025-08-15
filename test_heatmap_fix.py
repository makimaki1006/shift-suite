#!/usr/bin/env python3
# Test the heatmap fix for need_per_date_slot files

import sys
import os
import tempfile
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.getcwd())

print("=== Testing Heatmap Fix ===")

try:
    import pandas as pd
    from shift_suite.tasks.io_excel import ingest_excel
    from shift_suite.tasks.heatmap import build_heatmap
    
    # Test data file
    excel_path = Path("デイ_テスト用データ_休日精緻.xlsx")
    if not excel_path.exists():
        print(f"ERROR: Excel file not found: {excel_path}")
        exit(1)
    
    # Get sheet info
    sheets = pd.ExcelFile(excel_path, engine="openpyxl").sheet_names
    master_sheet = next((s for s in sheets if "勤務" in s), None)
    shift_sheets = [s for s in sheets if s != master_sheet]
    
    print(f"Using shift sheets: {shift_sheets}")
    
    # Create temporary work directory
    work_root = Path(tempfile.mkdtemp())
    out_dir = work_root / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Output directory: {out_dir}")
    
    # 1. Ingest
    print("Step 1: Ingest...")
    long_df, wt_df, unknown_codes = ingest_excel(
        excel_path,
        shift_sheets=shift_sheets,
        header_row=3
    )
    print(f"Ingest completed. long_df: {long_df.shape}, wt_df: {wt_df.shape}")
    
    # 2. Heatmap
    print("Step 2: Heatmap...")
    build_heatmap(long_df, wt_df, out_dir, 30, min_method="p25")
    print("Heatmap completed")
    
    # Check all output files
    output_files = list(out_dir.glob("*.xlsx")) + list(out_dir.glob("*.parquet")) + list(out_dir.glob("*.csv"))
    print(f"\nGenerated {len(output_files)} output files:")
    
    need_per_date_slot_files = []
    for f in sorted(output_files):
        size_kb = f.stat().st_size / 1024
        print(f"  - {f.name} ({size_kb:.1f} KB)")
        if f.name.startswith("need_per_date_slot"):
            need_per_date_slot_files.append(f.name)
    
    print(f"\nFound {len(need_per_date_slot_files)} need_per_date_slot files:")
    for f in need_per_date_slot_files:
        print(f"  ✓ {f}")
    
    if len(need_per_date_slot_files) > 1:  # Should have at least the general one plus role/employment specific ones
        print("\n✅ SUCCESS: Multiple need_per_date_slot files generated!")
        print("The fix appears to be working correctly.")
    else:
        print("\n❌ ISSUE: Only found general need_per_date_slot.parquet file.")
        print("Role/employment specific files may not be generated.")
    
    print(f"\nTest completed. Output directory: {out_dir}")
    
except Exception as e:
    print(f"ERROR: Test failed: {e}")
    import traceback
    traceback.print_exc()