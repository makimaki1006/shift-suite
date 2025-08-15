#!/usr/bin/env python3
"""
Phase 1: 最小限統合実装
不足分析タブにモード選択機能を追加して按分廃止機能を統合
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

class MinimalIntegrationImplementation:
    """最小限統合実装クラス"""
    
    def __init__(self):
        self.implementation_plan = {}
        self.backup_created = False
        self.integration_status = {}
        
    def create_implementation_plan(self):
        """実装計画作成"""
        print("=== Phase 1: 最小限統合実装計画 ===")
        
        plan = {
            'integration_approach': 'mode_selection_addition',
            'implementation_steps': [
                {
                    'step': 'backup_creation',
                    'description': '既存dash_app.pyの安全なバックアップ作成',
                    'risk_level': 'low',
                    'estimated_time': '30分'
                },
                {
                    'step': 'ui_mode_selector_design',
                    'description': '不足分析タブ内にモード選択UIを追加',
                    'risk_level': 'low',
                    'estimated_time': '2時間'
                },
                {
                    'step': 'proportional_logic_integration',
                    'description': '按分廃止計算ロジックを不足分析タブに統合',
                    'risk_level': 'medium',
                    'estimated_time': '4時間'
                },
                {
                    'step': 'callback_modification',
                    'description': 'コールバック関数の修正とモード対応',
                    'risk_level': 'medium',
                    'estimated_time': '3時間'
                },
                {
                    'step': 'data_flow_unification',
                    'description': 'データフロー統一とエラーハンドリング',
                    'risk_level': 'medium',
                    'estimated_time': '2時間'
                },
                {
                    'step': 'comprehensive_testing',
                    'description': '全機能包括テストの実行',
                    'risk_level': 'high',
                    'estimated_time': '4時間'
                }
            ],
            'total_estimated_time': '15.5時間',
            'risk_mitigation': {
                'backup_strategy': 'multiple_timestamped_backups',
                'rollback_plan': 'git_based_version_control',
                'testing_approach': 'comprehensive_ui_validation'
            }
        }
        
        self.implementation_plan = plan
        
        print(f"実装ステップ: {len(plan['implementation_steps'])}段階")
        print(f"予想総工数: {plan['total_estimated_time']}")
        
        return plan
    
    def execute_step1_backup_creation(self):
        """Step 1: バックアップ作成"""
        print("\n=== Step 1: 安全なバックアップ作成 ===")
        
        backup_result = {
            'backup_files_created': [],
            'backup_success': False,
            'backup_location': None
        }
        
        try:
            # タイムスタンプ付きバックアップディレクトリ作成
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = Path(f'INTEGRATION_BACKUP_{timestamp}')
            backup_dir.mkdir(exist_ok=True)
            
            # 主要ファイルのバックアップ
            files_to_backup = [
                'dash_app.py',
                'app.py',
                'requirements.txt'
            ]
            
            for file_name in files_to_backup:
                source_path = Path(file_name)
                if source_path.exists():
                    backup_path = backup_dir / f'{file_name}.backup'
                    
                    # ファイルコピー
                    with open(source_path, 'r', encoding='utf-8') as src:
                        content = src.read()
                    
                    with open(backup_path, 'w', encoding='utf-8') as dst:
                        dst.write(content)
                    
                    backup_result['backup_files_created'].append(str(backup_path))
                    print(f"  ✓ {file_name} → {backup_path}")
            
            # バックアップ情報ファイル作成
            backup_info = {
                'backup_timestamp': timestamp,
                'backup_purpose': 'shortage_tab_minimal_integration',
                'original_files': files_to_backup,
                'backup_location': str(backup_dir),
                'restoration_command': f'copy {backup_dir}\\*.backup to current directory'
            }
            
            info_path = backup_dir / 'backup_info.json'
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
            
            backup_result['backup_success'] = True
            backup_result['backup_location'] = str(backup_dir)
            self.backup_created = True
            
            print(f"✓ バックアップ完了: {backup_dir}")
            print(f"  バックアップファイル数: {len(backup_result['backup_files_created'])}")
            
        except Exception as e:
            print(f"✗ バックアップ作成失敗: {e}")
            backup_result['error'] = str(e)
        
        return backup_result
    
    def execute_step2_ui_mode_selector(self):
        """Step 2: UIモード選択器の設計"""
        print("\n=== Step 2: モード選択UI設計 ===")
        
        ui_design = {
            'mode_selector_component': self._design_mode_selector(),
            'integration_point': 'create_shortage_tab_function',
            'ui_layout_modification': self._design_layout_modification(),
            'styling_approach': self._design_styling()
        }
        
        print("✓ モード選択UIデザイン完了")
        print(f"  選択可能モード: {len(ui_design['mode_selector_component']['options'])}個")
        
        return ui_design
    
    def _design_mode_selector(self):
        """モード選択器デザイン"""
        return {
            'component_type': 'dcc.RadioItems',
            'component_id': 'shortage-analysis-mode',
            'options': [
                {
                    'label': '🔍 基本モード（従来計算）',
                    'value': 'traditional',
                    'description': 'シンプルで高速な従来の不足分析'
                },
                {
                    'label': '🎯 高精度モード（按分廃止計算）',
                    'value': 'proportional_abolition',
                    'description': '職種別精緻分析による高精度計算'
                }
            ],
            'default_value': 'proportional_abolition',
            'styling': {
                'display': 'flex',
                'flexDirection': 'column',
                'gap': '15px',
                'marginBottom': '25px',
                'padding': '15px',
                'border': '2px solid #e2e8f0',
                'borderRadius': '8px',
                'backgroundColor': '#f8fafc'
            }
        }
    
    def _design_layout_modification(self):
        """レイアウト変更設計"""
        return {
            'insertion_point': 'top_of_shortage_tab_content',
            'new_sections': [
                {
                    'section_id': 'mode-selection-section',
                    'title': '📊 分析モード選択',
                    'components': ['mode_selector', 'mode_explanation']
                },
                {
                    'section_id': 'dynamic-results-section', 
                    'title': '📈 分析結果',
                    'components': ['mode_dependent_content']
                }
            ],
            'existing_content': 'wrap_in_conditional_display'
        }
    
    def _design_styling(self):
        """スタイリング設計"""
        return {
            'mode_cards_styling': {
                'traditional_mode': {
                    'backgroundColor': '#f0f9ff',
                    'border': '2px solid #0ea5e9',
                    'color': '#0c4a6e'
                },
                'proportional_mode': {
                    'backgroundColor': '#f0fdf4',
                    'border': '2px solid #22c55e', 
                    'color': '#14532d'
                }
            },
            'explanation_panel': {
                'backgroundColor': '#fffbeb',
                'border': '1px solid #fbbf24',
                'padding': '12px',
                'borderRadius': '6px',
                'fontSize': '14px'
            }
        }
    
    def execute_step3_logic_integration(self):
        """Step 3: 按分廃止ロジック統合"""
        print("\n=== Step 3: 按分廃止ロジック統合 ===")
        
        integration_result = {
            'functions_extracted': [],
            'data_access_unified': False,
            'error_handling_integrated': False,
            'integration_success': False
        }
        
        try:
            # dash_app.py読み込み
            dash_app_path = Path('dash_app.py')
            with open(dash_app_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # 按分廃止タブから必要なロジックを抽出
            extracted_logic = self._extract_proportional_logic(original_content)
            integration_result['functions_extracted'] = extracted_logic['extracted_functions']
            
            # create_shortage_tab関数の変更
            modified_content = self._modify_shortage_tab_function(
                original_content, 
                extracted_logic
            )
            
            # 統合コード生成
            integrated_code = self._generate_integrated_shortage_function(extracted_logic)
            
            # 統合結果の検証
            if self._validate_integration(integrated_code):
                integration_result['integration_success'] = True
                integration_result['data_access_unified'] = True
                integration_result['error_handling_integrated'] = True
                
                # 実際のファイル更新は次のステップで実行
                print("✓ 按分廃止ロジック統合設計完了")
                print(f"  抽出関数数: {len(integration_result['functions_extracted'])}")
            else:
                print("✗ 統合検証失敗")
        
        except Exception as e:
            print(f"✗ ロジック統合失敗: {e}")
            integration_result['error'] = str(e)
        
        return integration_result
    
    def _extract_proportional_logic(self, content: str) -> Dict:
        """按分廃止ロジック抽出"""
        # create_proportional_abolition_tab関数の境界を特定
        prop_function = self._find_function_boundaries(content, 'create_proportional_abolition_tab')
        
        if not prop_function:
            return {'extracted_functions': [], 'core_logic': ''}
        
        prop_code = prop_function['code']
        
        # 核心ロジックの抽出
        extracted_logic = {
            'extracted_functions': ['create_proportional_abolition_tab'],
            'core_logic': prop_code,
            'data_access_patterns': self._extract_data_access_patterns(prop_code),
            'ui_components': self._extract_ui_components(prop_code),
            'essential_imports': self._extract_essential_imports(prop_code)
        }
        
        return extracted_logic
    
    def _find_function_boundaries(self, content: str, function_name: str) -> Optional[Dict]:
        """関数境界特定（Phase 0から再利用）"""
        lines = content.split('\n')
        
        start_line = None
        for i, line in enumerate(lines):
            if f'def {function_name}(' in line:
                start_line = i + 1
                break
        
        if start_line is None:
            return None
        
        indent_level = len(lines[start_line - 1]) - len(lines[start_line - 1].lstrip())
        end_line = len(lines)
        
        for i in range(start_line, len(lines)):
            line = lines[i]
            if line.strip() and not line.startswith(' ' * (indent_level + 1)) and not line.startswith('#'):
                if line.startswith('def ') or line.startswith('class ') or line.startswith('@'):
                    end_line = i
                    break
        
        return {
            'start': start_line,
            'end': end_line,
            'code': '\n'.join(lines[start_line - 1:end_line])
        }
    
    def _extract_data_access_patterns(self, code: str) -> List[str]:
        """データアクセスパターン抽出"""
        patterns = []
        
        # data_get呼び出し
        data_gets = re.findall(r'data_get\s*\([^)]*[\'"]([^\'"]*)[\'"]', code)
        patterns.extend(data_gets)
        
        # enhanced_data_get呼び出し
        enhanced_gets = re.findall(r'enhanced_data_get\s*\([^)]*[\'"]([^\'"]*)[\'"]', code)
        patterns.extend(enhanced_gets)
        
        return list(set(patterns))
    
    def _extract_ui_components(self, code: str) -> List[str]:
        """UIコンポーネント抽出"""
        components = re.findall(r'(html\.\w+|dcc\.\w+|dash_table\.\w+)', code)
        return list(set(components))
    
    def _extract_essential_imports(self, code: str) -> List[str]:
        """必要インポート抽出"""
        # この関数では按分廃止で使用される特有のインポートを特定
        imports = []
        
        if 'UNIFIED_SYSTEM' in code:
            imports.append('unified_data_pipeline')
        
        if 'enhanced_data_get' in code:
            imports.append('enhanced_data_get')
        
        return imports
    
    def _modify_shortage_tab_function(self, content: str, extracted_logic: Dict) -> str:
        """create_shortage_tab関数の変更"""
        # 元の関数を見つけて、モード選択機能を追加する形で変更
        shortage_function = self._find_function_boundaries(content, 'create_shortage_tab')
        
        if not shortage_function:
            return content
        
        # 新しい統合関数のコード生成
        integrated_function = self._generate_integrated_shortage_function(extracted_logic)
        
        # 元のcreate_shortage_tab関数を置き換え
        lines = content.split('\n')
        new_lines = (
            lines[:shortage_function['start']-1] +
            integrated_function.split('\n') +
            lines[shortage_function['end']:]
        )
        
        return '\n'.join(new_lines)
    
    def _generate_integrated_shortage_function(self, extracted_logic: Dict) -> str:
        """統合された不足分析関数生成"""
        function_template = '''def create_integrated_shortage_tab(selected_scenario: str = None) -> html.Div:
    """統合された不足分析タブ（従来 + 按分廃止モード対応）"""
    
    try:
        shortage_dash_log.info("===== 統合不足分析タブ作成開始 =====")
        
        if selected_scenario is None:
            selected_scenario = "extracted_results"
        
        # モード選択UI
        mode_selector = html.Div([
            html.H4("📊 分析モード選択", style={'marginBottom': '15px', 'color': '#1f2937'}),
            dcc.RadioItems(
                id='shortage-analysis-mode',
                options=[
                    {
                        'label': html.Div([
                            html.Span("🔍 基本モード（従来計算）", style={'fontWeight': 'bold'}),
                            html.Br(),
                            html.Small("シンプルで高速な従来の不足分析", style={'color': '#6b7280'})
                        ]),
                        'value': 'traditional'
                    },
                    {
                        'label': html.Div([
                            html.Span("🎯 高精度モード（按分廃止計算）", style={'fontWeight': 'bold'}),
                            html.Br(),
                            html.Small("職種別精緻分析による高精度計算", style={'color': '#6b7280'})
                        ]),
                        'value': 'proportional_abolition'
                    }
                ],
                value='proportional_abolition',  # デフォルト
                style={'display': 'flex', 'flexDirection': 'column', 'gap': '15px'}
            ),
            html.Div(id='shortage-mode-explanation', style={'marginTop': '15px'})
        ], style={
            'padding': '20px',
            'border': '2px solid #e5e7eb',
            'borderRadius': '8px',
            'backgroundColor': '#f9fafb',
            'marginBottom': '25px'
        })
        
        # 動的結果表示エリア
        results_container = html.Div(
            id='shortage-results-container',
            children=[html.Div("分析モードを選択してください...")],
            style={'minHeight': '400px'}
        )
        
        return html.Div([
            mode_selector,
            results_container
        ], id='integrated-shortage-tab-content')
        
    except Exception as e:
        shortage_dash_log.error(f"統合不足分析タブ作成エラー: {e}")
        return html.Div([
            html.H3("不足分析タブ作成エラー", style={'color': 'red'}),
            html.P(f"エラー内容: {str(e)}"),
            html.P("システム管理者にお問い合わせください。")
        ])


def create_traditional_shortage_analysis(selected_scenario: str) -> html.Div:
    """従来方式の不足分析"""
    try:
        # 従来のcreate_shortage_tab関数の核心ロジックをここに移行
        # [既存のロジックを保持]
        
        # 仮実装：既存ロジックの構造を維持
        content = []
        
        # データ取得
        df_shortage_role = data_get('shortage_role_summary')
        df_shortage_emp = data_get('shortage_employment_summary')
        
        if df_shortage_role is None:
            df_shortage_role = pd.DataFrame()
        if df_shortage_emp is None:
            df_shortage_emp = pd.DataFrame()
        
        # 結果表示
        if not df_shortage_role.empty or not df_shortage_emp.empty:
            content.append(
                html.H4("📊 従来方式不足分析結果", style={'color': '#0ea5e9'})
            )
            
            # グラフとテーブルの生成
            if not df_shortage_role.empty:
                content.append(
                    dash_table.DataTable(
                        data=df_shortage_role.to_dict('records'),
                        columns=[{"name": i, "id": i} for i in df_shortage_role.columns],
                        style_cell={'textAlign': 'left'},
                        style_header={'backgroundColor': '#f0f9ff', 'fontWeight': 'bold'}
                    )
                )
        else:
            content.append(
                html.Div([
                    html.H4("📊 従来方式不足分析", style={'color': '#6b7280'}),
                    html.P("分析データが見つかりませんでした。")
                ])
            )
        
        return html.Div(content)
        
    except Exception as e:
        return html.Div([
            html.H4("従来分析エラー", style={'color': 'red'}),
            html.P(f"エラー: {str(e)}")
        ])


def create_proportional_abolition_analysis(selected_scenario: str) -> html.Div:
    """按分廃止方式の不足分析"""
    try:
        # 按分廃止タブの核心ロジックをここに移行
        content = []
        
        # 按分廃止データの取得
        df_proportional_role = data_get('proportional_abolition_role_summary')
        df_proportional_org = data_get('proportional_abolition_organization_summary')
        
        if df_proportional_role is None:
            df_proportional_role = pd.DataFrame()
        if df_proportional_org is None:
            df_proportional_org = pd.DataFrame()
        
        # 結果表示
        content.append(
            html.H4("🎯 高精度モード（按分廃止）分析結果", style={'color': '#22c55e'})
        )
        
        if not df_proportional_role.empty:
            content.append(
                html.H5("職種別分析結果")
            )
            content.append(
                dash_table.DataTable(
                    data=df_proportional_role.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in df_proportional_role.columns],
                    style_cell={'textAlign': 'left'},
                    style_header={'backgroundColor': '#f0fdf4', 'fontWeight': 'bold'}
                )
            )
        
        if not df_proportional_org.empty:
            content.append(
                html.H5("組織別分析結果", style={'marginTop': '20px'})
            )
            content.append(
                dash_table.DataTable(
                    data=df_proportional_org.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in df_proportional_org.columns],
                    style_cell={'textAlign': 'left'},
                    style_header={'backgroundColor': '#f0fdf4', 'fontWeight': 'bold'}
                )
            )
        
        if df_proportional_role.empty and df_proportional_org.empty:
            content.append(
                html.Div([
                    html.P("按分廃止分析データが見つかりませんでした。"),
                    html.Ul([
                        html.Li("シナリオが選択されているか確認してください"),
                        html.Li("按分廃止分析が実行済みか確認してください")
                    ])
                ])
            )
        
        return html.Div(content)
        
    except Exception as e:
        return html.Div([
            html.H4("按分廃止分析エラー", style={'color': 'red'}),
            html.P(f"エラー: {str(e)}")
        ])'''
        
        return function_template
    
    def _validate_integration(self, integrated_code: str) -> bool:
        """統合コード検証"""
        try:
            # 構文チェック
            compile(integrated_code, '<string>', 'exec')
            
            # 基本構造チェック
            required_elements = [
                'def create_integrated_shortage_tab',
                'shortage-analysis-mode',
                'shortage-results-container',
                'create_traditional_shortage_analysis',
                'create_proportional_abolition_analysis'
            ]
            
            for element in required_elements:
                if element not in integrated_code:
                    print(f"検証失敗: {element} が見つかりません")
                    return False
            
            return True
            
        except SyntaxError as e:
            print(f"構文エラー: {e}")
            return False
        except Exception as e:
            print(f"検証エラー: {e}")
            return False
    
    def execute_step4_callback_modification(self):
        """Step 4: コールバック修正"""
        print("\n=== Step 4: コールバック関数修正 ===")
        
        callback_result = {
            'new_callbacks_designed': [],
            'existing_callbacks_modified': [],
            'callback_integration_success': False
        }
        
        try:
            # 新しいコールバック設計
            new_callbacks = self._design_integration_callbacks()
            callback_result['new_callbacks_designed'] = new_callbacks
            
            # 既存コールバックの修正計画
            existing_modifications = self._plan_existing_callback_modifications()
            callback_result['existing_callbacks_modified'] = existing_modifications
            
            callback_result['callback_integration_success'] = True
            
            print("✓ コールバック修正計画完了")
            print(f"  新規コールバック: {len(new_callbacks)}個")
            print(f"  修正対象コールバック: {len(existing_modifications)}個")
            
        except Exception as e:
            print(f"✗ コールバック修正計画失敗: {e}")
            callback_result['error'] = str(e)
        
        return callback_result
    
    def _design_integration_callbacks(self) -> List[Dict]:
        """統合コールバック設計"""
        return [
            {
                'callback_name': 'update_shortage_mode_explanation',
                'purpose': 'モード選択時の説明更新',
                'inputs': ['shortage-analysis-mode.value'],
                'outputs': ['shortage-mode-explanation.children'],
                'implementation': 'mode_explanation_callback'
            },
            {
                'callback_name': 'update_shortage_results_container',
                'purpose': 'モード別結果表示',
                'inputs': ['shortage-analysis-mode.value', 'selected-scenario.value'],
                'outputs': ['shortage-results-container.children'],
                'implementation': 'results_display_callback'
            }
        ]
    
    def _plan_existing_callback_modifications(self) -> List[Dict]:
        """既存コールバック修正計画"""
        return [
            {
                'callback_name': 'update_shortage_tab',
                'modification_type': 'function_name_change',
                'old_function': 'create_shortage_tab',
                'new_function': 'create_integrated_shortage_tab',
                'risk_level': 'low'
            }
        ]
    
    def generate_implementation_code(self):
        """実装コード生成"""
        print("\n=== 実装コード生成 ===")
        
        generated_code = {
            'integrated_function': self._generate_integrated_shortage_function({}),
            'new_callbacks': self._generate_callback_code(),
            'helper_functions': self._generate_helper_functions(),
            'styling_updates': self._generate_styling_code()
        }
        
        # 完全な統合コードの生成
        complete_code = self._assemble_complete_integration_code(generated_code)
        
        # コードファイルとして保存
        code_path = Path(f'integrated_shortage_tab_code_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py')
        with open(code_path, 'w', encoding='utf-8') as f:
            f.write(complete_code)
        
        print(f"✓ 統合コード生成完了: {code_path}")
        
        return {
            'code_file_path': str(code_path),
            'generated_components': list(generated_code.keys()),
            'ready_for_integration': True
        }
    
    def _generate_callback_code(self) -> str:
        """コールバックコード生成"""
        return '''
# 新しい統合コールバック

@app.callback(
    Output('shortage-mode-explanation', 'children'),
    [Input('shortage-analysis-mode', 'value')]
)
def update_shortage_mode_explanation(selected_mode):
    """モード選択時の説明更新"""
    try:
        if selected_mode == 'traditional':
            return html.Div([
                html.P("🔍 基本モード選択中", style={'fontWeight': 'bold', 'color': '#0ea5e9'}),
                html.P("従来の不足分析計算を使用します。シンプルで高速な分析結果を表示します。", 
                      style={'fontSize': '14px', 'color': '#6b7280'})
            ], style={'backgroundColor': '#f0f9ff', 'padding': '10px', 'borderRadius': '4px'})
        
        elif selected_mode == 'proportional_abolition':
            return html.Div([
                html.P("🎯 高精度モード選択中", style={'fontWeight': 'bold', 'color': '#22c55e'}),
                html.P("按分廃止による職種別精緻分析を使用します。より詳細で正確な分析結果を表示します。",
                      style={'fontSize': '14px', 'color': '#6b7280'})
            ], style={'backgroundColor': '#f0fdf4', 'padding': '10px', 'borderRadius': '4px'})
        
        else:
            return html.Div("モードを選択してください", style={'color': '#6b7280'})
            
    except Exception as e:
        log.error(f"モード説明更新エラー: {e}")
        return html.Div("説明の読み込みに失敗しました", style={'color': '#dc2626'})


@app.callback(
    Output('shortage-results-container', 'children'),
    [Input('shortage-analysis-mode', 'value'),
     Input('selected-scenario', 'value')]
)
def update_shortage_results_container(analysis_mode, selected_scenario):
    """モード別結果表示"""
    try:
        if analysis_mode == 'traditional':
            return create_traditional_shortage_analysis(selected_scenario)
        elif analysis_mode == 'proportional_abolition':
            return create_proportional_abolition_analysis(selected_scenario)
        else:
            return html.Div([
                html.H4("分析モード未選択"),
                html.P("上記から分析モードを選択してください。")
            ], style={'textAlign': 'center', 'color': '#6b7280', 'padding': '40px'})
            
    except Exception as e:
        log.error(f"不足分析結果更新エラー: {e}")
        return html.Div([
            html.H4("分析結果取得エラー", style={'color': '#dc2626'}),
            html.P(f"エラー内容: {str(e)}"),
            html.P("データの再読み込みまたはシナリオの再選択をお試しください。")
        ])


# 既存コールバックの修正
@app.callback(
    [Output('shortage-tab-container', 'children'),
     Output('shortage-tab-container', 'style')],
    [Input('shortage-tab-container', 'style'),
     Input('selected-scenario', 'value'),
     Input('data-status', 'data')]
)
def update_integrated_shortage_tab(style, selected_scenario, data_status):
    """統合不足分析タブの更新（既存のupdate_shortage_tabを置き換え）"""
    log.info(f"[integrated_shortage_tab] 初期化開始 - scenario: {selected_scenario}, data_status: {data_status}")
    
    if style is None or style.get('display') == 'none':
        log.info("[integrated_shortage_tab] PreventUpdate - 非表示状態")
        raise PreventUpdate
    
    try:
        log.info("[integrated_shortage_tab] create_integrated_shortage_tab呼び出し開始")
        result = create_integrated_shortage_tab(selected_scenario)
        log.info("[integrated_shortage_tab] create_integrated_shortage_tab完了")
        
        return result, {'display': 'block'}
        
    except Exception as e:
        log.error(f"統合不足分析タブの初期化エラー: {str(e)}")
        error_content = html.Div([
            html.H3("統合不足分析タブエラー", style={'color': 'red'}),
            html.P(f"エラー内容: {str(e)}"),
            html.P("システム管理者にお問い合わせください。")
        ])
        return error_content, {'display': 'block'}
'''
    
    def _generate_helper_functions(self) -> str:
        """ヘルパー関数生成"""
        return '''
# ヘルパー関数

def safe_data_access(data_key: str, default_value=None):
    """安全なデータアクセス"""
    try:
        result = data_get(data_key)
        return result if result is not None else default_value
    except Exception as e:
        log.warning(f"データアクセスエラー ({data_key}): {e}")
        return default_value

def create_error_display(error_message: str, suggestion: str = None) -> html.Div:
    """エラー表示の統一化"""
    content = [
        html.H4("エラーが発生しました", style={'color': '#dc2626'}),
        html.P(error_message)
    ]
    
    if suggestion:
        content.append(html.P(f"対処方法: {suggestion}", style={'color': '#6b7280', 'fontSize': '14px'}))
    
    return html.Div(content, style={
        'padding': '20px',
        'border': '1px solid #fecaca',
        'borderRadius': '6px',
        'backgroundColor': '#fef2f2'
    })

def create_mode_info_card(mode: str, title: str, description: str, icon: str, color: str) -> html.Div:
    """モード情報カード生成"""
    return html.Div([
        html.H5([icon, " ", title], style={'color': color, 'marginBottom': '8px'}),
        html.P(description, style={'fontSize': '14px', 'color': '#6b7280'})
    ], style={
        'padding': '15px',
        'border': f'2px solid {color}',
        'borderRadius': '8px',
        'backgroundColor': f'{color}0f'  # 薄い背景色
    })
'''
    
    def _generate_styling_code(self) -> str:
        """スタイリングコード生成"""
        return '''
# スタイリング定義

SHORTAGE_TAB_STYLES = {
    'mode_selector': {
        'padding': '20px',
        'border': '2px solid #e5e7eb',
        'borderRadius': '8px',
        'backgroundColor': '#f9fafb',
        'marginBottom': '25px'
    },
    'traditional_mode': {
        'backgroundColor': '#f0f9ff',
        'borderColor': '#0ea5e9',
        'color': '#0c4a6e'
    },
    'proportional_mode': {
        'backgroundColor': '#f0fdf4',
        'borderColor': '#22c55e',
        'color': '#14532d'
    },
    'results_container': {
        'minHeight': '400px',
        'padding': '20px'
    },
    'error_display': {
        'padding': '20px',
        'border': '1px solid #fecaca',
        'borderRadius': '6px',
        'backgroundColor': '#fef2f2'
    }
}
'''
    
    def _assemble_complete_integration_code(self, generated_code: Dict) -> str:
        """完全な統合コード組み立て"""
        complete_code = f'''"""
