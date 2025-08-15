#!/usr/bin/env python3
"""
motogi_short.zipの元データを詳細に調査
"""

import pandas as pd
from pathlib import Path
import json

def investigate_original_data():
    """motogi_short.zipの元データを調査"""
    
    print("=== motogi_short.zip 元データ調査 ===")
    
    # motogi_short.zipの中のメタデータを確認
    import os
    base_path = Path("/tmp/tmpdl5z1z7n/motogi_short/out_median_based")
    print(f"チェックパス: {base_path}")
    print(f"存在確認: {base_path.exists()}")
    
    if not base_path.exists():
        print(f"ERROR: Path not found: {base_path}")
        return
    
    # pre_aggregated_data.parquetを確認
    pre_agg_path = base_path / "pre_aggregated_data.parquet"
    if pre_agg_path.exists():
        print("\n--- pre_aggregated_data.parquet 分析 ---")
        df = pd.read_parquet(pre_agg_path)
        print(f"Shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        
        # コード列がある場合
        if 'code' in df.columns:
            code_counts = df['code'].value_counts()
            print(f"\nコード使用頻度:")
            for code, count in code_counts.head(20).items():
                print(f"  '{code}': {count}回")
            
            # 明番コード「●」の存在確認
            dawn_mask = df['code'] == '●'
            dawn_count = dawn_mask.sum()
            print(f"\n明番コード「●」のレコード数: {dawn_count}")
            
            if dawn_count > 0:
                print("明番コード「●」のサンプルデータ:")
                print(df[dawn_mask].head())
        
        # 夜勤時間帯のデータ確認
        if 'ds' in df.columns:
            df['hour'] = pd.to_datetime(df['ds']).dt.hour
            night_hours = [0, 1, 2, 3, 4, 5]
            night_mask = df['hour'].isin(night_hours)
            night_df = df[night_mask]
            
            print(f"\n夜勤時間帯（0-6時）のデータ:")
            print(f"  総レコード数: {len(night_df)}")
            
            if 'code' in night_df.columns:
                night_codes = night_df['code'].value_counts()
                print(f"  コード分布:")
                for code, count in night_codes.items():
                    print(f"    '{code}': {count}回")
    
    # shortage.meta.jsonを確認
    meta_path = base_path / "shortage.meta.json"
    if meta_path.exists():
        print("\n--- shortage.meta.json 分析 ---")
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta_data = json.load(f)
        
        if 'night_shift_info' in meta_data:
            print("夜勤情報:")
            print(json.dumps(meta_data['night_shift_info'], indent=2, ensure_ascii=False))
    
    # intermediate_data.parquetを確認
    intermediate_path = base_path / "intermediate_data.parquet"
    if intermediate_path.exists():
        print("\n--- intermediate_data.parquet 分析 ---")
        df = pd.read_parquet(intermediate_path)
        print(f"Shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        
        if 'shift_code' in df.columns:
            shift_codes = df['shift_code'].value_counts()
            print(f"\nシフトコード分布:")
            for code, count in shift_codes.head(10).items():
                print(f"  '{code}': {count}回")
    
    # need_per_date_slot.parquetを確認
    need_path = base_path / "need_per_date_slot.parquet"
    if need_path.exists():
        print("\n--- need_per_date_slot.parquet 分析 ---")
        df = pd.read_parquet(need_path)
        print(f"Shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        
        # 夜勤時間帯の必要人数を確認
        if 'slot' in df.columns:
            night_slots = ['00:00', '00:30', '01:00', '01:30', '02:00', '02:30', 
                          '03:00', '03:30', '04:00', '04:30', '05:00', '05:30']
            night_mask = df['slot'].isin(night_slots)
            night_need_df = df[night_mask]
            
            if 'required' in night_need_df.columns:
                print(f"\n夜勤時間帯の必要人数:")
                print(f"  平均: {night_need_df['required'].mean():.2f}人")
                print(f"  最大: {night_need_df['required'].max()}人")
                print(f"  最小: {night_need_df['required'].min()}人")
    
    print("\n=== 調査完了 ===")

if __name__ == "__main__":
    investigate_original_data()