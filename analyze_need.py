import pandas as pd
import numpy as np
import os

print('=== Need Per Date Slot Analysis ===')
need_df = pd.read_parquet('temp_analysis_results/out_mean_based/need_per_date_slot.parquet')
print(f'Shape: {need_df.shape}')

# Total need across all slots and dates  
total_need_all = need_df.sum().sum()
print(f'Total need across all slots and dates: {total_need_all:.1f}')

# Convert to hours (assuming 30-minute slots)
total_need_hours = total_need_all * 0.5
print(f'Total need hours (30-min slots): {total_need_hours:.1f}')
print()

# Check individual role heatmaps for comparison
print('=== Individual Role Need Values ===')
files = os.listdir('temp_analysis_results/out_mean_based/')
role_files = []
for f in files:
    if f.startswith('heat_') and f.endswith('.parquet'):
        if not f.startswith('heat_emp_') and f != 'heat_ALL.parquet':
            role_files.append(f)

total_role_needs = {}
for role_file in role_files[:5]:  # Check first 5 roles
    role_name = role_file.replace('heat_', '').replace('.parquet', '')
    try:
        role_df = pd.read_parquet(f'temp_analysis_results/out_mean_based/{role_file}')
        if 'need' in role_df.columns:
            role_need_sum = role_df['need'].sum()
            total_role_needs[role_name] = role_need_sum
            print(f'{role_name}: {role_need_sum:.1f}')
    except Exception as e:
        print(f'{role_name}: Error - {e}')

print()
sum_individual_roles = sum(total_role_needs.values())
print(f'Sum of individual role needs: {sum_individual_roles:.1f}')
print(f'Need per date slot total: {total_need_hours:.1f}')
if total_need_hours > 0:
    print(f'Ratio: {sum_individual_roles / total_need_hours:.3f}')