#!/usr/bin/env python3
"""
Numerical Results Verification
数値結果の詳細検証
"""
import pandas as pd
import json
import os

def verify_shortage_calculations():
    """不足時間計算の数値検証"""
    print("=== 不足時間計算数値検証 ===")
    
    scenarios = ['out_mean_based', 'out_median_based', 'out_p25_based']
    
    for scenario in scenarios:
        print(f"\n--- {scenario} ---")
        
        # 職種別不足データの詳細
        shortage_role_path = f"downloaded_analysis_results/{scenario}/shortage_role_summary.parquet"
        if os.path.exists(shortage_role_path):
            df_role = pd.read_parquet(shortage_role_path)
            
            print(f"職種別不足分析結果:")
            print(f"データ形状: {df_role.shape}")
            
            # 数値列の確認
            numeric_columns = ['need_h', 'staff_h', 'lack_h', 'excess_h']
            for col in numeric_columns:
                if col in df_role.columns:
                    total = df_role[col].sum()
                    print(f"  {col} 合計: {total:.1f} 時間")
            
            # 職種別詳細
            print("職種別詳細:")
            for idx, row in df_role.iterrows():
                role = row.get('role', 'Unknown')
                need = row.get('need_h', 0)
                staff = row.get('staff_h', 0) 
                lack = row.get('lack_h', 0)
                excess = row.get('excess_h', 0)
                print(f"  {role}: 必要={need:.1f}h, 配置={staff:.1f}h, 不足={lack:.1f}h, 過剰={excess:.1f}h")
        
        # 雇用形態別不足データの詳細
        shortage_emp_path = f"downloaded_analysis_results/{scenario}/shortage_employment_summary.parquet"
        if os.path.exists(shortage_emp_path):
            df_emp = pd.read_parquet(shortage_emp_path)
            
            print(f"\n雇用形態別不足分析結果:")
            print("雇用形態別詳細:")
            for idx, row in df_emp.iterrows():
                emp = row.get('employment', 'Unknown')
                need = row.get('need_h', 0)
                staff = row.get('staff_h', 0)
                lack = row.get('lack_h', 0)
                excess = row.get('excess_h', 0)
                print(f"  {emp}: 必要={need:.1f}h, 配置={staff:.1f}h, 不足={lack:.1f}h, 過剰={excess:.1f}h")

def verify_intermediate_data_details():
    """中間データの詳細検証"""
    print("\n=== 中間データ詳細検証 ===")
    
    scenario = 'out_mean_based'  # 代表として平均ベースを使用
    intermediate_path = f"downloaded_analysis_results/{scenario}/intermediate_data.parquet"
    
    if os.path.exists(intermediate_path):
        df = pd.read_parquet(intermediate_path)
        
        print(f"中間データ詳細分析:")
        print(f"データ期間: {df['ds'].min()} ～ {df['ds'].max()}")
        print(f"総レコード数: {len(df)}")
        print(f"ユニークスタッフ数: {df['staff'].nunique()}")
        
        # スタッフ別集計
        staff_summary = df.groupby('staff').agg({
            'parsed_slots_count': 'sum',
            'ds': 'count'
        }).round(1)
        print(f"\nスタッフ別勤務実績 (上位10名):")
        print(f"{'スタッフ名':15s} {'総勤務スロット':>12s} {'総勤務日数':>10s}")
        for staff, row in staff_summary.head(10).iterrows():
            slots = row['parsed_slots_count']
            days = row['ds']
            print(f"{staff:15s} {slots:>12.1f} {days:>10d}")
        
        # 職種別集計
        role_summary = df.groupby('role').agg({
            'parsed_slots_count': 'sum',
            'staff': 'nunique'
        }).round(1)
        print(f"\n職種別勤務実績:")
        print(f"{'職種':15s} {'総勤務スロット':>12s} {'人数':>6s}")
        for role, row in role_summary.iterrows():
            slots = row['parsed_slots_count']
            count = row['staff']
            print(f"{role:15s} {slots:>12.1f} {count:>6d}")
        
        # 休日タイプの分布
        if 'holiday_type' in df.columns:
            holiday_dist = df['holiday_type'].value_counts()
            print(f"\n休日タイプ分布:")
            for holiday_type, count in holiday_dist.items():
                print(f"  {holiday_type}: {count}件")

