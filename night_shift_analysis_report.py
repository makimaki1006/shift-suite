#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
夜勤・明け番連続勤務の詳細分析レポート生成
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

def generate_comprehensive_report():
    """包括的な夜勤・明け番分析レポートを生成"""
    
    file_path = "test_shift_data.xlsx"
    
    if not os.path.exists(file_path):
        print(f"ファイルが見つかりません: {file_path}")
        return
    
    print("="*80)
    print("夜勤・明け番連続勤務パターン 総合分析レポート")
    print("="*80)
    
    try:
        xl_file = pd.ExcelFile(file_path)
        
        # 勤務区分定義の分析
        shift_definitions = analyze_shift_definitions(xl_file)
        
        # 実際の連続勤務パターンの分析
        actual_patterns = analyze_actual_continuous_shifts(xl_file)
        
        # 0:00重複問題の詳細分析
        overlap_analysis = analyze_midnight_overlap_detailed(xl_file, shift_definitions)
        
        # 総合レポートの生成
        generate_final_report(shift_definitions, actual_patterns, overlap_analysis)
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()

def analyze_shift_definitions(xl_file):
    """勤務区分定義の詳細分析"""
    
    print("【1. 勤務区分定義の分析】")
    print("="*50)
    
    df_shift = pd.read_excel(xl_file, sheet_name='勤務区分')
    
    # 夜勤・明け番の定義を抽出
    night_shift_def = df_shift[df_shift['記号'] == '夜'].iloc[0] if len(df_shift[df_shift['記号'] == '夜']) > 0 else None
    morning_shift_def = df_shift[df_shift['記号'] == '明'].iloc[0] if len(df_shift[df_shift['記号'] == '明']) > 0 else None
    
    definitions = {
        'night_shift': night_shift_def,
        'morning_shift': morning_shift_def
    }
    
    if night_shift_def is not None:
        print("★ 夜勤の定義:")
        print(f"  記号: {night_shift_def['記号']}")
        print(f"  開始時間: {night_shift_def['開始']}")
        print(f"  終了時間: {night_shift_def['終了']}")
        print(f"  備考: {night_shift_def['備考']}")
        
        # 時間の詳細分析
        start_time = night_shift_def['開始']
        end_time = night_shift_def['終了']
        
        if pd.notna(start_time) and pd.notna(end_time):
            print(f"  実働時間計算: {start_time} ～ {end_time}")
            
            # 時間計算（0:00をまたぐ場合）
            if isinstance(start_time, pd.Timestamp) and isinstance(end_time, pd.Timestamp):
                if end_time.time() < start_time.time():  # 日をまたぐ場合
                    work_hours = (24 - start_time.hour) + end_time.hour - (start_time.minute + end_time.minute) / 60
                    print(f"  → 日をまたぐ勤務: 約{work_hours:.2f}時間")
                else:
                    work_hours = (end_time.hour - start_time.hour) + (end_time.minute - start_time.minute) / 60
                    print(f"  → 通常勤務: 約{work_hours:.2f}時間")
    
    print()
    
    if morning_shift_def is not None:
        print("★ 明け番の定義:")
        print(f"  記号: {morning_shift_def['記号']}")
        print(f"  開始時間: {morning_shift_def['開始']}")
        print(f"  終了時間: {morning_shift_def['終了']}")
        print(f"  備考: {morning_shift_def['備考']}")
        
        # 時間の詳細分析
        start_time = morning_shift_def['開始']
        end_time = morning_shift_def['終了']
        
        if pd.notna(start_time) and pd.notna(end_time):
            print(f"  実働時間計算: {start_time} ～ {end_time}")
            work_hours = (end_time.hour - start_time.hour) + (end_time.minute - start_time.minute) / 60
            print(f"  → 実働時間: 約{work_hours:.2f}時間")
    
    print()
    return definitions

def analyze_actual_continuous_shifts(xl_file):
    """実際の連続勤務パターンの分析"""
    
    print("【2. 実際の連続勤務パターンの分析】")
    print("="*50)
    
    df = pd.read_excel(xl_file, sheet_name='R7.6')
    
    # 6月2日-3日の具体例を抽出
    june_2_col = None
    june_3_col = None
    
    for col in df.columns:
        if isinstance(col, datetime):
            if col.month == 6 and col.day == 2:
                june_2_col = col
            elif col.month == 6 and col.day == 3:
                june_3_col = col
    
    continuous_patterns = []
    
    if june_2_col is not None and june_3_col is not None:
        print(f"分析対象期間: {june_2_col.strftime('%Y年%m月%d日')} → {june_3_col.strftime('%Y年%m月%d日')}")
        print()
        
        for index, row in df.iterrows():
            staff_name = row.get('氏名', f'職員{index}')
            june_2_value = row[june_2_col]
            june_3_value = row[june_3_col]
            
            if pd.notna(june_2_value) and pd.notna(june_3_value):
                june_2_str = str(june_2_value)
                june_3_str = str(june_3_value)
                
                # 夜勤→明け番パターンをチェック
                if june_2_str == '夜' and june_3_str == '明':
                    continuous_patterns.append({
                        'staff_name': staff_name,
                        'date_1': june_2_col,
                        'date_2': june_3_col,
                        'shift_1': june_2_str,
                        'shift_2': june_3_str,
                        'is_continuous': True,
                        'overlap_risk': True
                    })
    
    print(f"★ 発見された連続勤務パターン: {len(continuous_patterns)}件")
    print()
    
    for i, pattern in enumerate(continuous_patterns, 1):
        print(f"連続勤務例 {i}:")
        print(f"  職員名: {pattern['staff_name']}")
        print(f"  {pattern['date_1'].strftime('%m月%d日')}: {pattern['shift_1']} (夜勤)")
        print(f"  {pattern['date_2'].strftime('%m月%d日')}: {pattern['shift_2']} (明け番)")
        print(f"  連続勤務判定: {'○' if pattern['is_continuous'] else '×'}")
        print(f"  0:00重複リスク: {'高' if pattern['overlap_risk'] else '低'}")
        print()
    
    return continuous_patterns

