#!/usr/bin/env python3
"""
需要データ構造調査
need_per_date_slot_role_*.parquetファイルが0になっている原因調査
"""

import pandas as pd
import numpy as np
from pathlib import Path

def investigate_need_data_structure():
    """需要データ構造の詳細調査"""
    
    print("=" * 80)
    print("需要データ構造詳細調査")
    print("=" * 80)
    
    scenario_dir = Path("extracted_results/out_p25_based")
    if not scenario_dir.exists():
        print(f"ERROR: シナリオディレクトリが存在しません: {scenario_dir}")
        return
    
    # 1. 介護関連需要ファイルの詳細分析
    print("\n【STEP 1: 介護関連需要ファイル詳細分析】")
    
    need_files = list(scenario_dir.glob("need_per_date_slot_role_*.parquet"))
    care_need_files = [f for f in need_files if '介護' in f.name]
    
    print(f"介護関連需要ファイル数: {len(care_need_files)}")
    
    for i, need_file in enumerate(care_need_files):
        print(f"\n--- ファイル{i+1}: {need_file.name} ---")
        
        try:
            df = pd.read_parquet(need_file)
            print(f"データ形状: {df.shape}")
            print(f"インデックス: {df.index}")
            print(f"カラム: {list(df.columns)}")
            
            # データ型確認
            print(f"\nデータ型:")
            for col in df.columns[:10]:  # 最初の10カラム
                dtype = df[col].dtype
                non_null = df[col].count()
                print(f"  {col}: {dtype} (非NULL: {non_null})")
            
            # 統計情報
            print(f"\nデータ統計:")
            print(f"  全カラム数: {len(df.columns)}")
            print(f"  数値カラム数: {len(df.select_dtypes(include=[np.number]).columns)}")
            
            # 数値データの詳細確認
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                total_sum = df[numeric_cols].sum().sum()
                max_val = df[numeric_cols].max().max()
                min_val = df[numeric_cols].min().min()
                print(f"  数値データ合計: {total_sum}")
                print(f"  最大値: {max_val}")
                print(f"  最小値: {min_val}")
                
                # 0でないカラムの探索
                non_zero_cols = []
                for col in numeric_cols:
                    col_sum = df[col].sum()
                    if col_sum > 0:
                        non_zero_cols.append((col, col_sum))
                
                if non_zero_cols:
                    print(f"  0でないカラム: {len(non_zero_cols)}個")
                    for col, val in non_zero_cols[:5]:
                        print(f"    {col}: {val}")
                else:
                    print("  WARNING: すべてのカラムが0")
            
            # 実際のデータサンプル表示
            print(f"\nデータサンプル (最初3行、最初5列):")
            print(df.iloc[:3, :5])
            
            # ファイルサイズ確認
            file_size = need_file.stat().st_size
            print(f"ファイルサイズ: {file_size:,} bytes")
            
        except Exception as e:
            print(f"ERROR: ファイル読み込みエラー: {e}")
    
    # 2. 他の関連ファイルとの比較
    print(f"\n【STEP 2: 他の関連ファイルとの比較】")
    
    # shortage_time関連ファイルを確認
    shortage_files = list(scenario_dir.glob("shortage_time*.parquet"))
    print(f"shortage_time関連ファイル: {len(shortage_files)}個")
    
    for shortage_file in shortage_files[:3]:
        print(f"\n{shortage_file.name}:")
        try:
            df = pd.read_parquet(shortage_file)
            print(f"  形状: {df.shape}")
            print(f"  カラム例: {list(df.columns)[:5]}")
            
            # 数値データの合計
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                total = df[numeric_cols].sum().sum()
                print(f"  数値データ合計: {total}")
        except Exception as e:
            print(f"  ERROR: {e}")
    
    # role_kpi関連ファイルを確認
    role_kpi_files = list(scenario_dir.glob("role_kpi*.parquet"))
    print(f"\nrole_kpi関連ファイル: {len(role_kpi_files)}個")
    
    for kpi_file in role_kpi_files[:3]:
        print(f"\n{kpi_file.name}:")
        try:
            df = pd.read_parquet(kpi_file)
            print(f"  形状: {df.shape}")
            print(f"  カラム例: {list(df.columns)[:5]}")
            
            # 'need'関連カラムを探索
            need_cols = [col for col in df.columns if 'need' in col.lower()]
            shortage_cols = [col for col in df.columns if 'shortage' in col.lower()]
            
            if need_cols:
                print(f"  need関連カラム: {need_cols}")
                for col in need_cols:
                    val = df[col].sum() if col in df.columns else 0
                    print(f"    {col}: {val}")
            
            if shortage_cols:
                print(f"  shortage関連カラム: {shortage_cols}")
                for col in shortage_cols:
                    val = df[col].sum() if col in df.columns else 0
                    print(f"    {col}: {val}")
                    
        except Exception as e:
            print(f"  ERROR: {e}")
    
    # 3. intermediate_dataとの関係確認
    print(f"\n【STEP 3: intermediate_dataとの関係確認】")
    
    intermediate_file = scenario_dir / "intermediate_data.parquet"
    if intermediate_file.exists():
        try:
            df = pd.read_parquet(intermediate_file)
            print(f"intermediate_data形状: {df.shape}")
            
            # 介護関連データのサブセット
            if 'role' in df.columns:
                care_data = df[df['role'].str.contains('介護', na=False)]
                print(f"介護関連レコード: {len(care_data)}件")
                
                # 勤務関連カラムの確認
                work_cols = [col for col in df.columns if any(word in col.lower() for word in ['work', 'shift', '勤務', 'hour'])]
                if work_cols:
                    print(f"勤務関連カラム: {work_cols}")
                    
                # 時間関連の値を確認
                if 'ds' in df.columns and len(care_data) > 0:
                    print(f"期間: {df['ds'].min()} ～ {df['ds'].max()}")
                    
                    # 日別介護職員数
                    daily_care = care_data.groupby('ds').size()
                    print(f"日別介護職員数:")
                    print(f"  平均: {daily_care.mean():.1f}人/日")
                    print(f"  最大: {daily_care.max()}人/日")
                    print(f"  最小: {daily_care.min()}人/日")
                    
        except Exception as e:
            print(f"ERROR: intermediate_data読み込みエラー: {e}")
    
    # 4. 原因分析と推定
    print(f"\n【STEP 4: 原因分析と推定】")
    
    print("需要データが0になっている可能性:")
    print("1. データ生成プロセスでの問題")
    print("2. 異なるデータ構造（インデックスに需要データが含まれている可能性）")
    print("3. ファイル名パターンの不一致")
    print("4. 需要計算アルゴリズムの実行タイミング問題")
    
    print("\n推奨アクション:")
    print("- intermediate_dataから直接需要を推定")
    print("- role_kpiデータからshortage値を利用")
    print("- 勤務実績から標準的な需要率を適用")
    
    return True

if __name__ == "__main__":
    investigate_need_data_structure()