#!/usr/bin/env python3
"""
Excelファイルの実際の内容を確認して明番コード「●」の存在をチェック
"""

import pandas as pd
from pathlib import Path

def debug_excel_content():
    """Excelファイルの実際の内容を確認"""
    excel_path = Path("ショート_テスト用データ.xlsx")
    
    if not excel_path.exists():
        print(f"ERROR: Test file not found: {excel_path}")
        return
    
    print("=== Excelファイル内容確認 ===")
    
    # 全シートをチェック
    excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
    sheet_names = excel_file.sheet_names
    
    print(f"全シート: {sheet_names}")
    
    # 勤務区分シートを確認
    print(f"\n--- 勤務区分シート確認 ---")
    wt_df = pd.read_excel(excel_path, sheet_name="勤務区分", dtype=str).fillna("")
    print(f"勤務区分シート shape: {wt_df.shape}")
    print(f"列名: {wt_df.columns.tolist()}")
    print(f"勤務コード一覧:")
    for i, row in wt_df.iterrows():
        code_val = row.iloc[0] if len(row) > 0 else "N/A"
        start_val = row.iloc[1] if len(row) > 1 else "N/A"
        end_val = row.iloc[2] if len(row) > 2 else "N/A"
        print(f"  {i+1}: コード='{code_val}', 開始='{start_val}', 終了='{end_val}'")
    
    # 実績シートを確認
    shift_sheets = [s for s in sheet_names if "勤務" not in s]
    print(f"\n--- 実績シート確認 ---")
    print(f"実績シート: {shift_sheets}")
    
    for sheet_name in shift_sheets:
        print(f"\n=== シート: {sheet_name} ===")
        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=0, dtype=str).fillna("")
        
        print(f"Shape: {df.shape}")
        print(f"列名: {df.columns.tolist()}")
        
        # スタッフと職種の列を確認
        staff_col = None
        role_col = None
        
        for col in df.columns:
            col_str = str(col).strip()
            if any(keyword in col_str for keyword in ["氏名", "名前", "staff", "name", "従業員", "member"]):
                staff_col = col
            elif any(keyword in col_str for keyword in ["職種", "部署", "役職", "role"]):
                role_col = col
        
        print(f"スタッフ列: {staff_col}")
        print(f"職種列: {role_col}")
        
        if staff_col and role_col:
            # 日付列を特定
            date_cols = [c for c in df.columns if c not in [staff_col, role_col] and not str(c).startswith("Unnamed:")]
            print(f"日付列数: {len(date_cols)}")
            print(f"最初の5つの日付列: {date_cols[:5]}")
            
            # 全データの勤務コードを収集
            all_codes = set()
            for col in date_cols:
                col_values = df[col].dropna().astype(str)
                col_values = col_values[col_values != ""]
                all_codes.update(col_values.unique())
            
            # 曜日トークンを除去
            dow_tokens = {"月", "火", "水", "木", "金", "土", "日", "明"}
            all_codes = all_codes - dow_tokens - {"nan", "NaN"}
            
            print(f"実際のシフトデータで使用されているコード: {sorted(list(all_codes))}")
            
            # 明番コード「●」の検索
            dawn_codes = [code for code in all_codes if "●" in code]
            if dawn_codes:
                print(f"明番コード「●」発見: {dawn_codes}")
            else:
                print("⚠️ 明番コード「●」が見つかりません")
            
            # 夜勤コード「〇」の検索
            night_codes = [code for code in all_codes if "〇" in code]
            if night_codes:
                print(f"夜勤コード「〇」発見: {night_codes}")
            else:
                print("⚠️ 夜勤コード「〇」が見つかりません")
            
            # 各コードの使用頻度
            print(f"\nコード使用頻度:")
            code_counts = {}
            for col in date_cols:
                col_values = df[col].dropna().astype(str)
                col_values = col_values[col_values != ""]
                for code in col_values:
                    if code not in dow_tokens and code not in {"nan", "NaN"}:
                        code_counts[code] = code_counts.get(code, 0) + 1
            
            for code, count in sorted(code_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  '{code}': {count}回")
    
    print("\n=== End Debug ===")

if __name__ == "__main__":
    debug_excel_content()