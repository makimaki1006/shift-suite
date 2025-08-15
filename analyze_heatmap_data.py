#!/usr/bin/env python3
"""
ヒートマップデータで明け番の途切れを詳細分析
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
sys.path.append('.')

def analyze_heatmap_data():
    """ヒートマップデータでの明け番表示を詳細分析"""
    try:
        # ヒートマップのparquetファイルを読み込み
        heatmap_path = "analysis_results_20/out_p25_based/heat_ALL.parquet"
        df = pd.read_parquet(heatmap_path)
        
        print(f"ヒートマップデータ shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        
        # 時間列を確認
        time_cols = [col for col in df.columns if ':' in str(col)]
        print(f"\n時間列の数: {len(time_cols)}")
        print(f"時間列（最初の20個）: {time_cols[:20]}")
        
        # 00:00-10:00の時間列を特定
        morning_cols = []
        for col in time_cols:
            try:
                hour = int(str(col).split(':')[0])
                if 0 <= hour < 10:
                    morning_cols.append(col)
            except:
                continue
        
        print(f"\n早朝時間列（00:00-09:xx）: {sorted(morning_cols)}")
        
        # 早朝時間帯のデータをチェック
        print(f"\n早朝時間帯のデータ統計:")
        for col in sorted(morning_cols)[:10]:  # 最初の10列
            data = df[col]
            non_zero_count = (data > 0).sum()
            max_val = data.max()
            mean_val = data.mean()
            print(f"  {col}: 非ゼロ数={non_zero_count}, 最大値={max_val:.2f}, 平均={mean_val:.2f}")
        
        # 特定の行（職種・雇用形態）での早朝データを確認
        if 'role' in df.columns:
            print(f"\n職種別の早朝データ確認:")
            unique_roles = df['role'].unique()
            for role in unique_roles[:3]:  # 最初の3職種
                role_data = df[df['role'] == role]
                print(f"\n職種: {role}")
                for col in sorted(morning_cols)[:5]:  # 最初の5時間
                    val = role_data[col].iloc[0] if len(role_data) > 0 else 0
                    print(f"    {col}: {val}")
        
        # メタデータファイルも確認
        print(f"\nヒートマップメタデータの確認:")
        try:
            import json
            with open("analysis_results_20/out_p25_based/heatmap.meta.json", 'r', encoding='utf-8') as f:
                meta = json.load(f)
            
            print(f"ヒートマップ生成時刻: {meta.get('generated_at', 'N/A')}")
            print(f"データ期間: {meta.get('date_range', {}).get('start', 'N/A')} - {meta.get('date_range', {}).get('end', 'N/A')}")
            
            if 'dow_need_pattern' in meta:
                dow_pattern = meta['dow_need_pattern']
                print(f"\n曜日別需要パターン（早朝時間帯）:")
                for time_slot in sorted(morning_cols)[:10]:
                    if str(time_slot) in dow_pattern:
                        value = dow_pattern[str(time_slot)]
                        print(f"  {time_slot}: {value}")
                        
        except Exception as e:
            print(f"メタデータ読み込みエラー: {e}")
        
        # 需要データも確認
        print(f"\n需要データの確認:")
        need_path = "analysis_results_20/out_p25_based/need_per_date_slot.parquet"
        need_df = pd.read_parquet(need_path)
        
        print(f"需要データ shape: {need_df.shape}")
        
        # 需要データから早朝時間帯を抽出
        if 'ds' in need_df.columns:
            need_df['hour'] = pd.to_datetime(need_df['ds']).dt.hour
            morning_need = need_df[need_df['hour'] < 10]
            print(f"早朝時間帯（0-9時）の需要レコード数: {len(morning_need)}")
            
            if len(morning_need) > 0:
                print(f"早朝需要の統計:")
                print(f"  平均需要: {morning_need['need'].mean():.2f}")
                print(f"  最大需要: {morning_need['need'].max():.2f}")
                print(f"  需要ゼロの割合: {(morning_need['need'] == 0).mean():.2%}")
                
                # 時間別需要
                hourly_need = morning_need.groupby('hour')['need'].mean().sort_index()
                print(f"\n時間別平均需要:")
                for hour, need in hourly_need.items():
                    print(f"  {hour:02d}時: {need:.2f}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_heatmap_data()