#!/usr/bin/env python3
"""
ingest_excel処理で明シフトがどこで失われるかをデバッグ
"""

import sys
import pandas as pd
from pathlib import Path

sys.path.append('.')
from shift_suite.tasks.io_excel import load_shift_patterns

def debug_ingest_flow():
    """ingest処理の各段階で明シフトを追跡"""
    try:
        excel_path = Path('テストデータ_勤務表　勤務時間_トライアル.xlsx')
        
        print("=== Step 1: Work pattern loading ===")
        wt_df, code2slots = load_shift_patterns(excel_path)
        
        print(f"Work patterns loaded: {len(wt_df)} patterns")
        
        # 明パターンの確認
        ake_pattern = wt_df[wt_df['code'] == '明']
        if len(ake_pattern) > 0:
            print("OK: 明 pattern found in work patterns")
            print(f"明 pattern slots: {code2slots.get('明', [])}")
            print(f"明 pattern details: {ake_pattern.iloc[0].to_dict()}")
        else:
            print("NG: 明 pattern NOT found in work patterns")
            
        print(f"\nAll pattern codes: {sorted(list(code2slots.keys()))}")
        
        print("\n=== Step 2: Excel sheet reading ===")
        # シート読み込み（ingest_excelの処理をシミュレート）
        df_sheet = pd.read_excel(
            excel_path,
            sheet_name='R7.6',
            header=0,  # header_row=1 means 0-indexed
            dtype=str,
        ).fillna("")
        
        print(f"Sheet shape: {df_sheet.shape}")
        
        # Column mapping
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
        
        df_sheet.columns = [
            SHEET_COL_ALIAS.get(_normalize(str(c)), _normalize(str(c)))
            for c in df_sheet.columns
        ]
        
        # 日付列候補の特定
        date_cols_candidate = [
            c for c in df_sheet.columns
            if c not in ("staff", "role", "employment")
            and not str(c).startswith("Unnamed:")
        ]
        
        print(f"Date columns identified: {len(date_cols_candidate)}")
        
        print("\n=== Step 3: Code processing ===")
        # 明コードの処理を詳細に追跡
        ake_records_found = 0
        ake_records_processed = 0
        ake_codes_filtered = 0
        
        for _, row_data in df_sheet.iterrows():
            staff = _normalize(row_data.get("staff", ""))
            role = _normalize(row_data.get("role", ""))
            
            # スタッフ・役職行のスキップ条件をチェック
            DOW_TOKENS = {"月", "火", "水", "木", "金", "土", "日", "明"}
            if (staff in DOW_TOKENS or role in DOW_TOKENS or (staff == "" and role == "")):
                continue
                
            for col_name in date_cols_candidate:
                shift_code_raw = row_data.get(col_name, "")
                code_val = _normalize(str(shift_code_raw))
                
                if code_val == '明':
                    ake_records_found += 1
                    
                    # ingest_excelの条件をチェック
                    if code_val in ("", "nan", "NaN"):
                        continue
                        
                    if code_val in DOW_TOKENS:
                        ake_codes_filtered += 1
                        continue
                        
                    if code_val not in code2slots:
                        print(f"Warning: 明 code not found in code2slots!")
                        continue
                        
                    ake_records_processed += 1
                    print(f"明 shift processed: staff={staff}, date={col_name}")
        
        print(f"\n明 shift processing summary:")
        print(f"  Found in Excel: {ake_records_found}")
        print(f"  Filtered by DOW_TOKENS: {ake_codes_filtered}")
        print(f"  Successfully processed: {ake_records_processed}")
        
        if ake_codes_filtered > 0:
            print(f"\nWARNING: {ake_codes_filtered} 明 shifts were filtered out because '明' is in DOW_TOKENS!")
            print(f"DOW_TOKENS = {DOW_TOKENS}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_ingest_flow()