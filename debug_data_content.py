#!/usr/bin/env python3
# Debug data content to understand dynamic role/employment detection

import sys
import os
sys.path.insert(0, os.getcwd())

print("=== Data Content Analysis ===")

try:
    import pandas as pd
    from shift_suite.tasks.io_excel import ingest_excel
    from pathlib import Path
    
    # Load the Excel data
    excel_path = Path("デイ_テスト用データ_休日精緻.xlsx")
    shift_sheets = ["R7.2", "R7.6"]
    
    print("Step 1: Loading data...")
    long_df, wt_df, unknown_codes = ingest_excel(
        excel_path,
        shift_sheets=shift_sheets,
        header_row=3
    )
    
    print(f"Long_df shape: {long_df.shape}")
    print(f"Columns: {long_df.columns.tolist()}")
    
    # Analyze role and employment data
    print("\n=== Role Analysis ===")
    if 'role' in long_df.columns:
        unique_roles = long_df['role'].unique()
        print(f"Unique roles found: {len(unique_roles)}")
        for role in sorted(unique_roles):
            if role and str(role) != 'nan':
                count = len(long_df[long_df['role'] == role])
                print(f"  - {role}: {count} records")
    else:
        print("ERROR: No 'role' column found!")
    
    print("\n=== Employment Analysis ===")
    if 'employment' in long_df.columns:
        unique_emp = long_df['employment'].unique()
        print(f"Unique employment types found: {len(unique_emp)}")
        for emp in sorted(unique_emp):
            if emp and str(emp) != 'nan':
                count = len(long_df[long_df['employment'] == emp])
                print(f"  - {emp}: {count} records")
    else:
        print("ERROR: No 'employment' column found!")
    
    print("\n=== Staff Analysis ===")
    if 'staff' in long_df.columns:
        unique_staff = long_df['staff'].unique()
        print(f"Unique staff found: {len(unique_staff)}")
        print("Sample staff names:")
        for staff in sorted(unique_staff)[:10]:
            if staff and str(staff) != 'nan':
                print(f"  - {staff}")
    
    print("\n=== Sample Data ===")
    print(long_df.head(10).to_string())
    
    print("\n=== Non-empty role/employment combinations ===")
    if 'role' in long_df.columns and 'employment' in long_df.columns:
        filtered_df = long_df[(long_df['role'].notna()) & (long_df['role'] != '') & 
                             (long_df['employment'].notna()) & (long_df['employment'] != '')]
        print(f"Records with both role and employment: {len(filtered_df)}")
        
        if len(filtered_df) > 0:
            role_emp_combinations = filtered_df.groupby(['role', 'employment']).size().reset_index(name='count')
            print("Role-Employment combinations:")
            print(role_emp_combinations.to_string())
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()