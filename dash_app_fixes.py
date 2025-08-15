#!/usr/bin/env python3
"""
dash_app.py 修正パッチ
- 重複表示の解消
- ブループリント分析の修正
- UIスタイルの統一
"""

# === 修正1: ブループリント分析のボタンとコールバック修正 ===

BLUEPRINT_BUTTON_FIX = """
# ブループリント分析タブの修正版
def create_blueprint_analysis_tab() -> html.Div:
    \"\"\"ブループリント分析タブを作成（修正版）\"\"\"
    return html.Div([
        html.H3("📘 ブループリント分析", style={'marginBottom': '20px'}),
        html.P("シフト作成の暗黙知と客観的事実を分析します", style={'color': '#666', 'marginBottom': '20px'}),
        
        # 分析設定エリア
        html.Div([
            html.Label("分析タイプを選択:", style={'fontWeight': 'bold', 'marginBottom': '10px'}),
            dcc.RadioItems(
                id='blueprint-analysis-type',
                options=[
                    {'label': '🧠 暗黙知重視分析', 'value': 'implicit'},
                    {'label': '📊 事実重視分析', 'value': 'facts'},
                    {'label': '🔗 統合分析', 'value': 'integrated'}
                ],
                value='integrated',
                style={'marginBottom': '20px'}
            ),
            
            html.Button(
                "分析を開始",
                id='generate-blueprint-button',
                n_clicks=0,
                style={
                    "backgroundColor": "#3498db",
                    "color": "white",
                    "padding": "10px 30px",
                    "fontSize": "16px",
                    "border": "none",
                    "borderRadius": "5px",
                    "cursor": "pointer",
                    "marginBottom": "20px"
                }
            ),
        ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '8px', 'marginBottom': '20px'}),
        
        # 結果表示エリア
        dcc.Loading(
            id="loading-blueprint",
            type="default",
            children=html.Div(id='blueprint-analysis-results', children=[
                html.Div("分析を開始するには上のボタンをクリックしてください", 
                        style={'textAlign': 'center', 'color': '#999', 'padding': '40px'})
            ])
        ),
    ])
"""

# === 修正2: 統合ダッシュボードの重複解消 ===

DASHBOARD_DUPLICATION_FIX = """
def create_overview_tab(selected_scenario: str = None, show_dashboard: bool = True) -> html.Div:
    \"\"\"概要タブを作成（統合ダッシュボード表示制御付き）\"\"\"
    # ... 既存のコード ...
    
    # 統合ダッシュボードの条件付き表示
    comprehensive_dashboard_content = None
    
    if show_dashboard and ComprehensiveDashboard is not None and CURRENT_SCENARIO_DIR is not None:
        try:
            # ... ダッシュボード作成コード ...
        except Exception as e:
            log.warning(f"統合ダッシュボード作成エラー: {e}")
    
    # 概要コンテンツの構築（ダッシュボードを含むかどうかを制御）
    overview_content = [
        html.H3("分析概要", style={'marginBottom': '20px'}),
        # ... 既存のKPI表示 ...
    ]
    
    # ダッシュボードがある場合のみ追加
    if comprehensive_dashboard_content:
        overview_content.extend(comprehensive_dashboard_content)
    
    return html.Div(overview_content)
"""

# === 修正3: ブループリント分析のコールバック修正 ===

