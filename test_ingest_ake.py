#!/usr/bin/env python3
"""
明シフトのingest_excel処理をテスト
"""

import sys
import pandas as pd
from pathlib import Path

# shift_suiteモジュールパスを追加
sys.path.append('.')

from shift_suite.tasks.io_excel import ingest_excel

def test_ingest_ake():
    """明シフトのingest処理をテスト"""
    try:
        excel_path = Path('テストデータ_勤務表　勤務時間_トライアル.xlsx')
        
        # ingest_excelを実行
        print("ingest_excel実行中...")
        long_df, wt_df, unknown_codes = ingest_excel(
            excel_path,
            shift_sheets=['R7.6'],
            header_row=1  # 正しいヘッダー行は1行目（1-indexed）
        )
        
        print(f"long_df shape: {long_df.shape}")
        print(f"wt_df shape: {wt_df.shape}")
        print(f"unknown_codes: {unknown_codes}")
        
        # 明シフトのレコードを確認
        ake_records = long_df[long_df['code'] == '明']
        print(f"\n明シフトのレコード数: {len(ake_records)}")
        
        if len(ake_records) > 0:
            print("明シフトレコードの最初の10件:")
            print(ake_records[['ds', 'staff', 'code']].head(10))
            
            # 時間別の分布を確認
            ake_records['hour'] = ake_records['ds'].dt.hour
            hour_dist = ake_records['hour'].value_counts().sort_index()
            print(f"\n明シフトの時間別分布:")
            print(hour_dist)
            
            # 0:00-10:00の時間帯があるかチェック
            morning_hours = ake_records[ake_records['hour'] < 10]
            print(f"\n0:00-9:xx時間帯の明シフトレコード数: {len(morning_hours)}")
            
        else:
            print("明シフトのレコードが見つかりません")
            
            # 全体のユニークコードを確認
            unique_codes = long_df['code'].unique()
            print(f"long_dfに含まれるユニークコード: {sorted(unique_codes)}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ingest_ake()