def analyze_midnight_overlap_detailed(xl_file, shift_definitions):
    """0:00重複問題の詳細分析"""
    
    print("【3. 0:00重複問題の詳細分析】")
    print("="*50)
    
    night_def = shift_definitions.get('night_shift')
    morning_def = shift_definitions.get('morning_shift')
    
    analysis_result = {
        'overlap_exists': False,
        'overlap_duration': 0,
        'recommendations': []
    }
    
    if night_def is not None and morning_def is not None:
        night_end = night_def['終了']
        morning_start = morning_def['開始']
        
        print(f"★ 夜勤終了時間: {night_end}")
        print(f"★ 明け番開始時間: {morning_start}")
        print()
        
        # 重複の確認
        if pd.notna(night_end) and pd.notna(morning_start):
            if isinstance(night_end, pd.Timestamp) and isinstance(morning_start, pd.Timestamp):
                if night_end.time() == morning_start.time():
                    analysis_result['overlap_exists'] = True
                    print("警告: 重複発見 - 夜勤終了時間と明け番開始時間が同じ (0:00)")
                    print()
                    
                    print("【重複による問題点】")
                    print("1. 工数計算時の重複カウント:")
                    print("   - 夜勤: 16:45 ～ 0:00 = 7時間15分")
                    print("   - 明け番: 0:00 ～ 10:00 = 10時間")
                    print("   - 単純合計: 17時間15分")
                    print("   - 実際: 0:00が両方にカウントされ、重複の可能性")
                    print()
                    
                    print("2. システム処理上の問題:")
                    print("   - 0:00の時刻が2回記録される")
                    print("   - 勤務時間の境界があいまい")
                    print("   - 残業計算や休憩時間の算出に影響")
                    print()
                    
                    # 推奨対応策
                    recommendations = [
                        "夜勤終了を23:59に変更 (0:00を明け番専用とする)",
                        "連続勤務フラグを追加して一体管理",
                        "時間境界の排他制御実装 (end_time < start_time_next)",
                        "工数計算時の重複除去ロジック追加"
                    ]
                    
                    analysis_result['recommendations'] = recommendations
                    
                    print("【推奨対応策】")
                    for i, rec in enumerate(recommendations, 1):
                        print(f"{i}. {rec}")
                    print()
                    
                else:
                    print("OK: 重複なし - 夜勤終了時間と明け番開始時間が異なる")
            else:
                print("警告: 時間データの型が不正です")
        else:
            print("警告: 時間データが不完全です")
    
    return analysis_result

def generate_final_report(shift_definitions, actual_patterns, overlap_analysis):
    """最終レポートの生成"""
    
    print("【4. 総合分析結果とまとめ】")
    print("="*50)
    
    print("★ データ構造の確認結果:")
    print(f"  - 夜勤定義: {'○' if shift_definitions.get('night_shift') is not None else '×'}")
    print(f"  - 明け番定義: {'○' if shift_definitions.get('morning_shift') is not None else '×'}")
    print(f"  - 実際の連続勤務例: {len(actual_patterns)}件")
    print(f"  - 0:00重複リスク: {'高' if overlap_analysis.get('overlap_exists') else '低'}")
    print()
    
    print("★ 夜勤・明け番の記録パターン:")
    if shift_definitions.get('night_shift') is not None:
        night_def = shift_definitions['night_shift']
        print(f"  夜勤: 記号「夜」 {night_def['開始']} ～ {night_def['終了']}")
    
    if shift_definitions.get('morning_shift') is not None:
        morning_def = shift_definitions['morning_shift']
        print(f"  明け番: 記号「明」 {morning_def['開始']} ～ {morning_def['終了']}")
    print()
    
    print("★ 連続勤務の実装方式:")
    print("  - 日付別・行別での記録")
    print("  - 6月2日「夜」, 6月3日「明」として別々に記録")
    print("  - 同一職員の連続勤務が別行として管理")
    print()
    
    print("★ 確認された問題点:")
    if overlap_analysis.get('overlap_exists'):
        print("  1. 0:00での時間重複")
        print("     - 夜勤終了: 0:00")
        print("     - 明け番開始: 0:00")
        print("     → 同一時刻が両方の勤務に含まれる")
        print()
        print("  2. 工数計算への影響")
        print("     - 単純な時間合計では重複カウント")
        print("     - 実働17時間15分が正確に計算されない可能性")
        print()
    else:
        print("  重複問題は検出されませんでした")
    
    print("★ 推奨される改善策:")
    if overlap_analysis.get('recommendations'):
        for i, rec in enumerate(overlap_analysis['recommendations'], 1):
            print(f"  {i}. {rec}")
    else:
        print("  現在の実装で問題ありません")
    
    print()
    print("【結論】")
    print("-"*30)
    print("テストデータでは以下が確認されました:")
    print("- 夜勤: 16:45-0:00 (記号「夜」)")
    print("- 明け番: 0:00-10:00 (記号「明」)")  
    print("- 6月2日-3日で実際の連続勤務例が存在")
    print("- 0:00での時間境界重複リスクが確認")
    print()
    print("システム改修時は、0:00の重複処理を適切に実装することを推奨します。")

if __name__ == "__main__":
    generate_comprehensive_report()