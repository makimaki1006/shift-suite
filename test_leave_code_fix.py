#!/usr/bin/env python3
"""Test script to verify that leave codes are now being recognized"""

import sys
from pathlib import Path
import pandas as pd
import logging

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from shift_suite.tasks.io_excel import load_shift_patterns, ingest_excel, LEAVE_CODES
from shift_suite.logger_config import configure_logging

# Enable logging to see the results
configure_logging(level=logging.INFO)
log = logging.getLogger(__name__)

def test_leave_code_recognition():
    """Test that leave codes are properly recognized"""
    print("🔍 Testing leave code recognition...")
    
    # List of test files
    test_files = [
        "ショート_テスト用データ.xlsx",
        "デイ_テスト用データ_休日精緻.xlsx"
    ]
    
    for file_name in test_files:
        file_path = Path(file_name)
        if not file_path.exists():
            print(f"⚠️ File not found: {file_name}")
            continue
        
        print(f"\n{'='*60}")
        print(f"📁 Testing file: {file_name}")
        print(f"{'='*60}")
        
        try:
            # Test 1: Load shift patterns and check for leave codes
            print("\n1️⃣ Testing shift pattern loading...")
            wt_df, code2slots = load_shift_patterns(file_path)
            
            print(f"   Total patterns loaded: {len(wt_df)}")
            
            # Check for leave codes
            leave_patterns = wt_df[wt_df['is_leave_code'] == True]
            if not leave_patterns.empty:
                print(f"   ✅ Found {len(leave_patterns)} leave code patterns:")
                for _, row in leave_patterns.iterrows():
                    print(f"      • Code: '{row['code']}' → Holiday Type: '{row['holiday_type']}' (Slots: {row['parsed_slots_count']})")
            else:
                print("   ❌ No leave codes detected in shift patterns!")
                
            # Check if any of the defined LEAVE_CODES are present
            found_leave_codes = []
            for code in LEAVE_CODES.keys():
                if code in wt_df['code'].values:
                    pattern_row = wt_df[wt_df['code'] == code].iloc[0]
                    found_leave_codes.append({
                        'code': code,
                        'is_leave': pattern_row['is_leave_code'],
                        'holiday_type': pattern_row['holiday_type']
                    })
            
            if found_leave_codes:
                print(f"\n   📋 LEAVE_CODES found in patterns:")
                for item in found_leave_codes:
                    status = "✅" if item['is_leave'] else "❌"
                    print(f"      {status} '{item['code']}' → is_leave: {item['is_leave']}, holiday_type: '{item['holiday_type']}'")
            
            # Test 2: Load full data and check holiday types
            print(f"\n2️⃣ Testing full data ingestion...")
            xl = pd.ExcelFile(file_path)
            shift_sheets = [s for s in xl.sheet_names if s != "勤務区分"]
            
            long_df, wt_df, unknown_codes = ingest_excel(
                file_path,
                shift_sheets=shift_sheets,
                header_row=2,
                year_month_cell_location="A1"
            )
            
            print(f"   Total records: {len(long_df)}")
            
            if 'holiday_type' in long_df.columns:
                holiday_counts = long_df['holiday_type'].value_counts()
                print(f"\n   📊 Holiday type distribution:")
                for htype, count in holiday_counts.items():
                    print(f"      • {htype}: {count} records")
                
                # Check if leave records exist
                leave_records = long_df[long_df['holiday_type'] != '通常勤務']
                if not leave_records.empty:
                    print(f"\n   ✅ Found {len(leave_records)} leave/holiday records ({len(leave_records)/len(long_df)*100:.1f}%)")
                    
                    # Show unique leave codes found in data
                    unique_leave_codes = leave_records['code'].unique()
                    print(f"   📝 Leave codes found in data: {list(unique_leave_codes)}")
                else:
                    print(f"\n   ❌ No leave/holiday records found in final data")
            else:
                print(f"   ⚠️ No holiday_type column in final data")
                
        except Exception as e:
            print(f"   ❌ Error testing {file_name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Leave Code Recognition Test")
    print("=" * 50)
    test_leave_code_recognition()
    print("\n✨ Test completed!")