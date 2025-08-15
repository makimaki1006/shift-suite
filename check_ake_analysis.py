#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
明け番の可視化問題を調査するスクリプト
テストデータと15分スロット分析結果を比較分析
"""

import pandas as pd
import zipfile
import os
import json
from datetime import datetime, time
import numpy as np

def analyze_ake_issue():
    """明け番可視化問題の詳細調査"""
    print("="*80)
    print("明け番可視化問題調査")
    print("="*80)
    
    # 1. テストデータの明け番定義確認
    print("1. テストデータの明け番定義確認")
    print("-" * 40)
    analyze_test_data_ake_definition()
    
    # 2. 15分スロット分析結果確認
    print("\n2. 15分スロット分析結果確認")
    print("-" * 40)
    analyze_15min_slot_results()
    
    # 3. 明け番の時間処理パターン分析
    print("\n3. 明け番の時間処理パターン分析")
    print("-" * 40)
    analyze_ake_time_patterns()

def analyze_test_data_ake_definition():
    """テストデータの明け番定義を詳細分析"""
    file_path = "./テストデータ_勤務表　勤務時間_トライアル.xlsx"
    
    try:
        # 勤務区分シートを詳細分析
        df_work_types = pd.read_excel(file_path, sheet_name="勤務区分", header=None)
        
        print("勤務区分シートの詳細:")
        for row_idx in range(len(df_work_types)):
            row_data = df_work_types.iloc[row_idx]
            row_values = [str(cell) if not pd.isna(cell) else '' for cell in row_data]
            
            # 明け関連の行を特定
            if any('明け' in str(cell) or 'アケ' in str(cell) or 'ake' in str(cell).lower() for cell in row_values):
                print(f"  明け番関連 行{row_idx+1}: {row_values}")
            
            # 0:00を含む行も確認
            if any('00:00:00' in str(cell) for cell in row_values):
                print(f"  0:00含む 行{row_idx+1}: {row_values}")
        
        # シフト表での明け番使用状況確認
        df_schedule = pd.read_excel(file_path, sheet_name="R7.6", header=None)
        
        print(f"\nシフト表での勤務パターン統計:")
        shift_patterns = {}
        
        for row_idx in range(2, min(len(df_schedule), 40)):  # スタッフデータ行
            for col_idx in range(3, min(len(df_schedule.columns), 35)):  # 日付列
                cell = df_schedule.iloc[row_idx, col_idx]
                if not pd.isna(cell):
                    shift_code = str(cell).strip()
                    if shift_code:
                        shift_patterns[shift_code] = shift_patterns.get(shift_code, 0) + 1
        
        # 明け番関連のシフトコードを確認
        print("明け番関連シフトコード:")
        ake_codes = {}
        for code, count in shift_patterns.items():
            if any(keyword in code.lower() for keyword in ['明け', 'アケ', 'ake', '明']):
                ake_codes[code] = count
        
        if ake_codes:
            for code, count in ake_codes.items():
                print(f"  {code}: {count}回")
        else:
            print("  明け番関連のシフトコードは見つかりませんでした")
            
        # 夜勤系のシフトコードを確認
        print("\n夜勤関連シフトコード:")
        night_codes = {}
        for code, count in shift_patterns.items():
            if any(keyword in code for keyword in ['夜', '準夜', '深夜', 'N', '夜勤']):
                night_codes[code] = count
        
        if night_codes:
            for code, count in night_codes.items():
                print(f"  {code}: {count}回")
        else:
            print("  夜勤関連のシフトコードは見つかりませんでした")
            
        # 全てのシフトコードを表示（上位20個）
        print(f"\n全シフトコード（上位20個）:")
        sorted_patterns = sorted(shift_patterns.items(), key=lambda x: x[1], reverse=True)
        for code, count in sorted_patterns[:20]:
            print(f"  {code}: {count}回")
            
    except Exception as e:
        print(f"エラー: {e}")

def analyze_15min_slot_results():
    """15分スロット分析結果の確認"""
    zip_path = "./analysis_results (17).zip"
    
    if not os.path.exists(zip_path):
        print("15分スロット分析結果ファイルが見つかりません")
        return
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            print(f"分析結果ファイル数: {len(file_list)}")
            
            # CSVファイルを探して内容確認
            csv_files = [f for f in file_list if f.endswith('.csv')]
            print(f"CSVファイル数: {len(csv_files)}")
            
            # 主要なCSVファイルを確認
            for csv_file in csv_files[:5]:
                print(f"\n--- {csv_file} ---")
                try:
                    with zip_ref.open(csv_file) as f:
                        df = pd.read_csv(f, encoding='utf-8')
                        print(f"サイズ: {df.shape}")
                        if len(df.columns) > 0:
                            print(f"列名: {list(df.columns)[:10]}")
                        
                        # 明け番関連データの検索
                        if 'shift_type' in df.columns or 'シフト' in str(df.columns):
                            ake_entries = df[df.astype(str).apply(lambda x: x.str.contains('明け|アケ|ake', case=False, na=False)).any(axis=1)]
                            if len(ake_entries) > 0:
                                print(f"明け番関連エントリ: {len(ake_entries)}件")
                                print(ake_entries.head())
                            
                        # 0:00関連データの検索
                        zero_time_entries = df[df.astype(str).apply(lambda x: x.str.contains('00:00', na=False)).any(axis=1)]
                        if len(zero_time_entries) > 0:
                            print(f"0:00関連エントリ: {len(zero_time_entries)}件")
                            print(zero_time_entries.head())
                            
                except Exception as e:
                    print(f"ファイル読み込みエラー: {e}")
                    
    except Exception as e:
        print(f"Zipファイル読み込みエラー: {e}")

def analyze_ake_time_patterns():
    """明け番の時間処理パターンを分析"""
    print("明け番の想定される時間パターン:")
    
    # 一般的な明け番パターンを分析
    patterns = [
        {
            'name': '夜勤明け（前日17:00～当日9:00）',
            'start': '17:00',
            'end': '09:00',
            'cross_midnight': True,
            'description': '前日夕方から翌日朝まで'
        },
        {
            'name': '準夜明け（前日21:00～当日6:00）',
            'start': '21:00', 
            'end': '06:00',
            'cross_midnight': True,
            'description': '前日夜から翌日早朝まで'
        },
        {
            'name': '深夜明け（00:00～10:00）',
            'start': '00:00',
            'end': '10:00', 
            'cross_midnight': False,
            'description': '0時から10時まで（当日内）'
        }
    ]
    
    for i, pattern in enumerate(patterns, 1):
        print(f"{i}. {pattern['name']}")
        print(f"   時間: {pattern['start']} ～ {pattern['end']}")
        print(f"   日跨ぎ: {'あり' if pattern['cross_midnight'] else 'なし'}")
        print(f"   説明: {pattern['description']}")
        print()
    
    # テストデータの勤務区分から実際のパターンを確認
    print("テストデータの明け番パターン確認:")
    file_path = "./テストデータ_勤務表　勤務時間_トライアル.xlsx"
    
    try:
        df = pd.read_excel(file_path, sheet_name="勤務区分")
        
        # 明け関連行を探す
        for idx, row in df.iterrows():
            row_str = ' '.join([str(cell) for cell in row if not pd.isna(cell)])
            if '明け' in row_str or 'アケ' in row_str:
                print(f"  発見: {list(row)}")
                
                # 時間データの抽出
                times = []
                for cell in row:
                    if isinstance(cell, time):
                        times.append(cell.strftime('%H:%M'))
                    elif isinstance(cell, str) and ':' in cell:
                        times.append(cell)
                
                if len(times) >= 2:
                    start_time, end_time = times[0], times[1]
                    print(f"    時間: {start_time} ～ {end_time}")
                    
                    # 日跨ぎの判定
                    if start_time > end_time:
                        print(f"    → 日跨ぎパターン（{start_time}開始、翌日{end_time}終了）")
                    else:
                        print(f"    → 当日完結パターン（{start_time}～{end_time}）")
    
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    analyze_ake_issue()