#!/usr/bin/env python3
"""
計算フローのトレース - どこで値が爆発するか特定
"""

import pandas as pd
import numpy as np
from pathlib import Path

def trace_calculation_flow():
    """計算フローの各段階をトレース"""
    
    print("🔍 === 計算フロートレース ===\n")
    
    # 1. heatmap計算後のNeed値確認
    print("【1. Heatmapの出力確認】")
    heatmap_files = [
        "need_per_date_slot.parquet",
        "need_per_date_slot_role_介護.parquet",
        "need_pattern_dow_slot.parquet"
    ]
    
    for scenario in ["out_mean_based", "out_median_based", "out_p25_based"]:
        scenario_path = Path(scenario)
        if scenario_path.exists():
            print(f"\n📁 {scenario}:")
            for file in heatmap_files:
                file_path = scenario_path / file
                if file_path.exists():
                    try:
                        df = pd.read_parquet(file_path)
                        if 'need' in df.columns:
                            total_need = df['need'].sum()
                        else:
                            # 日付列の合計
                            date_cols = [col for col in df.columns if col not in ['time', 'timeslot', 'role', 'employment']]
                            total_need = df[date_cols].sum().sum() if date_cols else 0
                        
                        print(f"  {file}: 合計Need = {total_need:.0f}")
                        
                        # 日付列数の確認
                        date_cols = [col for col in df.columns if col not in ['time', 'timeslot', 'role', 'employment']]
                        print(f"    日付列数: {len(date_cols)}")
                        
                        # サンプル値確認
                        if len(date_cols) > 0:
                            sample_col = date_cols[0]
                            sample_values = df[sample_col].head(5).tolist()
                            print(f"    {sample_col}のサンプル値: {sample_values}")
                            
                    except Exception as e:
                        print(f"  {file}: 読み込みエラー - {e}")
    
    print("\n" + "="*60)
    
    # 2. shortage計算後の不足値確認
    print("\n【2. Shortageの出力確認】")
    shortage_files = [
        "shortage_time.parquet",
        "shortage_role_summary.parquet",
        "shortage_employment_summary.parquet"
    ]
    
    for scenario in ["out_mean_based", "out_median_based", "out_p25_based"]:
        scenario_path = Path(scenario)
        if scenario_path.exists():
            print(f"\n📁 {scenario}:")
            
            # shortage_time.parquet
            shortage_time_path = scenario_path / "shortage_time.parquet"
            if shortage_time_path.exists():
                try:
                    df = pd.read_parquet(shortage_time_path)
                    total_lack_count = df.sum().sum()
                    print(f"  shortage_time: 合計不足人数 = {total_lack_count:.0f}")
                    
                    # スロット時間を仮定して時間換算
                    for slot_hours in [0.25, 0.5, 1.0]:
                        total_hours = total_lack_count * slot_hours
                        print(f"    → {slot_hours}時間スロットなら: {total_hours:.0f}時間")
                        
                except Exception as e:
                    print(f"  shortage_time: 読み込みエラー - {e}")
            
            # サマリーファイル
            for file in ["shortage_role_summary.parquet", "shortage_employment_summary.parquet"]:
                file_path = scenario_path / file
                if file_path.exists():
                    try:
                        df = pd.read_parquet(file_path)
                        if 'lack_h' in df.columns:
                            total_lack_h = df['lack_h'].sum()
                            print(f"  {file}: 合計不足時間 = {total_lack_h:.0f}時間")
                            
                            # 詳細確認
                            print(f"    レコード数: {len(df)}")
                            if len(df) > 0:
                                print(f"    最大不足: {df['lack_h'].max():.0f}時間")
                                print(f"    平均不足: {df['lack_h'].mean():.0f}時間")
                                
                    except Exception as e:
                        print(f"  {file}: 読み込みエラー - {e}")
    
    print("\n" + "="*60)
    
    # 3. 計算ロジックの確認
    print("\n【3. 計算ロジックの確認】")
    print("A. Need計算（heatmap.py）:")
    print("   - 期間内の各時間×曜日のデータから統計値を計算")
    print("   - 1ヶ月: 約4-5データ → 統計値A")
    print("   - 3ヶ月: 約12-15データ → 統計値B（外れ値・季節変動含む）")
    print()
    print("B. 不足計算（shortage.py）:")
    print("   - lack_count = (need - actual).clip(lower=0)")
    print("   - lack_hours = lack_count * slot_hours")
    print("   - total = sum(all_slots, all_dates)")
    print()
    print("C. 時間軸補正（time_axis_shortage_calculator.py）:")
    print("   - estimated_demand = supply + (baseline * ratio)")
    print("   - 問題: baselineが既に巨大な値")
    
    print("\n" + "="*60)
    
    # 4. 期間による違いの推定
    print("\n【4. 期間による違いの推定】")
    print("1ヶ月分析:")
    print("  - 統計値が局所的 → Need値が現実的")
    print("  - 例: 各スロット2-3人必要 × 48スロット/日 × 30日 = 2,880-4,320人")
    print("  - 0.5時間スロットなら: 1,440-2,160時間")
    print()
    print("3ヶ月分析:")
    print("  - 統計値が変動 → Need値が増大")
    print("  - 外れ値の影響でNeed値が倍増する可能性")
    print("  - 例: 各スロット5-10人必要 × 48スロット/日 × 90日 = 21,600-43,200人")
    print("  - 0.5時間スロットなら: 10,800-21,600時間")
    print()
    print("さらに時間軸補正で加算されると...")
    print("  → 55,518時間のような異常値に！")

if __name__ == "__main__":
    trace_calculation_flow()