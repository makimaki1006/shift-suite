#!/usr/bin/env python3
"""
Detailed Analysis Results Verification
分析結果の詳細検証
"""
import pandas as pd
import json
import os
from pathlib import Path

def analyze_shortage_data():
    """不足分析データの詳細確認"""
    print("=== 不足分析データ確認 ===")
    
    scenarios = ['out_mean_based', 'out_median_based', 'out_p25_based']
    
    for scenario in scenarios:
        print(f"\n--- {scenario} ---")
        
        # 職種別不足データ
        shortage_role_path = f"downloaded_analysis_results/{scenario}/shortage_role_summary.parquet"
        if os.path.exists(shortage_role_path):
            df_role = pd.read_parquet(shortage_role_path)
            print(f"職種別不足サマリー: {df_role.shape}")
            print(f"列: {list(df_role.columns)}")
            if len(df_role) > 0:
                print("サンプルデータ (最初の3行):")
                for idx, row in df_role.head(3).iterrows():
                    print(f"  {row.get('role', 'N/A')}: 不足={row.get('shortage_hours', 'N/A')}")
        
        # 雇用形態別不足データ
        shortage_emp_path = f"downloaded_analysis_results/{scenario}/shortage_employment_summary.parquet"
        if os.path.exists(shortage_emp_path):
            df_emp = pd.read_parquet(shortage_emp_path)
            print(f"雇用形態別不足サマリー: {df_emp.shape}")
            print(f"列: {list(df_emp.columns)}")
            if len(df_emp) > 0:
                print("サンプルデータ (最初の3行):")
                for idx, row in df_emp.head(3).iterrows():
                    print(f"  {row.get('employment', 'N/A')}: 不足={row.get('shortage_hours', 'N/A')}")

