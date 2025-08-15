#!/usr/bin/env python3
"""
Excelファイルのシート名を確認
"""

import pandas as pd
from pathlib import Path

def check_excel_sheets():
    """Excelファイルのシート名とセル内容を確認"""
    
    test_file = Path("デイ_テスト用データ_休日精緻.xlsx")
    
    if not test_file.exists():
        print(f"File not found: {test_file}")
        return
    
    try:
        # シート名一覧取得
        excel_file = pd.ExcelFile(test_file)
        sheet_names = excel_file.sheet_names
        
        print(f"Excel file: {test_file}")
        print(f"Sheet names: {sheet_names}")
        
        # 各シートの先頭部分を確認
        for sheet in sheet_names:
            print(f"\n--- Sheet: {sheet} ---")
            df = pd.read_excel(test_file, sheet_name=sheet, header=None, nrows=5)
            print(df.to_string())
            
        # 年月セルの確認
        if sheet_names:
            first_sheet = sheet_names[0]
            print(f"\n--- Checking year-month cell in {first_sheet} ---")
            df_cell = pd.read_excel(test_file, sheet_name=first_sheet, header=None, nrows=3, usecols="A:C")
            print(df_cell.to_string())
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_excel_sheets()