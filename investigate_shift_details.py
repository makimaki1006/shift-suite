#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
勤務区分シートの詳細調査と夜勤・明け番の時間パターン分析
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

def analyze_shift_details():
    """勤務区分シートの詳細分析"""
    
    file_path = "test_shift_data.xlsx"
    
    if not os.path.exists(file_path):
        print(f"ファイルが見つかりません: {file_path}")
        return
    
    print("="*80)
    print("勤務区分詳細調査 - 夜勤・明け番の時間パターン分析")
    print("="*80)
    
    try:
        xl_file = pd.ExcelFile(file_path)
        print(f"利用可能シート: {xl_file.sheet_names}")
        print()
        
        # 勤務区分シートを分析
        if '勤務区分' in xl_file.sheet_names:
            print("【勤務区分シートの分析】")
            print("-"*50)
            
            df_shift = pd.read_excel(file_path, sheet_name='勤務区分')
            print(f"勤務区分シートの形状: {df_shift.shape}")
            print(f"列名: {list(df_shift.columns)}")
            print()
            
            print("【勤務区分データの内容】")
            print(df_shift.to_string())
            print()
            
            # 夜勤・明け番の定義を検索
            analyze_night_shift_definitions(df_shift)
            
        # R7.6シートで実際のパターンを詳細分析
        analyze_actual_patterns(xl_file)
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()

def analyze_night_shift_definitions(df):
    """夜勤・明け番の定義を分析"""
    
    print("【夜勤・明け番の定義検索】")
    print("-"*50)
    
    night_definitions = []
    morning_definitions = []
    
    for index, row in df.iterrows():
        row_str = ' '.join([str(val) for val in row.values if pd.notna(val)])
        
        if any(keyword in row_str for keyword in ['夜', 'Night', 'night']):
            night_definitions.append({
                'index': index,
                'data': row.to_dict(),
                'text': row_str
            })
        
        if any(keyword in row_str for keyword in ['明', 'Morning', 'morning', 'AM']):
            morning_definitions.append({
                'index': index,
                'data': row.to_dict(),
                'text': row_str
            })
    
    print(f"夜勤関連定義: {len(night_definitions)}")
    for i, definition in enumerate(night_definitions):
        print(f"  夜勤定義 {i+1}:")
        for key, value in definition['data'].items():
            if pd.notna(value):
                print(f"    {key}: {value}")
        print()
    
    print(f"明け番関連定義: {len(morning_definitions)}")
    for i, definition in enumerate(morning_definitions):
        print(f"  明け番定義 {i+1}:")
        for key, value in definition['data'].items():
            if pd.notna(value):
                print(f"    {key}: {value}")
        print()

def analyze_actual_patterns(xl_file):
    """実際のシフトパターンを詳細分析"""
    
    print("【実際のシフトパターン詳細分析】")
    print("-"*50)
    
    df = pd.read_excel(xl_file, sheet_name='R7.6')
    
    # 具体的な時間パターンを検索
    time_patterns = find_time_patterns(df)
    
    # 連続勤務パターンを分析
    analyze_consecutive_patterns(df, time_patterns)
    
    # 6月2日-3日の具体例を抽出
    analyze_june_2_3_example(df)

def find_time_patterns(df):
    """詳細な時間パターンを検索"""
    
    print("【時間パターンの詳細検索】")
    print("-"*30)
    
    patterns = {
        'night_shift': [],    # 夜勤パターン
        'morning_shift': [],  # 明け番パターン
        'mixed_patterns': []  # 複合パターン
    }
    
    for index, row in df.iterrows():
        for col_idx, col in enumerate(df.columns):
            value = row[col]
            if pd.notna(value):
                value_str = str(value)
                
                # 時間を含むパターンを検索
                if ':' in value_str or '時' in value_str:
                    # 16:45や0:00などの時間パターン
                    if any(time_mark in value_str for time_mark in ['16:', '17:', '18:', '0:', '00:', '10:']):
                        pattern_info = {
                            'row': index,
                            'col': col,
                            'col_index': col_idx,
                            'value': value_str,
                            'full_row': row.to_dict()
                        }
                        
                        # パターン分類
                        if any(night_mark in value_str for night_mark in ['16:', '17:', '18:']):
                            if '0:' in value_str or '00:' in value_str:
                                patterns['night_shift'].append(pattern_info)
                        elif '0:' in value_str and '10:' in value_str:
                            patterns['morning_shift'].append(pattern_info)
                        else:
                            patterns['mixed_patterns'].append(pattern_info)
                
                # 記号パターンも検索（夜、明など）
                if any(symbol in value_str for symbol in ['夜', '明']):
                    symbol_info = {
                        'row': index,
                        'col': col,
                        'col_index': col_idx,
                        'value': value_str,
                        'type': 'symbol',
                        'full_row': row.to_dict()
                    }
                    
                    if '夜' in value_str:
                        patterns['night_shift'].append(symbol_info)
                    elif '明' in value_str:
                        patterns['morning_shift'].append(symbol_info)
    
    print(f"夜勤パターン数: {len(patterns['night_shift'])}")
    print(f"明け番パターン数: {len(patterns['morning_shift'])}")
    print(f"その他時間パターン数: {len(patterns['mixed_patterns'])}")
    
    return patterns

