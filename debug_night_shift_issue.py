#!/usr/bin/env python3
# 夜勤処理失敗の原因を特定するためのデバッグ

import pandas as pd
from pathlib import Path
import sys
import os

# パスを追加
sys.path.insert(0, os.getcwd())

from shift_suite.tasks.io_excel import ingest_excel

def debug_night_shift_processing():
    """夜勤処理の問題を特定"""
    excel_path = Path("ショート_テスト用データ.xlsx")
    
    if not excel_path.exists():
        print(f"ERROR: Test file not found: {excel_path}")
        return
    
    print("=== 夜勤処理デバッグ ===")
    
    # シート名を取得
    excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
    sheet_names = excel_file.sheet_names
    shift_sheets = [s for s in sheet_names if "勤務" not in s]
    
    print(f"Shift sheets: {shift_sheets}")
    
    # 現在の設定でテスト
    print("\n--- 現在の設定でテスト ---")
    try:
        long_df, wt_df, unknown_codes = ingest_excel(
            excel_path,
            shift_sheets=shift_sheets,
            header_row=0,  # 現在の設定
            slot_minutes=30,
            year_month_cell_location="D1"
        )
        
        print(f"SUCCESS: Long DF shape: {long_df.shape}")
        print(f"  WTファイル shape: {wt_df.shape}")
        print(f"  Unknown codes: {unknown_codes}")
        
        # 夜勤コードの確認
        print(f"\n--- 夜勤コード確認 ---")
        print(f"WTファイルの勤務コード: {wt_df['code'].unique()}")
        
        # 各勤務コードの時間帯確認
        for code in wt_df['code'].unique():
            wt_code = wt_df[wt_df['code'] == code]
            if not wt_code.empty:
                start_parsed = wt_code['start_parsed'].iloc[0] if 'start_parsed' in wt_code.columns else 'N/A'
                end_parsed = wt_code['end_parsed'].iloc[0] if 'end_parsed' in wt_code.columns else 'N/A'
                print(f"コード '{code}': {start_parsed} - {end_parsed}")
        
        # 夜勤時間帯のデータ確認
        print(f"\n--- 夜勤時間帯データ確認 ---")
        night_slots = []
        for hour in range(0, 6):  # 0:00-6:00
            for minute in [0, 30]:
                time_str = f"{hour:02d}:{minute:02d}"
                night_slots.append(time_str)
        
        print(f"夜勤時間帯: {night_slots}")
        
        # 実際のデータで夜勤時間帯の確認
        long_df['time_str'] = long_df['ds'].dt.strftime('%H:%M')
        night_data = long_df[long_df['time_str'].isin(night_slots)]
        
        print(f"夜勤時間帯のデータ数: {len(night_data)}")
        if len(night_data) > 0:
            print(f"夜勤時間帯のコード: {night_data['code'].unique()}")
            print(f"夜勤時間帯の最初の5件:")
            print(night_data[['staff', 'role', 'ds', 'code', 'time_str']].head())
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== End Debug ===")

if __name__ == "__main__":
    debug_night_shift_processing()