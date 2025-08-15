#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
夜勤・明け番の連続勤務パターン調査スクリプト

テストデータで夜勤と明け番の連続勤務がどのように記録されているかを詳しく分析
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

def analyze_night_shift_patterns():
    """夜勤・明け番の連続勤務パターンを詳細分析"""
    
    # ローカルコピーファイルを使用
    file_path = "test_shift_data.xlsx"
    
    if not os.path.exists(file_path):
        print(f"ファイルが見つかりません: {file_path}")
        return
    
    print("="*80)
    print("夜勤・明け番連続勤務パターン調査")
    print("="*80)
    
    try:
        # Excelファイルの全シート名を取得
        xl_file = pd.ExcelFile(file_path)
        print(f"利用可能シート: {xl_file.sheet_names}")
        print()
        
        # R7.6シートのデータを読み込み
        if 'R7.6' in xl_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name='R7.6')
            print("【R7.6シートのデータ構造】")
            print(f"行数: {len(df)}, 列数: {len(df.columns)}")
            print(f"列名: {list(df.columns)}")
            print()
            
            # データの最初の20行を表示
            print("【データサンプル（最初の20行）】")
            print(df.head(20).to_string())
            print()
            
            # 夜勤・明け番関連のデータを抽出
            analyze_shift_patterns(df)
            
        else:
            print("R7.6シートが見つかりません")
            
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()

def analyze_shift_patterns(df):
    """シフトパターンの詳細分析"""
    
    print("【1. データ構造の確認】")
    print("-"*50)
    print(f"データの形状: {df.shape}")
    print(f"列名一覧:\n{list(df.columns)}")
    print()
    
    # 6月2日-3日のデータを特に確認
    print("【2. 6月2日-3日の連続勤務パターンの確認】")
    print("-"*50)
    
    # 日付列を特定
    date_columns = []
    for col in df.columns:
        col_str = str(col)
        if any(keyword in col_str for keyword in ['日', '月', 'date', 'Date', '6']):
            date_columns.append(col)
    
    print(f"日付関連列: {date_columns}")
    
    # 6月2日、6月3日のデータを抽出
    june_2_3_data = []
    for index, row in df.iterrows():
        row_str = ' '.join([str(val) for val in row.values if pd.notna(val)])
        if any(pattern in row_str for pattern in ['6月2日', '6/2', '6-2', '6月3日', '6/3', '6-3']):
            june_2_3_data.append({
                'index': index,
                'row_data': row.to_dict(),
                'row_string': row_str
            })
    
    print(f"6月2日-3日関連データ件数: {len(june_2_3_data)}")
    
    if june_2_3_data:
        for i, data in enumerate(june_2_3_data):
            print(f"\n6月2-3日データ {i+1} (行{data['index']}):")
            for key, value in data['row_data'].items():
                if pd.notna(value) and str(value).strip():
                    print(f"  {key}: {value}")
    
    print("\n【3. 夜勤・明け番データの抽出】")
    print("-"*50)
    
    # シフト種別列を特定
    shift_columns = [col for col in df.columns if '勤務' in str(col) or 'シフト' in str(col) or '番' in str(col)]
    time_columns = [col for col in df.columns if '時間' in str(col) or '開始' in str(col) or '終了' in str(col)]
    
    print(f"シフト関連列: {shift_columns}")
    print(f"時間関連列: {time_columns}")
    print()
    
    # 夜勤・明け番のパターンを検索
    night_shift_patterns = []
    
    for index, row in df.iterrows():
        row_data = {}
        for col in df.columns:
            value = row[col]
            if pd.notna(value):
                value_str = str(value).lower()
                if any(keyword in value_str for keyword in ['夜', '明', 'night', 'morning']):
                    row_data[col] = value
        
        if row_data:
            night_shift_patterns.append({
                'row_index': index,
                'data': row_data,
                'full_row': row.to_dict()
            })
    
    print(f"夜勤・明け番関連データ件数: {len(night_shift_patterns)}")
    
    # 具体例を表示
    if night_shift_patterns:
        print("\n【2. 夜勤・明け番の具体例】")
        print("-"*50)
        
        for i, pattern in enumerate(night_shift_patterns[:10]):  # 最初の10件
            print(f"\n例{i+1} (行番号: {pattern['row_index']}):")
            for key, value in pattern['data'].items():
                print(f"  {key}: {value}")
    
    # 連続勤務パターンの分析
    analyze_consecutive_shifts(df, night_shift_patterns)
    
    # 時間データの分析
    analyze_time_patterns(df)