def analyze_consecutive_patterns(df, patterns):
    """連続勤務パターンの詳細分析"""
    
    print("\n【連続勤務パターンの詳細分析】")
    print("-"*30)
    
    # 同一行または隣接行での夜勤→明け番パターンを検索
    consecutive_cases = []
    
    for night in patterns['night_shift']:
        for morning in patterns['morning_shift']:
            # 同一職員（同一行）または隣接行の場合
            if night['row'] == morning['row']:
                # 同一行での連続パターン
                consecutive_cases.append({
                    'type': 'same_row',
                    'night': night,
                    'morning': morning,
                    'analysis': '同一行内での夜勤→明け番パターン'
                })
            elif abs(night['col_index'] - morning['col_index']) == 1:
                # 隣接列（隣接日）での連続パターン
                consecutive_cases.append({
                    'type': 'adjacent_day',
                    'night': night,
                    'morning': morning,
                    'analysis': '隣接日での夜勤→明け番パターン'
                })
    
    print(f"連続勤務パターン発見数: {len(consecutive_cases)}")
    
    for i, case in enumerate(consecutive_cases[:5]):  # 最初の5例
        print(f"\n連続勤務例 {i+1} ({case['type']}):")
        print(f"  夜勤: 行{case['night']['row']}, 列{case['night']['col']} = {case['night']['value']}")
        print(f"  明け番: 行{case['morning']['row']}, 列{case['morning']['col']} = {case['morning']['value']}")
        print(f"  分析: {case['analysis']}")
        
        # 職員情報を表示
        if '氏名' in case['night']['full_row']:
            print(f"  職員: {case['night']['full_row']['氏名']}")

def analyze_june_2_3_example(df):
    """6月2日-3日の具体例を詳細分析"""
    
    print("\n【6月2日-3日の連続勤務具体例】")
    print("-"*30)
    
    # 6月2日、3日の列を特定
    june_2_col = None
    june_3_col = None
    
    for col in df.columns:
        if isinstance(col, datetime):
            if col.month == 6 and col.day == 2:
                june_2_col = col
            elif col.month == 6 and col.day == 3:
                june_3_col = col
    
    if june_2_col is None or june_3_col is None:
        print("6月2日または6月3日の列が見つかりません")
        return
    
    print(f"6月2日列: {june_2_col}")
    print(f"6月3日列: {june_3_col}")
    
    # 6月2日-3日の連続勤務例を検索
    consecutive_examples = []
    
    for index, row in df.iterrows():
        june_2_value = row[june_2_col]
        june_3_value = row[june_3_col]
        
        if pd.notna(june_2_value) and pd.notna(june_3_value):
            june_2_str = str(june_2_value)
            june_3_str = str(june_3_value)
            
            # 夜勤→明け番パターンをチェック
            is_night_pattern = any(pattern in june_2_str for pattern in ['夜', '16:', '17:', '18:'])
            is_morning_pattern = any(pattern in june_3_str for pattern in ['明', '0:', '00:', '10:'])
            
            if is_night_pattern or is_morning_pattern:
                consecutive_examples.append({
                    'row': index,
                    'staff': row.get('氏名', 'N/A'),
                    'june_2': june_2_str,
                    'june_3': june_3_str,
                    'is_consecutive': is_night_pattern and is_morning_pattern
                })
    
    print(f"\n6月2日-3日の勤務パターン: {len(consecutive_examples)}")
    
    for i, example in enumerate(consecutive_examples):
        print(f"\n例 {i+1}:")
        print(f"  職員: {example['staff']}")
        print(f"  6月2日: {example['june_2']}")
        print(f"  6月3日: {example['june_3']}")
        print(f"  連続勤務判定: {'はい' if example['is_consecutive'] else 'いいえ'}")
        
        if example['is_consecutive']:
            print("  → 潜在的0:00重複リスク: あり")
            print("  → 推奨対応: 16:45-23:59 + 0:00-10:00として分離処理")

if __name__ == "__main__":
    analyze_shift_details()