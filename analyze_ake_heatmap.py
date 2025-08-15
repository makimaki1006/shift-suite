#!/usr/bin/env python3
"""
明け番シフトがヒートマップでどのように表示されているか詳細分析
"""

import pandas as pd
import numpy as np
from datetime import datetime

def analyze_ake_heatmap():
    """明け番のヒートマップ表示を詳細分析"""
    try:
        # 全体ヒートマップを読み込み
        heat_all = pd.read_parquet("analysis_results_20/out_p25_based/heat_ALL.parquet")
        
        print("=== ヒートマップデータ構造 ===")
        print(f"Shape: {heat_all.shape}")
        print(f"\n時間インデックス（0:00-10:00の部分）:")
        morning_times = [idx for idx in heat_all.index if ':' in str(idx) and int(str(idx).split(':')[0]) < 10]
        print(f"早朝時間: {morning_times}")
        
        # 日付列を特定
        date_cols = [col for col in heat_all.columns if col not in ['need', 'upper', 'staff', 'lack', 'excess']]
        print(f"\n日付列数: {len(date_cols)}")
        
        # 早朝時間帯のデータを確認（最初の3日分）
        print("\n=== 早朝時間帯の実績値（最初の3日） ===")
        for date_col in date_cols[:3]:
            print(f"\n{date_col}:")
            for time_idx in morning_times[:10]:  # 0:00-5:00
                value = heat_all.loc[time_idx, date_col]
                if value > 0:
                    print(f"  {time_idx}: {value:.0f}人")
                else:
                    print(f"  {time_idx}: 0人 ← ★データなし")
        
        # 連続性をチェック
        print("\n=== 連続性チェック ===")
        for date_col in date_cols[:3]:
            print(f"\n{date_col}の連続性:")
            gaps = []
            prev_value = None
            prev_time = None
            
            for time_idx in morning_times:
                current_value = heat_all.loc[time_idx, date_col]
                
                if prev_value is not None and prev_value > 0 and current_value == 0:
                    gaps.append(f"{prev_time} ({prev_value:.0f}人) → {time_idx} (0人)")
                elif prev_value == 0 and current_value > 0:
                    gaps.append(f"{prev_time} (0人) → {time_idx} ({current_value:.0f}人)")
                
                prev_value = current_value
                prev_time = time_idx
            
            if gaps:
                print(f"  ギャップ検出:")
                for gap in gaps:
                    print(f"    {gap}")
            else:
                print(f"  連続性OK")
        
        # 需要値も確認
        print("\n=== 早朝時間帯の需要値 ===")
        for time_idx in morning_times[:10]:
            need_value = heat_all.loc[time_idx, 'need']
            print(f"  {time_idx}: 需要 {need_value:.0f}人")
        
        # 職種別ヒートマップも確認（介護職）
        print("\n=== 職種別ヒートマップ（介護職）===")
        try:
            heat_kaigo = pd.read_parquet("analysis_results_20/out_p25_based/heat_2F介護.parquet")
            print(f"2F介護 shape: {heat_kaigo.shape}")
            
            for date_col in date_cols[:2]:
                if date_col in heat_kaigo.columns:
                    print(f"\n{date_col}:")
                    for time_idx in morning_times[:6]:  # 0:00-3:00
                        value = heat_kaigo.loc[time_idx, date_col]
                        print(f"  {time_idx}: {value:.0f}人")
        except Exception as e:
            print(f"職種別ヒートマップ読み込みエラー: {e}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_ake_heatmap()