def analyze_consecutive_shifts(df, night_patterns):
    """連続勤務パターンの分析"""
    
    print("\n【3. 連続勤務パターンの分析】")
    print("-"*50)
    
    # 職員IDや名前を特定
    name_columns = [col for col in df.columns if '名' in str(col) or 'ID' in str(col) or '職員' in str(col)]
    date_columns = [col for col in df.columns if '日' in str(col) or '月' in str(col) or 'date' in str(col).lower()]
    
    print(f"職員識別列: {name_columns}")
    print(f"日付関連列: {date_columns}")
    
    if name_columns and date_columns:
        # 職員別の連続勤務を分析
        name_col = name_columns[0]
        date_col = date_columns[0]
        
        print(f"\n職員名列: {name_col}")
        print(f"日付列: {date_col}")
        
        # 各職員の勤務パターンを追跡
        staff_shifts = {}
        
        for index, row in df.iterrows():
            staff_name = row.get(name_col)
            date_value = row.get(date_col)
            
            if pd.notna(staff_name) and pd.notna(date_value):
                if staff_name not in staff_shifts:
                    staff_shifts[staff_name] = []
                
                staff_shifts[staff_name].append({
                    'index': index,
                    'date': date_value,
                    'row_data': row.to_dict()
                })
        
        print(f"\n職員数: {len(staff_shifts)}")
        
        # 連続勤務の例を検索
        find_consecutive_examples(staff_shifts)

def find_consecutive_examples(staff_shifts):
    """連続勤務の具体例を検索"""
    
    print("\n【4. 連続勤務の具体例】")
    print("-"*50)
    
    consecutive_examples = []
    
    for staff_name, shifts in staff_shifts.items():
        if len(shifts) >= 2:
            # 日付順にソート
            shifts_sorted = sorted(shifts, key=lambda x: x['date'] if pd.notna(x['date']) else datetime.min)
            
            for i in range(len(shifts_sorted) - 1):
                current_shift = shifts_sorted[i]
                next_shift = shifts_sorted[i + 1]
                
                # 連続する日付かチェック
                try:
                    current_date = pd.to_datetime(current_shift['date'])
                    next_date = pd.to_datetime(next_shift['date'])
                    
                    if (next_date - current_date).days == 1:
                        # 夜勤→明け番パターンをチェック
                        current_row = current_shift['row_data']
                        next_row = next_shift['row_data']
                        
                        current_has_night = any('夜' in str(v) for v in current_row.values() if pd.notna(v))
                        next_has_morning = any('明' in str(v) for v in next_row.values() if pd.notna(v))
                        
                        if current_has_night or next_has_morning:
                            consecutive_examples.append({
                                'staff': staff_name,
                                'date1': current_date,
                                'date2': next_date,
                                'shift1': current_row,
                                'shift2': next_row
                            })
                except:
                    continue
    
    print(f"連続勤務例の発見数: {len(consecutive_examples)}")
    
    # 具体例を表示
    for i, example in enumerate(consecutive_examples[:5]):  # 最初の5例
        print(f"\n連続勤務例 {i+1}:")
        print(f"職員: {example['staff']}")
        print(f"日付1: {example['date1'].strftime('%Y-%m-%d')} → 日付2: {example['date2'].strftime('%Y-%m-%d')}")
        
        print("  1日目のデータ:")
        for key, value in example['shift1'].items():
            if pd.notna(value) and str(value).strip():
                print(f"    {key}: {value}")
        
        print("  2日目のデータ:")
        for key, value in example['shift2'].items():
            if pd.notna(value) and str(value).strip():
                print(f"    {key}: {value}")

