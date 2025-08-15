#!/usr/bin/env python3
"""
全データフロー影響範囲分析
修正前に影響範囲を完全に把握
"""

import pandas as pd
from pathlib import Path
import sys
import os
import re

# パスを追加
sys.path.insert(0, os.getcwd())

def analyze_dataflow_impact():
    """全データフローの影響範囲分析"""
    print("=== 全データフロー影響範囲分析 ===")
    
    # 1. ファイル構成の確認
    print("\n【1. ファイル構成確認】")
    
    key_files = {
        "データ入稿": ["shift_suite/tasks/io_excel.py"],
        "データ分解": ["shift_suite/tasks/utils.py"],
        "データ分析": ["shift_suite/tasks/shortage_factor_analyzer.py", "shift_suite/tasks/analyzers/"],
        "可視化加工": ["dash_app.py"],
        "可視化表示": ["dash_app.py"]
    }
    
    existing_files = {}
    for phase, files in key_files.items():
        existing_files[phase] = []
        for file_pattern in files:
            file_path = Path(file_pattern)
            if file_path.exists():
                existing_files[phase].append(str(file_path))
            elif file_path.suffix == "":  # ディレクトリ
                if file_path.exists():
                    py_files = list(file_path.glob("*.py"))
                    existing_files[phase].extend([str(f) for f in py_files])
        
        print(f"{phase}: {len(existing_files[phase])}ファイル")
        for f in existing_files[phase][:3]:  # 最初の3ファイル
            print(f"  - {f}")
    
    # 2. dash_app.pyの不足時間関連関数の特定
    print("\n【2. dash_app.py不足時間関連関数】")
    
    dash_path = Path("dash_app.py")
    if dash_path.exists():
        with open(dash_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 不足時間関連関数を検索
        shortage_functions = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if re.search(r'def.*shortage', line, re.IGNORECASE):
                shortage_functions.append((i+1, line.strip()))
        
        print(f"不足時間関連関数: {len(shortage_functions)}個")
        for line_num, func_line in shortage_functions:
            print(f"  行{line_num}: {func_line}")
        
        # コールバック関数の特定
        callback_pattern = r'@app\.callback'
        callbacks = []
        for i, line in enumerate(lines):
            if re.search(callback_pattern, line):
                # 次の関数定義を探す
                for j in range(i+1, min(i+10, len(lines))):
                    if lines[j].strip().startswith('def '):
                        callbacks.append((i+1, j+1, lines[j].strip()))
                        break
        
        print(f"\nコールバック関数: {len(callbacks)}個")
        
        # 不足時間に関連するコールバックを特定
        shortage_callbacks = []
        for cb_start, func_line_num, func_def in callbacks:
            if 'shortage' in func_def.lower():
                shortage_callbacks.append((cb_start, func_line_num, func_def))
        
        print(f"不足時間関連コールバック: {len(shortage_callbacks)}個")
        for cb_start, func_line, func_def in shortage_callbacks:
            print(f"  行{cb_start}-{func_line}: {func_def}")
    
    # 3. データフロー内の計算ロジック特定
    print("\n【3. データフロー計算ロジック特定】")
    
    # create_shortage_from_heat_all関数の詳細分析
    shortage_func_start = None
    shortage_func_end = None
    
    for i, line in enumerate(lines):
        if 'def create_shortage_from_heat_all' in line:
            shortage_func_start = i
        elif shortage_func_start and not line.startswith('    ') and not line.startswith('\t') and line.strip():
            shortage_func_end = i
            break
    
    if shortage_func_start:
        print(f"create_shortage_from_heat_all関数: 行{shortage_func_start+1}-{shortage_func_end}")
        
        # 関数内容の分析
        func_lines = lines[shortage_func_start:shortage_func_end] if shortage_func_end else lines[shortage_func_start:shortage_func_start+50]
        
        # 計算ロジックの特定
        calculation_lines = []
        for i, line in enumerate(func_lines):
            if any(keyword in line.lower() for keyword in ['need', 'actual', 'shortage', '不足', '計算']):
                calculation_lines.append((shortage_func_start + i + 1, line.strip()))
        
        print("計算ロジック関連行:")
        for line_num, line_content in calculation_lines:
            print(f"  行{line_num}: {line_content}")
    
    # 4. 職種別・雇用形態別処理の特定
    print("\n【4. 職種別・雇用形態別処理特定】")
    
    role_related_lines = []
    employment_related_lines = []
    
    for i, line in enumerate(lines):
        if any(keyword in line for keyword in ['role', '職種', 'Role']):
            role_related_lines.append((i+1, line.strip()))
        if any(keyword in line for keyword in ['employment', '雇用', 'Employment']):
            employment_related_lines.append((i+1, line.strip()))
    
    print(f"職種関連処理: {len(role_related_lines)}行")
    print(f"雇用形態関連処理: {len(employment_related_lines)}行")
    
    # 重要な処理行を表示
    important_role_lines = [line for line in role_related_lines if any(kw in line[1] for kw in ['def ', 'groupby', '合計', 'sum'])]
    important_emp_lines = [line for line in employment_related_lines if any(kw in line[1] for kw in ['def ', 'groupby', '合計', 'sum'])]
    
    print("重要な職種別処理:")
    for line_num, line_content in important_role_lines[:5]:
        print(f"  行{line_num}: {line_content[:80]}...")
    
    print("重要な雇用形態別処理:")
    for line_num, line_content in important_emp_lines[:5]:
        print(f"  行{line_num}: {line_content[:80]}...")
    
    # 5. 修正対象箇所の特定
    print("\n【5. 修正対象箇所特定】")
    
    modification_targets = {
        "主要関数": [
            ("create_shortage_from_heat_all", shortage_func_start + 1 if shortage_func_start else None),
        ],
        "コールバック": shortage_callbacks,
        "職種別処理": important_role_lines,
        "雇用形態別処理": important_emp_lines
    }
    
    print("修正対象:")
    for category, targets in modification_targets.items():
        print(f"  {category}: {len(targets)}箇所")
    
    # 6. データフロー依存関係
    print("\n【6. データフロー依存関係】")
    
    dependencies = {
        "入稿→分解": "io_excel.py → utils.py",
        "分解→分析": "utils.py → shortage_factor_analyzer.py",
        "分析→加工": "各analyzer → dash_app.py",
        "加工→可視化": "dash_app.py内部フロー"
    }
    
    for dep_name, dep_desc in dependencies.items():
        print(f"  {dep_name}: {dep_desc}")
    
    # 7. 修正影響予測
    print("\n【7. 修正影響予測】")
    
    impact_assessment = {
        "低影響": ["データ入稿フェーズ (io_excel.py)", "データ分解フェーズ (utils.py)"],
        "中影響": ["データ分析フェーズ (analyzers)", "既存コールバック"],
        "高影響": ["可視化加工フェーズ (create_shortage_from_heat_all)", "職種別・雇用形態別表示"]
    }
    
    for impact_level, areas in impact_assessment.items():
        print(f"  {impact_level}:")
        for area in areas:
            print(f"    - {area}")
    
    return {
        "existing_files": existing_files,
        "shortage_functions": shortage_functions,
        "shortage_callbacks": shortage_callbacks,
        "modification_targets": modification_targets,
        "impact_assessment": impact_assessment
    }

if __name__ == "__main__":
    result = analyze_dataflow_impact()
    print(f"\n影響範囲分析完了: {len(result['shortage_functions'])}個の関数、{len(result['shortage_callbacks'])}個のコールバック")