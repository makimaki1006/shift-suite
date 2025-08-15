#!/usr/bin/env python3
"""
正確な実データ調査 - roleカラムの詳細確認
ユーザー指摘を受けた再調査
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

def correct_real_data_investigation():
    """実データのroleカラム詳細確認"""
    
    print("=" * 80)
    print("正確な実データ調査 - roleカラム確認")
    print("=" * 80)
    
    base_dir = Path("extracted_results/out_p25_based")
    
    # 1. need_per_date_slot.parquet の詳細再調査
    print("\n【need_per_date_slot.parquet 再調査】")
    
    try:
        need_df = pd.read_parquet(base_dir / 'need_per_date_slot.parquet')
        print(f"データ形状: {need_df.shape}")
        
        # インデックスの詳細確認
        print(f"\nインデックス詳細:")
        print(f"  インデックス名: {need_df.index.name}")
        print(f"  インデックスのタイプ: {type(need_df.index)}")
        
        # インデックスがMultiIndexかどうか確認
        if hasattr(need_df.index, 'names'):
            print(f"  インデックスレベル数: {need_df.index.nlevels}")
            print(f"  インデックスレベル名: {need_df.index.names}")
            
            # MultiIndexの場合、各レベルを確認
            if need_df.index.nlevels > 1:
                for i, level_name in enumerate(need_df.index.names):
                    level_values = need_df.index.get_level_values(i).unique()
                    print(f"  レベル{i} ({level_name}): {list(level_values)[:5]}...")
                    
                    # roleがレベル名にあるか確認
                    if level_name == 'role':
                        print(f"    FOUND: roleレベルが存在!")
                        all_roles = list(level_values)
                        print(f"    全職種: {all_roles}")
        
        # インデックスの実際の値を確認
        print(f"\nインデックス値のサンプル:")
        for i in range(min(10, len(need_df))):
            print(f"  [{i}] {need_df.index[i]}")
            
        # reset_indexでroleカラムが出現するか確認
        print(f"\nreset_index()テスト:")
        reset_df = need_df.reset_index()
        print(f"  reset後の形状: {reset_df.shape}")
        print(f"  reset後のカラム: {list(reset_df.columns)}")
        
        if 'role' in reset_df.columns:
            print(f"  SUCCESS: roleカラムが発見されました!")
            roles = reset_df['role'].unique()
            print(f"  職種一覧: {list(roles)}")
            
            # 介護職種の確認
            care_roles = [role for role in roles if '介護' in str(role)]
            print(f"  介護関連職種: {care_roles}")
            
            return reset_df  # 正しいデータフレームを返す
        else:
            print(f"  WARNING: reset後もroleカラムが見つからない")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        print(traceback.format_exc())
    
    # 2. 他のファイルでのrole確認
    print("\n\n【他のファイルでのrole確認】")
    
    # work_patterns.parquetを確認
    work_patterns_path = base_dir / 'work_patterns.parquet'
    if work_patterns_path.exists():
        try:
            work_df = pd.read_parquet(work_patterns_path)
            print(f"work_patterns.parquet:")
            print(f"  形状: {work_df.shape}")
            print(f"  カラム: {list(work_df.columns)}")
            
            if 'role' in work_df.columns:
                print(f"  SUCCESS: work_patternsにroleカラム発見!")
                roles = work_df['role'].unique()
                print(f"  職種: {list(roles)[:10]}")
            else:
                work_reset = work_df.reset_index()
                if 'role' in work_reset.columns:
                    print(f"  SUCCESS: work_patterns(reset後)にroleカラム発見!")
                    
        except Exception as e:
            print(f"  ERROR: {e}")
    
    # attendance.csvを確認
    attendance_path = base_dir / 'attendance.csv'
    if attendance_path.exists():
        try:
            att_df = pd.read_csv(attendance_path)
            print(f"\nattendance.csv:")
            print(f"  形状: {att_df.shape}")
            print(f"  カラム: {list(att_df.columns)}")
            
            if 'role' in att_df.columns:
                print(f"  SUCCESS: attendanceにroleカラム発見!")
                roles = att_df['role'].unique()
                print(f"  職種: {list(roles)[:10]}")
                
        except Exception as e:
            print(f"  ERROR: {e}")
    
    # 3. 職種別ファイルを再確認
    print(f"\n\n【職種別ファイル再確認】")
    
    role_file = base_dir / 'need_per_date_slot_role_介護.parquet'
    if role_file.exists():
        try:
            care_df = pd.read_parquet(role_file)
            print(f"need_per_date_slot_role_介護.parquet:")
            print(f"  形状: {care_df.shape}")
            print(f"  カラム: {list(care_df.columns)}")
            print(f"  インデックス: {care_df.index.names}")
            
            # このファイル構造の確認
            if care_df.shape[0] > 0:
                print(f"  データサンプル:")
                print(care_df.head(3))
                
        except Exception as e:
            print(f"  ERROR: {e}")

if __name__ == "__main__":
    result = correct_real_data_investigation()
    print(f"\n最終結果: {'roleカラム発見' if result is not None else 'roleカラム未発見'}")