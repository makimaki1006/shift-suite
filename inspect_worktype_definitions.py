#!/usr/bin/env python3
"""
勤務区分シートの実際の定義内容確認
"""

import pandas as pd
from pathlib import Path

def inspect_worktype_definitions():
    """勤務区分の詳細確認"""
    
    print("=== Worktype Definitions Inspection ===")
    
    test_file = Path("デイ_テスト用データ_休日精緻.xlsx")
    
    try:
        # 勤務区分シート読み込み
        df_worktype = pd.read_excel(test_file, sheet_name="勤務区分", dtype=str).fillna("")
        
        print(f"Worktype sheet shape: {df_worktype.shape}")
        print(f"Columns: {df_worktype.columns.tolist()}")
        
        # 問題のコード（実績では使用されているが0スロット）
        problem_codes = ['有', '休', '欠']  # Unicode文字で直接指定
        
        print(f"\n=== All Worktype Definitions ===")
        for idx, row in df_worktype.iterrows():
            code = str(row.iloc[0]).strip() if row.iloc[0] else ""
            start = str(row.iloc[1]).strip() if len(row) > 1 and row.iloc[1] else ""
            end = str(row.iloc[2]).strip() if len(row) > 2 and row.iloc[2] else ""
            remarks = str(row.iloc[3]).strip() if len(row) > 3 and row.iloc[3] else ""
            
            if code:  # 空でないコードのみ表示
                status = "WORK" if (start and end) else "LEAVE/EMPTY"
                marker = " *** PROBLEM ***" if code in problem_codes else ""
                
                print(f"  {idx:2d}: '{code}' | '{start}' - '{end}' | '{remarks}' | {status}{marker}")
        
        print(f"\n=== Problem Code Analysis ===")
        for problem_code in problem_codes:
            found = False
            for idx, row in df_worktype.iterrows():
                code = str(row.iloc[0]).strip() if row.iloc[0] else ""
                if code == problem_code:
                    start = str(row.iloc[1]).strip() if len(row) > 1 and row.iloc[1] else ""
                    end = str(row.iloc[2]).strip() if len(row) > 2 and row.iloc[2] else ""
                    remarks = str(row.iloc[3]).strip() if len(row) > 3 and row.iloc[3] else ""
                    
                    print(f"\n  Code '{problem_code}':")
                    print(f"    Start: '{start}' (empty: {not start})")
                    print(f"    End: '{end}' (empty: {not end})")
                    print(f"    Remarks: '{remarks}'")
                    
                    if not start or not end:
                        print(f"    Issue: Missing time definition - treated as leave")
                        print(f"    Solution: Need to define work hours for this code")
                    else:
                        print(f"    Unexpected: Has time definition but still treated as leave")
                    
                    found = True
                    break
            
            if not found:
                print(f"\n  Code '{problem_code}': NOT FOUND in worktype definitions!")
        
        # 解決策提案
        print(f"\n=== Resolution Strategy ===")
        print(f"1. Verify if these codes should actually be work shifts")
        print(f"2. If yes, add proper time definitions in worktype sheet")
        print(f"3. If no, remove them from actual shift data")
        print(f"4. Test with corrected definitions")
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_worktype_definitions()