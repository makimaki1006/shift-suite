#!/usr/bin/env python3
"""
Excelシートの「明」コード処理をデバッグ
"""

import pandas as pd

try:
    excel_path = 'テストデータ_勤務表　勤務時間_トライアル.xlsx'
    
    # 正しいヘッダー行で読み込み
    df = pd.read_excel(excel_path, sheet_name='R7.6', header=0, dtype=str).fillna("")
    
    print(f"Excel DataFrame shape: {df.shape}")
    print(f"Column names: {df.columns.tolist()}")
    
    # Mapping of column names (from io_excel.py)
    SHEET_COL_ALIAS = {
        "氏名": "staff", "名前": "staff", "staff": "staff", "name": "staff",
        "従業員": "staff", "member": "staff",
        "職種": "role", "部署": "role", "役職": "role", "role": "role",
        "雇用形態": "employment", "雇用区分": "employment", "employment": "employment",
    }
    
    def _normalize(val):
        import re
        txt = str(val).replace("　", " ")
        return re.sub(r"\s+", "", txt).strip()
    
    # Column mapping
    df.columns = [SHEET_COL_ALIAS.get(_normalize(str(c)), _normalize(str(c))) for c in df.columns]
    print(f"Mapped column names: {df.columns.tolist()}")
    
    # Check for staff/role columns
    if "staff" in df.columns:
        print("OK 'staff' column found")
    else:
        print("NG 'staff' column not found")
        
    if "role" in df.columns:
        print("OK 'role' column found")  
    else:
        print("NG 'role' column not found")
    
    # Find date columns
    date_cols = [c for c in df.columns if c not in ("staff", "role", "employment") and not str(c).startswith("Unnamed")]
    print(f"Date columns: {date_cols}")
    
    # Count 明 occurrences in each date column
    ake_count = 0
    ake_locations = []
    
    for col in date_cols:
        col_ake_count = (df[col].astype(str) == '明').sum()
        ake_count += col_ake_count
        
        if col_ake_count > 0:
            print(f"Column '{col}': {col_ake_count} 明 shifts")
            # Find staff names with 明 shifts
            ake_rows = df[df[col].astype(str) == '明']
            for idx, row in ake_rows.iterrows():
                staff_name = row.get('staff', row.get('職員', 'Unknown'))
                ake_locations.append((staff_name, col, idx))
    
    print(f"\nTotal 明 shift occurrences: {ake_count}")
    
    if ake_count > 0:
        print("明 shift locations (first 10):")
        for staff, date_col, row_idx in ake_locations[:10]:
            print(f"  {staff} - {date_col} (row {row_idx})")
    
    # Check all unique shift codes
    all_codes = set()
    for col in date_cols:
        values = df[col].dropna().astype(str)
        for val in values:
            val_clean = str(val).strip()
            if val_clean and val_clean not in ['nan', '', 'NaN']:
                all_codes.add(val_clean)
    
    print(f"\nAll unique shift codes in Excel: {sorted(list(all_codes))}")
    
    if '明' in all_codes:
        print("OK '明' code found in Excel data")
    else:
        print("NG '明' code NOT found in Excel data")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()