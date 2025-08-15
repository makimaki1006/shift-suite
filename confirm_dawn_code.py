#!/usr/bin/env python3
"""
明番コードが「明」で表現されていることを確認
"""

import pandas as pd
from pathlib import Path
import sys
import os

# パスを追加
sys.path.insert(0, os.getcwd())

from shift_suite.tasks.io_excel import ingest_excel

def confirm_dawn_code():
    """「明」コードの存在と処理を確認"""
    excel_path = Path("ショート_テスト用データ.xlsx")
    
    if not excel_path.exists():
        print(f"ERROR: Test file not found: {excel_path}")
        return
    
    print("=== 明番コード「明」の確認 ===")
    
    # Excelファイルの直接確認
    print("\n--- Excelファイル直接確認 ---")
    df = pd.read_excel(excel_path, sheet_name="R7.6", header=0, dtype=str).fillna("")
    
    # 日付列を取得
    date_cols = [c for c in df.columns if not str(c) in ['氏名', '職種', '雇用形態'] and not str(c).startswith("Unnamed:")]
    
    # 全データで「明」コードを検索
    dawn_found = False
    dawn_count = 0
    
    for col in date_cols:
        col_values = df[col].dropna().astype(str)
        dawn_in_col = col_values[col_values == '明']
        if len(dawn_in_col) > 0:
            dawn_found = True
            dawn_count += len(dawn_in_col)
            print(f"列 '{col}' に「明」コード発見: {len(dawn_in_col)}個")
    
    print(f"\n「明」コード総数: {dawn_count}個")
    
    if not dawn_found:
        print("⚠️ 「明」コードが見つかりません")
        # 類似コードを検索
        all_codes = set()
        for col in date_cols:
            col_values = df[col].dropna().astype(str)
            col_values = col_values[col_values != ""]
            all_codes.update(col_values.unique())
        
        # 「明」に関連するコードを検索
        related_codes = [code for code in all_codes if '明' in code]
        if related_codes:
            print(f"「明」を含むコード: {related_codes}")
        
        print(f"すべてのユニークコード: {sorted(list(all_codes))}")
    
    # ingest_excelでの処理確認
    print("\n--- ingest_excel処理での「明」コード確認 ---")
    sheet_names = pd.ExcelFile(excel_path, engine="openpyxl").sheet_names
    shift_sheets = [s for s in sheet_names if "勤務" not in s]
    
    try:
        long_df, wt_df, unknown_codes = ingest_excel(
            excel_path,
            shift_sheets=shift_sheets,
            header_row=0,
            slot_minutes=30,
            year_month_cell_location="D1"
        )
        
        # 「明」コードの処理状況確認
        if '明' in long_df['code'].values:
            dawn_records = long_df[long_df['code'] == '明']
            print(f"処理後の「明」レコード数: {len(dawn_records)}")
            print(f"「明」コードの時間帯分布:")
            dawn_records['hour'] = pd.to_datetime(dawn_records['ds']).dt.hour
            hour_dist = dawn_records['hour'].value_counts().sort_index()
            for hour, count in hour_dist.items():
                print(f"  {hour:02d}時台: {count}件")
        else:
            print("⚠️ 処理後のデータに「明」コードが存在しません")
            print(f"処理後に存在するコード: {sorted(long_df['code'].unique())}")
        
        # 勤務区分での「明」の定義確認
        if '明' in wt_df['code'].values:
            dawn_wt = wt_df[wt_df['code'] == '明']
            print(f"\n勤務区分での「明」定義:")
            print(f"  開始時刻: {dawn_wt['start_parsed'].iloc[0]}")
            print(f"  終了時刻: {dawn_wt['end_parsed'].iloc[0]}")
            print(f"  休暇タイプ: {dawn_wt['holiday_type'].iloc[0]}")
        else:
            print("⚠️ 勤務区分に「明」コードが定義されていません")
            print(f"勤務区分のコード: {sorted(wt_df['code'].unique())}")
    
    except Exception as e:
        print(f"処理エラー: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== 確認完了 ===")

if __name__ == "__main__":
    confirm_dawn_code()