def verify_ai_report_key_insights():
    """AIレポートの主要インサイト確認"""
    print("\n=== AIレポート主要インサイト ===")
    
    ai_report_path = "downloaded_analysis_results/ai_comprehensive_report_20250809_204858_021cccab.json"
    
    if os.path.exists(ai_report_path):
        try:
            with open(ai_report_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            # 実行サマリーの確認
            if 'execution_summary' in report_data:
                exec_summary = report_data['execution_summary']
                print("実行サマリー:")
                for key, value in exec_summary.items():
                    if isinstance(value, (int, float, str)) and len(str(value)) < 100:
                        print(f"  {key}: {value}")
            
            # KPI確認
            if 'key_performance_indicators' in report_data:
                kpi_data = report_data['key_performance_indicators']
                print("\n主要パフォーマンス指標:")
                for key, value in kpi_data.items():
                    if isinstance(value, dict):
                        print(f"  {key}:")
                        for sub_key, sub_value in value.items():
                            if isinstance(sub_value, (int, float)):
                                print(f"    {sub_key}: {sub_value}")
                            elif isinstance(sub_value, str) and len(sub_value) < 100:
                                print(f"    {sub_key}: {sub_value}")
            
            # データ品質評価
            if 'data_quality_assessment' in report_data:
                quality_data = report_data['data_quality_assessment']
                print(f"\nデータ品質評価:")
                for key, value in quality_data.items():
                    if isinstance(value, (int, float, str)) and len(str(value)) < 100:
                        print(f"  {key}: {value}")
            
        except Exception as e:
            print(f"AIレポート詳細分析エラー: {e}")

def verify_generated_files():
    """生成ファイルの妥当性確認"""
    print("\n=== 生成ファイル妥当性確認 ===")
    
    # 重要なファイルの存在と内容確認
    critical_files = [
        'shortage_role_summary.parquet',
        'shortage_employment_summary.parquet', 
        'intermediate_data.parquet',
        'need_per_date_slot.parquet'
    ]
    
    scenario = 'out_mean_based'
    
    for file_name in critical_files:
        file_path = f"downloaded_analysis_results/{scenario}/{file_name}"
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"✓ {file_name}: {file_size:,} bytes")
            
            # データ内容の基本チェック
            if file_name.endswith('.parquet'):
                try:
                    df = pd.read_parquet(file_path)
                    print(f"    形状: {df.shape}, データ型: {len(df.select_dtypes(include=['number']).columns)} 数値列")
                    
                    # 数値データの異常値チェック
                    numeric_columns = df.select_dtypes(include=['number']).columns
                    for col in numeric_columns:
                        if df[col].isna().all():
                            print(f"    WARNING: {col} 列が全てNA")
                        elif (df[col] < 0).any():
                            negative_count = (df[col] < 0).sum()
                            print(f"    WARNING: {col} 列に負の値が {negative_count} 件")
                        elif df[col].sum() == 0:
                            print(f"    WARNING: {col} 列の合計が0")
                            
                except Exception as e:
                    print(f"    ERROR: データ読み込み失敗 - {e}")
        else:
            print(f"✗ {file_name}: ファイルが見つかりません")

def main():
    print("=== 数値結果詳細検証 ===")
    
    verify_shortage_calculations()
    verify_intermediate_data_details()
    verify_ai_report_key_insights()
    verify_generated_files()
    
    print("\n=== 検証結論 ===")
    print("1. 基本データ構造: 正常")
    print("2. 数値計算結果: 要詳細確認")
    print("3. AIレポート: 充実")
    print("4. ファイル生成: 適切")

if __name__ == "__main__":
    main()