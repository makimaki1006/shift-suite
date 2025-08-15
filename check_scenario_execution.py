#!/usr/bin/env python3
"""
Check which analyses are executed only in specific scenarios
"""
import re
from pathlib import Path

def analyze_scenario_specific_execution(app_py_path):
    """Analyze app.py to find scenario-specific execution patterns"""
    
    # Files that are only in p25_based
    p25_only_files = [
        'anomaly_days.parquet',
        'attendance.csv',
        'combined_score.csv',
        'concentration_requested.csv',
        'cost_benefit.parquet',
        'leave_analysis.csv',
        'optimal_hire_plan.parquet',
        'rest_time.csv',
        'work_patterns.csv',
        'stats_*.parquet'
    ]
    
    # Read app.py
    with open(app_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find scenario loop patterns
    scenario_loops = []
    
    # Pattern 1: for scenario_name in scenarios
    pattern1 = re.findall(r'for\s+(\w+)\s+in\s+.*scenarios.*?:(.*?)(?=for\s+\w+\s+in|if\s+|$)', content, re.DOTALL)
    
    # Pattern 2: for scenario_path in scenario_dirs
    pattern2 = re.findall(r'for\s+.*?\s+in\s+.*?scenario.*?:(.*?)(?=for\s+\w+\s+in|if\s+|$)', content, re.DOTALL)
    
    print("=== Scenario Loop Analysis ===")
    print(f"Found {len(pattern1) + len(pattern2)} scenario loops\n")
    
    # Check where specific files are generated
    print("=== File Generation Locations ===")
    
    for file_name in p25_only_files:
        if '*' in file_name:
            base_name = file_name.replace('*', '')
            matches = re.findall(rf'([\w_]+\.(?:parquet|csv|xlsx|txt)).*?{base_name}', content)
        else:
            matches = re.findall(rf'{file_name}', content)
        
        if matches:
            print(f"\n{file_name}:")
            # Find context around each match
            for match in set(matches):
                # Find line number
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if match in line:
                        # Check if in scenario loop
                        preceding_lines = '\n'.join(lines[max(0, i-20):i])
                        if 'for' in preceding_lines and 'scenario' in preceding_lines:
                            print(f"  Line {i+1}: Inside scenario loop")
                        else:
                            print(f"  Line {i+1}: Outside scenario loop")
                        print(f"    Context: {line.strip()[:80]}...")
                        break

if __name__ == "__main__":
    app_py_path = Path(r"app.py")
    if app_py_path.exists():
        analyze_scenario_specific_execution(app_py_path)
    else:
        print(f"Error: {app_py_path} not found")