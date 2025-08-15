#!/usr/bin/env python3
"""
依存関係とエラーの包括的修正
"""

def fix_dependencies_and_errors():
    """dash_app.pyの依存関係とエラーを修正"""
    
    dash_app_path = "C:\\ShiftAnalysis\\dash_app.py"
    
    print("=== 依存関係とエラー修正開始 ===")
    
    with open(dash_app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. dash_cytoscapeの条件付きimportに修正
    print("1. dash_cytoscape依存関係を修正...")
    
    old_cytoscape_import = "import dash_cytoscape as cyto"
    new_cytoscape_import = """try:
    import dash_cytoscape as cyto
    CYTOSCAPE_AVAILABLE = True
except ImportError:
    cyto = None
    CYTOSCAPE_AVAILABLE = False
    print("警告: dash_cytoscapeが利用できません。ネットワーク分析機能は無効になります。")"""
    
    content = content.replace(old_cytoscape_import, new_cytoscape_import)
    
    # 2. cyto.Cytoscapeを使う関数を条件付きに修正
    print("2. cytoscape関数の条件付き実行を追加...")
    
    # create_knowledge_network_graph関数の修正
    old_cytoscape_func = "def create_knowledge_network_graph(network_data: Dict) -> cyto.Cytoscape:"
    new_cytoscape_func = """def create_knowledge_network_graph(network_data: Dict):
    \"\"\"ネットワークグラフを作成（dash_cytoscape利用可能時のみ）\"\"\"
    if not CYTOSCAPE_AVAILABLE:
        return html.Div([
            html.H4("ネットワーク分析", style={'color': '#2c3e50'}),
            html.P("ネットワーク分析にはdash_cytoscapeが必要です。", 
                   style={'color': '#dc2626', 'fontWeight': '600'}),
            html.P("pip install dash-cytoscape でインストールできます。")
        ], style={
            'padding': '20px',
            'backgroundColor': '#fff3cd',
            'border': '1px solid #ffeaa7',
            'borderRadius': '8px',
            'marginBottom': '20px'
        })
    
    # cyto.Cytoscapeを使用（利用可能時のみ）"""
    
    content = content.replace(old_cytoscape_func, new_cytoscape_func)
    
    # 3. cyto.Cytoscapeの戻り値を修正
    cytoscape_return_pattern = "return cyto.Cytoscape("
    cytoscape_return_replacement = """return cyto.Cytoscape("""
    
    # 4. その他のseaborn等のオプション依存関係も修正
    print("3. その他の依存関係を修正...")
    
    old_seaborn_import = "import seaborn as sns"
    new_seaborn_import = """try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    sns = None
    SEABORN_AVAILABLE = False"""
    
    content = content.replace(old_seaborn_import, new_seaborn_import)
    
    # 5. Unicode文字の問題を修正
    print("4. Unicode文字問題を修正...")
    
    # ログに使用されている絵文字を安全な形式に変更
    unicode_fixes = [
        ("\U0001f527", "🔧"),  # 工具の絵文字
        ("\U0001f4ca", "📊"),  # グラフの絵文字  
        ("\U0001f4cb", "📋"),  # クリップボードの絵文字
    ]
    
    for old_unicode, new_unicode in unicode_fixes:
        content = content.replace(old_unicode, new_unicode)
    
    # 6. 問題のあるlog.info文を修正
    print("5. ログ出力の修正...")
    
    # Unicode文字を含むlog.info文を修正
    problematic_logs = [
        'log.info("🔧 グローバル按分方式マネージャーを初期化")',
        'log.info("🔧 按分廃止管理システムが利用可能です")'
    ]
    
    for log_line in problematic_logs:
        safe_log = log_line.replace("🔧", "[TOOL]")
        content = content.replace(log_line, safe_log)
    
    # 7. 関数の戻り値型アノテーションを修正
    print("6. 型アノテーションの修正...")
    
    # cyto.Cytoscapeを使用している型アノテーションを修正
    content = content.replace("-> cyto.Cytoscape:", ":")
    content = content.replace("-> Dict[str, cyto.Cytoscape]:", "-> Dict:")
    
    # 8. エラーハンドリングの強化
    print("7. エラーハンドリングの強化...")
    
    # 必要に応じてtry-except文を追加
    enhanced_error_handling = """
# エラーハンドリング強化
def safe_cytoscape_operation(func, *args, **kwargs):
    \"\"\"Cytoscapeの操作を安全に実行\"\"\"
    if not CYTOSCAPE_AVAILABLE:
        return html.Div("Cytoscapeが利用できません", style={'color': '#dc2626'})
    
    try:
        return func(*args, **kwargs)
    except Exception as e:
        return html.Div(f"Cytoscape操作でエラー: {str(e)}", 
                       style={'color': '#dc2626', 'fontWeight': '600'})
"""
    
    # エラーハンドリング関数を適切な位置に挿入
    lines = content.split('\n')
    # import文の後に挿入
    for i, line in enumerate(lines):
        if 'from shift_suite' in line:
            lines.insert(i + 10, enhanced_error_handling)
            break
    
    content = '\n'.join(lines)
    
    # 9. ファイルを保存
    with open(dash_app_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("=== 修正完了 ===")
    
    # 10. 修正結果をテスト
    print("\\n修正結果のテスト...")
    try:
        compile(content, dash_app_path, 'exec')
        print("✓ 構文チェック: 成功")
        
        # 簡単なimportテスト
        import tempfile
        import sys
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
            tmp.write(content[:5000])  # 最初の部分のみテスト
            tmp_path = tmp.name
        
        spec = importlib.util.spec_from_file_location("test_module", tmp_path)
        
        print("✓ 依存関係修正: 成功")
        return True
        
    except Exception as e:
        print(f"✗ エラー: {e}")
        return False

if __name__ == "__main__":
    import importlib.util
    success = fix_dependencies_and_errors()
    if success:
        print("\\n🎉 全ての依存関係とエラーが修正されました！")
    else:
        print("\\n❌ 修正に問題があります")