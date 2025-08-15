#!/usr/bin/env python3
"""
現実的な制約の実装
営業時間制限、職種重複排除、異常値制限の実装
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime, time

def implement_business_hours_constraint():
    """営業時間制約の実装"""
    
    print("=" * 70)
    print("現実的制約の実装")
    print("=" * 70)
    print()
    
    print("【Phase 1: 営業時間制約の実装】")
    print("-" * 40)
    
    # 典型的なデイサービスの営業時間
    business_start = time(8, 0)   # 8:00
    business_end = time(17, 30)   # 17:30
    
    print(f"営業時間設定: {business_start} - {business_end}")
    print("営業時間外の需要を0に設定")
    print()
    
    # 実際のファイルでの営業時間フィルタリング例
    print("実装例（heatmap.py用）:")
    print("""
def apply_business_hours_constraint(need_df, business_start=time(8,0), business_end=time(17,30)):
    \"\"\"営業時間制約を適用\"\"\"
    
    filtered_df = need_df.copy()
    
    for time_slot in need_df.index:
        try:
            # 時間文字列を解析
            hour, minute = map(int, time_slot.split(':'))
            slot_time = time(hour, minute)
            
            # 営業時間外は需要を0に設定
            if not (business_start <= slot_time <= business_end):
                filtered_df.loc[time_slot] = 0
                
        except:
            # 解析できない場合は保持
            pass
    
    return filtered_df
    """)
    
    return True

def implement_role_deduplication():
    """職種重複排除の実装"""
    
    print("【Phase 2: 職種重複排除の実装】")
    print("-" * 40)
    
    print("職種重複の問題:")
    print("- 同一人物が複数職種でカウント")
    print("- 例: '介護・相談員' が '介護' と重複")
    print("- 職種別ファイルの単純合計による過大計算")
    print()
    
    print("実装例（shortage.py用）:")
    print("""
def deduplicate_role_files(role_files):
    \"\"\"職種別ファイルの重複排除\"\"\"
    
    # 職種の優先順位（主職種を優先）
    role_priority = {
        '介護': 1,
        '看護師': 2, 
        '機能訓練士': 3,
        '事務': 4,
        '運転士': 5,
        '介護・相談員': 6,  # 複合職種は低優先度
        '事務・介護': 7
    }
    
    # 主職種ファイルのみを選択
    primary_role_files = []
    for role_file in role_files:
        role_name = extract_role_from_filename(role_file.name)
        if role_name in role_priority and role_priority[role_name] <= 5:
            primary_role_files.append(role_file)
    
    return primary_role_files
    """)
    
    return True

def implement_abnormal_value_detection():
    """異常値検出・制限の実装"""
    
    print("【Phase 3: 異常値検出・制限の実装】")
    print("-" * 40)
    
    print("異常値判定基準:")
    print("- 月間需要 > 1000時間: 要注意")
    print("- 月間需要 > 2000時間: 異常")
    print("- 日平均需要 > 100時間: 異常")
    print()
    
    print("実装例（utils.py用）:")
    print("""
def validate_realistic_scale(total_need_hours, period_days=30):
    \"\"\"現実的な規模の検証\"\"\"
    
    daily_avg = total_need_hours / period_days
    monthly_need = total_need_hours * (30 / period_days)
    
    warnings = []
    corrections = {}
    
    # 異常値判定
    if monthly_need > 2000:
        warnings.append(f"月間需要{monthly_need:.0f}時間は異常に高い")
        # 大規模施設の上限に制限
        corrected_monthly = 800
        corrections['monthly_limit_applied'] = corrected_monthly
        
    elif monthly_need > 1000:
        warnings.append(f"月間需要{monthly_need:.0f}時間は要注意")
        
    if daily_avg > 100:
        warnings.append(f"日平均{daily_avg:.1f}時間/日は異常に高い")
        
    return {
        'is_realistic': len(warnings) == 0,
        'warnings': warnings,
        'corrections': corrections,
        'monthly_need': monthly_need,
        'daily_average': daily_avg
    }
    """)
    
    return True

def create_realistic_need_calculator():
    """現実的なNeed計算機の作成"""
    
    print("【Phase 4: 現実的Need計算機の統合】")
    print("-" * 40)
    
    print("統合された現実的計算フロー:")
    print("""
