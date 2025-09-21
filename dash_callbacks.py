"""Dash callback functions"""

from dash_imports import *
import base64
import io
import zipfile
import shutil
import tempfile
import logging
from pathlib import Path
from user_friendly_messages import UserFriendlyMessages, safe_error_display

# ロガー設定
log = logging.getLogger(__name__)

# グローバル変数
CURRENT_SCENARIO_DIR = None
TEMP_DIRS_TO_CLEANUP = []

def process_upload(contents, filename):
    """ZIPファイルのアップロード処理"""
    global CURRENT_SCENARIO_DIR

    if contents is None:
        return (None, [], None, {'display': 'none'})

    try:
        # ファイルサイズチェック (100MB制限)
        if len(contents) > 100 * 1024 * 1024:  # 100MB
            error_msg = safe_error_display("upload", "file_too_large")
            return (
                {'success': False, 'error': 'ファイルサイズが大きすぎます (最大100MB)', 'user_message': error_msg},
                [],
                None,
                {'display': 'none'}
            )

        # ファイル形式チェック
        if not filename or not filename.lower().endswith('.zip'):
            error_msg = safe_error_display("upload", "invalid_format")
            return (
                {'success': False, 'error': 'ZIPファイルのみ対応しています', 'user_message': error_msg},
                [],
                None,
                {'display': 'none'}
            )

        # Base64デコード
        try:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
        except Exception as decode_error:
            error_msg = safe_error_display("upload", "corrupted_file", str(decode_error))
            return (
                {'success': False, 'error': 'ファイルの読み込みに失敗しました', 'user_message': error_msg},
                [],
                None,
                {'display': 'none'}
            )

        # ZIPファイル処理
        if filename.endswith('.zip'):
            log.info(f"Processing ZIP file: {filename}")

            # 一時ディレクトリに展開
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # ZIP展開
                with zipfile.ZipFile(io.BytesIO(decoded), 'r') as zip_ref:
                    zip_ref.extractall(temp_path)
                    extracted_files = list(temp_path.rglob('*'))
                    log.info(f"Extracted {len(extracted_files)} files")

                # 分析結果を探す
                analysis_dirs = []
                for item in temp_path.iterdir():
                    if item.is_dir():
                        parquet_files = list(item.rglob('*.parquet'))
                        if parquet_files:
                            analysis_dirs.append(item)

                if analysis_dirs:
                    selected_dir = analysis_dirs[0]

                    # 永続的な一時場所にコピー
                    permanent_temp = Path(tempfile.mkdtemp(prefix="ShiftAnalysis_"))
                    TEMP_DIRS_TO_CLEANUP.append(permanent_temp)
                    permanent_analysis_dir = permanent_temp / "analysis_results"
                    shutil.copytree(selected_dir, permanent_analysis_dir)

                    CURRENT_SCENARIO_DIR = permanent_analysis_dir
                    scenario_name = permanent_analysis_dir.name

                    # シナリオリストを作成
                    scenario_options = [{'label': scenario_name, 'value': str(permanent_analysis_dir)}]

                    return (
                        {'success': True, 'path': str(permanent_analysis_dir)},  # data-ingestion-output
                        scenario_options,  # scenario-dropdown options
                        str(permanent_analysis_dir),  # scenario-dropdown value
                        {'display': 'block'}  # scenario-selector-div style
                    )
                else:
                    # 分析結果が見つからない
                    error_msg = safe_error_display("upload", "no_analysis_data")
                    return (
                        {'success': False, 'error': 'ZIPファイルに分析データが含まれていません', 'user_message': error_msg},
                        [],
                        None,
                        {'display': 'none'}
                    )

    except zipfile.BadZipFile:
        error_msg = safe_error_display("upload", "corrupted_file")
        return (
            {'success': False, 'error': 'ZIPファイルが破損しています', 'user_message': error_msg},
            [],
            None,
            {'display': 'none'}
        )
    except MemoryError:
        error_msg = safe_error_display("analysis", "memory_error")
        return (
            {'success': False, 'error': 'ファイルが大きすぎて処理できません', 'user_message': error_msg},
            [],
            None,
            {'display': 'none'}
        )
    except Exception as e:
        log.error(f"Upload processing error: {str(e)}")
        error_msg = safe_error_display("upload", "network_error", str(e))
        return (
            {'success': False, 'error': '予期しないエラーが発生しました', 'user_message': error_msg},
            [],
            None,
            {'display': 'none'}
        )

