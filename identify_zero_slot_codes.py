#!/usr/bin/env python3
"""
0スロット（休暇扱い）になっているコードの特定
"""

import sys
import pandas as pd
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def identify_zero_slot_codes():
    """0スロットコードの特定"""
    
    print("=== Zero Slot Code Investigation ===")
    
    test_file = project_root / "デイ_テスト用データ_休日精緻.xlsx"
    
    try:
        # 1. load_shift_patternsで生成されるcode2slotsを確認
        print("1. Loading shift patterns...")
        from shift_suite.tasks.io_excel import load_shift_patterns
        wt_df, code2slots = load_shift_patterns(test_file, slot_minutes=30)
        
        # 2. 実際に使用されているコードを取得
        print("\n2. Getting actual codes from data sheets...")
        all_actual_codes = set()
        for sheet_name in ["R7.2", "R7.6"]:
            df = pd.read_excel(test_file, sheet_name=sheet_name, header=0, dtype=str).fillna("")
            date_cols = df.columns[3:]
            for col in date_cols:
                for val in df[col].dropna():
                    val_str = str(val).strip()
                    if val_str and val_str not in ['土', '日', '月', '火', '水', '木', '金', 'nan']:
                        all_actual_codes.add(val_str)
        
        print(f"   Found {len(all_actual_codes)} actual codes")
        
        # 3. 各コードのスロット数を確認
        print("\n3. Slot analysis for actual codes:")
        work_codes = []
        leave_codes = []
        
        for code in sorted(all_actual_codes):
            if code in code2slots:
                slots = code2slots[code]
                slot_count = len(slots)
                if slot_count > 0:
                    work_codes.append((code, slot_count))
                    print(f"   '{code}': {slot_count} slots (WORK)")
                else:
                    leave_codes.append(code)
                    print(f"   '{code}': 0 slots (LEAVE)")
            else:
                print(f"   '{code}': NOT FOUND in code2slots")
        
        print(f"\n4. Summary:")
        print(f"   Work codes: {len(work_codes)}")
        print(f"   Leave codes: {len(leave_codes)}")
        
        if leave_codes:
            print(f"\n   PROBLEM CODES (0 slots):")
            for code in leave_codes:
                print(f"     '{code}'")
        
        # 5. 勤務区分シートの該当コードを確認
        print(f"\n5. Checking worktype definitions for problem codes...")
        df_worktype = pd.read_excel(test_file, sheet_name="勤務区分", dtype=str).fillna("")
        
        for code in leave_codes:
            # このコードの定義を探す
            for idx, row in df_worktype.iterrows():
                if str(row.iloc[0]).strip() == code:
                    start_time = str(row.iloc[1]).strip() if len(row) > 1 else ""
                    end_time = str(row.iloc[2]).strip() if len(row) > 2 else ""
                    remarks = str(row.iloc[3]).strip() if len(row) > 3 else ""
                    
                    print(f"   '{code}': start='{start_time}', end='{end_time}', remarks='{remarks}'")
                    
                    # 修正前のロジックを推測
                    if not start_time or not end_time:
                        print(f"     -> Missing start/end time = leave code")
                    elif remarks and any(leave_word in remarks for leave_word in ['休', '欠席', '有給']):
                        print(f"     -> Remarks contains leave indicator = leave code")
                    else:
                        print(f"     -> Should be work code but marked as leave!")
                    break
            else:
                print(f"   '{code}': Definition not found!")
                
        # 6. 解決策の提案
        if leave_codes:
            print(f"\n6. Resolution needed:")
            print(f"   These codes should be work codes but are treated as leave:")
            for code in leave_codes:
                print(f"     '{code}' - needs slot assignment fix")
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    identify_zero_slot_codes()