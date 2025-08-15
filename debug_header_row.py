#!/usr/bin/env python3
# Header row debug

import pandas as pd
from pathlib import Path
import sys
import os

# パスを追加
sys.path.insert(0, os.getcwd())

from shift_suite.tasks.io_excel import ingest_excel

def debug_header_row():
    """Header row の動作確認"""
    excel_path = Path("デイ_テスト用データ_休日精緻.xlsx")
    
    if not excel_path.exists():
        print(f"ERROR: Test file not found: {excel_path}")
        return
    
    print("=== Header Row Debug ===")
    
    # シート名を取得
    excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
    sheet_names = excel_file.sheet_names
    shift_sheets = [s for s in sheet_names if "勤務" not in s]
    
    print(f"Shift sheets: {shift_sheets}")
    
    # 各header_rowでのテスト
    for header_row in [0, 1, 2]:
        print(f"\n--- Testing header_row={header_row} ---")
        try:
            long_df, wt_df, unknown_codes = ingest_excel(
                excel_path,
                shift_sheets=shift_sheets,
                header_row=header_row,
                slot_minutes=30,
                year_month_cell_location="D1"
            )
            
            print(f"SUCCESS: Long DF shape: {long_df.shape}")
            print(f"  Staff count: {long_df['staff'].nunique()}")
            print(f"  Role count: {long_df['role'].nunique()}")
            print(f"  Date range: {long_df['ds'].dt.date.min()} to {long_df['ds'].dt.date.max()}")
            
        except Exception as e:
            print(f"ERROR: {e}")
    
    print("\n=== End Debug ===")

if __name__ == "__main__":
    debug_header_row()