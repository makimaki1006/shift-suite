#!/usr/bin/env python3
# Complete verification test with fixed io_excel.py

import sys
import os
sys.path.insert(0, os.getcwd())

print("=== Complete Verification Test ===")

try:
    import pandas as pd
    from pathlib import Path
    from shift_suite.tasks.io_excel import ingest_excel
    from shift_suite.tasks.heatmap import build_heatmap
    import glob
    
    # Test data file
    excel_path = Path("デイ_テスト用データ_休日精緻.xlsx")
    
    if not excel_path.exists():
        print(f"ERROR: Test file not found: {excel_path}")
        sys.exit(1)
    
    # Test with the corrected header_row=0
    print("1. Testing data ingestion with header_row=0...")
    
    # Get sheet info
    sheets = pd.ExcelFile(excel_path, engine="openpyxl").sheet_names
    master_sheet = next((s for s in sheets if "勤務" in s), None)
    shift_sheets = [s for s in sheets if s != master_sheet]
    
    print(f"   Master sheet: {master_sheet}")
    print(f"   Shift sheets: {shift_sheets}")
    
    # Test ingestion
    long_df, wt_df, unknown_codes = ingest_excel(
        excel_path,
        shift_sheets=shift_sheets,
        header_row=0  # Fixed header row
    )
    
    print(f"   SUCCESS: Data ingested successfully")
    print(f"   Long DF shape: {long_df.shape}")
    print(f"   Staff count: {long_df['staff'].nunique()}")
    print(f"   Role count: {long_df['role'].nunique()}")
    print(f"   Date range: {long_df['ds'].dt.date.min()} to {long_df['ds'].dt.date.max()}")
    
    # Test heatmap generation
    print("\n2. Testing heatmap generation...")
    
    # Create output directory
    output_dir = Path("temp_verification_output")
    output_dir.mkdir(exist_ok=True)
    
    # Run heatmap analysis
    build_heatmap(
        long_df=long_df,
        wt_df=wt_df,
        out_dir_path=output_dir,
        force_recalc=True
    )
    
    print(f"   SUCCESS: Heatmap generated")
    
    # Check for need_per_date_slot files
    print("\n3. Checking for need_per_date_slot files...")
    
    need_files = list(output_dir.glob("need_per_date_slot_*.parquet"))
    print(f"   Found {len(need_files)} need_per_date_slot files:")
    
    for file in sorted(need_files):
        file_size = file.stat().st_size
        print(f"     {file.name} ({file_size} bytes)")
        
        # Check file content
        try:
            df = pd.read_parquet(file)
            print(f"       Content: {df.shape} rows x {df.columns.tolist()}")
        except Exception as e:
            print(f"       Error reading file: {e}")
    
    # Summary
    print(f"\n=== VERIFICATION SUMMARY ===")
    print(f"✓ Data ingestion: SUCCESS with header_row=0")
    print(f"✓ Long DataFrame: {long_df.shape} records")
    print(f"✓ Heatmap generation: SUCCESS")
    print(f"✓ Need files generated: {len(need_files)} files")
    
    if len(need_files) > 0:
        print(f"✓ ISSUE RESOLVED: need_per_date_slot files are now being generated!")
    else:
        print(f"✗ ISSUE PERSISTS: No need_per_date_slot files found")
    
    # Clean up
    import shutil
    shutil.rmtree(output_dir)
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()