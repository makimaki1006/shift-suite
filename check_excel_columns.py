#!/usr/bin/env python3
"""
ExcelファイルのR7.6シートの列構造を確認
"""

import pandas as pd

try:
    excel_path = 'テストデータ_勤務表　勤務時間_トライアル.xlsx'
    
    # ヘッダー行=2（Pythonの0ベースで1）で読み込み
    df = pd.read_excel(excel_path, sheet_name='R7.6', header=1, dtype=str)
    
    print("Excel列名（header=1）:")
    for i, col in enumerate(df.columns):
        print(f"{i}: '{col}'")
    
    print(f"\nDataFrame shape: {df.shape}")
    print(f"\n最初の5行:")
    print(df.head())
    
    # ヘッダー無しでも試す
    print("\n" + "="*50)
    print("ヘッダー無しで読み込み（最初の3行）:")
    df_no_header = pd.read_excel(excel_path, sheet_name='R7.6', header=None, dtype=str)
    print(df_no_header.head(3))
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()