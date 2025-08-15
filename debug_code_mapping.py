#!/usr/bin/env python3
"""
実績シートの勤務コードと勤務区分のマッピング確認
"""

import sys
import pandas as pd
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_code_mapping():
    """実績シートと勤務区分のコードマッピング確認"""
    
    print("Code Mapping Debug")
    print("=" * 40)
    
    test_file = project_root / "デイ_テスト用データ_休日精緻.xlsx"
    if not test_file.exists():
        print(f"Error: Test file not found: {test_file}")
        return
    
    try:
        # 1. 勤務区分シートのコード一覧
        print("1. Worktype codes (勤務区分):")
        df_worktype = pd.read_excel(test_file, sheet_name="勤務区分", dtype=str).fillna("")
        worktype_codes = set(df_worktype.iloc[:, 0].tolist())  # 最初の列がコード
        worktype_codes = {code for code in worktype_codes if code and code.strip()}
        
        print(f"   Found {len(worktype_codes)} codes:")
        for code in sorted(worktype_codes):
            try:
                print(f"     '{code}'")
            except UnicodeEncodeError:
                print(f"     [Unicode code: len={len(code)}]")
        
        # 2. 実績シートのコード一覧
        print(f"\n2. Actual shift codes in data sheets:")
        
        for sheet_name in ["R7.2", "R7.6"]:
            print(f"\n   --- {sheet_name} ---")
            df_actual = pd.read_excel(test_file, sheet_name=sheet_name, header=0, dtype=str).fillna("")
            
            print(f"   Sheet shape: {df_actual.shape}")
            print(f"   Columns: {df_actual.columns.tolist()}")
            
            # 日付列以外の列を確認（職員名、職種、雇用形態列）
            non_date_cols = df_actual.columns[:3]  # 最初の3列は非日付と仮定
            print(f"   Non-date columns: {non_date_cols.tolist()}")
            
            # 日付列（勤務コードが入っている列）
            date_cols = df_actual.columns[3:]
            print(f"   Date columns count: {len(date_cols)}")
            
            # 勤務コードを収集
            sheet_codes = set()
            for col in date_cols:
                for val in df_actual[col].dropna():
                    if val and str(val).strip() and str(val) not in ['土', '日', '月', '火', '水', '木', '金']:
                        sheet_codes.add(str(val).strip())
            
            print(f"   Found {len(sheet_codes)} unique codes:")
            for code in sorted(sheet_codes):
                try:
                    print(f"     '{code}'")
                except UnicodeEncodeError:
                    print(f"     [Unicode code: len={len(code)}]")
            
            # マッチング確認
            matched = sheet_codes & worktype_codes
            unmatched = sheet_codes - worktype_codes
            
            print(f"   Matched codes: {len(matched)}")
            for code in sorted(matched):
                print(f"     ✓ '{code}'")
            
            if unmatched:
                print(f"   Unmatched codes: {len(unmatched)}")
                for code in sorted(unmatched):
                    print(f"     ✗ '{code}'")
            else:
                print(f"   All codes matched!")
        
        # 3. 総合マッチング確認
        print(f"\n3. Overall code analysis:")
        
        # 全実績シートのコードを統合
        all_actual_codes = set()
        for sheet_name in ["R7.2", "R7.6"]:
            df = pd.read_excel(test_file, sheet_name=sheet_name, header=0, dtype=str).fillna("")
            date_cols = df.columns[3:]
            for col in date_cols:
                for val in df[col].dropna():
                    if val and str(val).strip() and str(val) not in ['土', '日', '月', '火', '水', '木', '金']:
                        all_actual_codes.add(str(val).strip())
        
        print(f"   Total worktype codes: {len(worktype_codes)}")
        print(f"   Total actual codes: {len(all_actual_codes)}")
        
        matched_total = all_actual_codes & worktype_codes
        unmatched_total = all_actual_codes - worktype_codes
        
        print(f"   Matched: {len(matched_total)}")
        print(f"   Unmatched: {len(unmatched_total)}")
        
        if unmatched_total:
            print(f"   Missing from worktype definition:")
            for code in sorted(unmatched_total):
                print(f"     '{code}'")
                
        if len(matched_total) == 0:
            print(f"   ⚠️  NO CODES MATCHED - This explains why no valid records are generated!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_code_mapping()