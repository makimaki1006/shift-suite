#!/usr/bin/env python3
"""
実データ構造の詳細調査
想定していた構造と実際の構造の差異を明確化
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

def investigate_actual_data_structure():
    """実データ構造の完全調査"""
    
    print("=" * 80)
    print("実データ構造詳細調査")
    print("=" * 80)
    
    base_dir = Path("extracted_results/out_p25_based")
    
    # 1. need_per_date_slot.parquet詳細調査
    print("\n【need_per_date_slot.parquet 構造調査】")
    
    try:
        need_df = pd.read_parquet(base_dir / 'need_per_date_slot.parquet')
        print(f"データ形状: {need_df.shape}")
        print(f"全カラム一覧:")
        for i, col in enumerate(need_df.columns):
            dtype = need_df[col].dtype
            sample_val = need_df[col].iloc[0] if len(need_df) > 0 else "N/A"
            print(f"  [{i:2d}] {col:15s} ({dtype:8s}) = {sample_val}")
        
        print(f"\nインデックス情報:")
        print(f"  インデックス名: {need_df.index.name}")
        print(f"  インデックス型: {type(need_df.index)}")
        print(f"  インデックス例: {list(need_df.index[:5])}")
        
        # データサンプル
        print(f"\n最初の3行:")
        print(need_df.head(3))
        
    except Exception as e:
        print(f"ERROR: {e}")
    
    # 2. 職種別ファイルの調査
    print("\n\n【職種別ファイル調査】")
    
    role_files = list(base_dir.glob("need_per_date_slot_role_*.parquet"))
    print(f"職種別ファイル数: {len(role_files)}")
    
    for role_file in role_files[:3]:  # 最初の3つのみ
        role_name = role_file.stem.replace("need_per_date_slot_role_", "")
        print(f"\n--- {role_name} ---")
        try:
            df = pd.read_parquet(role_file)
            print(f"  形状: {df.shape}")
            print(f"  カラム例: {list(df.columns[:5])}")
            print(f"  インデックス例: {list(df.index[:3])}")
            
            # データ値の例
            if df.shape[0] > 0 and df.shape[1] > 0:
                first_col = df.columns[0]
                sample_vals = df[first_col].head(3).tolist()
                print(f"  {first_col}の例: {sample_vals}")
                
        except Exception as e:
            print(f"  ERROR: {e}")
    
    # 3. staff系ファイルの確認
    print("\n\n【staff系ファイル確認】")
    
    staff_files = list(base_dir.glob("*staff*.parquet"))
    print(f"staff関連ファイル数: {len(staff_files)}")
    for staff_file in staff_files:
        print(f"  {staff_file.name}")
    
    # staff系ファイルがないか確認
    if not staff_files:
        print("  WARN: staff系ファイルが見つからない")
        print("  代替候補を探索中...")
        
        # working_data系ファイル探索
        working_files = list(base_dir.glob("*work*.parquet"))
        attendance_files = list(base_dir.glob("*attendance*.csv"))
        
        print(f"  working系ファイル: {len(working_files)}")
        for f in working_files:
            print(f"    {f.name}")
            
        print(f"  attendance系ファイル: {len(attendance_files)}")
        for f in attendance_files:
            print(f"    {f.name}")
    
    # 4. メタデータとの関連調査
    print("\n\n【メタデータとの関連性】")
    
    try:
        with open(base_dir / 'heatmap.meta.json', 'r', encoding='utf-8') as f:
            meta_data = json.load(f)
        
        print(f"メタデータ職種: {meta_data.get('roles', [])}")
        print(f"期間情報: {meta_data.get('dates', [])[:5]}...")
        print(f"スロット: {meta_data.get('slot', 'N/A')}")
        
        # 実際の職種別ファイルとの比較
        actual_role_files = [f.stem.replace("need_per_date_slot_role_", "") 
                           for f in role_files]
        meta_roles = meta_data.get('roles', [])
        
        print(f"実ファイル職種: {actual_role_files}")
        print(f"メタ職種と実ファイルの一致:")
        for role in meta_roles:
            exists = role in actual_role_files
            print(f"  {role}: {'OK' if exists else 'MISSING'}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    # 5. データ構造の結論
    print("\n\n【データ構造分析結果】")
    
    print("判明した実際の構造:")
    print("1. need_per_date_slot.parquet:")
    print("   - roleカラムは存在しない")  
    print("   - 日付がカラム名になっている")
    print("   - インデックスに何かしらの識別子")
    print("   - 48行×30列 (時間帯×日付？)")
    
    print("\n2. 職種別データ:")
    print("   - need_per_date_slot_role_<職種名>.parquet として分離")
    print("   - 各職種ごとに独立したファイル")
    
    print("\n3. staffデータ:")
    print("   - staff_per_date_slot.parquet は存在しない可能性")
    print("   - attendance.csv や work系ファイルが代替候補")
    
    print("\n【職種別詳細分析への影響】")
    print("CRITICAL: 想定していた統合データ構造と完全に異なる")
    print("必要な修正:")
    print("1. 職種別ファイルを個別に読み込む必要")
    print("2. staffデータの所在確認・代替策検討") 
    print("3. データ結合・統合ロジックの全面見直し")
    print("4. occupation_specific_calculator.pyの大幅修正")
    
    print("\nリスク評価: 高")
    print("Phase 2進行推奨: 一時停止 → 設計見直し必要")

if __name__ == "__main__":
    investigate_actual_data_structure()