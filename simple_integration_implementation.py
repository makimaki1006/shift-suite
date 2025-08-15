#!/usr/bin/env python3
"""
Simple Integration Implementation
不足分析タブにモード選択機能を追加して按分廃止機能を統合
"""

import shutil
from pathlib import Path
from datetime import datetime
import subprocess

def create_backup():
    """バックアップ作成"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(f"INTEGRATION_BACKUP_{timestamp}")
        backup_dir.mkdir(exist_ok=True)
        
        # dash_app.pyのバックアップ
        if Path('dash_app.py').exists():
            shutil.copy2('dash_app.py', backup_dir / 'dash_app.py.backup')
            print(f"Backup created: {backup_dir}")
            return backup_dir
        else:
            print("Error: dash_app.py not found")
            return None
    except Exception as e:
        print(f"Backup error: {e}")
        return None

def find_shortage_tab_function():
    """create_shortage_tab関数の位置を特定"""
    try:
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        start_line = None
        end_line = len(lines)
        
        for i, line in enumerate(lines):
            if 'def create_shortage_tab(' in line:
                start_line = i
                break
        
        if start_line is None:
            print("Error: create_shortage_tab function not found")
            return None
            
        # 関数終了位置を特定
        indent_level = len(lines[start_line]) - len(lines[start_line].lstrip())
        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            if line.strip() and not line.startswith(' ' * (indent_level + 1)):
                if line.startswith('def ') or line.startswith('class ') or line.startswith('@'):
                    end_line = i
                    break
        
        print(f"Found create_shortage_tab: lines {start_line + 1}-{end_line}")
        return {'start': start_line, 'end': end_line}
        
    except Exception as e:
        print(f"Function search error: {e}")
        return None

def generate_integrated_shortage_tab():
    """統合された不足分析タブのコード生成"""
    return '''def create_shortage_tab(selected_scenario: str = None) -> html.Div:
    """統合された不足分析タブを作成（モード選択機能付き）"""
    try:
        log.info("create_shortage_tab統合版開始")
        
        # モード選択UI
        mode_selector = html.Div([
            html.H4("分析モード選択", style={'marginBottom': '15px'}),
            dcc.RadioItems(
                id='shortage-analysis-mode',
                options=[
                    {'label': '基本モード（従来計算）', 'value': 'basic'},
                    {'label': '高精度モード（按分廃止計算）', 'value': 'advanced'}
                ],
                value='advanced',
                style={'display': 'flex', 'flexDirection': 'row', 'gap': '20px', 'marginBottom': '20px'}
            )
        ], style={'marginBottom': '30px'})
        
        # 説明パネル
        explanation = html.Div(id='shortage-mode-explanation', style={'marginBottom': '20px'})
        
        # 結果コンテナ
        results = html.Div(id='shortage-results-container')
        
        return html.Div([
            html.H3("不足分析", style={'marginBottom': '20px'}),
            mode_selector,
            explanation,
            results
        ])
        
    except Exception as e:
        log.error(f"create_shortage_tab統合版エラー: {e}")
        return html.Div([
            html.H3("不足分析エラー"),
            html.P(f"エラー: {str(e)}")
        ])'''

def generate_new_callbacks():
    """新しいコールバック関数の生成"""
    return '''
@app.callback(
    Output('shortage-mode-explanation', 'children'),
    Input('shortage-analysis-mode', 'value')
)
def update_shortage_mode_explanation(mode):
    """モード説明の更新"""
    try:
        if mode == 'basic':
            return html.Div([
                html.P("基本モード: 従来の不足時間計算"),
                html.P("シンプルで高速な計算")
            ], style={'backgroundColor': '#f8f9fa', 'padding': '15px', 'borderRadius': '5px'})
        elif mode == 'advanced':
            return html.Div([
                html.P("高精度モード: 職種別精緻分析計算"),
                html.P("より実態に即した高精度な分析")
            ], style={'backgroundColor': '#e7f3ff', 'padding': '15px', 'borderRadius': '5px'})
        else:
            return html.Div("モードを選択してください")
    except Exception as e:
        return html.P(f"説明更新エラー: {e}")

@app.callback(
    Output('shortage-results-container', 'children'),
    [Input('shortage-analysis-mode', 'value'), Input('selected-scenario', 'value')]
)
def update_shortage_results(mode, scenario):
    """分析結果の更新"""
    try:
        if mode == 'basic':
            return create_basic_shortage_display(scenario)
        elif mode == 'advanced':
            return create_advanced_shortage_display(scenario)
        else:
            return html.Div("分析モードを選択してください")
    except Exception as e:
        log.error(f"結果更新エラー: {e}")
        return html.Div(f"結果更新エラー: {e}")

def create_basic_shortage_display(scenario=None):
    """基本モード表示"""
    try:
        df_shortage_role = data_get("shortage_role_summary")
        if df_shortage_role is None or df_shortage_role.empty:
            return html.P("基本モード用データが利用できません")
        
        return html.Div([
            html.H4("職種別不足状況（基本計算）"),
            dash_table.DataTable(
                data=df_shortage_role.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df_shortage_role.columns],
                style_cell={'textAlign': 'center'},
                style_header={'backgroundColor': 'lightblue'}
            )
        ])
    except Exception as e:
        return html.Div(f"基本分析エラー: {e}")

def create_advanced_shortage_display(scenario=None):
    """高精度モード表示"""
    try:
        df_role = data_get("proportional_abolition_role_summary")
        df_org = data_get("proportional_abolition_organization_summary")
        
        content = []
        
        if df_org is not None and not df_org.empty:
            content.append(html.H4("組織全体サマリー（高精度計算）"))
            for _, row in df_org.iterrows():
                content.append(html.Div([
                    html.P(f"総需要時間: {row.get('total_need', 0):.1f}時間/日"),
                    html.P(f"実配置時間: {row.get('total_actual', 0):.1f}時間/日"),
                    html.P(f"不足時間: {row.get('total_shortage', 0):.1f}時間/日"),
                    html.P(f"総スタッフ数: {row.get('total_staff_count', 0)}名")
                ], style={'backgroundColor': '#f8f9fa', 'padding': '15px', 'borderRadius': '5px', 'marginBottom': '15px'}))
        
        if df_role is not None and not df_role.empty:
            content.append(html.H4("職種別詳細分析（高精度計算）"))
            content.append(dash_table.DataTable(
                data=df_role.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df_role.columns],
                style_cell={'textAlign': 'center'},
                style_header={'backgroundColor': '#007bff', 'color': 'white'},
                style_data_conditional=[{
                    'if': {'filter_query': '{状態} = SHORTAGE'},
                    'backgroundColor': '#ffebee',
                    'color': 'red'
                }]
            ))
        
        if not content:
            content.append(html.P("高精度モード用データが利用できません"))
        
        return html.Div(content)
        
    except Exception as e:
        return html.Div(f"高精度分析エラー: {e}")
'''

def update_dash_app(function_pos, new_function, new_callbacks):
    """dash_app.pyの更新"""
    try:
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # 新しいコードで置換
        new_lines = (
            lines[:function_pos['start']] +
            new_function.split('\n') +
            [''] +
            new_callbacks.split('\n') +
            [''] +
            lines[function_pos['end']:]
        )
        
        new_content = '\n'.join(new_lines)
        with open('dash_app.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("dash_app.py updated successfully")
        return True
        
    except Exception as e:
        print(f"Update error: {e}")
        return False

def test_syntax():
    """構文テスト"""
    try:
        result = subprocess.run([
            'python', '-m', 'py_compile', 'dash_app.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Syntax check passed")
            return True
        else:
            print(f"Syntax error: {result.stderr}")
            return False
    except Exception as e:
        print(f"Syntax test error: {e}")
        return False

def test_import():
    """インポートテスト"""
    try:
        result = subprocess.run([
            'python', '-c', 'import dash_app; print("Import successful")'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("Import test passed")
            return True
        else:
            print(f"Import failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"Import test error: {e}")
        return False

def rollback(backup_dir):
    """ロールバック"""
    try:
        if backup_dir and (backup_dir / 'dash_app.py.backup').exists():
            shutil.copy2(backup_dir / 'dash_app.py.backup', 'dash_app.py')
            print(f"Rolled back from {backup_dir}")
            return True
    except Exception as e:
        print(f"Rollback error: {e}")
    return False

def main():
    print("=== Phase 1: Minimal Integration Implementation ===")
    
    try:
        # Step 1: Backup
        print("\nStep 1: Creating backup...")
        backup_dir = create_backup()
        if not backup_dir:
            raise Exception("Backup creation failed")
        
        # Step 2: Find function
        print("\nStep 2: Analyzing current shortage tab...")
        function_pos = find_shortage_tab_function()
        if not function_pos:
            raise Exception("Function analysis failed")
        
        # Step 3: Generate integrated code
        print("\nStep 3: Generating integrated code...")
        new_function = generate_integrated_shortage_tab()
        new_callbacks = generate_new_callbacks()
        
        # Step 4: Update dash_app.py
        print("\nStep 4: Updating dash_app.py...")
        if not update_dash_app(function_pos, new_function, new_callbacks):
            raise Exception("Update failed")
        
        # Step 5: Syntax check
        print("\nStep 5: Syntax check...")
        if not test_syntax():
            print("Syntax error detected - rolling back...")
            rollback(backup_dir)
            raise Exception("Syntax errors found")
        
        # Step 6: Import test
        print("\nStep 6: Import test...")
        if not test_import():
            print("Import failed - rolling back...")
            rollback(backup_dir)
            raise Exception("Import test failed")
        
        print("\nPhase 1 integration completed successfully!")
        print(f"Backup location: {backup_dir}")
        print("Next steps:")
        print("  1. Run comprehensive UI tests")
        print("  2. Verify all functionality")
        print("  3. Consider removing old proportional abolition tab")
        
        return {'success': True, 'backup_dir': backup_dir}
        
    except Exception as e:
        print(f"\nPhase 1 integration failed: {e}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    main()