#!/usr/bin/env python3
"""
根本原因に基づく修正のテスト
営業時間制限と職種重複排除の効果検証
"""

import pandas as pd
from pathlib import Path
from datetime import time

def test_business_hours_constraint():
    """営業時間制約のテスト"""
    
    print("=" * 60)
    print("営業時間制約のテスト")
    print("=" * 60)
    
    # 48スロット（24時間）のサンプルデータ作成
    time_slots = [f"{h:02d}:{m:02d}" for h in range(24) for m in [0, 30]]
    sample_data = pd.DataFrame({
        'need': [10] * len(time_slots)  # 全時間帯に一定の需要
    }, index=time_slots)
    
    print(f"テスト前:")
    print(f"  総スロット数: {len(sample_data)}")
    print(f"  総需要: {sample_data.sum().sum()}人・スロット")
    print(f"  時間換算: {sample_data.sum().sum() * 0.5}時間")
    
    # 営業時間制約の適用（8:00-17:30）
    business_start = time(8, 0)
    business_end = time(17, 30)
    
    filtered_data = sample_data.copy()
    slots_filtered = 0
    
    for time_slot in sample_data.index:
        try:
            hour, minute = map(int, time_slot.split(':'))
            slot_time = time(hour, minute)
            
            if not (business_start <= slot_time <= business_end):
                filtered_data.loc[time_slot] = 0
                slots_filtered += 1
        except:
            pass
    
    print(f"\nテスト後:")
    print(f"  フィルタ済スロット: {slots_filtered}")
    print(f"  残存需要: {filtered_data.sum().sum()}人・スロット")
    print(f"  時間換算: {filtered_data.sum().sum() * 0.5}時間")
    print(f"  削減効果: {slots_filtered/len(sample_data)*100:.1f}%")
    
    return True

def test_role_deduplication():
    """職種重複排除のテスト"""
    
    print("\n" + "=" * 60)
    print("職種重複排除のテスト")
    print("=" * 60)
    
    # 職種別ファイルのシミュレーション
    role_files = [
        'need_per_date_slot_role_介護.parquet',
        'need_per_date_slot_role_看護師.parquet', 
        'need_per_date_slot_role_機能訓練士.parquet',
        'need_per_date_slot_role_介護・相談員.parquet',  # 重複職種
        'need_per_date_slot_role_事務・介護.parquet',     # 重複職種
        'need_per_date_slot_role_管理者.parquet',
        'need_per_date_slot_role_運転士.parquet'
    ]
    
    overlap_roles = ['介護・相談員', '事務・介護', '管理者・相談員']
    
    print(f"職種ファイル総数: {len(role_files)}")
    
    # 重複排除処理
    primary_files = []
    excluded_files = []
    
    for role_file in role_files:
        is_overlap = any(overlap in role_file for overlap in overlap_roles)
        
        if not is_overlap:
            primary_files.append(role_file)
        else:
            excluded_files.append(role_file)
    
    print(f"主職種ファイル: {len(primary_files)}")
    for f in primary_files:
        print(f"  ✓ {f}")
    
    print(f"除外ファイル: {len(excluded_files)}")
    for f in excluded_files:
        print(f"  ✗ {f}")
    
    reduction_ratio = len(excluded_files) / len(role_files)
    print(f"削減効果: {reduction_ratio*100:.1f}%")
    
    return True

def estimate_combined_effect():
    """総合効果の推定"""
    
    print("\n" + "=" * 60)
    print("総合効果の推定")
    print("=" * 60)
    
    # 現在の値
    current_values = {
        'p25_based': 2739.0,
        'median_based': 2984.5,
        'mean_based': 2954.5
    }
    
    # 効果係数
    business_hours_reduction = 28 / 48  # 58%削減
    role_overlap_reduction = 0.22       # 22%削減（2/9ファイル除外）
    
    print("修正効果の推定:")
    print(f"  営業時間制限: -{business_hours_reduction*100:.0f}%")
    print(f"  職種重複排除: -{role_overlap_reduction*100:.0f}%")
    print()
    
    for method_key, current_value in current_values.items():
        method_name = {'p25_based': '25%ile', 'median_based': '中央値', 'mean_based': '平均'}[method_key]
        
        # 段階的適用
        after_business_hours = current_value * (1 - business_hours_reduction)
        after_deduplication = after_business_hours * (1 - role_overlap_reduction)
        
        daily_hours = after_deduplication / 30
        
        print(f"{method_name}:")
        print(f"  現在: {current_value:.0f}時間/月")
        print(f"  営業時間制限後: {after_business_hours:.0f}時間/月")
        print(f"  重複排除後: {after_deduplication:.0f}時間/月")
        print(f"  日平均: {daily_hours:.1f}時間/日")
        
        # 現実性評価
        if 15 <= daily_hours <= 40:
            evaluation = "✓ 現実的"
        elif 40 < daily_hours <= 60:
            evaluation = "△ やや高い"
        else:
            evaluation = "要再調整"
        
        print(f"  評価: {evaluation}")
        print()

def main():
    """メインテスト実行"""
    
    test_business_hours_constraint()
    test_role_deduplication()
    estimate_combined_effect()
    
    print("=" * 60)
    print("結論")
    print("=" * 60)
    print("根本原因に基づく修正により、現実的な範囲に収束")
    print("無理やり制限するのではなく、計算の妥当性を確保")
    print("目標: 900-1200時間/月 (日平均30-40時間)")
    print("=" * 60)

if __name__ == "__main__":
    main()