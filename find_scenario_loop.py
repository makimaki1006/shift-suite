#!/usr/bin/env python3
"""
Find the exact structure of scenario loop in app.py
"""
from pathlib import Path

def analyze_scenario_loop_structure(app_py_path):
    """Analyze the structure of scenario loops"""
    
    with open(app_py_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the scenario loop start
    scenario_loop_start = None
    for i, line in enumerate(lines):
        if 'for scenario_key, scenario_params in analysis_scenarios.items():' in line:
            scenario_loop_start = i
            break
    
    if scenario_loop_start is None:
        print("Scenario loop not found!")
        return
    
    print(f"Scenario loop starts at line {scenario_loop_start + 1}")
    
    # Track indentation levels
    base_indent = len(lines[scenario_loop_start]) - len(lines[scenario_loop_start].lstrip())
    print(f"Base indentation: {base_indent} spaces")
    
    # Find where the loop ends
    print("\nAnalyzing loop structure...")
    in_loop = True
    line_num = scenario_loop_start + 1
    
    while line_num < len(lines) and in_loop:
        line = lines[line_num]
        # Skip empty lines
        if line.strip() == '':
            line_num += 1
            continue
            
        current_indent = len(line) - len(line.lstrip())
        
        # If we find a line with same or less indentation as the for loop, it's the end
        if current_indent <= base_indent and line.strip() != '':
            print(f"\nScenario loop ends at line {line_num + 1}")
            print(f"Next statement: {line.strip()[:80]}...")
            in_loop = False
            break
            
        # Check for important statements
        if '他の追加モジュールの実行' in line:
            print(f"\nLine {line_num + 1}: Found '他の追加モジュールの実行' at indent {current_indent}")
            if current_indent > base_indent:
                print("  -> INSIDE scenario loop")
            else:
                print("  -> OUTSIDE scenario loop")
                
        if 'opt_module_name_exec_run' in line and 'for' in line:
            print(f"\nLine {line_num + 1}: Found opt_module loop at indent {current_indent}")
            if current_indent > base_indent:
                print("  -> INSIDE scenario loop")
            else:
                print("  -> OUTSIDE scenario loop")
        
        line_num += 1
    
    # Check specific modules
    print("\n\nChecking specific module executions:")
    modules_to_check = ["Fatigue", "Rest Time Analysis", "Work Pattern Analysis", 
                       "Attendance Analysis", "Cost / Benefit", "Stats"]
    
    for module in modules_to_check:
        for i, line in enumerate(lines):
            if f'== "{module}"' in line:
                indent = len(line) - len(line.lstrip())
                print(f"\n{module}:")
                print(f"  Line {i + 1}, indent {indent}")
                if scenario_loop_start < i < line_num:
                    print(f"  -> Inside scenario loop")
                else:
                    print(f"  -> Outside scenario loop")

if __name__ == "__main__":
    app_py_path = Path("app.py")
    if app_py_path.exists():
        analyze_scenario_loop_structure(app_py_path)
    else:
        print(f"Error: {app_py_path} not found")