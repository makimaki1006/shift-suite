#!/usr/bin/env python3
"""
シンプルなデータ確認
CSVに変換して最初の数行を確認
"""

import subprocess
import sys
from pathlib import Path

def check_parquet_data():
    """parquetファイルの内容確認"""
    
    # パスを探す
    parquet_files = [
        "./temp_analysis_check/out_median_based/shortage_role_summary.parquet",
        "./median_based/shortage_role_summary.parquet",
        "./mean_based/shortage_role_summary.parquet",
    ]
    
    found_file = None
    for pf in parquet_files:
        if Path(pf).exists():
            found_file = pf
            break
    
    if not found_file:
        print("❌ shortage_role_summary.parquet が見つかりません")
        return
    
    print(f"✅ ファイル発見: {found_file}")
    
    # pandasを使わずに確認する方法を試す
    try:
        # pyarrowで直接読む
        import pyarrow.parquet as pq
        
        table = pq.read_table(found_file)
        df = table.to_pandas()
        
        print("\n【データ概要】")
        print(f"行数: {len(df)}")
        print(f"カラム: {df.columns.tolist()}")
        
        if 'lack_h' in df.columns:
            print(f"\n【lack_h カラムの統計】")
            print(f"最小値: {df['lack_h'].min():.2f}")
            print(f"最大値: {df['lack_h'].max():.2f}")
            print(f"平均値: {df['lack_h'].mean():.2f}")
            print(f"合計値: {df['lack_h'].sum():.2f}")
            
            print("\n【最初の5行】")
            print(df[['role', 'lack_h', 'need_h', 'staff_h']].head())
            
            # 値の桁数チェック
            max_val = df['lack_h'].max()
            if max_val > 10000:
                print(f"\n⚠️ 警告: lack_h の最大値 {max_val:.2f} は異常に大きいです")
                print("→ スロット数が誤って時間として扱われている可能性があります")
                
                # スロット時間での換算を試算
                for slot_minutes in [15, 30, 60]:
                    estimated_hours = max_val / (60 / slot_minutes)
                    print(f"  {slot_minutes}分スロットとすると: {estimated_hours:.2f}時間")
        
    except ImportError:
        print("❌ pyarrowが利用できません")
        # CSVに変換して確認する代替案
        print("\nparquetファイルの内容を直接確認できません")

if __name__ == "__main__":
    check_parquet_data()