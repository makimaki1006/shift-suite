#!/usr/bin/env python3
"""
Calculation Discrepancy Analysis  
計算不整合の原因分析
"""
import pandas as pd
import os

def analyze_shortage_discrepancy():
    """不足時間計算の不整合分析"""
    print("=== 不足時間計算不整合分析 ===")
    
    scenario = 'out_mean_based'
    
    # 職種別と雇用形態別データの読み込み
    role_path = f"downloaded_analysis_results/{scenario}/shortage_role_summary.parquet"
    emp_path = f"downloaded_analysis_results/{scenario}/shortage_employment_summary.parquet"
    
    if os.path.exists(role_path) and os.path.exists(emp_path):
        df_role = pd.read_parquet(role_path)
        df_emp = pd.read_parquet(emp_path)
        
        print("=== 比較分析 ===")
        
        # 職種別合計
        role_totals = {
            'need': df_role['need_h'].sum(),
            'staff': df_role['staff_h'].sum(), 
            'lack': df_role['lack_h'].sum(),
            'excess': df_role['excess_h'].sum()
        }
        
        # 雇用形態別合計
        emp_totals = {
            'need': df_emp['need_h'].sum(),
            'staff': df_emp['staff_h'].sum(),
            'lack': df_emp['lack_h'].sum(), 
            'excess': df_emp['excess_h'].sum()
        }
        
        print("職種別合計:")
        for key, value in role_totals.items():
            print(f"  {key}: {value:.1f}")
        
        print("\n雇用形態別合計:")
        for key, value in emp_totals.items():
            print(f"  {key}: {value:.1f}")
        
        print("\n差異分析:")
        for key in role_totals.keys():
            diff = emp_totals[key] - role_totals[key]
            ratio = emp_totals[key] / role_totals[key] if role_totals[key] != 0 else float('inf')
            print(f"  {key}: 差異={diff:.1f}, 比率={ratio:.2f}倍")
        
        # 詳細分析
        print("\n=== 詳細分析 ===")
        
        # 職種別詳細表示
        print("職種別詳細:")
        print(f"{'職種':15s} {'必要':>8s} {'配置':>8s} {'不足':>8s} {'過剰':>8s}")
        print("-" * 50)
        for _, row in df_role.iterrows():
            role = str(row['role'])[:14]
            need = row['need_h']
            staff = row['staff_h'] 
            lack = row['lack_h']
            excess = row['excess_h']
            print(f"{role:15s} {need:>8.1f} {staff:>8.1f} {lack:>8.1f} {excess:>8.1f}")
        
        print("\n雇用形態別詳細:")
        print(f"{'雇用形態':15s} {'必要':>8s} {'配置':>8s} {'不足':>8s} {'過剰':>8s}")
        print("-" * 50)
        for _, row in df_emp.iterrows():
            emp = str(row['employment'])[:14]
            need = row['need_h']
            staff = row['staff_h']
            lack = row['lack_h']
            excess = row['excess_h']
            print(f"{emp:15s} {need:>8.1f} {staff:>8.1f} {lack:>8.1f} {excess:>8.1f}")

def analyze_need_data():
    """需要データの詳細分析"""
    print("\n=== 需要データ詳細分析 ===")
    
    scenario = 'out_mean_based'
    
    # 需要データファイルの確認
    need_files = []
    result_dir = f"downloaded_analysis_results/{scenario}"
    
    for file_name in os.listdir(result_dir):
        if file_name.startswith('need_per_date_slot') and file_name.endswith('.parquet'):
            need_files.append(file_name)
    
    print(f"需要データファイル数: {len(need_files)}")
    
    total_need_by_file = {}
    
    for file_name in need_files:
        file_path = os.path.join(result_dir, file_name)
        try:
            df = pd.read_parquet(file_path)
            # 数値列の合計を計算
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                total_need = df[numeric_cols].sum().sum()
                total_need_by_file[file_name] = {
                    'total_need': total_need,
                    'shape': df.shape,
                    'numeric_columns': len(numeric_cols)
                }
                print(f"{file_name}:")
                print(f"  総需要: {total_need:.1f}")
                print(f"  形状: {df.shape}")
            else:
                print(f"{file_name}: 数値列なし")
        except Exception as e:
            print(f"{file_name}: エラー - {e}")
    
    # 需要データの合計比較
    if total_need_by_file:
        print(f"\n需要データファイル別合計:")
        for file_name, info in total_need_by_file.items():
            category = file_name.replace('need_per_date_slot_', '').replace('.parquet', '')
            print(f"  {category}: {info['total_need']:.1f}")

def check_intermediate_data_breakdown():
    """中間データの詳細分解"""
    print("\n=== 中間データ分解分析 ===")
    
    scenario = 'out_mean_based'
    intermediate_path = f"downloaded_analysis_results/{scenario}/intermediate_data.parquet"
    
    if os.path.exists(intermediate_path):
        df = pd.read_parquet(intermediate_path)
        
        # 職種×雇用形態のクロス集計
        if 'role' in df.columns and 'employment' in df.columns and 'parsed_slots_count' in df.columns:
            cross_table = pd.crosstab(
                df['role'], 
                df['employment'], 
                values=df['parsed_slots_count'], 
                aggfunc='sum',
                fill_value=0
            )
            
            print("職種×雇用形態 勤務スロット数:")
            print(cross_table)
            
            # 職種別合計と雇用形態別合計
            role_totals = cross_table.sum(axis=1)
            emp_totals = cross_table.sum(axis=0)
            
            print(f"\n職種別合計勤務スロット:")
            for role, total in role_totals.items():
                print(f"  {role}: {total:.0f}")
            
            print(f"\n雇用形態別合計勤務スロット:")
            for emp, total in emp_totals.items():
                print(f"  {emp}: {total:.0f}")
        
        # スタッフ別詳細
        if 'staff' in df.columns and 'role' in df.columns and 'employment' in df.columns:
            staff_details = df.groupby(['staff', 'role', 'employment']).agg({
                'parsed_slots_count': 'sum',
                'ds': 'count'
            }).reset_index()
            
            print(f"\nスタッフ別詳細 (上位10名):")
            print(f"{'スタッフ':15s} {'職種':12s} {'雇用形態':8s} {'スロット':>8s} {'日数':>6s}")
            print("-" * 60)
            
            top_staff = staff_details.nlargest(10, 'parsed_slots_count')
            for _, row in top_staff.iterrows():
                staff = str(row['staff'])[:14]
                role = str(row['role'])[:11] 
                emp = str(row['employment'])[:7]
                slots = row['parsed_slots_count']
                days = row['ds']
                print(f"{staff:15s} {role:12s} {emp:8s} {slots:>8.1f} {days:>6d}")

def main():
    print("=== 計算不整合詳細分析 ===")
    
    analyze_shortage_discrepancy()
    analyze_need_data()
    check_intermediate_data_breakdown()
    
    print("\n=== 分析結論 ===")
    print("1. 雇用形態別の不足時間が職種別より大幅に高い")
    print("2. 計算ロジックまたはデータ集計に問題がある可能性")
    print("3. 統合タブの表示結果に影響する重要な問題")
    print("4. さらなる調査が必要")

if __name__ == "__main__":
    main()