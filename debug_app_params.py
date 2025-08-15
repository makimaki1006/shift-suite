#!/usr/bin/env python3
# アプリが実際に使用しているパラメータを確認

import pandas as pd
from pathlib import Path
import sys
import os

# パスを追加
sys.path.insert(0, os.getcwd())

def debug_app_params():
    """アプリが実際に使用しているパラメータを確認"""
    excel_path = Path("デイ_テスト用データ_休日精緻.xlsx")
    
    if not excel_path.exists():
        print(f"ERROR: Test file not found: {excel_path}")
        return
    
    print("=== App Parameters Debug ===")
    
    # UIが1を表示する場合の変換テスト
    ui_value = 1  # ユーザーが入力する値
    actual_header_row = ui_value - 1  # 実際に使用される値
    
    print(f"UI value (1-indexed): {ui_value}")
    print(f"Internal value (0-indexed): {actual_header_row}")
    
    # 実際に使用されるパラメータでテスト
    from shift_suite.tasks.io_excel import ingest_excel
    
    try:
        # シート名を取得
        excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
        sheet_names = excel_file.sheet_names
        shift_sheets = [s for s in sheet_names if "勤務" not in s]
        
        print(f"Testing with shift_sheets: {shift_sheets}")
        print(f"Testing with header_row: {actual_header_row}")
        
        long_df, wt_df, unknown_codes = ingest_excel(
            excel_path,
            shift_sheets=shift_sheets,
            header_row=actual_header_row,
            slot_minutes=30,
            year_month_cell_location="A1"
        )
        
        print(f"✓ SUCCESS: Data loaded successfully")
        print(f"  Shape: {long_df.shape}")
        print(f"  Staff count: {long_df['staff'].nunique()}")
        print(f"  Role count: {long_df['role'].nunique()}")
        
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== End Debug ===")

if __name__ == "__main__":
    debug_app_params()