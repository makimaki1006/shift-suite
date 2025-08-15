#!/usr/bin/env python3
"""
test_app_reproduction.py
app.pyと同じ処理を実行して、motogi_day.zipと同じ結果を生成するテストスクリプト
"""

import datetime as dt
import tempfile
from pathlib import Path

import pandas as pd

# Shift-Suite modules
from shift_suite.tasks.io_excel import ingest_excel
from shift_suite.tasks.heatmap import build_heatmap
from shift_suite.tasks.shortage import shortage_and_brief
from shift_suite.tasks.build_stats import build_stats
from shift_suite.tasks.anomaly import detect_anomaly
from shift_suite.tasks.fatigue import train_fatigue
from shift_suite.tasks.cluster import cluster_staff
from shift_suite.tasks.skill_nmf import build_skill_matrix
from shift_suite.tasks.fairness import run_fairness
from shift_suite.tasks.forecast import build_demand_series, forecast_need
from shift_suite.tasks.rl import learn_roster
from shift_suite.tasks.cost_benefit import analyze_cost_benefit
from shift_suite.tasks.hire_plan import build_hire_plan
from shift_suite.tasks.daily_cost import calculate_daily_cost
from shift_suite.tasks.optimal_hire_plan import create_optimal_hire_plan
from shift_suite.tasks.leave_analyzer import analyze_leave_concentration


def run_complete_analysis():
    """motogi_day.zipと同じ分析を実行"""
    
    # 入力ファイル
    excel_path = Path("デイ_テスト用データ_休日精緻.xlsx")
    if not excel_path.exists():
        print(f"Error: {excel_path} not found")
        return
    
    # 出力ディレクトリ
    work_root = Path(tempfile.mkdtemp(prefix="shift_suite_test_"))
    print(f"Output directory: {work_root}")
    
    # app.pyと同じ3つのシナリオ
    analysis_scenarios = {
        "median_based": {"name": "中央値ベース", "need_stat_method": "中央値"},
        "mean_based": {"name": "平均値ベース", "need_stat_method": "平均値"},
        "p25_based": {"name": "25パーセンタイルベース", "need_stat_method": "25パーセンタイル"},
    }
    
    # app.pyのデフォルト設定  
    slot = 30
    header_row = 1  # 0-indexed, so this is actually row 1 (second row)
    # Excelファイルからシート名を取得
    xls = pd.ExcelFile(excel_path)
    all_sheets = xls.sheet_names
    print(f"Available sheets: {all_sheets}")
    
    # マスターシートを検出（勤務区分を含むもの）
    master_sheet = None
    for sheet in all_sheets:
        if "勤務" in sheet:
            master_sheet = sheet
            break
    
    if not master_sheet:
        print("Error: No master sheet found (should contain '勤務')")
        return
        
    # シフトシート（マスター以外）
    shift_sheets = [s for s in all_sheets if s != master_sheet]
    
    print(f"Master sheet: {master_sheet}")
    print(f"Shift sheets: {shift_sheets}")
    
    # 拡張モジュール（app.pyのデフォルト）
    ext_opts = [
        "Stats",
        "Anomaly", 
        "Fatigue",
        "Cluster",
        "Skill",
        "Fairness",
        "Rest Time Analysis",
        "Work Pattern Analysis", 
        "Attendance Analysis",
        "Combined Score",
        "Low Staff Load",
        "Leave Analysis",
        "Need forecast",
        "RL roster (PPO)",
        "RL roster (model)",
        "Hire plan",
        "Cost / Benefit",
        "最適採用計画",
    ]
    
    try:
        print("1. Starting ingest_excel...")
        long_df, wt_df, unknown_codes = ingest_excel(
            excel_path,
            shift_sheets=shift_sheets,
            header_row=header_row,
            slot_minutes=slot,
            year_month_cell_location=None  # 年月セルは指定しない（ヘッダーから自動検出）
        )
        print(f"   Ingested {len(long_df)} records")
        
        # 各シナリオで分析実行
        for scenario_key, scenario_config in analysis_scenarios.items():
            print(f"\n=== Processing scenario: {scenario_config['name']} ===")
            scenario_out_dir = work_root / f"out_{scenario_key}"
            scenario_out_dir.mkdir(parents=True, exist_ok=True)
            
            print("2. Building heatmap...")
            # method mapping
            method_map = {
                "中央値": "median", 
                "平均値": "mean",
                "25パーセンタイル": "p25"
            }
            min_method = method_map.get(scenario_config["need_stat_method"], "p25")
            
            build_heatmap(long_df, wt_df, scenario_out_dir, slot, min_method=min_method)
            
            print("3. Analyzing shortage...")
            shortage_and_brief(scenario_out_dir, slot, min_method=min_method)
            
            # 拡張モジュール実行
            if "Stats" in ext_opts:
                print("4. Building stats...")
                build_stats(scenario_out_dir)
                
            if "Anomaly" in ext_opts:
                print("5. Detecting anomaly...")
                detect_anomaly(scenario_out_dir)
                
            if "Fatigue" in ext_opts:
                print("6. Training fatigue model...")
                train_fatigue(long_df, scenario_out_dir)
                
            if "Cluster" in ext_opts:
                print("7. Clustering staff...")
                cluster_staff(long_df, scenario_out_dir)
                
            if "Skill" in ext_opts:
                print("8. Building skill matrix...")
                build_skill_matrix(long_df, scenario_out_dir)
                
            if "Fairness" in ext_opts:
                print("9. Analyzing fairness...")
                run_fairness(long_df, scenario_out_dir)
                
            if "Need forecast" in ext_opts:
                print("10. Forecasting need...")
                csv_path = build_demand_series(scenario_out_dir / "heat_ALL.xlsx", scenario_out_dir / "demand_series.csv")
                forecast_need(csv_path, scenario_out_dir / "forecast.parquet", choose="auto")
                
            if "RL roster (PPO)" in ext_opts:
                print("11. Learning roster with RL...")
                learn_roster(scenario_out_dir / "demand_series.csv", scenario_out_dir / "rl_roster.xlsx")
                
            if "Hire plan" in ext_opts:
                print("12. Building hire plan...")
                build_hire_plan(scenario_out_dir)
                
            if "Cost / Benefit" in ext_opts:
                print("13. Analyzing cost/benefit...")
                analyze_cost_benefit(scenario_out_dir)
                
            if "最適採用計画" in ext_opts:
                print("14. Creating optimal hire plan...")
                create_optimal_hire_plan(scenario_out_dir)
                
            if "Leave Analysis" in ext_opts:
                print("15. Analyzing leave...")
                analyze_leave_concentration(long_df, scenario_out_dir)
                
            print(f"   Scenario {scenario_key} completed")
        
        # 共通分析（シナリオ共通）
        common_out_dir = work_root
        
        print("\n=== Running common analyses ===")
        # 各種分析を共通ディレクトリに保存
        if "Daily Cost" in ext_opts:
            print("16. Calculating daily cost...")
            calculate_daily_cost(long_df, common_out_dir)
            
        print(f"\nAnalysis completed successfully!")
        print(f"Output saved to: {work_root}")
        return work_root
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result_dir = run_complete_analysis()
    if result_dir:
        print(f"\nTo compare with motogi_day.zip, check: {result_dir}")