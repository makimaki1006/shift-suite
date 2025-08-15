#!/usr/bin/env python3
"""
Fix plan for all modules to save to all scenarios
"""

# 修正が必要なモジュールとそのファイル
modules_to_fix = {
    "Rest Time Analysis": [
        "rest_time.csv",
        "rest_time_monthly.csv"
    ],
    "Work Pattern Analysis": [
        "work_patterns.csv", 
        "work_pattern_monthly.csv"
    ],
    "Attendance Analysis": [
        "attendance.csv"
    ],
    "Low Staff Load": [
        "low_staff_load.csv"
    ],
    "Combined Score": [
        "combined_score.csv"
    ],
    "Stats": [
        "stats_alerts.parquet",
        "stats_daily_metrics_raw.parquet", 
        "stats_monthly_summary.parquet",
        "stats_overall_summary.parquet",
        "stats_summary.txt"
    ],
    "Cost / Benefit": [
        "cost_benefit.parquet",
        "cost_benefit_summary.txt"
    ],
    "Anomaly": [
        "anomaly_days.parquet"
    ],
    "最適採用計画": [
        "optimal_hire_plan.parquet"
    ]
}

# 各モジュールの後に追加するコード
copy_template = '''
                    # Copy {module_name} files to all scenarios
                    try:
                        for scenario_name, scenario_path in st.session_state.current_scenario_dirs.items():
                            if scenario_path != scenario_out_dir:  # Don't copy to itself
                                for file_name in {file_list}:
                                    source_file = scenario_out_dir / file_name
                                    if source_file.exists():
                                        target_file = Path(scenario_path) / file_name
                                        shutil.copy2(source_file, target_file)
                                        log.info(f"{module_name}結果を {{scenario_name}} にコピーしました: {{file_name}}")
                    except Exception as e_copy:
                        log.warning(f"{module_name}結果のコピー中にエラー: {{e_copy}}")
'''

print("修正計画:")
print("=" * 60)
print("各モジュールの実行後に、生成されたファイルを全シナリオにコピーする処理を追加します。")
print("\n影響を受けるモジュール:")
for module, files in modules_to_fix.items():
    print(f"\n{module}:")
    for f in files:
        print(f"  - {f}")

print("\n" + "=" * 60)
print("実装方法:")
print("1. 各モジュールの処理後にファイルコピー処理を追加")
print("2. st.session_state.current_scenario_dirsを使用して全シナリオにコピー")
print("3. エラーハンドリングを含める")