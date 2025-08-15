#!/usr/bin/env python3
# Excel構造の詳細デバッグ

import pandas as pd
from pathlib import Path
import sys
import os

# パスを追加
sys.path.insert(0, os.getcwd())

from shift_suite.tasks.io_excel import SHEET_COL_ALIAS, _normalize

def debug_excel_structure():
    """Excelファイルの構造を詳しく調査"""
    excel_path = Path("デイ_テスト用データ_休日精緻.xlsx")
    
    if not excel_path.exists():
        print(f"ERROR: Test file not found: {excel_path}")
        return
    
    print("=== Excel Structure Debug ===")
    
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
    
    # 各シートの詳細構造を確認
    for sheet_name in shift_sheets:
        print(f"\n=== Sheet: {sheet_name} ===")
        
        # 生データを最初の数行読み込み
        try:
            df_raw = pd.read_excel(excel_path, sheet_name=sheet_name, header=None, dtype=str)
            print(f"Raw data shape: {df_raw.shape}")
            
            # 最初の5行を表示
            print("First 5 rows:")
            for i in range(min(5, len(df_raw))):
                print(f"Row {i}: {df_raw.iloc[i].tolist()}")
            
            # 各行をヘッダーとして試す
            for header_row in range(min(5, len(df_raw))):
                try:
                    df = pd.read_excel(excel_path, sheet_name=sheet_name, header=header_row, dtype=str)
                    print(f"\nheader_row={header_row}: shape={df.shape}")
                    print(f"  Raw columns: {df.columns.tolist()}")
                    
                    # 列名の正規化をテスト
                    normalized_cols = []
                    for c in df.columns:
                        norm_c = _normalize(str(c))
                        alias_c = SHEET_COL_ALIAS.get(norm_c, norm_c)
                        normalized_cols.append(alias_c)
                        print(f"    '{c}' -> '{norm_c}' -> '{alias_c}'")
                    
                    print(f"  Normalized columns: {normalized_cols}")
                    
                    # staff/role列の検出
                    has_staff = "staff" in normalized_cols
                    has_role = "role" in normalized_cols
                    print(f"  Has staff: {has_staff}, Has role: {has_role}")
                    
                    if has_staff and has_role:
                        print(f"  ✓ SUCCESS: Both staff and role columns found with header_row={header_row}")
                        
                        # 実際のデータの例を表示
                        staff_col = df.columns[normalized_cols.index("staff")]
                        role_col = df.columns[normalized_cols.index("role")]
                        print(f"  Staff column '{staff_col}' values: {df[staff_col].dropna().unique()[:5]}")
                        print(f"  Role column '{role_col}' values: {df[role_col].dropna().unique()[:5]}")
                        break
                    else:
                        print(f"  ✗ FAILED: Missing columns")
                        
                except Exception as e:
                    print(f"header_row={header_row}: ERROR - {e}")
        
        except Exception as e:
            print(f"Error reading sheet {sheet_name}: {e}")
    
    print("\n=== End Debug ===")

if __name__ == "__main__":
    debug_excel_structure()