def register_callbacks(app):
    """Register all callbacks with the Dash app"""

    @app.callback(
        [Output('data-ingestion-output', 'data'),
         Output('scenario-dropdown', 'options'),
         Output('scenario-dropdown', 'value'),
         Output('scenario-selector-div', 'style'),
         Output('upload-status', 'children'),
         Output('upload-progress', 'children')],
        [Input('upload-data', 'contents')],
        [State('upload-data', 'filename'),
         State('session-id-store', 'data')]
    )
    def handle_file_upload(contents, filename, session_id=None):
        # セッションサポート
        if session_id is None:
            from session_integration import session_integration
            session_id = session_integration.get_session_id()
        workspace = session_integration.get_workspace_path(session_id)

        """ZIPファイルアップロード処理のコールバック"""
        # === 詳細ログ開始 ===
        import json
        log.info("\n" + "="*80)
        log.info("🔍 [DETAILED LOG] ZIPアップロード処理開始")
        log.info("="*80)
        log.info(f"📝 Filename: {filename}")
        log.info(f"📦 Contents exists: {contents is not None}")
        if contents:
            log.info(f"📏 Contents length: {len(contents)}")
            log.info(f"🔤 Contents type: {type(contents)}")
            # Base64ヘッダーの確認
            if ',' in contents:
                header, _ = contents.split(',', 1)
                log.info(f"📋 Content header: {header}")
    
        # コールスタック出力
        import traceback
        log.info("📍 Call stack:")
        for line in traceback.format_stack()[-3:]:
            log.info(f"  {line.strip()}")

        import json
    
        log.info("="*80)
        log.info("[SYSTEM FLOW] 1. FRONTEND -> CALLBACK LAYER")
        log.info("="*80)
        log.info(f"[handle_file_upload] ENTRY POINT")
        log.info(f"  - Function: handle_file_upload")
        log.info(f"  - Filename: {filename}")
        log.info(f"  - Contents type: {type(contents)}")
        log.info(f"  - Contents is None: {contents is None}")
    
        if contents:
            # コンテンツの詳細情報
            log.info(f"  - Contents length: {len(contents)}")
            log.info(f"  - Contents preview: {contents[:100]}...")
        
            # Base64フォーマットの確認
            if ',' in contents:
                header, data = contents.split(',', 1)
                log.info(f"  - Data header: {header}")
                log.info(f"  - Data length: {len(data)}")
            else:
                log.info(f"  - WARNING: No comma separator found in contents")
    
        log.info("[handle_file_upload] ========== PROCESSING START ==========")
    
        if contents is None:
            log.info("[handle_file_upload] BRANCH: No contents")
            # デフォルトシナリオがある場合はそれを使用
            if workspace:
                scenarios = [workspace.name]
                log.info(f"[handle_file_upload] Using default scenario: {scenarios}")

                result = (
                    None,
                    [{'label': s, 'value': s} for s in scenarios],
                    scenarios[0] if scenarios else None,
                    {'display': 'block'},
                    html.Div("データがアップロードされていません", style={'color': '#666'}),
                    html.Div()
                )
            
                log.info(f"[handle_file_upload] RETURN (default): tuple with {len(result)} elements")
                return result
            
            log.info("[handle_file_upload] No contents and no default scenario")
            result = (None, [], None, {'display': 'none'},
                     UserFriendlyMessages.create_info_message("no_data"),
                     html.Div())
            log.info(f"[handle_file_upload] RETURN (empty): {result}")
            return result
    
        try:
            log.info("[handle_file_upload] BRANCH: Processing upload")
            log.info(f"[handle_file_upload] Starting to process upload for: {filename}")
        
            # ファイルタイプをチェック
            if not filename.lower().endswith('.zip'):
                log.warning(f"[handle_file_upload] Not a ZIP file: {filename}")
                error_msg = safe_error_display("upload", "invalid_format")
                result = (None, [], None, {'display': 'none'}, error_msg, html.Div())
                log.info(f"[handle_file_upload] RETURN (not zip): {result}")
                return result
        
            # アップロード開始メッセージを表示
            upload_status = UserFriendlyMessages.create_info_message("processing")
            upload_progress = html.Div([
                html.P("ファイルを処理中..."),
                html.Progress(value=0, max=100, style={'width': '100%'})
            ], style={'text-align': 'center'})

            # process_upload関数を呼び出し
            log.info("="*80)
            log.info("[SYSTEM FLOW] 2. CALLBACK -> PROCESSING LAYER")
            log.info("="*80)
            log.info(f"[handle_file_upload] Calling process_upload...")
            log.info(f"  - Input filename: {filename}")
            log.info(f"  - Input contents length: {len(contents)}")

            upload_result = process_upload(contents, filename)
        
            log.info("="*80)
            log.info("[SYSTEM FLOW] 3. PROCESSING -> CALLBACK LAYER")
            log.info("="*80)
            log.info(f"[handle_file_upload] process_upload returned")
            log.info(f"  - Return type: {type(upload_result)}")
            log.info(f"  - Is tuple: {isinstance(upload_result, tuple)}")
            if isinstance(upload_result, tuple):
                log.info(f"  - Tuple length: {len(upload_result)}")
                log.info(f"  - Element types: {[type(x).__name__ for x in upload_result]}")
            log.info(f"  - Return value preview: {str(upload_result)[:500]}")

            if isinstance(upload_result, tuple) and len(upload_result) == 4:
                data, options, value, style = upload_result
                log.info(f"[handle_file_upload] SUCCESS - Unpacked 4 values")
                log.info(f"  - data type: {type(data)}")
                log.info(f"  - data content: {str(data)[:200] if data else 'None'}")
                log.info(f"  - options: {options}")
                log.info(f"  - value: {value}")
                log.info(f"  - style: {style}")
            
                log.info("="*80)
                log.info("[SYSTEM FLOW] 4. CALLBACK -> FRONTEND LAYER")
                log.info("="*80)
                log.info(f"[handle_file_upload] RETURN (success): Sending to frontend")
                log.info(f"  - Returning 4 values to Dash callbacks")
                log.info(f"  - Output 1 (data-ingestion-output): {type(data).__name__}")
                log.info(f"  - Output 2 (scenario-dropdown options): {len(options) if options else 0} items")
                log.info(f"  - Output 3 (scenario-dropdown value): {value}")
                log.info(f"  - Output 4 (scenario-selector-div style): {style}")
            
                # 成功時のUIフィードバック
                if data and data.get('success'):
                    success_msg = UserFriendlyMessages.create_success_message("upload_complete")
                    progress_complete = html.Div([
                        html.P("✅ アップロード完了", style={'color': 'green', 'fontWeight': 'bold'}),
                        html.Progress(value=100, max=100, style={'width': '100%'})
                    ], style={'text-align': 'center'})
                else:
                    # 失敗時のUIフィードバック
                    error_detail = data.get('error', '不明なエラー') if data else '処理に失敗しました'
                    success_msg = safe_error_display("upload", "corrupted_file", error_detail)
                    progress_complete = html.Div()

                # グローバル変数を更新してタブを再読み込み可能にする
                global OUTPUT_DIR
                OUTPUT_DIR = workspace
                log.info(f"[handle_file_upload] OUTPUT_DIR updated to: {OUTPUT_DIR}")

                return data, options, value, style, success_msg, progress_complete
            else:
                # エラーの場合
                log.error(f"[handle_file_upload] UNEXPECTED result format")
                log.error(f"  - Expected: tuple of 4 elements")
                log.error(f"  - Got: {type(upload_result)}")
                log.error(f"  - Result content: {str(upload_result)[:500]}")
                error_msg = safe_error_display("upload", "corrupted_file")
                result = (None, [], None, {'display': 'none'}, error_msg, html.Div())
                log.info(f"[handle_file_upload] RETURN (error): {result}")
                return result
            
        except Exception as e:
            log.error(f"[handle_file_upload] EXCEPTION occurred: {e}", exc_info=True)
            import traceback
            log.error(f"[handle_file_upload] Full traceback:\n{traceback.format_exc()}")
            error_msg = safe_error_display("upload", "network_error", str(e))
            result = (None, [], None, {'display': 'none'}, error_msg, html.Div())
            log.info(f"[handle_file_upload] RETURN (exception): {result}")
            return result
        finally:
            log.info(f"[handle_file_upload] ========== UPLOAD ENDED ==========")
            log.info("="*80)


    @app.callback(
        Output('main-tabs', 'value'),
        Input('selected-tab-store', 'data')
    )
    @safe_callback  
    def update_legacy_tabs(selected_tab, session_id=None):
        # セッションサポート
        if session_id is None:
            from session_integration import session_integration
            session_id = session_integration.get_session_id()
        workspace = session_integration.get_workspace_path(session_id)

        """互換性のため既存タブの値を更新"""
        return selected_tab if selected_tab else 'overview'


    @app.callback(
        Output('overview-content', 'children'),
        [Input('selected-tab-store', 'data'),
         Input('scenario-dropdown', 'value')],
        [State('data-loaded', 'data')],
        State('session-id-store', 'data'),
    )
    def initialize_overview_content(selected_tab, selected_scenario, data_status, session_id=None):
        # セッションサポート
        if session_id is None:
            from session_integration import session_integration
            session_id = session_integration.get_session_id()
        workspace = session_integration.get_workspace_path(session_id)

        """概要タブの内容を初期化"""
        log.info(f"[initialize_overview_content] Called with tab: {selected_tab}, scenario: {selected_scenario}, data_status: {data_status}")
        if not selected_scenario or selected_tab != 'overview':
            raise PreventUpdate
        # data_statusがboolの場合もあるので、Falseの場合のみチェック
        if data_status is False:
            raise PreventUpdate
        try:
            return create_overview_tab(selected_scenario)
        except Exception as e:
            log.error(f"概要タブの初期化エラー: {str(e)}")
            return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

    @app.callback(
        Output('heatmap-content', 'children'),
        [Input('selected-tab-store', 'data'),
         Input('scenario-dropdown', 'value')],
        [State('data-loaded', 'data')],
    )
    @safe_callback
    def initialize_heatmap_content(selected_tab, selected_scenario, data_status):
        """ヒートマップタブの内容を初期化"""
        log.info(f"[initialize_heatmap_content] Called with tab: {selected_tab}, scenario: {selected_scenario}, data_status: {data_status}")
        if not selected_scenario or selected_tab != 'heatmap':
            raise PreventUpdate
        if data_status is False:
            raise PreventUpdate
        try:
            return create_heatmap_tab()
        except Exception as e:
            log.error(f"ヒートマップタブの初期化エラー: {str(e)}")
            return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

    @app.callback(
        Output('shortage-content', 'children'),
        [Input('shortage-tab-container', 'style'),
         Input('scenario-dropdown', 'value')],
        State('data-loaded', 'data'),
    )
    @safe_callback
    def initialize_shortage_content(style_dict, selected_scenario, data_status):
        """不足分析タブの内容を初期化"""
        log.info(f"[shortage_tab] 初期化開始 - style: {style_dict}, scenario: {selected_scenario}, data_status: {data_status}")
    
        # styleがdisplay: blockの場合のみ処理
        if not style_dict or style_dict.get('display') != 'block':
            log.info("[shortage_tab] PreventUpdate - タブが非表示")
            raise PreventUpdate
    
        if not selected_scenario or not data_status:
            log.info("[shortage_tab] PreventUpdate - シナリオまたはデータなし")
            raise PreventUpdate
        try:
            log.info("[shortage_tab] create_shortage_tab呼び出し開始")
            result = create_shortage_tab(selected_scenario)
            log.info("[shortage_tab] create_shortage_tab完了")
            return result
        except Exception as e:
            log.error(f"不足分析タブの初期化エラー: {str(e)}")
            import traceback
            log.error(f"不足分析タブ詳細エラー: {traceback.format_exc()}")
            return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

    @app.callback(
        Output('optimization-content', 'children'),
        [Input('selected-tab-store', 'data'),
         Input('scenario-dropdown', 'value')],
        [State('data-loaded', 'data')],
    )
    @safe_callback
    def initialize_optimization_content(selected_tab, selected_scenario, data_status):
        """最適化分析タブの内容を初期化"""
        if not selected_scenario or selected_tab != 'optimization':
            raise PreventUpdate
        if data_status is False:
            raise PreventUpdate
        try:
            return create_optimization_tab()
        except Exception as e:
            log.error(f"最適化分析タブの初期化エラー: {str(e)}")
            return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

    @app.callback(
        Output('leave-content', 'children'),
        [Input('selected-tab-store', 'data'),
         Input('scenario-dropdown', 'value')],
        [State('data-loaded', 'data')],
    )
    @safe_callback
    def initialize_leave_content(selected_tab, selected_scenario, data_status):
        """休暇分析タブの内容を初期化"""
        log.info(f"[leave_tab] 初期化開始 - scenario: {selected_scenario}, data_status: {data_status}")
    
        if not selected_scenario or not data_status or selected_tab != 'leave':
            log.info("[leave_tab] PreventUpdate - 条件不満足")
            raise PreventUpdate
        try:
            log.info("[leave_tab] create_leave_analysis_tab呼び出し開始")
            result = create_leave_analysis_tab()
            log.info("[leave_tab] create_leave_analysis_tab完了")
            # === 戻り値の詳細ログ ===
            log.info("\n🔍 [RETURN VALUE CHECK]")
            if isinstance(result, tuple) and len(result) == 4:
                data, options, value, style = result
                log.info(f"✅ Returning tuple with 4 elements:")
                log.info(f"  1. data type: {type(data)}, success: {data.get('success') if isinstance(data, dict) else 'N/A'}")
                log.info(f"  2. options count: {len(options) if options else 0}")
                log.info(f"  3. selected value: {value}")
                log.info(f"  4. style: {style}")
                if isinstance(data, dict) and data.get('scenarios'):
                    log.info(f"  📁 Scenarios found: {list(data['scenarios'].keys())}")
                    for scenario, path in data['scenarios'].items():
                        log.info(f"    - {scenario}: {path}")
            else:
                log.info(f"❌ Unexpected return format: {type(result)}")
        
            return result
        except Exception as e:
            log.error(f"休暇分析タブの初期化エラー: {str(e)}")
            import traceback
            log.error(f"休暇分析タブ詳細エラー: {traceback.format_exc()}")
            return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

    @app.callback(
        Output('cost-content', 'children'),
        [Input('selected-tab-store', 'data'),
         Input('scenario-dropdown', 'value')],
        [State('data-loaded', 'data')],
    )
    @safe_callback
    def initialize_cost_content(selected_tab, selected_scenario, data_status):
        """コスト分析タブの内容を初期化"""
        if not selected_scenario or selected_tab != 'cost':
            raise PreventUpdate
        if data_status is False:
            raise PreventUpdate
        try:
            return create_cost_analysis_tab()
        except Exception as e:
            log.error(f"コスト分析タブの初期化エラー: {str(e)}")
            return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

    @app.callback(
        Output('hire-plan-content', 'children'),
        [Input('selected-tab-store', 'data'),
         Input('scenario-dropdown', 'value')],
        [State('data-loaded', 'data')],
    )
    @safe_callback
    def initialize_hire_plan_content(selected_tab, selected_scenario, data_status):
        """採用計画タブの内容を初期化"""
        if not selected_scenario or selected_tab != 'hire_plan':
            raise PreventUpdate
        if data_status is False:
            raise PreventUpdate
        try:
            return create_hire_plan_tab()
        except Exception as e:
            log.error(f"採用計画タブの初期化エラー: {str(e)}")
            return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

    @app.callback(
        Output('fatigue-content', 'children'),
        [Input('selected-tab-store', 'data'),
         Input('scenario-dropdown', 'value')],
        [State('data-loaded', 'data')],
    )
    @safe_callback
    def initialize_fatigue_content(selected_tab, selected_scenario, data_status):
        """疲労分析タブの内容を初期化"""
        if not selected_scenario or selected_tab != 'fatigue':
            raise PreventUpdate
        if data_status is False:
            raise PreventUpdate
        try:
            return create_fatigue_tab()
        except Exception as e:
            log.error(f"疲労分析タブの初期化エラー: {str(e)}")
            return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

    @app.callback(
        Output('forecast-content', 'children'),
        [Input('selected-tab-store', 'data'),
         Input('scenario-dropdown', 'value')],
        [State('data-loaded', 'data')],
    )
    @safe_callback
    def initialize_forecast_content(selected_tab, selected_scenario, data_status):
        """需要予測タブの内容を初期化"""
        if not selected_scenario or selected_tab != 'forecast':
            raise PreventUpdate
        if data_status is False:
            raise PreventUpdate
        try:
            return create_forecast_tab()
        except Exception as e:
            log.error(f"需要予測タブの初期化エラー: {str(e)}")
            return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})

    @app.callback(
        Output('fairness-content', 'children'),
        [Input('selected-tab-store', 'data'),
         Input('scenario-dropdown', 'value')],
        [State('data-loaded', 'data')],
    )
    @safe_callback
    def initialize_fairness_content(selected_tab, selected_scenario, data_status):
        """公平性タブの内容を初期化"""
        if not selected_scenario or selected_tab != 'fairness':
            raise PreventUpdate
        if data_status is False:
            raise PreventUpdate
        try:
            return create_fairness_tab()
        except Exception as e:
            log.error(f"公平性タブの初期化エラー: {str(e)}")
            return html.Div(f"エラーが発生しました: {str(e)}", style={'color': 'red'})


    @app.callback(
        Output('turnover-prediction-history', 'children'),
        [Input('turnover-history-button', 'n_clicks'),
         Input('turnover-clear-history-button', 'n_clicks')],
        prevent_initial_call=True
    )
    @safe_callback
    def handle_prediction_history(history_clicks, clear_clicks):
        """予測履歴の表示・クリア処理"""
        ctx = dash.callback_context
    
        if ctx.triggered:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
            if button_id == 'turnover-clear-history-button':
                # 履歴クリア
                if clear_prediction_history():
                    return html.Div("履歴をクリアしました。", style={'color': 'green', 'padding': '10px'})
                else:
                    return html.Div("履歴のクリアに失敗しました。", style={'color': 'red', 'padding': '10px'})
        
            elif button_id == 'turnover-history-button':
                # 履歴表示
                history_data = load_prediction_history()
                return create_prediction_history_display(history_data)
    
        return ""


