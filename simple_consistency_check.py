#!/usr/bin/env python3
"""
シンプルな一貫性チェック
"""

import pandas as pd
from pathlib import Path
import sys
import os

# パスを追加
sys.path.insert(0, os.getcwd())

def simple_consistency_check():
    """シンプルな一貫性チェック"""
    print("=== 客観的一貫性チェック ===")
    
    # 1. 基本ファイル確認
    print("\n[1. ファイル存在確認]")
    files = [
        "ショート_テスト用データ.xlsx",
        "dash_app.py", 
        "shift_suite/tasks/io_excel.py"
    ]
    
    for filepath in files:
        exists = Path(filepath).exists()
        status = "OK" if exists else "NG"
        print(f"  {status}: {filepath}")
    
    # 2. データ処理確認
    print("\n[2. データ処理確認]")
    try:
        from shift_suite.tasks.io_excel import ingest_excel
        print("  OK: shift_suite import成功")
        
        excel_path = Path("ショート_テスト用データ.xlsx")
        excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
        shift_sheets = [s for s in excel_file.sheet_names if "勤務" not in s]
        
        long_df, wt_df, unknown_codes = ingest_excel(
            excel_path,
            shift_sheets=shift_sheets,
            header_row=0,
            slot_minutes=30,
            year_month_cell_location="D1"
        )
        
        print(f"  OK: データ処理成功 ({len(long_df)}レコード)")
        
    except Exception as e:
        print(f"  NG: データ処理エラー - {e}")
        return
    
    # 3. データ品質確認
    print("\n[3. データ品質確認]")
    working_data = long_df[long_df['holiday_type'] == '通常勤務']
    
    print(f"  総レコード数: {len(long_df)}")
    print(f"  勤務レコード数: {len(working_data)}")
    print(f"  勤務比率: {len(working_data)/len(long_df)*100:.1f}%")
    
    # 職種・雇用形態確認
    roles = working_data['role'].nunique()
    employments = working_data['employment'].nunique()
    print(f"  職種数: {roles}")
    print(f"  雇用形態数: {employments}")
    
    # 日付範囲確認
    working_data['date'] = pd.to_datetime(working_data['ds']).dt.date
    unique_dates = working_data['date'].nunique()
    print(f"  日付数: {unique_dates}")
    
    # 4. 明番確認
    print("\n[4. 明番コード確認]")
    dawn_data = working_data[working_data['code'] == '明']
    print(f"  明番レコード数: {len(dawn_data)}")
    
    if len(dawn_data) > 0:
        dawn_data['hour'] = pd.to_datetime(dawn_data['ds']).dt.hour
        night_dawn = dawn_data[dawn_data['hour'].isin([0, 1, 2, 3, 4, 5])]
        print(f"  夜勤時間帯明番: {len(night_dawn)}レコード")
        print("  OK: 明番データ存在")
    else:
        print("  NG: 明番データなし")
    
    # 5. 不足時間計算の一貫性
    print("\n[5. 不足時間計算一貫性]")
    
    # シンプルな不足計算
    daily_counts = working_data.groupby(['date', 'time_slot']).size().reset_index(name='count')
    median_scenario = daily_counts.groupby('time_slot')['count'].median()
    
    # 実績vs必要の比較
    actual_by_slot = working_data.groupby('time_slot').size() / unique_dates
    shortage_simple = (median_scenario - actual_by_slot).clip(lower=0).sum() * 0.5
    
    print(f"  中央値シナリオ不足時間: {shortage_simple:.1f}時間")
    
    # 職種別不足（概算）
    role_shortages = {}
    for role in working_data['role'].unique():
        role_data = working_data[working_data['role'] == role]
        role_daily = role_data.groupby(['date', 'time_slot']).size().reset_index(name='count')
        if len(role_daily) > 0:
            role_median = role_daily.groupby('time_slot')['count'].median()
            role_actual = role_data.groupby('time_slot').size() / unique_dates
            role_shortage = (role_median - role_actual).clip(lower=0).sum() * 0.5
            role_shortages[role] = role_shortage
    
    total_role_shortage = sum(role_shortages.values())
    print(f"  職種別不足合計: {total_role_shortage:.1f}時間")
    
    # 雇用形態別不足（概算）
    emp_shortages = {}
    for emp in working_data['employment'].unique():
        emp_data = working_data[working_data['employment'] == emp]
        emp_daily = emp_data.groupby(['date', 'time_slot']).size().reset_index(name='count')
        if len(emp_daily) > 0:
            emp_median = emp_daily.groupby('time_slot')['count'].median()
            emp_actual = emp_data.groupby('time_slot').size() / unique_dates
            emp_shortage = (emp_median - emp_actual).clip(lower=0).sum() * 0.5
            emp_shortages[emp] = emp_shortage
    
    total_emp_shortage = sum(emp_shortages.values())
    print(f"  雇用形態別不足合計: {total_emp_shortage:.1f}時間")
    
    # 一貫性評価
    print(f"\n[6. 一貫性評価]")
    consistency_issues = []
    
    if abs(shortage_simple - total_role_shortage) > 1:
        consistency_issues.append(f"全体({shortage_simple:.1f}h) != 職種別({total_role_shortage:.1f}h)")
    
    if abs(shortage_simple - total_emp_shortage) > 1:
        consistency_issues.append(f"全体({shortage_simple:.1f}h) != 雇用形態別({total_emp_shortage:.1f}h)")
    
    if consistency_issues:
        print("  NG: 不整合発見")
        for issue in consistency_issues:
            print(f"    - {issue}")
    else:
        print("  OK: 計算一貫性確認")
    
    # 7. dash_app.py確認
    print("\n[7. ダッシュボード確認]")
    dash_path = Path("dash_app.py")
    if dash_path.exists():
        with open(dash_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        callback_count = content.count('@app.callback')
        shortage_mentions = content.count('shortage')
        
        print(f"  OK: dash_app.py存在")
        print(f"  コールバック数: {callback_count}")
        print(f"  shortage参照数: {shortage_mentions}")
    else:
        print("  NG: dash_app.py不存在")
    
    # 8. 総合評価
    print("\n[8. 総合評価]")
    
    score_elements = {
        "データ処理": len(long_df) > 0,
        "勤務データ": len(working_data) > 1000,
        "職種データ": roles >= 3,
        "雇用形態": employments >= 2,
        "明番データ": len(dawn_data) > 0,
        "日付完整性": unique_dates == 30,
        "計算一貫性": len(consistency_issues) == 0,
        "ダッシュボード": dash_path.exists()
    }
    
    passed = sum(score_elements.values())
    total = len(score_elements)
    score = passed / total * 100
    
    print(f"  整合性スコア: {passed}/{total} ({score:.1f}%)")
    
    if score >= 80:
        print("  判定: システム健全")
    elif score >= 60:
        print("  判定: 軽微な問題あり")
    else:
        print("  判定: 重大な問題あり")
    
    print("\n=== 一貫性チェック完了 ===")
    
    return {
        "score": score,
        "total_records": len(long_df),
        "working_records": len(working_data),
        "consistency_issues": consistency_issues
    }

if __name__ == "__main__":
    result = simple_consistency_check()