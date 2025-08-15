#!/usr/bin/env python
"""
Need計算の詳細分析スクリプト
"""
import pandas as pd
import numpy as np
from pathlib import Path

def detailed_need_analysis():
    """Need計算の詳細分析"""
    
    analysis_dir = Path("analysis_results")
    
    print("=== Need計算の詳細分析 ===\n")
    
    # 1. need_per_date_slot.parquetの詳細分析
    need_file = analysis_dir / "need_per_date_slot.parquet"
    if need_file.exists():
        print("1. need_per_date_slot.parquet 詳細分析:")
        need_df = pd.read_parquet(need_file)
        
        # 最初の数日分の詳細データ
        first_5_dates = need_df.columns[:5]
        print(f"   最初の5日間の詳細:")
        for date in first_5_dates:
            daily_sum = need_df[date].sum()
            max_val = need_df[date].max()
            non_zero_count = (need_df[date] > 0).sum()
            print(f"     {date}: 合計={daily_sum:.1f}, 最大値={max_val:.1f}, 非ゼロ時間帯数={non_zero_count}")
        
        # 時間帯別の平均値
        print("\n   時間帯別の平均Need値 (最初の10時間帯):")
        for i, time_slot in enumerate(need_df.index[:10]):
            avg_val = need_df.loc[time_slot].mean()
            max_val = need_df.loc[time_slot].max()
            print(f"     {time_slot}: 平均={avg_val:.1f}, 最大={max_val:.1f}")
        
        # データの分布確認
        all_values = need_df.values.flatten()
        print(f"\n   データ分布:")
        print(f"     全値の範囲: {all_values.min():.1f} - {all_values.max():.1f}")
        print(f"     平均: {all_values.mean():.1f}")
        print(f"     標準偏差: {all_values.std():.1f}")
        print(f"     ゼロでない値の割合: {(all_values > 0).mean():.3f}")
        
    print("\n")
    
    # 2. heat_ALL.parquetとの比較
    heat_all_file = analysis_dir / "heat_ALL.parquet"
    if heat_all_file.exists():
        print("2. heat_ALL.parquet との比較:")
        heat_all_df = pd.read_parquet(heat_all_file)
        
        # 日付列のみ抽出
        date_cols = [col for col in heat_all_df.columns 
                    if col not in ['need', 'upper', 'staff', 'lack', 'excess']]
        
        print(f"   日付列数: {len(date_cols)}")
        
        if date_cols:
            # 最初の数日分を比較
            for date in date_cols[:5]:
                if date in need_df.columns:
                    need_detail = need_df[date].sum()
                    heat_actual = heat_all_df[date].sum() if date in heat_all_df.columns else 0
                    print(f"     {date}: need_per_date_slot={need_detail:.1f}, heat_ALL実績={heat_actual:.1f}")
        
        # need列との比較
        if 'need' in heat_all_df.columns:
            print(f"\n   heat_ALL.parquetのneed列:")
            need_series = heat_all_df['need']
            print(f"     範囲: {need_series.min():.1f} - {need_series.max():.1f}")
            print(f"     合計: {need_series.sum():.1f}")
            print(f"     非ゼロ時間帯数: {(need_series > 0).sum()}")
            
            # 時間帯別比較（最初の10時間帯）
            print(f"\n   時間帯別比較 (最初の10時間帯):")
            for i, time_slot in enumerate(need_series.index[:10]):
                need_val = need_series.loc[time_slot]
                if time_slot in need_df.index:
                    avg_detail = need_df.loc[time_slot].mean()
                    print(f"     {time_slot}: heat_ALL={need_val:.1f}, need_per_date平均={avg_detail:.1f}")
    
    print("\n")
    
    # 3. 職種別ヒートマップとの比較
    print("3. 職種別ヒートマップとの詳細比較:")
    role_files = [f for f in analysis_dir.glob("heat_*.parquet") 
                  if not f.name.startswith("heat_emp_") and f.name != "heat_ALL.parquet"]
    
    for role_file in role_files[:3]:  # 最初の3職種のみ
        role_name = role_file.stem.replace("heat_", "")
        role_df = pd.read_parquet(role_file)
        
        print(f"\n   職種: {role_name}")
        if 'need' in role_df.columns:
            need_col = role_df['need']
            print(f"     need列合計: {need_col.sum():.1f}")
            print(f"     need列範囲: {need_col.min():.1f} - {need_col.max():.1f}")
            print(f"     非ゼロ時間帯数: {(need_col > 0).sum()}")
            
            # 実際の日付列データもチェック
            date_cols_role = [col for col in role_df.columns 
                            if col not in ['need', 'upper', 'staff', 'lack', 'excess']]
            if date_cols_role:
                first_date_sum = role_df[date_cols_role[0]].sum()
                print(f"     実績データ例({date_cols_role[0]}): {first_date_sum:.1f}")

def check_heatmap_calculation_logic():
    """ヒートマップの計算ロジックをチェック"""
    
    print("\n=== ヒートマップ計算ロジックの検証 ===")
    
    analysis_dir = Path("analysis_results")
    
    # メタデータファイルの確認
    meta_file = analysis_dir / "heatmap.meta.json"
    if meta_file.exists():
        import json
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta_data = json.load(f)
        
        print("heatmap.meta.json の内容:")
        print(f"  スロット: {meta_data.get('slot')}")
        print(f"  職種数: {len(meta_data.get('roles', []))}")
        print(f"  日付数: {len(meta_data.get('dates', []))}")
        print(f"  休業日数: {len(meta_data.get('estimated_holidays', []))}")
        
        # Need計算パラメータ
        need_params = meta_data.get('need_calculation_params', {})
        print(f"  Need計算手法: {need_params.get('statistic_method')}")
        print(f"  参照期間: {need_params.get('ref_start_date')} - {need_params.get('ref_end_date')}")
        
        # 曜日別Needパターン
        dow_pattern = meta_data.get('dow_need_pattern', [])
        if dow_pattern:
            print(f"  曜日別Needパターン数: {len(dow_pattern)}")
            # 日曜日（6）のパターンを確認
            sunday_pattern = [p for p in dow_pattern if p.get('6') is not None]
            if sunday_pattern:
                sunday_values = [p.get('6', 0) for p in dow_pattern]
                print(f"  日曜日Need合計: {sum(sunday_values)}")

if __name__ == "__main__":
    detailed_need_analysis()
    check_heatmap_calculation_logic()