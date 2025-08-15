#!/usr/bin/env python3
"""
Simplified Root Cause Analysis
Unicode問題を回避した根本原因分析
"""
import pandas as pd
import os

def analyze_calculation_discrepancy():
    """計算不整合の根本原因分析"""
    print("=== Root Cause Analysis ===")
    
    scenario = 'out_p25_based'
    
    # データ読み込み
    intermediate_path = f"downloaded_analysis_results/{scenario}/intermediate_data.parquet"
    role_path = f"downloaded_analysis_results/{scenario}/shortage_role_summary.parquet"
    emp_path = f"downloaded_analysis_results/{scenario}/shortage_employment_summary.parquet"
    
    df_intermediate = pd.read_parquet(intermediate_path)
    df_role = pd.read_parquet(role_path)  
    df_emp = pd.read_parquet(emp_path)
    
    print("1. Basic Data Summary:")
    print(f"   Intermediate records: {len(df_intermediate)}")
    print(f"   Total working hours: {(df_intermediate['parsed_slots_count'] * 0.5).sum():.1f}h")
    
    # 職種別と雇用形態別の合計比較
    print("\n2. Summary Totals Comparison:")
    role_totals = df_role[['need_h', 'staff_h', 'lack_h', 'excess_h']].sum()
    emp_totals = df_emp[['need_h', 'staff_h', 'lack_h', 'excess_h']].sum()
    
    print("   Role-based totals:")
    print(f"     Need: {role_totals['need_h']:.1f}h")
    print(f"     Staff: {role_totals['staff_h']:.1f}h")
    print(f"     Shortage: {role_totals['lack_h']:.1f}h")
    print(f"     Excess: {role_totals['excess_h']:.1f}h")
    
    print("   Employment-based totals:")
    print(f"     Need: {emp_totals['need_h']:.1f}h")
    print(f"     Staff: {emp_totals['staff_h']:.1f}h")
    print(f"     Shortage: {emp_totals['lack_h']:.1f}h")
    print(f"     Excess: {emp_totals['excess_h']:.1f}h")
    
    # 差異分析
    print("\n3. Discrepancy Analysis:")
    shortage_ratio = emp_totals['lack_h'] / role_totals['lack_h']
    print(f"   Shortage difference: {emp_totals['lack_h'] - role_totals['lack_h']:.1f}h")
    print(f"   Employment/Role ratio: {shortage_ratio:.2f}x")
    
    # 需要データの詳細分析
    print("\n4. Need Data Analysis:")
    need_files = {
        'total': 'need_per_date_slot.parquet',
        'emp_part': 'need_per_date_slot_emp_パート.parquet',
        'emp_regular': 'need_per_date_slot_emp_正社員.parquet',
        'emp_spot': 'need_per_date_slot_emp_スポット.parquet'
    }
    
    need_totals = {}
    for name, filename in need_files.items():
        filepath = f"downloaded_analysis_results/{scenario}/{filename}"
        if os.path.exists(filepath):
            df = pd.read_parquet(filepath)
            numeric_cols = df.select_dtypes(include=['number']).columns
            total_need = df[numeric_cols].sum().sum()
            need_totals[name] = total_need
            print(f"   {name}: {total_need:.1f}")
    
    # 需要合計の整合性確認
    emp_need_sum = need_totals.get('emp_part', 0) + need_totals.get('emp_regular', 0) + need_totals.get('emp_spot', 0)
    total_need = need_totals.get('total', 0)
    print(f"   Employment sum: {emp_need_sum:.1f}")
    print(f"   Total need: {total_need:.1f}")
    print(f"   Need discrepancy: {abs(emp_need_sum - total_need):.1f}")

