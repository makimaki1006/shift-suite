#!/usr/bin/env python3
# Test the clean app version without problematic imports

import sys
import os
import tempfile
import traceback
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.getcwd())

print("Testing with clean app version...")

try:
    import pandas as pd
    print("Pandas imported successfully")
    
    # Load the Excel file
    excel_path = Path("デイ_テスト用データ_休日精緻.xlsx")
    if not excel_path.exists():
        print(f"Excel file not found: {excel_path}")
        exit(1)
    
    print(f"Excel file found: {excel_path}")
    
    # Get sheet names
    sheets = pd.ExcelFile(excel_path, engine="openpyxl").sheet_names
    print(f"Available sheets: {sheets}")
    
    # Find master and shift sheets
    master_sheet = next((s for s in sheets if "勤務" in s), None)
    shift_sheets = [s for s in sheets if s != master_sheet]
    
    print(f"Master sheet: {master_sheet}")
    print(f"Shift sheets: {shift_sheets}")
    
    if not master_sheet or not shift_sheets:
        print("Required sheets not found")
        exit(1)
    
    # Try to import specific functions using try-catch for each
    print("Attempting to import core functions...")
    
    # Test individual module imports with error handling
    functions_to_test = []
    
    try:
        from shift_suite.tasks.io_excel import ingest_excel
        functions_to_test.append(("ingest_excel", ingest_excel))
        print("✓ ingest_excel imported")
    except Exception as e:
        print(f"✗ ingest_excel failed: {e}")
    
    try:
        from shift_suite.tasks.heatmap import build_heatmap
        functions_to_test.append(("build_heatmap", build_heatmap))
        print("✓ build_heatmap imported")
    except Exception as e:
        print(f"✗ build_heatmap failed: {e}")
    
    try:
        from shift_suite.tasks.shortage import shortage_and_brief
        functions_to_test.append(("shortage_and_brief", shortage_and_brief))
        print("✓ shortage_and_brief imported")
    except Exception as e:
        print(f"✗ shortage_and_brief failed: {e}")
    
    if functions_to_test:
        print(f"Successfully imported {len(functions_to_test)} functions")
        
        # Test with a minimal example
        if any(name == "ingest_excel" for name, _ in functions_to_test):
            print("Testing ingest_excel...")
            work_root = Path(tempfile.mkdtemp())
            out_dir = work_root / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                long_df, wt_df = ingest_excel(
                    excel_path,
                    shift_sheets=shift_sheets[:1],  # Test with first sheet only
                    master_sheet=master_sheet,
                    header_row=3
                )
                print(f"ingest_excel successful! long_df: {long_df.shape}, wt_df: {wt_df.shape}")
                
                # Test heatmap if available
                if any(name == "build_heatmap" for name, _ in functions_to_test):
                    print("Testing build_heatmap...")
                    build_heatmap(long_df, wt_df, out_dir, 30, min_method="p25")
                    print("build_heatmap successful!")
                    
                    # Check output files
                    output_files = list(out_dir.glob("*.xlsx"))
                    print(f"Generated {len(output_files)} output files:")
                    for f in output_files:
                        print(f"  - {f.name}")
                    
            except Exception as e:
                print(f"Function test failed: {e}")
                traceback.print_exc()
    else:
        print("No functions could be imported")

except Exception as e:
    print(f"Overall test failed: {e}")
    traceback.print_exc()