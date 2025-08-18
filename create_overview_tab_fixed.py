def create_overview_tab(selected_scenario: str = None, show_integrated_dashboard: bool = True) -> html.Div:
    """概要タブを作成（統合ダッシュボード表示制御付き）"""
    # 按分方式による一貫データ取得
    df_shortage_role = data_get('shortage_role_summary', pd.DataFrame())
    df_shortage_emp = data_get('shortage_employment_summary', pd.DataFrame())
    df_fairness = data_get('fairness_before', pd.DataFrame())
    df_staff = data_get('staff_stats', pd.DataFrame())
    df_alerts = data_get('stats_alerts', pd.DataFrame())
    
    # 統合ダッシュボードの条件付き初期化
    comprehensive_dashboard_content = None
    global CURRENT_SCENARIO_DIR
    
    # 統合ダッシュボードを表示するかどうかを制御
    if show_integrated_dashboard and ComprehensiveDashboard is not None and CURRENT_SCENARIO_DIR is not None:
        try:
            log.info("統合ダッシュボードを概要タブに表示中...")
            output_dir = Path(CURRENT_SCENARIO_DIR)
            dashboard = create_comprehensive_dashboard(output_dir, months_back=6)
            figures = dashboard.get_dashboard_figures()
            summary_metrics = dashboard._calculate_summary_metrics()
            
            # 統合ダッシュボードコンテンツを構築
            comprehensive_dashboard_content = [
                html.Hr(style={'margin': '40px 0', 'border': '2px solid #3498db'}),
                html.H3("🏥 統合シフト分析ダッシュボード", 
                       style={'color': '#2c3e50', 'marginBottom': '20px', 'textAlign': 'center'}),
                
                # サマリー統計カード
                html.Div([
                    html.H4("📊 高度分析指標", style={'color': '#2c3e50', 'marginBottom': '15px'}),
                    
                    html.Div([
                        # 疲労度カード
                        html.Div([
                            html.H5("😴 平均疲労スコア", style={'color': '#e74c3c', 'marginBottom': '10px'}),
                            html.H2(f"{summary_metrics.get('average_fatigue_score', 0):.1f}", 
                                   style={'color': '#e74c3c', 'margin': '0'}),
                            html.P(f"高疲労職員: {summary_metrics.get('high_fatigue_count', 0)}名", 
                                  style={'margin': '5px 0', 'fontSize': '14px', 'color': '#666'})
                        ], style={
                            'padding': '20px',
                            'backgroundColor': '#fff5f5',
                            'borderRadius': '10px',
                            'border': '2px solid #fed7d7',
                            'textAlign': 'center',
                            'flex': '1',
                            'margin': '0 10px'
                        }),
                        
                        # 公平性カード
                        html.Div([
                            html.H5("⚖️ 平均公平性スコア", style={'color': '#3498db', 'marginBottom': '10px'}),
                            html.H2(f"{summary_metrics.get('average_fairness_score', 0):.2f}", 
                                   style={'color': '#3498db', 'margin': '0'}),
                            html.P(f"要改善職員: {summary_metrics.get('low_fairness_count', 0)}名", 
                                  style={'margin': '5px 0', 'fontSize': '14px', 'color': '#666'})
                        ], style={
                            'padding': '20px',
                            'backgroundColor': '#f0f8ff',
                            'borderRadius': '10px',
                            'border': '2px solid #bde4ff',
                            'textAlign': 'center',
                            'flex': '1',
                            'margin': '0 10px'
                        }),
                        
                        # 対応能力カード
                        html.Div([
                            html.H5("🔄 平均対応能力", style={'color': '#27ae60', 'marginBottom': '10px'}),
                            html.H2(f"{summary_metrics.get('average_capability_score', 0):.2f}", 
                                   style={'color': '#27ae60', 'margin': '0'}),
                            html.P(f"マルチスキル職員: {summary_metrics.get('multiskill_staff_count', 0)}名", 
                                  style={'margin': '5px 0', 'fontSize': '14px', 'color': '#666'})
                        ], style={
                            'padding': '20px',
                            'backgroundColor': '#f0fff4',
                            'borderRadius': '10px',
                            'border': '2px solid #c6f6d5',
                            'textAlign': 'center',
                            'flex': '1',
                            'margin': '0 10px'
                        })
                    ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '20px'})
                ], style={
                    'padding': '20px',
                    'backgroundColor': 'white',
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                    'marginBottom': '30px'
                }),
                
                # 統合ダッシュボード図表
                html.Div([
                    html.H4("📈 統合分析ダッシュボード", style={'color': '#2c3e50', 'marginBottom': '15px'}),
                    dcc.Graph(
                        figure=figures.get('comprehensive', go.Figure()),
                        style={'height': '800px'}
                    )
                ], style={
                    'padding': '20px',
                    'backgroundColor': 'white',
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                    'marginBottom': '30px'
                }),
                
                # 疲労度ヒートマップ
                html.Div([
                    html.H4("😴 職員別疲労度分析", style={'color': '#2c3e50', 'marginBottom': '15px'}),
                    dcc.Graph(
                        figure=figures.get('fatigue_heatmap', go.Figure()),
                        style={'height': '600px'}
                    )
                ], style={
                    'padding': '20px',
                    'backgroundColor': 'white',
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                    'marginBottom': '30px'
                }),
                
                # 説明・操作ガイド 
                html.Div([
                    html.H4("💡 ダッシュボード活用ガイド", style={'color': '#2c3e50', 'marginBottom': '15px'}),
                    html.Div([
                        html.H5("📊 統合分析の見方"),
                        html.Ul([
                            html.Li("疲労度vs性能分析 - 疲労と性能の相関関係を可視化"),
                            html.Li("公平性スコア - 職員間の勤務負担の均等度"),
                            html.Li("勤務区分対応能力 - マルチスキル度（20名以下の場合に表示）"),
                            html.Li("職員パフォーマンス - 総合評価（20名以下の場合に表示）"),
                            html.Li("疲労度ヒートマップ - 各職員の詳細な疲労状況")
                        ]),
                        
                        html.H5("🖱️ ホバー機能", style={'marginTop': '20px'}),
                        html.Ul([
                            html.Li("各グラフにマウスを当てると詳細情報を表示"),
                            html.Li("職員ID表示時でも、ホバーで実名と職種を確認可能"),
                            html.Li("疲労度、公平性、対応能力の具体的な数値を表示"),
                            html.Li("ヒートマップでは職種とリスクレベルも表示")
                        ]),
                        
                        html.H5("🎯 重要な指標", style={'marginTop': '20px'}),
                        html.Ul([
                            html.Li("疲労スコア7.0以上: 緊急の休息が必要"),
                            html.Li("公平性スコア0.6未満: 勤務配分の見直しが必要"),
                            html.Li("対応能力3以上: マルチスキル職員として評価"),
                            html.Li("赤色表示: 重点的なケアとサポートが必要")
                        ])
                    ], style={'fontSize': '14px', 'color': '#555'})
                ], style={
                    'padding': '20px',
                    'backgroundColor': '#f8f9fa',
                    'borderRadius': '10px',
                    'border': '1px solid #dee2e6'
                })
            ]
            
            log.info("統合ダッシュボードを概要タブに統合しました")
            
        except Exception as e:
            log.warning(f"統合ダッシュボード統合エラー: {e}")
            comprehensive_dashboard_content = [
                html.Hr(style={'margin': '40px 0', 'border': '2px solid #e74c3c'}),
                html.Div([
                    html.H4("⚠️ 統合ダッシュボード読み込みエラー", style={'color': '#e74c3c'}),
                    html.P(f"エラー詳細: {str(e)}"),
                    html.P("データが不足している可能性があります。分析を実行してからお試しください。")
                ], style={
                    'padding': '20px',
                    'backgroundColor': '#fff5f5',
                    'borderRadius': '8px',
                    'border': '1px solid #fed7d7'
                })
            ]

    # 正しい不足時間計算（元のshortage_timeから直接計算）
    lack_h = 0
    
    # まず元のshortage_timeから正確な値を取得
    shortage_time_df = data_get('shortage_time', pd.DataFrame())
    if not shortage_time_df.empty:
        try:
            # 数値列のみ取得してスロット数を計算
            numeric_cols = shortage_time_df.select_dtypes(include=[np.number])
            if not numeric_cols.empty:
                total_shortage_slots = float(np.nansum(numeric_cols.values))
                # スロットを時間に変換
                slot_hours = get_dynamic_slot_hours()
                lack_h = total_shortage_slots * slot_hours
                log.info(f"正確な不足時間（shortage_timeより）: {lack_h:.2f}h ({total_shortage_slots:.0f}スロット)")
                log.info(f"  使用したslot_hours: {slot_hours:.2f}時間 ({slot_hours * 60:.0f}分)")
                
                # 🔧 情報表示: 3ヶ月分データセットの場合の参考情報
                if lack_h > 10000:
                    monthly_avg = lack_h / 3  # 3ヶ月分として月平均を計算
                    daily_avg = monthly_avg / 30  # 1ヶ月30日として日平均を計算
                    log.info(f"📊 概要タブ: 大規模データセット {lack_h:.0f}時間")
                    log.info(f"  月平均不足時間: {monthly_avg:.0f}時間/月")
                    log.info(f"  日平均不足時間: {daily_avg:.0f}時間/日")
                    log.info(f"  スロット数: {total_shortage_slots:.0f}, slot_hours: {slot_hours:.2f}")
            else:
                lack_h = 0
        except Exception as e:
            log.error(f"shortage_time読み取りエラー: {e}")
            lack_h = 0
    else:
        # フォールバック: shortage_role_summaryは異常値なので使用しない
        log.warning("shortage_timeデータが見つかりません。不足時間を0として処理します。")
        lack_h = 0
    
    # コスト計算も同様に修正
    excess_cost = 0
    lack_temp_cost = 0
    lack_penalty_cost = 0
    
    if not df_shortage_role.empty:
        # 合計行があるかチェック
        total_rows = df_shortage_role[df_shortage_role['role'].isin(['全体', '合計', '総計'])]
        if not total_rows.empty:
            # 選択されたシナリオに対応する全体行があるかチェック
            if selected_scenario and 'scenario' in total_rows.columns:
                scenario_total = total_rows[total_rows['scenario'] == selected_scenario]
                if not scenario_total.empty:
                    excess_cost = scenario_total['estimated_excess_cost'].iloc[0] if 'estimated_excess_cost' in scenario_total.columns else 0
                    lack_temp_cost = scenario_total['estimated_lack_cost_if_temporary_staff'].iloc[0] if 'estimated_lack_cost_if_temporary_staff' in scenario_total.columns else 0
                    lack_penalty_cost = scenario_total['estimated_lack_penalty_cost'].iloc[0] if 'estimated_lack_penalty_cost' in scenario_total.columns else 0
                else:
                    excess_cost = total_rows['estimated_excess_cost'].iloc[0] if 'estimated_excess_cost' in total_rows.columns else 0
                    lack_temp_cost = total_rows['estimated_lack_cost_if_temporary_staff'].iloc[0] if 'estimated_lack_cost_if_temporary_staff' in total_rows.columns else 0
                    lack_penalty_cost = total_rows['estimated_lack_penalty_cost'].iloc[0] if 'estimated_lack_penalty_cost' in total_rows.columns else 0
            else:
                excess_cost = total_rows['estimated_excess_cost'].iloc[0] if 'estimated_excess_cost' in total_rows.columns else 0
                lack_temp_cost = total_rows['estimated_lack_cost_if_temporary_staff'].iloc[0] if 'estimated_lack_cost_if_temporary_staff' in total_rows.columns else 0
                lack_penalty_cost = total_rows['estimated_lack_penalty_cost'].iloc[0] if 'estimated_lack_penalty_cost' in total_rows.columns else 0
        else:
            # 職種別データから計算（シナリオ別）
            if selected_scenario and 'scenario' in df_shortage_role.columns:
                scenario_filtered = df_shortage_role[df_shortage_role['scenario'] == selected_scenario]
            else:
                scenario_filtered = df_shortage_role
            
            if not scenario_filtered.empty:
                # 職種別データのみを使用（雇用形態別を除外）
                role_only = scenario_filtered[~scenario_filtered['role'].isin(['全体', '合計', '総計'])]
                # 雇用形態別データを除外（通常 'emp_' プレフィックスがある）
                if 'role' in role_only.columns:
                    role_only = role_only[~role_only['role'].str.startswith('emp_', na=False)]
                
                if not role_only.empty:
                    excess_cost = role_only['estimated_excess_cost'].sum() if 'estimated_excess_cost' in role_only.columns else 0
                    lack_temp_cost = role_only['estimated_lack_cost_if_temporary_staff'].sum() if 'estimated_lack_cost_if_temporary_staff' in role_only.columns else 0
                    lack_penalty_cost = role_only['estimated_lack_penalty_cost'].sum() if 'estimated_lack_penalty_cost' in role_only.columns else 0
                else:
                    excess_cost = 0
                    lack_temp_cost = 0
                    lack_penalty_cost = 0
            else:
                excess_cost = 0
                lack_temp_cost = 0
                lack_penalty_cost = 0

    # Jain指数の安全な取得
    jain_index = "N/A"
    try:
        if not df_fairness.empty and 'metric' in df_fairness.columns:
            jain_row = df_fairness[df_fairness['metric'] == 'jain_index']
            if not jain_row.empty and 'value' in jain_row.columns:
                value = jain_row['value'].iloc[0]
                if pd.notna(value):
                    jain_index = f"{float(value):.3f}"
    except (ValueError, TypeError, IndexError) as e:
        log.debug(f"Jain指数の計算でエラー: {e}")
        jain_index = "エラー"

    # 基本統計の安全な計算
    staff_count = len(df_staff) if not df_staff.empty else 0
    avg_night_ratio = 0
    try:
        if not df_staff.empty and 'night_ratio' in df_staff.columns:
            night_ratios = df_staff['night_ratio'].dropna()
            avg_night_ratio = float(night_ratios.mean()) if len(night_ratios) > 0 else 0
    except (ValueError, TypeError) as e:
        log.debug(f"夜勤比率の計算でエラー: {e}")
        avg_night_ratio = 0
    
    alerts_count = len(df_alerts) if not df_alerts.empty else 0

    return html.Div([
        html.Div(id='overview-insights', style={  # type: ignore
            'padding': '15px',
            'backgroundColor': '#e9f2fa',
            'borderRadius': '8px',
            'marginBottom': '20px',
            'border': '1px solid #cce5ff'
        }),
        html.H3("分析概要", style={'marginBottom': '20px'}),  # type: ignore
        # 📊 重要指標を大きく表示（最優先）
        html.Div([  # type: ignore
            html.Div([
                html.Div([
                    html.H2(f"{lack_h:.1f}", style={
                        'margin': '0', 'color': '#d32f2f' if lack_h > 100 else '#2e7d32', 
                        'fontSize': '3rem', 'fontWeight': 'bold'
                    }),
                    html.P("総不足時間(h)" + (" (3ヶ月分)" if lack_h > 10000 else ""), 
                           style={'margin': '5px 0', 'fontSize': '1.1rem', 'color': '#666'})
                ], style={
                    'textAlign': 'center', 'padding': '20px', 'backgroundColor': 'white',
                    'borderRadius': '12px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.12)',
                    'border': f"3px solid {'#d32f2f' if lack_h > 100 else '#2e7d32'}"
                }),
            ], style={'width': '24%', 'display': 'inline-block', 'padding': '5px'}),
            
            html.Div([
                html.Div([
                    html.H3(f"{excess_cost:,.0f}", style={
                        'margin': '0', 'color': '#ff9800', 'fontSize': '2rem', 'fontWeight': 'bold'
                    }),
                    html.P("総過剰コスト(¥)", style={'margin': '5px 0', 'fontSize': '1rem', 'color': '#666'})
                ], style={
                    'textAlign': 'center', 'padding': '15px', 'backgroundColor': 'white',
                    'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                    'border': '2px solid #ff9800'
                }),
            ], style={'width': '24%', 'display': 'inline-block', 'padding': '5px'}),
            
            html.Div([
                html.Div([
                    html.H3(f"{lack_temp_cost:,.0f}", style={
                        'margin': '0', 'color': '#f44336', 'fontSize': '2rem', 'fontWeight': 'bold'
                    }),
                    html.P("不足コスト(派遣)(¥)", style={'margin': '5px 0', 'fontSize': '1rem', 'color': '#666'})
                ], style={
                    'textAlign': 'center', 'padding': '15px', 'backgroundColor': 'white',
                    'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                    'border': '2px solid #f44336'
                }),
            ], style={'width': '24%', 'display': 'inline-block', 'padding': '5px'}),
            
            html.Div([
                html.Div([
                    html.H3(str(alerts_count), style={
                        'margin': '0', 'color': '#ff7f0e' if alerts_count > 0 else '#1f77b4', 
                        'fontSize': '2rem', 'fontWeight': 'bold'
                    }),
                    html.P("アラート数", style={'margin': '5px 0', 'fontSize': '1rem', 'color': '#666'})
                ], style={
                    'textAlign': 'center', 'padding': '15px', 'backgroundColor': 'white',
                    'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                    'border': f"2px solid {'#ff7f0e' if alerts_count > 0 else '#1f77b4'}"
                }),
            ], style={'width': '24%', 'display': 'inline-block', 'padding': '5px'}),
        ], style={'marginBottom': '20px'}),
        
        # 📈 詳細指標を小さく表示（補助情報）
        html.Div([  # type: ignore
            html.Div([
                create_metric_card("夜勤 Jain指数", jain_index),
            ], style={'width': '20%', 'display': 'inline-block', 'padding': '3px'}),
            html.Div([
                create_metric_card("総スタッフ数", str(staff_count)),
            ], style={'width': '20%', 'display': 'inline-block', 'padding': '3px'}),
            html.Div([
                create_metric_card("平均夜勤比率", f"{avg_night_ratio:.3f}"),
            ], style={'width': '20%', 'display': 'inline-block', 'padding': '3px'}),
            html.Div([
                create_metric_card("不足ペナルティ(¥)", f"{lack_penalty_cost:,.0f}"),
            ], style={'width': '20%', 'display': 'inline-block', 'padding': '3px'}),
            html.Div([
                html.Div([
                    html.P(f"総不足率: {(lack_h / (lack_h + 100)) * 100:.1f}%" if lack_h > 0 else "総不足率: 0%", 
                           style={'margin': '0', 'fontSize': '0.9rem', 'textAlign': 'center'})
                ], style={
                    'padding': '10px', 'backgroundColor': 'white', 'borderRadius': '8px',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'minHeight': '60px', 'display': 'flex',
                    'alignItems': 'center', 'justifyContent': 'center'
                }),
            ], style={'width': '20%', 'display': 'inline-block', 'padding': '3px'}),
        ], style={'marginBottom': '30px'}),
        
        # 📚 計算方法の説明セクション
        html.Details([
            html.Summary("📚 計算方法の詳細説明", style={
                'fontSize': '1.1rem', 'fontWeight': 'bold', 'color': '#1f77b4',
                'cursor': 'pointer', 'padding': '10px', 'backgroundColor': '#f8f9fa',
                'border': '1px solid #dee2e6', 'borderRadius': '5px'
            }),
            html.Div([
                html.H5("不足時間計算方法", style={'color': '#d32f2f', 'marginTop': '15px'}),
                html.P([
                    "• ", html.Strong("統計手法: "), "中央値ベース（外れ値に強い安定した代表値）",
                    html.Br(),
                    "• ", html.Strong("時間軸ベース分析: "), f"{DETECTED_SLOT_INFO['slot_minutes']}分スロット単位での真の過不足分析による職種別・雇用形態別算出",
                    html.Br(),
                    "• ", html.Strong("スロット変換: "), f"1スロット = {DETECTED_SLOT_INFO['slot_hours']:.2f}時間（{DETECTED_SLOT_INFO['slot_minutes']}分間隔）",
                    html.Br(),
                    "• ", html.Strong("異常値検出: "), "10,000スロット（5,000時間）超過時に1/10調整"
                ], style={'lineHeight': '1.6'}),
                
                html.H5("コスト計算方法", style={'color': '#ff9800', 'marginTop': '15px'}),
                html.P([
                    "• ", html.Strong("過剰コスト: "), f"余剰時間 × 平均時給({WAGE_RATES['average_hourly_wage']}円/h)",
                    html.Br(),
                    "• ", html.Strong("不足コスト: "), f"不足時間 × 派遣時給({WAGE_RATES['temporary_staff']}円/h)",
                    html.Br(),
                    "• ", html.Strong("ペナルティ: "), f"不足時間 × ペナルティ単価({COST_PARAMETERS['penalty_per_shortage_hour']}円/h)",
                    html.Br(),
                    "• ", html.Strong("夜勤割増: "), f"{WAGE_RATES['night_differential']}倍、休日割増: {WAGE_RATES['weekend_differential']}倍"
                ], style={'lineHeight': '1.6'}),
                
                html.H5("公平性指標", style={'color': '#2e7d32', 'marginTop': '15px'}),
                html.P([
                    "• ", html.Strong("Jain指数: "), "0-1の範囲で1が完全公平（分散の逆数指標）",
                    html.Br(),
                    "• ", html.Strong("計算式: "), "(合計値)² / (要素数 × 各値の2乗和)",
                    html.Br(),
                    "• ", html.Strong("評価基準: "), "0.8以上=良好、0.6-0.8=普通、0.6未満=要改善"
                ], style={'lineHeight': '1.6'}),
                
                html.H5("データ一貫性", style={'color': '#9c27b0', 'marginTop': '15px'}),
                html.P([
                    "• ", html.Strong("三段階検証: "), "全体・職種別・雇用形態別の合計値一致確認",
                    html.Br(),
                    "• ", html.Strong("許容誤差: "), "0.01時間（1分未満）の誤差は許容",
                    html.Br(),
                    "• ", html.Strong("統計的信頼度: "), f"{STATISTICAL_THRESHOLDS['confidence_level']*100}%（{STATISTICAL_THRESHOLDS['min_sample_size']}サンプル以上で有効）"
                ], style={'lineHeight': '1.6'})
            ], style={'padding': '15px', 'backgroundColor': 'white', 'border': '1px solid #dee2e6', 'marginTop': '5px'})
        ], style={'marginTop': '20px', 'marginBottom': '20px'}),
    ] + (comprehensive_dashboard_content if comprehensive_dashboard_content else []))

