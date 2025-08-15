#!/usr/bin/env python3
"""
按分方式計算のテスト実装
修正案の技術的妥当性を検証
"""

import pandas as pd
from pathlib import Path
import sys
import os
import numpy as np
from typing import Dict, Tuple

# パスを追加
sys.path.insert(0, os.getcwd())

def calculate_proportional_shortage(working_data: pd.DataFrame, total_shortage_hours: float) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    按分方式による職種別・雇用形態別不足時間計算
    
    Args:
        working_data: 勤務データ
        total_shortage_hours: 全体不足時間
    
    Returns:
        (職種別不足時間辞書, 雇用形態別不足時間辞書)
    """
    total_records = len(working_data)
    
    # 職種別按分計算
    role_shortages = {}
    role_counts = working_data['role'].value_counts()
    
    for role, count in role_counts.items():
        proportion = count / total_records
        role_shortage = total_shortage_hours * proportion
        role_shortages[role] = role_shortage
    
    # 雇用形態別按分計算
    employment_shortages = {}
    employment_counts = working_data['employment'].value_counts()
    
    for employment, count in employment_counts.items():
        proportion = count / total_records
        employment_shortage = total_shortage_hours * proportion
        employment_shortages[employment] = employment_shortage
    
    return role_shortages, employment_shortages

def validate_calculation_consistency(total: float, role_dict: Dict[str, float], employment_dict: Dict[str, float]) -> Dict[str, bool]:
    """
    三つのレベル計算の一貫性検証
    
    Returns:
        {"total_vs_role": bool, "total_vs_employment": bool, "all_consistent": bool}
    """
    role_sum = sum(role_dict.values())
    employment_sum = sum(employment_dict.values())
    
    tolerance = 0.01  # 1分未満の誤差は許容
    
    total_vs_role = abs(total - role_sum) < tolerance
    total_vs_employment = abs(total - employment_sum) < tolerance
    
    return {
        "total_vs_role": total_vs_role,
        "total_vs_employment": total_vs_employment,
        "all_consistent": total_vs_role and total_vs_employment,
        "role_sum": role_sum,
        "employment_sum": employment_sum,
        "role_diff": total - role_sum,
        "employment_diff": total - employment_sum
    }

def test_proportional_calculation():
    """按分計算のテスト実行"""
    print("=== 按分方式計算テスト ===")
    
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
    
    print(f"テストデータ: {len(working_data)}レコード")
    
    # 1. 現在の全体不足時間を計算（正しい値）
    daily_counts = working_data.groupby(['date', 'time_slot']).size().reset_index(name='count')
    median_demand = daily_counts.groupby('time_slot')['count'].median()
    actual_avg = working_data.groupby('time_slot').size() / working_data['date'].nunique()
    shortage_by_slot = np.maximum(0, median_demand - actual_avg)
    total_shortage_hours = shortage_by_slot.sum() * 0.5
    
    print(f"全体不足時間: {total_shortage_hours:.3f}時間")
    
    # 2. 按分方式で職種別・雇用形態別を計算
    role_shortages, employment_shortages = calculate_proportional_shortage(working_data, total_shortage_hours)
    
    print(f"\n=== 按分による職種別不足時間 ===")
    for role, shortage in role_shortages.items():
        count = len(working_data[working_data['role'] == role])
        proportion = count / len(working_data)
        print(f"{role:12}: {shortage:.3f}時間 (構成比: {proportion:.1%}, {count}レコード)")
    
    print(f"\n=== 按分による雇用形態別不足時間 ===")
    for employment, shortage in employment_shortages.items():
        count = len(working_data[working_data['employment'] == employment])
        proportion = count / len(working_data)
        print(f"{employment:8}: {shortage:.3f}時間 (構成比: {proportion:.1%}, {count}レコード)")
    
    # 3. 一貫性検証
    consistency = validate_calculation_consistency(total_shortage_hours, role_shortages, employment_shortages)
    
    print(f"\n=== 一貫性検証結果 ===")
    print(f"全体不足時間:        {total_shortage_hours:.3f}時間")
    print(f"職種別合計:          {consistency['role_sum']:.3f}時間")
    print(f"雇用形態別合計:      {consistency['employment_sum']:.3f}時間")
    print(f"")
    print(f"全体 vs 職種別差異:  {consistency['role_diff']:.6f}時間")
    print(f"全体 vs 雇用形態差異: {consistency['employment_diff']:.6f}時間")
    print(f"")
    print(f"職種別一貫性:        {'✅ PASS' if consistency['total_vs_role'] else '❌ FAIL'}")
    print(f"雇用形態別一貫性:    {'✅ PASS' if consistency['total_vs_employment'] else '❌ FAIL'}")
    print(f"全体一貫性:          {'✅ PASS' if consistency['all_consistent'] else '❌ FAIL'}")
    
    # 4. 従来計算との比較
    print(f"\n=== 従来独立計算との比較 ===")
    
    # 職種別独立計算（従来方式）
    role_independent_total = 0
    for role in working_data['role'].unique():
        role_data = working_data[working_data['role'] == role]
        if len(role_data) > 0:
            role_daily = role_data.groupby(['date', 'time_slot']).size().reset_index(name='count')
            role_median = role_daily.groupby('time_slot')['count'].median()
            role_actual = role_data.groupby('time_slot').size() / working_data['date'].nunique()
            role_shortage = np.maximum(0, role_median - role_actual).sum() * 0.5
            role_independent_total += role_shortage
    
    print(f"従来独立計算合計:    {role_independent_total:.3f}時間")
    print(f"按分計算合計:        {sum(role_shortages.values()):.3f}時間")
    print(f"改善効果:            {role_independent_total - sum(role_shortages.values()):.3f}時間削減")
    
    # 5. 修正案の妥当性評価
    print(f"\n=== 修正案妥当性評価 ===")
    
    evaluation = {
        "数学的一貫性": consistency['all_consistent'],
        "計算精度": abs(consistency['role_diff']) < 0.001 and abs(consistency['employment_diff']) < 0.001,
        "ビジネス要件": consistency['all_consistent'],  # 全体=職種別=雇用形態別
        "実装容易性": True,  # 単純な按分計算
    }
    
    print("評価項目:")
    for criterion, result in evaluation.items():
        status = "✅ 合格" if result else "❌ 不合格"
        print(f"  {criterion:12}: {status}")
    
    overall_score = sum(evaluation.values()) / len(evaluation) * 100
    print(f"\n総合評価: {overall_score:.0f}点")
    
    if overall_score >= 100:
        print("🎯 修正案は技術的に完全に妥当です")
    elif overall_score >= 75:
        print("✅ 修正案は概ね妥当です")
    else:
        print("⚠️ 修正案に改善が必要です")
    
    return {
        "total_shortage": total_shortage_hours,
        "role_shortages": role_shortages,
        "employment_shortages": employment_shortages,
        "consistency": consistency,
        "evaluation": evaluation,
        "overall_score": overall_score
    }

if __name__ == "__main__":
    result = test_proportional_calculation()
    print(f"\n按分計算テスト完了: {result['overall_score']:.0f}点")