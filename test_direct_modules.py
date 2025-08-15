#!/usr/bin/env python3
# Direct module test bypassing __init__.py

import sys
import os
sys.path.insert(0, os.getcwd())

# Test direct imports
print("Testing direct imports...")

try:
    # Import core modules directly
    import pandas as pd
    import tempfile
    from pathlib import Path
    
    # Test io_excel directly
    sys.path.append('shift_suite/tasks')
    import io_excel
    print("io_excel loaded successfully")
    
    # Test specific functions
    print("Testing ingest_excel function...")
    
    # Load data using the restored modules
    excel_path = Path("デイ_テスト用データ_休日精緻.xlsx")
    if excel_path.exists():
        print(f"Excel file found: {excel_path}")
        
        # Test sheet reading
        sheets = pd.ExcelFile(excel_path, engine="openpyxl").sheet_names
        print(f"Available sheets: {sheets}")
        
        # Find shift sheets (excluding 勤務区分)
        shift_sheets = [s for s in sheets if s != "勤務区分"]
        print(f"Shift sheets: {shift_sheets}")
        
        if shift_sheets:
            print("Attempting ingest_excel...")
            try:
                long_df, wt_df, unknown_codes = io_excel.ingest_excel(
                    excel_path,
                    shift_sheets=shift_sheets[:1],  # Test with just one sheet
                    header_row=3
                )
                print(f"Success! Long_df shape: {long_df.shape}, wt_df shape: {wt_df.shape}")
                print(f"Unknown codes: {unknown_codes}")
            except Exception as e:
                print(f"ingest_excel failed: {e}")
                import traceback
                traceback.print_exc()
    else:
        print(f"Excel file not found: {excel_path}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()