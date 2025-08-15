#!/usr/bin/env python3
"""
包括的診断ツール - dash_app.pyの全ての問題を検出・修正
"""

def comprehensive_diagnosis():
    """dash_app.pyの全ての問題を診断"""
    
    dash_app_path = "C:\\ShiftAnalysis\\dash_app.py"
    
    print("=== 包括的診断開始 ===")
    
    with open(dash_app_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\\n')
    
    issues_found = []
    
    # 1. 構文エラーの検出
    print("\\n1. 構文エラーチェック...")
    try:
        compile(content, dash_app_path, 'exec')
        print("   ✓ 構文OK")
    except SyntaxError as e:
        issue = f"構文エラー: 行{e.lineno} - {e.msg}"
        issues_found.append(issue)
        print(f"   ✗ {issue}")
        
        # エラー箇所の詳細
        if e.lineno <= len(lines):
            print(f"   問題行: {lines[e.lineno-1]}")
    
    # 2. 未終了文字列の検出
    print("\\n2. 未終了文字列チェック...")
    unterminated_strings = []
    for i, line in enumerate(lines):
        # ''' や """ の対応チェック
        if line.count('"""') % 2 == 1:
            unterminated_strings.append(f"行{i+1}: 未終了の三重引用符 - {line.strip()[:50]}...")
        if line.count("'''") % 2 == 1:
            unterminated_strings.append(f"行{i+1}: 未終了の三重引用符 - {line.strip()[:50]}...")
        
        # f-stringの未終了チェック
        if 'f"' in line and line.count('"') % 2 == 1:
            unterminated_strings.append(f"行{i+1}: 未終了のf-string - {line.strip()[:50]}...")
        if "f'" in line and line.count("'") % 2 == 1:
            unterminated_strings.append(f"行{i+1}: 未終了のf-string - {line.strip()[:50]}...")
    
    if unterminated_strings:
        for issue in unterminated_strings:
            issues_found.append(issue)
            print(f"   ✗ {issue}")
    else:
        print("   ✓ 未終了文字列なし")
    
    # 3. import文の問題チェック
    print("\\n3. Import依存関係チェック...")
    import_issues = []
    import_lines = [line for line in lines if line.strip().startswith('import ') or line.strip().startswith('from ')]
    
    problematic_imports = [
        'dash_cytoscape',
        'dash_leaflet', 
        'dash_ag_grid',
        'plotly_express',
        'seaborn'
    ]
    
    for line in import_lines:
        for prob_import in problematic_imports:
            if prob_import in line:
                import_issues.append(f"問題のあるimport: {line.strip()}")
    
    if import_issues:
        for issue in import_issues:
            issues_found.append(issue)
            print(f"   ✗ {issue}")
    else:
        print("   ✓ Import依存関係OK")
    
    # 4. 重複パラメータの検出
    print("\\n4. 重複パラメータチェック...")
    duplicate_params = []
    for i, line in enumerate(lines):
        if 'DataTable(' in line:
            # DataTableの開始を検出
            table_lines = []
            bracket_count = 0
            for j in range(i, min(i + 50, len(lines))):
                table_lines.append(lines[j])
                bracket_count += lines[j].count('(') - lines[j].count(')')
                if bracket_count <= 0 and j > i:
                    break
            
            table_content = '\\n'.join(table_lines)
            param_counts = {}
            
            # パラメータをカウント
            import re
            params = re.findall(r'(\\w+)=', table_content)
            for param in params:
                param_counts[param] = param_counts.get(param, 0) + 1
                if param_counts[param] > 1:
                    duplicate_params.append(f"行{i+1}付近: 重複パラメータ '{param}'")
    
    if duplicate_params:
        for issue in duplicate_params:
            issues_found.append(issue) 
            print(f"   ✗ {issue}")
    else:
        print("   ✓ 重複パラメータなし")
    
    # 5. Listの連携問題チェック
    print("\\n5. Listの連携問題チェック...")
    list_issues = []
    
    # 不正なリスト操作を検出
    for i, line in enumerate(lines):
        if '.append(' in line and 'content.append(' not in line:
            # contentリスト以外のappend操作
            if not any(var in line for var in ['metrics_content', 'tabs', 'children']):
                list_issues.append(f"行{i+1}: 疑わしいリスト操作 - {line.strip()[:50]}...")
        
        # 不正なリスト結合
        if '+=' in line and 'list' in line.lower():
            list_issues.append(f"行{i+1}: リスト結合操作 - {line.strip()[:50]}...")
    
    if list_issues:
        for issue in list_issues:
            issues_found.append(issue)
            print(f"   ✗ {issue}")
    else:
        print("   ✓ Listの連携問題なし")
    
    # 6. 論理エラーの検出
    print("\\n6. 論理エラーチェック...")
    logic_issues = []
    
    # 未定義変数の使用
    for i, line in enumerate(lines):
        if 'return' in line and 'None' not in line and '{}' not in line:
            # return文で未定義の可能性がある変数
            stripped = line.strip()
            if stripped.startswith('return ') and len(stripped.split()) == 2:
                var_name = stripped.split()[1]
                if not any(f'{var_name} =' in prev_line for prev_line in lines[:i]):
                    logic_issues.append(f"行{i+1}: 未定義変数の可能性 '{var_name}'")
    
    if logic_issues:
        for issue in logic_issues:
            issues_found.append(issue)
            print(f"   ✗ {issue}")
    else:
        print("   ✓ 論理エラーなし")
    
    # 診断結果の出力
    print(f"\\n=== 診断完了: {len(issues_found)}個の問題を検出 ===")
    
    if issues_found:
        print("\\n検出された問題:")
        for i, issue in enumerate(issues_found, 1):
            print(f"{i}. {issue}")
        return issues_found
    else:
        print("✓ 問題なし - dash_app.pyは健全です")
        return []

if __name__ == "__main__":
    issues = comprehensive_diagnosis()
    if issues:
        print(f"\\n修正が必要な問題数: {len(issues)}")
    else:
        print("\\n全て正常です！")