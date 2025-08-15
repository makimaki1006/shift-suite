#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Excelファイルの構造を詳細に分析するスクリプト
"""
import pandas as pd
import os
import sys

def analyze_excel_structure(file_path):
    """Excelファイルの構造を詳細分析"""
    print(f"\n=== {os.path.basename(file_path)} の分析 ===")
    
    try:
        # ファイルの存在確認
        if not os.path.exists(file_path):
            print(f"ファイルが存在しません: {file_path}")
            return
        
        # Excel ファイルのシート一覧を取得
        excel_file = pd.ExcelFile(file_path)
        print(f"シート数: {len(excel_file.sheet_names)}")
        print(f"シート名: {excel_file.sheet_names}")
        
        # 各シートの詳細分析
        for sheet_name in excel_file.sheet_names:
            print(f"\n--- シート: {sheet_name} ---")
            
            try:
                # データを読み込み（ヘッダーなしで最初の10行を確認）
                df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=10)
                print(f"サイズ（最初の10行）: {df_raw.shape}")
                print("最初の5行:")
                print(df_raw.head())
                
                # 実際のデータ行数を確認
                df_full = pd.read_excel(file_path, sheet_name=sheet_name)
                print(f"実際のデータサイズ: {df_full.shape}")
                print(f"列名: {list(df_full.columns)}")
                
                # データの型を確認
                print("データ型:")
                print(df_full.dtypes)
                
                # 欠損値の確認
                print(f"欠損値の数: {df_full.isnull().sum().sum()}")
                
                print("-" * 50)
                
            except Exception as e:
                print(f"シート {sheet_name} の読み込みエラー: {e}")
                
    except Exception as e:
        print(f"ファイル分析エラー: {e}")

def main():
    # テストファイルのパス
    test_files = [
        r"C:\Users\fuji1\OneDrive\デスクトップ\シフト分析\ショート_テスト用データ.xlsx",
        r"C:\Users\fuji1\OneDrive\デスクトップ\シフト分析\デイ_テスト用データ_休日精緻.xlsx",
        r"C:\Users\fuji1\OneDrive\デスクトップ\シフト分析\テストデータ_2024 本木ショート（7～9月）.xlsx"
    ]
    
    for file_path in test_files:
        analyze_excel_structure(file_path)

if __name__ == "__main__":
    main()