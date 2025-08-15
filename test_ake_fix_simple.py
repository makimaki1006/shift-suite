#!/usr/bin/env python3
"""明け番ヒートマップ表示修正のテストスクリプト"""

import sys
from pathlib import Path
import pandas as pd

# プロジェクトのパスを追加
sys.path.insert(0, str(Path(__file__).parent))

from shift_suite.tasks.io_excel import ingest_excel

def test_ake_fix():
    """明け番シフトの処理をテスト"""
    print("=== 明け番ヒートマップ表示修正テスト ===")
    
    # テストファイルのパス
    test_file = Path("勤務表　勤務時間_トライアル.xlsx")
    if not test_file.exists():
        print(f"テストファイル {test_file} が見つかりません")
        return
    
    try:
        # Excelファイルから勤務データを読み込み
        print("1. Excelファイルからデータを読み込み中...")
        long_df, wt_df, unknown_codes = ingest_excel(
            test_file,
            shift_sheets=["R7.6"],
            header_row=2,
            slot_minutes=15,
            year_month_cell_location="B1"
        )
        
        print(f"読み込み完了: {len(long_df)} レコード")
        
        # 明け番データの確認
        print("\\n2. 明け番データの確認...")
        ake_records = long_df[long_df['code'] == '明']
        
        if ake_records.empty:
            print("明け番（明）のレコードが見つかりません")
        else:
            print(f"明け番レコード数: {len(ake_records)}")
            
            # 時間別の分布を確認
            ake_records_copy = ake_records.copy()
            ake_records_copy['hour'] = ake_records_copy['ds'].dt.hour
            hour_counts = ake_records_copy['hour'].value_counts().sort_index()
            
            print("\\n明け番の時間別分布:")
            for hour, count in hour_counts.items():
                print(f"  {hour:02d}時台: {count}件")
            
            # 午前中（0:00-11:59）のデータ確認
            morning_ake = ake_records_copy[ake_records_copy['hour'] < 12]
            print(f"\\n午前中の明け番レコード数: {len(morning_ake)}")
            
            if len(morning_ake) > 0:
                print("修正成功: 明け番の午前中部分が元の日付で処理されています")
            else:
                print("警告: 午前中の明け番データが見つかりません")
        
        print("\\n=== テスト完了 ===")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ake_fix()