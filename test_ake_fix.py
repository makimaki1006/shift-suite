#\!/usr/bin/env python3
"""
明け番ヒートマップ表示修正のテストスクリプト
"""

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
            shift_sheets=["R7.6"],  # シート名を指定
            header_row=2,
            slot_minutes=15,
            year_month_cell_location="B1"
        )
        
        print(f"読み込み完了: {len(long_df)} レコード")
        
        # 明け番データの確認
        print("\n2. 明け番データの確認...")
        ake_records = long_df[long_df['code'] == '明']
        
        if ake_records.empty:
            print("明け番（明）のレコードが見つかりません")
        else:
            print(f"明け番レコード数: {len(ake_records)}")
            
            # 時間別の分布を確認
            ake_records['hour'] = ake_records['ds'].dt.hour
            hour_counts = ake_records['hour'].value_counts().sort_index()
            
            print("\n明け番の時間別分布:")
            for hour, count in hour_counts.items():
                print(f"  {hour:02d}時台: {count}件")
            
            # 日付別の確認
            ake_records['date'] = ake_records['ds'].dt.date
            date_counts = ake_records['date'].value_counts().sort_index()
            
            print(f"\n明け番が登録されている日数: {len(date_counts)}")
            print("日付別の明け番レコード数（最初の5日）:")
            for date, count in list(date_counts.items())[:5]:
                print(f"  {date}: {count}件")
            
            # 午前中（0:00-11:59）のデータ確認
            morning_ake = ake_records[ake_records['hour'] < 12]
            print(f"\n午前中の明け番レコード数: {len(morning_ake)}")
            
            if len(morning_ake) > 0:
                print("修正成功: 明け番の午前中部分が元の日付で処理されています")
                
                # サンプルデータの表示
                print("\n午前中の明け番データサンプル:")
                sample_data = morning_ake[['ds', 'staff', 'role', 'code']].head(10)
                print(sample_data.to_string(index=False))
            else:
                print("警告: 午前中の明け番データが見つかりません")
        
        # 勤務区分の確認
        print("\n3. 勤務区分の確認...")
        ake_patterns = wt_df[wt_df['code'] == '明']
        if not ake_patterns.empty:
            print("明け番の勤務パターン:")
            for _, pattern in ake_patterns.iterrows():
                print(f"  開始: {pattern.get('start_parsed', 'N/A')}")
                print(f"  終了: {pattern.get('end_parsed', 'N/A')}")
                print(f"  スロット数: {pattern.get('parsed_slots_count', 'N/A')}")
        
        print("\n=== テスト完了 ===")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ake_fix()
EOF < /dev/null
