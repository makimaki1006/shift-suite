#!/usr/bin/env python3
"""
analysis_results (17).zipファイルの内容を詳しく調査するスクリプト
特に明け番データとヒートマップの状況を確認
"""

import zipfile
import pandas as pd
import json
from io import BytesIO
import os
from datetime import datetime

def investigate_zip_contents(zip_path):
    """ZIPファイルの内容を詳しく調査"""
    
    print(f"=== {zip_path} の調査開始 ===\n")
    
    if not os.path.exists(zip_path):
        print(f"エラー: {zip_path} が見つかりません")
        return
    
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        # 1. ファイル構造の確認
        print("1. ZIPファイル内のファイル構造:")
        print("-" * 50)
        file_list = zip_file.namelist()
        for file_name in sorted(file_list):
            file_info = zip_file.getinfo(file_name)
            size_mb = file_info.file_size / 1024 / 1024
            print(f"  {file_name} ({size_mb:.2f} MB)")
        
        # 2. ヒートマップ関連ファイルの確認
        print("\n2. ヒートマップ関連ファイル:")
        print("-" * 50)
        heatmap_files = [f for f in file_list if 'heat' in f.lower() and f.endswith('.parquet')]
        
        if not heatmap_files:
            print("  ヒートマップファイルが見つかりません")
        else:
            for heatmap_file in heatmap_files:
                print(f"\n  分析中: {heatmap_file}")
                
                # Parquetファイルを読み込む
                with zip_file.open(heatmap_file) as f:
                    df = pd.read_parquet(BytesIO(f.read()))
                
                print(f"    データ形状: {df.shape}")
                print(f"    カラム: {list(df.columns)}")
                
                # 時間帯の確認
                if 'hour' in df.columns:
                    print(f"    時間帯の範囲: {df['hour'].min()} - {df['hour'].max()}")
                    print(f"    ユニークな時間帯: {sorted(df['hour'].unique())}")
                    
                    # 明け番時間帯（0-9時）のデータ確認
                    akebann_hours = df[df['hour'].isin(range(0, 10))]
                    print(f"    明け番時間帯(0-9時)のレコード数: {len(akebann_hours)}")
                    
                    if len(akebann_hours) > 0:
                        print("    明け番時間帯のデータサンプル:")
                        print(akebann_hours.head())
                
                # 役割と時間帯の組み合わせ確認
                if 'role' in df.columns and 'hour' in df.columns:
                    print("\n    役割別の時間帯カバレッジ:")
                    role_hour_coverage = df.groupby('role')['hour'].agg(['min', 'max', 'nunique', lambda x: sorted(x.unique())])
                    role_hour_coverage.columns = ['最小時間', '最大時間', 'ユニーク時間数', '時間帯リスト']
                    print(role_hour_coverage)
                
                # ackShift列の確認
                if 'ackShift' in df.columns:
                    print(f"\n    ackShift列の値: {df['ackShift'].unique()}")
                    ack_shift_counts = df['ackShift'].value_counts()
                    print("    ackShift別レコード数:")
                    print(ack_shift_counts)
                    
                    # 明け番データの詳細確認
                    akebann_data = df[df['ackShift'] == True]
                    if len(akebann_data) > 0:
                        print(f"\n    明け番データのレコード数: {len(akebann_data)}")
                        if 'hour' in akebann_data.columns:
                            print(f"    明け番の時間帯: {sorted(akebann_data['hour'].unique())}")
                        if 'role' in akebann_data.columns:
                            print(f"    明け番の役割: {akebann_data['role'].unique()}")
        
        # 3. 元データファイルの確認
        print("\n3. 元データファイルの確認:")
        print("-" * 50)
        excel_files = [f for f in file_list if f.endswith('.xlsx')]
        
        for excel_file in excel_files:
            print(f"\n  {excel_file}:")
            with zip_file.open(excel_file) as f:
                excel_data = pd.ExcelFile(BytesIO(f.read()))
                print(f"    シート名: {excel_data.sheet_names}")
                
                # 最初のシートの内容を確認
                if excel_data.sheet_names:
                    df = pd.read_excel(BytesIO(f.read()), sheet_name=excel_data.sheet_names[0])
                    print(f"    データ形状: {df.shape}")
                    print(f"    カラム: {list(df.columns)[:10]}...")  # 最初の10カラムのみ表示
        
        # 4. JSONファイルの確認
        print("\n4. JSONファイルの確認:")
        print("-" * 50)
        json_files = [f for f in file_list if f.endswith('.json')]
        
        for json_file in json_files:
            print(f"\n  {json_file}:")
            with zip_file.open(json_file) as f:
                data = json.loads(f.read().decode('utf-8'))
                if isinstance(data, dict):
                    print(f"    キー: {list(data.keys())}")
                    # 明け番関連の設定を探す
                    for key in data.keys():
                        if 'ake' in key.lower() or 'morning' in key.lower():
                            print(f"    {key}: {data[key]}")
        
        # 5. 可視化結果の確認
        print("\n5. 可視化結果（画像ファイル）:")
        print("-" * 50)
        image_files = [f for f in file_list if f.endswith(('.png', '.jpg', '.jpeg'))]
        
        for img_file in image_files:
            print(f"  {img_file}")
            # 明け番関連の画像を特定
            if 'ake' in img_file.lower() or '明け' in img_file or 'morning' in img_file.lower():
                print(f"    → 明け番関連の可能性あり")

if __name__ == "__main__":
    # ZIPファイルのパス
    zip_path = "analysis_results (17).zip"
    
    # 調査実行
    investigate_zip_contents(zip_path)