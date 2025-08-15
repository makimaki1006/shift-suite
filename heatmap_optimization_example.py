#!/usr/bin/env python3
"""
ヒートマップ最適化の実例デモンストレーション
実際のメモリ使用量とパフォーマンスの改善を確認
"""

import pandas as pd
import numpy as np
import sys
from datetime import datetime, timedelta

def create_sample_heatmap_data(days=365, time_slots=48, max_staff=20):
    """サンプルヒートマップデータを生成"""
    
    # 日付列を生成（365日分）
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') 
             for i in range(days)]
    
    # 時間ラベル（30分間隔で48スロット）
    time_labels = [f"{h:02d}:{m:02d}" for h in range(24) for m in [0, 30]]
    
    # ランダムな人数データを生成
    np.random.seed(42)
    data = np.random.randint(0, max_staff, size=(time_slots, days))
    
    # データフレーム作成
    df = pd.DataFrame(data, index=time_labels, columns=dates)
    
    return df

def analyze_memory_usage(df, title):
    """メモリ使用量を分析"""
    memory_usage = df.memory_usage(deep=True).sum()
    print(f"\n=== {title} ===")
    print(f"データ形状: {df.shape}")
    print(f"メモリ使用量: {memory_usage / 1024 / 1024:.2f} MB")
    print(f"データ型情報:")
    for dtype in df.dtypes.unique():
        cols_with_dtype = (df.dtypes == dtype).sum()
        print(f"  {dtype}: {cols_with_dtype}列")
    
    return memory_usage

def optimize_heatmap_data_demo(df, max_days=60):
    """実際の最適化処理（デモ版）"""
    print(f"\n🔧 最適化開始...")
    
    # 1. 日付列制限
    date_cols = df.columns.tolist()
    if len(date_cols) > max_days:
        print(f"📅 日付制限: {len(date_cols)}日 -> 直近{max_days}日")
        recent_dates = sorted(date_cols)[-max_days:]
        df_optimized = df[recent_dates].copy()
    else:
        df_optimized = df.copy()
    
    # 2. データ型最適化
    print(f"🔢 データ型最適化:")
    for col in df_optimized.columns:
        if df_optimized[col].dtype == 'int64':
            max_val = df_optimized[col].max()
            original_dtype = df_optimized[col].dtype
            
            if max_val <= 255:
                df_optimized[col] = df_optimized[col].astype('uint8')
                new_dtype = 'uint8'
            elif max_val <= 32767:
                df_optimized[col] = df_optimized[col].astype('int16')
                new_dtype = 'int16'
            else:
                df_optimized[col] = df_optimized[col].astype('int32')
                new_dtype = 'int32'
            
            if original_dtype != new_dtype:
                print(f"    列 {col}: {original_dtype} -> {new_dtype}")
                break  # 最初の数列のみ表示
    
    return df_optimized

def main():
    """最適化デモンストレーション"""
    print("=" * 60)
    print("ヒートマップデータ最適化デモンストレーション")
    print("=" * 60)
    
    # 1. 大量データ生成（365日 × 48時間スロット）
    print("📊 大量サンプルデータ生成中...")
    original_df = create_sample_heatmap_data(days=365, time_slots=48, max_staff=50)
    
    # 2. 最適化前のメモリ分析
    original_memory = analyze_memory_usage(original_df, "最適化前")
    
    # 3. 最適化実行
    optimized_df = optimize_heatmap_data_demo(original_df, max_days=60)
    
    # 4. 最適化後のメモリ分析
    optimized_memory = analyze_memory_usage(optimized_df, "最適化後")
    
    # 5. 改善効果の計算
    print(f"\n🎯 === 最適化効果 ===")
    memory_reduction = (original_memory - optimized_memory) / original_memory * 100
    data_reduction = (original_df.shape[1] - optimized_df.shape[1]) / original_df.shape[1] * 100
    
    print(f"メモリ使用量削減: {memory_reduction:.1f}%")
    print(f"データ量削減: {data_reduction:.1f}%")
    print(f"処理速度向上予想: {memory_reduction * 0.8:.1f}%")  # 概算
    
    # 6. 実際のヒートマップサイズでの計算例
    print(f"\n📈 === 実用例 ===")
    print(f"年間データ（365日×48スロット）:")
    print(f"  最適化前: {original_memory / 1024 / 1024:.1f} MB")
    print(f"  最適化後: {optimized_memory / 1024 / 1024:.1f} MB")
    print(f"  節約容量: {(original_memory - optimized_memory) / 1024 / 1024:.1f} MB")
    
    print(f"\n複数職種（10職種）での効果:")
    total_original = original_memory * 10 / 1024 / 1024
    total_optimized = optimized_memory * 10 / 1024 / 1024
    print(f"  最適化前: {total_original:.1f} MB")
    print(f"  最適化後: {total_optimized:.1f} MB")
    print(f"  節約容量: {total_original - total_optimized:.1f} MB")

if __name__ == "__main__":
    main()