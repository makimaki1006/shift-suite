#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
シンプルなExcelファイル分析テスト
"""
import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
import json

def analyze_excel_files():
    """3つのExcelファイルの基本分析"""
    test_files = [
        {
            'path': r"C:\Users\fuji1\OneDrive\デスクトップ\シフト分析\ショート_テスト用データ.xlsx",
            'name': "ショート"
        },
        {
            'path': r"C:\Users\fuji1\OneDrive\デスクトップ\シフト分析\デイ_テスト用データ_休日精緻.xlsx",
            'name': "デイ"
        },
        {
            'path': r"C:\Users\fuji1\OneDrive\デスクトップ\シフト分析\テストデータ_2024 本木ショート（7～9月）.xlsx",
            'name': "3ヶ月"
        }
    ]
    
    results = {}
    
    for file_info in test_files:
        print(f"\n{'='*50}")
        print(f"分析中: {file_info['name']}")
        print(f"{'='*50}")
        
        try:
            excel_file = pd.ExcelFile(file_info['path'])
            sheets = excel_file.sheet_names
            print(f"シート数: {len(sheets)}")
            print(f"シート名: {sheets}")
            
            file_results = {}
            
            # 勤務区分シートの分析
            if "勤務区分" in sheets:
                pattern_df = pd.read_excel(file_info['path'], sheet_name="勤務区分")
                print(f"勤務区分: {pattern_df.shape}")
                
                # 勤務パターンの分析
                if '記号' in pattern_df.columns or 'コード' in pattern_df.columns:
                    code_col = '記号' if '記号' in pattern_df.columns else 'コード'
                    codes = pattern_df[code_col].value_counts()
                    print(f"勤務コード数: {len(codes)}")
                    
                    # 休暇系コードの確認
                    rest_codes = [code for code in codes.index if str(code) in ['×', '休', '有', '希', '欠']]
                    if rest_codes:
                        print(f"休暇コード: {rest_codes}")
                
                file_results['pattern_count'] = len(pattern_df)
            
            # 実績シートの分析
            shift_sheets = [s for s in sheets if s != "勤務区分"]
            total_days = 0
            total_staff = 0
            
            for sheet in shift_sheets:
                try:
                    df = pd.read_excel(file_info['path'], sheet_name=sheet)
                    print(f"{sheet}: {df.shape}")
                    
                    # 日付列の推定
                    date_cols = []
                    for col in df.columns:
                        col_str = str(col)
                        if any(char.isdigit() for char in col_str) and len(col_str) <= 10:
                            date_cols.append(col)
                    
                    total_days += len(date_cols)
                    
                    # スタッフ数の推定
                    if '氏名' in df.columns:
                        staff_count = df['氏名'].nunique() - df['氏名'].isna().sum()
                        total_staff += staff_count
                        print(f"  スタッフ数: {staff_count}")
                    
                    print(f"  日付列数: {len(date_cols)}")
                    
                except Exception as e:
                    print(f"  {sheet} エラー: {e}")
            
            file_results.update({
                'sheet_count': len(sheets),
                'shift_sheets': len(shift_sheets),
                'total_days': total_days,
                'total_staff': total_staff,
                'estimated_period_months': total_days / 30 if total_days > 0 else 0
            })
            
            # 期間依存性の予測
            if total_days > 60:  # 2ヶ月以上
                months = total_days / 30
                estimated_shortage_per_month = 3000 * months  # 仮の計算
                print(f"期間: {total_days}日 ({months:.1f}ヶ月)")
                print(f"予想月間不足: {estimated_shortage_per_month:.0f}時間")
                
                if estimated_shortage_per_month > 10000:
                    print("⚠️ 期間依存問題の可能性: 高")
                elif estimated_shortage_per_month > 5000:
                    print("⚠️ 期間依存問題の可能性: 中")
            
            results[file_info['name']] = file_results
            
        except Exception as e:
            print(f"❌ ファイル分析エラー: {e}")
            results[file_info['name']] = {'error': str(e)}
    
    # 結果サマリー
    print(f"\n{'='*50}")
    print("分析結果サマリー")
    print(f"{'='*50}")
    
    for name, data in results.items():
        if 'error' not in data:
            print(f"{name}:")
            print(f"  期間: {data.get('total_days', 0)}日 ({data.get('estimated_period_months', 0):.1f}ヶ月)")
            print(f"  スタッフ: {data.get('total_staff', 0)}人")
            print(f"  実績シート: {data.get('shift_sheets', 0)}個")
    
    # 3ヶ月問題の検証
    if "3ヶ月" in results and 'error' not in results["3ヶ月"]:
        three_month_data = results["3ヶ月"]
        period_months = three_month_data.get('estimated_period_months', 0)
        
        print(f"\n🎯 3ヶ月データの問題検証:")
        print(f"実際の期間: {period_months:.1f}ヶ月")
        
        if period_months > 2.5:
            print("✅ 3ヶ月データとして妥当")
            # 期間依存性による不足時間の跳ね上がり予測
            single_month_shortage = 3000  # 仮定値
            predicted_shortage = single_month_shortage * period_months
            print(f"予測総不足時間: {predicted_shortage:.0f}時間")
            print(f"これが27,486.5時間問題の原因可能性: {'高' if predicted_shortage > 20000 else '中' if predicted_shortage > 10000 else '低'}")
        else:
            print("❌ 期間が短すぎる")
    
    return results

if __name__ == "__main__":
    analyze_excel_files()