#!/usr/bin/env python3
"""
実際のファイル内容を正確に確認
"""

import pandas as pd
from pathlib import Path

def check_actual_content():
    """実際のファイル内容確認"""
    
    test_file = Path("デイ_テスト用データ_休日精緻.xlsx")
    
    try:
        # 1. 勤務区分シートの実際の内容
        print("=== 勤務区分シート ===")
        df_worktype = pd.read_excel(test_file, sheet_name="勤務区分", dtype=str).fillna("")
        
        print("最初の10行:")
        for i in range(min(10, len(df_worktype))):
            row = df_worktype.iloc[i]
            code = row.iloc[0] if len(row) > 0 else ""
            start = row.iloc[1] if len(row) > 1 else ""
            end = row.iloc[2] if len(row) > 2 else ""
            remarks = row.iloc[3] if len(row) > 3 else ""
            print(f"{i}: [{code}] [{start}] [{end}] [{remarks}]")
        
        # 2. R7.2シートの実際の内容
        print("\n=== R7.2シート ===")
        df_r72 = pd.read_excel(test_file, sheet_name="R7.2", dtype=str).fillna("")
        
        print(f"形状: {df_r72.shape}")
        print("最初の5行x10列:")
        for i in range(min(5, len(df_r72))):
            row_data = []
            for j in range(min(10, len(df_r72.columns))):
                val = df_r72.iloc[i, j] if j < len(df_r72.columns) else ""
                row_data.append(str(val)[:8])  # 最初の8文字まで
            print(f"{i}: {row_data}")
            
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_actual_content()