#!/usr/bin/env python3
"""
dash_app.py 按分廃止タブ統合パッチ
Step 2: 按分廃止・職種別分析タブの追加

使用方法:
1. このファイルの内容を確認
2. dash_app.pyに手動で追加、または
3. 自動パッチスクリプトを実行
"""

# ================================================================================
# 1. create_proportional_abolition_tab関数をdash_app.pyに追加
# ================================================================================

def create_proportional_abolition_tab(selected_scenario: str = None) -> html.Div:
    """按分廃止・職種別分析タブを作成"""
    try:
        log.info("===== 按分廃止・職種別分析タブ作成開始 =====")
        log.info(f"scenario: {selected_scenario}")
        
        content = []
        
        # 🎯 分析タイトルとコンセプト説明
        content.append(html.Div([
            html.H2("🎯 按分廃止・職種別分析", style=UNIFIED_STYLES['header']),
            html.P([
                "従来の按分方式を廃止し、各職種の真の過不足を分析します。",
                html.Br(),
                "按分による「真実の隠蔽」を排除し、現場の実態に即した分析を提供します。"
            ], style={
                'backgroundColor': '#e8f4fd', 
                'padding': '15px', 
                'border-left': '4px solid #2196F3',
                'marginBottom': '30px'
            })
        ]))
        
        # 按分廃止データ読み込み
        log.info("按分廃止データ読み込み開始")
        df_proportional_role = data_get('proportional_abolition_role_summary', pd.DataFrame())
        df_proportional_org = data_get('proportional_abolition_organization_summary', pd.DataFrame())
        
        if df_proportional_role.empty:
            log.warning("按分廃止分析結果が見つかりません")
            content.append(html.Div([
                html.H4("⚠️ データ不足", style={'color': '#ff9800'}),
                html.P([
                    "按分廃止分析結果が見つかりません。",
                    html.Br(),
                    "app.pyで按分廃止分析を実行し、結果をZIPファイルでアップロードしてください。"
                ], style={'color': '#666', 'fontSize': '16px'}),
                html.Div([
                    html.H5("実行手順:"),
                    html.Ol([
                        html.Li("app.pyで分析を実行"),
                        html.Li("按分廃止分析結果を含むZIPファイルをダウンロード"),
                        html.Li("このダッシュボードにZIPファイルをアップロード"),
                        html.Li("按分廃止分析タブで結果確認")
                    ])
                ], style={'marginTop': '20px'})
            ], style={
                'backgroundColor': '#fff3e0',
                'padding': '20px',
                'borderRadius': '8px',
                'border': '2px solid #ff9800'
            }))
            return html.Div(content)
        
        log.info(f"按分廃止データ読み込み完了: 職種{len(df_proportional_role)}個")
        
        # 📊 組織全体サマリー
        if not df_proportional_org.empty:
            org_data = df_proportional_org.iloc[0]
            log.info(f"組織全体データ: {org_data['status']}")
            
            content.append(html.H3("📊 組織全体の真の過不足状況"))
            
            # 状態に応じた色設定
            shortage_color = '#f44336' if org_data['total_shortage'] > 0 else '#4caf50' if org_data['total_shortage'] < 0 else '#ff9800'
            status_colors = {
                'SHORTAGE': '#f44336',
                'SURPLUS': '#4caf50', 
                'BALANCED': '#ff9800'
            }
            status_color = status_colors.get(org_data['status'], '#666')
            
            status_text = {
                'SHORTAGE': '🔴 人手不足',
                'SURPLUS': '🟢 人手余剰',
                'BALANCED': '🟡 適正配置'
            }.get(org_data['status'], org_data['status'])
            
            metrics_row = html.Div([
                html.Div([
                    create_metric_card("Need時間/日", f"{org_data['total_need']:.1f}h")
                ], style={'width': '23%', 'display': 'inline-block', 'padding': '5px'}),
                
                html.Div([
                    create_metric_card("実配置時間/日", f"{org_data['total_actual']:.1f}h")  
                ], style={'width': '23%', 'display': 'inline-block', 'padding': '5px'}),
                
                html.Div([
                    create_metric_card("過不足時間/日", 
                                     f"{org_data['total_shortage']:+.1f}h",
                                     color=shortage_color)
                ], style={'width': '23%', 'display': 'inline-block', 'padding': '5px'}),
                
                html.Div([
                    create_metric_card("組織状態", status_text, color=status_color)
                ], style={'width': '23%', 'display': 'inline-block', 'padding': '5px'}),
                
                html.Div([
                    create_metric_card("総スタッフ数", f"{org_data['total_staff_count']}名")
                ], style={'width': '8%', 'display': 'inline-block', 'padding': '5px'})
            ], style={'marginBottom': '30px', 'display': 'flex', 'flexWrap': 'wrap'})
            
            content.append(metrics_row)
        
        # 🎯 職種別真の過不足分析
        content.append(html.H3("🎯 職種別真の過不足分析 (按分廃止)", 
                              style={'marginTop': '30px'}))
        
        # 職種別メトリクス表示
        if not df_proportional_role.empty:
            
            # 不足職種と余剰職種の分離
            shortage_roles = df_proportional_role[df_proportional_role['過不足時間/日'] > 0].sort_values('過不足時間/日', ascending=False)
            surplus_roles = df_proportional_role[df_proportional_role['過不足時間/日'] < 0].sort_values('過不足時間/日', ascending=True)
            balanced_roles = df_proportional_role[df_proportional_role['過不足時間/日'] == 0]
            
            # 重要な発見の表示
            if len(shortage_roles) > 0:
                severe_shortage = shortage_roles[shortage_roles['過不足時間/日'] > 2.0]
                zero_allocation = shortage_roles[shortage_roles['現在スタッフ数'] == 0]
                
                if len(severe_shortage) > 0 or len(zero_allocation) > 0:
                    content.append(html.Div([
                        html.H4("⚠️ 按分廃止により発見された重要な問題", style={'color': '#f44336'}),
                        html.Ul([
                            html.Li(f"深刻な不足職種: {len(severe_shortage)}職種 (2時間/日以上の不足)") if len(severe_shortage) > 0 else None,
                            html.Li(f"完全未配置職種: {len(zero_allocation)}職種 (スタッフ0名だがNeed有り)") if len(zero_allocation) > 0 else None
                        ])
                    ], style={
                        'backgroundColor': '#ffebee',
                        'padding': '15px',
                        'border-left': '4px solid #f44336',
                        'marginBottom': '20px'
                    }))
            
            # データテーブル表示
            content.append(dash_table.DataTable(
                id='proportional-abolition-table',
                data=df_proportional_role.to_dict('records'),
                columns=[
                    {'name': '職種', 'id': '職種', 'type': 'text'},
                    {'name': 'Need時間/日', 'id': 'Need時間/日', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                    {'name': '実配置時間/日', 'id': '実配置時間/日', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                    {'name': '過不足時間/日', 'id': '過不足時間/日', 'type': 'numeric', 'format': {'specifier': '+.1f'}},
                    {'name': '現在スタッフ数', 'id': '現在スタッフ数', 'type': 'numeric'},
                    {'name': '状態', 'id': '状態', 'type': 'text'}
                ],
                style_cell={
                    'textAlign': 'center',
                    'padding': '12px',
                    'fontFamily': 'Arial, sans-serif'
                },
                style_header={
                    'backgroundColor': '#1976d2',
                    'color': 'white',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{状態} = SHORTAGE'},
                        'backgroundColor': '#ffebee',
                        'color': 'black'
                    },
                    {
                        'if': {'filter_query': '{状態} = SURPLUS'}, 
                        'backgroundColor': '#e8f5e8',
                        'color': 'black'
                    },
                    {
                        'if': {'filter_query': '{現在スタッフ数} = 0 && {過不足時間/日} > 0'},
                        'backgroundColor': '#ffcdd2',
                        'color': '#d32f2f',
                        'fontWeight': 'bold'
                    }
                ],
                sort_action="native",
                style_table={'marginBottom': '30px'}
            ))
            
            # 📈 按分廃止の効果説明
            content.append(html.Div([
                html.H4("📈 按分廃止分析の効果"),
                html.Div([
                    html.Div([
                        html.H5("🔴 按分廃止方式の結果:", style={'color': '#f44336'}),
                        html.P("各職種の真の過不足を露呈し、隠れていた問題を可視化")
                    ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px', 'verticalAlign': 'top'}),
                    
                    html.Div([
                        html.H5("⚪ 従来の按分方式の問題:", style={'color': '#666'}),
                        html.P("組織全体では均衡に見えるが、個別職種の深刻な不均衡が隠蔽される")
                    ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px', 'verticalAlign': 'top'})
                ])
            ], style={
                'backgroundColor': '#f8f9fa',
                'padding': '20px',
                'border-left': '4px solid #007bff',
                'marginBottom': '30px'
            }))
            
            # 改善アクションプラン
            if len(shortage_roles) > 0:
                content.append(html.H4("🎯 改善アクションプラン"))
                
                action_items = []
                for _, role_row in shortage_roles.head(5).iterrows():  # 上位5職種
                    if role_row['現在スタッフ数'] == 0:
                        priority = "緊急"
                        action = f"【{priority}】{role_row['職種']}の専門スタッフを至急採用"
                        color = "#f44336"
                    elif role_row['過不足時間/日'] > 5.0:
                        priority = "高"
                        needed_staff = role_row['過不足時間/日'] / 4.0  # 1人4時間/日と仮定
                        action = f"【{priority}】{role_row['職種']}を約{needed_staff:.1f}名増員"
                        color = "#ff9800"
                    elif role_row['過不足時間/日'] > 2.0:
                        priority = "中"
                        action = f"【{priority}】{role_row['職種']}の勤務時間を{role_row['過不足時間/日']:.1f}時間/日増加"
                        color = "#ffc107"
                    else:
                        priority = "低"
                        action = f"【{priority}】{role_row['職種']}の配置微調整 (+{role_row['過不足時間/日']:.1f}時間/日)"
                        color = "#4caf50"
                    
                    action_items.append(html.Li(action, style={'color': color, 'marginBottom': '8px'}))
                
                content.append(html.Ol(action_items, style={'fontSize': '16px'}))
        
        else:
            content.append(html.P("職種別データが読み込まれていません。", style={'color': '#f44336'}))
        
        return html.Div(content)
        
    except Exception as e:
        log.error(f"按分廃止タブ作成エラー: {e}")
        import traceback
        log.error(f"詳細エラー: {traceback.format_exc()}")
        return html.Div([
            html.H3("🎯 按分廃止・職種別分析"),
            html.P(f"エラーが発生しました: {str(e)}", style={'color': 'red'}),
            html.P("データが正しく読み込まれているか確認してください。", style={'color': '#666'})
        ])


# ================================================================================
# 2. create_main_ui_tabs()のタブ定義に追加
# ================================================================================

# create_main_ui_tabs()関数内のタブ定義に以下を追加:

dcc.Tab(label='🎯 按分廃止分析', value='proportional_abolition'),


# ================================================================================
# 3. create_main_ui_tabs()のタブコンテナに追加  
# ================================================================================

# create_main_ui_tabs()関数内のタブコンテナ部分に以下を追加:

html.Div(id='proportional-abolition-tab-container',
         style={'display': 'none'},
         children=[
             dcc.Loading(
                 id="loading-proportional-abolition",
                 type="circle", 
                 children=html.Div(id='proportional-abolition-content')
             )
         ]),


# ================================================================================
# 4. update_tab_visibility関数の更新
# ================================================================================

# update_tab_visibility関数のOutput部分に以下を追加:
Output('proportional-abolition-tab-container', 'style'),

# update_tab_visibility関数の戻り値に以下を追加:
{'display': 'block'} if active_tab == 'proportional_abolition' and selected_scenario and data_status else {'display': 'none'},


# ================================================================================
# 5. 按分廃止コンテンツ初期化コールバック追加
# ================================================================================

# 按分廃止タブ用の新しいコールバック関数を追加:

@app.callback(
    Output('proportional-abolition-content', 'children'),
    [Input('proportional-abolition-tab-container', 'style'),
     Input('scenario-dropdown', 'value')],
    State('data-loaded', 'data'),
)
@safe_callback
def initialize_proportional_abolition_content(style, selected_scenario, data_status):
    """按分廃止分析タブの内容を初期化"""
    log.info(f"[proportional_abolition_tab] 初期化開始 - scenario: {selected_scenario}, data_status: {data_status}, style: {style}")
    
    if not selected_scenario or not data_status or style.get('display') == 'none':
        log.info("[proportional_abolition_tab] PreventUpdate - 条件不満足")
        raise PreventUpdate
    try:
        log.info("[proportional_abolition_tab] create_proportional_abolition_tab呼び出し開始")
        result = create_proportional_abolition_tab(selected_scenario)
        log.info("[proportional_abolition_tab] create_proportional_abolition_tab完了")
        return result
    except Exception as e:
        log.error(f"按分廃止分析タブの初期化エラー: {str(e)}")
        import traceback
        log.error(f"按分廃止分析タブ詳細エラー: {traceback.format_exc()}")
        return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})


# ================================================================================
# 実装手順
# ================================================================================
"""
Step 1: dash_app.pyを開く

Step 2: create_shortage_tab関数の後に、create_proportional_abolition_tab関数を追加

Step 3: create_main_ui_tabs()関数内で:
   - タブ定義部分（dcc.Tabs children）に按分廃止タブを追加
   - タブコンテナ部分に按分廃止コンテナを追加

Step 4: update_tab_visibility関数を更新:
   - Output部分に按分廃止タブのstyleを追加
   - 戻り値に按分廃止タブの表示制御を追加

Step 5: 按分廃止コンテンツ初期化コールバックを追加

Step 6: dash_app.pyの動作確認
"""
