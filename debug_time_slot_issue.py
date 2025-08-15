#!/usr/bin/env python3
"""
時間スロット変換問題（15分→30分）のデバッグ
"""

import pandas as pd
from pathlib import Path
import sys
import os

# パスを追加
sys.path.insert(0, os.getcwd())

from shift_suite.tasks.io_excel import ingest_excel, SLOT_MINUTES

def debug_slot_minutes_issue():
    """時間スロット変換の問題を特定"""
    excel_path = Path("ショート_テスト用データ.xlsx")
    
    if not excel_path.exists():
        print(f"ERROR: Test file not found: {excel_path}")
        return
    
    print("=== 時間スロット変換デバッグ ===")
    
    # シート名を取得
    excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
    sheet_names = excel_file.sheet_names
    shift_sheets = [s for s in sheet_names if "勤務" not in s]
    
    print(f"Shift sheets: {shift_sheets}")
    print(f"SLOT_MINUTES設定: {SLOT_MINUTES}分")
    
    # 15分スロットでテスト
    print(f"\n--- 15分スロットでテスト ---")
    try:
        long_df_15, wt_df_15, unknown_codes_15 = ingest_excel(
            excel_path,
            shift_sheets=shift_sheets,
            header_row=0,
            slot_minutes=15,  # 15分スロット
            year_month_cell_location="D1"
        )
        
        print(f"15分スロット: Long DF shape: {long_df_15.shape}")
        print(f"  夜勤時間帯（00:00-06:00）のデータ:")
        
        # 夜勤時間帯の確認（15分スロット）
        night_times = []
        for hour in range(0, 6):
            for minute in [0, 15, 30, 45]:
                night_times.append(f"{hour:02d}:{minute:02d}")
        
        long_df_15['time_str'] = long_df_15['ds'].dt.strftime('%H:%M')
        night_data_15 = long_df_15[long_df_15['time_str'].isin(night_times)]
        night_non_holiday_15 = night_data_15[night_data_15['holiday_type'] == '通常勤務']
        
        print(f"    15分スロット総データ数: {len(night_data_15)}")
        print(f"    15分スロット通常勤務数: {len(night_non_holiday_15)}")
        print(f"    15分スロットコード分布: {night_data_15['code'].value_counts().to_dict()}")
        
    except Exception as e:
        print(f"15分スロットエラー: {e}")
    
    # 30分スロットでテスト
    print(f"\n--- 30分スロットでテスト ---")
    try:
        long_df_30, wt_df_30, unknown_codes_30 = ingest_excel(
            excel_path,
            shift_sheets=shift_sheets,
            header_row=0,
            slot_minutes=30,  # 30分スロット
            year_month_cell_location="D1"
        )
        
        print(f"30分スロット: Long DF shape: {long_df_30.shape}")
        print(f"  夜勤時間帯（00:00-06:00）のデータ:")
        
        # 夜勤時間帯の確認（30分スロット）
        night_times = []
        for hour in range(0, 6):
            for minute in [0, 30]:
                night_times.append(f"{hour:02d}:{minute:02d}")
        
        long_df_30['time_str'] = long_df_30['ds'].dt.strftime('%H:%M')
        night_data_30 = long_df_30[long_df_30['time_str'].isin(night_times)]
        night_non_holiday_30 = night_data_30[night_data_30['holiday_type'] == '通常勤務']
        
        print(f"    30分スロット総データ数: {len(night_data_30)}")
        print(f"    30分スロット通常勤務数: {len(night_non_holiday_30)}")
        print(f"    30分スロットコード分布: {night_data_30['code'].value_counts().to_dict()}")
        
        print(f"\n--- データ量比較 ---")
        print(f"総レコード数: 15分={len(long_df_15)}, 30分={len(long_df_30)}")
        print(f"差異: {len(long_df_15) - len(long_df_30)} レコード")
        print(f"比率: {len(long_df_30) / len(long_df_15):.3f}")
        
        # 期待値との比較
        expected_15_to_30_ratio = 0.5  # 15分→30分なので約半分になるはず
        actual_ratio = len(long_df_30) / len(long_df_15)
        print(f"期待比率: {expected_15_to_30_ratio:.3f}")
        print(f"実際比率: {actual_ratio:.3f}")
        
        if abs(actual_ratio - expected_15_to_30_ratio) > 0.1:
            print("⚠️ 警告: スロット変換に問題がある可能性があります")
        
    except Exception as e:
        print(f"30分スロットエラー: {e}")
    
    print("\n=== End Debug ===")

if __name__ == "__main__":
    debug_slot_minutes_issue()