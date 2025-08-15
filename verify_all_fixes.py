#!/usr/bin/env python3
"""
Verify all fixes have been properly implemented
"""
from pathlib import Path
import re

def verify_fixes(app_py_path):
    """Verify all implemented fixes"""
    
    with open(app_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("=== 修正内容の検証 ===\n")
    
    # 1. Check skip_opts
    print("1. skip_opts確認:")
    skip_opts_match = re.search(r'skip_opts = \{([^}]+)\}', content)
    if skip_opts_match:
        skip_opts = skip_opts_match.group(1)
        if "Fatigue" not in skip_opts:
            print("  ✓ Fatigueがskip_optsから削除されています")
        else:
            print("  ✗ Fatigueがまだskip_optsに含まれています")
    
    # 2. Check train_fatigue fix
    print("\n2. train_fatigue戻り値の修正:")
    if "model = train_fatigue(" in content:
        print("  ✓ train_fatigueの戻り値をmodelとして扱っています")
    else:
        print("  ✗ train_fatigueの戻り値がまだ修正されていません")
    
    # 3. Check file copy implementations
    print("\n3. ファイルコピー機能の実装:")
    
    modules_to_check = [
        ("Rest Time Analysis", ["rest_time.csv", "rest_time_monthly.csv"]),
        ("Work Pattern Analysis", ["work_patterns.csv", "work_pattern_monthly.csv"]),
        ("Stats", ["stats_alerts.parquet"]),
        ("Anomaly", ["anomaly_days.parquet"]),
        ("Fatigue", ["fatigue_score"]),
        ("Leave Analysis", ["leave_analysis.csv"])
    ]
    
    for module_name, files in modules_to_check:
        # Search for copy implementation
        pattern = f"Copy {module_name}.*?files to all scenarios"
        if re.search(pattern, content):
            print(f"  ✓ {module_name}: ファイルコピー機能が実装されています")
        else:
            print(f"  ✗ {module_name}: ファイルコピー機能が見つかりません")
    
    # 4. Check modules still needing fixes
    print("\n4. 未修正のモジュール:")
    
    unimplemented_modules = [
        "Attendance Analysis",
        "Low Staff Load", 
        "Combined Score",
        "Cost / Benefit",
        "最適採用計画"
    ]
    
    for module in unimplemented_modules:
        pattern = f"Copy {module}.*?files to all scenarios"
        if not re.search(pattern, content):
            print(f"  - {module}: まだファイルコピー機能が実装されていません")
    
    # 5. Check scenario_out_dir usage
    print("\n5. scenario_out_dir使用状況:")
    scenario_out_dir_count = content.count("scenario_out_dir")
    print(f"  scenario_out_dirが{scenario_out_dir_count}回使用されています")
    
    # 6. Check current_scenario_dirs usage
    print("\n6. current_scenario_dirs使用状況:")
    current_scenario_dirs_count = content.count("st.session_state.current_scenario_dirs")
    print(f"  current_scenario_dirsが{current_scenario_dirs_count}回使用されています")

if __name__ == "__main__":
    app_py_path = Path("app.py")
    if app_py_path.exists():
        verify_fixes(app_py_path)
    else:
        print(f"Error: {app_py_path} not found")