#!/usr/bin/env python3
"""
分析結果可視化加工フェーズの深い思考検証
実際の不足時間計算、シナリオ別集計、ダッシュボード用データ生成を包括的に検証
"""

import pandas as pd
from pathlib import Path
import sys
import os
import numpy as np
from datetime import datetime, timedelta
import json

# パスを追加
sys.path.insert(0, os.getcwd())

from shift_suite.tasks.io_excel import ingest_excel

def deep_verify_visualization_processing():
    """分析結果可視化加工フェーズの包括的検証"""
    excel_path = Path("ショート_テスト用データ.xlsx")
    
    if not excel_path.exists():
        print(f"ERROR: Test file not found: {excel_path}")
        return
    
    print("=== 分析結果可視化加工フェーズ 深い思考検証 ===")
    
    # 1. 基礎データの取得
    print("\n【1. 基礎データ取得とクロスチェック】")
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
    
    # 2. dash_app.pyの不足時間計算アルゴリズムの詳細分析
    print("\n【2. 実際の不足時間計算アルゴリズム分析】")
    
    # dash_app.pyの実装を調査する（存在する場合）
    dash_app_path = Path("dash_app.py")
    if dash_app_path.exists():
        print("dash_app.py が存在します。不足時間計算の実装を分析中...")
        
        # ファイル内容を読み取って不足時間計算に関連する部分を抽出
        with open(dash_app_path, 'r', encoding='utf-8') as f:
            dash_content = f.read()
        
        # 不足時間関連の関数やロジックを検索
        shortage_related_lines = []
        lines = dash_content.split('\n')
        
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['shortage', '不足', 'deficit', 'shortfall']):
                # 前後5行も含めて抽出
                start = max(0, i-2)
                end = min(len(lines), i+3)
                context = lines[start:end]
                shortage_related_lines.append(f"行{i+1}周辺: " + "\n  ".join(context))
        
        if shortage_related_lines:
            print("不足時間計算関連コード（最初の3箇所）:")
            for idx, context in enumerate(shortage_related_lines[:3]):
                print(f"\n=== 箇所{idx+1} ===")
                print(context)
        else:
            print("⚠️ dash_app.py に明示的な不足時間計算コードが見つかりません")
    else:
        print("⚠️ dash_app.py が見つかりません")
    
    # 3. 実勤務データからのシナリオ別需要計算シミュレーション
    print("\n【3. シナリオ別需要計算シミュレーション】")
    
    working_data = long_df[long_df['holiday_type'] == '通常勤務'].copy()
    working_data['hour'] = pd.to_datetime(working_data['ds']).dt.hour
    working_data['date'] = pd.to_datetime(working_data['ds']).dt.date
    working_data['time_slot'] = pd.to_datetime(working_data['ds']).dt.strftime('%H:%M')
    
    # 時間スロット×日付の実勤務者数マトリックス作成
    daily_slot_counts = working_data.groupby(['date', 'time_slot']).size().reset_index(name='actual_count')
    pivot_actual = daily_slot_counts.pivot(index='time_slot', columns='date', values='actual_count').fillna(0)
    
    print(f"実勤務マトリックス形状: {pivot_actual.shape} (時間スロット×日付)")
    print(f"実勤務データ範囲: {pivot_actual.values.min():.0f} - {pivot_actual.values.max():.0f}人")
    
    # 各時間スロットでのシナリオ計算
    scenario_results = {}
    
    for time_slot in pivot_actual.index:
        slot_data = pivot_actual.loc[time_slot]
        slot_data_nonzero = slot_data[slot_data > 0]  # 0人の日は除外
        
        if len(slot_data_nonzero) > 0:
            scenarios = {
                'median': slot_data_nonzero.median(),
                'mean': slot_data_nonzero.mean(),
                '25th_percentile': slot_data_nonzero.quantile(0.25),
                '75th_percentile': slot_data_nonzero.quantile(0.75)
            }
        else:
            scenarios = {
                'median': 0,
                'mean': 0,
                '25th_percentile': 0,
                '75th_percentile': 0
            }
        
        scenario_results[time_slot] = scenarios
    
    # シナリオ結果の概要表示
    print("\nシナリオ計算結果サンプル（最初の6時間スロット）:")
    scenario_df = pd.DataFrame(scenario_results).T
    print(scenario_df.head(12).round(2))
    
    # 4. 職種別需要シナリオ計算
    print("\n【4. 職種別需要シナリオ計算】")
    
    role_scenario_results = {}
    unique_roles = working_data['role'].unique()
    
    for role in unique_roles[:3]:  # 最初の3職種のみ詳細分析
        role_data = working_data[working_data['role'] == role]
        role_daily_counts = role_data.groupby(['date', 'time_slot']).size().reset_index(name='count')
        role_pivot = role_daily_counts.pivot(index='time_slot', columns='date', values='count').fillna(0)
        
        role_scenarios = {}
        for time_slot in role_pivot.index:
            slot_data = role_pivot.loc[time_slot]
            slot_data_nonzero = slot_data[slot_data > 0]
            
            if len(slot_data_nonzero) > 0:
                role_scenarios[time_slot] = {
                    'median': slot_data_nonzero.median(),
                    'mean': slot_data_nonzero.mean(),
                    '25th_percentile': slot_data_nonzero.quantile(0.25)
                }
            else:
                role_scenarios[time_slot] = {
                    'median': 0,
                    'mean': 0,
                    '25th_percentile': 0
                }
        
        role_scenario_results[role] = role_scenarios
        
        # 職種別結果サマリー
        role_scenario_df = pd.DataFrame(role_scenarios).T
        total_median_demand = role_scenario_df['median'].sum() * 0.5  # 30分 = 0.5時間
        total_mean_demand = role_scenario_df['mean'].sum() * 0.5
        
        print(f"\n=== 職種: {role} ===")
        print(f"  中央値シナリオ総需要時間: {total_median_demand:.1f}時間")
        print(f"  平均値シナリオ総需要時間: {total_mean_demand:.1f}時間")
        print(f"  勤務時間スロット数: {(role_scenario_df['median'] > 0).sum()}")
    
    # 5. 不足時間計算の詳細シミュレーション
    print("\n【5. 不足時間計算詳細シミュレーション】")
    
    # 中央値シナリオでの不足時間計算
    median_scenario_df = scenario_df[['median']].copy()
    median_scenario_df.columns = ['required_staff']
    
    # 実勤務者数と必要人数の比較
    actual_avg_per_slot = working_data.groupby('time_slot').size() / 30  # 30日平均
    comparison_df = pd.DataFrame({
        'time_slot': actual_avg_per_slot.index,
        'actual_avg': actual_avg_per_slot.values,
        'required_median': median_scenario_df['required_staff'].values
    })
    
    comparison_df['shortage'] = np.maximum(0, comparison_df['required_median'] - comparison_df['actual_avg'])
    comparison_df['excess'] = np.maximum(0, comparison_df['actual_avg'] - comparison_df['required_median'])
    comparison_df['shortage_hours'] = comparison_df['shortage'] * 0.5  # 30分間隔
    comparison_df['excess_hours'] = comparison_df['excess'] * 0.5
    
    total_shortage_hours = comparison_df['shortage_hours'].sum()
    total_excess_hours = comparison_df['excess_hours'].sum()
    
    print(f"中央値シナリオ不足時間計算結果:")
    print(f"  総不足時間: {total_shortage_hours:.1f}時間")
    print(f"  総余剰時間: {total_excess_hours:.1f}時間")
    print(f"  不足スロット数: {(comparison_df['shortage'] > 0).sum()}/48")
    print(f"  余剰スロット数: {(comparison_df['excess'] > 0).sum()}/48")
    
    # 最も不足している時間帯の詳細
    max_shortage_idx = comparison_df['shortage'].idxmax()
    max_shortage_slot = comparison_df.loc[max_shortage_idx]
    print(f"  最大不足時間帯: {max_shortage_slot['time_slot']} ({max_shortage_slot['shortage']:.1f}人不足)")
    
    # 6. 夜勤時間帯の特別不足分析
    print("\n【6. 夜勤時間帯特別不足分析】")
    
    night_slots = ['00:00', '00:30', '01:00', '01:30', '02:00', '02:30', 
                   '03:00', '03:30', '04:00', '04:30', '05:00', '05:30']
    
    night_comparison = comparison_df[comparison_df['time_slot'].isin(night_slots)]
    night_shortage_hours = night_comparison['shortage_hours'].sum()
    
    print(f"夜勤時間帯不足分析:")
    print(f"  夜勤不足時間: {night_shortage_hours:.1f}時間")
    print(f"  夜勤不足比率: {night_shortage_hours / total_shortage_hours * 100:.1f}%" if total_shortage_hours > 0 else "  夜勤不足比率: 0%")
    
    # 夜勤の明番コード「明」の影響分析
    dawn_data = working_data[working_data['code'] == '明']
    if len(dawn_data) > 0:
        dawn_slot_counts = dawn_data.groupby('time_slot').size()
        print(f"  明番「明」による夜勤カバー:")
        for slot, count in dawn_slot_counts.items():
            if slot in night_slots:
                avg_dawn_per_day = count / 30
                print(f"    {slot}: 平均{avg_dawn_per_day:.1f}人/日")
    
    # 7. 三つのレベル合計検証（全体＝職種別合計＝雇用形態別合計）
    print("\n【7. 三つのレベル合計検証】")
    
    # 全体合計
    total_shortage_all = comparison_df['shortage_hours'].sum()
    
    # 職種別合計
    role_shortage_total = 0
    for role in unique_roles:
        role_data = working_data[working_data['role'] == role]
        role_slot_counts = role_data.groupby('time_slot').size() / 30
        
        role_comparison = comparison_df.copy()
        # 各職種の実勤務者数で比較（簡易版）
        role_comparison['role_actual'] = role_comparison['time_slot'].map(role_slot_counts).fillna(0)
        role_comparison['role_shortage'] = np.maximum(0, role_comparison['required_median'] * (len(role_data) / len(working_data)) - role_comparison['role_actual'])
        role_comparison['role_shortage_hours'] = role_comparison['role_shortage'] * 0.5
        
        role_shortage = role_comparison['role_shortage_hours'].sum()
        role_shortage_total += role_shortage
        
        if role in unique_roles[:3]:  # 最初の3職種のみ表示
            print(f"  {role}不足時間: {role_shortage:.1f}時間")
    
    # 雇用形態別合計
    employment_shortage_total = 0
    unique_employments = working_data['employment'].unique()
    for emp in unique_employments:
        emp_data = working_data[working_data['employment'] == emp]
        emp_slot_counts = emp_data.groupby('time_slot').size() / 30
        
        emp_comparison = comparison_df.copy()
        emp_comparison['emp_actual'] = emp_comparison['time_slot'].map(emp_slot_counts).fillna(0)
        emp_comparison['emp_shortage'] = np.maximum(0, emp_comparison['required_median'] * (len(emp_data) / len(working_data)) - emp_comparison['emp_actual'])
        emp_comparison['emp_shortage_hours'] = emp_comparison['emp_shortage'] * 0.5
        
        emp_shortage = emp_comparison['emp_shortage_hours'].sum()
        employment_shortage_total += emp_shortage
        
        print(f"  {emp}不足時間: {emp_shortage:.1f}時間")
    
    print(f"\n合計検証:")
    print(f"  全体不足時間: {total_shortage_all:.1f}時間")
    print(f"  職種別合計: {role_shortage_total:.1f}時間")
    print(f"  雇用形態別合計: {employment_shortage_total:.1f}時間")
    print(f"  整合性: {'OK' if abs(total_shortage_all - role_shortage_total) < 1 else 'NG'}")
    
    # 8. ダッシュボード用データ構造の生成検証
    print("\n【8. ダッシュボード用データ構造生成検証】")
    
    # Plotly用のデータ構造を模擬
    dashboard_data = {
        'overview': {
            'total_shortage_hours': total_shortage_hours,
            'total_excess_hours': total_excess_hours,
            'scenario': 'median'
        },
        'hourly_breakdown': comparison_df[['time_slot', 'shortage_hours', 'excess_hours']].to_dict('records'),
        'role_breakdown': {},
        'employment_breakdown': {}
    }
    
    # 職種別データ
    for role in unique_roles:
        role_data = working_data[working_data['role'] == role]
        role_slot_counts = role_data.groupby('time_slot').size() / 30
        
        dashboard_data['role_breakdown'][role] = {
            'total_hours': len(role_data) * 0.5,
            'avg_staff_per_slot': role_slot_counts.mean()
        }
    
    # 雇用形態別データ
    for emp in unique_employments:
        emp_data = working_data[working_data['employment'] == emp]
        
        dashboard_data['employment_breakdown'][emp] = {
            'total_hours': len(emp_data) * 0.5,
            'staff_count': emp_data['staff'].nunique()
        }
    
    print("ダッシュボード用データ構造:")
    print(f"  概要データ: {dashboard_data['overview']}")
    print(f"  時間別データ: {len(dashboard_data['hourly_breakdown'])}スロット")
    print(f"  職種別データ: {len(dashboard_data['role_breakdown'])}職種")
    print(f"  雇用形態別データ: {len(dashboard_data['employment_breakdown'])}形態")
    
    # 9. データ出力形式の検証（Parquet想定）
    print("\n【9. データ出力形式検証】")
    
    # Parquet出力用のデータフレーム作成
    output_df = comparison_df.copy()
    output_df['scenario'] = 'median'
    output_df['date_generated'] = datetime.now()
    
    print("出力データフレーム:")
    print(f"  形状: {output_df.shape}")
    print(f"  列: {output_df.columns.tolist()}")
    print(f"  データ型: {output_df.dtypes.to_dict()}")
    
    # メモリ使用量と効率性
    memory_usage = output_df.memory_usage(deep=True).sum() / 1024 / 1024  # MB
    print(f"  メモリ使用量: {memory_usage:.2f}MB")
    
    # 10. 計算精度と性能の検証
    print("\n【10. 計算精度と性能検証】")
    
    # 異なるシナリオでの計算時間測定
    import time
    
    scenarios_to_test = ['median', 'mean', '25th_percentile']
    calculation_times = {}
    
    for scenario in scenarios_to_test:
        start_time = time.time()
        
        scenario_column = scenario_df[scenario]
        test_comparison = pd.DataFrame({
            'required': scenario_column.values,
            'actual': actual_avg_per_slot.values
        })
        test_comparison['shortage'] = np.maximum(0, test_comparison['required'] - test_comparison['actual'])
        test_shortage = test_comparison['shortage'].sum() * 0.5
        
        end_time = time.time()
        calculation_times[scenario] = end_time - start_time
        
        print(f"  {scenario}シナリオ: {test_shortage:.1f}時間不足 (計算時間: {calculation_times[scenario]*1000:.2f}ms)")
    
    # 11. エラーハンドリングと異常値検出
    print("\n【11. エラーハンドリングと異常値検出】")
    
    # 異常に高い不足時間の検出
    threshold_shortage = comparison_df['shortage_hours'].quantile(0.95)
    abnormal_slots = comparison_df[comparison_df['shortage_hours'] > threshold_shortage]
    
    if len(abnormal_slots) > 0:
        print("異常に高い不足時間のスロット:")
        for _, row in abnormal_slots.iterrows():
            print(f"  {row['time_slot']}: {row['shortage_hours']:.1f}時間不足")
    else:
        print("異常な不足時間は検出されませんでした")
    
    # データ品質チェック
    data_quality_issues = []
    
    if comparison_df['shortage_hours'].isna().any():
        data_quality_issues.append("不足時間にNaN値が含まれています")
    
    if (comparison_df['shortage_hours'] < 0).any():
        data_quality_issues.append("負の不足時間が検出されました")
    
    if len(data_quality_issues) > 0:
        print("データ品質の問題:")
        for issue in data_quality_issues:
            print(f"  ⚠️ {issue}")
    else:
        print("データ品質: 正常")
    
    print("\n=== 分析結果可視化加工フェーズ検証完了 ===")
    
    # 主要な発見をサマリー
    print(f"\n【主要な発見】")
    print(f"1. 中央値シナリオでの総不足時間: {total_shortage_hours:.1f}時間")
    print(f"2. 夜勤時間帯の不足時間: {night_shortage_hours:.1f}時間 ({night_shortage_hours/total_shortage_hours*100:.1f}%)" if total_shortage_hours > 0 else "2. 夜勤時間帯の不足時間: 0時間")
    print(f"3. 処理された時間スロット数: {len(comparison_df)}")
    print(f"4. 異常値スロット数: {len(abnormal_slots)}")
    print(f"5. データ品質: {'正常' if len(data_quality_issues) == 0 else '問題あり'}")

if __name__ == "__main__":
    deep_verify_visualization_processing()