#!/usr/bin/env python3
"""
Dashヒートマップの休日除外問題確認スクリプト
"""

import pandas as pd
import os
import sys
from pathlib import Path

def check_data_files():
    """データファイルの休日除外状況を確認"""
    print("="*70)
    print("🔍 Dashヒートマップ休日除外問題の確認")
    print("="*70)
    
    # 最新の分析結果ディレクトリを探す
    analysis_dirs = list(Path(".").glob("analysis_results*"))
    if not analysis_dirs:
        print("❌ analysis_resultsディレクトリが見つかりません")
        return
    
    latest_dir = max(analysis_dirs, key=os.path.getmtime)
    print(f"📁 最新の分析結果: {latest_dir}")
    
    # outディレクトリ内のシナリオを確認
    out_dir = latest_dir / "out"
    if not out_dir.exists():
        print("❌ outディレクトリが見つかりません")
        return
    
    scenarios = list(out_dir.glob("out_*"))
    print(f"\n📊 シナリオ数: {len(scenarios)}")
    
    for scenario_dir in scenarios[:1]:  # 最初のシナリオのみチェック
        print(f"\n🔸 シナリオ: {scenario_dir.name}")
        
        # 1. heat_ALL.parquetの確認
        heat_all_path = scenario_dir / "heat_ALL.parquet"
        if heat_all_path.exists():
            try:
                df = pd.read_parquet(heat_all_path)
                print(f"\n📈 heat_ALL.parquet:")
                print(f"  - 総レコード数: {len(df)}")
                
                # 日付列を確認
                date_cols = [c for c in df.columns if c not in ['time', 'hour', 'minute']]
                if date_cols:
                    # 各日付列の合計値を確認
                    total_staff = df[date_cols].sum().sum()
                    avg_per_slot = total_staff / len(df) if len(df) > 0 else 0
                    print(f"  - 日付列数: {len(date_cols)}")
                    print(f"  - 総スタッフ数: {total_staff}")
                    print(f"  - 平均スタッフ数/スロット: {avg_per_slot:.2f}")
                    
                    # 0値の割合を確認
                    zero_count = (df[date_cols] == 0).sum().sum()
                    zero_ratio = zero_count / (len(df) * len(date_cols)) * 100
                    print(f"  - 0値の割合: {zero_ratio:.1f}%")
                    
                    # サンプルデータ表示
                    print(f"\n  サンプルデータ（最初の5行、3列）:")
                    sample_cols = ['time'] + date_cols[:2]
                    print(df[sample_cols].head())
                    
            except Exception as e:
                print(f"  ❌ エラー: {e}")
        
        # 2. pre_aggregated_data.parquetの確認
        pre_agg_path = scenario_dir / "pre_aggregated_data.parquet"
        if pre_agg_path.exists():
            try:
                df = pd.read_parquet(pre_agg_path)
                print(f"\n📊 pre_aggregated_data.parquet:")
                print(f"  - 総レコード数: {len(df)}")
                
                if 'staff_count' in df.columns:
                    # staff_count = 0のレコード数
                    zero_staff = (df['staff_count'] == 0).sum()
                    print(f"  - staff_count = 0 のレコード数: {zero_staff}")
                    print(f"  - staff_count = 0 の割合: {zero_staff/len(df)*100:.1f}%")
                    
                    # 平均staff_count
                    avg_staff = df['staff_count'].mean()
                    print(f"  - 平均staff_count: {avg_staff:.2f}")
                    
                    # parsed_slots_countがある場合
                    if 'parsed_slots_count' in df.columns:
                        zero_slots = (df['parsed_slots_count'] == 0).sum()
                        print(f"  - parsed_slots_count = 0 のレコード数: {zero_slots}")
                    
                    # holiday_typeがある場合
                    if 'holiday_type' in df.columns:
                        holiday_counts = df['holiday_type'].value_counts()
                        print(f"\n  holiday_type別カウント:")
                        for htype, count in holiday_counts.items():
                            print(f"    - {htype}: {count}")
                    
            except Exception as e:
                print(f"  ❌ エラー: {e}")
        
        # 3. intermediate_data.parquetの確認
        inter_path = scenario_dir / "intermediate_data.parquet"
        if inter_path.exists():
            try:
                df = pd.read_parquet(inter_path)
                print(f"\n📋 intermediate_data.parquet:")
                print(f"  - 総レコード数: {len(df)}")
                
                if 'parsed_slots_count' in df.columns:
                    zero_slots = (df['parsed_slots_count'] == 0).sum()
                    print(f"  - parsed_slots_count = 0 のレコード数: {zero_slots}")
                    print(f"  - parsed_slots_count = 0 の割合: {zero_slots/len(df)*100:.1f}%")
                
                if 'code' in df.columns:
                    # 休暇コードの確認
                    rest_codes = ['×', 'X', 'x', '休', 'OFF', 'off', '有', '欠']
                    rest_count = df[df['code'].isin(rest_codes)].shape[0]
                    print(f"  - 休暇コード該当レコード数: {rest_count}")
                    
            except Exception as e:
                print(f"  ❌ エラー: {e}")
    
    print("\n" + "="*70)
    print("💡 確認結果:")
    print("  - heat_ALL.parquetに休日データが含まれている可能性")
    print("  - pre_aggregated_dataにstaff_count=0のレコードが残存")
    print("  - 根本的な休日除外が不完全な可能性")
    print("="*70)

if __name__ == "__main__":
    check_data_files()