#!/usr/bin/env python3
# Debug Excel column mapping issue

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
    
    if not excel_path.exists():
        print(f"ERROR: Excel file not found: {excel_path}")
        exit(1)
    
    # Read Excel file
    xls = pd.ExcelFile(excel_path, engine="openpyxl")
    print(f"Sheet names: {xls.sheet_names}")
    
    # Check each sheet
    for sheet_name in xls.sheet_names:
        print(f"\n=== Sheet: {sheet_name} ===")
        
        if "勤務" in sheet_name:
            print("Skipping shift pattern sheet")
            continue
        
        # Read sheet with header row 3 (index 2)
        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=2, engine="openpyxl")
        
        print(f"Shape: {df.shape}")
        print(f"Original columns: {df.columns.tolist()}")
        
        # Test the normalize function
        def _normalize(val):
            txt = str(val).replace("　", " ")
            return re.sub(r"\s+", "", txt).strip()
        
        # Column alias mapping
        SHEET_COL_ALIAS = {
            "氏名": "staff",
            "名前": "staff",
            "staff": "staff",
            "name": "staff",
            "従業員": "staff",
            "member": "staff",
            "職種": "role",
            "部署": "role",
            "役職": "role",
            "role": "role",
            "雇用形態": "employment",
            "雇用区分": "employment",
            "employment": "employment",
        }
        
        # Show normalization results
        print(f"Normalized columns:")
        for col in df.columns:
            normalized = _normalize(str(col))
            mapped = SHEET_COL_ALIAS.get(normalized, normalized)
            print(f"  '{col}' -> '{normalized}' -> '{mapped}'")
        
        # Apply mapping
        new_columns = [
            SHEET_COL_ALIAS.get(_normalize(str(c)), _normalize(str(c)))
            for c in df.columns
        ]
        
        print(f"Final mapped columns: {new_columns}")
        
        # Check if staff and role exist
        has_staff = "staff" in new_columns
        has_role = "role" in new_columns
        
        print(f"Has 'staff': {has_staff}")
        print(f"Has 'role': {has_role}")
        
        if not has_staff or not has_role:
            print("❌ Missing required columns!")
            
            # Show first few rows to understand the structure
            print(f"First 5 rows:")
            print(df.head())
            
            # Show columns with their dtypes
            print(f"Column info:")
            for i, col in enumerate(df.columns):
                print(f"  {i}: '{col}' (dtype: {df[col].dtype})")
        else:
            print("✅ Required columns found")
            
        # Check for hidden characters
        print(f"\nColumn character analysis:")
        for col in df.columns:
            col_str = str(col)
            print(f"  '{col_str}' -> bytes: {col_str.encode('utf-8')}")
        
        break  # Only check first data sheet
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()