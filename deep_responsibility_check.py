#!/usr/bin/env python3
"""
深い思考と責任感を持った根本的確認
前提条件から全て見直す
"""

import pandas as pd
from pathlib import Path
import sys
import os
import numpy as np

# パスを追加
sys.path.insert(0, os.getcwd())

def deep_responsibility_check():
    """深い思考と責任感を持った確認"""
    print("=== 深い思考と責任感を持った根本的確認 ===")
    
    # データ取得
    from shift_suite.tasks.io_excel import ingest_excel
    
    excel_path = Path("ショート_テスト用データ.xlsx")
    excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
    shift_sheets = [s for s in excel_file.sheet_names if "勤務" not in s]
    
    long_df, wt_df, unknown_codes = ingest_excel(
        excel_path,
        shift_sheets=shift_sheets,
        header_row=0,
        slot_minutes=30,
        year_month_cell_location="D1"
    )
    
    print(f"データ取得完了: {len(long_df)}レコード")
    
    # 1. データ構造の根本的理解
    print("\n【1. データ構造の根本的理解】")
    
    print(f"long_dfカラム: {long_df.columns.tolist()}")
    print(f"サンプルレコード:")
    print(long_df.head(3))
    
    # 各レコードが何を表すかの確認
    working_data = long_df[long_df['holiday_type'] == '通常勤務'].copy()
    print(f"\n勤務データ: {len(working_data)}レコード")
    
    # 時間軸の理解
    working_data['datetime'] = pd.to_datetime(working_data['ds'])
    working_data['date'] = working_data['datetime'].dt.date
    working_data['time_slot'] = working_data['datetime'].dt.strftime('%H:%M')
    
    print(f"時間範囲: {working_data['datetime'].min()} から {working_data['datetime'].max()}")
    print(f"ユニーク日数: {working_data['date'].nunique()}")
    print(f"ユニーク時間スロット: {working_data['time_slot'].nunique()}")
    
    # 2. 「不足時間」の定義を根本的に確認
    print("\n【2. 不足時間の定義の根本的確認】")
    
    # 前提条件の確認
    print("前提条件の検証:")
    print("- 各レコードは「特定の人が特定の30分間で勤務する」ことを表す")
    print("- time_slotは30分単位の時間帯")
    print("- 不足時間 = (必要な人数 - 実際の人数) × 0.5時間")
    
    # 実際のデータでの確認
    sample_slot = "09:00"
    sample_date = working_data['date'].iloc[0]
    
    sample_data = working_data[
        (working_data['time_slot'] == sample_slot) & 
        (working_data['date'] == sample_date)
    ]
    
    print(f"\nサンプル確認 ({sample_date} {sample_slot}):")
    print(f"該当レコード数: {len(sample_data)}")
    print(f"勤務者: {sample_data['staff'].tolist()}")
    print(f"職種: {sample_data['role'].tolist()}")
    
    # 3. 需要の算出方法の根本的検証
    print("\n【3. 需要算出方法の根本的検証】")
    
    # 全体需要の計算方法の検証
    print("=== 全体需要計算の詳細 ===")
    
    # 各時間スロットでの日別人数
    daily_slot_counts = working_data.groupby(['date', 'time_slot']).size().reset_index(name='people_count')
    print(f"日別スロット別カウント例:")
    print(daily_slot_counts.head())
    
    # 時間スロット別の中央値計算
    median_by_slot = daily_slot_counts.groupby('time_slot')['people_count'].median()
    print(f"\n時間スロット別中央値 (最初の10スロット):")
    print(median_by_slot.head(10))
    
    # 4. 職種別計算の根本的検証
    print("\n【4. 職種別計算の根本的検証】")
    
    roles = working_data['role'].unique()
    print(f"職種一覧: {roles}")
    
    # 職種別の詳細分析
    role_analysis = {}
    for role in roles:
        role_data = working_data[working_data['role'] == role]
        
        # 職種別の日別スロット別カウント
        role_daily_counts = role_data.groupby(['date', 'time_slot']).size().reset_index(name='people_count')
        role_median = role_daily_counts.groupby('time_slot')['people_count'].median() if len(role_daily_counts) > 0 else pd.Series()
        
        role_analysis[role] = {
            'total_records': len(role_data),
            'unique_dates': role_data['date'].nunique(),
            'unique_slots': role_data['time_slot'].nunique(),
            'median_demand_slots': len(role_median),
            'total_median_demand': role_median.sum() if len(role_median) > 0 else 0
        }
        
        print(f"\n{role}:")
        for key, value in role_analysis[role].items():
            print(f"  {key}: {value}")
    
    # 5. 計算ロジックの根本的な問題の特定
    print("\n【5. 計算ロジックの根本的問題特定】")
    
    # 正しい全体計算
    print("=== 正しい全体計算の検証 ===")
    
    # 方法1: 全データから時間スロット別の中央値需要を計算
    total_daily_counts = working_data.groupby(['date', 'time_slot']).size().reset_index(name='total_people')
    total_median_demand = total_daily_counts.groupby('time_slot')['total_people'].median()
    
    # 方法2: 各日の実績平均
    total_actual_avg = working_data.groupby('time_slot').size() / working_data['date'].nunique()
    
    # 全体不足計算
    total_shortage_by_slot = np.maximum(0, total_median_demand - total_actual_avg)
    total_shortage_hours = total_shortage_by_slot.sum() * 0.5
    
    print(f"全体中央値需要合計: {total_median_demand.sum():.2f}人")
    print(f"全体実績平均合計: {total_actual_avg.sum():.2f}人")
    print(f"全体不足時間: {total_shortage_hours:.2f}時間")
    
    # 6. 職種別合計の正当性確認
    print("\n=== 職種別合計の正当性確認 ===")
    
    # 各職種の需要を個別に計算して合計
    role_total_demand = 0
    role_total_actual = 0
    role_total_shortage = 0
    
    print("職種別詳細:")
    for role in roles:
        role_data = working_data[working_data['role'] == role]
        
        if len(role_data) > 0:
            # 職種別の日別カウント
            role_daily = role_data.groupby(['date', 'time_slot']).size().reset_index(name='count')
            role_median_demand = role_daily.groupby('time_slot')['count'].median()
            role_actual_avg = role_data.groupby('time_slot').size() / working_data['date'].nunique()
            
            role_shortage = np.maximum(0, role_median_demand - role_actual_avg).sum() * 0.5
            
            role_total_demand += role_median_demand.sum()
            role_total_actual += role_actual_avg.sum()
            role_total_shortage += role_shortage
            
            print(f"  {role}: 需要{role_median_demand.sum():.1f}, 実績{role_actual_avg.sum():.1f}, 不足{role_shortage:.2f}h")
    
    print(f"職種別合計: 需要{role_total_demand:.1f}, 実績{role_total_actual:.1f}, 不足{role_total_shortage:.2f}h")
    
    # 7. 根本的な問題の特定
    print("\n【7. 根本的問題の特定】")
    
    demand_diff = abs(total_median_demand.sum() - role_total_demand)
    actual_diff = abs(total_actual_avg.sum() - role_total_actual)
    shortage_diff = abs(total_shortage_hours - role_total_shortage)
    
    print(f"需要の差異: {demand_diff:.2f}人")
    print(f"実績の差異: {actual_diff:.2f}人")
    print(f"不足時間の差異: {shortage_diff:.2f}時間")
    
    # 8. dash_app.pyの実装との比較
    print("\n【8. dash_app.py実装との根本的比較】")
    
    # dash_app.pyの関数を探す
    dash_path = Path("dash_app.py")
    if dash_path.exists():
        with open(dash_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # create_shortage_from_heat_all関数の詳細抽出
        lines = content.split('\n')
        in_function = False
        function_lines = []
        
        for line in lines:
            if 'def create_shortage_from_heat_all' in line:
                in_function = True
                function_lines.append(line)
            elif in_function:
                if line.strip() == '' or line.startswith('    ') or line.startswith('\t'):
                    function_lines.append(line)
                else:
                    break
        
        print("dash_app.pyの不足時間計算関数:")
        print('\n'.join(function_lines[:30]))  # 最初の30行
    
    # 9. 正しい計算方法の提案
    print("\n【9. 責任ある正しい計算方法の提案】")
    
    print("根本的問題:")
    print("1. 職種別計算では各職種が独立してスロットに需要を持つと仮定")
    print("2. 全体計算では全職種合計での需要を計算")
    print("3. これらは数学的に異なる概念")
    
    print("\n正しいアプローチの選択肢:")
    print("A. 全体基準: 全体の中央値需要から職種別に按分")
    print("B. 職種基準: 各職種の需要を独立計算（現在の職種別計算）")
    print("C. 混合基準: ビジネスルールに基づく調整")
    
    # 按分方式での計算例
    print("\n=== 按分方式での職種別計算例 ===")
    
    # 職種別の構成比
    role_ratios = {}
    for role in roles:
        role_count = len(working_data[working_data['role'] == role])
        role_ratios[role] = role_count / len(working_data)
        print(f"{role}: {role_ratios[role]:.3f} ({role_count}/{len(working_data)})")
    
    # 全体需要を按分
    adjusted_role_shortage = 0
    print("\n按分による職種別不足時間:")
    for role in roles:
        adjusted_shortage = total_shortage_hours * role_ratios[role]
        adjusted_role_shortage += adjusted_shortage
        print(f"{role}: {adjusted_shortage:.2f}時間")
    
    print(f"按分合計: {adjusted_role_shortage:.2f}時間")
    print(f"全体との差異: {abs(total_shortage_hours - adjusted_role_shortage):.2f}時間")
    
    # 10. 責任ある最終結論
    print("\n【10. 責任ある最終結論】")
    
    print("検証結果:")
    print(f"- 全体不足時間: {total_shortage_hours:.2f}時間")
    print(f"- 職種別独立計算合計: {role_total_shortage:.2f}時間")
    print(f"- 按分による職種別合計: {adjusted_role_shortage:.2f}時間")
    
    if abs(total_shortage_hours - adjusted_role_shortage) < 0.01:
        print("\n✅ 按分方式により一貫性を確保可能")
        recommendation = "按分方式の採用"
    else:
        print("\n⚠️ 数値計算に追加の調査が必要")
        recommendation = "詳細なビジネス要件の確認"
    
    print(f"\n責任ある推奨事項: {recommendation}")
    
    return {
        'total_shortage': total_shortage_hours,
        'role_independent_total': role_total_shortage,
        'role_proportional_total': adjusted_role_shortage,
        'recommendation': recommendation,
        'consistency_achieved': abs(total_shortage_hours - adjusted_role_shortage) < 0.01
    }

if __name__ == "__main__":
    result = deep_responsibility_check()
    print(f"\n深い思考による結論: {result['recommendation']}")