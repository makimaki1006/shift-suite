#!/usr/bin/env python3
"""
メタデータの詳細確認とneed計算パラメータの分析
"""

import zipfile
import pandas as pd
import json
from io import BytesIO
import os

def check_meta_details(zip_path):
    """メタデータの詳細確認"""
    
    print(f"=== メタデータ詳細分析: {zip_path} ===\n")
    
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        file_list = zip_file.namelist()
        
        # メタデータファイルの詳細確認
        meta_files = [f for f in file_list if f.endswith('.json')]
        
        for meta_file in meta_files:
            print(f"\n{'='*60}")
            print(f"ファイル: {meta_file}")
            print('='*60)
            
            try:
                with zip_file.open(meta_file) as f:
                    data = json.loads(f.read().decode('utf-8'))
                
                # 構造的に表示
                if isinstance(data, dict):
                    for key, value in data.items():
                        print(f"\n[{key}]:")
                        if key == 'need_calculation_params':
                            print("  ★明け番問題に関連する重要な設定★")
                            print(json.dumps(value, indent=4, ensure_ascii=False))
                        elif key == 'slot':
                            print(f"  時間スロット設定: {value}")
                        elif key == 'roles':
                            print(f"  役割リスト: {value}")
                        elif key == 'dow_need_pattern':
                            print("  曜日別需要パターン:")
                            if isinstance(value, dict):
                                for dow, pattern in value.items():
                                    print(f"    {dow}: {pattern}")
                        elif isinstance(value, dict) and len(value) < 10:
                            print(json.dumps(value, indent=4, ensure_ascii=False))
                        elif isinstance(value, list) and len(value) < 20:
                            print(f"  {value}")
                        else:
                            print(f"  {type(value).__name__}: {len(value) if hasattr(value, '__len__') else value}")
                
            except Exception as e:
                print(f"読み込みエラー: {e}")
        
        # 特定の役割のヒートマップを詳細確認
        print(f"\n\n{'='*60}")
        print("特定役割のヒートマップ詳細分析")
        print('='*60)
        
        # 2F看護のデータを確認
        target_file = "out_mean_based/heat_2F看護.parquet"
        if target_file in file_list:
            with zip_file.open(target_file) as f:
                df = pd.read_parquet(BytesIO(f.read()))
            
            print(f"\n{target_file} の詳細:")
            print(f"データ形状: {df.shape}")
            
            # 明け番時間帯の詳細データ
            akebann_indices = list(range(40))  # 0:00-9:45
            akebann_data = df.iloc[akebann_indices]
            
            print(f"\n明け番時間帯 (0:00-9:45) のデータ:")
            print(f"時間帯\tneed\tstaff\tlack\texcess")
            print("-" * 50)
            
            for i in range(min(20, len(akebann_data))):  # 最初の20スロット(0:00-4:45)
                row = akebann_data.iloc[i]
                time_slot = df.index[i]
                need = row.get('need', 'N/A')
                staff = row.get('staff', 'N/A')
                lack = row.get('lack', 'N/A')
                excess = row.get('excess', 'N/A')
                print(f"{time_slot}\t{need}\t{staff}\t{lack}\t{excess}")
            
            # 日勤時間帯との比較
            print(f"\n日勤時間帯 (9:00-17:00) のデータサンプル:")
            day_shift_start = 9 * 4  # 9:00 = 36番目のスロット
            day_shift_end = 17 * 4   # 17:00 = 68番目のスロット
            day_shift_data = df.iloc[day_shift_start:day_shift_end]
            
            print(f"時間帯\tneed\tstaff\tlack\texcess")
            print("-" * 50)
            for i in range(0, min(8, len(day_shift_data)), 4):  # 1時間おき
                row = day_shift_data.iloc[i]
                time_slot = df.index[day_shift_start + i]
                need = row.get('need', 'N/A')
                staff = row.get('staff', 'N/A')
                lack = row.get('lack', 'N/A')
                excess = row.get('excess', 'N/A')
                print(f"{time_slot}\t{need}\t{staff}\t{lack}\t{excess}")

if __name__ == "__main__":
    zip_path = "analysis_results (17).zip"
    check_meta_details(zip_path)