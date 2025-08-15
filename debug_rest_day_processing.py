#!/usr/bin/env python3
"""
休日処理デバッグスクリプト
======================

テストデータ「ショート_テスト用データ.xlsx」で「×」がどのように処理されているかをデバッグ
"""

import sys
import pandas as pd
from pathlib import Path

# 必要に応じてパスを調整
sys.path.append('.')
from shift_suite.tasks.io_excel import (
    load_shift_patterns, 
    process_shift_data,
    _is_leave_code,
    LEAVE_CODES
)

def debug_rest_day_processing():
    """休日処理のデバッグ"""
    print("=" * 60)
    print("休日処理デバッグ")
    print("=" * 60)
    
    excel_file = Path("ショート_テスト用データ.xlsx")
    if not excel_file.exists():
        print(f"❌ テストファイルが見つかりません: {excel_file}")
        return False
    
    print(f"✅ テストファイル: {excel_file}")
    
    # 1. LEAVE_CODESの確認
    print(f"\n📋 定義されている休暇コード:")
    for code, desc in LEAVE_CODES.items():
        print(f"  '{code}' → {desc}")
    
    # 2. ×の判定テスト
    test_codes = ['×', 'X', 'x', '休', '有', '通常コード']
    print(f"\n🔍 休暇コード判定テスト:")
    for code in test_codes:
        is_leave = _is_leave_code(code)
        print(f"  '{code}' → {'休暇' if is_leave else '通常'}")
    
    try:
        # 3. 勤務区分シートの読み込み
        print(f"\n📖 勤務区分シートの読み込み...")
        wt_df, code2slots = load_shift_patterns(excel_file, "勤務区分")
        
        print(f"勤務区分の総数: {len(wt_df)}")
        print(f"スロット定義数: {len(code2slots)}")
        
        # ×のレコードをチェック
        cross_records = wt_df[wt_df['code'] == '×']
        if not cross_records.empty:
            print(f"\n🔍 '×'コードの処理結果:")
            for _, row in cross_records.iterrows():
                print(f"  code: '{row['code']}'")
                print(f"  parsed_slots_count: {row['parsed_slots_count']}")
                print(f"  holiday_type: '{row['holiday_type']}'")
                print(f"  is_leave_code: {row['is_leave_code']}")
        else:
            print(f"\n❌ '×'コードが勤務区分に見つかりません")
        
        # 4. 実際のシフトデータ処理
        print(f"\n📊 シフトデータの処理...")
        long_df = process_shift_data(excel_file)
        
        if not long_df.empty:
            print(f"総レコード数: {len(long_df)}")
            
            # ×関連のレコードをチェック
            cross_shift_records = long_df[long_df['code'] == '×']
            print(f"'×'コードのレコード数: {len(cross_shift_records)}")
            
            if not cross_shift_records.empty:
                print(f"\n🔍 '×'レコードのサンプル (最初の3件):")
                for i, (_, row) in enumerate(cross_shift_records.head(3).iterrows()):
                    print(f"  レコード {i+1}:")
                    print(f"    staff: {row['staff']}")
                    print(f"    code: '{row['code']}'")
                    print(f"    parsed_slots_count: {row['parsed_slots_count']}")
                    print(f"    holiday_type: '{row['holiday_type']}'")
            
            # parsed_slots_count=0のレコードをチェック
            zero_slot_records = long_df[long_df['parsed_slots_count'] == 0]
            print(f"\n📈 parsed_slots_count=0のレコード数: {len(zero_slot_records)}")
            
            if not zero_slot_records.empty:
                code_counts = zero_slot_records['code'].value_counts()
                print(f"コード別内訳:")
                for code, count in code_counts.items():
                    print(f"  '{code}': {count}件")
            
            # holiday_type別の統計
            holiday_stats = long_df['holiday_type'].value_counts()
            print(f"\n📊 holiday_type別統計:")
            for htype, count in holiday_stats.items():
                print(f"  '{htype}': {count}件")
        
        print(f"\n✅ デバッグ完了")
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_rest_day_processing()
    sys.exit(0 if success else 1)