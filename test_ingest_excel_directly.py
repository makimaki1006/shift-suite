#!/usr/bin/env python3
"""
ingest_excel関数を直接実行してレコード生成を確認
"""

import sys
import pandas as pd
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_ingest_excel_directly():
    """ingest_excel関数の直接実行テスト"""
    
    print("=== Direct ingest_excel Test ===")
    
    test_file = project_root / "デイ_テスト用データ_休日精緻.xlsx"
    
    try:
        # ingest_excel関数を直接実行
        print("1. Executing ingest_excel...")
        from shift_suite.tasks.io_excel import ingest_excel
        
        long_df, wt_df, unknown_codes = ingest_excel(
            excel_path=test_file,
            shift_sheets=["R7.2"],  # 1シートのみテスト
            header_row=0,
            slot_minutes=30
        )
        
        print(f"Results:")
        print(f"  long_df shape: {long_df.shape}")
        print(f"  wt_df shape: {wt_df.shape}")
        print(f"  unknown_codes: {unknown_codes}")
        
        if long_df.empty:
            print("  ❌ No records generated!")
            return
        
        print(f"\n2. Generated records analysis:")
        print(f"  Total records: {len(long_df)}")
        print(f"  Unique codes: {long_df['code'].unique()}")
        print(f"  Code counts:")
        for code, count in long_df['code'].value_counts().items():
            print(f"    '{code}': {count} records")
        
        # 休暇コードの詳細確認
        print(f"\n3. Leave code analysis:")
        leave_codes = ['休', '有', '欠']
        for leave_code in leave_codes:
            leave_records = long_df[long_df['code'] == leave_code]
            print(f"  '{leave_code}': {len(leave_records)} records")
            
            if len(leave_records) > 0:
                print(f"    Sample records:")
                for idx, record in leave_records.head(3).iterrows():
                    print(f"      {record['ds']} | {record['staff']} | slots: {record.get('parsed_slots_count', 'N/A')}")
        
        # 空コードの確認
        empty_code_records = long_df[long_df['code'] == '']
        print(f"\n4. Empty code records: {len(empty_code_records)}")
        
        # スロット数の分布
        print(f"\n5. Slot count distribution:")
        if 'parsed_slots_count' in long_df.columns:
            slot_counts = long_df['parsed_slots_count'].value_counts().sort_index()
            for slots, count in slot_counts.items():
                print(f"  {slots} slots: {count} records")
        
        # 正常なレコードの確認
        work_records = long_df[long_df['parsed_slots_count'] > 0] if 'parsed_slots_count' in long_df.columns else pd.DataFrame()
        leave_records = long_df[long_df['parsed_slots_count'] == 0] if 'parsed_slots_count' in long_df.columns else pd.DataFrame()
        
        print(f"\n6. Record type breakdown:")
        print(f"  Work records (slots > 0): {len(work_records)}")
        print(f"  Leave records (slots = 0): {len(leave_records)}")
        
        if len(work_records) > 0:
            print("  ✅ Work records are being generated")
        else:
            print("  ❌ No work records generated")
            
        if len(leave_records) > 0:
            print("  ✅ Leave records are being generated")
        else:
            print("  ❌ No leave records generated")
            
        return long_df, wt_df, unknown_codes
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

if __name__ == "__main__":
    test_ingest_excel_directly()