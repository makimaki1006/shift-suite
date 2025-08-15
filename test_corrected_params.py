#!/usr/bin/env python3
# 修正後のパラメータでテスト

import pandas as pd
from pathlib import Path
import sys
import os

# パスを追加
sys.path.insert(0, os.getcwd())

def test_corrected_params():
    """修正後のパラメータでテスト"""
    excel_path = Path("デイ_テスト用データ_休日精緻.xlsx")
    
    if not excel_path.exists():
        print(f"ERROR: Test file not found: {excel_path}")
        return
    
    print("=== Corrected Parameters Test ===")
    
    # 修正後のパラメータ
    ui_header_row = 1
    actual_header_row = ui_header_row - 1  # 0
    year_month_cell = "D1"
    
    print(f"UI header row: {ui_header_row}")
    print(f"Internal header row: {actual_header_row}")
    print(f"Year/month cell: {year_month_cell}")
    
    # 実際に使用されるパラメータでテスト
    from shift_suite.tasks.io_excel import ingest_excel
    
    try:
        # シート名を取得
        excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
        sheet_names = excel_file.sheet_names
        shift_sheets = [s for s in sheet_names if "勤務" not in s]
        
        print(f"Testing with shift_sheets: {shift_sheets}")
        
        long_df, wt_df, unknown_codes = ingest_excel(
            excel_path,
            shift_sheets=shift_sheets,
            header_row=actual_header_row,
            slot_minutes=30,
            year_month_cell_location=year_month_cell
        )
        
        print(f"✓ SUCCESS: Data loaded successfully")
        print(f"  Long DF shape: {long_df.shape}")
        print(f"  Staff count: {long_df['staff'].nunique()}")
        print(f"  Role count: {long_df['role'].nunique()}")
        print(f"  Date range: {long_df['ds'].dt.date.min()} to {long_df['ds'].dt.date.max()}")
        print(f"  Unknown codes: {unknown_codes}")
        
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== End Test ===")

if __name__ == "__main__":
    test_corrected_params()