#!/usr/bin/env python3
"""
勤務コードの詳細分析
"""

import pandas as pd
from pathlib import Path

def detailed_code_analysis():
    """勤務コードの詳細分析"""
    
    print("Detailed Code Analysis")
    print("=" * 30)
    
    test_file = Path("デイ_テスト用データ_休日精緻.xlsx")
    
    try:
        # 1. 勤務区分シートの詳細
        print("1. Worktype Definition Sheet:")
        df_worktype = pd.read_excel(test_file, sheet_name="勤務区分", dtype=str).fillna("")
        
        print(f"   Total rows: {len(df_worktype)}")
        print("   Code definitions:")
        
        for idx, row in df_worktype.iterrows():
            code = str(row.iloc[0]).strip() if row.iloc[0] else ""
            start = str(row.iloc[1]).strip() if len(row) > 1 and row.iloc[1] else ""
            end = str(row.iloc[2]).strip() if len(row) > 2 and row.iloc[2] else ""
            remarks = str(row.iloc[3]).strip() if len(row) > 3 and row.iloc[3] else ""
            
            if code:
                print(f"     '{code}': {start}-{end} ({remarks})")
        
        # 勤務区分コードのセット
        worktype_codes = {str(row.iloc[0]).strip() for _, row in df_worktype.iterrows() 
                         if row.iloc[0] and str(row.iloc[0]).strip()}
        
        # 2. 実績シートの詳細（サンプル）
        print(f"\n2. Actual Data Analysis (R7.2 sample):")
        df_actual = pd.read_excel(test_file, sheet_name="R7.2", header=0, dtype=str).fillna("")
        
        # スタッフ別のサンプルデータ
        print("   Sample staff schedules:")
        for idx in range(min(5, len(df_actual))):
            if idx == 0:  # ヘッダー行をスキップ
                continue
                
            row = df_actual.iloc[idx]
            staff_name = str(row.iloc[0]) if row.iloc[0] else "Unknown"
            role = str(row.iloc[1]) if len(row) > 1 and row.iloc[1] else "Unknown"
            
            print(f"     Staff: {staff_name} ({role})")
            
            # 最初の7日分の勤務コードを表示
            daily_codes = []
            for col_idx in range(3, min(10, len(row))):  # 日付列から7日分
                code = str(row.iloc[col_idx]).strip() if row.iloc[col_idx] else ""
                if code and code not in ['土', '日', '月', '火', '水', '木', '金', 'nan']:
                    daily_codes.append(code)
                else:
                    daily_codes.append("--")
            
            print(f"       Codes: {daily_codes}")
            
            # 各コードが定義されているかチェック
            unique_codes = {code for code in daily_codes if code != "--"}
            for code in unique_codes:
                if code in worktype_codes:
                    print(f"         '{code}' ✓ (defined)")
                else:
                    print(f"         '{code}' ✗ (NOT DEFINED)")
        
        # 3. 全体的な未定義コードの確認
        print(f"\n3. Overall undefined codes:")
        
        all_actual_codes = set()
        date_cols = df_actual.columns[3:]
        
        for col in date_cols:
            for val in df_actual[col].dropna():
                val_str = str(val).strip()
                if val_str and val_str not in ['土', '日', '月', '火', '水', '木', '金', 'nan']:
                    all_actual_codes.add(val_str)
        
        undefined_codes = all_actual_codes - worktype_codes
        defined_codes = all_actual_codes & worktype_codes
        
        print(f"   Total actual codes: {len(all_actual_codes)}")
        print(f"   Defined codes: {len(defined_codes)} - {sorted(list(defined_codes))}")
        print(f"   Undefined codes: {len(undefined_codes)} - {sorted(list(undefined_codes))}")
        
        if undefined_codes:
            print(f"\n   *** PROBLEM: {len(undefined_codes)} codes are used but not defined! ***")
            print(f"   This explains why no valid records are generated.")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    detailed_code_analysis()