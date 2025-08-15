#!/usr/bin/env python3
"""
データ分解フェーズの深い思考検証
long_dfから各種集計・分解処理を包括的に検証
"""

import pandas as pd
from pathlib import Path
import sys
import os
import numpy as np
from datetime import datetime, timedelta

# パスを追加
sys.path.insert(0, os.getcwd())

from shift_suite.tasks.io_excel import ingest_excel

def deep_verify_data_decomposition():
    """データ分解フェーズの包括的検証"""
    excel_path = Path("ショート_テスト用データ.xlsx")
    
    if not excel_path.exists():
        print(f"ERROR: Test file not found: {excel_path}")
        return
    
    print("=== データ分解フェーズ 深い思考検証 ===")
    
    # 1. 基礎データの取得
    print("\n【1. 基礎データ取得】")
    excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
    sheet_names = excel_file.sheet_names
    shift_sheets = [s for s in sheet_names if "勤務" not in s]
    
    try:
        long_df, wt_df, unknown_codes = ingest_excel(
            excel_path,
            shift_sheets=shift_sheets,
            header_row=0,
            slot_minutes=30,
            year_month_cell_location="D1"
        )
        print(f"基礎データ: {len(long_df)}レコード")
        
    except Exception as e:
        print(f"基礎データ取得エラー: {e}")
        return
    
    # 2. 職種別分解の詳細検証
    print("\n【2. 職種別分解検証】")
    role_analysis = long_df.groupby('role').agg({
        'ds': 'count',
        'code': lambda x: x.value_counts().to_dict(),
        'holiday_type': lambda x: x.value_counts().to_dict(),
        'parsed_slots_count': ['sum', 'mean']
    }).round(2)
    
    print("職種別統計:")
    unique_roles = long_df['role'].unique()
    print(f"職種数: {len(unique_roles)}")
    print(f"職種一覧: {unique_roles.tolist()}")
    
    for role in unique_roles:
        role_data = long_df[long_df['role'] == role]
        print(f"\n=== 職種: {role} ===")
        print(f"  レコード数: {len(role_data)}")
        print(f"  スタッフ数: {role_data['staff'].nunique()}")
        
        # コード分布
        code_dist = role_data['code'].value_counts()
        print(f"  主要コード: {dict(list(code_dist.items())[:5])}")
        
        # 時間帯分布
        role_data_copy = role_data.copy()
        role_data_copy['hour'] = pd.to_datetime(role_data_copy['ds']).dt.hour
        hour_dist = role_data_copy['hour'].value_counts().sort_index()
        print(f"  時間帯範囲: {hour_dist.index.min()}時-{hour_dist.index.max()}時")
        
        # 夜勤時間帯の特別確認
        night_data = role_data_copy[role_data_copy['hour'].isin([0,1,2,3,4,5])]
        if len(night_data) > 0:
            print(f"  夜勤時間帯: {len(night_data)}件")
            night_codes = night_data['code'].value_counts()
            print(f"    夜勤コード: {dict(night_codes.items())}")
    
    # 3. 雇用形態別分解の詳細検証
    print("\n【3. 雇用形態別分解検証】")
    employment_analysis = long_df.groupby('employment').agg({
        'ds': 'count',
        'role': lambda x: x.value_counts().to_dict(),
        'code': lambda x: x.value_counts().to_dict()
    })
    
    unique_employments = long_df['employment'].unique()
    print(f"雇用形態数: {len(unique_employments)}")
    print(f"雇用形態一覧: {unique_employments.tolist()}")
    
    for emp in unique_employments:
        emp_data = long_df[long_df['employment'] == emp]
        print(f"\n=== 雇用形態: {emp} ===")
        print(f"  レコード数: {len(emp_data)}")
        print(f"  スタッフ数: {emp_data['staff'].nunique()}")
        
        # 職種分布
        role_dist = emp_data['role'].value_counts()
        print(f"  職種分布: {dict(list(role_dist.items())[:3])}")
    
    # 4. 時間帯別分解の詳細検証
    print("\n【4. 時間帯別分解検証】")
    long_df_copy = long_df.copy()
    long_df_copy['hour'] = pd.to_datetime(long_df_copy['ds']).dt.hour
    long_df_copy['minute'] = pd.to_datetime(long_df_copy['ds']).dt.minute
    long_df_copy['time_slot'] = long_df_copy['hour'].astype(str).str.zfill(2) + ":" + long_df_copy['minute'].astype(str).str.zfill(2)
    
    # 時間スロット分析
    time_slot_analysis = long_df_copy.groupby('time_slot').agg({
        'ds': 'count',
        'staff': 'nunique',
        'code': lambda x: (x != '').sum()  # 空文字以外の実勤務
    }).round(2)
    
    print("時間スロット統計:")
    print(f"総時間スロット数: {len(time_slot_analysis)}")
    print(f"時間範囲: {time_slot_analysis.index.min()} - {time_slot_analysis.index.max()}")
    
    # 30分間隔の確認
    time_slots = sorted(time_slot_analysis.index.tolist())
    print(f"30分間隔確認:")
    expected_slots = []
    for hour in range(24):
        expected_slots.extend([f"{hour:02d}:00", f"{hour:02d}:30"])
    
    missing_slots = set(expected_slots) - set(time_slots)
    extra_slots = set(time_slots) - set(expected_slots)
    
    print(f"  期待スロット数: {len(expected_slots)}")
    print(f"  実際スロット数: {len(time_slots)}")
    print(f"  欠損スロット: {len(missing_slots)} - {list(missing_slots)[:5] if missing_slots else '無し'}")
    print(f"  余剰スロット: {len(extra_slots)} - {list(extra_slots)[:5] if extra_slots else '無し'}")
    
    # 5. 職種×雇用形態クロス分析
    print("\n【5. 職種×雇用形態クロス分析】")
    cross_table = pd.crosstab(long_df['role'], long_df['employment'], margins=True)
    print("職種×雇用形態クロステーブル:")
    print(cross_table)
    
    # 6. 時間別実勤務者数分析
    print("\n【6. 時間別実勤務者数分析】")
    # 実勤務（空文字以外）のデータのみ
    working_data = long_df_copy[long_df_copy['code'] != '']
    working_data = working_data[working_data['holiday_type'] == '通常勤務']
    
    hourly_working = working_data.groupby('hour').agg({
        'staff': 'count',
        'code': lambda x: x.value_counts().to_dict()
    })
    
    print("時間別実勤務者数:")
    for hour in range(24):
        if hour in hourly_working.index:
            count = hourly_working.loc[hour, 'staff']
            codes = hourly_working.loc[hour, 'code']
            main_codes = dict(list(codes.items())[:3]) if isinstance(codes, dict) else {}
            print(f"  {hour:02d}時台: {count}人 - 主要コード: {main_codes}")
    
    # 特に夜勤時間帯の詳細分析
    print("\n【7. 夜勤時間帯詳細分析】")
    night_hours = [0, 1, 2, 3, 4, 5]
    night_working = working_data[working_data['hour'].isin(night_hours)]
    
    print(f"夜勤時間帯実勤務:")
    print(f"  総実勤務件数: {len(night_working)}")
    print(f"  実勤務者数/時間: {len(night_working) / len(night_hours):.1f}人")
    
    night_code_dist = night_working['code'].value_counts()
    print(f"  夜勤コード分布: {dict(night_code_dist.items())}")
    
    # 明番の詳細確認
    if '明' in night_code_dist.index:
        dawn_data = night_working[night_working['code'] == '明']
        dawn_hourly = dawn_data['hour'].value_counts().sort_index()
        print(f"  明番時間分布: {dict(dawn_hourly.items())}")
        
        # 明番の職種・雇用形態分布
        dawn_roles = dawn_data['role'].value_counts()
        dawn_employments = dawn_data['employment'].value_counts()
        print(f"  明番職種分布: {dict(dawn_roles.items())}")
        print(f"  明番雇用形態: {dict(dawn_employments.items())}")
    
    # 8. データ整合性チェック
    print("\n【8. データ整合性チェック】")
    
    # 合計チェック
    total_records = len(long_df)
    role_sum = sum(len(long_df[long_df['role'] == role]) for role in unique_roles)
    emp_sum = sum(len(long_df[long_df['employment'] == emp]) for emp in unique_employments)
    
    print(f"データ整合性:")
    print(f"  総レコード数: {total_records}")
    print(f"  職種別合計: {role_sum}")
    print(f"  雇用形態別合計: {emp_sum}")
    print(f"  職種整合性: {'OK' if total_records == role_sum else 'NG'}")
    print(f"  雇用形態整合性: {'OK' if total_records == emp_sum else 'NG'}")
    
    # 時間スロット整合性
    expected_total_slots = 30 * 48  # 30日 × 48スロット/日
    actual_unique_slots = long_df_copy['ds'].nunique()
    print(f"  期待時間スロット: {expected_total_slots}")
    print(f"  実際時間スロット: {actual_unique_slots}")
    print(f"  時間整合性: {'OK' if expected_total_slots == actual_unique_slots else 'NG'}")
    
    # 9. ヒートマップ用データ生成テスト
    print("\n【9. ヒートマップ用データ生成テスト】")
    try:
        # create_heatmap_data関数のテスト（存在する場合）
        print("ヒートマップデータ生成テスト実行中...")
        
        # 職種別ヒートマップデータ作成のシミュレーション
        for role in unique_roles[:2]:  # 最初の2職種のみテスト
            role_data = long_df[long_df['role'] == role]
            role_working = role_data[role_data['holiday_type'] == '通常勤務']
            
            if len(role_working) > 0:
                # 日付×時間のピボットテーブル作成
                role_working_copy = role_working.copy()
                role_working_copy['date'] = pd.to_datetime(role_working_copy['ds']).dt.date
                role_working_copy['time_slot'] = pd.to_datetime(role_working_copy['ds']).dt.strftime('%H:%M')
                
                pivot_data = role_working_copy.groupby(['date', 'time_slot']).size().reset_index(name='count')
                pivot_table = pivot_data.pivot(index='date', columns='time_slot', values='count').fillna(0)
                
                print(f"  {role}ヒートマップ: {pivot_table.shape} (日×時間)")
                print(f"    勤務データ範囲: {pivot_table.values.min()}-{pivot_table.values.max()}人")
        
    except Exception as e:
        print(f"ヒートマップテストエラー: {e}")
    
    print("\n=== データ分解フェーズ検証完了 ===")

if __name__ == "__main__":
    deep_verify_data_decomposition()