#!/usr/bin/env python3
"""
Deep Calculation Analysis
計算ロジックの根本的解析
"""
import pandas as pd
import os

def analyze_raw_calculation_flow():
    """生の計算フローを詳細解析"""
    print("=== 計算フロー根本解析 ===")
    
    scenario = 'out_p25_based'  # 按分廃止計算のシナリオ
    
    # 1. 中間データの詳細
    intermediate_path = f"downloaded_analysis_results/{scenario}/intermediate_data.parquet"
    df_intermediate = pd.read_parquet(intermediate_path)
    
    print("1. 中間データ基礎分析:")
    print(f"   総レコード数: {len(df_intermediate)}")
    print(f"   期間: {df_intermediate['ds'].min()} - {df_intermediate['ds'].max()}")
    
    # スタッフ×雇用形態×職種の実際の勤務時間
    print("\n2. 実際の勤務時間分析:")
    
    # スロットを時間に変換（0.5時間/スロット）
    df_intermediate['working_hours'] = df_intermediate['parsed_slots_count'] * 0.5
    
    # 雇用形態別集計
    emp_actual = df_intermediate.groupby('employment')['working_hours'].sum()
    print("   雇用形態別実勤務時間:")
    for emp, hours in emp_actual.items():
        print(f"     {emp}: {hours:.1f}時間")
    
    # 職種別集計
    role_actual = df_intermediate.groupby('role')['working_hours'].sum()
    print("   職種別実勤務時間:")
    for role, hours in role_actual.items():
        print(f"     {role}: {hours:.1f}時間")
    
    print(f"   全体実勤務時間: {df_intermediate['working_hours'].sum():.1f}時間")

def analyze_need_calculation_detail():
    """需要計算の詳細分析"""
    print("\n=== 需要計算詳細分析 ===")
    
    scenario = 'out_p25_based'
    
    # 需要データの詳細分析
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
            # 数値列の合計
            numeric_cols = df.select_dtypes(include=['number']).columns
            total_need = df[numeric_cols].sum().sum()
            need_totals[name] = total_need
            
            print(f"{name} 需要:")
            print(f"   ファイル: {filename}")
            print(f"   形状: {df.shape}")
            print(f"   総需要: {total_need:.1f}")
            
            # 日別・時間帯別の需要分布確認
            if len(df) > 0:
                daily_avg = total_need / len(df)
                slot_avg = total_need / (len(df) * len(numeric_cols))
                print(f"   日平均: {daily_avg:.1f}")
                print(f"   スロット平均: {slot_avg:.1f}")

def analyze_shortage_calculation_logic():
    """不足計算ロジックの詳細分析"""
    print("\n=== 不足計算ロジック分析 ===")
    
    scenario = 'out_p25_based'
    
    # 不足サマリーデータの詳細
    role_path = f"downloaded_analysis_results/{scenario}/shortage_role_summary.parquet"
    emp_path = f"downloaded_analysis_results/{scenario}/shortage_employment_summary.parquet"
    
    df_role = pd.read_parquet(role_path)
    df_emp = pd.read_parquet(emp_path)
    
    print("職種別不足計算結果の詳細:")
    print(df_role[['role', 'need_h', 'staff_h', 'lack_h', 'excess_h']].round(1))
    
    print("\n雇用形態別不足計算結果の詳細:")
    print(df_emp[['employment', 'need_h', 'staff_h', 'lack_h', 'excess_h']].round(1))
    
    # 計算の整合性チェック
    print("\n計算整合性チェック:")
    
    for _, row in df_role.iterrows():
        need = row['need_h']
        staff = row['staff_h'] 
        lack = row['lack_h']
        excess = row['excess_h']
        
        # need = staff + lack - excess の関係が成り立つか
        expected_need = staff + lack - excess
        diff = abs(need - expected_need)
        
        if diff > 0.1:  # 0.1時間以上の誤差
            print(f"   ⚠️  {row['role']}: 計算不整合 (誤差: {diff:.1f}h)")
        else:
            print(f"   ✓  {row['role']}: 計算整合")
    
    print("\n雇用形態別計算整合性:")
    for _, row in df_emp.iterrows():
        need = row['need_h']
        staff = row['staff_h']
        lack = row['lack_h'] 
        excess = row['excess_h']
        
        expected_need = staff + lack - excess
        diff = abs(need - expected_need)
        
        if diff > 0.1:
            print(f"   ⚠️  {row['employment']}: 計算不整合 (誤差: {diff:.1f}h)")
        else:
            print(f"   ✓  {row['employment']}: 計算整合")

