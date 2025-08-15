#!/usr/bin/env python3
"""
問題2: 補正パラメータの恣意性解決 - 期間制御閾値の統計的根拠分析
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import matplotlib.pyplot as plt

def analyze_correction_parameters():
    """期間制御閾値の恣意性問題を詳細分析"""
    
    print("=" * 80)
    print("問題2: 補正パラメータの恣意性解決 - 期間制御閾値分析")
    print("=" * 80)
    
    # 1. 現在の期間制御閾値を分析
    print("\n【STEP 1: 現在の期間制御閾値分析】")
    
    current_thresholds = {
        "超長期 (180日+)": {"threshold": 2.0, "description": "非常に厳格"},
        "中長期 (90-180日)": {"threshold": 3.0, "description": "厳格"}, 
        "中期 (60-90日)": {"threshold": 4.0, "description": "やや厳格"},
        "短期 (-60日)": {"threshold": 5.0, "description": "標準"}
    }
    
    print("現在の期間制御閾値:")
    for period, params in current_thresholds.items():
        print(f"  {period}: {params['threshold']}h/日 ({params['description']})")
    
    # 2. 実データで閾値の妥当性を検証
    print("\n【STEP 2: 実データでの閾値妥当性検証】")
    
    # shortage_time.parquetがあるか確認
    shortage_files = list(Path("extracted_results").rglob("shortage_time.parquet"))
    
    if shortage_files:
        for shortage_file in shortage_files[:3]:  # 最大3ファイル分析
            try:
                print(f"\n分析対象: {shortage_file}")
                shortage_df = pd.read_parquet(shortage_file)
                
                # 期間日数計算
                period_days = len(shortage_df.columns)
                print(f"分析期間: {period_days}日")
                
                # 1日あたり平均不足時間計算（スロット時間=0.5h想定）
                slot_hours = 0.5
                daily_shortage_slots = shortage_df.sum()  # 日別不足スロット数
                daily_shortage_hours = daily_shortage_slots * slot_hours
                
                print(f"日別不足時間統計:")
                print(f"  平均: {daily_shortage_hours.mean():.2f}h/日")
                print(f"  中央値: {daily_shortage_hours.median():.2f}h/日") 
                print(f"  最大: {daily_shortage_hours.max():.2f}h/日")
                print(f"  最小: {daily_shortage_hours.min():.2f}h/日")
                print(f"  標準偏差: {daily_shortage_hours.std():.2f}h")
                
                # 現在の閾値との比較
                if period_days > 180:
                    current_threshold = 2.0
                elif period_days > 90:
                    current_threshold = 3.0
                elif period_days > 60:
                    current_threshold = 4.0
                else:
                    current_threshold = 5.0
                
                avg_daily = daily_shortage_hours.mean()
                print(f"\n閾値適用結果:")
                print(f"  現在の閾値: {current_threshold}h/日")
                print(f"  実際の平均: {avg_daily:.2f}h/日")
                
                if avg_daily > current_threshold:
                    reduction_factor = current_threshold / avg_daily
                    print(f"  制御適用: YES (削減率 {(1-reduction_factor)*100:.1f}%)")
                    print(f"  制御後平均: {current_threshold:.2f}h/日")
                else:
                    print(f"  制御適用: NO")
                
                # パーセンタイル分析
                print(f"\n日別不足時間分布:")
                percentiles = [10, 25, 50, 75, 90, 95, 99]
                for p in percentiles:
                    value = np.percentile(daily_shortage_hours, p)
                    print(f"  {p}%ile: {value:.2f}h/日")
                    
            except Exception as e:
                print(f"  分析エラー: {e}")
    else:
        print("shortage_time.parquet ファイルが見つかりません")
    
    # 3. 統計的根拠の問題点特定
    print("\n【STEP 3: 期間制御閾値の問題点分析】")
    
    problems = [
        "NG 恣意性A: 閾値設定に科学的根拠なし",
        "   - 2.0h, 3.0h, 4.0h, 5.0h という値の設定理由が不明",
        "   - 業界標準や法定基準との関連性なし",
        "",
        "NG 恣意性B: 期間区分の根拠不足",
        "   - 60日、90日、180日という区切りの科学的根拠なし", 
        "   - なぜこの3つの期間で区切るのか不明",
        "",
        "NG 恣意性C: 統計的検証の欠如",
        "   - 閾値が実データ分布と整合するか未検証",
        "   - 異なる期間での一貫性未確認",
        "",
        "NG 恣意性D: 業務実態との乖離リスク",
        "   - 実際の業務に必要な人員を過度に削減する可能性",
        "   - 安全・品質基準を下回るリスク",
        "",
        "NG 恣意性E: 動的調整機能の欠如",
        "   - 実績データに基づく閾値の自動調整なし",
        "   - 季節変動・特殊事情への対応なし"
    ]
    
    for problem in problems:
        print(problem)
    
    # 4. 統計的根拠に基づく改善提案
    print("\n【STEP 4: 統計的根拠に基づく改善提案】")
    
    improvements = [
        "OK 改善A: データ駆動型閾値設定",
        "   - 実データの分布分析（平均±2σ、95%ile等）に基づく閾値",
        "   - 業界ベンチマークとの比較による妥当性確認",
        "",
        "OK 改善B: 適応的期間区分", 
        "   - データ量・変動性に基づく動的期間区分",
        "   - 統計的有意性を考慮した期間設定",
        "",
        "OK 改善C: 多段階制御システム",
        "   - 警告レベル（90%ile）と緊急制御レベル（99%ile）の2段階",
        "   - グラデーション制御（段階的削減）",
        "",
        "OK 改善D: リスク評価連動型制御",
        "   - 安全性・品質指標との連動",
        "   - ビジネスリスク評価に基づく制御レベル調整",
        "",
        "OK 改善E: 学習型閾値システム",
        "   - 実績フィードバックによる自動学習",
        "   - 機械学習による最適閾値予測"
    ]
    
    for improvement in improvements:
        print(improvement)
    
    # 5. 具体的実装案
    print("\n【STEP 5: 統計的閾値設定の具体案】")
    
    implementation_proposals = [
        "1. パーセンタイル基準閾値:",
        "   - 短期（30日未満）: 95%ile",
        "   - 中期（30-90日）: 90%ile", 
        "   - 長期（90日+）: 75%ile",
        "",
        "2. 業界標準連動閾値:",
        "   - 介護保険法人員配置基準 × 余裕率1.2-1.5",
        "   - 地域平均 ± 標準偏差範囲内",
        "",
        "3. 信頼区間基準閾値:",
        "   - 平均 + 95%信頼区間上限",
        "   - ベイズ統計による不確実性考慮",
        "",
        "4. 機械学習予測閾値:",
        "   - 過去データからの予測モデル",
        "   - リアルタイム調整機能"
    ]
    
    for proposal in implementation_proposals:
        print(proposal)
    
    print("\n" + "=" * 80)
    print("分析完了: 問題2 - 補正パラメータの恣意性解決")
    print("次段階: 統計的根拠に基づく閾値設定システム実装")
    print("=" * 80)

if __name__ == "__main__":
    analyze_correction_parameters()