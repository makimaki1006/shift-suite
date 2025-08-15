#!/usr/bin/env python3
"""Test script to verify leave/holiday detection logic"""

import pandas as pd
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def test_leave_detection():
    """Test the leave detection logic"""
    
    # Import the functions we need to test
    from shift_suite.tasks.io_excel import (
        _is_leave_code, 
        _determine_holiday_type_from_code,
        _determine_holiday_type,
        LEAVE_CODES,
        DEFAULT_HOLIDAY_TYPE
    )
    
    print("=" * 60)
    print("LEAVE CODE DETECTION TEST")
    print("=" * 60)
    
    # Test leave code detection
    test_codes = ["休", "有", "希", "×", "L", "2F", "3F", "", "研", "欠", "特", "組", "P有"]
    
    print("\n1. Testing _is_leave_code function:")
    print("-" * 40)
    for code in test_codes:
        is_leave = _is_leave_code(code)
        holiday_type = _determine_holiday_type_from_code(code)
        print(f"Code: '{code}' -> is_leave: {is_leave}, holiday_type: {holiday_type}")
    
    print("\n2. Testing remarks-based holiday type detection:")
    print("-" * 40)
    test_remarks = [
        "有給休暇",
        "希望休",
        "通常勤務",
        "",
        "研修のため休み",
        "欠勤",
        None
    ]
    
    for remark in test_remarks:
        holiday_type = _determine_holiday_type(str(remark) if remark is not None else "")
        print(f"Remark: '{remark}' -> holiday_type: {holiday_type}")
    
    print("\n3. Defined LEAVE_CODES:")
    print("-" * 40)
    for code, htype in LEAVE_CODES.items():
        print(f"  '{code}': '{htype}'")
    
    print("\n4. Testing with sample Excel data:")
    print("-" * 40)
    
    # List Excel files in the directory
    excel_files = list(Path(".").glob("*.xlsx"))
    if excel_files:
        print(f"Found {len(excel_files)} Excel files:")
        for i, f in enumerate(excel_files[:5]):  # Show first 5
            print(f"  {i+1}. {f.name}")
        
        # Try to load and check one file
        test_file = excel_files[0]
        print(f"\nTesting with: {test_file}")
        
        try:
            from shift_suite.tasks.io_excel import load_shift_patterns
            wt_df, code2slots = load_shift_patterns(test_file)
            
            print(f"\nLoaded {len(wt_df)} worktype records")
            
            # Show leave records
            leave_records = wt_df[wt_df['is_leave_code'] == True]
            if not leave_records.empty:
                print(f"\nFound {len(leave_records)} leave code records:")
                for _, row in leave_records.iterrows():
                    print(f"  Code: '{row['code']}' -> holiday_type: '{row['holiday_type']}', slots: {row['parsed_slots_count']}")
            else:
                print("\nNo leave code records found!")
                
            # Show holiday type distribution
            if 'holiday_type' in wt_df.columns:
                print("\nHoliday type distribution:")
                print(wt_df['holiday_type'].value_counts())
                
        except Exception as e:
            print(f"Error loading file: {e}")
    else:
        print("No Excel files found in current directory")

if __name__ == "__main__":
    test_leave_detection()