BLUEPRINT_CALLBACK_FIX = """
@app.callback(
    Output('blueprint-analysis-results', 'children'),
    Input('generate-blueprint-button', 'n_clicks'),
    State('blueprint-analysis-type', 'value'),
    State('scenario-dropdown', 'value'),
    prevent_initial_call=True
)
@safe_callback
def update_blueprint_analysis(n_clicks, analysis_type, selected_scenario):
    \"\"\"ブループリント分析を実行\"\"\"
    if not n_clicks or not selected_scenario:
        raise PreventUpdate
    
    try:
        # AdvancedBlueprintEngineV2を使用
        if 'AdvancedBlueprintEngineV2' not in globals():
            from shift_suite.tasks.advanced_blueprint_engine_v2 import AdvancedBlueprintEngineV2
        
        # 分析実行
        log.info(f"ブループリント分析開始: {analysis_type}")
        
        # データ取得
        scenario_dir = Path(f'./data/{selected_scenario}')
        if not scenario_dir.exists():
            return html.Div("データディレクトリが見つかりません", style={'color': 'red'})
        
        # エンジン初期化と分析
        engine = AdvancedBlueprintEngineV2()
        
        # タイプに応じた分析
        if analysis_type == 'implicit':
            results = engine.analyze_implicit_knowledge(scenario_dir)
        elif analysis_type == 'facts':
            results = engine.analyze_objective_facts(scenario_dir)
        else:  # integrated
            results = engine.analyze_integrated(scenario_dir)
        
        # 結果表示の構築
        return create_blueprint_results_display(results, analysis_type)
        
    except Exception as e:
        log.error(f"ブループリント分析エラー: {e}", exc_info=True)
        return html.Div([
            html.H4("エラーが発生しました", style={'color': 'red'}),
            html.P(f"詳細: {str(e)}")
        ])

def create_blueprint_results_display(results: dict, analysis_type: str) -> html.Div:
    \"\"\"ブループリント分析結果の表示を構築\"\"\"
    
    # タブ構造で結果を表示
    tabs = []
    
    if 'implicit_knowledge' in results:
        tabs.append(
            dcc.Tab(label='暗黙知分析', children=[
                html.Div([
                    html.H4("発見された暗黙知ルール"),
                    dash_table.DataTable(
                        data=results['implicit_knowledge'],
                        columns=[
                            {'name': 'ルールID', 'id': 'rule_id'},
                            {'name': '説明', 'id': 'description'},
                            {'name': '確信度', 'id': 'confidence', 'type': 'numeric'},
                            {'name': '影響スタッフ数', 'id': 'affected_staff'}
                        ],
                        style_data_conditional=[
                            {
                                'if': {'column_id': 'confidence', 'filter_query': '{confidence} >= 0.8'},
                                'backgroundColor': '#d4edda'
                            }
                        ]
                    )
                ])
            ])
        )
    
    if 'objective_facts' in results:
        tabs.append(
            dcc.Tab(label='客観的事実', children=[
                html.Div([
                    html.H4("抽出された事実"),
                    dash_table.DataTable(
                        data=results['objective_facts'],
                        columns=[
                            {'name': 'カテゴリー', 'id': 'category'},
                            {'name': '事実', 'id': 'fact'},
                            {'name': '根拠データ数', 'id': 'evidence_count'},
                            {'name': '重要度', 'id': 'importance'}
                        ]
                    )
                ])
            ])
        )
    
    if 'integrated_insights' in results:
        tabs.append(
            dcc.Tab(label='統合洞察', children=[
                html.Div([
                    html.H4("統合分析による洞察"),
                    html.Div([
                        html.Div([
                            html.H5(insight['title']),
                            html.P(insight['description']),
                            html.Hr()
                        ]) for insight in results['integrated_insights']
                    ])
                ])
            ])
        )
    
    return html.Div([
        dcc.Tabs(children=tabs) if tabs else html.Div("分析結果がありません")
    ])
"""

# === 修正4: メインレイアウトの整理 ===

MAIN_LAYOUT_FIX = """
# app.layoutの修正（重複要素の削除）
app.layout = html.Div([
    # ストレージ（重複削除済み）
    dcc.Store(id='device-info-store', storage_type='session'),
    dcc.Store(id='kpi-data-store', storage_type='memory'),
    dcc.Store(id='data-loaded', storage_type='memory'),
    dcc.Store(id='full-analysis-store', storage_type='memory'),
    dcc.Store(id='blueprint-results-store', storage_type='memory'),
    dcc.Store(id='progress-store', data={}),
    
    # インターバル
    dcc.Interval(id='progress-interval', interval=500, n_intervals=0),
    
    # ヘッダー（シンプル化）
    html.Div([
        html.H1("🗂️ Shift-Suite 高速分析ビューア", style={
            'textAlign': 'center',
            'color': 'white',
            'margin': '0',
            'padding': '20px'
        })
    ], style={
        'backgroundColor': '#2c3e50',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
    }),
    
    # データアップロードエリア（統一スタイル）
    html.Div([
        create_upload_area()  # 関数化して整理
    ], style={'padding': '20px'}),
    
    # 進捗表示エリア
    html.Div(id='progress-display-div', style={'display': 'none', 'padding': '20px'}),
    
    # シナリオ選択
    html.Div(id='scenario-selector-div', style={'display': 'none', 'padding': '20px'}),
    
    # メインコンテンツ
    html.Div(id='main-content', style={'padding': '20px'}),
    
    # システム状態（オプション）
    html.Div(id='system-status-div', style={'display': 'none', 'padding': '20px'})
])
"""

