#!/usr/bin/env python3
"""
23.6時間/日 → 0.0時間/日修正の客観的検証
ユーザー指摘: 「静的に処理していないか不安」

客観的かつネガティブなレビューによる計算ロジック検証
"""

import pandas as pd
from pathlib import Path
import numpy as np

def critical_logic_verification():
    """計算ロジックの客観的・批判的検証"""
    
    print('=' * 80)
    print('23.6時間/日 → 0.0時間/日 修正ロジックの客観的検証')
    print('目的: 静的処理・ロジックエラーの可能性を徹底調査')
    print('=' * 80)
    
    scenario_dir = Path('extracted_results/out_p25_based')
    
    # === 1. 生データの直接確認 ===
    print('\n【1. 生データの直接確認】')
    
    # 需要データの詳細分析
    need_files = list(scenario_dir.glob('need_per_date_slot_role_*介護*.parquet'))
    print(f'需要ファイル数: {len(need_files)}')
    
    total_need_raw = 0
    need_details = {}
    
    for need_file in need_files:
        df = pd.read_parquet(need_file)
        
        # 各セルの値を詳細確認
        print(f'\n{need_file.name}:')
        print(f'  形状: {df.shape}')
        print(f'  データ型: {df.dtypes.iloc[0]}')
        
        # セルの実際の値をサンプル表示
        print(f'  セルサンプル(左上5x5):')
        print(f'  {df.iloc[:5, :5].values}')
        
        # 統計
        file_sum = df.sum().sum()
        max_val = df.max().max()
        min_val = df.min().min()
        non_zero = (df > 0).sum().sum()
        
        print(f'  ファイル合計: {file_sum}')
        print(f'  最大値: {max_val}')
        print(f'  最小値: {min_val}')
        print(f'  非ゼロセル数: {non_zero}/{df.size} ({non_zero/df.size*100:.1f}%)')
        
        total_need_raw += file_sum
        need_details[need_file.name] = {
            'sum': file_sum,
            'max': max_val,
            'min': min_val,
            'shape': df.shape,
            'non_zero_rate': non_zero/df.size
        }
    
    print(f'\n需要データ合計: {total_need_raw}')
    
    # === 2. 配置データの詳細確認 ===
    print(f'\n【2. 配置データの詳細確認】')
    
    intermediate_data = pd.read_parquet(scenario_dir / 'intermediate_data.parquet')
    care_data = intermediate_data[intermediate_data['role'].str.contains('介護', na=False)]
    
    print(f'intermediate_data:')
    print(f'  総レコード数: {len(intermediate_data)}')
    print(f'  介護レコード数: {len(care_data)}')
    print(f'  期間: {intermediate_data["ds"].min()} ～ {intermediate_data["ds"].max()}')
    print(f'  実日数: {intermediate_data["ds"].dt.date.nunique()}日')
    
    # 1日あたりのレコード分布
    daily_care_counts = care_data.groupby(care_data['ds'].dt.date).size()
    print(f'\n1日あたり介護レコード統計:')
    print(f'  平均: {daily_care_counts.mean():.1f}レコード/日')
    print(f'  最大: {daily_care_counts.max()}レコード/日')
    print(f'  最小: {daily_care_counts.min()}レコード/日')
    print(f'  標準偏差: {daily_care_counts.std():.1f}')
    print(f'  分布: {daily_care_counts.describe()}')
    
    # === 3. 計算ステップの詳細追跡 ===
    print(f'\n【3. 計算ステップの詳細追跡】')
    
    # Step 1: 需要計算
    print(f'Step 1 - 需要計算:')
    need_people_timeslots = total_need_raw
    need_hours_conversion = need_people_timeslots * 0.5
    daily_need_hours = need_hours_conversion / 30
    
    print(f'  需要(人・時間帯): {need_people_timeslots}')
    print(f'  需要(時間換算): {need_hours_conversion} = {need_people_timeslots} × 0.5')
    print(f'  1日需要: {daily_need_hours:.1f} = {need_hours_conversion} ÷ 30')
    
    # Step 2: 配置計算
    print(f'\nStep 2 - 配置計算:')
    staff_records = len(care_data)
    staff_hours_conversion = staff_records * 0.5
    daily_staff_hours = staff_hours_conversion / 30
    
    print(f'  配置(レコード数): {staff_records}')
    print(f'  配置(時間換算): {staff_hours_conversion} = {staff_records} × 0.5')
    print(f'  1日配置: {daily_staff_hours:.1f} = {staff_hours_conversion} ÷ 30')
    
    # Step 3: 不足計算
    print(f'\nStep 3 - 不足計算:')
    raw_shortage = daily_need_hours - daily_staff_hours
    final_shortage = max(0, raw_shortage)
    
    print(f'  生の差分: {raw_shortage:.1f} = {daily_need_hours:.1f} - {daily_staff_hours:.1f}')
    print(f'  最終不足: {final_shortage:.1f} = max(0, {raw_shortage:.1f})')
    
    # === 4. 潜在的問題の特定 ===
    print(f'\n【4. 潜在的問題の特定（批判的視点）】')
    
    problems_found = []
    
    # 問題1: max(0, x)による静的な0化
    if raw_shortage < 0:
        problems_found.append(f'max(0, x)により負の不足({raw_shortage:.1f})が0に強制変換された')
        print(f'[ERROR] 問題1: max(0, x)による静的処理')
        print(f'   実際には配置過多({abs(raw_shortage):.1f}時間/日)だが0として表示')
    
    # 問題2: 配置データの解釈疑問
    if daily_staff_hours > daily_need_hours:
        excess_ratio = (daily_staff_hours - daily_need_hours) / daily_need_hours * 100
        problems_found.append(f'配置が需要を{excess_ratio:.1f}%上回る - 過剰配置の疑い')
        print(f'[ERROR] 問題2: 過剰配置の疑い')
        print(f'   配置{daily_staff_hours:.1f}時間 vs 需要{daily_need_hours:.1f}時間')
    
    # 問題3: 単位換算の妥当性
    time_per_record = 0.5
    print(f'[WARNING] 問題3: 単位換算の妥当性検証')
    print(f'   1レコード = {time_per_record}時間の根拠は？')
    print(f'   30分スロット前提だが、実際の勤務時間と一致するか？')
    
    # 問題4: 期間設定の妥当性
    period_days = 30
    actual_days = intermediate_data['ds'].dt.date.nunique()
    if period_days != actual_days:
        problems_found.append(f'期間設定不一致: 計算{period_days}日 vs 実データ{actual_days}日')
        print(f'[ERROR] 問題4: 期間設定の不一致')
        print(f'   計算で30日使用、実データは{actual_days}日')
    
    # === 5. 代替計算による検証 ===
    print(f'\n【5. 代替計算による検証】')
    
    # 代替案1: 実期間での計算
    alt1_daily_need = need_hours_conversion / actual_days
    alt1_daily_staff = staff_hours_conversion / actual_days
    alt1_shortage = max(0, alt1_daily_need - alt1_daily_staff)
    
    print(f'代替案1（実期間{actual_days}日）:')
    print(f'  1日需要: {alt1_daily_need:.1f}時間')
    print(f'  1日配置: {alt1_daily_staff:.1f}時間')
    print(f'  1日不足: {alt1_shortage:.1f}時間')
    
    # 代替案2: レコードあたり時間を変更
    alt_time_per_record = 1.0  # 1時間と仮定
    alt2_staff_hours = staff_records * alt_time_per_record / 30
    alt2_shortage = max(0, daily_need_hours - alt2_staff_hours)
    
    print(f'\n代替案2（1レコード=1時間）:')
    print(f'  1日配置: {alt2_staff_hours:.1f}時間')
    print(f'  1日不足: {alt2_shortage:.1f}時間')
    
    # === 6. 結論と推奨 ===
    print(f'\n【6. 結論と推奨修正】')
    
    if len(problems_found) > 0:
        print(f'[WARNING] 発見された問題: {len(problems_found)}件')
        for i, problem in enumerate(problems_found, 1):
            print(f'   {i}. {problem}')
    
    print(f'\n推奨修正:')
    print(f'1. max(0, x)による静的処理を廃止し、負の値も適切に表示')
    print(f'2. 実際の期間({actual_days}日)を使用した計算')
    print(f'3. 1レコードあたりの時間換算根拠の明確化')
    print(f'4. 配置過多の場合の適切な表示方法')
    
    return {
        'raw_shortage': raw_shortage,
        'final_shortage': final_shortage,
        'is_static_processing': raw_shortage < 0,
        'problems_count': len(problems_found),
        'problems': problems_found,
        'actual_period_days': actual_days,
        'calculated_period_days': 30
    }

if __name__ == "__main__":
    result = critical_logic_verification()
    
    print('\n' + '=' * 80)
    if result['is_static_processing']:
        print('結論: 静的処理により0.0時間が生成された疑いあり')
        print('実際には配置過多の可能性が高い')
    else:
        print('結論: 真の不足として0.0時間が算出された')
    
    print(f'発見された問題: {result["problems_count"]}件')
    print('=' * 80)