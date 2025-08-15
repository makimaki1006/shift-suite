#!/usr/bin/env python3
"""
'休'コードの詳細なマッピング問題調査
"""

import sys
import pandas as pd
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_rest_code_mapping():
    """'休'コードマッピングの詳細調査"""
    
    print("=== Rest Code Mapping Debug ===")
    
    test_file = project_root / "デイ_テスト用データ_休日精緻.xlsx"
    
    try:
        # 1. 勤務区分の'休'コード候補を全て確認
        print("1. All codes in worktype sheet:")
        df_worktype = pd.read_excel(test_file, sheet_name="勤務区分", dtype=str).fillna("")
        
        for idx, row in df_worktype.iterrows():
            code = str(row.iloc[0]).strip() if row.iloc[0] else ""
            if code:
                # バイト表現も表示
                code_bytes = code.encode('utf-8', errors='replace')
                print(f"  {idx:2d}: '{code}' (bytes: {code_bytes}) (len: {len(code)})")
                
                # '休'に類似するコードを特定
                if '休' in code or code == '休':
                    start = str(row.iloc[1]).strip() if len(row) > 1 and row.iloc[1] else ""
                    end = str(row.iloc[2]).strip() if len(row) > 2 and row.iloc[2] else ""
                    remarks = str(row.iloc[3]).strip() if len(row) > 3 and row.iloc[3] else ""
                    print(f"    *** REST CODE CANDIDATE: start='{start}', end='{end}', remarks='{remarks}'")
        
        # 2. 実績シートの'休'コード使用状況
        print("\n2. Rest codes used in actual sheets:")
        all_rest_codes = set()
        
        for sheet_name in ["R7.2", "R7.6"]:
            df = pd.read_excel(test_file, sheet_name=sheet_name, header=0, dtype=str).fillna("")
            date_cols = df.columns[3:]
            
            for col in date_cols:
                for val in df[col].dropna():
                    val_str = str(val).strip()
                    if '休' in val_str:
                        all_rest_codes.add(val_str)
                        val_bytes = val_str.encode('utf-8', errors='replace')
                        print(f"  Found in {sheet_name}: '{val_str}' (bytes: {val_bytes}) (len: {len(val_str)})")
        
        print(f"\nUnique rest codes in data: {sorted(all_rest_codes)}")
        
        # 3. load_shift_patterns関数でのコードマッピング確認
        print("\n3. Testing load_shift_patterns function:")
        from shift_suite.tasks.io_excel import load_shift_patterns
        wt_df, code2slots = load_shift_patterns(test_file, slot_minutes=30)
        
        print(f"Code2slots contains {len(code2slots)} codes:")
        rest_related_codes = {}
        for code, slots in code2slots.items():
            if '休' in code:
                rest_related_codes[code] = len(slots)
                code_bytes = code.encode('utf-8', errors='replace')
                print(f"  '{code}' (bytes: {code_bytes}): {len(slots)} slots")
        
        # 4. 実際のコードが定義済みかチェック
        print("\n4. Matching check:")
        for actual_code in all_rest_codes:
            if actual_code in code2slots:
                slots = len(code2slots[actual_code])
                print(f"  '{actual_code}': FOUND in definitions ({slots} slots)")
            else:
                print(f"  '{actual_code}': NOT FOUND in definitions")
                
                # 類似コード検索
                similar = []
                for defined_code in code2slots.keys():
                    if '休' in defined_code:
                        similar.append(defined_code)
                
                if similar:
                    print(f"    Similar codes available: {similar}")
                    
                    # バイト比較
                    for sim_code in similar:
                        if actual_code.encode('utf-8') == sim_code.encode('utf-8'):
                            print(f"    *** BYTE MATCH with '{sim_code}' ***")
                        else:
                            print(f"    Byte difference with '{sim_code}': actual={actual_code.encode('utf-8')} vs defined={sim_code.encode('utf-8')}")
        
        print(f"\n5. Root cause analysis:")
        if len(all_rest_codes) == 0:
            print("  No rest codes found in actual data")
        elif len(rest_related_codes) == 0:
            print("  No rest codes defined in worktype")
        else:
            print("  Both exist - likely encoding or normalization issue")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_rest_code_mapping()