# === 修正5: UIスタイルの統一 ===

UI_STYLE_CONSTANTS = """
# 統一スタイル定数
UNIFIED_STYLES = {
    'header': {
        'fontSize': '24px',
        'fontWeight': 'bold',
        'color': '#2c3e50',
        'marginBottom': '20px'
    },
    'subheader': {
        'fontSize': '18px',
        'fontWeight': 'bold',
        'color': '#34495e',
        'marginBottom': '15px'
    },
    'card': {
        'backgroundColor': 'white',
        'padding': '20px',
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'marginBottom': '20px'
    },
    'button_primary': {
        'backgroundColor': '#3498db',
        'color': 'white',
        'padding': '10px 30px',
        'fontSize': '16px',
        'border': 'none',
        'borderRadius': '5px',
        'cursor': 'pointer'
    },
    'button_secondary': {
        'backgroundColor': '#95a5a6',
        'color': 'white',
        'padding': '8px 20px',
        'fontSize': '14px',
        'border': 'none',
        'borderRadius': '5px',
        'cursor': 'pointer'
    },
    'metric_card': {
        'backgroundColor': '#f8f9fa',
        'padding': '15px',
        'borderRadius': '8px',
        'textAlign': 'center',
        'minHeight': '100px'
    }
}

def apply_style(element_type: str) -> dict:
    \"\"\"統一スタイルを適用\"\"\"
    return UNIFIED_STYLES.get(element_type, {})
"""

# === 修正6: タブの整理と重複削除 ===

TAB_ORGANIZATION_FIX = """
def create_main_tabs(selected_scenario: str) -> dcc.Tabs:
    \"\"\"メインタブを作成（整理版）\"\"\"
    
    # タブグループの定義
    basic_analysis_tabs = [
        dcc.Tab(label='📊 概要', value='overview'),
        dcc.Tab(label='🔥 ヒートマップ', value='heatmap'),
        dcc.Tab(label='⚠️ 不足分析', value='shortage'),
    ]
    
    hr_management_tabs = [
        dcc.Tab(label='👤 職員分析', value='individual_analysis'),
        dcc.Tab(label='👥 チーム分析', value='team_analysis'),
        dcc.Tab(label='😴 疲労分析', value='fatigue'),
        dcc.Tab(label='⚖️ 公平性', value='fairness'),
        dcc.Tab(label='🏖️ 休暇分析', value='leave'),
    ]
    
    planning_tabs = [
        dcc.Tab(label='📈 需要予測', value='forecast'),
        dcc.Tab(label='💰 コスト分析', value='cost'),
        dcc.Tab(label='📋 採用計画', value='hireplan'),
        dcc.Tab(label='🎯 最適化', value='optimization'),
    ]
    
    advanced_tabs = [
        dcc.Tab(label='📘 ブループリント', value='blueprint'),
        dcc.Tab(label='🧩 MECE制約', value='mece_constraint'),
        dcc.Tab(label='📊 基準乖離', value='gap'),
        dcc.Tab(label='📑 レポート', value='report'),
    ]
    
    # すべてのタブを統合
    all_tabs = basic_analysis_tabs + hr_management_tabs + planning_tabs + advanced_tabs
    
    return dcc.Tabs(
        id='main-tabs',
        value='overview',
        children=all_tabs,
        style={'marginBottom': '20px'}
    )
"""

print("dash_app.py修正パッチが準備されました")
print("主な修正内容:")
print("1. ブループリント分析のボタンとコールバック修正")
print("2. 統合ダッシュボードの重複表示解消")
print("3. UIスタイルの統一化")
print("4. タブ構造の整理")
print("5. 不要な重複要素の削除")