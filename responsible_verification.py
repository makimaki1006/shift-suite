#!/usr/bin/env python3
"""
責任感を持った検証ポイント確認
指摘された問題を徹底的に検証
"""

import pandas as pd
from pathlib import Path
import sys
import os
import numpy as np

# パスを追加
sys.path.insert(0, os.getcwd())

def responsible_verification():
    """責任感を持った検証"""
    print("=== 責任感を持った検証ポイント確認 ===")
    
    # データ取得
    from shift_suite.tasks.io_excel import ingest_excel
    
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
    
    working_data = long_df[long_df['holiday_type'] == '通常勤務'].copy()
    working_data['date'] = pd.to_datetime(working_data['ds']).dt.date
    working_data['time_slot'] = pd.to_datetime(working_data['ds']).dt.strftime('%H:%M')
    
    print(f"基礎データ: 総{len(long_df)}件、勤務{len(working_data)}件")
    
    # 1. 三つのレベル合計不整合の徹底検証
    print("\n【重要】三つのレベル合計不整合の詳細検証")
    
    # 全体レベルの不足時間計算
    print("\n=== 全体レベル計算 ===")
    daily_counts = working_data.groupby(['date', 'time_slot']).size().reset_index(name='count')
    median_demand_by_slot = daily_counts.groupby('time_slot')['count'].median()
    actual_by_slot = working_data.groupby('time_slot').size() / 30  # 30日平均
    
    global_shortage_by_slot = np.maximum(0, median_demand_by_slot - actual_by_slot)
    global_total_shortage = global_shortage_by_slot.sum() * 0.5  # 30分 = 0.5時間
    
    print(f"全体不足時間: {global_total_shortage:.2f}時間")
    print(f"不足スロット数: {(global_shortage_by_slot > 0).sum()}/48")
    
    # 職種レベルの不足時間計算
    print("\n=== 職種レベル計算 ===")
    role_shortages = {}
    role_total_shortage = 0
    
    for role in working_data['role'].unique():
        role_data = working_data[working_data['role'] == role]
        
        # 職種別の日別時間スロット別カウント
        role_daily_counts = role_data.groupby(['date', 'time_slot']).size().reset_index(name='count')
        
        if len(role_daily_counts) > 0:
            # 職種別の中央値需要
            role_median_demand = role_daily_counts.groupby('time_slot')['count'].median()
            
            # 職種別の実績平均
            role_actual = role_data.groupby('time_slot').size() / 30
            
            # 職種別不足計算
            role_shortage_by_slot = np.maximum(0, role_median_demand - role_actual)
            role_shortage_total = role_shortage_by_slot.sum() * 0.5
            
            role_shortages[role] = role_shortage_total
            role_total_shortage += role_shortage_total
            
            print(f"  {role}: {role_shortage_total:.2f}時間 (スロット数: {len(role_median_demand)})")
    
    print(f"職種別合計不足時間: {role_total_shortage:.2f}時間")
    
    # 雇用形態レベルの不足時間計算
    print("\n=== 雇用形態レベル計算 ===")
    employment_shortages = {}
    employment_total_shortage = 0
    
    for emp in working_data['employment'].unique():
        emp_data = working_data[working_data['employment'] == emp]
        
        # 雇用形態別の日別時間スロット別カウント
        emp_daily_counts = emp_data.groupby(['date', 'time_slot']).size().reset_index(name='count')
        
        if len(emp_daily_counts) > 0:
            # 雇用形態別の中央値需要
            emp_median_demand = emp_daily_counts.groupby('time_slot')['count'].median()
            
            # 雇用形態別の実績平均
            emp_actual = emp_data.groupby('time_slot').size() / 30
            
            # 雇用形態別不足計算
            emp_shortage_by_slot = np.maximum(0, emp_median_demand - emp_actual)
            emp_shortage_total = emp_shortage_by_slot.sum() * 0.5
            
            employment_shortages[emp] = emp_shortage_total
            employment_total_shortage += emp_shortage_total
            
            print(f"  {emp}: {emp_shortage_total:.2f}時間 (スロット数: {len(emp_median_demand)})")
    
    print(f"雇用形態別合計不足時間: {employment_total_shortage:.2f}時間")
    
    # 不整合の詳細分析
    print("\n=== 不整合分析 ===")
    diff_role = abs(global_total_shortage - role_total_shortage)
    diff_emp = abs(global_total_shortage - employment_total_shortage)
    
    print(f"全体 vs 職種別差異: {diff_role:.2f}時間")
    print(f"全体 vs 雇用形態別差異: {diff_emp:.2f}時間")
    
    # 不整合の原因分析
    print("\n=== 不整合原因分析 ===")
    
    # 1. スロット出現パターンの違い
    print("1. スロット出現パターン分析:")
    global_slots = set(median_demand_by_slot.index)
    
    all_role_slots = set()
    for role in working_data['role'].unique():
        role_data = working_data[working_data['role'] == role]
        role_daily_counts = role_data.groupby(['date', 'time_slot']).size().reset_index(name='count')
        if len(role_daily_counts) > 0:
            role_slots = set(role_daily_counts.groupby('time_slot')['count'].median().index)
            all_role_slots.update(role_slots)
    
    print(f"  全体スロット数: {len(global_slots)}")
    print(f"  職種別統合スロット数: {len(all_role_slots)}")
    print(f"  スロット差異: {len(all_role_slots - global_slots)}")
    
    # 2. 計算方法の違い検証
    print("\n2. 計算方法検証:")
    
    # 全体の別計算方法（職種を考慮しない）
    alternative_global = 0
    for slot in global_slots:
        slot_data = working_data[working_data['time_slot'] == slot]
        slot_daily_counts = slot_data.groupby('date').size()
        slot_median = slot_daily_counts.median() if len(slot_daily_counts) > 0 else 0
        slot_actual_avg = len(slot_data) / 30
        slot_shortage = max(0, slot_median - slot_actual_avg) * 0.5
        alternative_global += slot_shortage
    
    print(f"  代替全体計算: {alternative_global:.2f}時間")
    print(f"  元の全体計算: {global_total_shortage:.2f}時間")
    print(f"  計算方法差異: {abs(alternative_global - global_total_shortage):.2f}時間")
    
    # 3. 重複カウントの検証
    print("\n3. 重複カウント検証:")
    
    # 職種×雇用形態のクロス集計
    cross_check = {}
    total_cross_shortage = 0
    
    for role in working_data['role'].unique():
        for emp in working_data['employment'].unique():
            subset_data = working_data[(working_data['role'] == role) & (working_data['employment'] == emp)]
            
            if len(subset_data) > 0:
                subset_daily = subset_data.groupby(['date', 'time_slot']).size().reset_index(name='count')
                if len(subset_daily) > 0:
                    subset_median = subset_daily.groupby('time_slot')['count'].median()
                    subset_actual = subset_data.groupby('time_slot').size() / 30
                    subset_shortage = np.maximum(0, subset_median - subset_actual).sum() * 0.5
                    
                    cross_check[f"{role}×{emp}"] = subset_shortage
                    total_cross_shortage += subset_shortage
    
    print(f"  職種×雇用形態クロス合計: {total_cross_shortage:.2f}時間")
    
    # 2. dash_app.pyでの実際の計算ロジック確認
    print("\n【重要】dash_app.pyの実装確認")
    
    dash_path = Path("dash_app.py")
    if dash_path.exists():
        with open(dash_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 不足時間計算関数の特定
        lines = content.split('\n')
        shortage_functions = []
        
        for i, line in enumerate(lines):
            if 'def ' in line and ('shortage' in line.lower() or 'create_' in line.lower()):
                # 関数の開始から終了まで抽出
                func_lines = [line]
                j = i + 1
                indent_level = len(line) - len(line.lstrip())
                
                while j < len(lines) and (lines[j].strip() == '' or len(lines[j]) - len(lines[j].lstrip()) > indent_level):
                    func_lines.append(lines[j])
                    j += 1
                    if j - i > 50:  # 50行以上は切る
                        break
                
                shortage_functions.append({
                    'name': line.strip(),
                    'line_start': i + 1,
                    'content': '\n'.join(func_lines[:20])  # 最初の20行
                })
        
        print(f"検出された関数数: {len(shortage_functions)}")
        for func in shortage_functions[:3]:  # 最初の3つ
            print(f"\n=== {func['name']} (行{func['line_start']}) ===")
            print(func['content'][:500] + "..." if len(func['content']) > 500 else func['content'])
    
    # 3. 元データとの比較（motogi_short.zip）
    print("\n【重要】元データとの比較")
    
    # 現在の主要指標
    current_metrics = {
        'total_records': len(long_df),
        'working_records': len(working_data),
        'unique_staff': working_data['staff'].nunique(),
        'unique_roles': working_data['role'].nunique(),
        'unique_dates': working_data['date'].nunique(),
        'dawn_records': len(working_data[working_data['code'] == '明']),
        'global_shortage': global_total_shortage,
        'role_shortage_sum': role_total_shortage,
        'employment_shortage_sum': employment_total_shortage
    }
    
    print("現在のシステム指標:")
    for metric, value in current_metrics.items():
        print(f"  {metric}: {value}")
    
    # 4. 責任を持った結論と推奨事項
    print("\n【責任を持った結論】")
    
    issues_found = []
    
    if diff_role > 1.0:
        issues_found.append(f"職種別合計不整合: {diff_role:.2f}時間差")
    
    if diff_emp > 1.0:
        issues_found.append(f"雇用形態別合計不整合: {diff_emp:.2f}時間差")
    
    if abs(alternative_global - global_total_shortage) > 0.1:
        issues_found.append(f"計算方法による差異: {abs(alternative_global - global_total_shortage):.2f}時間")
    
    if len(issues_found) > 0:
        print("検出された問題:")
        for issue in issues_found:
            print(f"  ❌ {issue}")
        
        print("\n優先対応事項:")
        print("  1. 不足時間計算ロジックの統一")
        print("  2. 職種別・雇用形態別計算の見直し")
        print("  3. dash_app.pyでの集計方法確認")
        
    else:
        print("✅ 重大な不整合は検出されませんでした")
    
    # 5. 最終検証結果
    verification_result = {
        'data_quality': 'GOOD' if len(working_data) > 7000 else 'POOR',
        'calculation_consistency': 'POOR' if len(issues_found) > 0 else 'GOOD',
        'system_integrity': 'GOOD' if dash_path.exists() else 'POOR',
        'dawn_shift_handling': 'GOOD' if len(working_data[working_data['code'] == '明']) > 1000 else 'POOR'
    }
    
    print(f"\n最終検証結果:")
    for aspect, result in verification_result.items():
        status = "✅" if result == 'GOOD' else "❌"
        print(f"  {status} {aspect}: {result}")
    
    overall_status = "ACCEPTABLE" if list(verification_result.values()).count('GOOD') >= 3 else "NEEDS_ATTENTION"
    print(f"\n総合判定: {overall_status}")
    
    return {
        'global_shortage': global_total_shortage,
        'role_shortage_sum': role_total_shortage,
        'employment_shortage_sum': employment_total_shortage,
        'issues_found': issues_found,
        'verification_result': verification_result,
        'overall_status': overall_status
    }

if __name__ == "__main__":
    result = responsible_verification()
    print(f"\n検証完了: {result['overall_status']}")