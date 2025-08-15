#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
明け番処理のデバッグスクリプト
io_excel.pyの日付またぎ処理を検証
"""

import pandas as pd
import datetime as dt
import sys
import os

def debug_ake_processing():
    """明け番処理のデバッグ"""
    print("="*80)
    print("明け番処理デバッグ")
    print("="*80)
    
    # テストデータの勤務区分確認
    print("1. テストデータの勤務区分確認")
    print("-" * 40)
    
    file_path = "./テストデータ_勤務表　勤務時間_トライアル.xlsx"
    
    try:
        # 勤務区分シート読み込み
        wt_df = pd.read_excel(file_path, sheet_name="勤務区分")
        print(f"勤務区分シート読み込み成功: {wt_df.shape}")
        
        # 列名の確認
        print(f"列名: {list(wt_df.columns)}")
        
        # 明け番の定義確認
        print("\n明け番（明）の定義:")
        ake_rows = wt_df[wt_df.astype(str).apply(lambda x: x.str.contains('明', na=False)).any(axis=1)]
        for idx, row in ake_rows.iterrows():
            print(f"  行{idx+1}: {list(row)}")
        
        # 実際のio_excel.pyの処理をシミュレート
        print("\n2. io_excel.pyの処理シミュレーション")
        print("-" * 40)
        
        simulate_io_excel_processing(wt_df)
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

def simulate_io_excel_processing(wt_df):
    """io_excel.pyの処理をシミュレートして明け番の問題を特定"""
    
    # code_to_start_timeの構築（io_excel.pyと同じロジック）
    code_to_start_time = {}
    
    print("勤務区分データ:")
    for idx, row in wt_df.iterrows():
        print(f"  行{idx+1}: {dict(row)}")
    
    # start_parsedカラムの特定
    possible_start_cols = ['開始', 'start', 'start_parsed', '開始時間']
    start_col = None
    
    for col in wt_df.columns:
        if any(name in str(col).lower() for name in ['start', '開始']):
            start_col = col
            break
    
    print(f"\n開始時間カラム: {start_col}")
    
    if start_col is None:
        # 列インデックスでの推定
        if len(wt_df.columns) >= 2:
            start_col = wt_df.columns[1]  # 2番目のカラムを開始時間と仮定
            print(f"推定開始時間カラム: {start_col}")
    
    # code_to_start_timeの構築
    code_col = wt_df.columns[0]  # 1番目のカラムをコードと仮定
    
    print(f"\ncode_to_start_time構築:")
    for idx, row in wt_df.iterrows():
        code = row.get(code_col)
        if start_col in row.index:
            start_value = row.get(start_col)
        else:
            start_value = None
            
        print(f"  コード: {code}, 開始時間: {start_value} (型: {type(start_value)})")
        
        if code and start_value:
            try:
                if isinstance(start_value, dt.time):
                    code_to_start_time[code] = start_value
                elif isinstance(start_value, str):
                    code_to_start_time[code] = dt.datetime.strptime(start_value, "%H:%M").time()
                else:
                    code_to_start_time[code] = None
                    print(f"    → 変換失敗: {start_value}")
            except (ValueError, TypeError) as e:
                code_to_start_time[code] = None
                print(f"    → 変換エラー: {e}")
        else:
            code_to_start_time[code] = None
    
    print(f"\n最終的なcode_to_start_time:")
    for code, start_time in code_to_start_time.items():
        print(f"  {code}: {start_time}")
    
    # 明け番の日付またぎ処理テスト
    print("\n3. 明け番の日付またぎ処理テスト")
    print("-" * 40)
    
    # 明け番のシフト定義を取得
    ake_code = "明"
    ake_start_time = code_to_start_time.get(ake_code)
    
    print(f"明け番コード '{ake_code}' の開始時間: {ake_start_time}")
    
    if ake_start_time:
        # テスト用の時間スロット
        test_slots = ["00:00", "01:00", "02:00", "08:00", "09:00", "10:00"]
        test_date = dt.date(2025, 6, 15)  # テスト日付
        
        print(f"\nテスト日付: {test_date}")
        print(f"明け番開始時間: {ake_start_time}")
        
        for slot_str in test_slots:
            slot_time = dt.datetime.strptime(slot_str, "%H:%M").time()
            
            # io_excel.pyと同じ日付またぎ判定
            current_date = test_date
            if ake_start_time and slot_time < ake_start_time:
                current_date += dt.timedelta(days=1)
                cross_midnight = True
            else:
                cross_midnight = False
            
            final_datetime = dt.datetime.combine(current_date, slot_time)
            
            print(f"  スロット {slot_str}: {final_datetime} (日跨ぎ: {cross_midnight})")
    
    else:
        print("明け番の開始時間が取得できませんでした")
        
        # 可能性のある問題を診断
        print("\n問題診断:")
        print("1. 勤務区分シートに '明' コードが存在するか？")
        ake_in_codes = any('明' in str(row.iloc[0]) for _, row in wt_df.iterrows())
        print(f"   → {ake_in_codes}")
        
        print("2. 明け番の開始時間データが正しく読み込まれているか？")
        for idx, row in wt_df.iterrows():
            if '明' in str(row.iloc[0]):
                print(f"   明け番行 {idx+1}: {list(row)}")
        
        print("3. 時間データの形式は適切か？")
        for idx, row in wt_df.iterrows():
            for col_idx, cell in enumerate(row):
                if isinstance(cell, (dt.time, dt.datetime)):
                    print(f"   時間データ発見 行{idx+1}列{col_idx+1}: {cell} (型: {type(cell)})")

if __name__ == "__main__":
    debug_ake_processing()