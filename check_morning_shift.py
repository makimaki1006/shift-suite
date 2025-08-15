#!/usr/bin/env python3
"""
元のExcelファイルで朝シフトの使用状況を確認
"""

import pandas as pd

try:
    excel_path = 'テストデータ_勤務表　勤務時間_トライアル.xlsx'
    
    # シートR7.6を読み込み
    df = pd.read_excel(excel_path, sheet_name='R7.6', header=1, dtype=str)
    print(f'Excelファイル shape: {df.shape}')
    
    # 全セルの値を確認
    all_codes = set()
    for col in df.columns:
        if not str(col).startswith('Unnamed'):
            # 職員・職種列以外を対象
            if not any(keyword in str(col).lower() for keyword in ['staff', 'role', '職員', '氏名', '職種', '部署', '雇用']):
                values = df[col].dropna().astype(str)
                for val in values:
                    val_clean = str(val).strip()
                    if val_clean and val_clean != 'nan':
                        all_codes.add(val_clean)
    
    print(f'全シフトコード: {sorted(list(all_codes))}')
    
    # 朝シフトがあるかチェック
    has_morning = '朝' in all_codes
    print(f'朝シフトの存在: {has_morning}')
    
    if has_morning:
        # 朝シフトの使用回数をカウント
        morning_count = 0
        for col in df.columns:
            morning_in_col = (df[col].astype(str) == '朝').sum()
            morning_count += morning_in_col
        print(f'朝シフトの使用回数: {morning_count}')
        
        # 朝シフトが使われている職員を特定
        morning_staff = []
        for _, row in df.iterrows():
            staff = row.get('職員名', row.get('氏名', row.get('staff', '')))
            for col in df.columns:
                if str(row[col]) == '朝':
                    morning_staff.append((staff, col))
        
        if morning_staff:
            print('朝シフトが使われている職員・日付:')
            for staff, date_col in morning_staff[:10]:  # 最初の10件
                print(f'  {staff} - {date_col}')
        
except Exception as e:
    print(f'Error: {e}')