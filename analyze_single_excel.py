#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
単一のExcelファイルを詳細分析するスクリプト
"""
import pandas as pd
import os
import sys

def analyze_single_excel(file_path):
    """単一のExcelファイルを詳細分析"""
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
        
        # 最初のシートのみ詳細分析
        if excel_file.sheet_names:
            sheet_name = excel_file.sheet_names[0]
            print(f"\n--- メインシート: {sheet_name} ---")
            
            try:
                # データを読み込み（ヘッダーなしで最初の20行を確認）
                df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=20)
                print(f"サイズ（最初の20行）: {df_raw.shape}")
                print("最初の10行:")
                print(df_raw.head(10))
                
                # 実際のデータ行数を確認
                df_full = pd.read_excel(file_path, sheet_name=sheet_name)
                print(f"\n実際のデータサイズ: {df_full.shape}")
                print(f"列名: {list(df_full.columns)[:10]}...")  # 最初の10列のみ表示
                
                # データの型を確認
                print(f"\nデータ型 (最初の5列):")
                print(df_full.dtypes.head())
                
                # 欠損値の確認
                print(f"\n総欠損値の数: {df_full.isnull().sum().sum()}")
                
                print("-" * 50)
                
            except Exception as e:
                print(f"シート {sheet_name} の読み込みエラー: {e}")
                
    except Exception as e:
        print(f"ファイル分析エラー: {e}")

def main():
    if len(sys.argv) != 2:
        print("使用法: python analyze_single_excel.py <ファイルパス>")
        return
    
    file_path = sys.argv[1]
    analyze_single_excel(file_path)

if __name__ == "__main__":
    main()