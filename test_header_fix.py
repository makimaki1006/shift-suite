#!/usr/bin/env python3
# Test header row fix

import sys
import os
sys.path.insert(0, os.getcwd())

print("=== Header Row Fix Test ===")

try:
    import pandas as pd
    from pathlib import Path
    from shift_suite.tasks.io_excel import ingest_excel
    
    # Test data file
    excel_path = Path("デイ_テスト用データ_休日精緻.xlsx")
    
    # Get sheet info
    sheets = pd.ExcelFile(excel_path, engine="openpyxl").sheet_names
    master_sheet = next((s for s in sheets if "勤務" in s), None)
    shift_sheets = [s for s in sheets if s != master_sheet]
    
    print(f"Master sheet: {master_sheet}")
    print(f"Shift sheets: {shift_sheets}")
    
    # Test with different header row values
    for header_row in [0, 1, 2, 3]:
        print(f"\n--- Testing header_row={header_row} ---")
        try:
            long_df, wt_df, unknown_codes = ingest_excel(
                excel_path,
                shift_sheets=shift_sheets,
                header_row=header_row
            )
            print(f"SUCCESS: long_df shape: {long_df.shape}, wt_df shape: {wt_df.shape}")
            print(f"Columns: {long_df.columns.tolist()[:5]}")
            
            # Check if we have the expected columns
            if 'staff' in long_df.columns and 'role' in long_df.columns:
                print("✓ Required columns found!")
                
                # Show sample data
                print("Sample data:")
                print(long_df[['staff', 'role']].head(3))
                
                # This is the correct header row
                print(f"*** header_row={header_row} is CORRECT! ***")
                break
            else:
                print("Missing required columns")
                
        except Exception as e:
            print(f"ERROR: {e}")
            continue
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()