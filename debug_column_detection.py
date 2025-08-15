#!/usr/bin/env python3
# デバッグ用: 列名検出の確認

import pandas as pd
from pathlib import Path
import sys
import os

# パスを追加
sys.path.insert(0, os.getcwd())

def debug_excel_columns():
    """Excelファイルの列名を確認"""
    excel_path = Path("デイ_テスト用データ_休日精緻.xlsx")
    
    if not excel_path.exists():
        print(f"ERROR: Test file not found: {excel_path}")
        return
    
    print("=== Excel Column Detection Debug ===")
    
    # シート名を取得
    try:
        excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
        sheet_names = excel_file.sheet_names
        print(f"Available sheets: {sheet_names}")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return
    
    # 勤務区分シートを除外
    shift_sheets = [s for s in sheet_names if "勤務" not in s]
    print(f"Shift sheets: {shift_sheets}")
    
    # 各シートの列名を確認
    for sheet_name in shift_sheets:
        print(f"\n--- Sheet: {sheet_name} ---")
        
        # 異なるheader_rowでの読み込みテスト
        for header_row in [0, 1, 2]:
            try:
                df = pd.read_excel(excel_path, sheet_name=sheet_name, header=header_row, dtype=str)
                print(f"header_row={header_row}: shape={df.shape}")
                print(f"  Columns: {df.columns.tolist()}")
                
                # 列名の正規化をテスト
                from shift_suite.tasks.io_excel import SHEET_COL_ALIAS, _normalize
                normalized_cols = [
                    SHEET_COL_ALIAS.get(_normalize(str(c)), _normalize(str(c))) 
                    for c in df.columns
                ]
                print(f"  Normalized: {normalized_cols}")
                
                # staff/role列の検出
                has_staff = "staff" in normalized_cols
                has_role = "role" in normalized_cols
                print(f"  Has staff: {has_staff}, Has role: {has_role}")
                
                if has_staff and has_role:
                    print(f"  ✓ SUCCESS: Both staff and role columns found with header_row={header_row}")
                    break
                else:
                    print(f"  ✗ FAILED: Missing columns")
                    
            except Exception as e:
                print(f"header_row={header_row}: ERROR - {e}")
    
    print("\n=== End Debug ===")

if __name__ == "__main__":
    debug_excel_columns()