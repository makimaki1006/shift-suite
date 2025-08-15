#!/usr/bin/env python3
"""
Calculate Actual Discrepancy - Simple Analysis
実際の不整合を単純計算で確認
"""
import pandas as pd

def simple_calculation_check():
    """シンプルな計算チェック"""
    print("=== シンプル計算チェック ===")
    
    scenario = 'out_p25_based'
    
    # 職種別データ
    role_path = f"downloaded_analysis_results/{scenario}/shortage_role_summary.parquet"
    df_role = pd.read_parquet(role_path)
    
    # 雇用形態別データ  
    emp_path = f"downloaded_analysis_results/{scenario}/shortage_employment_summary.parquet"
    df_emp = pd.read_parquet(emp_path)
    
    print("職種別合計:")
    role_totals = df_role[['need_h', 'staff_h', 'lack_h', 'excess_h']].sum()
    print(f"  必要: {role_totals['need_h']:.1f}h")
    print(f"  配置: {role_totals['staff_h']:.1f}h")  
    print(f"  不足: {role_totals['lack_h']:.1f}h")
    print(f"  過剰: {role_totals['excess_h']:.1f}h")
    
    print("\n雇用形態別合計:")
    emp_totals = df_emp[['need_h', 'staff_h', 'lack_h', 'excess_h']].sum()
    print(f"  必要: {emp_totals['need_h']:.1f}h")
    print(f"  配置: {emp_totals['staff_h']:.1f}h")
    print(f"  不足: {emp_totals['lack_h']:.1f}h")  
    print(f"  過剰: {emp_totals['excess_h']:.1f}h")
    
    # 差異計算
    print("\n差異分析:")
    need_diff = emp_totals['need_h'] - role_totals['need_h']
    staff_diff = emp_totals['staff_h'] - role_totals['staff_h']
    lack_diff = emp_totals['lack_h'] - role_totals['lack_h']
    excess_diff = emp_totals['excess_h'] - role_totals['excess_h']
    
    print(f"  必要時間差異: {need_diff:.1f}h")
    print(f"  配置時間差異: {staff_diff:.1f}h")
    print(f"  不足時間差異: {lack_diff:.1f}h (雇用形態別が {lack_diff/role_totals['lack_h']:.1f}倍)")
    print(f"  過剰時間差異: {excess_diff:.1f}h")
    
    # 計算の妥当性チェック
    print("\n計算妥当性チェック:")
    
    print("職種別:")
    role_check = role_totals['staff_h'] + role_totals['lack_h'] - role_totals['excess_h']
    role_error = abs(role_check - role_totals['need_h'])
    print(f"  配置({role_totals['staff_h']:.1f}) + 不足({role_totals['lack_h']:.1f}) - 過剰({role_totals['excess_h']:.1f}) = {role_check:.1f}")
    print(f"  必要時間 = {role_totals['need_h']:.1f}")
    print(f"  誤差 = {role_error:.1f}h ({'OK' if role_error < 1 else 'ERROR'})")
    
    print("\n雇用形態別:")
    emp_check = emp_totals['staff_h'] + emp_totals['lack_h'] - emp_totals['excess_h']  
    emp_error = abs(emp_check - emp_totals['need_h'])
    print(f"  配置({emp_totals['staff_h']:.1f}) + 不足({emp_totals['lack_h']:.1f}) - 過剰({emp_totals['excess_h']:.1f}) = {emp_check:.1f}")
    print(f"  必要時間 = {emp_totals['need_h']:.1f}")
    print(f"  誤差 = {emp_error:.1f}h ({'OK' if emp_error < 1 else 'ERROR'})")

def check_intermediate_totals():
    """中間データとの整合性確認"""
    print("\n=== 中間データ整合性確認 ===")
    
    scenario = 'out_p25_based'
    intermediate_path = f"downloaded_analysis_results/{scenario}/intermediate_data.parquet"
    df_intermediate = pd.read_parquet(intermediate_path)
    
    # 実勤務時間（スロット×0.5）
    actual_hours = (df_intermediate['parsed_slots_count'] * 0.5).sum()
    print(f"実勤務時間合計: {actual_hours:.1f}h")
    
    # 雇用形態別実勤務時間
    emp_actual = df_intermediate.groupby('employment').apply(
        lambda x: (x['parsed_slots_count'] * 0.5).sum()
    )
    print("雇用形態別実勤務時間:")
    for emp, hours in emp_actual.items():
        print(f"  {emp}: {hours:.1f}h")
    emp_actual_total = emp_actual.sum()
    print(f"雇用形態別合計: {emp_actual_total:.1f}h")
    
    # 職種別実勤務時間  
    role_actual = df_intermediate.groupby('role').apply(
        lambda x: (x['parsed_slots_count'] * 0.5).sum()
    )
    print("職種別実勤務時間:")
    for role, hours in role_actual.items():
        print(f"  {role}: {hours:.1f}h")
    role_actual_total = role_actual.sum()
    print(f"職種別合計: {role_actual_total:.1f}h")
    
    # 整合性確認
    print(f"\n整合性確認:")
    print(f"  全体合計: {actual_hours:.1f}h")
    print(f"  雇用形態別合計: {emp_actual_total:.1f}h (差異: {abs(actual_hours-emp_actual_total):.1f}h)")
    print(f"  職種別合計: {role_actual_total:.1f}h (差異: {abs(actual_hours-role_actual_total):.1f}h)")

def main():
    print("=== 実際の計算不整合確認 ===")
    
    simple_calculation_check()
    check_intermediate_totals()
    
    print("\n=== 問題の特定 ===")
    print("雇用形態別の不足時間計算に明確な異常があります")
    print("これは統合タブのユーザー体験に直接影響します")

if __name__ == "__main__":
    main()