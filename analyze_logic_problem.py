# 私の修正ロジックがどのように動作しているかを詳細調査
import pandas as pd
from pathlib import Path

print('=== 現在の修正ロジックの問題点調査 ===')
print()

print('私の修正ロジック:')
print('1. 各職種のneed列合計で比率計算')
print('2. need_per_date_slot全体を比率分配')
print()

print('問題点:')
print('- 各職種のneed列(固定値)を使用')
print('- 日付別の動的Need値を無視')
print('- 日付×時間帯×職種の3次元処理なし')
print()

print('正しいアプローチ:')
print('- 各職種の各日付の実際のNeed値を使用')
print('- 日付×時間帯レベルでの正確な処理')
print('- 完全にデータドリブンな動的処理')
print()

# 実データでの検証例
analysis_dir = Path('temp_analysis_results/out_mean_based')
need_df = pd.read_parquet(analysis_dir / 'need_per_date_slot.parquet')

# 看護師の実データを確認
nurse_file = analysis_dir / 'heat_看護師.parquet'
if nurse_file.exists():
    nurse_df = pd.read_parquet(nurse_file)
    
    print('=== 看護師データでの比較例 ===')
    print('月曜日（2025-06-02）:')
    print(f'  need_per_date_slot総Need: {need_df["2025-06-02"].sum():.1f}')
    print(f'  看護師の実際のNeed: {nurse_df["2025-06-02"].sum():.1f}')
    print(f'  看護師のneed列: {nurse_df["need"].sum():.1f}')
    print()
    
    print('木曜日（2025-06-05）:')
    print(f'  need_per_date_slot総Need: {need_df["2025-06-05"].sum():.1f}')
    print(f'  看護師の実際のNeed: {nurse_df["2025-06-05"].sum():.1f}')
    print(f'  看護師のneed列: {nurse_df["need"].sum():.1f}')
    print()
    
    print('問題の詳細:')
    print('- 私の修正では看護師のneed列(53.0)を基準に比率計算')
    print('- しかし各日で実際のNeed値は異なる(72.0, 54.0など)')
    print('- この差異が異常な不足の原因')
    print()
    
    # 全職種の日付別Need合計を確認
    role_files = [f for f in analysis_dir.glob('heat_*.parquet') 
                  if not f.name.startswith('heat_emp_') and f.name != 'heat_ALL.parquet']
    
    print('=== 全職種の日付別Need検証 ===')
    total_roles_need = {}
    for date_col in ['2025-06-01', '2025-06-02', '2025-06-03']:
        total_need = 0
        for role_file in role_files:
            try:
                role_df = pd.read_parquet(role_file)
                if date_col in role_df.columns:
                    total_need += role_df[date_col].sum()
            except:
                pass
        total_roles_need[date_col] = total_need
        overall_need = need_df[date_col].sum()
        print(f'{date_col}: 職種合計={total_need:.1f}, 全体Need={overall_need:.1f}')
    
print()
print('=== 結論 ===')
print('各職種のヒートマップは正しい日付別Needを持っている')
print('問題は私の修正ロジックが固定値(need列)を使用していること')
print('正解: 各職種の各日付の実際のNeed値を直接使用すべき')