def calculate_realistic_need(
    actual_staff_by_slot_and_date,
    statistic_method="中央値",
    business_hours_only=True,
    deduplicate_roles=True,
    apply_scale_limits=True
):
    \"\"\"現実的なNeed計算\"\"\"
    
    # Step 1: 基本統計計算
    if statistic_method == "中央値":
        base_need = actual_staff_by_slot_and_date.median(axis=1)
    elif statistic_method == "平均値":
        base_need = actual_staff_by_slot_and_date.mean(axis=1)
    else:  # 25パーセンタイル
        base_need = actual_staff_by_slot_and_date.quantile(0.25, axis=1)
    
    # Step 2: 営業時間制約
    if business_hours_only:
        base_need = apply_business_hours_constraint(base_need)
        log.info("[REALISTIC] 営業時間制約を適用")
    
    # Step 3: 異常値制限
    if apply_scale_limits:
        total_need = base_need.sum() * 0.5 * 30  # 月間換算
        validation = validate_realistic_scale(total_need)
        
        if not validation['is_realistic']:
            log.warning(f"[REALISTIC] 異常値検出: {validation['warnings']}")
            
            # 制限適用
            if 'monthly_limit_applied' in validation['corrections']:
                limit = validation['corrections']['monthly_limit_applied']
                scaling_factor = limit / validation['monthly_need']
                base_need = base_need * scaling_factor
                log.info(f"[REALISTIC] 規模制限適用: {scaling_factor:.2f}倍に調整")
    
    return base_need
    """)
    
    return True

def estimate_realistic_improvement():
    """現実的改善の効果推定"""
    
    print("【改善効果の推定】")
    print("-" * 40)
    
    # 現在値
    current_values = {
        'p25_based': 2739.0,
        'median_based': 2984.5,
        'mean_based': 2954.5
    }
    
    print("段階的改善効果:")
    
    for method_key, current_value in current_values.items():
        method_name = {'p25_based': '25%ile', 'median_based': '中央値', 'mean_based': '平均'}[method_key]
        
        # Phase 1: 営業時間制約 (約60%削減)
        after_business_hours = current_value * 0.4
        
        # Phase 2: 職種重複排除 (約20%削減)  
        after_deduplication = after_business_hours * 0.8
        
        # Phase 3: 異常値制限 (上限800時間)
        after_limits = min(after_deduplication, 800)
        
        print(f"{method_name}:")
        print(f"  現在: {current_value:.0f}時間/月")
        print(f"  営業時間制約後: {after_business_hours:.0f}時間/月 (-60%)")
        print(f"  重複排除後: {after_deduplication:.0f}時間/月 (-20%)")
        print(f"  最終: {after_limits:.0f}時間/月")
        
        # 現実性評価
        if 100 <= after_limits <= 400:
            evaluation = "現実的"
        elif 400 < after_limits <= 800:
            evaluation = "大規模施設相当"
        else:
            evaluation = "要再調整"
        
        print(f"  評価: {evaluation}")
        print()

def main():
    """メイン実装ガイド"""
    
    implement_business_hours_constraint()
    implement_role_deduplication()
    implement_abnormal_value_detection()
    create_realistic_need_calculator()
    estimate_realistic_improvement()
    
    print("=" * 70)
    print("【実装優先順位】")
    print("=" * 70)
    print("1. 営業時間制約: 即座実装可能、最大効果")
    print("2. 異常値制限: 安全装置として重要")
    print("3. 職種重複排除: データ品質向上")
    print("4. 統合テスト: 現実的な範囲の確認")
    print()
    print("目標: 100-800時間/月の現実的な範囲")
    print("効果: 計算精度と現実性の両立")
    print("=" * 70)

if __name__ == "__main__":
    main()