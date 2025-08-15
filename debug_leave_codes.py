#!/usr/bin/env python3
"""Debug script to trace why leave codes are not being recognized"""

import logging
import pandas as pd
from pathlib import Path
from shift_suite.tasks.io_excel import (
    load_shift_patterns, 
    ingest_excel, 
    LEAVE_CODES,
    _is_leave_code,
    _normalize,
    _determine_holiday_type_from_code
)
from shift_suite.logger_config import configure_logging

# Enable detailed logging
configure_logging(level=logging.DEBUG)
log = logging.getLogger(__name__)

# Test files
test_files = [
    "ショート_テスト用データ.xlsx",
    "デイ_テスト用データ_休日精緻.xlsx"
]

for file_name in test_files:
    file_path = Path(file_name)
    if not file_path.exists():
        log.warning(f"File not found: {file_name}")
        continue
    
    print(f"\n{'='*80}")
    print(f"Testing file: {file_name}")
    print(f"{'='*80}")
    
    # Step 1: Load shift patterns and check leave code detection
    print("\n1. Loading shift patterns...")
    try:
        wt_df, code2slots = load_shift_patterns(file_path)
        
        print(f"\nTotal patterns loaded: {len(wt_df)}")
        print("\nLEAVE_CODES defined in constants:")
        for code, desc in LEAVE_CODES.items():
            print(f"  '{code}': {desc}")
        
        # Check which codes are detected as leave codes
        print("\n2. Checking leave code detection in wt_df:")
        leave_codes_in_wt = wt_df[wt_df['is_leave_code'] == True]
        if not leave_codes_in_wt.empty:
            print("\nDetected leave codes:")
            for _, row in leave_codes_in_wt.iterrows():
                print(f"  Code: '{row['code']}', Holiday Type: '{row['holiday_type']}', Slots: {row['parsed_slots_count']}")
        else:
            print("  No leave codes detected!")
        
        # Check all codes
        print("\n3. All shift codes in pattern sheet:")
        for _, row in wt_df.iterrows():
            code = row['code']
            is_leave = _is_leave_code(code)
            holiday_from_code = _determine_holiday_type_from_code(code)
            print(f"  Code: '{code}'")
            print(f"    - is_leave_code: {is_leave}")
            print(f"    - holiday_type_from_code: {holiday_from_code}")
            print(f"    - final holiday_type: {row['holiday_type']}")
            print(f"    - parsed_slots_count: {row['parsed_slots_count']}")
            print(f"    - start: {row.get('start_original', '')}, end: {row.get('end_original', '')}")
        
    except Exception as e:
        print(f"Error loading shift patterns: {e}")
        continue
    
    # Step 2: Load full data and check filtering
    print("\n4. Loading full shift data...")
    try:
        # Get sheet names
        xl = pd.ExcelFile(file_path)
        shift_sheets = [s for s in xl.sheet_names if s != "勤務区分"]
        
        long_df, wt_df, unknown_codes = ingest_excel(
            file_path,
            shift_sheets=shift_sheets,
            header_row=2,
            year_month_cell_location="A1"
        )
        
        print(f"\nTotal records in long_df: {len(long_df)}")
        
        # Check holiday_type distribution
        if 'holiday_type' in long_df.columns:
            print("\n5. Holiday type distribution in final data:")
            holiday_counts = long_df['holiday_type'].value_counts()
            for htype, count in holiday_counts.items():
                print(f"  {htype}: {count}")
        
        # Check if any leave codes exist in the data
        print("\n6. Checking for leave codes in final data:")
        for code in LEAVE_CODES.keys():
            code_records = long_df[long_df['code'] == code]
            if not code_records.empty:
                print(f"\n  Code '{code}' found: {len(code_records)} records")
                # Show sample records
                sample = code_records.head(3)
                for _, rec in sample.iterrows():
                    print(f"    Staff: {rec['staff']}, Date: {rec['ds']}, Holiday Type: {rec['holiday_type']}, Slots: {rec.get('parsed_slots_count', 0)}")
        
        # Check for any non-'通常勤務' records
        print("\n7. Non-通常勤務 records:")
        non_normal = long_df[long_df['holiday_type'] != '通常勤務']
        if non_normal.empty:
            print("  No non-通常勤務 records found!")
        else:
            print(f"  Found {len(non_normal)} non-通常勤務 records")
            
    except Exception as e:
        print(f"Error loading full data: {e}")
        import traceback
        traceback.print_exc()