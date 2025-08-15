#!/usr/bin/env python3
"""
真実の不足計算修正版
max(0, x)による静的処理を廃止し、配置過多も正しく表示する
"""

import pandas as pd
from pathlib import Path

def calculate_true_shortage():
    """配置過多も含む真実の不足計算"""
    
    print('=' * 80)
    print('真実の不足計算修正版')
    print('静的処理を廃止し、配置過多も正確に表示')
    print('=' * 80)
    
    scenario_dir = Path('extracted_results/out_p25_based')
    
    # データ読み込み
    intermediate_data = pd.read_parquet(scenario_dir / 'intermediate_data.parquet')
    care_data = intermediate_data[intermediate_data['role'].str.contains('介護', na=False)]
    
    need_files = list(scenario_dir.glob('need_per_date_slot_role_*介護*.parquet'))
    
    total_need = 0
    for need_file in need_files:
        df = pd.read_parquet(need_file)
        total_need += df.sum().sum()
    
    print(f'\n=== 真実の計算（静的処理なし） ===')
    
    # 単位変換
    need_hours = total_need * 0.5  # 人数→時間
    staff_hours = len(care_data) * 0.5  # レコード→時間
    
    # 30日基準
    daily_need = need_hours / 30
    daily_staff = staff_hours / 30
    
    # 真の差分（静的処理なし）
    true_difference = daily_need - daily_staff
    
    print(f'1日需要: {daily_need:.1f}時間/日')
    print(f'1日配置: {daily_staff:.1f}時間/日')
    print(f'真の差分: {true_difference:.1f}時間/日')
    
    if true_difference > 0:
        print(f'状況: 不足 {true_difference:.1f}時間/日')
        impact = '人員不足により運営に支障'
    elif true_difference < 0:
        print(f'状況: 配置過多 {abs(true_difference):.1f}時間/日')
        impact = '人員過多による運営効率低下'
    else:
        print(f'状況: 完全均衡')
        impact = '理想的な人員配置'
    
    print(f'運営への影響: {impact}')
    
    print(f'\n=== 従来の静的処理との比較 ===')
    static_result = max(0, true_difference)
    print(f'静的処理結果: {static_result:.1f}時間/日')
    print(f'真実の結果: {true_difference:.1f}時間/日')
    
    if true_difference < 0:
        hidden_truth = abs(true_difference)
        print(f'隠蔽された真実: {hidden_truth:.1f}時間/日の配置過多')
        print(f'情報損失: 運営改善の機会を逸失')
    
    print(f'\n=== 改善提案 ===')
    if true_difference < 0:
        excess_hours = abs(true_difference)
        print(f'1. 過剰配置{excess_hours:.1f}時間/日の有効活用検討')
        print(f'2. 他部署への人員移動可能性調査')
        print(f'3. 研修・スキルアップ時間への転用')
        print(f'4. 将来の需要増加に備えた余力として位置づけ')
    elif true_difference > 0:
        shortage_hours = true_difference
        print(f'1. {shortage_hours:.1f}時間/日の人員不足への対策が必要')
        print(f'2. 採用計画の見直し')
        print(f'3. 勤務時間の調整検討')
    else:
        print(f'1. 現在の人員配置は適正')
        print(f'2. この均衡状態の維持が重要')
    
    return {
        'true_difference': true_difference,
        'daily_need': daily_need,
        'daily_staff': daily_staff,
        'static_result': static_result,
        'information_loss': true_difference != static_result
    }

if __name__ == "__main__":
    result = calculate_true_shortage()
    
    print('\n' + '=' * 80)
    if result['information_loss']:
        print('結論: 静的処理により重要な情報が隠蔽されていた')
        print('修正により運営改善の機会を正確に把握可能')
    else:
        print('結論: 静的処理の影響なし')
    print('=' * 80)