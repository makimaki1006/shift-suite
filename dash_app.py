# dash_app.py (高速分析ビューア) - 機能完全再現版
import base64
import io
import zipfile
import logging
import re

import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- ロガー設定 (デバッグ用にレベルをDEBUGに変更) ---
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# --- Dashアプリケーションの初期化 ---
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = "Shift-Suite 高速分析ビューア"

# --- UI文言の管理 ---
TEXT = {
    "title": "Shift-Suite 高速分析ビューア",
    "upload_label": "分析結果のZIPファイルをここにドラッグ＆ドロップ、または ",
    "upload_link": "ファイルを選択",
    "error_zip_processing": "ZIPファイルの処理中にエラーが発生しました。ファイルが破損しているか、形式が正しくない可能性があります。",
    "waiting_for_upload": "分析結果のZIPファイルをアップロードして、ダッシュボードを表示してください。",
    "data_not_found": "この分析データはZIPファイルに含まれていませんでした。",
    "graph_error": "このグラフの作成中にエラーが発生しました。データの形式を確認してください。",
    "overview": "概要",
    "heatmap": "ヒートマップ",
    "shortage": "不足分析",
    "optimization": "最適化分析",
    "fatigue": "疲労分析",
    "fairness": "公平性分析",
    "leave": "休暇分析",
    "cost": "コスト分析",
    "hire_plan": "採用計画",
    "alerts": "アラート",
    "heatmap_unit": "表示単位",
    "heatmap_target": "表示対象",
    "unit_all": "全体",
    "unit_role": "職種別",
    "unit_employment": "雇用形態別",
}

# --- ヘルパー関数 ---
def create_styled_div(message, level='info'):
    """レベルに応じたスタイルでメッセージDivを作成する"""
    styles = {
        'info': {'border': '1px solid #bee5eb', 'background': '#d1ecf1', 'color': '#0c5460'},
        'warning': {'border': '1px solid #ffeeba', 'background': '#fff3cd', 'color': '#856404'},
        'error': {'border': '1px solid #f5c6cb', 'background': '#f8d7da', 'color': '#721c24'}
    }
    style = styles.get(level, 'info')
    style.update({'padding': '15px', 'margin': '10px 0', 'borderRadius': '5px'})
    return html.Div(message, style=style)

