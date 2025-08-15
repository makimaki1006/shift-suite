#!/usr/bin/env python3
"""
全parquetファイルからroleカラムを探索
"""

import pandas as pd
from pathlib import Path

def find_role_column():
    """全parquetファイルでroleカラムの存在を確認"""
    
    base_dir = Path("extracted_results/out_p25_based")
    parquet_files = list(base_dir.glob("*.parquet"))
    
    print(f"調査対象ファイル数: {len(parquet_files)}")
    
    role_found_files = []
    
    for pq_file in parquet_files:
        try:
            df = pd.read_parquet(pq_file)
            
            # カラムにroleがあるかチェック
            has_role_column = 'role' in df.columns
            
            # reset_index後にroleがあるかチェック  
            df_reset = df.reset_index()
            has_role_after_reset = 'role' in df_reset.columns
            
            if has_role_column or has_role_after_reset:
                role_found_files.append(pq_file.name)
                print(f"\n*** ROLE FOUND: {pq_file.name} ***")
                print(f"  形状: {df.shape}")
                if has_role_column:
                    print(f"  カラムにrole: あり")
                    roles = df['role'].unique()[:10]
                    print(f"  職種例: {list(roles)}")
                if has_role_after_reset:
                    print(f"  reset後にrole: あり")
                    roles = df_reset['role'].unique()[:10]
                    print(f"  職種例: {list(roles)}")
                    
                # データ構造も表示
                print(f"  インデックス: {df.index.names}")
                print(f"  カラム: {list(df.columns)[:5]}...")
                
            else:
                print(f"  {pq_file.name}: role未発見")
                
        except Exception as e:
            print(f"  ERROR {pq_file.name}: {e}")
    
    print(f"\n=== 結果 ===")
    print(f"roleカラムが見つかったファイル: {len(role_found_files)}個")
    for f in role_found_files:
        print(f"  - {f}")

if __name__ == "__main__":
    find_role_column()