def analyze_time_patterns(df):
    """時間パターンの分析"""
    
    print("\n【5. 時間データの詳細分析】")
    print("-"*50)
    
    time_patterns = []
    
    for index, row in df.iterrows():
        for col in df.columns:
            value = str(row[col]) if pd.notna(row[col]) else ""
            
            # 時間パターンを検索（16:45-0:00, 0:00-10:00 など）
            if any(pattern in value for pattern in [':', '-', '～', '〜']):
                if any(time_marker in value for time_marker in ['0:00', '00:00', '16:', '10:', '夜', '明']):
                    time_patterns.append({
                        'row': index,
                        'column': col,
                        'value': value,
                        'full_row': row.to_dict()
                    })
    
    print(f"時間パターン発見数: {len(time_patterns)}")
    
    # 0:00をまたぐパターンを特定
    midnight_patterns = [p for p in time_patterns if '0:00' in p['value'] or '00:00' in p['value']]
    
    print(f"0:00関連パターン: {len(midnight_patterns)}")
    
    if midnight_patterns:
        print("\n【0:00関連の時間パターン詳細】")
        for i, pattern in enumerate(midnight_patterns):
            print(f"\n{i+1}. 行{pattern['row']}, 列'{pattern['column']}':")
            print(f"   時間値: {pattern['value']}")
            # 同じ行の他の関連データも表示
            relevant_data = {}
            for key, val in pattern['full_row'].items():
                if pd.notna(val) and str(val).strip():
                    val_str = str(val)
                    if any(keyword in val_str for keyword in ['夜', '明', '職員', '名前', '6月', '時間']):
                        relevant_data[key] = val
            
            if relevant_data:
                print("   関連データ:")
                for key, val in relevant_data.items():
                    print(f"     {key}: {val}")
    
    # 特に16:45-0:00と0:00-10:00のパターンを検索
    print("\n【6. 夜勤→明け番の具体的時間パターン】")
    print("-"*50)
    
    night_patterns = []
    morning_patterns = []
    
    for pattern in time_patterns:
        value = pattern['value']
        if '16:' in value and '0:00' in value:
            night_patterns.append(pattern)
        elif '0:00' in value and '10:' in value:
            morning_patterns.append(pattern)
    
    print(f"夜勤パターン (16:xx-0:00): {len(night_patterns)}")
    print(f"明け番パターン (0:00-10:xx): {len(morning_patterns)}")
    
    if night_patterns:
        print("\n夜勤パターン例:")
        for i, pattern in enumerate(night_patterns[:3]):
            print(f"  {i+1}. 行{pattern['row']}: {pattern['value']}")
    
    if morning_patterns:
        print("\n明け番パターン例:")
        for i, pattern in enumerate(morning_patterns[:3]):
            print(f"  {i+1}. 行{pattern['row']}: {pattern['value']}")
    
    # 0:00の重複問題を分析
    analyze_midnight_overlap(df, night_patterns, morning_patterns)

def analyze_midnight_overlap(df, night_patterns, morning_patterns):
    """0:00での重複問題を詳細分析"""
    
    print("\n【7. 0:00重複問題の分析】")
    print("-"*50)
    
    print("連続勤務において、以下の問題が発生する可能性があります:")
    print("- 6月2日 16:45-0:00 (夜勤終了)")
    print("- 6月3日 0:00-10:00 (明け番開始)")
    print("→ 0:00が両方に含まれる場合、重複カウントされる可能性")
    print()
    
    # 同一職員で連続する夜勤→明け番パターンを探す
    overlapping_patterns = []
    
    for night in night_patterns:
        for morning in morning_patterns:
            # 行番号が近い（連続する日）かチェック
            if abs(night['row'] - morning['row']) <= 2:
                # 同じ職員かチェック
                night_row = night['full_row']
                morning_row = morning['full_row']
                
                # 職員名が一致するかチェック
                staff_match = False
                for key in night_row.keys():
                    if pd.notna(night_row.get(key)) and pd.notna(morning_row.get(key)):
                        if str(night_row[key]) == str(morning_row[key]) and '職員' in str(key):
                            staff_match = True
                            break
                
                if staff_match or abs(night['row'] - morning['row']) == 1:
                    overlapping_patterns.append({
                        'night': night,
                        'morning': morning,
                        'gap': abs(night['row'] - morning['row'])
                    })
    
    print(f"潜在的な0:00重複パターン: {len(overlapping_patterns)}")
    
    if overlapping_patterns:
        print("\n【潜在的重複の具体例】")
        for i, overlap in enumerate(overlapping_patterns[:3]):
            print(f"\n重複例 {i+1}:")
            print(f"夜勤 (行{overlap['night']['row']}): {overlap['night']['value']}")
            print(f"明け番 (行{overlap['morning']['row']}): {overlap['morning']['value']}")
            print(f"行間隔: {overlap['gap']}")
            
            # 重複している時間を明示
            print("→ 問題: 両方に0:00が含まれており、工数計算時に重複する可能性")
    
    # 推奨される処理方法を提示
    print("\n【推奨される連続勤務処理方法】")
    print("-"*50)
    print("1. 排他的時間範囲での記録:")
    print("   - 夜勤: 16:45-23:59")
    print("   - 明け番: 0:00-10:00")
    print()
    print("2. 連続勤務フラグの追加:")
    print("   - 夜勤と明け番を連続勤務として識別")
    print("   - 0:00での切り替わりを適切に処理")
    print()
    print("3. 工数計算時の調整:")
    print("   - 16:45-0:00 = 7時間15分")
    print("   - 0:00-10:00 = 10時間")
    print("   - 合計: 17時間15分（0:00の重複なし）")

if __name__ == "__main__":
    analyze_night_shift_patterns()