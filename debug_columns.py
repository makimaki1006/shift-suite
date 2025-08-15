import pandas as pd
import re

def _normalize(val):
    txt = str(val).replace('　', ' ')
    return re.sub(r'\s+', '', txt).strip()

SHEET_COL_ALIAS = {
    '氏名': 'staff',
    '職種': 'role', 
    '雇用形態': 'employment',
    '����': 'staff',
    '�E��': 'role',
    '�ٗp�`��': 'employment',
}

excel_path = 'テストデータ_勤務表　勤務時間_トライアル.xlsx'

# Test different header rows
for header_val in [0, 1, 2]:
    print(f'\n=== Testing header={header_val} ===')
    try:
        df_sheet = pd.read_excel(excel_path, sheet_name='R7.6', header=header_val, dtype=str).fillna('')
        
        print('Original columns:')
        for i, col in enumerate(df_sheet.columns[:5]):
            print(f'{i}: {repr(col)}')
        
        print('After normalization and mapping:')
        mapped_columns = []
        for i, col in enumerate(df_sheet.columns[:5]):
            normalized = _normalize(str(col))
            mapped = SHEET_COL_ALIAS.get(normalized, normalized)
            mapped_columns.append(mapped)
            print(f'{i}: {repr(col)} -> {repr(normalized)} -> {repr(mapped)}')
        
        print(f'Required columns check:')
        print(f'staff in mapped: {"staff" in mapped_columns}')
        print(f'role in mapped: {"role" in mapped_columns}')
        
        if "staff" in mapped_columns and "role" in mapped_columns:
            print("*** THIS HEADER ROW WORKS! ***")
            
    except Exception as e:
        print(f'Error with header={header_val}: {e}')