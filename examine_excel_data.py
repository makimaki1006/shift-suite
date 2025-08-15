#!/usr/bin/env python3
"""
Examine Excel data to understand the structure and location of × symbols
"""

import pandas as pd
from pathlib import Path

def examine_excel_file(excel_file):
    print(f'Examining {excel_file}...')
    
    if not Path(excel_file).exists():
        print(f'File not found: {excel_file}')
        return
    
    # Check sheet names
    xl_file = pd.ExcelFile(excel_file)
    print(f'Sheet names: {xl_file.sheet_names}')
    
    # Read the first shift sheet (not the pattern sheet)
    for sheet_name in xl_file.sheet_names:
        if sheet_name != '勤務区分':
            print(f'\nExamining sheet: {sheet_name}')
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=2)
            print(f'Shape: {df.shape}')
            print(f'Columns: {df.columns.tolist()}')
            
            # Look for staff column
            staff_col = None
            for col in df.columns:
                col_str = str(col)
                if '氏名' in col_str or '名前' in col_str or 'staff' in col_str.lower():
                    staff_col = col
                    break
            
            if staff_col:
                print(f'Staff column: {staff_col}')
                staff_values = df[staff_col].dropna().unique()
                print(f'Staff values (first 15): {list(staff_values[:15])}')
                
                # Check for rest symbols in staff column
                rest_symbols = ['×', 'X', 'x', '休', '欠', 'OFF', '-', '−']
                found_symbols = []
                for symbol in rest_symbols:
                    if symbol in staff_values:
                        found_symbols.append(symbol)
                        count = (df[staff_col] == symbol).sum()
                        print(f'  Found {symbol} in staff column: {count} occurrences')
                
                print(f'Rest symbols found in staff: {found_symbols}')
                
                # Check date columns for shift codes
                date_cols = []
                for col in df.columns:
                    col_str = str(col)
                    # Look for columns that look like dates (numbers, dates)
                    if (col_str.isdigit() or 
                        '/' in col_str or 
                        '-' in col_str or
                        '(' in col_str and ')' in col_str):
                        date_cols.append(col)
                
                print(f'Date columns found: {len(date_cols)}')
                print(f'Date columns sample: {date_cols[:5]}')
                
                # Check for × symbols in date columns (shift codes)
                if date_cols:
                    for i, sample_col in enumerate(date_cols[:3]):  # Check first 3 date columns
                        shift_values = df[sample_col].dropna().unique()
                        print(f'\nShift codes in column {sample_col}: {list(shift_values)}')
                        
                        # Check for rest symbols in shift codes
                        for symbol in rest_symbols:
                            if symbol in shift_values:
                                count = (df[sample_col] == symbol).sum()
                                print(f'  Found rest symbol {symbol} in shift codes: {count} occurrences')
                
                # Show sample data
                print(f'\nSample data (first 5 rows):')
                sample_cols = [staff_col] + date_cols[:3]
                print(df[sample_cols].head())
            
            break  # Only examine first shift sheet

def main():
    excel_files = [
        'デイ_テスト用データ_休日精緻.xlsx',
        'ショート_テスト用データ.xlsx'
    ]
    
    for excel_file in excel_files:
        examine_excel_file(excel_file)
        print('='*50)

if __name__ == "__main__":
    main()