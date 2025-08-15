#!/usr/bin/env python3
"""
_parse_as_date関数のテスト
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_date_parsing_function():
    """_parse_as_date関数のテスト"""
    
    print("=== Date Parsing Function Test ===")
    
    try:
        from shift_suite.tasks.utils import _parse_as_date
        
        # 実際にingest_excelで検出された日付列候補
        test_dates = [
            '2025-02-0100:00:00',
            '2025-02-0200:00:00', 
            '2025-02-0300:00:00',
            '2025-02-0400:00:00',
            '2025-02-0500:00:00'
        ]
        
        print("Testing actual date candidates from ingest_excel:")
        for date_str in test_dates:
            result = _parse_as_date(date_str)
            print(f"  '{date_str}' → {result}")
            
        # より簡単な形式もテスト
        simple_dates = [
            '2025-02-01',
            '2025-02-02',
            '2025/02/01',
            '20250201'
        ]
        
        print("\nTesting simple date formats:")
        for date_str in simple_dates:
            result = _parse_as_date(date_str)
            print(f"  '{date_str}' → {result}")
            
        # datetime型もテスト
        import datetime as dt
        import pandas as pd
        
        datetime_objects = [
            dt.datetime(2025, 2, 1, 0, 0, 0),
            dt.date(2025, 2, 1),
            pd.Timestamp('2025-02-01')
        ]
        
        print("\nTesting datetime objects:")
        for date_obj in datetime_objects:
            result = _parse_as_date(date_obj)
            print(f"  {date_obj} ({type(date_obj)}) → {result}")
            
        # 問題の診断
        print("\n=== Diagnosis ===")
        problem_date = '2025-02-0100:00:00'
        print(f"Problem date: '{problem_date}'")
        
        # 正規表現マッチをテスト
        import re
        m = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", problem_date)
        if m:
            print(f"  Regex match: '{m.group(1)}'")
            try:
                parsed = pd.to_datetime(m.group(1), errors="raise").date()
                print(f"  Pandas parse result: {parsed}")
            except Exception as e:
                print(f"  Pandas parse error: {e}")
        else:
            print("  No regex match!")
            
        # スペース分割テスト
        split_result = problem_date.split(" ")[0]
        print(f"  Split result: '{split_result}'")
        try:
            parsed_split = pd.to_datetime(split_result, errors="raise").date()
            print(f"  Split parse result: {parsed_split}")
        except Exception as e:
            print(f"  Split parse error: {e}")
            
        # 修正案テスト
        print("\n=== Fix Test ===")
        # 直接的なフォーマット修正
        fixed_date = problem_date.replace('00:00:00', '').rstrip()
        print(f"Fixed date: '{fixed_date}'")
        result_fixed = _parse_as_date(fixed_date)
        print(f"Fixed result: {result_fixed}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_date_parsing_function()