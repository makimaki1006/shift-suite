#!/usr/bin/env python3
"""
勤務区分シートで「明」シフトの定義を確認
"""

import pandas as pd

try:
    # 勤務区分シートから「明」の定義を確認
    excel_path = 'テストデータ_勤務表　勤務時間_トライアル.xlsx'
    wt_df = pd.read_excel(excel_path, sheet_name='勤務区分', dtype=str)
    
    print('勤務区分シート:')
    print(wt_df.to_string())
    
    # 「明」の定義を特定
    ake_def = wt_df[wt_df.iloc[:, 0].astype(str) == '明']
    if len(ake_def) > 0:
        print('\n「明」の定義:')
        print(ake_def.to_string())
    else:
        print('\n勤務区分シートに「明」の定義が見つかりません')
        
        # 全ての行を確認
        print('\n全勤務コード:')
        for idx, row in wt_df.iterrows():
            code = str(row.iloc[0]).strip()
            if code and code != 'nan':
                print(f'{code}: {row.iloc[1]} - {row.iloc[2]}')
        
except Exception as e:
    print(f'Error: {e}')