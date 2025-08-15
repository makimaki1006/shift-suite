#!/usr/bin/env python3
"""
特定のヒートマップデータを詳細確認
"""

import zipfile
import pandas as pd
from io import BytesIO

def check_specific_heatmap(zip_path):
    """特定のヒートマップファイルを詳細確認"""
    
    print(f"=== 特定ヒートマップデータ詳細分析 ===\n")
    
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        file_list = zip_file.namelist()
        
        # 2F看護のデータを確認
        target_files = [
            "out_mean_based/heat_2F看護.parquet",
            "out_mean_based/heat_ALL.parquet"
        ]
        
        for target_file in target_files:
            if target_file in file_list:
                print(f"\n{'='*60}")
                print(f"ファイル: {target_file}")
                print('='*60)
                
                with zip_file.open(target_file) as f:
                    df = pd.read_parquet(BytesIO(f.read()))
                
                print(f"データ形状: {df.shape}")
                print(f"カラム: {list(df.columns)}")
                print(f"インデックス: {list(df.index)[:10]}...")
                
                # 基本統計
                print(f"\n基本統計:")
                for col in ['need', 'staff', 'lack', 'excess']:
                    if col in df.columns:
                        print(f"{col}: min={df[col].min()}, max={df[col].max()}, mean={df[col].mean():.2f}")
                
                # 明け番時間帯の詳細（0:00-9:45）
                print(f"\n明け番時間帯 (0:00-9:45) の詳細データ:")
                print(f"{'時間':<8} {'need':<6} {'staff':<6} {'lack':<6} {'excess':<8}")
                print("-" * 40)
                
                # 30分ごとにサンプル表示
                for i in range(0, 40, 2):  # 0:00, 0:30, 1:00, ...
                    if i < len(df):
                        row = df.iloc[i]
                        time_slot = df.index[i]
                        need = row.get('need', 'N/A')
                        staff = row.get('staff', 'N/A') 
                        lack = row.get('lack', 'N/A')
                        excess = row.get('excess', 'N/A')
                        print(f"{time_slot:<8} {need:<6} {staff:<6} {lack:<6} {excess:<8}")
                
                # 日勤時間帯との比較（9:00-17:00）
                print(f"\n日勤時間帯 (9:00-17:00) のサンプルデータ:")
                print(f"{'時間':<8} {'need':<6} {'staff':<6} {'lack':<6} {'excess':<8}")
                print("-" * 40)
                
                day_start = 9 * 4  # 9:00 = 36番目
                day_end = 17 * 4   # 17:00 = 68番目
                
                for i in range(day_start, min(day_end, len(df)), 8):  # 2時間ごと
                    row = df.iloc[i]
                    time_slot = df.index[i]
                    need = row.get('need', 'N/A')
                    staff = row.get('staff', 'N/A')
                    lack = row.get('lack', 'N/A')
                    excess = row.get('excess', 'N/A')
                    print(f"{time_slot:<8} {need:<6} {staff:<6} {lack:<6} {excess:<8}")
                
                # 夜勤時間帯との比較（18:00-23:45）
                print(f"\n夜勤時間帯 (18:00-23:45) のサンプルデータ:")
                print(f"{'時間':<8} {'need':<6} {'staff':<6} {'lack':<6} {'excess':<8}")
                print("-" * 40)
                
                night_start = 18 * 4  # 18:00 = 72番目
                
                for i in range(night_start, min(len(df), 96), 8):  # 2時間ごと
                    row = df.iloc[i]
                    time_slot = df.index[i]
                    need = row.get('need', 'N/A')
                    staff = row.get('staff', 'N/A')
                    lack = row.get('lack', 'N/A')
                    excess = row.get('excess', 'N/A')
                    print(f"{time_slot:<8} {need:<6} {staff:<6} {lack:<6} {excess:<8}")
                
                # 特定の日付カラムの確認
                date_columns = [col for col in df.columns if '2025-06' in str(col)]
                if date_columns:
                    print(f"\n日付別データサンプル (最初の日):")
                    first_date = date_columns[0]
                    print(f"日付: {first_date}")
                    print(f"明け番時間帯の値:")
                    for i in range(0, 40, 4):  # 1時間ごと
                        if i < len(df):
                            time_slot = df.index[i]
                            value = df.iloc[i][first_date]
                            print(f"  {time_slot}: {value}")
            else:
                print(f"\nファイルが見つかりません: {target_file}")

if __name__ == "__main__":
    zip_path = "analysis_results (17).zip"
    check_specific_heatmap(zip_path)