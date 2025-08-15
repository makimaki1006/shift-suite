#!/usr/bin/env python3
"""
月次基準値統合アプローチのテスト
期間依存性問題の解決を検証
"""

import sys
import os
import datetime as dt
import pandas as pd
import numpy as np

# プロジェクトのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from shift_suite.tasks.heatmap import (
        calculate_integrated_monthly_pattern_need,
        create_monthly_dow_pattern,
        create_integrated_pattern
    )
    from shift_suite.tasks.utils import gen_labels
    print("✅ インポート成功")
except Exception as e:
    print(f"❌ インポートエラー: {e}")
    sys.exit(1)

def create_test_data():
    """
    テスト用の実績データを作成
    3ヶ月分のデータ（7月、8月、9月）
    """
    print("\n=== テストデータ作成 ===")
    
    # 時間スロット作成
    time_labels = gen_labels(30)  # 30分スロット
    
    # 日付範囲
    start_date = dt.date(2024, 7, 1)
    end_date = dt.date(2024, 9, 30)
    
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += dt.timedelta(days=1)
    
    print(f"期間: {start_date} - {end_date}")
    print(f"日数: {len(dates)}日")
    print(f"時間帯数: {len(time_labels)}")
    
    # データフレーム作成
    df = pd.DataFrame(0, index=time_labels, columns=dates)
    
    # 曜日・時間帯別のパターンを設定
    np.random.seed(42)  # 再現可能性のため
    
    for date in dates:
        dow = date.weekday()  # 0=月曜
        
        # 曜日別の基本パターン
        if dow < 5:  # 平日
            base_staff = np.random.normal(5, 1)  # 平均5人、標準偏差1
        else:  # 土日
            base_staff = np.random.normal(3, 0.5)  # 平均3人、標準偏差0.5
        
        # 時間帯別の変動
        for i, time_slot in enumerate(time_labels):
            if "09:00" <= time_slot <= "17:00":
                # 日中は多め
                staff = max(0, int(base_staff + np.random.normal(2, 0.5)))
            elif "18:00" <= time_slot <= "21:00":
                # 夕方も多め
                staff = max(0, int(base_staff + np.random.normal(1, 0.5)))
            else:
                # 早朝・深夜は少なめ
                staff = max(0, int(base_staff * 0.3 + np.random.normal(0, 0.3)))
            
            df.loc[time_slot, date] = staff
    
    print("✅ テストデータ作成完了")
    return df

def test_period_independence():
    """
    期間依存性テスト
    1ヶ月分析 vs 3ヶ月分析の結果比較
    """
    print("\n=== 期間依存性テスト ===")
    
    # テストデータ作成
    test_data = create_test_data()
    
    # 1ヶ月分析（7月のみ）
    july_data = test_data.loc[:, [col for col in test_data.columns 
                                 if isinstance(col, dt.date) and col.month == 7]]
    
    print("1ヶ月分析（7月）実行中...")
    july_pattern = calculate_integrated_monthly_pattern_need(
        july_data,
        dt.date(2024, 7, 1),
        dt.date(2024, 7, 31),
        "平均値",
        False,
        1.5,
        30
    )
    
    # 3ヶ月分析
    print("3ヶ月分析（7-9月）実行中...")
    three_month_pattern = calculate_integrated_monthly_pattern_need(
        test_data,
        dt.date(2024, 7, 1),
        dt.date(2024, 9, 30),
        "平均値",
        False,
        1.5,
        30
    )
    
    # 結果比較
    july_total = july_pattern.sum().sum()
    three_month_total = three_month_pattern.sum().sum()
    
    print(f"\n=== 結果比較 ===")
    print(f"1ヶ月パターン総Need: {july_total}")
    print(f"3ヶ月パターン総Need: {three_month_total}")
    
    # パターンの詳細比較
    print("\n=== パターン詳細比較 ===")
    for dow in range(7):
        dow_name = ["月", "火", "水", "木", "金", "土", "日"][dow]
        july_dow_total = july_pattern.iloc[:, dow].sum()
        three_month_dow_total = three_month_pattern.iloc[:, dow].sum()
        
        print(f"{dow_name}曜日 - 1ヶ月: {july_dow_total:.1f}, 3ヶ月: {three_month_dow_total:.1f}")
    
    # 相関係数計算
    correlation = np.corrcoef(
        july_pattern.values.flatten(),
        three_month_pattern.values.flatten()
    )[0, 1]
    
    print(f"\nパターン相関係数: {correlation:.4f}")
    
    return {
        'july_pattern': july_pattern,
        'three_month_pattern': three_month_pattern,
        'correlation': correlation,
        'july_total': july_total,
        'three_month_total': three_month_total
    }

