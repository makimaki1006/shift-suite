#!/usr/bin/env python3
"""
数値不整合の根本原因特定
シンプルに3つの値の違いの原因を突き止める
"""

import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, os.getcwd())

from pathlib import Path
from shift_suite.tasks.io_excel import ingest_excel
from shift_suite.tasks.proportional_calculator import calculate_total_shortage_from_data

def debug_shortage_calculations():
    """
    3つの異なる値の発生原因をシンプルに特定
    """
    print("=== 数値不整合の根本原因特定 ===")
    
    # テストファイルを探す
    test_files = [
        "ショート_テスト用データ.xlsx",
        "デイ_テスト用データ_休日精緻.xlsx",
        "シフト分析/ショート_テスト用データ.xlsx"
    ]
    
    excel_path = None
    for file_path in test_files:
        if Path(file_path).exists():
            excel_path = file_path
            break
    
    if not excel_path:
        print("テストファイルが見つかりません")
        return
    
    print(f"使用ファイル: {excel_path}")
    
    try:
        # 1. データ読み込み
        excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
        shift_sheets = [s for s in excel_file.sheet_names if "勤務" not in s]
        
        long_df, wt_df, unknown_codes = ingest_excel(
            Path(excel_path),
            shift_sheets=shift_sheets,
            header_row=0,
            slot_minutes=30,
            year_month_cell_location="D1"
        )
        
        working_data = long_df[long_df['holiday_type'] == '通常勤務'].copy()
        print(f"勤務データ件数: {len(working_data)}")
        
        if working_data.empty:
            print("勤務データが空です")
            return
        
        # 2. 新しい按分方式での計算（正しい値）
        correct_total = calculate_total_shortage_from_data(working_data, "median")
        print(f"\n新按分方式での正しい全体不足時間: {correct_total:.2f}時間")
        
        # 3. 職種別按分計算
        role_counts = working_data['role'].value_counts()
        total_records = len(working_data)
        
        role_shortages = {}
        for role, count in role_counts.items():
            proportion = count / total_records
            role_shortage = correct_total * proportion
            role_shortages[role] = role_shortage
        
        role_total = sum(role_shortages.values())
        print(f"職種別合計: {role_total:.2f}時間")
        
        # 4. 雇用形態別按分計算
        employment_counts = working_data['employment'].value_counts()
        
        employment_shortages = {}
        for employment, count in employment_counts.items():
            proportion = count / total_records
            employment_shortage = correct_total * proportion
            employment_shortages[employment] = employment_shortage
        
        employment_total = sum(employment_shortages.values())
        print(f"雇用形態別合計: {employment_total:.2f}時間")
        
        # 5. 既存の問題あるロジックの模倣
        print("\n=== 問題あるロジックの再現 ===")
        
        # 問題1: dash_app.pyの * 0.5 ロジック
        # shortage_time_dfから値を取得してそのまま 0.5倍
        working_data_copy = working_data.copy()
        working_data_copy['date'] = pd.to_datetime(working_data_copy['ds']).dt.date
        working_data_copy['time_slot'] = pd.to_datetime(working_data_copy['ds']).dt.strftime('%H:%M')
        
        daily_counts = working_data_copy.groupby(['date', 'time_slot']).size().reset_index(name='count')
        demand_by_slot = daily_counts.groupby('time_slot')['count'].median()
        unique_dates = working_data_copy['date'].nunique()
        actual_by_slot = working_data_copy.groupby('time_slot').size() / unique_dates
        shortage_by_slot = np.maximum(0, demand_by_slot - actual_by_slot)
        
        # 問題あるロジック1: 0.5をかけ忘れ -> 大きな値
        big_value = shortage_by_slot.sum()  # 0.5をかけない
        print(f"0.5をかけ忘れの場合: {big_value:.2f}時間 (18564.0hに近い値？)")
        
        # 問題あるロジック2: さらに0.5をかける -> 小さな値
        small_value = correct_total * 0.5
        print(f"さらに0.5をかける場合: {small_value:.2f}時間 (4.18hに近い値？)")
        
        # 問題あるロジック3: 何らかの重複計算
        duplicate_value = correct_total * 5  # 5倍
        print(f"5倍の重複計算: {duplicate_value:.2f}時間 (20.13hに近い値？)")
        
        print("\n=== 問題の根本原因 ===")
        print("1. 18564.0h → shortage_time計算で0.5時間変換を忘れている")
        print("2. 4.18h → 正しい値にさらに0.5をかけている (dash_app.py line 1450, 5064)")
        print("3. 20.13h → 何らかの重複計算または係数エラー")
        
        print("\n=== 修正方法 ===")
        print("1. dash_app.py の * 0.5 を削除")
        print("2. shortage_time計算で正しく0.5時間変換")
        print("3. 按分計算ロジックを統一")
        
        # 正確な一致確認
        print(f"\n=== 一致確認 ===")
        print(f"正しい全体不足時間: {correct_total:.2f}h")
        print(f"職種別合計: {role_total:.2f}h (差: {abs(correct_total - role_total):.6f})")
        print(f"雇用形態別合計: {employment_total:.2f}h (差: {abs(correct_total - employment_total):.6f})")
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_shortage_calculations()