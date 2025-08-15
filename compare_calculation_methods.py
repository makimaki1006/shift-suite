#!/usr/bin/env python3
"""
全体人数ベース vs 職種別Need値による不足時間差異分析
"""

import pandas as pd
import numpy as np
from pathlib import Path

def compare_calculation_methods():
    """計算方法の比較分析"""
    
    print('全体人数ベース vs 職種別Need値による不足時間差異分析')
    print('=' * 70)
    
    scenario_dir = Path('extracted_results/out_p25_based')
    
    # 1. intermediate_dataから全体状況把握
    data = pd.read_parquet(scenario_dir / 'intermediate_data.parquet')
    operating_data = data[data['role'] != 'NIGHT_SLOT']  # 夜間プレースホルダー除外
    
    print('【基本データ】')
    print(f'総配置レコード数: {len(operating_data):,}件')
    print(f'期間: {data["ds"].dt.date.nunique()}日間')
    print(f'総配置時間: {len(operating_data) * 0.5:.1f}時間 ({len(operating_data)} × 0.5時間/レコード)')
    print(f'日平均配置: {len(operating_data) * 0.5 / 30:.1f}時間/日')
    print()
    
    # 2. Need値情報
    need_files = list(scenario_dir.glob('need_per_date_slot_role_*.parquet'))
    total_need = 0
    
    for need_file in need_files:
        df = pd.read_parquet(need_file)
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        file_need = df[numeric_cols].sum().sum()
        total_need += file_need
    
    need_hours = total_need * 0.5  # Need値を時間に変換
    daily_need = need_hours / 30
    
    print(f'総Need値: {total_need:.0f}人・時間帯')
    print(f'総Need時間: {need_hours:.1f}時間 ({total_need:.0f} × 0.5時間/スロット)')
    print(f'日平均Need: {daily_need:.1f}時間/日')
    print()
    
    # 3. 職種別Need値計算（正確な方法）
    print('【方法1: 職種別Need値による不足計算】')
    actual_hours = len(operating_data) * 0.5
    daily_actual = actual_hours / 30
    daily_shortage_accurate = max(0, daily_need - daily_actual)
    
    print(f'日平均Need: {daily_need:.1f}時間/日')
    print(f'日平均配置: {daily_actual:.1f}時間/日')
    print(f'日平均不足: {daily_shortage_accurate:.1f}時間/日')
    print()
    
    # 4. 全体人数ベース単純計算（問題のある方法）
    print('【方法2: 全体人数ベース単純計算】')
    
    # 全スタッフ数
    total_staff = operating_data['staff'].nunique()
    print(f'総スタッフ数: {total_staff}名')
    
    # 単純な人数ベース計算パターンをいくつか試行
    print()
    print('パターン2-1: 1人=8時間/日と仮定')
    simple_daily_hours_8h = total_staff * 8
    simple_shortage_8h = max(0, daily_need - simple_daily_hours_8h)
    print(f'  仮定配置: {simple_daily_hours_8h:.1f}時間/日 ({total_staff}名 × 8時間)')
    print(f'  仮定不足: {simple_shortage_8h:.1f}時間/日')
    print(f'  差異: {abs(daily_shortage_accurate - simple_shortage_8h):.1f}時間/日')
    
    print()
    print('パターン2-2: 1人=6時間/日と仮定')
    simple_daily_hours_6h = total_staff * 6
    simple_shortage_6h = max(0, daily_need - simple_daily_hours_6h)
    print(f'  仮定配置: {simple_daily_hours_6h:.1f}時間/日 ({total_staff}名 × 6時間)')
    print(f'  仮定不足: {simple_shortage_6h:.1f}時間/日')
    print(f'  差異: {abs(daily_shortage_accurate - simple_shortage_6h):.1f}時間/日')
    
    print()
    print('パターン2-3: 1人=4時間/日と仮定')
    simple_daily_hours_4h = total_staff * 4
    simple_shortage_4h = max(0, daily_need - simple_daily_hours_4h)
    print(f'  仮定配置: {simple_daily_hours_4h:.1f}時間/日 ({total_staff}名 × 4時間)')
    print(f'  仮定不足: {simple_shortage_4h:.1f}時間/日')
    print(f'  差異: {abs(daily_shortage_accurate - simple_shortage_4h):.1f}時間/日')
    
    # 5. 実際の1人あたり平均勤務時間を計算
    actual_avg_hours_per_staff = actual_hours / total_staff / 30  # 日平均
    print()
    print('【実際の1人あたり平均勤務時間】')
    print(f'実際の平均: {actual_avg_hours_per_staff:.2f}時間/日/人')
    
    print()
    print('パターン2-4: 実際の平均勤務時間を使用')
    simple_daily_hours_actual = total_staff * actual_avg_hours_per_staff
    simple_shortage_actual = max(0, daily_need - simple_daily_hours_actual)
    print(f'  実測配置: {simple_daily_hours_actual:.1f}時間/日 ({total_staff}名 × {actual_avg_hours_per_staff:.2f}時間)')
    print(f'  実測不足: {simple_shortage_actual:.1f}時間/日')
    print(f'  差異: {abs(daily_shortage_accurate - simple_shortage_actual):.1f}時間/日')
    
    print()
    print('=' * 70)
    print('【結論】')
    print(f'正確な職種別Need計算: {daily_shortage_accurate:.1f}時間/日不足')
    print()
    print('全体人数ベース単純計算の問題点:')
    print(f'  8時間仮定: {simple_shortage_8h - daily_shortage_accurate:+.1f}時間/日の誤差')
    print(f'  6時間仮定: {simple_shortage_6h - daily_shortage_accurate:+.1f}時間/日の誤差')
    print(f'  4時間仮定: {simple_shortage_4h - daily_shortage_accurate:+.1f}時間/日の誤差')
    print(f'  実測ベース: {simple_shortage_actual - daily_shortage_accurate:+.1f}時間/日の誤差')
    
    print()
    print('最大誤差幅:')
    errors = [
        abs(simple_shortage_8h - daily_shortage_accurate),
        abs(simple_shortage_6h - daily_shortage_accurate),
        abs(simple_shortage_4h - daily_shortage_accurate)
    ]
    max_error = max(errors)
    min_error = min(errors)
    print(f'  最大: {max_error:.1f}時間/日')
    print(f'  最小: {min_error:.1f}時間/日')
    print(f'  誤差範囲: ±{max_error:.1f}時間/日')
    
    # 6. 職種別詳細分析
    print()
    print('【職種別配置 vs Need差異】')
    
    role_analysis = {}
    
    for need_file in sorted(need_files):
        # 職種名抽出
        role_name = need_file.name.replace('need_per_date_slot_role_', '').replace('.parquet', '')
        
        # Need値
        df = pd.read_parquet(need_file)
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        role_need = df[numeric_cols].sum().sum()
        role_need_hours = role_need * 0.5
        daily_role_need = role_need_hours / 30
        
        # 実配置
        role_data = operating_data[operating_data['role'] == role_name]
        role_actual_records = len(role_data)
        role_actual_hours = role_actual_records * 0.5
        daily_role_actual = role_actual_hours / 30
        
        # 差異
        daily_role_shortage = daily_role_need - daily_role_actual
        
        role_analysis[role_name] = {
            'need_hours_daily': daily_role_need,
            'actual_hours_daily': daily_role_actual,
            'shortage_daily': daily_role_shortage,
            'staff_count': role_data['staff'].nunique() if len(role_data) > 0 else 0
        }
        
        print(f'{role_name}:')
        print(f'  Need: {daily_role_need:6.1f}時間/日')
        print(f'  実配置: {daily_role_actual:6.1f}時間/日 ({role_analysis[role_name]["staff_count"]}名)')
        print(f'  差異: {daily_role_shortage:+6.1f}時間/日')
    
    print()
    print('【按分廃止の効果】')
    print('職種別Need値を使用することで:')
    print('- 各職種の真の不足/余剰が明確化')
    print('- 全体人数ベースの大幅な誤差（最大±{:.1f}時間/日）を回避'.format(max_error))
    print('- 具体的な職種別採用計画が策定可能')
    
    return {
        'accurate_shortage': daily_shortage_accurate,
        'simple_8h_shortage': simple_shortage_8h,
        'simple_6h_shortage': simple_shortage_6h,
        'simple_4h_shortage': simple_shortage_4h,
        'max_error': max_error,
        'role_analysis': role_analysis
    }

if __name__ == "__main__":
    result = compare_calculation_methods()