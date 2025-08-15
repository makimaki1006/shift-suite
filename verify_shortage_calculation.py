#!/usr/bin/env python3
"""
27,486.5時間問題の根本的検証
ユーザーの確信に基づく詳細分析
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analyze_shortage_calculation():
    """不足時間計算の完全検証"""
    base_path = Path("/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/extracted_test")
    
    print("=== 27,486.5時間問題 - 根本的再検証 ===\n")
    
    # 分析期間の確認
    print("【1. 分析期間の検証】")
    
    # P25ベースの詳細分析
    p25_shortage_path = base_path / "out_p25_based" / "shortage_time.parquet"
    df_shortage = pd.read_parquet(p25_shortage_path)
    
    print(f"データ形状: {df_shortage.shape}")
    print(f"時間帯数: {len(df_shortage.index)}")
    print(f"日数: {len(df_shortage.columns)}")
    
    # 日付範囲の確認
    dates = pd.to_datetime(df_shortage.columns)
    print(f"開始日: {dates.min()}")
    print(f"終了日: {dates.max()}")
    print(f"期間: {(dates.max() - dates.min()).days + 1}日")
    
    # 月数計算
    months = (dates.max() - dates.min()).days / 30.4
    print(f"推定月数: {months:.1f}ヶ月")
    
    print("\n【2. 不足時間の詳細計算】")
    
    # 総不足スロット数
    total_shortage_slots = df_shortage.sum().sum()
    print(f"総不足スロット数: {total_shortage_slots}")
    
    # スロット時間の検証
    print(f"\nスロット時間の仮定:")
    print(f"  0.5時間（30分）の場合: {total_shortage_slots * 0.5:,.1f}時間")
    print(f"  1.0時間（60分）の場合: {total_shortage_slots * 1.0:,.1f}時間")
    
    # 日平均・月平均の検証
    daily_shortage = df_shortage.sum()
    print(f"\n日別不足統計:")
    print(f"  平均: {daily_shortage.mean():.1f}スロット/日")
    print(f"  最大: {daily_shortage.max():.1f}スロット/日")
    print(f"  最小: {daily_shortage.min():.1f}スロット/日")
    
    # 時間帯別の分析
    hourly_shortage = df_shortage.sum(axis=1)
    print(f"\n時間帯別不足統計:")
    print(f"  平均: {hourly_shortage.mean():.1f}スロット/時間帯")
    print(f"  最大: {hourly_shortage.max():.1f}スロット/時間帯")
    
    print("\n【3. 期間依存性の検証】")
    
    # もし3ヶ月分なら
    if months > 2.5 and months < 3.5:
        print("⚠️ 約3ヶ月分のデータ")
        monthly_avg = total_shortage_slots * 0.5 / 3
        print(f"月平均不足時間: {monthly_avg:,.1f}時間")
        print(f"これは1ヶ月あたり{monthly_avg:,.0f}時間")
        
        # 1ヶ月分析との比較
        print(f"\n1ヶ月分析の期待値:")
        print(f"  759時間 × 3 = 2,277時間")
        print(f"  実際の値: {total_shortage_slots * 0.5:,.0f}時間")
        print(f"  差異: {total_shortage_slots * 0.5 - 2277:,.0f}時間 ({(total_shortage_slots * 0.5 / 2277 - 1) * 100:.0f}%)")
    
    # もし1年分なら
    elif months > 11:
        print("⚠️ 約1年分のデータの可能性")
        monthly_avg = total_shortage_slots * 0.5 / 12
        print(f"月平均不足時間: {monthly_avg:,.1f}時間")
    
    print("\n【4. 27,486.5時間の逆算】")
    target_hours = 27486.5
    
    # 必要なスロット数
    required_slots = target_hours / 0.5
    print(f"27,486.5時間に必要なスロット数: {required_slots:,.0f}")
    print(f"実際のスロット数: {total_shortage_slots:,.0f}")
    print(f"差異: {total_shortage_slots - required_slots:,.0f}スロット")
    
    # 別のスロット時間の可能性
    possible_slot_hours = target_hours / total_shortage_slots
    print(f"\n実際のスロット時間の可能性: {possible_slot_hours:.4f}時間 ({possible_slot_hours * 60:.2f}分)")
    
    print("\n【5. 統計手法による差異】")
    
    # 全3手法の比較
    methods = ['mean_based', 'median_based', 'p25_based']
    for method in methods:
        method_path = base_path / f"out_{method}" / "shortage_time.parquet"
        if method_path.exists():
            df_method = pd.read_parquet(method_path)
            total_slots = df_method.sum().sum()
            total_hours = total_slots * 0.5
            print(f"{method}: {total_hours:,.1f}時間 ({total_slots:,.0f}スロット)")
    
    print("\n【6. 不足が発生している時間帯の詳細】")
    
    # 不足が多い時間帯TOP10
    top_times = hourly_shortage.nlargest(10)
    print("不足が多い時間帯TOP10:")
    for time, shortage in top_times.items():
        print(f"  {time}: {shortage:.1f}スロット")
    
    print("\n【7. ユーザーの指摘の可能性】")
    print("考えられる問題:")
    print("1. 分析期間が3ヶ月ではない")
    print("2. スロット時間が30分ではない")
    print("3. 休日・祝日の扱いが異なる")
    print("4. 統計処理の期間依存性がまだ残っている")
    print("5. 別の計算要素（例：職種別の加重）が存在する")
    
    # Need値の確認
    print("\n【8. Need値の確認】")
    need_path = base_path / "out_p25_based" / "need_per_date_slot.parquet"
    if need_path.exists():
        df_need = pd.read_parquet(need_path)
        total_need = df_need.sum().sum()
        print(f"総Need: {total_need}スロット ({total_need * 0.5:,.1f}時間)")
    
    # 実績データの確認
    print("\n【9. 実績データの確認】")
    heat_all_path = base_path / "out_p25_based" / "heat_ALL.parquet"
    if heat_all_path.exists():
        df_heat = pd.read_parquet(heat_all_path)
        # 'actual'列を探す
        actual_cols = [col for col in df_heat.columns if 'actual' in str(col).lower() or col.startswith('20')]
        if actual_cols:
            print(f"実績データ列数: {len(actual_cols)}")

if __name__ == "__main__":
    analyze_shortage_calculation()