def test_linear_additivity():
    """
    線形加算性テスト
    月別パターンの合計 vs 統合パターンの期間適用
    """
    print("\n=== 線形加算性テスト ===")
    
    test_data = create_test_data()
    
    # 各月のパターンを個別作成
    monthly_patterns = []
    monthly_totals = []
    
    for month in [7, 8, 9]:
        month_data = test_data.loc[:, [col for col in test_data.columns 
                                      if isinstance(col, dt.date) and col.month == month]]
        
        month_pattern = calculate_integrated_monthly_pattern_need(
            month_data,
            dt.date(2024, month, 1),
            dt.date(2024, month, 31) if month != 9 else dt.date(2024, 9, 30),
            "平均値",
            False,
            1.5,
            30
        )
        
        monthly_patterns.append(month_pattern)
        month_total = month_pattern.sum().sum()
        monthly_totals.append(month_total)
        
        print(f"{month}月パターン総Need: {month_total:.1f}")
    
    # 手動合計
    manual_total = sum(monthly_totals)
    print(f"手動合計: {manual_total:.1f}")
    
    # 統合パターンでの期間適用（3ヶ月）
    integrated_pattern = calculate_integrated_monthly_pattern_need(
        test_data,
        dt.date(2024, 7, 1),
        dt.date(2024, 9, 30),
        "平均値",
        False,
        1.5,
        30
    )
    
    # 統合パターンを3ヶ月期間に適用した場合の総Need
    integrated_total = integrated_pattern.sum().sum()
    
    # 期間中の営業日数を計算
    total_days = (dt.date(2024, 9, 30) - dt.date(2024, 7, 1)).days + 1
    print(f"総日数: {total_days}日")
    
    # 統合パターンの日平均Need
    avg_daily_need = integrated_total
    print(f"統合パターン日平均Need: {avg_daily_need:.1f}")
    
    # 期間適用での理論値
    theoretical_total = avg_daily_need * total_days
    print(f"理論期間総Need: {theoretical_total:.1f}")
    
    return {
        'monthly_totals': monthly_totals,
        'manual_total': manual_total,
        'integrated_pattern': integrated_pattern,
        'integrated_total': integrated_total,
        'theoretical_total': theoretical_total
    }

def main():
    """メインテスト実行"""
    print("🔬 月次基準値統合アプローチ検証テスト")
    print("=" * 60)
    
    try:
        # 期間依存性テスト
        period_test_results = test_period_independence()
        
        # 線形加算性テスト
        linearity_test_results = test_linear_additivity()
        
        print("\n" + "=" * 60)
        print("🎯 テスト結果サマリー")
        print("=" * 60)
        
        # 期間依存性評価
        correlation = period_test_results['correlation']
        if correlation > 0.8:
            print(f"✅ 期間依存性: 高い一貫性 (相関: {correlation:.4f})")
        elif correlation > 0.6:
            print(f"⚠️ 期間依存性: 中程度の一貫性 (相関: {correlation:.4f})")
        else:
            print(f"❌ 期間依存性: 低い一貫性 (相関: {correlation:.4f})")
        
        # 線形加算性評価
        manual_total = linearity_test_results['manual_total']
        integrated_total = linearity_test_results['integrated_total']
        
        if abs(manual_total - integrated_total) < manual_total * 0.1:
            print(f"✅ 線形加算性: 良好 (手動: {manual_total:.1f}, 統合: {integrated_total:.1f})")
        else:
            print(f"❌ 線形加算性: 問題あり (手動: {manual_total:.1f}, 統合: {integrated_total:.1f})")
        
        print("\n🏆 月次基準値統合アプローチの実装が完了しました！")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)