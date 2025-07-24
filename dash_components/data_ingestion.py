# data_ingestion.py - データ入稿フロー専用モジュール
"""
データアップロードから前処理までのワークフローを管理
ユーザーフレンドリーな入稿体験を提供
"""

import base64
import io
import logging
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import dash
from dash import dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate

# ログ設定
log = logging.getLogger(__name__)

class DataIngestionFlow:
    """データ入稿フローの統合管理クラス"""
    
    def __init__(self):
        self.supported_formats = {'.zip', '.xlsx', '.csv'}
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.validation_rules = {}
        
    def create_upload_ui(self) -> html.Div:
        """ユーザーフレンドリーなアップロードUIを作成"""
        return html.Div([
            # アップロード説明
            html.Div([
                html.H4("📁 データファイルをアップロード", 
                       style={'color': '#2c3e50', 'marginBottom': '10px'}),
                html.P([
                    "サポート形式: ",
                    html.Code(".zip, .xlsx, .csv", 
                             style={'backgroundColor': '#f8f9fa', 'padding': '2px 5px'})
                ], style={'marginBottom': '15px', 'color': '#555'}),
            ]),
            
            # アップロードエリア
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    html.Div([
                        html.I(className="fas fa-cloud-upload-alt", 
                              style={'fontSize': '48px', 'color': '#3498db', 'marginBottom': '10px'}),
                        html.H5("ファイルをドラッグ&ドロップ", 
                               style={'margin': '0', 'color': '#2c3e50'}),
                        html.P("または クリックしてファイルを選択", 
                              style={'margin': '5px 0 0 0', 'color': '#7f8c8d'})
                    ], style={'textAlign': 'center', 'padding': '20px'})
                ]),
                style={
                    'width': '100%',
                    'height': '120px',
                    'lineHeight': '120px',
                    'borderWidth': '2px',
                    'borderStyle': 'dashed',
                    'borderColor': '#3498db',
                    'borderRadius': '8px',
                    'backgroundColor': '#f8f9ff',
                    'textAlign': 'center',
                    'margin': '10px 0',
                    'cursor': 'pointer',
                    'transition': 'all 0.3s ease'
                },
                multiple=False
            ),
            
            # 進捗表示エリア
            html.Div(id='upload-progress', style={'marginTop': '20px'}),
            
            # 検証結果表示エリア
            html.Div(id='validation-results', style={'marginTop': '15px'}),
            
            # データプレビューエリア
            html.Div(id='data-preview', style={'marginTop': '20px'})
        ], style={'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'})
    
    def validate_file(self, contents: str, filename: str) -> Dict[str, Any]:
        """包括的なファイル検証を実行"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'file_info': {},
            'recommendations': []
        }
        
        try:
            # ファイルサイズ検証
            file_size = len(base64.b64decode(contents.split(',')[1]))
            validation_result['file_info']['size_mb'] = round(file_size / (1024 * 1024), 2)
            
            if file_size > self.max_file_size:
                validation_result['valid'] = False
                validation_result['errors'].append(
                    f"ファイルサイズが上限（{self.max_file_size/(1024*1024):.0f}MB）を超えています"
                )
            
            # ファイル形式検証
            file_ext = Path(filename).suffix.lower()
            validation_result['file_info']['extension'] = file_ext
            
            if file_ext not in self.supported_formats:
                validation_result['valid'] = False
                validation_result['errors'].append(
                    f"未サポートの形式です。サポート形式: {', '.join(self.supported_formats)}"
                )
            
            # MIMEタイプ検証（簡易版）
            mime_prefix = contents.split(',')[0]
            validation_result['file_info']['mime_type'] = mime_prefix
            
            # ファイル内容の基本検証
            if file_ext == '.zip':
                self._validate_zip_contents(contents, validation_result)
            elif file_ext in {'.xlsx', '.csv'}:
                self._validate_excel_csv_contents(contents, validation_result)
                
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"ファイル検証中にエラーが発生しました: {str(e)}")
            log.error(f"File validation error: {e}", exc_info=True)
        
        return validation_result
    
    def _validate_zip_contents(self, contents: str, validation_result: Dict):
        """ZIPファイルの内容検証"""
        try:
            decoded = base64.b64decode(contents.split(',')[1])
            with zipfile.ZipFile(io.BytesIO(decoded), 'r') as zip_file:
                file_list = zip_file.namelist()
                validation_result['file_info']['zip_contents'] = file_list
                
                # 必要なファイルの存在確認
                required_patterns = ['*.xlsx', '*.csv']
                has_data_files = any(
                    any(f.endswith(ext[1:]) for ext in ['.xlsx', '.csv']) 
                    for f in file_list
                )
                
                if not has_data_files:
                    validation_result['warnings'].append(
                        "ZIPファイル内にExcelまたはCSVファイルが見つかりません"
                    )
                
                # ファイル数チェック
                if len(file_list) > 50:
                    validation_result['warnings'].append(
                        f"ファイル数が多すぎます（{len(file_list)}個）。処理に時間がかかる可能性があります"
                    )
                    
        except zipfile.BadZipFile:
            validation_result['valid'] = False
            validation_result['errors'].append("破損したZIPファイルです")
        except Exception as e:
            validation_result['warnings'].append(f"ZIP内容の詳細検証に失敗: {str(e)}")
    
    def _validate_excel_csv_contents(self, contents: str, validation_result: Dict):
        """Excel/CSVファイルの内容検証"""
        try:
            decoded = base64.b64decode(contents.split(',')[1])
            
            # DataFrameとして読み込み試行
            if validation_result['file_info']['extension'] == '.xlsx':
                df = pd.read_excel(io.BytesIO(decoded))
            else:  # CSV
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            
            # データ品質チェック
            validation_result['file_info']['rows'] = len(df)
            validation_result['file_info']['columns'] = len(df.columns)
            validation_result['file_info']['empty_cells'] = df.isnull().sum().sum()
            
            # 推奨事項の生成
            if len(df) == 0:
                validation_result['valid'] = False
                validation_result['errors'].append("空のファイルです")
            elif len(df) < 10:
                validation_result['warnings'].append("データ行数が少ないです（10行未満）")
            
            if validation_result['file_info']['empty_cells'] > len(df) * len(df.columns) * 0.5:
                validation_result['warnings'].append("空白セルの割合が高いです（50%以上）")
                
        except Exception as e:
            validation_result['warnings'].append(f"ファイル内容の詳細検証に失敗: {str(e)}")
    
    def create_progress_display(self, stage: str, progress: int) -> html.Div:
        """処理進捗の可視化"""
        stages = {
            'upload': {'name': 'アップロード', 'icon': '📁'},
            'validate': {'name': 'ファイル検証', 'icon': '✅'},
            'process': {'name': 'データ前処理', 'icon': '🔄'},
            'analyze': {'name': '分析処理', 'icon': '📊'},
            'complete': {'name': '完了', 'icon': '🎉'}
        }
        
        return html.Div([
            html.H5(f"{stages[stage]['icon']} {stages[stage]['name']}", 
                   style={'marginBottom': '10px'}),
            dcc.Graph(
                figure={
                    'data': [{
                        'x': [progress],
                        'y': ['進捗'],
                        'type': 'bar',
                        'orientation': 'h',
                        'marker': {'color': '#3498db'},
                        'text': [f'{progress}%'],
                        'textposition': 'inside'
                    }],
                    'layout': {
                        'xaxis': {'range': [0, 100], 'showticklabels': False},
                        'yaxis': {'showticklabels': False},
                        'height': 80,
                        'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0},
                        'showlegend': False
                    }
                },
                config={'displayModeBar': False},
                style={'height': '80px'}
            )
        ], style={'marginBottom': '15px'})
    
    def create_validation_results_display(self, validation_result: Dict) -> html.Div:
        """検証結果の表示"""
        if not validation_result:
            return html.Div()
        
        components = []
        
        # ファイル情報表示
        if 'file_info' in validation_result:
            info = validation_result['file_info']
            components.append(
                html.Div([
                    html.H6("📋 ファイル情報", style={'color': '#2c3e50'}),
                    html.Ul([
                        html.Li(f"サイズ: {info.get('size_mb', 'N/A')} MB"),
                        html.Li(f"形式: {info.get('extension', 'N/A')}"),
                        html.Li(f"行数: {info.get('rows', 'N/A')}") if 'rows' in info else None,
                        html.Li(f"列数: {info.get('columns', 'N/A')}") if 'columns' in info else None,
                    ])
                ], style={'marginBottom': '15px'})
            )
        
        # エラー表示
        if validation_result.get('errors'):
            components.append(
                html.Div([
                    html.H6("❌ エラー", style={'color': '#e74c3c'}),
                    html.Ul([
                        html.Li(error, style={'color': '#e74c3c'}) 
                        for error in validation_result['errors']
                    ])
                ], style={'marginBottom': '15px'})
            )
        
        # 警告表示
        if validation_result.get('warnings'):
            components.append(
                html.Div([
                    html.H6("⚠️ 注意事項", style={'color': '#f39c12'}),
                    html.Ul([
                        html.Li(warning, style={'color': '#f39c12'}) 
                        for warning in validation_result['warnings']
                    ])
                ], style={'marginBottom': '15px'})
            )
        
        # 成功表示
        if validation_result.get('valid') and not validation_result.get('errors'):
            components.append(
                html.Div([
                    html.H6("✅ 検証完了", style={'color': '#27ae60'}),
                    html.P("ファイルは正常です。処理を続行できます。", style={'color': '#27ae60'})
                ], style={'marginBottom': '15px'})
            )
        
        return html.Div(components) if components else html.Div()
    
    def create_data_preview(self, df: pd.DataFrame) -> html.Div:
        """データプレビューの表示"""
        if df is None or df.empty:
            return html.Div()
        
        # 最初の5行のプレビュー
        preview_df = df.head(5)
        
        return html.Div([
            html.H6("👀 データプレビュー", style={'color': '#2c3e50', 'marginBottom': '10px'}),
            html.Div([
                html.P(f"総行数: {len(df):,} 行、列数: {len(df.columns)} 列", 
                      style={'marginBottom': '10px', 'color': '#555'}),
                dash.dash_table.DataTable(
                    data=preview_df.to_dict('records'),
                    columns=[{'name': i, 'id': i} for i in preview_df.columns],
                    style_cell={'textAlign': 'left', 'fontSize': '12px', 'padding': '8px'},
                    style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                    style_data={'backgroundColor': 'white'},
                    page_size=5
                )
            ], style={
                'border': '1px solid #dee2e6',
                'borderRadius': '4px',
                'padding': '15px',
                'backgroundColor': '#f8f9fa'
            })
        ])

# グローバルインスタンス
data_ingestion = DataIngestionFlow()