def investigate_shortage_leave_data():
    """shortage_leave.csvの特別調査"""
    print("\n=== shortage_leave.csv 特別調査 ===")
    
    scenario = 'out_p25_based'
    shortage_leave_path = f"downloaded_analysis_results/{scenario}/shortage_leave.csv"
    
    if os.path.exists(shortage_leave_path):
        df = pd.read_csv(shortage_leave_path)
        print(f"shortage_leave.csv が存在:")
        print(f"   ファイルサイズ: {os.path.getsize(shortage_leave_path):,} bytes")
        print(f"   データ形状: {df.shape}")
        
        if len(df.columns) > 0:
            print(f"   列名: {list(df.columns)}")
            
            # 数値列の合計
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                for col in numeric_cols:
                    total = df[col].sum()
                    print(f"   {col} 合計: {total:.1f}")
            
            # サンプルデータ
            if len(df) > 0:
                print("   サンプルデータ（最初の5行）:")
                print(df.head().to_string(index=False))
    else:
        print("shortage_leave.csv は out_p25_based にのみ存在")

def find_calculation_root_cause():
    """計算不整合の根本原因特定"""
    print("\n=== 根本原因特定 ===")
    
    scenario = 'out_p25_based'
    
    # 各データソースの合計値を比較
    print("1. データソース別合計比較:")
    
    # 中間データ
    intermediate_path = f"downloaded_analysis_results/{scenario}/intermediate_data.parquet"
    df_intermediate = pd.read_parquet(intermediate_path)
    actual_hours = (df_intermediate['parsed_slots_count'] * 0.5).sum()
    print(f"   実勤務時間: {actual_hours:.1f}時間")
    
    # 需要データ合計
    need_path = f"downloaded_analysis_results/{scenario}/need_per_date_slot.parquet"
    df_need = pd.read_parquet(need_path)
    numeric_cols = df_need.select_dtypes(include=['number']).columns
    total_need = df_need[numeric_cols].sum().sum()
    print(f"   総需要: {total_need:.1f}時間")
    
    # 職種別不足データの配置時間合計
    role_path = f"downloaded_analysis_results/{scenario}/shortage_role_summary.parquet" 
    df_role = pd.read_parquet(role_path)
    role_staff_total = df_role['staff_h'].sum()
    print(f"   職種別配置時間合計: {role_staff_total:.1f}時間")
    
    # 雇用形態別不足データの配置時間合計
    emp_path = f"downloaded_analysis_results/{scenario}/shortage_employment_summary.parquet"
    df_emp = pd.read_parquet(emp_path)
    emp_staff_total = df_emp['staff_h'].sum()
    print(f"   雇用形態別配置時間合計: {emp_staff_total:.1f}時間")
    
    print("\n2. 整合性判定:")
    
    # 実勤務時間と配置時間の比較
    role_diff = abs(actual_hours - role_staff_total)
    emp_diff = abs(actual_hours - emp_staff_total)
    
    print(f"   実勤務 vs 職種別配置: 差異 {role_diff:.1f}時間")
    if role_diff < 10:
        print("     → ✓ 整合")
    else:
        print("     → ❌ 不整合")
    
    print(f"   実勤務 vs 雇用形態別配置: 差異 {emp_diff:.1f}時間")
    if emp_diff < 10:
        print("     → ✓ 整合")
    else:
        print("     → ❌ 不整合")
    
    # 需要の比較
    role_need_total = df_role['need_h'].sum()
    emp_need_total = df_emp['need_h'].sum()
    
    print(f"   職種別需要合計: {role_need_total:.1f}時間")
    print(f"   雇用形態別需要合計: {emp_need_total:.1f}時間")
    print(f"   需要差異: {abs(role_need_total - emp_need_total):.1f}時間")

def main():
    print("=== 計算ロジック根本解析開始 ===")
    
    analyze_raw_calculation_flow()
    analyze_need_calculation_detail()
    analyze_shortage_calculation_logic()
    investigate_shortage_leave_data()
    find_calculation_root_cause()
    
    print("\n=== 解析完了 ===")
    print("この解析により、計算不整合の具体的な原因を特定します。")

if __name__ == "__main__":
    main()