def decode_data(data_json, file_key):
    if data_json and file_key in data_json:
        try:
            log.debug(f"Decoding data for {file_key}...")
            df = pd.read_json(io.StringIO(data_json[file_key]), orient='split')
            log.debug(f"Successfully decoded {file_key}, shape: {df.shape}")
            return df
        except Exception as e:
            log.warning(f"Failed to decode {file_key}: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def sanitize_dataframe(df, id_vars=None):
    """DataFrameをサニタイズする。インデックスを列に変換し、可読性を高める。"""
    if df.empty:
        return df
    df_sanitized = df.copy().reset_index()
    if 'index' in df_sanitized.columns and id_vars and id_vars not in df.columns:
        df_sanitized = df_sanitized.rename(columns={'index': id_vars})
    return df_sanitized

def render_plot(title, plot_function, data_json, required_files, plot_args={}):
    """グラフ描画を試み、失敗した場合はエラーDivを返す汎用ラッパー"""
    try:
        for f in required_files:
            if f not in data_json: return create_styled_div(f"「{f}」 - {TEXT['data_not_found']}", 'warning')
        log.debug(f"Rendering plot: {title}")
        content = plot_function(data_json, **plot_args)
        return html.Div([
            html.H4(title, style={'marginBottom': '10px', 'borderBottom': '2px solid #dee2e6', 'paddingBottom': '5px'}),
            content
        ], style={'padding': '15px', 'border': '1px solid #ddd', 'borderRadius': '5px', 'marginBottom': '20px', 'backgroundColor': 'white'})
    except Exception as e:
        log.error(f"Failed to render plot '{title}': {e}", exc_info=True)
        return create_styled_div(f"グラフ「{title}」の描画に失敗しました: {e}", 'error')

# --- 各種UIコンポーネント生成 ---
def create_alerts_div(data_json):
    alerts = []
    # 疲労アラート
    df_fatigue = decode_data(data_json, 'fatigue_score.parquet')
    if not df_fatigue.empty:
        df_fatigue_sane = sanitize_dataframe(df_fatigue, 'staff')
        if 'fatigue_score' in df_fatigue_sane.columns:
            high_fatigue_staff = df_fatigue_sane[df_fatigue_sane['fatigue_score'] >= 0.8]
            if not high_fatigue_staff.empty:
                staff_list = ", ".join(high_fatigue_staff['staff'])
                alerts.append(create_styled_div(f"疲労スコアが高いスタッフがいます: {staff_list}", 'warning'))
    if not alerts:
        return None
    return html.Div([html.H3(TEXT["alerts"])] + alerts, style={'marginBottom': '20px'})

def create_overview_tab(data_json):
    return render_plot("分析概要", lambda data: dash_table.DataTable(
        data=sanitize_dataframe(decode_data(data, 'summary.csv')).to_dict('records'),
        columns=[{'name': i, 'id': i} for i in sanitize_dataframe(decode_data(data, 'summary.csv')).columns],
        style_table={'overflowX': 'auto'}, style_cell={'textAlign': 'left'},
        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
    ), data_json, ['summary.csv'])

def create_heatmap_tab(data_json):
    df_heat = decode_data(data_json, 'heat_ALL.parquet')
    if df_heat.empty: return create_styled_div(TEXT['data_not_found'], 'warning')
    
    # 絞り込み対象の列が存在するか確認
    has_role = 'role' in df_heat.columns
    has_employment = 'employment_type' in df_heat.columns
    
    options = [{'label': TEXT['unit_all'], 'value': 'all'}]
    if has_role:
        options.append({'label': TEXT['unit_role'], 'value': 'role'})
    if has_employment:
        options.append({'label': TEXT['unit_employment'], 'value': 'employment'})
        
    return html.Div([
        html.H3(TEXT["heatmap"]),
        html.Div([
            html.Div([
                html.Label(TEXT["heatmap_unit"]),
                dcc.Dropdown(id='heatmap-unit-dropdown', options=options, value='all'),
            ], style={'width': '48%', 'display': 'inline-block'}),
            html.Div([
                html.Label(TEXT["heatmap_target"]),
                dcc.Dropdown(id='heatmap-target-dropdown'),
            ], style={'width': '48%', 'display': 'inline-block', 'marginLeft': '4%'}),
        ], style={'marginBottom': '20px'}),
        dcc.Loading(id="loading-heatmap", type="circle", children=html.Div(id='heatmap-container')),
    ], style={'padding': '15px', 'border': '1px solid #ddd', 'borderRadius': '5px', 'backgroundColor': 'white'})

def create_shortage_tab(data_json):
    plots = [html.H3(TEXT["shortage"])]
    plots.append(render_plot("時間帯別不足人数ヒートマップ", lambda d: dcc.Graph(figure=px.imshow(decode_data(d, 'shortage_time.parquet'), text_auto=True, aspect="auto")), data_json, ['shortage_time.parquet']))
    plots.append(render_plot("役割別合計不足時間", lambda d: dcc.Graph(figure=px.bar(sanitize_dataframe(decode_data(d, 'shortage_role_summary.parquet'), 'role'), x='role', y='shortage_hours')), data_json, ['shortage_role_summary.parquet']))
    plots.append(render_plot("雇用形態別合計不足時間", lambda d: dcc.Graph(figure=px.bar(sanitize_dataframe(decode_data(d, 'shortage_employment_summary.parquet'), 'employment_type'), x='employment_type', y='shortage_hours')), data_json, ['shortage_employment_summary.parquet']))
    return html.Div(plots)

def create_fatigue_tab(data_json):
    return render_plot("疲労スコア", lambda data: html.Div([
        dcc.Graph(figure=px.bar(sanitize_dataframe(decode_data(data, 'fatigue_score.parquet'), 'staff'), x="staff", y="fatigue_score", title="スタッフ別疲労スコア")),
        dcc.Graph(figure=px.histogram(sanitize_dataframe(decode_data(data, 'fatigue_score.parquet'), 'staff'), x="fatigue_score", title="疲労スコア分布"))
    ]), data_json, ['fatigue_score.parquet'])

def create_leave_tab(data_json):
    plots = [html.H3(TEXT["leave"])]
    
    def plot_leave_bar(data):
        df = sanitize_dataframe(decode_data(data, 'leave_analysis.csv'), 'date')
        if not all(col in df.columns for col in ['date', 'actual', 'leave_count']):
            return create_styled_div("leave_analysis.csvに必要な列がありません。", "error")
        fig = go.Figure(data=[
            go.Bar(name='出勤者数', x=df['date'], y=df['actual']),
            go.Bar(name='休暇者数', x=df['date'], y=df['leave_count'])
        ]).update_layout(barmode='stack')
        return dcc.Graph(figure=fig)
    plots.append(render_plot("日別出勤・休暇者数", plot_leave_bar, data_json, ['leave_analysis.csv']))
    
    def plot_leave_pie(data):
        df = sanitize_dataframe(decode_data(data, 'leave_ratio_breakdown.csv'))
        if not all(col in df.columns for col in ['reason', 'count']):
             return create_styled_div("leave_ratio_breakdown.csvに必要な列がありません。", "error")
        return dcc.Graph(figure=px.pie(df, names='reason', values='count'))
    plots.append(render_plot("休暇取得理由 内訳", plot_leave_pie, data_json, ['leave_ratio_breakdown.csv']))
    
    return html.Div(plots)

def create_fairness_tab(data_json):
    df = decode_data(data_json, 'fairness_after.parquet')
    if df.empty: return create_file_not_found_div('fairness_after.parquet')
    df = sanitize_dataframe(df)
    if 'metric' not in df.columns: return create_styled_div("公平性分析データに 'metric' 列が見つかりません。", 'error')
    metrics = df['metric'].unique()
    return html.Div([
        html.H3(TEXT["fairness"]),
        dcc.Dropdown(id='fairness-metric-dropdown', options=[{'label': m, 'value': m} for m in metrics], value=metrics[0] if len(metrics) > 0 else None),
        dcc.Graph(id='fairness-graph')
    ], style={'padding': '15px', 'border': '1px solid #ddd', 'borderRadius': '5px', 'backgroundColor': 'white'})

def create_optimization_tab(data_json):
    plots = [html.H3(TEXT["optimization"])]
    plots.append(render_plot("時間帯別最適化スコア", lambda d: dcc.Graph(figure=px.imshow(decode_data(d, 'optimization_score_time.parquet'), text_auto=".1f", aspect="auto")), data_json, ['optimization_score_time.parquet']))
    plots.append(render_plot("必要人数に対する過剰人員時間", lambda d: dcc.Graph(figure=px.imshow(decode_data(d, 'surplus_vs_need_time.parquet'), text_auto=".1f", aspect="auto")), data_json, ['surplus_vs_need_time.parquet']))
    return html.Div(plots)

def create_cost_tab(data_json):
    return render_plot("日別コスト", lambda d: dcc.Graph(figure=px.bar(sanitize_dataframe(decode_data(d, 'daily_cost_summary.parquet'), 'date'), x='date', y='cost')), data_json, ['daily_cost_summary.parquet'])

def create_hire_plan_tab(data_json):
    return render_plot("採用計画", lambda data: dash_table.DataTable(
        data=sanitize_dataframe(decode_data(data, 'hire_plan.parquet')).to_dict('records'),
        columns=[{'name': i, 'id': i} for i in sanitize_dataframe(decode_data(data, 'hire_plan.parquet')).columns],
        page_size=10, style_table={'overflowX': 'auto'}
    ), data_json, ['hire_plan.parquet'])

# --- アプリケーションのメインレイアウト ---
app.layout = html.Div(style={'backgroundColor': '#f0f2f5'}, children=[
    dcc.Store(id='analysis-data-store', storage_type='session'),
    html.Div([html.H1(TEXT["title"], style={'color': 'white'})], style={'backgroundColor': '#2c3e50', 'padding': '20px', 'textAlign': 'center'}),
    html.Div(style={'padding': '20px'}, children=[
        dcc.Upload(
            id='upload-zip',
            children=html.Div([TEXT["upload_label"], html.A(TEXT["upload_link"])]),
            style={'width': '100%', 'height': '100px', 'lineHeight': '100px', 'borderWidth': '2px', 'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center', 'marginBottom': '20px', 'backgroundColor': '#fff'},
            multiple=False
        ),
        html.Div(id='alert-container'),
        dcc.Loading(id="loading-main", type="cube", fullscreen=False, children=html.Div(id='dashboard-container'))
    ])
])

# --- コールバック関数 ---
@app.callback(Output('analysis-data-store', 'data'), Input('upload-zip', 'contents'))
def parse_zip_and_store_data(contents):
    if contents is None: raise PreventUpdate
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    dataframes = {}
    try:
        with zipfile.ZipFile(io.BytesIO(decoded), 'r') as zf:
            for file_info in zf.infolist():
                if file_info.is_dir(): continue
                fname = file_info.filename.replace('\\', '/')
                with zf.open(fname) as f:
                    log.debug(f"Reading {fname} from zip...")
                    if fname.endswith('.parquet'):
                        dataframes[fname] = pd.read_parquet(f)
                    elif fname.endswith('.csv'):
                        dataframes[fname] = pd.read_csv(f)
        json_data = {name: df.to_json(date_format='iso', orient='split') for name, df in dataframes.items()}
        log.info(f"Successfully processed zip file with {len(json_data)} files.")
        return json_data
    except Exception as e:
        log.error(f"ZIP processing error: {e}", exc_info=True)
        return None

@app.callback(Output('dashboard-container', 'children'), Output('alert-container', 'children'), Input('analysis-data-store', 'data'))
def render_dashboard_and_alerts(data_json):
    if data_json is None:
        return html.Div(TEXT["waiting_for_upload"], style={'textAlign': 'center', 'padding': '50px', 'fontSize': '1.2em'}), None

    tab_map = {
        "overview": {"label": TEXT["overview"], "file": "summary.csv", "func": create_overview_tab},
        "heatmap": {"label": TEXT["heatmap"], "file": "heat_ALL.parquet", "func": create_heatmap_tab},
        "shortage": {"label": TEXT["shortage"], "file": "shortage_time.parquet", "func": create_shortage_tab},
        "optimization": {"label": TEXT["optimization"], "file": "optimization_score_time.parquet", "func": create_optimization_tab},
        "fatigue": {"label": TEXT["fatigue"], "file": "fatigue_score.parquet", "func": create_fatigue_tab},
        "fairness": {"label": TEXT["fairness"], "file": "fairness_after.parquet", "func": create_fairness_tab},
        "leave": {"label": TEXT["leave"], "file": "leave_analysis.csv", "func": create_leave_tab},
        "cost": {"label": TEXT["cost"], "file": "daily_cost_summary.parquet", "func": create_cost_tab},
        "hire_plan": {"label": TEXT["hire_plan"], "file": "hire_plan.parquet", "func": create_hire_plan_tab},
    }
    
    tabs = [dcc.Tab(label=val["label"], children=[val["func"](data_json)], value=key) for key, val in tab_map.items() if val["file"] in data_json]
    dashboard = dcc.Tabs(id="main-tabs", children=tabs, style={'fontFamily': 'sans-serif'}) if tabs else create_styled_div("表示可能な分析データがZIPファイルに含まれていません。", "warning")
    alerts = create_alerts_div(data_json)
    return dashboard, alerts

@app.callback(Output('heatmap-target-dropdown', 'options'), Output('heatmap-target-dropdown', 'style'), Input('heatmap-unit-dropdown', 'value'), State('analysis-data-store', 'data'))
def update_heatmap_target_dropdown(unit, data_json):
    if not unit or unit == 'all':
        return [], {'display': 'none'}
    if data_json is None:
        raise PreventUpdate
        
    df = decode_data(data_json, 'heat_ALL.parquet')
    if df.empty:
        return [], {'display': 'none'}

    col_map = {'role': 'role', 'employment': 'employment_type'}
    target_col = col_map.get(unit)

    if target_col and target_col in df.columns:
        options = [{'label': i, 'value': i} for i in df[target_col].unique()]
        return options, {'width': '48%', 'display': 'inline-block', 'marginLeft': '4%'}
    return [], {'display': 'none'}

@app.callback(Output('heatmap-container', 'children'), Input('heatmap-unit-dropdown', 'value'), Input('heatmap-target-dropdown', 'value'), State('analysis-data-store', 'data'))
def update_heatmap(unit, target, data_json):
    if not unit or data_json is None:
        raise PreventUpdate

    title = "ヒートマップ"
    df_all = decode_data(data_json, 'heat_ALL.parquet')
    if df_all.empty:
        return create_styled_div("ヒートマップデータ(heat_ALL.parquet)が見つかりません。", 'warning')
        
    df_filtered = df_all.copy()
    if unit == 'role' and target:
        if 'role' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['role'] == target]
            title += f" (職種: {target})"
    elif unit == 'employment' and target:
        if 'employment_type' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['employment_type'] == target]
            title += f" (雇用形態: {target})"

    try:
        heatmap_df = df_filtered.pivot_table(index='time', columns='date', values='is_work', aggfunc='sum')
        fig = px.imshow(heatmap_df, text_auto=False, aspect="auto", title=title)
        return dcc.Graph(figure=fig)
    except Exception as e:
        log.error(f"Error creating heatmap: {e}", exc_info=True)
        return create_styled_div(f"ヒートマップの作成中にエラーが発生しました: {e}", 'error')

@app.callback(Output('fairness-graph', 'figure'), Input('fairness-metric-dropdown', 'value'), State('analysis-data-store', 'data'))
def update_fairness_graph(selected_metric, data_json):
    if not selected_metric or not data_json: raise PreventUpdate
    try:
        df = sanitize_dataframe(decode_data(data_json, 'fairness_after.parquet'), 'staff')
        if not all(col in df.columns for col in ['metric', 'staff', 'value']):
            return go.Figure().update_layout(title_text="公平性データに必要な列が見つかりません。")
        dff = df[df['metric'] == selected_metric]
        fig = px.bar(dff, x='staff', y='value', title=f'公平性指標: {selected_metric}')
        return fig
    except Exception as e:
        log.error(f"Error in update_fairness_graph: {e}", exc_info=True)
        return go.Figure().update_layout(title_text=TEXT["graph_error"])

# --- アプリケーションの実行 ---
if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
