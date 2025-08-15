#!/usr/bin/env python3
# Simple debug without emoji

import sys
import os
sys.path.insert(0, os.getcwd())

print("=== Excel Column Debug ===")

try:
    import pandas as pd
    import re
    from pathlib import Path
    
    # Excel file path
    excel_path = Path("デイ_テスト用データ_休日精緻.xlsx")
    
    # Read Excel file
    xls = pd.ExcelFile(excel_path, engine="openpyxl")
    print(f"Sheet names: {xls.sheet_names}")
    
    # Check R7.2 sheet
    sheet_name = "R7.2"
    print(f"\n=== Sheet: {sheet_name} ===")
    
    # Read sheet with header row 3 (index 2)
    df = pd.read_excel(excel_path, sheet_name=sheet_name, header=2, engine="openpyxl")
    
    print(f"Shape: {df.shape}")
    print(f"Original columns (first 5): {df.columns.tolist()[:5]}")
    
    # Show actual column names in detail
    print(f"\nDetailed column analysis:")
    for i, col in enumerate(df.columns[:5]):
        col_str = str(col)
        print(f"  Column {i}: '{col_str}'")
        print(f"    Bytes: {col_str.encode('utf-8')}")
        print(f"    Length: {len(col_str)}")
        
        # Check if it contains expected characters
        if "氏名" in col_str:
            print(f"    >>> Contains '氏名' (staff name)")
        if "職種" in col_str:
            print(f"    >>> Contains '職種' (role)")
        if "雇用" in col_str:
            print(f"    >>> Contains '雇用' (employment)")
    
    # Check first few rows
    print(f"\nFirst 3 rows:")
    print(df.head(3))
    
    # The issue might be with header row selection
    print(f"\nTrying different header rows:")
    for header_row in [0, 1, 2, 3]:
        try:
            df_test = pd.read_excel(excel_path, sheet_name=sheet_name, header=header_row, engine="openpyxl")
            print(f"  Header row {header_row}: {df_test.columns.tolist()[:3]}")
        except Exception as e:
            print(f"  Header row {header_row}: ERROR - {e}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()