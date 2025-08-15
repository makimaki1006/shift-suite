import os
import zipfile
import tempfile
from pathlib import Path

# 簡単なZIPファイルテスト
current_dir = r"C:\Users\fuji1\OneDrive\デスクトップ\シフト分析"
zip_files = [f for f in os.listdir(current_dir) if f.endswith('.zip')]

print(f"Found ZIP files: {zip_files}")

for zip_file in zip_files:
    zip_path = os.path.join(current_dir, zip_file)
    print(f"\nTesting: {zip_file}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            file_list = zf.namelist()
            print(f"  Files in ZIP: {len(file_list)}")
            
            # シナリオディレクトリの確認
            scenarios = [f.split('/')[0] for f in file_list if f.startswith('out_') and '/' in f]
            unique_scenarios = list(set(scenarios))
            print(f"  Scenarios: {unique_scenarios}")
            
            # 重要ファイルの確認
            for scenario in unique_scenarios:
                print(f"    {scenario}:")
                key_files = [
                    f'{scenario}/pre_aggregated_data.parquet',
                    f'{scenario}/shortage_time.parquet',
                    f'{scenario}/need_per_date_slot.parquet'
                ]
                
                for key_file in key_files:
                    exists = key_file in file_list
                    print(f"      {key_file.split('/')[-1]}: {'OK' if exists else 'MISSING'}")
                    
    except Exception as e:
        print(f"  Error: {e}")