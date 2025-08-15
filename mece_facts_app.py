#!/usr/bin/env python3
"""
MECE事実抽出専用アプリケーション
軸1(施設ルール)のMECE事実抽出を独立した環境で実行・確認

使用方法:
1. python mece_facts_app.py を実行
2. ブラウザで http://localhost:8051 にアクセス
3. Excelファイルをアップロード
4. MECE事実抽出を実行
5. 結果を確認・エクスポート
"""

import os
import sys
import json
import tempfile
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

import dash
from dash import dcc, html, dash_table, Input, Output, State, callback
from dash.exceptions import PreventUpdate
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# MECE事実抽出システムのインポート
try:
    from shift_suite.tasks.mece_fact_extractor import MECEFactExtractor
    from shift_suite.tasks.io_excel import ingest_excel
    from shift_suite.tasks.advanced_blueprint_engine_v2 import AdvancedBlueprintEngineV2
except ImportError as e:
    print(f"必要なモジュールのインポートに失敗しました: {e}")
    print("このアプリを実行するには、shift_suiteモジュールが必要です。")
    sys.exit(1)

# Dashアプリケーション初期化
app = dash.Dash(
    __name__,
    title="MECE事実抽出システム",
    suppress_callback_exceptions=True
)

# アプリのレイアウト
app.layout = html.Div([
    # ヘッダー
    html.Div([
        html.H1("📋 MECE事実抽出システム", style={'color': '#1976d2', 'textAlign': 'center'}),
        html.P("軸1(施設ルール) - 過去シフト実績からの事実ベース制約抽出", 
               style={'textAlign': 'center', 'color': '#666', 'fontSize': '1.1em'})
    ], style={'padding': '20px', 'backgroundColor': '#f5f5f5', 'marginBottom': '30px'}),
    
    # メインコンテンツ
    html.Div([
        # ファイルアップロードセクション
        html.Div([
            html.H3("📁 データアップロード"),
            dcc.Upload(
                id='upload-excel',
                children=html.Div([
                    html.I(className="fa fa-upload", style={'fontSize': '2em', 'marginBottom': '10px'}),
                    html.Div('シフト実績Excelファイルをドラッグ&ドロップ または クリックして選択'),
                    html.Small('対応形式: .xlsx, .xls', style={'color': '#666'})
                ]),
                style={
                    'width': '100%', 'height': '120px', 'lineHeight': '60px',
                    'borderWidth': '2px', 'borderStyle': 'dashed', 'borderRadius': '10px',
                    'textAlign': 'center', 'margin': '10px 0', 'backgroundColor': '#fafafa',
                    'cursor': 'pointer', 'border': '2px dashed #1976d2'
                },
                multiple=False
            ),
            html.Div(id='upload-status', style={'marginTop': '10px'})
        ], style={'marginBottom': '30px', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
        
        # 設定セクション
        html.Div([
            html.H3("⚙️ 分析設定"),
            html.Div([
                html.Div([
                    html.Label("実績シート名 (カンマ区切り):"),
                    dcc.Input(
                        id='sheet-names-input',
                        type='text',
                        placeholder='例: 1月,2月,3月',
                        value='Sheet1',
                        style={'width': '100%', 'padding': '8px', 'borderRadius': '4px', 'border': '1px solid #ddd'}
                    )
                ], style={'marginBottom': '15px'}),
                
                html.Div([
                    html.Div([
                        html.Label("ヘッダー行 (1-indexed):"),
                        dcc.Input(
                            id='header-row-input',
                            type='number',
                            value=1,
                            min=1,
                            style={'width': '100%', 'padding': '8px', 'borderRadius': '4px', 'border': '1px solid #ddd'}
                        )
                    ], style={'width': '48%', 'display': 'inline-block'}),
                    
                    html.Div([
                        html.Label("スロット長 (分):"),
                        dcc.Input(
                            id='slot-minutes-input',
                            type='number',
                            value=30,
                            min=1,
                            style={'width': '100%', 'padding': '8px', 'borderRadius': '4px', 'border': '1px solid #ddd'}
                        )
                    ], style={'width': '48%', 'display': 'inline-block', 'marginLeft': '4%'})
                ]),
                
                html.Div([
                    html.Label("年月セル位置 (例: A1):"),
                    dcc.Input(
                        id='year-month-cell-input',
                        type='text',
                        placeholder='例: A1',
                        style={'width': '100%', 'padding': '8px', 'borderRadius': '4px', 'border': '1px solid #ddd'}
                    )
                ], style={'marginTop': '15px'})
            ])
        ], style={'marginBottom': '30px', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
        
        # 実行ボタン
        html.Div([
            html.Button(
                "🔍 MECE事実抽出を実行",
                id='execute-button',
                n_clicks=0,
                disabled=True,
                style={
                    'width': '100%', 'padding': '15px', 'fontSize': '1.2em',
                    'backgroundColor': '#1976d2', 'color': 'white', 'border': 'none',
                    'borderRadius': '8px', 'cursor': 'pointer'
                }
            )
        ], style={'marginBottom': '30px'}),
        
        # 結果表示セクション
        dcc.Loading(
            id="loading-analysis",
            type="default",
            children=html.Div(id='results-container')
        )
    ], style={'maxWidth': '1200px', 'margin': '0 auto', 'padding': '0 20px'}),
    
    # データストア
    dcc.Store(id='excel-data-store'),
    dcc.Store(id='mece-results-store'),
    dcc.Download(id="download-constraints"),
    dcc.Download(id="download-report")
], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#f0f2f5', 'minHeight': '100vh'})


@app.callback(
    [Output('excel-data-store', 'data'),
     Output('upload-status', 'children'),
     Output('execute-button', 'disabled')],
    Input('upload-excel', 'contents'),
    State('upload-excel', 'filename')
)
def handle_file_upload(contents, filename):
    """ファイルアップロード処理"""
    if contents is None:
        return None, "", True
    
    try:
        import base64
        import io
        
        # ファイル内容をデコード
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(decoded)
            temp_path = tmp_file.name
        
        # ファイル情報を保存
        file_info = {
            'filename': filename,
            'temp_path': temp_path,
            'upload_time': datetime.now().isoformat()
        }
        
        status_msg = html.Div([
            html.Span("✅ ", style={'color': 'green'}),
            f"アップロード完了: {filename}",
            html.Br(),
            html.Small(f"サイズ: {len(decoded)} bytes", style={'color': '#666'})
        ])
        
        return file_info, status_msg, False
        
    except Exception as e:
        error_msg = html.Div([
            html.Span("❌ ", style={'color': 'red'}),
            f"アップロードエラー: {str(e)}"
        ])
        return None, error_msg, True


@app.callback(
    [Output('mece-results-store', 'data'),
     Output('results-container', 'children')],
    Input('execute-button', 'n_clicks'),
    [State('excel-data-store', 'data'),
     State('sheet-names-input', 'value'),
     State('header-row-input', 'value'),
     State('slot-minutes-input', 'value'),
     State('year-month-cell-input', 'value')],
    prevent_initial_call=True
)
def execute_mece_analysis(n_clicks, file_info, sheet_names, header_row, slot_minutes, year_month_cell):
    """MECE事実抽出を実行"""
    if not n_clicks or not file_info:
        raise PreventUpdate
    
    try:
        # パラメータ準備
        excel_path = Path(file_info['temp_path'])
        shift_sheets = [s.strip() for s in sheet_names.split(',') if s.strip()]
        header_row_zero_indexed = (header_row or 1) - 1
        slot_min = slot_minutes or 30
        ym_cell = year_month_cell.strip() if year_month_cell else None
        
        # データ読み込み
        long_df, wt_df, unknown_codes = ingest_excel(
            excel_path,
            shift_sheets=shift_sheets,
            header_row=header_row_zero_indexed,
            slot_minutes=slot_min,
            year_month_cell_location=ym_cell
        )
        
        if long_df.empty:
            error_result = html.Div([
                html.H4("❌ データ読み込みエラー", style={'color': 'red'}),
                html.P("有効なシフトデータが見つかりませんでした。設定を確認してください。")
            ])
            return {}, error_result
        
        # MECE事実抽出実行
        extractor = MECEFactExtractor()
        mece_results = extractor.extract_axis1_facility_rules(long_df, wt_df)
        
        # 結果表示用コンポーネント作成
        results_display = create_results_display(mece_results, long_df, unknown_codes)
        
        # 一時ファイル削除
        try:
            os.unlink(file_info['temp_path'])
        except:
            pass
            
        return mece_results, results_display
        
    except Exception as e:
        error_result = html.Div([
            html.H4("❌ 処理エラー", style={'color': 'red'}),
            html.P(f"エラー詳細: {str(e)}"),
            html.Details([
                html.Summary("スタックトレース"),
                html.Pre(traceback.format_exc(), style={'backgroundColor': '#f5f5f5', 'padding': '10px'})
            ])
        ])
        return {}, error_result


def create_results_display(mece_results: Dict[str, Any], long_df: pd.DataFrame, unknown_codes: set) -> html.Div:
    """結果表示コンポーネントを作成"""
    human_readable = mece_results.get('human_readable', {})
    machine_readable = mece_results.get('machine_readable', {})
    extraction_metadata = mece_results.get('extraction_metadata', {})
    
    summary = human_readable.get('抽出事実サマリー', {})
    confidence_classification = human_readable.get('確信度別分類', {})
    mece_facts = human_readable.get('MECE分解事実', {})
    data_quality = extraction_metadata.get('data_quality', {})
    
    return html.Div([
        # 成功メッセージ
        html.Div([
            html.H3("✅ MECE事実抽出完了", style={'color': 'green', 'textAlign': 'center'}),
            html.P(f"処理レコード数: {len(long_df):,} 件", style={'textAlign': 'center', 'color': '#666'})
        ], style={'marginBottom': '30px'}),
        
        # サマリーカード
        html.Div([
            html.H4("📊 抽出サマリー"),
            html.Div([
                html.Div([
                    html.H3(f"{summary.get('総事実数', 0)}", style={'margin': '0', 'color': '#1976d2'}),
                    html.P("総事実数", style={'margin': '5px 0 0 0'})
                ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#e3f2fd', 'borderRadius': '8px'}),
                
                html.Div([
                    html.H3(f"{len(summary) - 1}", style={'margin': '0', 'color': '#388e3c'}),
                    html.P("分析カテゴリー", style={'margin': '5px 0 0 0'})
                ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#e8f5e8', 'borderRadius': '8px'}),
                
                html.Div([
                    html.H3(f"{data_quality.get('completeness_ratio', 0):.1%}", style={'margin': '0', 'color': '#f57c00'}),
                    html.P("データ完全性", style={'margin': '5px 0 0 0'})
                ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#fff3e0', 'borderRadius': '8px'}),
                
                html.Div([
                    html.H3(f"{data_quality.get('staff_count', 0)}", style={'margin': '0', 'color': '#7b1fa2'}),
                    html.P("分析対象スタッフ", style={'margin': '5px 0 0 0'})
                ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#f3e5f5', 'borderRadius': '8px'})
            ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '15px'})
        ], style={'marginBottom': '30px', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '8px'}),
        
        # 確信度別分類
        html.Div([
            html.H4("🎯 確信度別事実分類"),
            html.Div([
                # 高確信度
                html.Div([
                    html.H5("高確信度 (≥80%)", style={'color': '#2e7d32', 'margin': '0 0 10px 0'}),
                    html.H4(f"{len(confidence_classification.get('高確信度', []))}件", style={'margin': '0', 'color': '#2e7d32'}),
                    html.P("AI実行で高信頼性", style={'fontSize': '0.9em', 'color': '#666'})
                ], style={'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#e8f5e8', 'borderRadius': '8px'}),
                
                # 中確信度
                html.Div([
                    html.H5("中確信度 (50-80%)", style={'color': '#f57c00', 'margin': '0 0 10px 0'}),
                    html.H4(f"{len(confidence_classification.get('中確信度', []))}件", style={'margin': '0', 'color': '#f57c00'}),
                    html.P("人間確認推奨", style={'fontSize': '0.9em', 'color': '#666'})
                ], style={'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#fff3e0', 'borderRadius': '8px'}),
                
                # 低確信度
                html.Div([
                    html.H5("低確信度 (<50%)", style={'color': '#d32f2f', 'margin': '0 0 10px 0'}),
                    html.H4(f"{len(confidence_classification.get('低確信度', []))}件", style={'margin': '0', 'color': '#d32f2f'}),
                    html.P("要検証・除外検討", style={'fontSize': '0.9em', 'color': '#666'})
                ], style={'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#ffebee', 'borderRadius': '8px'})
            ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(3, 1fr)', 'gap': '15px'})
        ], style={'marginBottom': '30px', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '8px'}),
        
        # MECE分解事実詳細
        html.Div([
            html.H4("🔍 MECE分解事実詳細"),
            html.Div([
                html.Div([
                    html.H5(f"{category} ({len(facts)}件)", style={'color': '#1976d2'}),
                    html.Div([
                        html.P(f"• {fact.get('事実タイプ', '不明')}: {fact.get('詳細', '')}")
                        for fact in facts[:3]  # 最初の3件のみ
                    ]),
                    html.P(f"...他{max(0, len(facts) - 3)}件", style={'color': '#666', 'fontStyle': 'italic'}) if len(facts) > 3 else html.Div()
                ], style={'margin': '10px 0', 'padding': '15px', 'border': '1px solid #ddd', 'borderRadius': '8px'})
                for category, facts in mece_facts.items() if facts
            ])
        ], style={'marginBottom': '30px', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '8px'}),
        
        # AI実行用制約サマリー
        html.Div([
            html.H4("🤖 AI実行用制約データ"),
            html.Div([
                html.Div([
                    html.H4(f"{len(machine_readable.get('hard_constraints', []))}", style={'margin': '0', 'color': '#d32f2f'}),
                    html.P("ハード制約", style={'margin': '5px 0 0 0'}),
                    html.Small("必須遵守", style={'color': '#666'})
                ], style={'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#ffebee', 'borderRadius': '8px'}),
                
                html.Div([
                    html.H4(f"{len(machine_readable.get('soft_constraints', []))}", style={'margin': '0', 'color': '#f57c00'}),
                    html.P("ソフト制約", style={'margin': '5px 0 0 0'}),
                    html.Small("可能な限り遵守", style={'color': '#666'})
                ], style={'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#fff3e0', 'borderRadius': '8px'}),
                
                html.Div([
                    html.H4(f"{len(machine_readable.get('preferences', []))}", style={'margin': '0', 'color': '#388e3c'}),
                    html.P("推奨設定", style={'margin': '5px 0 0 0'}),
                    html.Small("最適化ヒント", style={'color': '#666'})
                ], style={'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#e8f5e8', 'borderRadius': '8px'})
            ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(3, 1fr)', 'gap': '15px'})
        ], style={'marginBottom': '30px', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '8px'}),
        
        # エクスポートボタン
        html.Div([
            html.H4("💾 データエクスポート"),
            html.Div([
                html.Button(
                    "🤖 AI実行用制約データ (JSON)",
                    id="export-constraints-btn",
                    n_clicks=0,
                    style={
                        'padding': '12px 24px', 'backgroundColor': '#4caf50', 'color': 'white',
                        'border': 'none', 'borderRadius': '6px', 'marginRight': '15px', 'cursor': 'pointer'
                    }
                ),
                html.Button(
                    "📋 人間確認用レポート (JSON)",
                    id="export-report-btn",
                    n_clicks=0,
                    style={
                        'padding': '12px 24px', 'backgroundColor': '#ff9800', 'color': 'white',
                        'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer'
                    }
                )
            ])
        ], style={'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '8px'}),
        
        # 未知コード警告（あれば）
        html.Div([
            html.H5("⚠️ 未知の勤務コード", style={'color': '#f57c00'}),
            html.P(f"以下のコードが勤務区分シートに定義されていません: {', '.join(sorted(unknown_codes))}")
        ], style={'marginTop': '20px', 'padding': '15px', 'backgroundColor': '#fff3e0', 'borderRadius': '8px'}) if unknown_codes else html.Div()
    ])


@app.callback(
    Output('download-constraints', 'data'),
    Input('export-constraints-btn', 'n_clicks'),
    State('mece-results-store', 'data'),
    prevent_initial_call=True
)
def export_constraints(n_clicks, mece_results):
    """AI実行用制約データをエクスポート"""
    if not n_clicks or not mece_results:
        raise PreventUpdate
    
    machine_readable = mece_results.get('machine_readable', {})
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"facility_constraints_{timestamp}.json"
    
    return dict(
        content=json.dumps(machine_readable, ensure_ascii=False, indent=2),
        filename=filename,
        type="application/json"
    )


@app.callback(
    Output('download-report', 'data'),
    Input('export-report-btn', 'n_clicks'),
    State('mece-results-store', 'data'),
    prevent_initial_call=True
)
def export_report(n_clicks, mece_results):
    """人間確認用レポートをエクスポート"""
    if not n_clicks or not mece_results:
        raise PreventUpdate
    
    human_readable = mece_results.get('human_readable', {})
    machine_readable = mece_results.get('machine_readable', {})
    extraction_metadata = mece_results.get('extraction_metadata', {})
    
    report_data = {
        "report_metadata": {
            "generated_at": datetime.now().isoformat(),
            "report_type": "MECE施設ルール事実抽出レポート",
            "application": "MECE事実抽出専用アプリ",
            "data_period": extraction_metadata.get("data_period", {}),
            "data_quality": extraction_metadata.get("data_quality", {})
        },
        "summary": human_readable.get('抽出事実サマリー', {}),
        "confidence_classification": human_readable.get('確信度別分類', {}),
        "detailed_facts": human_readable.get('MECE分解事実', {}),
        "constraints_preview": {
            "hard_constraints_count": len(machine_readable.get("hard_constraints", [])),
            "soft_constraints_count": len(machine_readable.get("soft_constraints", [])),
            "preferences_count": len(machine_readable.get("preferences", []))
        }
    }
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"facility_facts_report_{timestamp}.json"
    
    return dict(
        content=json.dumps(report_data, ensure_ascii=False, indent=2),
        filename=filename,
        type="application/json"
    )


if __name__ == '__main__':
    print("🚀 MECE事実抽出専用アプリを起動中...")
    print("📱 ブラウザで http://localhost:8051 にアクセスしてください")
    print("📋 軸1(施設ルール)のMECE事実抽出が利用可能です")
    print("💡 Ctrl+C で終了")
    
    app.run_server(
        debug=True,
        host='0.0.0.0',
        port=8051,
        dev_tools_hot_reload=True
    )