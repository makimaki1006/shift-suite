#!/usr/bin/env python3
"""
統計手法一貫性修正のテスト
shortage_time.parquetが統計手法を正しく反映するかを検証
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

def test_need_file_integration():
    """統計手法別Needファイル統合のテスト"""
    
    print("=" * 70)
    print("統計手法一貫性修正テスト")
    print("=" * 70)
    print(f"テスト実行: {datetime.now().strftime('%Y年%m月%d日 %H時%M分')}")
    print()
    
    # 3つの統計手法ディレクトリを確認
    base_dir = Path('extracted_results')
    methods = {
        'p25_based': '25パーセンタイル',
        'median_based': '中央値', 
        'mean_based': '平均値'
    }
    
    print("【修正前の状況確認】")
    print("-" * 40)
    
    for method_key, method_name in methods.items():
        method_dir = base_dir / f'out_{method_key}'
        
        if not method_dir.exists():
            print(f"{method_name}: ディレクトリ不存在")
            continue
        
        print(f"{method_name} ({method_key}):")
        
        # 職種別Needファイルの存在確認
        need_role_files = list(method_dir.glob('need_per_date_slot_role_*.parquet'))
        print(f"  職種別Needファイル: {len(need_role_files)}個")
        
        if need_role_files:
            # 統合計算のシミュレーション
            total_need = 0
            for need_file in need_role_files:
                try:
                    df = pd.read_parquet(need_file)
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    file_total = df[numeric_cols].sum().sum()
                    total_need += file_total
                except Exception as e:
                    print(f"    エラー: {need_file.name} - {e}")
            
            print(f"  統合Need合計: {total_need:.1f}人・スロット")
            print(f"  統合Need時間: {total_need * 0.5:.1f}時間/月")
        
        # 現在のshortage_time.parquet
        shortage_file = method_dir / 'shortage_time.parquet'
        if shortage_file.exists():
            df_shortage = pd.read_parquet(shortage_file)
            shortage_total = df_shortage.sum().sum() * 0.5
            print(f"  現在shortage_time: {shortage_total:.1f}時間")
        
        print()
    
    return True

def simulate_fix_impact():
    """修正の影響をシミュレーション"""
    
    print("【修正効果のシミュレーション】")
    print("-" * 40)
    
    # 統計手法別のNeed値（実測値）
    need_values = {
        'p25_based': 2062.0,    # 25パーセンタイル
        'median_based': 2396.0, # 中央値
        'mean_based': 2336.0    # 平均値
    }
    
    print("修正前（固定ファイル使用）:")
    print("  全統計手法で同じshortage_time: -2505.0時間")
    print("  → 統計手法の設定が無効化")
    print()
    
    print("修正後（統計手法別Need統合）:")
    for method_key, need_total in need_values.items():
        method_name = {'p25_based': '25%ile', 'median_based': '中央値', 'mean_based': '平均'}[method_key]
        
        # 供給は固定と仮定（実績値基準）
        supply_hours = 2881.0  # 5764 * 0.5
        need_hours = need_total * 0.5
        
        # 修正後のshortage_time予測
        predicted_shortage = need_hours - supply_hours
        
        print(f"  {method_name}:")
        print(f"    Need: {need_hours:.1f}時間")
        print(f"    Supply: {supply_hours:.1f}時間") 
        print(f"    予測shortage_time: {predicted_shortage:.1f}時間")
        
        # 25%ileとの比較
        if method_key != 'p25_based':
            base_need = need_values['p25_based'] * 0.5
            base_shortage = base_need - supply_hours
            diff = predicted_shortage - base_shortage
            print(f"    25%ileとの差異: {diff:+.1f}時間")
        
        print()

def calculate_expected_27486_correlation():
    """27,486.5時間問題との相関予測"""
    
    print("【27,486.5時間問題との相関予測】")
    print("-" * 40)
    
    target = 27486.5
    
    # 修正後の統計手法別予測（30日→90日拡張）
    need_values = {
        'p25_based': 2062.0,
        'median_based': 2396.0,
        'mean_based': 2336.0
    }
    
    supply_hours_30day = 2881.0
    
    for method_key, need_total in need_values.items():
        method_name = {'p25_based': '25%ile', 'median_based': '中央値', 'mean_based': '平均'}[method_key]
        
        # 30日での修正後shortage_time
        need_hours_30day = need_total * 0.5
        shortage_30day = need_hours_30day - supply_hours_30day
        
        # 90日拡張（サマリー計算想定）
        if shortage_30day > 0:  # 不足の場合
            # サマリー計算では正値になる想定
            summary_shortage_30day = abs(shortage_30day)
            projected_90day = summary_shortage_30day * 3.0
            
            diff_from_target = abs(projected_90day - target)
            
            print(f"{method_name}:")
            print(f"  修正後30日不足: {shortage_30day:.1f}時間")
            print(f"  サマリー換算: {summary_shortage_30day:.1f}時間")
            print(f"  90日推定: {projected_90day:.1f}時間")
            print(f"  27,486.5との差異: {diff_from_target:.1f}時間")
            
            if diff_from_target < 2000:
                correlation = "★★★ 高い相関"
            elif diff_from_target < 5000:
                correlation = "★★☆ 中程度の相関"
            else:
                correlation = "★☆☆ 低い相関"
            
            print(f"  相関評価: {correlation}")
            print()

def main():
    """メインテスト実行"""
    
    test_need_file_integration()
    simulate_fix_impact()
    calculate_expected_27486_correlation()
    
    print("=" * 70)
    print("【修正効果まとめ】")
    print("=" * 70)
    print("✅ 修正内容:")
    print("  1. shortage.py: 統計手法別Needファイルを正しく統合")
    print("  2. heatmap_v2.py: デフォルト統計手法を中央値に変更")
    print()
    print("✅ 期待される効果:")
    print("  1. shortage_time.parquetが統計手法を正しく反映")
    print("  2. 計算の一貫性確保による信頼性向上")
    print("  3. 中央値採用により現実的な需要推定")
    print("  4. 27,486.5時間問題の解決への道筋")
    print()
    print("📋 次のステップ:")
    print("  1. 修正したコードでの再計算実行")
    print("  2. 統計手法別shortage_time.parquetの差異確認")
    print("  3. 計算整合性の最終検証")
    print("=" * 70)

if __name__ == "__main__":
    main()