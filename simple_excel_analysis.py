#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Excelファイル分析（文字化ke対策版）
"""
import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
import json
import re
from datetime import datetime, date

def analyze_excel_structure():
    """3つのExcelファイルの構造分析"""
    test_files = [
        {
            'path': r"C:\Users\fuji1\OneDrive\デスクトップ\シフト分析\ショート_テスト用データ.xlsx",
            'name': "short"
        },
        {
            'path': r"C:\Users\fuji1\OneDrive\デスクトップ\シフト分析\デイ_テスト用データ_休日精緻.xlsx", 
            'name': "day"
        },
        {
            'path': r"C:\Users\fuji1\OneDrive\デスクトップ\シフト分析\テストデータ_2024 本木ショート（7～9月）.xlsx",
            'name': "three_months"
        }
    ]
    
    results = {}
    
    for file_info in test_files:
        print(f"\n=== {file_info['name']} ===")
        
        try:
            excel_file = pd.ExcelFile(file_info['path'])
            sheets = excel_file.sheet_names
            print(f"Sheets: {len(sheets)} - {sheets}")
            
            file_result = {
                'sheets': sheets,
                'shift_data': {}
            }
            
            # 実績シートの詳細分析
            shift_sheets = [s for s in sheets if s != "勤務区分"]
            
            for sheet in shift_sheets:
                try:
                    df = pd.read_excel(file_info['path'], sheet_name=sheet)
                    print(f"  {sheet}: {df.shape}")
                    
                    # 日付列の検出
                    date_columns = []
                    for col in df.columns:
                        col_str = str(col)
                        # 日付らしい列を検出
                        if isinstance(col, datetime):
                            date_columns.append(col)
                        elif re.match(r'^\d{4}-\d{2}-\d{2}', col_str):
                            date_columns.append(col)
                        elif re.match(r'^\d{1,2}$', col_str):
                            # 日付の日部分の可能性
                            try:
                                day_num = int(col_str)
                                if 1 <= day_num <= 31:
                                    date_columns.append(col)
                            except:
                                pass
                    
                    # スタッフ関連列の検出
                    staff_columns = []
                    for col in df.columns:
                        col_str = str(col).lower()
                        if any(keyword in col_str for keyword in ['氏名', 'name', 'staff', '名前']):
                            staff_columns.append(col)
                    
                    # 実際のスタッフ数をカウント
                    staff_count = 0
                    if staff_columns:
                        staff_col = staff_columns[0]
                        staff_data = df[staff_col].dropna()
                        # 空文字列や特殊文字を除外
                        valid_staff = staff_data[~staff_data.str.strip().isin(['', 'nan', 'NaN'])]
                        staff_count = len(valid_staff.unique())
                    
                    print(f"    Date columns: {len(date_columns)}")
                    print(f"    Staff count: {staff_count}")
                    
                    # データ密度の計算（実際のデータ／全セル）
                    total_data_cells = df.shape[0] * len(date_columns) if date_columns else 0
                    non_empty_cells = 0
                    if date_columns and total_data_cells > 0:
                        for col in date_columns:
                            non_empty = df[col].notna().sum()
                            non_empty_cells += non_empty
                        
                        data_density = non_empty_cells / total_data_cells if total_data_cells > 0 else 0
                        print(f"    Data density: {data_density:.2f}")
                    
                    # 期間の推定
                    period_days = len(date_columns)
                    period_months = period_days / 30 if period_days > 0 else 0
                    
                    file_result['shift_data'][sheet] = {
                        'shape': df.shape,
                        'date_columns': len(date_columns),
                        'staff_count': staff_count,
                        'period_days': period_days,
                        'period_months': period_months
                    }
                    
                except Exception as e:
                    print(f"    Error in {sheet}: {e}")
            
            results[file_info['name']] = file_result
            
        except Exception as e:
            print(f"Error analyzing {file_info['name']}: {e}")
    
    # 結果の比較分析
    print(f"\n=== COMPARISON ANALYSIS ===")
    
    total_analysis = {}
    for name, data in results.items():
        total_days = 0
        total_staff = 0
        sheet_count = 0
        
        for sheet_name, sheet_data in data.get('shift_data', {}).items():
            total_days += sheet_data.get('period_days', 0)
            total_staff += sheet_data.get('staff_count', 0)
            sheet_count += 1
        
        total_months = total_days / 30 if total_days > 0 else 0
        
        total_analysis[name] = {
            'total_days': total_days,
            'total_months': total_months,
            'total_staff': total_staff,
            'shift_sheets': sheet_count
        }
        
        print(f"{name}:")
        print(f"  Period: {total_days} days ({total_months:.1f} months)")
        print(f"  Staff: {total_staff} people")
        print(f"  Sheets: {sheet_count}")
    
    # 3ヶ月データの問題分析
    if 'three_months' in total_analysis:
        three_month = total_analysis['three_months']
        print(f"\n=== THREE MONTHS DATA ANALYSIS ===")
        print(f"Actual period: {three_month['total_months']:.1f} months")
        
        if three_month['total_months'] >= 2.5:
            print("Period is valid for 3-month analysis")
            
            # 期間依存性による不足時間増大の予測
            # 仮定: 1ヶ月あたり平均3000時間の不足が発生
            base_shortage_per_month = 3000
            predicted_total_shortage = base_shortage_per_month * three_month['total_months']
            
            print(f"Predicted shortage calculation:")
            print(f"  Base shortage per month: {base_shortage_per_month} hours")
            print(f"  Total predicted shortage: {predicted_total_shortage:.0f} hours")
            
            # 27,486.5時間との比較
            actual_problem_hours = 27486.5
            if abs(predicted_total_shortage - actual_problem_hours) < 5000:
                print(f"MATCH: Predicted ({predicted_total_shortage:.0f}) close to actual ({actual_problem_hours})")
                print("This confirms the period dependency issue!")
            else:
                ratio = predicted_total_shortage / actual_problem_hours
                print(f"Ratio: {ratio:.2f} (predicted/actual)")
                if ratio > 0.5 and ratio < 2.0:
                    print("Reasonable correlation - period dependency likely")
                else:
                    print("Large difference - other factors may be involved")
        else:
            print("Period too short for 3-month analysis")
    
    # 結果をファイルに保存
    output_file = Path(__file__).parent / "excel_analysis_results.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'detailed_results': results,
                'summary': total_analysis
            }, f, ensure_ascii=False, indent=2, default=str)
        print(f"\nResults saved to: {output_file}")
    except Exception as e:
        print(f"Failed to save results: {e}")
    
    return results, total_analysis

if __name__ == "__main__":
    analyze_excel_structure()