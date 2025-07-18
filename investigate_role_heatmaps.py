# 職種別ヒートマップの日付別Need分布を詳細調査
import pandas as pd
import numpy as np
from pathlib import Path
import datetime

print('=== 職種別ヒートマップの日付別Need分布調査 ===')
print()

analysis_dir = Path('temp_analysis_results/out_mean_based')

# 職種別ヒートマップファイルをリスト
role_files = []
for f in analysis_dir.glob('heat_*.parquet'):
    if not f.name.startswith('heat_emp_') and f.name != 'heat_ALL.parquet':
        role_files.append(f)

print(f'職種別ヒートマップファイル数: {len(role_files)}')

# 最初の3つの職種を詳細確認
for role_file in role_files[:3]:
    role_name = role_file.name.replace('heat_', '').replace('.parquet', '')
    print(f'\n=== 職種: {role_name} ===')
    
    try:
        role_df = pd.read_parquet(role_file)
        print(f'Shape: {role_df.shape}')
        
        # 日付列を特定
        date_columns = [col for col in role_df.columns if '2025' in str(col)]
        
        if date_columns:
            print('各日付の曜日と総Need:')
            for col in date_columns[:7]:  # 最初の7日間
                try:
                    date_obj = datetime.datetime.strptime(col, '%Y-%m-%d').date()
                    weekday_name = ['月', '火', '水', '木', '金', '土', '日'][date_obj.weekday()]
                    total_need = role_df[col].sum()
                    print(f'  {col} ({weekday_name}): 総Need={total_need:.1f}')
                except:
                    print(f'  {col}: 日付解析エラー')
                    
            # need列の値も確認
            if 'need' in role_df.columns:
                need_value = role_df['need'].sum()
                print(f'need列の合計: {need_value:.1f}')
                
        else:
            print('日付列が見つかりません')
            
    except Exception as e:
        print(f'エラー: {e}')

# need_per_date_slot.parquetとの比較
print(f'\n=== need_per_date_slot.parquet との比較 ===')
need_file = analysis_dir / 'need_per_date_slot.parquet'
if need_file.exists():
    need_df = pd.read_parquet(need_file)
    date_columns = [col for col in need_df.columns if '2025' in str(col)]
    
    print('need_per_date_slot の日付別総Need:')
    for col in date_columns[:7]:
        try:
            date_obj = datetime.datetime.strptime(col, '%Y-%m-%d').date()
            weekday_name = ['月', '火', '水', '木', '金', '土', '日'][date_obj.weekday()]
            total_need = need_df[col].sum()
            print(f'  {col} ({weekday_name}): 総Need={total_need:.1f}')
        except:
            print(f'  {col}: 日付解析エラー')