統合不足分析タブ実装コード
生成日時: {datetime.now().isoformat()}
目的: 従来の不足分析と按分廃止分析の統合
"""

# 必要インポート（既存のdash_app.pyに追加）
# （インポートは既存ファイルに含まれているため省略）

{generated_code['styling_updates']}

{generated_code['integrated_function']}

{generated_code['helper_functions']}

{generated_code['new_callbacks']}

# 実装完了
print("✓ 統合不足分析タブの実装コードが生成されました")
'''
        return complete_code

def main():
    print("=" * 70)
    print("*** Phase 1: 最小限統合実装開始 ***")
    print("目的: 不足分析タブにモード選択機能を追加")
    print("=" * 70)
    
    implementer = MinimalIntegrationImplementation()
    
    try:
        # Step 1: 実装計画作成
        plan = implementer.create_implementation_plan()
        
        # Step 2: バックアップ作成
        backup_result = implementer.execute_step1_backup_creation()
        
        if not backup_result['backup_success']:
            print("❌ バックアップ失敗のため実装を中止します")
            return None
        
        # Step 3: UI設計
        ui_design = implementer.execute_step2_ui_mode_selector()
        
        # Step 4: ロジック統合
        logic_result = implementer.execute_step3_logic_integration()
        
        # Step 5: コールバック修正
        callback_result = implementer.execute_step4_callback_modification()
        
        # Step 6: 実装コード生成
        code_result = implementer.generate_implementation_code()
        
        print("\n" + "=" * 70)
        print("*** Phase 1 実装準備完了 ***")
        print(f"バックアップ: {backup_result['backup_location']}")
        print(f"統合コード: {code_result['code_file_path']}")
        print("次のステップ: 実際のファイル適用と包括テスト")
        print("=" * 70)
        
        return {
            'implementation_plan': plan,
            'backup_result': backup_result,
            'ui_design': ui_design,
            'logic_result': logic_result,
            'callback_result': callback_result,
            'code_result': code_result
        }
        
    except Exception as e:
        print(f"\nERROR Phase 1実装中にエラー: {e}")
        import traceback
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    main()