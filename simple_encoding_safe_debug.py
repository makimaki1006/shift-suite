#!/usr/bin/env python3
"""
エンコーディング安全な勤務コード分析
"""

import sys
import pandas as pd
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def safe_encoding_debug():
    """エンコーディング安全な分析"""
    
    print("=== Safe Encoding Debug ===")
    
    test_file = project_root / "デイ_テスト用データ_休日精緻.xlsx"
    
    try:
        # 1. 勤務区分コード
        print("1. Reading worktype codes...")
        df_worktype = pd.read_excel(test_file, sheet_name="勤務区分", dtype=str).fillna("")
        worktype_codes = set()
        
        for idx, row in df_worktype.iterrows():
            code = str(row.iloc[0]).strip() if row.iloc[0] else ""
            if code:
                worktype_codes.add(code)
        
        print(f"   Found {len(worktype_codes)} worktype codes")
        
        # 2. 実績コード
        print("\n2. Reading actual shift codes...")
        for sheet_name in ["R7.2", "R7.6"]:
            print(f"\n   Sheet: {sheet_name}")
            
            df_actual = pd.read_excel(test_file, sheet_name=sheet_name, header=0, dtype=str).fillna("")
            
            # 日付列（3列目以降）のコードを収集
            date_cols = df_actual.columns[3:]
            sheet_codes = set()
            
            for col in date_cols:
                for val in df_actual[col].dropna():
                    val_str = str(val).strip()
                    if val_str and val_str not in ['土', '日', '月', '火', '水', '木', '金', 'nan']:
                        sheet_codes.add(val_str)
            
            print(f"   Found {len(sheet_codes)} actual codes")
            
            # マッチング確認
            matched = sheet_codes & worktype_codes
            unmatched = sheet_codes - worktype_codes
            
            print(f"   Matched: {len(matched)}")
            print(f"   Unmatched: {len(unmatched)}")
            
            if unmatched:
                print(f"   Missing codes:")
                for i, code in enumerate(sorted(unmatched)):
                    if i < 5:  # 最初の5個だけ表示
                        print(f"     '{code}' (len: {len(code)})")
                    
        # 3. 根本原因分析
        print("\n3. Root cause analysis:")
        
        # すべての実績コードを統合
        all_actual_codes = set()
        for sheet_name in ["R7.2", "R7.6"]:
            df = pd.read_excel(test_file, sheet_name=sheet_name, header=0, dtype=str).fillna("")
            date_cols = df.columns[3:]
            for col in date_cols:
                for val in df[col].dropna():
                    val_str = str(val).strip()
                    if val_str and val_str not in ['土', '日', '月', '火', '水', '木', '金', 'nan']:
                        all_actual_codes.add(val_str)
        
        matched_total = all_actual_codes & worktype_codes
        unmatched_total = all_actual_codes - worktype_codes
        
        print(f"   Total worktype codes: {len(worktype_codes)}")
        print(f"   Total actual codes: {len(all_actual_codes)}")
        print(f"   Matched codes: {len(matched_total)}")
        print(f"   Unmatched codes: {len(unmatched_total)}")
        
        if len(matched_total) > 0:
            print("\n   SUCCESS: Codes are matching!")
            print("   This means the problem is NOT with code mapping.")
            print("   The issue must be elsewhere in the ingest process.")
        else:
            print("\n   PROBLEM: No codes match between worktype and actual data!")
            
        # 4. 詳細調査 - 実際のプロセスを再現
        print("\n4. Testing actual ingest process...")
        try:
            from shift_suite.tasks.io_excel import load_shift_patterns
            wt_df, code2slots = load_shift_patterns(test_file, slot_minutes=30)
            
            # 有効なスロットを持つコード
            valid_codes = {code for code, slots in code2slots.items() if len(slots) > 0}
            
            print(f"   Valid work codes (with slots): {len(valid_codes)}")
            
            # 実際のコードとスロット定義の照合
            actual_with_slots = all_actual_codes & valid_codes
            actual_without_slots = all_actual_codes - valid_codes
            
            print(f"   Actual codes WITH slots: {len(actual_with_slots)}")
            print(f"   Actual codes WITHOUT slots: {len(actual_without_slots)}")
            
            if len(actual_with_slots) == 0:
                print("   *** ROOT CAUSE: No actual codes have slot definitions! ***")
                print("   This explains why no valid records are generated.")
            
        except Exception as e:
            print(f"   Error testing ingest process: {e}")
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    safe_encoding_debug()