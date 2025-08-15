#!/usr/bin/env python3
"""
ヒートマップ生成時の時間軸の問題を詳細調査
"""

import pandas as pd
import numpy as np
import json

def check_heatmap_issue():
    """ヒートマップの時間軸問題を調査"""
    try:
        # 日別ヒートマップを確認
        daily_heat = pd.read_parquet("analysis_results_20/out_p25_based/heat_ALL.parquet")
        print(f"日別ヒートマップ shape: {daily_heat.shape}")
        print(f"インデックス（行）: {daily_heat.index.tolist()[:10]}")  # 最初の10行
        print(f"カラム（列）: {daily_heat.columns.tolist()[:10]}")  # 最初の10列
        
        # インデックスが時間かどうか確認
        if len(daily_heat.index) > 0:
            first_idx = daily_heat.index[0]
            print(f"\n最初のインデックス値: '{first_idx}' (型: {type(first_idx)})")
            
            # 時間パターンのチェック
            time_pattern_count = sum(1 for idx in daily_heat.index if ':' in str(idx))
            print(f"時間パターン（HH:MM）を含むインデックス数: {time_pattern_count}/{len(daily_heat.index)}")
        
        # メタデータから期待される構造を確認
        with open("analysis_results_20/out_p25_based/heatmap.meta.json", 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        print(f"\nメタデータのスロット情報:")
        print(f"  slot: {meta.get('slot', 'N/A')} 分")
        print(f"  dow_need_pattern のエントリ数: {len(meta.get('dow_need_pattern', []))}")
        
        # 時間スロット数の確認
        expected_slots = 24 * 60 // meta.get('slot', 30)
        print(f"  期待される時間スロット数: {expected_slots}")
        print(f"  実際のインデックス数: {len(daily_heat.index)}")
        
        # 別の分析結果ファイルも確認
        print(f"\n他のヒートマップファイルを確認:")
        import os
        heat_files = [f for f in os.listdir("analysis_results_20/out_p25_based") 
                      if f.startswith('heat_') and f.endswith('.parquet')]
        
        for heat_file in heat_files[:3]:  # 最初の3ファイル
            df = pd.read_parquet(f"analysis_results_20/out_p25_based/{heat_file}")
            print(f"  {heat_file}: shape={df.shape}, インデックス数={len(df.index)}")
            if len(df.index) > 0:
                print(f"    最初のインデックス: {df.index[0]}")
        
        # 元のintermediate_dataも確認
        print(f"\n元の中間データを確認:")
        intermediate = pd.read_parquet("analysis_results_20/out_p25_based/intermediate_data.parquet")
        
        # 時間情報があるか確認
        if 'ds' in intermediate.columns:
            intermediate['hour'] = pd.to_datetime(intermediate['ds']).dt.hour
            intermediate['time_str'] = pd.to_datetime(intermediate['ds']).dt.strftime('%H:%M')
            
            print(f"中間データに含まれる時間スロット:")
            time_counts = intermediate['time_str'].value_counts().sort_index()
            print(f"  ユニークな時間スロット数: {len(time_counts)}")
            print(f"  最初の10スロット: {time_counts.index.tolist()[:10]}")
            
            # 明シフトの時間分布も確認
            if 'code' in intermediate.columns:
                ake_data = intermediate[intermediate['code'] == '明']
                if len(ake_data) > 0:
                    ake_times = ake_data['time_str'].value_counts().sort_index()
                    print(f"\n明シフトの時間分布:")
                    print(f"  時間スロット数: {len(ake_times)}")
                    print(f"  時間スロット: {ake_times.index.tolist()}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_heatmap_issue()