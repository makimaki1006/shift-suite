#!/usr/bin/env python3
"""
Script to analyze the Excel test data file for shift analysis
Focuses on understanding the structure and rest day representation
"""

import pandas as pd
import numpy as np
import sys
import os

def analyze_excel_file(file_path):
    """Analyze the Excel file structure and contents"""
    
    print(f"Analyzing Excel file: {file_path}")
    print("=" * 60)
    
    if not os.path.exists(file_path):
        print(f"ERROR: File does not exist: {file_path}")
        return
    
    try:
        # Read the Excel file - try different sheets if available
        xlsx_file = pd.ExcelFile(file_path)
        print(f"Sheet names available: {xlsx_file.sheet_names}")
        print()
        
        for sheet_name in xlsx_file.sheet_names:
            print(f"\n{'='*40}")
            print(f"ANALYZING SHEET: {sheet_name}")
            print(f"{'='*40}")
            
            # Read the sheet
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            print(f"Shape: {df.shape} (rows: {df.shape[0]}, columns: {df.shape[1]})")
            print()
            
            # Show basic info
            print("COLUMN NAMES:")
            for i, col in enumerate(df.columns):
                print(f"  {i:2d}: '{col}' (type: {df[col].dtype})")
            print()
            
            # Show first few rows
            print("FIRST 10 ROWS:")
            print(df.head(10).to_string())
            print()
            
            # Look for rest day symbols (×)
            print("SEARCHING FOR REST DAY SYMBOLS ('×'):")
            rest_day_found = False
            for col in df.columns:
                if df[col].dtype == 'object':  # Text columns
                    mask = df[col].astype(str).str.contains('×', na=False)
                    if mask.any():
                        rest_day_found = True
                        count = mask.sum()
                        print(f"  Column '{col}': Found {count} '×' symbols")
                        
                        # Show some examples
                        examples = df[mask][col].head(5).tolist()
                        print(f"    Examples: {examples}")
            
            if not rest_day_found:
                print("  No '×' symbols found in this sheet")
            print()
            
            # Look for other potential rest day indicators
            print("SEARCHING FOR OTHER REST DAY INDICATORS:")
            indicators = ['休', 'OFF', 'off', 'Rest', 'rest', '休み', '休日']
            for indicator in indicators:
                found_indicator = False
                for col in df.columns:
                    if df[col].dtype == 'object':
                        mask = df[col].astype(str).str.contains(indicator, na=False)
                        if mask.any():
                            found_indicator = True
                            count = mask.sum()
                            print(f"  Found '{indicator}' in column '{col}': {count} occurrences")
                
                if not found_indicator:
                    print(f"  No '{indicator}' found")
            print()
            
            # Analyze unique values in each column (first 20 columns only to avoid clutter)
            print("UNIQUE VALUES ANALYSIS (first 20 columns):")
            cols_to_analyze = df.columns[:20] if len(df.columns) > 20 else df.columns
            
            for col in cols_to_analyze:
                unique_vals = df[col].dropna().unique()
                if len(unique_vals) < 20:  # Only show if manageable number of unique values
                    print(f"  Column '{col}': {list(unique_vals)}")
                else:
                    print(f"  Column '{col}': {len(unique_vals)} unique values (too many to display)")
            print()
            
            # Look for date-like patterns
            print("DATE PATTERN ANALYSIS:")
            for col in df.columns:
                col_str = str(col).lower()
                if any(date_word in col_str for date_word in ['date', '日', '月', '年', 'day', 'time']):
                    print(f"  Potential date column: '{col}'")
                    print(f"    Sample values: {df[col].head(3).tolist()}")
            print()
            
            # Check for staff name patterns
            print("STAFF NAME ANALYSIS:")
            for col in df.columns:
                col_str = str(col).lower()
                if any(name_word in col_str for name_word in ['name', '名前', 'staff', 'スタッフ', '氏名']):
                    print(f"  Potential staff name column: '{col}'")
                    if df[col].dtype == 'object':
                        unique_names = df[col].dropna().unique()
                        print(f"    Number of unique names: {len(unique_names)}")
                        if len(unique_names) < 20:
                            print(f"    Names: {list(unique_names)}")
            print()
            
    except Exception as e:
        print(f"ERROR reading Excel file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import os
    import sys
    
    # Get the current directory and construct the file path
    current_dir = os.getcwd()
    file_path = os.path.join(current_dir, "ショート_テスト用データ.xlsx")
    
    print(f"Current directory: {current_dir}")
    print(f"Looking for file: {file_path}")
    print(f"File exists: {os.path.exists(file_path)}")
    print()
    
    analyze_excel_file(file_path)