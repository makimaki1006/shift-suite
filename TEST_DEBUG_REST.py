#!/usr/bin/env python3
"""休日除外問題デバッグ"""
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from shift_suite.tasks.io_excel import ingest_excel

# テスト実行
excel_path = Path("ショート_テスト用データ.xlsx")
if excel_path.exists():
    print("📋 Excelファイル読み込みテスト")
    
    long_df, wt_df, unknown = ingest_excel(
        excel_path,
        shift_sheets=["R7.6"],
        header_row=0,
        slot_minutes=30,
        year_month_cell_location="D1"
    )
    
    print(f"\n結果:")
    print(f"- 総レコード数: {len(long_df)}")
    
    if 'parsed_slots_count' in long_df.columns:
        zero = (long_df['parsed_slots_count'] == 0).sum()
        print(f"- parsed_slots_count=0: {zero}件")
        
        if zero > 0:
            print("\n⚠️ 問題: 休日レコードが除外されていません！")
        else:
            print("\n✅ 正常: 休日レコードは正しく除外されています")
else:
    print("❌ テストファイルが見つかりません")