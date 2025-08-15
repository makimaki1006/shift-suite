#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テストデータ_勤務表　勤務時間_トライアル.xlsxファイルの構造と内容分析
明け番の0:00開始勤務の記録形式を含めた詳細調査
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
import openpyxl
import os

def analyze_excel_file(file_path):
    """Excelファイルの詳細分析"""
    print(f"ファイル分析開始: {file_path}")
    print("=" * 80)
    
    # ファイル存在確認
    if not os.path.exists(file_path):
        print(f"エラー: ファイルが見つかりません: {file_path}")
        return
    
    try:
        # openpyxlでシート一覧取得
        wb = openpyxl.load_workbook(file_path, data_only=False)
        sheet_names = wb.sheetnames
        print(f"シート数: {len(sheet_names)}")
        print(f"シート名一覧: {sheet_names}")
        print()
        
        # 各シートの詳細分析
        for i, sheet_name in enumerate(sheet_names):
            print(f"【シート {i+1}: {sheet_name}】")
            print("-" * 60)
            
            try:
                # pandasでシート読み込み
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                print(f"シートサイズ: {df.shape[0]}行 × {df.shape[1]}列")
                
                # 空でない行の範囲を確認
                non_empty_rows = df.dropna(how='all').index
                if len(non_empty_rows) > 0:
                    print(f"データがある行: {non_empty_rows.min() + 1}行目 ～ {non_empty_rows.max() + 1}行目")
                
                # データの先頭部分を表示
                print("\n--- 最初の10行 × 10列のデータ ---")
                display_df = df.iloc[:10, :10]
                print(display_df.to_string(max_cols=10))
                
                # 時間データの特定と分析
                print("\n--- 時間データの分析 ---")
                analyze_time_data(df, sheet_name)
                
                # 明け番関連データの検索
                print("\n--- 明け番関連データの検索 ---")
                search_ake_data(df, sheet_name)
                
                print("\n")
                
            except Exception as e:
                print(f"シート読み込みエラー: {e}")
                print()
        
        wb.close()
        
    except Exception as e:
        print(f"ファイル読み込みエラー: {e}")

def analyze_time_data(df, sheet_name):
    """時間データの詳細分析"""
    time_patterns_found = []
    
    for row_idx in range(min(20, len(df))):
        for col_idx in range(min(20, len(df.columns))):
            cell_value = df.iloc[row_idx, col_idx]
            
            if pd.isna(cell_value):
                continue
                
            # 文字列の場合の時間パターン検索
            if isinstance(cell_value, str):
                # HH:MM形式のパターン
                if ':' in cell_value and any(char.isdigit() for char in cell_value):
                    time_patterns_found.append({
                        'position': f'行{row_idx+1}, 列{col_idx+1}',
                        'value': cell_value,
                        'type': 'string_time'
                    })
                # 0:00や24:00などの特殊パターン
                elif cell_value in ['0:00', '24:00', '00:00']:
                    time_patterns_found.append({
                        'position': f'行{row_idx+1}, 列{col_idx+1}',
                        'value': cell_value,
                        'type': 'special_time'
                    })
            
            # datetime型の場合
            elif isinstance(cell_value, (datetime, pd.Timestamp)):
                time_patterns_found.append({
                    'position': f'行{row_idx+1}, 列{col_idx+1}',
                    'value': cell_value,
                    'type': 'datetime'
                })
            
            # 数値型（Excelシリアル値の可能性）
            elif isinstance(cell_value, (int, float)):
                # 0-1の範囲の小数（時間のシリアル値の可能性）
                if 0 <= cell_value <= 1:
                    time_patterns_found.append({
                        'position': f'行{row_idx+1}, 列{col_idx+1}',
                        'value': cell_value,
                        'type': 'excel_serial'
                    })
    
    if time_patterns_found:
        print(f"時間データと思われるパターンを {len(time_patterns_found)} 個発見:")
        for pattern in time_patterns_found[:10]:  # 最初の10個まで表示
            print(f"  {pattern['position']}: {pattern['value']} ({pattern['type']})")
        if len(time_patterns_found) > 10:
            print(f"  ... 他に {len(time_patterns_found) - 10} 個")
    else:
        print("明確な時間データパターンは見つかりませんでした")

def search_ake_data(df, sheet_name):
    """明け番関連データの検索"""
    ake_patterns = []
    
    # 明け番を示すキーワード検索
    keywords = ['明け', 'アケ', 'ake', '0:00', '24:00', '00:00']
    
    for row_idx in range(len(df)):
        for col_idx in range(len(df.columns)):
            cell_value = df.iloc[row_idx, col_idx]
            
            if pd.isna(cell_value):
                continue
                
            cell_str = str(cell_value).lower()
            
            for keyword in keywords:
                if keyword.lower() in cell_str:
                    # 周辺のセルも含めて表示
                    context = get_cell_context(df, row_idx, col_idx)
                    ake_patterns.append({
                        'position': f'行{row_idx+1}, 列{col_idx+1}',
                        'value': cell_value,
                        'keyword': keyword,
                        'context': context
                    })
                    break
    
    if ake_patterns:
        print(f"明け番関連と思われるデータを {len(ake_patterns)} 個発見:")
        for pattern in ake_patterns:
            print(f"  {pattern['position']}: {pattern['value']} (キーワード: {pattern['keyword']})")
            print(f"    周辺データ: {pattern['context']}")
    else:
        print("明け番関連のデータは見つかりませんでした")

def get_cell_context(df, row_idx, col_idx, radius=2):
    """指定セル周辺のコンテキストを取得"""
    context = {}
    
    for r in range(max(0, row_idx-radius), min(len(df), row_idx+radius+1)):
        for c in range(max(0, col_idx-radius), min(len(df.columns), col_idx+radius+1)):
            if r == row_idx and c == col_idx:
                continue
            value = df.iloc[r, c]
            if not pd.isna(value):
                context[f'({r-row_idx:+d},{c-col_idx:+d})'] = value
    
    return context

def main():
    import sys
    import locale
    
    # 現在のディレクトリから相対パスで指定
    file_path = "./テストデータ_勤務表　勤務時間_トライアル.xlsx"
    
    # ファイル存在確認
    if not os.path.exists(file_path):
        # 別の形でファイルを探す
        import glob
        possible_files = glob.glob("*勤務表*勤務時間*トライアル*.xlsx")
        if possible_files:
            file_path = possible_files[0]
            print(f"ファイルを発見: {file_path}")
        else:
            print("該当するファイルが見つかりません")
            return
    
    analyze_excel_file(file_path)

if __name__ == "__main__":
    main()