#!/usr/bin/env python3
# Final test without Unicode issues

import sys
import os
import tempfile
import traceback
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.getcwd())

print("Testing restored modules...")

try:
    import pandas as pd
    print("OK: Pandas imported successfully")
    
    # Load the Excel file
    excel_path = Path("デイ_テスト用データ_休日精緻.xlsx")
    if not excel_path.exists():
        print(f"ERROR: Excel file not found: {excel_path}")
        exit(1)
    
    print(f"OK: Excel file found: {excel_path}")
    
    # Get sheet names
    sheets = pd.ExcelFile(excel_path, engine="openpyxl").sheet_names
    print(f"OK: Available sheets: {sheets}")
    
    # Find master and shift sheets
    master_sheet = next((s for s in sheets if "勤務" in s), None)
    shift_sheets = [s for s in sheets if s != master_sheet]
    
    print(f"OK: Master sheet: {master_sheet}")
    print(f"OK: Shift sheets: {shift_sheets}")
    
    if not master_sheet or not shift_sheets:
        print("ERROR: Required sheets not found")
        exit(1)
    
    # Test imports
    print("Testing module imports...")
    
    try:
        from shift_suite.tasks.io_excel import ingest_excel
        print("OK: ingest_excel imported")
        
        from shift_suite.tasks.heatmap import build_heatmap  
        print("OK: build_heatmap imported")
        
        from shift_suite.tasks.shortage import shortage_and_brief
        print("OK: shortage_and_brief imported")
        
        from shift_suite.tasks.build_stats import build_stats
        print("OK: build_stats imported")
        
        # Test the full pipeline
        print("Testing full analysis pipeline...")
        
        work_root = Path(tempfile.mkdtemp())
        out_dir = work_root / "out"
        out_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"OK: Created output directory: {out_dir}")
        
        # 1. Ingest
        print("STEP 1/4: Running ingest_excel...")
        long_df, wt_df, unknown_codes = ingest_excel(
            excel_path,
            shift_sheets=shift_sheets,
            header_row=3
        )
        print(f"OK: ingest_excel completed. long_df: {long_df.shape}, wt_df: {wt_df.shape}")
        
        # 2. Heatmap
        print("STEP 2/4: Running build_heatmap...")
        build_heatmap(long_df, wt_df, out_dir, 30, min_method="p25")
        print("OK: build_heatmap completed")
        
        # 3. Shortage
        print("STEP 3/4: Running shortage_and_brief...")
        shortage_and_brief(out_dir, 30, min_method="p25")
        print("OK: shortage_and_brief completed")
        
        # 4. Stats
        print("STEP 4/4: Running build_stats...")
        build_stats(out_dir)
        print("OK: build_stats completed")
        
        # Check output files
        output_files = list(out_dir.glob("*.xlsx")) + list(out_dir.glob("*.parquet"))
        print(f"OK: Generated {len(output_files)} output files:")
        for f in sorted(output_files):
            print(f"  - {f.name}")
        
        print(f"SUCCESS: All analysis completed successfully!")
        print(f"Output directory: {out_dir}")
        
    except Exception as e:
        print(f"ERROR: Analysis failed: {e}")
        traceback.print_exc()

except Exception as e:
    print(f"ERROR: Overall test failed: {e}")
    traceback.print_exc()