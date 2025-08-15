#!/usr/bin/env python3
"""
データ分析フェーズの深い思考検証
不足時間計算、需要予測、shortage分析を包括的に検証
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

def deep_verify_data_analysis():
    """データ分析フェーズの包括的検証"""
    excel_path = Path("ショート_テスト用データ.xlsx")
    
    if not excel_path.exists():
        print(f"ERROR: Test file not found: {excel_path}")
        return
    
    print("=== データ分析フェーズ 深い思考検証 ===")
    
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
    
    # 2. 実勤務時間と需要時間の詳細分析
    print("\n【2. 実勤務時間vs需要時間分析】")
    
    # 実勤務データ（休暇以外）
    working_data = long_df[long_df['holiday_type'] == '通常勤務'].copy()
    working_data['hour'] = pd.to_datetime(working_data['ds']).dt.hour
    working_data['date'] = pd.to_datetime(working_data['ds']).dt.date
    working_data['time_slot'] = pd.to_datetime(working_data['ds']).dt.strftime('%H:%M')
    
    print(f"実勤務データ件数: {len(working_data)}")
    print(f"休暇データ件数: {len(long_df) - len(working_data)}")
    
    # 時間スロット別実勤務者数
    slot_working_count = working_data.groupby('time_slot').size().reset_index(name='actual_staff')
    print(f"時間スロット別実勤務統計:")
    print(f"  最小勤務者数: {slot_working_count['actual_staff'].min()}人")
    print(f"  最大勤務者数: {slot_working_count['actual_staff'].max()}人")
    print(f"  平均勤務者数: {slot_working_count['actual_staff'].mean():.1f}人")
    
    # 職種別時間スロット分析
    print(f"\n職種別時間スロット分析:")
    for role in working_data['role'].unique()[:3]:  # 主要3職種
        role_data = working_data[working_data['role'] == role]
        role_slot_count = role_data.groupby('time_slot').size()
        print(f"  {role}: 平均{role_slot_count.mean():.1f}人/スロット (範囲: {role_slot_count.min()}-{role_slot_count.max()}人)")
    
    # 3. 夜勤時間帯の詳細不足分析
    print("\n【3. 夜勤時間帯詳細不足分析】")
    
    night_slots = ['00:00', '00:30', '01:00', '01:30', '02:00', '02:30', 
                   '03:00', '03:30', '04:00', '04:30', '05:00', '05:30']
    
    night_working = working_data[working_data['time_slot'].isin(night_slots)]
    
    print(f"夜勤時間帯分析:")
    print(f"  夜勤時間スロット数: {len(night_slots)}")
    print(f"  夜勤実勤務件数: {len(night_working)}")
    print(f"  平均夜勤者数/スロット: {len(night_working) / len(night_slots):.1f}人")
    
    # 夜勤の職種・雇用形態分析
    night_role_dist = night_working['role'].value_counts()
    night_emp_dist = night_working['employment'].value_counts()
    print(f"  夜勤職種分布: {dict(night_role_dist.items())}")
    print(f"  夜勤雇用形態: {dict(night_emp_dist.items())}")
    
    # 夜勤の日別変動分析
    night_daily = night_working.groupby('date').size()
    print(f"  夜勤日別変動: 平均{night_daily.mean():.1f}人/日 (範囲: {night_daily.min()}-{night_daily.max()}人)")
    
    # 4. 不足時間計算アルゴリズムの検証
    print("\n【4. 不足時間計算アルゴリズム検証】")
    
    # 簡易不足時間計算（仮定：各時間帯に最低2名必要）
    REQUIRED_STAFF_PER_SLOT = 2
    
    shortage_analysis = []
    for slot in slot_working_count['time_slot']:
        actual = slot_working_count[slot_working_count['time_slot'] == slot]['actual_staff'].iloc[0]
        required = REQUIRED_STAFF_PER_SLOT
        shortage = max(0, required - actual)
        excess = max(0, actual - required)
        
        shortage_analysis.append({
            'time_slot': slot,
            'actual': actual,
            'required': required,
            'shortage': shortage,
            'excess': excess,
            'shortage_hours': shortage * 0.5  # 30分 = 0.5時間
        })
    
    shortage_df = pd.DataFrame(shortage_analysis)
    
    total_shortage_hours = shortage_df['shortage_hours'].sum()
    total_excess_hours = shortage_df['excess'].sum() * 0.5
    
    print(f"不足時間計算結果:")
    print(f"  総不足時間: {total_shortage_hours:.1f}時間")
    print(f"  総余剰時間: {total_excess_hours:.1f}時間")
    print(f"  不足スロット数: {(shortage_df['shortage'] > 0).sum()}個")
    print(f"  余剰スロット数: {(shortage_df['excess'] > 0).sum()}個")
    
    # 最も不足している時間帯
    max_shortage_slot = shortage_df.loc[shortage_df['shortage'].idxmax()]
    print(f"  最大不足: {max_shortage_slot['time_slot']} ({max_shortage_slot['shortage']}人不足)")
    
    # 5. 夜勤時間帯の特別不足分析
    print("\n【5. 夜勤時間帯特別不足分析】")
    
    night_shortage = shortage_df[shortage_df['time_slot'].isin(night_slots)]
    night_total_shortage = night_shortage['shortage_hours'].sum()
    
    print(f"夜勤時間帯不足分析:")
    print(f"  夜勤不足時間: {night_total_shortage:.1f}時間")
    print(f"  夜勤不足比率: {night_total_shortage / total_shortage_hours * 100:.1f}%")
    
    # 各夜勤スロットの詳細
    print(f"  夜勤スロット別不足:")
    for _, row in night_shortage.iterrows():
        if row['shortage'] > 0:
            print(f"    {row['time_slot']}: {row['shortage']}人不足 ({row['shortage_hours']:.1f}時間)")
    
    # 6. 職種別不足分析
    print("\n【6. 職種別不足分析】")
    
    for role in working_data['role'].unique()[:3]:  # 主要3職種
        role_data = working_data[working_data['role'] == role]
        role_slot_count = role_data.groupby('time_slot').size()
        
        # 職種別不足計算（仮定：各職種最低1名必要）
        REQUIRED_ROLE_STAFF = 1
        role_shortage_slots = 48 - len(role_slot_count)  # 勤務していないスロット
        role_total_shortage = role_shortage_slots * REQUIRED_ROLE_STAFF * 0.5
        
        print(f"  {role}:")
        print(f"    勤務スロット数: {len(role_slot_count)}/48")
        print(f"    不足スロット数: {role_shortage_slots}")
        print(f"    推定不足時間: {role_total_shortage:.1f}時間")
    
    # 7. 雇用形態別コスト分析
    print("\n【7. 雇用形態別コスト分析】")
    
    # 仮想時給（分析用）
    HOURLY_RATES = {
        '正社員': 2000,
        'パート': 1200,
        'スポット': 1800
    }
    
    for emp_type in working_data['employment'].unique():
        emp_data = working_data[working_data['employment'] == emp_type]
        total_hours = len(emp_data) * 0.5  # 30分 = 0.5時間
        hourly_rate = HOURLY_RATES.get(emp_type, 1500)
        total_cost = total_hours * hourly_rate
        
        print(f"  {emp_type}:")
        print(f"    総勤務時間: {total_hours:.1f}時間")
        print(f"    時給: {hourly_rate:,}円")
        print(f"    推定総コスト: {total_cost:,.0f}円")
    
    # 8. 時系列変動分析
    print("\n【8. 時系列変動分析】")
    
    daily_working = working_data.groupby('date').size()
    
    print(f"日別勤務変動:")
    print(f"  平均勤務件数: {daily_working.mean():.1f}件/日")
    print(f"  最小勤務件数: {daily_working.min()}件/日")
    print(f"  最大勤務件数: {daily_working.max()}件/日")
    print(f"  標準偏差: {daily_working.std():.1f}件")
    
    # 曜日別分析
    daily_working_df = daily_working.reset_index()
    daily_working_df['weekday'] = pd.to_datetime(daily_working_df['date']).dt.day_name()
    weekday_avg = daily_working_df.groupby('weekday')[0].mean()
    
    print(f"  曜日別平均勤務:")
    for weekday, avg in weekday_avg.items():
        print(f"    {weekday}: {avg:.1f}件")
    
    # 9. 異常値・外れ値検出
    print("\n【9. 異常値・外れ値検出】")
    
    # 時間スロット別異常値検出
    slot_stats = slot_working_count['actual_staff']
    q1 = slot_stats.quantile(0.25)
    q3 = slot_stats.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    outliers = slot_working_count[
        (slot_working_count['actual_staff'] < lower_bound) | 
        (slot_working_count['actual_staff'] > upper_bound)
    ]
    
    print(f"時間スロット異常値検出:")
    print(f"  正常範囲: {lower_bound:.1f} - {upper_bound:.1f}人")
    print(f"  異常スロット数: {len(outliers)}")
    
    if len(outliers) > 0:
        print(f"  異常スロット例:")
        for _, row in outliers.head().iterrows():
            print(f"    {row['time_slot']}: {row['actual_staff']}人")
    
    # 10. 予測精度検証（簡易版）
    print("\n【10. 予測精度検証】")
    
    # 前半15日で後半15日を予測する簡易テスト
    split_date = datetime(2025, 6, 16).date()
    
    train_data = working_data[working_data['date'] < split_date]
    test_data = working_data[working_data['date'] >= split_date]
    
    # 時間スロット別平均を予測値とする
    train_slot_avg = train_data.groupby('time_slot').size()
    
    prediction_errors = []
    for slot in train_slot_avg.index:
        predicted = train_slot_avg[slot] / 15  # 15日間の平均を1日当たりに変換
        actual_test = test_data[test_data['time_slot'] == slot].groupby('date').size()
        
        if len(actual_test) > 0:
            avg_actual = actual_test.mean()
            error = abs(predicted - avg_actual)
            prediction_errors.append(error)
    
    if prediction_errors:
        avg_prediction_error = np.mean(prediction_errors)
        print(f"予測精度テスト:")
        print(f"  平均予測誤差: {avg_prediction_error:.2f}人/スロット")
        print(f"  予測精度: {100 - avg_prediction_error * 100:.1f}%")
    
    print("\n=== データ分析フェーズ検証完了 ===")

if __name__ == "__main__":
    deep_verify_data_analysis()