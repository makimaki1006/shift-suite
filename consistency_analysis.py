#!/usr/bin/env python3
"""
Deep consistency analysis of the implemented fixes
"""
from pathlib import Path
import re

def analyze_scenario_loop_consistency(app_py_path):
    """Analyze scenario loop structure and variable scope consistency"""
    
    with open(app_py_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("=== シナリオループ構造と変数スコープの一貫性検証 ===\n")
    
    # Find scenario loop
    scenario_loop_start = None
    scenario_loop_end = None
    
    for i, line in enumerate(lines):
        if 'for scenario_key, scenario_params in analysis_scenarios.items():' in line:
            scenario_loop_start = i
            base_indent = len(line) - len(line.lstrip())
            
            # Find loop end
            for j in range(i + 1, len(lines)):
                current_line = lines[j]
                if current_line.strip() == '':
                    continue
                current_indent = len(current_line) - len(current_line.lstrip())
                if current_indent <= base_indent and current_line.strip():
                    scenario_loop_end = j
                    break
            break
    
    if scenario_loop_start is None:
        print("ERROR: シナリオループが見つかりません")
        return False
    
    print(f"シナリオループ: {scenario_loop_start + 1} - {scenario_loop_end + 1}行")
    
    # Check scenario_out_dir definitions
    scenario_out_dir_definitions = []
    scenario_out_dir_usages = []
    
    for i, line in enumerate(lines):
        if 'scenario_out_dir =' in line:
            scenario_out_dir_definitions.append(i + 1)
        elif 'scenario_out_dir' in line and 'scenario_out_dir =' not in line:
            scenario_out_dir_usages.append(i + 1)
    
    print(f"\nscenario_out_dir定義箇所: {len(scenario_out_dir_definitions)}個")
    for line_num in scenario_out_dir_definitions:
        if scenario_loop_start < line_num <= scenario_loop_end:
            print(f"  行{line_num}: シナリオループ内")
        else:
            print(f"  行{line_num}: シナリオループ外")
    
    print(f"\nscenario_out_dir使用箇所: {len(scenario_out_dir_usages)}個")
    
    # Check usages in copy implementations
    copy_implementation_lines = []
    for i, line in enumerate(lines):
        if 'Copy ' in line and 'files to all scenarios' in line:
            copy_implementation_lines.append(i + 1)
    
    print(f"\nファイルコピー実装: {len(copy_implementation_lines)}個")
    for line_num in copy_implementation_lines:
        if scenario_loop_start < line_num <= scenario_loop_end:
            print(f"  行{line_num}: シナリオループ内 (潜在的問題)")
        else:
            print(f"  行{line_num}: シナリオループ外 (期待通り)")
    
    return True

def analyze_fatigue_execution_consistency(app_py_path):
    """Analyze fatigue analysis execution consistency"""
    
    with open(app_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n=== 疲労度分析実行の一貫性検証 ===\n")
    
    # Find all train_fatigue calls
    train_fatigue_calls = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if 'train_fatigue(' in line and not line.strip().startswith('#'):
            train_fatigue_calls.append(i + 1)
    
    print(f"train_fatigue呼び出し: {len(train_fatigue_calls)}個")
    for line_num in train_fatigue_calls:
        print(f"  行{line_num}: {lines[line_num-1].strip()[:80]}...")
    
    # Check skip_opts
    skip_opts_pattern = re.search(r'skip_opts = \{([^}]+)\}', content)
    if skip_opts_pattern:
        skip_opts_content = skip_opts_pattern.group(1)
        print(f"\nskip_opts: {skip_opts_content}")
        if 'Fatigue' in skip_opts_content:
            print("  WARNING: Fatigueがまだskip_optsに含まれています")
        else:
            print("  OK: Fatigueはskip_optsから除外されています")
    
    # Check if Fatigue is in the module loop
    fatigue_in_loop = '"Fatigue"' in content or "'Fatigue'" in content
    print(f"\nFatigueモジュール参照: {'あり' if fatigue_in_loop else 'なし'}")
    
    return True

def analyze_file_copy_pattern_consistency(app_py_path):
    """Analyze file copy pattern consistency across modules"""
    
    with open(app_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n=== ファイルコピーパターンの一貫性検証 ===\n")
    
    # Find all copy implementations
    copy_patterns = re.findall(r'# Copy ([^#]+?) files to all scenarios(.*?)except Exception as e_copy:', content, re.DOTALL)
    
    print(f"ファイルコピー実装: {len(copy_patterns)}個\n")
    
    for i, (module_name, implementation) in enumerate(copy_patterns, 1):
        print(f"{i}. {module_name.strip()}")
        
        # Check for consistent patterns
        has_scenario_dirs = 'st.session_state.current_scenario_dirs.items()' in implementation
        has_self_check = 'scenario_path != scenario_out_dir' in implementation
        has_file_existence = 'source_file.exists()' in implementation
        has_shutil_copy = 'shutil.copy2' in implementation
        has_logging = 'log.info' in implementation
        
        print(f"   ✓ scenario_dirs使用: {'○' if has_scenario_dirs else '✗'}")
        print(f"   ✓ 自己除外チェック: {'○' if has_self_check else '✗'}")
        print(f"   ✓ ファイル存在確認: {'○' if has_file_existence else '✗'}")
        print(f"   ✓ shutil.copy2使用: {'○' if has_shutil_copy else '✗'}")
        print(f"   ✓ ログ出力: {'○' if has_logging else '✗'}")
        
        consistency_score = sum([has_scenario_dirs, has_self_check, has_file_existence, has_shutil_copy, has_logging])
        print(f"   一貫性スコア: {consistency_score}/5\n")
    
    return True

if __name__ == "__main__":
    app_py_path = Path("app.py")
    if app_py_path.exists():
        analyze_scenario_loop_consistency(app_py_path)
        analyze_fatigue_execution_consistency(app_py_path)
        analyze_file_copy_pattern_consistency(app_py_path)
    else:
        print(f"Error: {app_py_path} not found")