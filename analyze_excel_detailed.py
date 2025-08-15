#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テストデータ_勤務表　勤務時間_トライアル.xlsxファイルの詳細分析
明け番の記録形式に特化した詳細調査
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
import openpyxl
import os
import sys

def analyze_shift_file():
    """シフトファイルの詳細分析"""
    file_path = "./テストデータ_勤務表　勤務時間_トライアル.xlsx"
    
    print("="*80)
    print("テストデータ_勤務表　勤務時間_トライアル.xlsx ファイル分析")
    print("="*80)
    
    try:
        # Excelファイルの基本情報取得
        xl_file = pd.ExcelFile(file_path)
        sheet_names = xl_file.sheet_names
        
        print(f"ファイル存在確認: OK")
        print(f"シート数: {len(sheet_names)}")
        print(f"シート名: {sheet_names}")
        print()
        
        # 各シートの分析
        for sheet_name in sheet_names:
            print(f"【{sheet_name} シート分析】")
            print("-" * 60)
            
            # シート読み込み
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            
            print(f"シートサイズ: {df.shape[0]}行 × {df.shape[1]}列")
            
            if sheet_name == "R7.6":
                analyze_shift_schedule_sheet(df)
            elif "勤務" in sheet_name or "時間" in sheet_name:
                analyze_time_definition_sheet(df)
            
            print()
    
    except Exception as e:
        print(f"エラー: {e}")

def analyze_shift_schedule_sheet(df):
    """シフト表シートの分析"""
    print("\n--- シフト表構造分析 ---")
    
    # ヘッダー行の特定
    header_row = None
    date_cols = []
    
    for row_idx in range(min(5, len(df))):
        row_data = df.iloc[row_idx]
        date_count = 0
        
        for col_idx, cell in enumerate(row_data):
            if pd.isna(cell):
                continue
            # 日付データの検出
            if isinstance(cell, datetime) or (isinstance(cell, str) and "2025" in str(cell)):
                date_count += 1
                if date_count == 1:  # 最初の日付列を記録
                    date_cols.append(col_idx)
        
        if date_count >= 7:  # 1週間分以上の日付があればヘッダー行と判定
            header_row = row_idx
            break
    
    print(f"ヘッダー行: {header_row + 1}行目" if header_row is not None else "ヘッダー行: 特定できず")
    
    if header_row is not None:
        # 日付範囲の確認
        header_data = df.iloc[header_row]
        dates = []
        for i in range(len(header_data)):
            cell = header_data.iloc[i]
            if isinstance(cell, datetime):
                dates.append(cell)
        
        if dates:
            print(f"対象期間: {dates[0].strftime('%Y-%m-%d')} ～ {dates[-1].strftime('%Y-%m-%d')}")
            print(f"日数: {len(dates)}日")
    
    # スタッフデータの分析
    print("\n--- スタッフ・シフトデータ分析 ---")
    staff_data_start = (header_row + 2) if header_row is not None else 2
    
    shift_patterns = {}
    ake_shift_examples = []
    
    for row_idx in range(staff_data_start, min(staff_data_start + 20, len(df))):
        row_data = df.iloc[row_idx]
        
        if pd.isna(row_data.iloc[0]):  # スタッフ名がない行はスキップ
            continue
        
        staff_name = str(row_data.iloc[0])
        shifts = []
        
        # 各日のシフトデータを収集
        for col_idx in range(3, min(len(row_data), 33)):  # 日付列から開始
            cell = row_data.iloc[col_idx]
            if not pd.isna(cell):
                shift_code = str(cell)
                shifts.append(shift_code)
                
                # シフトパターンの集計
                if shift_code not in shift_patterns:
                    shift_patterns[shift_code] = 0
                shift_patterns[shift_code] += 1
                
                # 明け番関連のシフトを記録
                if any(keyword in shift_code.lower() for keyword in ['ake', '明け', 'アケ']):
                    ake_shift_examples.append({
                        'staff': staff_name,
                        'shift': shift_code,
                        'position': f'行{row_idx+1}, 列{col_idx+1}'
                    })
    
    print("発見されたシフトパターン:")
    for pattern, count in sorted(shift_patterns.items(), key=lambda x: x[1], reverse=True):
        print(f"  {pattern}: {count}回")
    
    if ake_shift_examples:
        print(f"\n明け番関連シフト発見: {len(ake_shift_examples)}件")
        for example in ake_shift_examples[:5]:
            print(f"  {example['position']}: {example['staff']} - {example['shift']}")
    else:
        print("\n明け番関連のシフトコードは見つかりませんでした")

def analyze_time_definition_sheet(df):
    """時間定義シートの分析"""
    print("\n--- 時間定義シート分析 ---")
    
    # 0:00を含む行の検索
    zero_time_entries = []
    time_definitions = []
    
    for row_idx in range(len(df)):
        for col_idx in range(len(df.columns)):
            cell = df.iloc[row_idx, col_idx]
            
            if pd.isna(cell):
                continue
            
            # 時間データの検出
            if isinstance(cell, time):
                time_definitions.append({
                    'position': f'行{row_idx+1}, 列{col_idx+1}',
                    'value': cell,
                    'type': 'time',
                    'formatted': cell.strftime('%H:%M:%S')
                })
                
                # 0:00の検出
                if cell.hour == 0 and cell.minute == 0:
                    # 周辺データを取得
                    context = get_row_context(df, row_idx)
                    zero_time_entries.append({
                        'position': f'行{row_idx+1}, 列{col_idx+1}',
                        'context': context
                    })
            
            # 文字列での時間データ
            elif isinstance(cell, str) and ':' in cell:
                if any(char.isdigit() for char in cell):
                    time_definitions.append({
                        'position': f'行{row_idx+1}, 列{col_idx+1}',
                        'value': cell,
                        'type': 'string',
                        'formatted': cell
                    })
    
    print(f"時間定義エントリ数: {len(time_definitions)}")
    
    if zero_time_entries:
        print(f"\n0:00時刻の発見: {len(zero_time_entries)}件")
        for entry in zero_time_entries:
            print(f"  {entry['position']}")
            print(f"    行データ: {entry['context']}")
    
    # 明け番の定義を探す
    print("\n--- 明け番定義の検索 ---")
    ake_definitions = []
    
    for row_idx in range(len(df)):
        row_data = df.iloc[row_idx]
        row_str = ' '.join([str(cell) for cell in row_data if not pd.isna(cell)])
        
        if any(keyword in row_str for keyword in ['明け', 'アケ', 'ake']):
            ake_definitions.append({
                'row': row_idx + 1,
                'data': [str(cell) if not pd.isna(cell) else '' for cell in row_data[:6]]
            })
    
    if ake_definitions:
        print("明け番関連の定義行:")
        for defn in ake_definitions:
            print(f"  行{defn['row']}: {defn['data']}")
    else:
        print("明け番の定義は見つかりませんでした")

def get_row_context(df, row_idx):
    """指定行の前後を含むコンテキストを取得"""
    context = []
    for r in range(max(0, row_idx-1), min(len(df), row_idx+2)):
        row_data = [str(cell) if not pd.isna(cell) else '' for cell in df.iloc[r]]
        context.append(f"行{r+1}: {row_data[:6]}")
    return context

if __name__ == "__main__":
    analyze_shift_file()