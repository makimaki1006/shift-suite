#!/usr/bin/env python3
"""
簡単なコードマッピング確認（Unicode対応）
"""

import pandas as pd
from pathlib import Path

def simple_code_mapping():
    """簡単なコードマッピング確認"""
    
    print("Simple Code Mapping Check")
    print("=" * 30)
    
    test_file = Path("デイ_テスト用データ_休日精緻.xlsx")
    
    try:
        # 1. 勤務区分コード
        df_worktype = pd.read_excel(test_file, sheet_name="勤務区分", dtype=str).fillna("")
        worktype_codes = [code.strip() for code in df_worktype.iloc[:, 0].tolist() if code and code.strip()]
        
        print(f"Worktype codes: {len(worktype_codes)} found")
        print("Sample:", worktype_codes[:10])
        
        # 2. 実績コード（R7.2シートから）
        df_actual = pd.read_excel(test_file, sheet_name="R7.2", header=0, dtype=str).fillna("")
        
        # 最初の数行のデータを確認
        print(f"\nR7.2 sheet shape: {df_actual.shape}")
        print("First few rows of R7.2:")
        print(df_actual.head(3).to_string())
        
        # 日付列の勤務コードを確認
        date_cols = df_actual.columns[3:]  # 最初の3列をスキップ
        actual_codes = set()
        
        for col in date_cols[:5]:  # 最初の5日分だけ確認
            for val in df_actual[col].dropna():
                val_str = str(val).strip()
                if val_str and val_str not in ['土', '日', '月', '火', '水', '木', '金', 'nan']:
                    actual_codes.add(val_str)
        
        print(f"\nActual codes found: {len(actual_codes)}")
        print("Codes:", sorted(list(actual_codes)))
        
        # マッチング確認
        worktype_set = set(worktype_codes)
        matched = actual_codes & worktype_set
        unmatched = actual_codes - worktype_set
        
        print(f"\nMatching results:")
        print(f"  Matched: {len(matched)} - {sorted(list(matched))}")
        print(f"  Unmatched: {len(unmatched)} - {sorted(list(unmatched))}")
        
        if len(matched) == 0:
            print("  *** NO MATCHES - This is why no valid records are generated! ***")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_code_mapping()