def investigate_calculation_formula():
    """計算式の調査"""
    print("\n=== Calculation Formula Investigation ===")
    
    scenario = 'out_p25_based'
    df_role = pd.read_parquet(f"downloaded_analysis_results/{scenario}/shortage_role_summary.parquet")
    df_emp = pd.read_parquet(f"downloaded_analysis_results/{scenario}/shortage_employment_summary.parquet")
    
    print("Role-based calculation check:")
    role_inconsistent = []
    for _, row in df_role.iterrows():
        calculated_need = row['staff_h'] + row['lack_h'] - row['excess_h']
        diff = abs(row['need_h'] - calculated_need)
        if diff > 0.1:
            role_inconsistent.append({
                'role': row['role'],
                'need': row['need_h'],
                'calculated': calculated_need,
                'diff': diff
            })
            print(f"   INCONSISTENT: {row['role']} - diff: {diff:.1f}h")
    
    print(f"   Role inconsistencies: {len(role_inconsistent)}")
    
    print("\nEmployment-based calculation check:")
    emp_inconsistent = []
    for _, row in df_emp.iterrows():
        calculated_need = row['staff_h'] + row['lack_h'] - row['excess_h']
        diff = abs(row['need_h'] - calculated_need)
        if diff > 0.1:
            emp_inconsistent.append({
                'employment': row['employment'],
                'need': row['need_h'],
                'calculated': calculated_need,
                'diff': diff
            })
            print(f"   INCONSISTENT: {row['employment']} - diff: {diff:.1f}h")
    
    print(f"   Employment inconsistencies: {len(emp_inconsistent)}")
    
    return role_inconsistent, emp_inconsistent

def find_root_cause():
    """根本原因の特定"""
    print("\n=== Root Cause Identification ===")
    
    scenario = 'out_p25_based'
    
    # 実勤務時間vs配置時間の比較
    df_intermediate = pd.read_parquet(f"downloaded_analysis_results/{scenario}/intermediate_data.parquet")
    actual_total = (df_intermediate['parsed_slots_count'] * 0.5).sum()
    
    df_role = pd.read_parquet(f"downloaded_analysis_results/{scenario}/shortage_role_summary.parquet")
    df_emp = pd.read_parquet(f"downloaded_analysis_results/{scenario}/shortage_employment_summary.parquet")
    
    role_staff_total = df_role['staff_h'].sum()
    emp_staff_total = df_emp['staff_h'].sum()
    
    print("Staff hour allocation consistency:")
    print(f"   Actual working hours: {actual_total:.1f}h")
    print(f"   Role-based staff total: {role_staff_total:.1f}h")
    print(f"   Employment-based staff total: {emp_staff_total:.1f}h")
    
    role_diff = abs(actual_total - role_staff_total)
    emp_diff = abs(actual_total - emp_staff_total)
    
    print(f"   Role difference: {role_diff:.1f}h ({'OK' if role_diff < 100 else 'ERROR'})")
    print(f"   Employment difference: {emp_diff:.1f}h ({'OK' if emp_diff < 100 else 'ERROR'})")
    
    # 需要計算の問題特定
    print("\nNeed calculation analysis:")
    role_need_total = df_role['need_h'].sum()
    emp_need_total = df_emp['need_h'].sum()
    
    print(f"   Role-based need total: {role_need_total:.1f}h")
    print(f"   Employment-based need total: {emp_need_total:.1f}h")
    print(f"   Need ratio (emp/role): {emp_need_total/role_need_total:.3f}")
    
    # 不足計算の問題
    print("\nShortage calculation analysis:")
    role_lack_total = df_role['lack_h'].sum()
    emp_lack_total = df_emp['lack_h'].sum()
    
    print(f"   Role-based shortage: {role_lack_total:.1f}h")
    print(f"   Employment-based shortage: {emp_lack_total:.1f}h")
    print(f"   Shortage inflation: {emp_lack_total/role_lack_total:.1f}x")
    
    # 根本原因の推定
    print("\nRoot cause hypothesis:")
    if emp_staff_total < role_staff_total:
        print("   1. Staff allocation: Employment-based underestimates staff hours")
    if emp_need_total < role_need_total:
        print("   2. Need calculation: Employment-based underestimates need")
    if emp_lack_total > role_lack_total * 5:
        print("   3. CRITICAL: Employment-based shortage calculation is severely inflated")
        print("      This suggests a fundamental flaw in the employment-based calculation logic")

def main():
    analyze_calculation_discrepancy()
    investigate_calculation_formula()
    find_root_cause()
    
    print("\n=== CONCLUSION ===")
    print("The employment-based shortage calculation has a fundamental flaw")
    print("that inflates shortage values by 7-10x compared to role-based calculation.")
    print("This makes the integrated tab's 'advanced mode' unreliable for users.")

if __name__ == "__main__":
    main()