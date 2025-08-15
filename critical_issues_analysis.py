#!/usr/bin/env python3
"""
Phase 2実装の重要問題詳細分析
客観的レビューで検出された問題点の詳細調査
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analyze_critical_issues():
    """重要問題の詳細分析"""
    
    print("=" * 80)
    print("重要問題詳細分析")
    print("=" * 80)
    
    scenario_dir = Path("extracted_results/out_p25_based")
    
    # 問題1: データ重複の詳細検証
    print("\n【問題1: データ重複の詳細検証】")
    
    need_files = list(scenario_dir.glob("need_per_date_slot_role_*介護*.parquet"))
    print(f"介護関連需要ファイル数: {len(need_files)}")
    
    file_analysis = {}
    for need_file in need_files:
        df = pd.read_parquet(need_file)
        file_sum = df.select_dtypes(include=[np.number]).sum().sum()
        file_analysis[need_file.name] = {
            'sum': file_sum,
            'shape': df.shape,
            'hash': hash(str(df.values.tolist()))  # データ内容のハッシュ
        }
        print(f"  {need_file.name}: 合計={file_sum}, 形状={df.shape}")
    
    # 重複検出
    duplicates = {}
    for file1, data1 in file_analysis.items():
        for file2, data2 in file_analysis.items():
            if file1 != file2 and data1['hash'] == data2['hash']:
                if file1 not in duplicates:
                    duplicates[file1] = []
                duplicates[file1].append(file2)
    
    if duplicates:
        print("\n★重要問題★ データ重複が検出されました:")
        for original, dups in duplicates.items():
            print(f"  {original} と重複: {dups}")
        
        # 重複による過大計算の推定
        total_without_duplicates = sum(set(data['sum'] for data in file_analysis.values()))
        total_with_duplicates = sum(data['sum'] for data in file_analysis.values())
        overestimation = total_with_duplicates - total_without_duplicates
        
        print(f"\n重複による過大計算:")
        print(f"  重複込み合計: {total_with_duplicates}")
        print(f"  重複除外合計: {total_without_duplicates}")
        print(f"  過大計算量: {overestimation}")
        print(f"  過大率: {(overestimation / total_without_duplicates * 100):.1f}%")
        
        return {
            'duplicate_overestimation': overestimation,
            'correct_total': total_without_duplicates,
            'incorrect_total': total_with_duplicates
        }
    else:
        print("データ重複は検出されませんでした")
        return None

def analyze_staff_calculation_accuracy():
    """配置時間計算精度の詳細分析"""
    
    print("\n【問題2: 配置時間計算精度の詳細分析】")
    
    scenario_dir = Path("extracted_results/out_p25_based")
    intermediate_data = pd.read_parquet(scenario_dir / "intermediate_data.parquet")
    
    print(f"intermediate_data総レコード数: {len(intermediate_data)}")
    print(f"データ期間: {intermediate_data['ds'].min()} ～ {intermediate_data['ds'].max()}")
    
    # 介護関連職種の詳細分析
    care_roles = ['介護（W/2）', '介護（W/3）', '介護', '介護・相談員', '事務・介護']
    
    for role in care_roles:
        role_data = intermediate_data[intermediate_data['role'] == role]
        print(f"\n{role}:")
        print(f"  レコード数: {len(role_data)}")
        
        if len(role_data) > 0:
            # 日別分布
            daily_counts = role_data.groupby('ds').size()
            print(f"  日別平均: {daily_counts.mean():.1f} スロット/日")
            print(f"  日別最大: {daily_counts.max()} スロット/日")
            print(f"  日別最小: {daily_counts.min()} スロット/日")
            
            # 時間帯別分布（可能であれば）
            if 'time_slot' in role_data.columns:
                hourly_dist = role_data.groupby('time_slot').size()
                print(f"  ピーク時間帯: {hourly_dist.idxmax()} ({hourly_dist.max()}スロット)")
    
    # 合計配置時間の検証
    total_care_slots = len(intermediate_data[intermediate_data['role'].str.contains('介護', na=False)])
    total_care_hours = total_care_slots * 0.5
    
    print(f"\n配置時間計算検証:")
    print(f"  介護関連スロット数: {total_care_slots}")
    print(f"  計算配置時間: {total_care_hours}時間")
    print(f"  1日平均配置時間: {total_care_hours / 30:.1f}時間/日")  # 30日間
    
    # 妥当性チェック
    reasonable_hours_per_day = total_care_slots / 48 / 30  # 48スロット/日、30日間
    print(f"  日別標準稼働時間: {reasonable_hours_per_day * 24:.1f}時間/日")
    
    return {
        'total_care_slots': total_care_slots,
        'total_care_hours': total_care_hours,
        'daily_average': total_care_hours / 30
    }

def final_recommendation():
    """最終推奨事項"""
    
    print("\n【最終推奨事項】")
    
    duplicate_analysis = analyze_critical_issues()
    staff_analysis = analyze_staff_calculation_accuracy()
    
    if duplicate_analysis:
        print("\n★緊急修正が必要★")
        print("1. データ重複問題の即座修正")
        print("   - 重複ファイルの除外または統合")
        print("   - 需要計算ロジックの見直し")
        print(f"   - 過大計算量: {duplicate_analysis['overestimation']:.1f}時間を修正")
        
        print("\n2. 修正後の期待結果:")
        print(f"   - 正しい需要合計: {duplicate_analysis['correct_total']:.1f}時間")
        print(f"   - 配置時間: {staff_analysis['total_care_hours']:.1f}時間")
        expected_shortage = max(0, duplicate_analysis['correct_total'] - staff_analysis['total_care_hours'])
        print(f"   - 修正後不足: {expected_shortage:.1f}時間")
        
        return False  # 修正が必要
    
    else:
        print("重大な問題は検出されませんでした")
        print("現在の実装は基本的に妥当です")
        return True  # 問題なし

if __name__ == "__main__":
    is_valid = final_recommendation()
    if not is_valid:
        print("\n" + "=" * 80)
        print("結論: Phase 2実装には修正が必要")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)  
        print("結論: Phase 2実装は妥当")
        print("=" * 80)