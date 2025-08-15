#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parsed_slots_countの実データ検証
緊急対応: 二重変換問題の解決のための実データ調査
"""

import pandas as pd
from pathlib import Path

def verify_parsed_slots_count_meaning():
    """parsed_slots_countの意味を実データで検証"""
    
    print("🔍 parsed_slots_count実データ検証")
    print("=" * 80)
    
    # temp_analysis_checkディレクトリのintermediate_data.parquetを調査
    data_files = [
        "temp_analysis_check/out_mean_based/intermediate_data.parquet",
        "temp_analysis_check/out_median_based/intermediate_data.parquet", 
        "temp_analysis_check/out_p25_based/intermediate_data.parquet"
    ]
    
    for i, file_path in enumerate(data_files):
        path = Path(file_path)
        if path.exists():
            print(f"\n📊 分析{i+1}: {file_path}")
            try:
                df = pd.read_parquet(path)
                analyze_dataframe_structure(df, file_path)
                if i == 0:  # 最初のファイルで詳細分析
                    analyze_parsed_slots_count_values(df)
                break
            except Exception as e:
                print(f"  ❌ 読み込みエラー: {e}")
        else:
            print(f"  ❌ ファイル不存在: {file_path}")

def analyze_dataframe_structure(df, file_path):
    """DataFrameの構造分析"""
    
    print(f"  📋 データ構造:")
    print(f"    行数: {len(df):,}")
    print(f"    列数: {len(df.columns)}")
    print(f"    メモリ使用量: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    
    print(f"\n  📝 カラム一覧:")
    for col in df.columns:
        dtype = df[col].dtype
        non_null = df[col].count()
        print(f"    {col}: {dtype} ({non_null:,}/{len(df):,} 非null)")
    
    # parsed_slots_countの存在確認
    if 'parsed_slots_count' in df.columns:
        print(f"\n  ✅ parsed_slots_countカラムが存在")
    else:
        print(f"\n  ❌ parsed_slots_countカラムが存在しません")
        print(f"    利用可能なカラム: {list(df.columns)}")

def analyze_parsed_slots_count_values(df):
    """parsed_slots_countの値の詳細分析"""
    
    if 'parsed_slots_count' not in df.columns:
        print("  ❌ parsed_slots_countカラムが存在しないため、分析をスキップします")
        return
    
    print(f"\n🔍 parsed_slots_count詳細分析:")
    
    # 基本統計
    series = df['parsed_slots_count']
    print(f"  📊 基本統計:")
    print(f"    データ型: {series.dtype}")
    print(f"    総レコード数: {len(series):,}")
    print(f"    非null数: {series.count():,}")
    print(f"    最小値: {series.min()}")
    print(f"    最大値: {series.max()}")
    print(f"    平均値: {series.mean():.3f}")
    print(f"    中央値: {series.median():.3f}")
    print(f"    標準偏差: {series.std():.3f}")
    
    # 値の分布分析
    print(f"\n  📈 値の分布:")
    value_counts = series.value_counts().head(20)
    print(f"    上位20の値の出現回数:")
    for value, count in value_counts.items():
        percentage = (count / len(series)) * 100
        print(f"      {value}: {count:,}回 ({percentage:.2f}%)")
    
    # スロット数仮説の検証
    print(f"\n  🧪 スロット数仮説の検証:")
    
    # 30分刻み（スロット数）の仮説
    slot_hypothesis_values = [0.5, 1, 1.5, 2, 2.5, 3, 4, 8, 16]  # 30分〜8時間
    time_hypothesis_values = [0.5, 1, 1.5, 2, 2.5, 3, 4, 8, 16]  # 同じ値だが時間単位
    
    print(f"    30分刻み（スロット数）仮説:")
    for slot_val in slot_hypothesis_values:
        count = (series == slot_val).sum()
        if count > 0:
            percentage = (count / len(series)) * 100
            print(f"      {slot_val}スロット: {count:,}回 ({percentage:.2f}%)")
    
    # 整数値の比率
    integer_values = series[series == series.astype(int)]
    integer_ratio = len(integer_values) / len(series) * 100
    print(f"\n    整数値の比率: {integer_ratio:.2f}%")
    
    if integer_ratio > 90:
        print(f"      → スロット数（30分刻み）の可能性が高い")
    elif integer_ratio < 10:
        print(f"      → 時間値（小数点）の可能性が高い")
    else:
        print(f"      → 混在している可能性")
    
    # 実際の時間換算テスト
    print(f"\n  ⚖️ 時間換算テスト:")
    
    # ケース1: 既にスロット数として扱い、0.5を乗算
    case1_hours = series * 0.5
    print(f"    ケース1 (スロット数 × 0.5): 平均 {case1_hours.mean():.2f}時間/レコード")
    
    # ケース2: 既に時間値として扱い、そのまま使用
    case2_hours = series
    print(f"    ケース2 (そのまま時間値): 平均 {case2_hours.mean():.2f}時間/レコード")
    
    # 妥当性判定
    print(f"\n  💡 妥当性判定:")
    avg_case1 = case1_hours.mean()
    avg_case2 = case2_hours.mean()
    
    # 1レコードあたりの時間として妥当な範囲: 0.25〜8時間
    if 0.25 <= avg_case1 <= 8:
        print(f"    ✅ ケース1が妥当: 1レコード平均{avg_case1:.2f}時間")
    else:
        print(f"    ❌ ケース1は非妥当: 1レコード平均{avg_case1:.2f}時間")
    
    if 0.25 <= avg_case2 <= 8:
        print(f"    ✅ ケース2が妥当: 1レコード平均{avg_case2:.2f}時間")
    else:
        print(f"    ❌ ケース2は非妥当: 1レコード平均{avg_case2:.2f}時間")

def check_related_files():
    """関連ファイルでの時間データ確認"""
    
    print(f"\n📁 関連ファイルでの時間データ確認:")
    
    # shortage_time.parquetの確認
    shortage_files = [
        "temp_analysis_check/out_mean_based/shortage_time.parquet",
        "temp_analysis_check/out_mean_based/shortage_role_summary.parquet"
    ]
    
    for file_path in shortage_files:
        path = Path(file_path)
        if path.exists():
            print(f"\n  📊 {file_path}:")
            try:
                df = pd.read_parquet(path)
                print(f"    データ形状: {df.shape}")
                print(f"    カラム: {list(df.columns)}")
                
                # 数値カラムの統計
                numeric_cols = df.select_dtypes(include=['number']).columns
                for col in numeric_cols:
                    if 'lack' in col.lower() or 'shortage' in col.lower() or 'hour' in col.lower():
                        series = df[col]
                        print(f"    {col}: 平均 {series.mean():.2f}, 最大 {series.max():.2f}")
                        
            except Exception as e:
                print(f"    ❌ 読み込みエラー: {e}")

if __name__ == "__main__":
    print("🚨 緊急検証: parsed_slots_countの意味確認")
    print("二重変換問題の解決のため実データを調査します...")
    
    verify_parsed_slots_count_meaning()
    check_related_files()
    
    print(f"\n📋 検証まとめ:")
    print("1. parsed_slots_countの値の分布と型を確認")
    print("2. スロット数仮説 vs 時間値仮説を検証")
    print("3. 既存のshortage計算結果と照合")
    print("4. Phase 2/3.1の計算ロジック修正方針を決定")
    print("\n✅ 緊急検証完了")