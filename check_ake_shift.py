#!/usr/bin/env python3
"""
元のExcelファイルで「明」シフトの使用状況を確認
"""

import pandas as pd

try:
    excel_path = '勤務表　勤務時間_トライアル.xlsx'
    
    # シートR7.6を読み込み
    df = pd.read_excel(excel_path, sheet_name='R7.6', header=1, dtype=str)
    print(f'Excelファイル shape: {df.shape}')
    
    # 「明」シフトの使用状況をチェック
    ake_count = 0
    ake_locations = []
    
    for col in df.columns:
        if not str(col).startswith('Unnamed'):
            # 職員・職種列以外を対象
            if not any(keyword in str(col).lower() for keyword in ['staff', 'role', '職員', '氏名', '職種', '部署', '雇用']):
                col_ake_count = (df[col].astype(str) == '明').sum()
                ake_count += col_ake_count
                
                if col_ake_count > 0:
                    # 「明」シフトがある行を特定
                    ake_rows = df[df[col].astype(str) == '明']
                    for idx, row in ake_rows.iterrows():
                        staff_name = None
                        for staff_col in ['職員名', '氏名', 'staff']:
                            if staff_col in row:
                                staff_name = row[staff_col]
                                break
                        ake_locations.append((staff_name, col, idx))
    
    print(f'「明」シフトの使用回数: {ake_count}')
    
    if ake_count > 0:
        print('「明」シフトが使われている場所:')
        for staff, date_col, row_idx in ake_locations[:10]:  # 最初の10件
            print(f'  {staff} - {date_col} (行{row_idx})')
    else:
        print('「明」シフトはExcelファイルで使用されていません')
        
    # 全シフトコードの確認
    all_codes = set()
    for col in df.columns:
        if not str(col).startswith('Unnamed'):
            if not any(keyword in str(col).lower() for keyword in ['staff', 'role', '職員', '氏名', '職種', '部署', '雇用']):
                values = df[col].dropna().astype(str)
                for val in values:
                    val_clean = str(val).strip()
                    if val_clean and val_clean not in ['nan', '', 'NaN']:
                        all_codes.add(val_clean)
    
    print(f'\\nExcelファイル内の実際のシフトコード:')
    print(sorted(list(all_codes)))
    
    # 夜勤関連のコードを確認
    night_codes = [code for code in all_codes if any(char in code for char in ['夜', '遅', '明', '早'])]
    print(f'夜勤・明け番関連コード: {night_codes}')
        
except Exception as e:
    print(f'Error: {e}')