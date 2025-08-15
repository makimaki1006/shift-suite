#!/usr/bin/env python3
# アプリケーション修正テスト

import pandas as pd
from pathlib import Path
import sys
import os

# パスを追加
sys.path.insert(0, os.getcwd())

from shift_suite.tasks.io_excel import ingest_excel

def test_app_fix():
    """アプリケーションの修正をテスト"""
    excel_path = Path("デイ_テスト用データ_休日精緻.xlsx")
    
    if not excel_path.exists():
        print(f"ERROR: Test file not found: {excel_path}")
        return
    
    print("=== App Fix Test ===")
    
    # シート名を取得
    excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
    sheet_names = excel_file.sheet_names
    shift_sheets = [s for s in sheet_names if "勤務" not in s]
    
    print(f"Shift sheets: {shift_sheets}")
    
    # 修正後のパラメータでテスト
    print("\n--- Testing with corrected parameters ---")
    try:
        long_df, wt_df, unknown_codes = ingest_excel(
            excel_path,
            shift_sheets=shift_sheets,
            header_row=0,  # 修正後の値
            slot_minutes=30,
            year_month_cell_location="D1"  # 年月セル位置を指定
        )
        
        print(f"SUCCESS: Long DF shape: {long_df.shape}")
        print(f"  Staff count: {long_df['staff'].nunique()}")
        print(f"  Role count: {long_df['role'].nunique()}")
        print(f"  Date range: {long_df['ds'].dt.date.min()} to {long_df['ds'].dt.date.max()}")
        
        # 一部のデータを確認
        print(f"\nFirst few rows:")
        print(long_df[['staff', 'role', 'ds', 'code']].head())
        
        print(f"\nStaff names: {long_df['staff'].unique()[:5]}")
        print(f"Role names: {long_df['role'].unique()}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== End Test ===")

if __name__ == "__main__":
    test_app_fix()