def analyze_ai_report():
    """AIレポートの内容確認"""
    print("\n=== AIレポート確認 ===")
    
    ai_report_path = "downloaded_analysis_results/ai_comprehensive_report_20250809_204858_021cccab.json"
    
    if os.path.exists(ai_report_path):
        try:
            with open(ai_report_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            print(f"AIレポートファイルサイズ: {os.path.getsize(ai_report_path):,} bytes")
            
            # レポート構造の確認
            if isinstance(report_data, dict):
                print("レポート主要キー:")
                for key in report_data.keys():
                    if isinstance(report_data[key], (dict, list)):
                        if isinstance(report_data[key], list):
                            print(f"  {key}: リスト ({len(report_data[key])} 項目)")
                        else:
                            print(f"  {key}: 辞書 ({len(report_data[key])} キー)")
                    else:
                        value_preview = str(report_data[key])[:100] + "..." if len(str(report_data[key])) > 100 else str(report_data[key])
                        print(f"  {key}: {value_preview}")
            
            # 重要な分析結果の抽出
            important_keys = ['summary', 'analysis', 'shortage_analysis', 'recommendations', 'insights']
            for key in important_keys:
                if key in report_data:
                    print(f"\n{key} 内容:")
                    content = report_data[key]
                    if isinstance(content, str):
                        print(f"  {content[:200]}...")
                    elif isinstance(content, dict):
                        print(f"  サブキー: {list(content.keys())}")
                    elif isinstance(content, list):
                        print(f"  リスト項目数: {len(content)}")
                        if content and isinstance(content[0], str):
                            print(f"  最初の項目: {content[0][:100]}...")
            
        except Exception as e:
            print(f"AIレポート読み込みエラー: {e}")
    else:
        print("AIレポートファイルが見つかりません")

def analyze_logs():
    """ログファイルの内容確認"""
    print("\n=== ログファイル確認 ===")
    
    scenarios = ['out_mean_based', 'out_median_based', 'out_p25_based']
    
    for scenario in scenarios:
        print(f"\n--- {scenario} ログ ---")
        
        # ヒートマップ計算ログ
        heatmap_log_path = f"downloaded_analysis_results/{scenario}/2025年08月09日20時48分_ヒートマップ計算ログ.txt"
        if os.path.exists(heatmap_log_path):
            with open(heatmap_log_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
            print(f"ヒートマップ計算ログ: {len(log_content)} 文字")
            # 重要な部分の抽出
            lines = log_content.split('\n')
            important_lines = [line for line in lines if any(keyword in line for keyword in ['エラー', 'ERROR', '完了', '開始', '職種'])]
            if important_lines:
                print("重要なログ行 (最初の5行):")
                for line in important_lines[:5]:
                    print(f"  {line}")
        
        # 不足時間計算ログ  
        shortage_log_path = f"downloaded_analysis_results/{scenario}/2025年08月09日20時48分_不足時間計算詳細ログ.txt"
        if os.path.exists(shortage_log_path):
            with open(shortage_log_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
            print(f"不足時間計算ログ: {len(log_content)} 文字")
            # 重要な部分の抽出
            lines = log_content.split('\n')
            calculation_lines = [line for line in lines if any(keyword in line for keyword in ['計算', '不足', '時間', '職種'])]
            if calculation_lines:
                print("重要な計算ログ (最初の5行):")
                for line in calculation_lines[:5]:
                    print(f"  {line}")

def analyze_intermediate_data():
    """中間データの確認"""
    print("\n=== 中間データ確認 ===")
    
    scenarios = ['out_mean_based', 'out_median_based', 'out_p25_based']
    
    for scenario in scenarios:
        print(f"\n--- {scenario} 中間データ ---")
        
        intermediate_path = f"downloaded_analysis_results/{scenario}/intermediate_data.parquet"
        if os.path.exists(intermediate_path):
            df = pd.read_parquet(intermediate_path)
            print(f"中間データ形状: {df.shape}")
            print(f"列: {list(df.columns)}")
            
            # スタッフ情報の確認
            if 'staff' in df.columns:
                unique_staff = df['staff'].nunique()
                print(f"ユニークなスタッフ数: {unique_staff}")
            
            # 職種情報の確認
            if 'role' in df.columns:
                roles = df['role'].value_counts()
                print(f"職種分布:")
                for role, count in roles.head(5).items():
                    print(f"  {role}: {count}件")
            
            # 雇用形態の確認
            if 'employment' in df.columns:
                employments = df['employment'].value_counts()
                print(f"雇用形態分布:")
                for emp, count in employments.items():
                    print(f"  {emp}: {count}件")

def compare_scenarios():
    """シナリオ間の比較"""
    print("\n=== シナリオ間比較 ===")
    
    scenarios = ['out_mean_based', 'out_median_based', 'out_p25_based']
    shortage_data = {}
    
    # 各シナリオの不足データを読み込み
    for scenario in scenarios:
        shortage_role_path = f"downloaded_analysis_results/{scenario}/shortage_role_summary.parquet"
        if os.path.exists(shortage_role_path):
            df = pd.read_parquet(shortage_role_path)
            shortage_data[scenario] = df
    
    if len(shortage_data) > 1:
        print("シナリオ別不足時間比較:")
        
        # 共通の職種を特定
        common_roles = None
        for scenario, df in shortage_data.items():
            if 'role' in df.columns:
                scenario_roles = set(df['role'].unique())
                if common_roles is None:
                    common_roles = scenario_roles
                else:
                    common_roles = common_roles.intersection(scenario_roles)
        
        if common_roles:
            print("共通職種の不足時間比較:")
            for role in list(common_roles)[:5]:  # 最初の5職種
                print(f"\n職種: {role}")
                for scenario, df in shortage_data.items():
                    role_data = df[df['role'] == role]
                    if not role_data.empty and 'shortage_hours' in role_data.columns:
                        shortage_hours = role_data['shortage_hours'].iloc[0]
                        print(f"  {scenario}: {shortage_hours}")

def main():
    print("=== 分析結果詳細検証 ===")
    
    # 基本的な存在確認
    if not os.path.exists("downloaded_analysis_results"):
        print("ERROR: 分析結果ディレクトリが見つかりません")
        return
    
    analyze_shortage_data()
    analyze_ai_report()
    analyze_logs()
    analyze_intermediate_data()
    compare_scenarios()
    
    print("\n=== 検証完了 ===")

if __name__ == "__main__":
    main()