# dash_app.py - Shift-Suite高速分析ビューア (app.py機能完全再現版)
import base64
import io
import json
import logging
import tempfile
import zipfile
from pathlib import Path
from typing import List, Tuple
import unicodedata

import dash
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table, dcc, html
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate

# ロガー設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
log = logging.getLogger(__name__)

# Dashアプリケーション初期化
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = "Shift-Suite 高速分析ビューア"

# グローバル変数
DATA_STORE = {}
TEMP_DIR = None

# --- ユーティリティ関数 ---
def safe_filename(name: str) -> str:
    """Normalize and sanitize strings for file keys"""
    name = unicodedata.normalize("NFKC", name)
    for ch in ["/", "\\", ":", "*", "?", "\"", "<", ">", "|", "・", "／", "＼"]:
        name = name.replace(ch, "_")
    return name

def date_with_weekday(date_str: str) -> str:
    """日付文字列に曜日を追加"""
    try:
        date = pd.to_datetime(date_str)
        weekdays = ['月', '火', '水', '木', '金', '土', '日']
        return f"{date.strftime('%m/%d')}({weekdays[date.weekday()]})"
    except Exception:
        return str(date_str)


def safe_read_parquet(filepath: Path) -> pd.DataFrame:
    """Parquetファイルを安全に読み込む"""
    try:
        return pd.read_parquet(filepath)
    except Exception as e:
        log.warning(f"Failed to read {filepath}: {e}")
        return pd.DataFrame()


def safe_read_csv(filepath: Path) -> pd.DataFrame:
    """CSVファイルを安全に読み込む"""
    try:
        return pd.read_csv(filepath)
    except Exception as e:
        log.warning(f"Failed to read {filepath}: {e}")
        return pd.DataFrame()


def calc_ratio_from_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    """ヒートマップデータから不足率を計算"""
    if df.empty or "need" not in df.columns:
        return pd.DataFrame()

    date_cols = [c for c in df.columns if pd.to_datetime(c, errors='coerce') is not pd.NaT]
    if not date_cols:
        return pd.DataFrame()

    need_series = df["need"].fillna(0)
    need_df = pd.DataFrame(
        np.repeat(need_series.values[:, np.newaxis], len(date_cols), axis=1),
        index=need_series.index,
        columns=date_cols
    )
    staff_df = df[date_cols].fillna(0)
    ratio_df = ((need_df - staff_df) / need_df.replace(0, np.nan)).clip(lower=0).fillna(0)
    return ratio_df


def load_shortage_meta(data_dir: Path) -> Tuple[List[str], List[str]]:
    """職種と雇用形態のリストを読み込む"""
    roles = []
    employments = []
    meta_fp = data_dir / "shortage.meta.json"
    if meta_fp.exists():
        try:
            with open(meta_fp, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            roles = meta.get("roles", [])
            employments = meta.get("employments", [])
        except Exception as e:
            log.debug(f"Failed to load shortage meta: {e}")
    return roles, employments

# --- UIコンポーネント生成関数 ---
def create_metric_card(label: str, value: str, color: str = "#1f77b4") -> html.Div:
    """メトリクスカードを作成"""
    return html.Div([
        html.Div(label, style={
            'fontSize': '14px',
            'color': '#666',
            'marginBottom': '5px'
        }),
        html.Div(value, style={
            'fontSize': '24px',
            'fontWeight': 'bold',
            'color': color
        })
    ], style={
        'padding': '15px',
        'backgroundColor': 'white',
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'textAlign': 'center',
        'minHeight': '80px'
    })


def create_overview_tab() -> html.Div:
    """概要タブを作成"""
    df_shortage_role = DATA_STORE.get('shortage_role_summary', pd.DataFrame())
    df_fairness = DATA_STORE.get('fairness_before', pd.DataFrame())
    df_staff = DATA_STORE.get('staff_stats', pd.DataFrame())
    df_alerts = DATA_STORE.get('stats_alerts', pd.DataFrame())

    # メトリクス計算
    lack_h = df_shortage_role['lack_h'].sum() if 'lack_h' in df_shortage_role.columns else 0
    excess_cost = df_shortage_role['estimated_excess_cost'].sum() if 'estimated_excess_cost' in df_shortage_role.columns else 0
    lack_temp_cost = df_shortage_role['estimated_lack_cost_if_temporary_staff'].sum() if 'estimated_lack_cost_if_temporary_staff' in df_shortage_role.columns else 0
    lack_penalty_cost = df_shortage_role['estimated_lack_penalty_cost'].sum() if 'estimated_lack_penalty_cost' in df_shortage_role.columns else 0

    jain_index = "N/A"
    if not df_fairness.empty and 'metric' in df_fairness.columns:
        jain_row = df_fairness[df_fairness['metric'] == 'jain_index']
        if not jain_row.empty:
            jain_index = f"{float(jain_row['value'].iloc[0]):.3f}"

    staff_count = len(df_staff) if not df_staff.empty else 0
    avg_night_ratio = df_staff['night_ratio'].mean() if 'night_ratio' in df_staff.columns else 0
    alerts_count = len(df_alerts) if not df_alerts.empty else 0

    return html.Div([
        html.H3("分析概要", style={'marginBottom': '20px'}),
        html.Div([
            html.Div([
                create_metric_card("総不足時間(h)", f"{lack_h:.1f}"),
            ], style={'width': '12.5%', 'display': 'inline-block', 'padding': '5px'}),
            html.Div([
                create_metric_card("夜勤 Jain指数", jain_index),
            ], style={'width': '12.5%', 'display': 'inline-block', 'padding': '5px'}),
            html.Div([
                create_metric_card("総スタッフ数", str(staff_count)),
            ], style={'width': '12.5%', 'display': 'inline-block', 'padding': '5px'}),
            html.Div([
                create_metric_card("平均夜勤比率", f"{avg_night_ratio:.3f}"),
            ], style={'width': '12.5%', 'display': 'inline-block', 'padding': '5px'}),
            html.Div([
                create_metric_card("アラート数", str(alerts_count), "#ff7f0e" if alerts_count > 0 else "#1f77b4"),
            ], style={'width': '12.5%', 'display': 'inline-block', 'padding': '5px'}),
            html.Div([
                create_metric_card("総過剰コスト(¥)", f"{excess_cost:,.0f}"),
            ], style={'width': '12.5%', 'display': 'inline-block', 'padding': '5px'}),
            html.Div([
                create_metric_card("不足コスト(派遣)(¥)", f"{lack_temp_cost:,.0f}"),
            ], style={'width': '12.5%', 'display': 'inline-block', 'padding': '5px'}),
            html.Div([
                create_metric_card("不足ペナルティ(¥)", f"{lack_penalty_cost:,.0f}"),
            ], style={'width': '12.5%', 'display': 'inline-block', 'padding': '5px'}),
        ], style={'marginBottom': '20px'}),
    ])


def create_heatmap_tab() -> html.Div:
    """ヒートマップタブを作成"""
    roles = DATA_STORE.get('roles', [])
    employments = DATA_STORE.get('employments', [])

    scope_options = [{'label': '全体', 'value': 'overall'}]
    if roles:
        scope_options.append({'label': '職種別', 'value': 'role'})
    if employments:
        scope_options.append({'label': '雇用形態別', 'value': 'employment'})

    return html.Div([
        html.H3("ヒートマップ", style={'marginBottom': '20px'}),
        html.Div([
            html.Div([
                html.Label("表示範囲"),
                dcc.Dropdown(
                    id='heatmap-scope',
                    options=scope_options,
                    value='overall',
                    clearable=False
                ),
            ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '2%'}),
            html.Div([
                html.Label("詳細選択"),
                dcc.Dropdown(
                    id='heatmap-detail',
                    options=[],
                    value=None
                ),
            ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '2%'}),
            html.Div([
                html.Label("表示モード"),
                dcc.RadioItems(
                    id='heatmap-mode',
                    options=[
                        {'label': '実数', 'value': 'Raw'},
                        {'label': '充足率', 'value': 'Ratio'}
                    ],
                    value='Raw',
                    inline=True
                ),
            ], style={'width': '36%', 'display': 'inline-block'}),
        ], style={'marginBottom': '20px'}),
        dcc.Loading(
            id="loading-heatmap",
            type="default",
            children=html.Div(id='heatmap-content')
        ),
    ])


def create_shortage_tab() -> html.Div:
    """不足分析タブを作成"""
    df_shortage_role = DATA_STORE.get('shortage_role_summary', pd.DataFrame())
    df_shortage_emp = DATA_STORE.get('shortage_employment_summary', pd.DataFrame())

    content = [html.H3("不足分析", style={'marginBottom': '20px'})]

    # 職種別不足分析
    if not df_shortage_role.empty:
        content.append(html.H4("職種別不足時間"))

        # サマリーメトリクス
        total_lack = df_shortage_role['lack_h'].sum() if 'lack_h' in df_shortage_role.columns else 0
        if total_lack > 0:
            top_roles = df_shortage_role.nlargest(3, 'lack_h')[['role', 'lack_h']]
            metrics = [
                html.Div([
                    create_metric_card("総不足時間", f"{total_lack:.1f}h")
                ], style={'width': '25%', 'display': 'inline-block', 'padding': '5px'})
            ]
            for i, row in enumerate(top_roles.itertuples(index=False)):
                metrics.append(
                    html.Div([
                        create_metric_card(f"不足Top{i+1}", f"{row.role}: {row.lack_h:.1f}h")
                    ], style={'width': '25%', 'display': 'inline-block', 'padding': '5px'})
                )
            content.append(html.Div(metrics, style={'marginBottom': '20px'}))

        # 職種別不足時間グラフ
        fig_role_lack = px.bar(
            df_shortage_role,
            x='role',
            y='lack_h',
            title='職種別不足時間',
            labels={'role': '職種', 'lack_h': '不足時間(h)'},
            color_discrete_sequence=['#FFA500']
        )
        content.append(dcc.Graph(figure=fig_role_lack))

        # 職種別過剰時間グラフ
        if 'excess_h' in df_shortage_role.columns:
            fig_role_excess = px.bar(
                df_shortage_role,
                x='role',
                y='excess_h',
                title='職種別過剰時間',
                labels={'role': '職種', 'excess_h': '過剰時間(h)'},
                color_discrete_sequence=['#00BFFF']
            )
            content.append(dcc.Graph(figure=fig_role_excess))

    # 雇用形態別不足分析
    if not df_shortage_emp.empty:
        content.append(html.H4("雇用形態別不足時間", style={'marginTop': '30px'}))

        fig_emp_lack = px.bar(
            df_shortage_emp,
            x='employment',
            y='lack_h',
            title='雇用形態別不足時間',
            labels={'employment': '雇用形態', 'lack_h': '不足時間(h)'},
            color_discrete_sequence=['#2ca02c']
        )
        content.append(dcc.Graph(figure=fig_emp_lack))

    # 不足率ヒートマップセクション
    content.append(html.Div([
        html.H4("不足率ヒートマップ", style={'marginTop': '30px'}),
        html.P("各時間帯で必要人数に対してどれくらいの割合で人員が不足していたかを示します。"),
        html.Div([
            html.Label("表示範囲"),
            dcc.Dropdown(
                id='shortage-heatmap-scope',
                options=[
                    {'label': '全体', 'value': 'overall'},
                    {'label': '職種別', 'value': 'role'},
                    {'label': '雇用形態別', 'value': 'employment'}
                ],
                value='overall',
                style={'width': '200px'}
            ),
        ], style={'marginBottom': '10px'}),
        html.Div(id='shortage-heatmap-detail-container'),
        html.Div(id='shortage-ratio-heatmap')
    ]))

    return html.Div(content)


def create_optimization_tab() -> html.Div:
    """最適化分析タブを作成"""
    return html.Div([
        html.H3("最適化分析", style={'marginBottom': '20px'}),
        html.Div([
            html.Label("表示範囲"),
            dcc.Dropdown(
                id='opt-scope',
                options=[
                    {'label': '全体', 'value': 'overall'},
                    {'label': '職種別', 'value': 'role'},
                    {'label': '雇用形態別', 'value': 'employment'}
                ],
                value='overall',
                clearable=False
            ),
        ], style={'width': '30%', 'marginBottom': '20px'}),
        html.Div(id='opt-detail-container'),
        html.Div(id='optimization-content')
    ])


def create_leave_analysis_tab() -> html.Div:
    """休暇分析タブを作成"""
    content = [html.H3("休暇分析", style={'marginBottom': '20px'})]

    # 基本的な休暇分析データ
    df_leave = DATA_STORE.get('leave_analysis', pd.DataFrame())
    df_staff_balance = DATA_STORE.get('staff_balance_daily', pd.DataFrame())

    if not df_leave.empty:
        # 勤務予定人数と休暇取得者数の推移
        if not df_staff_balance.empty:
            fig_balance = px.line(
                df_staff_balance,
                x='date',
                y=['total_staff', 'leave_applicants_count', 'non_leave_staff'],
                title='スタッフバランスの推移',
                labels={
                    'value': '人数',
                    'variable': '項目',
                    'date': '日付'
                },
                markers=True
            )
            content.append(dcc.Graph(figure=fig_balance))

    # 休暇タイプ別の分析
    if 'leave_type' in df_leave.columns:
        # 日別休暇取得者数（内訳）
        fig_breakdown = px.bar(
            df_leave,
            x='date',
            y='total_leave_days',
            color='leave_type',
            title='日別 休暇取得者数（内訳）',
            labels={
                'date': '日付',
                'total_leave_days': '休暇取得者数',
                'leave_type': '休暇タイプ'
            },
            barmode='stack'
        )
        content.append(dcc.Graph(figure=fig_breakdown))

    # 休暇集中分析
    df_concentration = DATA_STORE.get('concentration_requested', pd.DataFrame())
    if not df_concentration.empty:
        content.append(html.H4("休暇集中日分析", style={'marginTop': '30px'}))
        content.append(html.P("閾値を超える休暇申請があった日を赤いダイヤモンドで表示します。"))

        fig_conc = go.Figure()

        # 基本の線グラフ
        fig_conc.add_trace(go.Scatter(
            x=df_concentration['date'],
            y=df_concentration['leave_applicants_count'],
            mode='lines+markers',
            name='休暇申請者数',
            line=dict(shape='spline', smoothing=0.5),
            marker=dict(size=6)
        ))

        # 集中日のマーカー
        if 'is_concentrated' in df_concentration.columns:
            concentrated = df_concentration[df_concentration['is_concentrated']]
            if not concentrated.empty:
                fig_conc.add_trace(go.Scatter(
                    x=concentrated['date'],
                    y=concentrated['leave_applicants_count'],
                    mode='markers',
                    marker=dict(color='red', size=12, symbol='diamond'),
                    name='閾値超過日',
                    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>申請者数: %{y}人<extra></extra>'
                ))

        fig_conc.update_layout(
            title='希望休 申請者数の推移と集中日',
            xaxis_title='日付',
            yaxis_title='申請者数'
        )

        content.append(dcc.Graph(figure=fig_conc))

    return html.Div(content)


def create_cost_analysis_tab() -> html.Div:
    """コスト分析タブを作成"""
    content = [html.H3("人件費分析", style={'marginBottom': '20px'})]

    df_cost = DATA_STORE.get('daily_cost', pd.DataFrame())
    if not df_cost.empty:
        # 日別コストグラフ
        fig_daily = px.bar(
            df_cost,
            x='date',
            y='cost',
            title='日別発生人件費',
            labels={'date': '日付', 'cost': 'コスト(円)'}
        )

        # カスタムホバーテンプレートを追加
        if all(col in df_cost.columns for col in ['day_of_week', 'total_staff', 'role_breakdown']):
            fig_daily.update_traces(
                customdata=df_cost[['day_of_week', 'total_staff', 'role_breakdown']],
                hovertemplate='<b>%{x|%Y-%m-%d} (%{customdata[0]})</b><br><br>' +
                             'コスト: %{y:,.0f}円<br>' +
                             '構成人数: %{customdata[1]}人<br>' +
                             '職種一覧: %{customdata[2]}<extra></extra>'
            )

        content.append(dcc.Graph(figure=fig_daily))

        # 累計コストグラフ
        if 'cost' in df_cost.columns:
            df_cost_sorted = df_cost.sort_values('date').copy()
            df_cost_sorted['cumulative_cost'] = df_cost_sorted['cost'].cumsum()

            fig_cumulative = px.line(
                df_cost_sorted,
                x='date',
                y='cumulative_cost',
                title='日別累計人件費',
                labels={'date': '日付', 'cumulative_cost': '累計人件費(円)'},
                markers=True
            )
            content.append(dcc.Graph(figure=fig_cumulative))

    return html.Div(content)


def create_hire_plan_tab() -> html.Div:
    """採用計画タブを作成"""
    content = [html.H3("採用計画", style={'marginBottom': '20px'})]

    df_hire = DATA_STORE.get('hire_plan', pd.DataFrame())
    if not df_hire.empty:
        content.append(html.H4("必要FTE（職種別）"))

        # テーブル表示
        content.append(dash_table.DataTable(
            data=df_hire.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in df_hire.columns],
            style_cell={'textAlign': 'left'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
        ))

        # グラフ表示
        if 'role' in df_hire.columns and 'hire_fte' in df_hire.columns:
            fig_hire = px.bar(
                df_hire,
                x='role',
                y='hire_fte',
                title='職種別必要FTE',
                labels={'role': '職種', 'hire_fte': '必要FTE'},
                color_discrete_sequence=['#1f77b4']
            )
            content.append(dcc.Graph(figure=fig_hire))

    # 最適採用計画
    df_optimal = DATA_STORE.get('optimal_hire_plan', pd.DataFrame())
    if not df_optimal.empty:
        content.append(html.H4("最適採用計画", style={'marginTop': '30px'}))
        content.append(html.P("分析の結果、以下の具体的な採用計画を推奨します。"))
        content.append(dash_table.DataTable(
            data=df_optimal.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in df_optimal.columns],
            style_cell={'textAlign': 'left'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
        ))

    return html.Div(content)

# --- メインレイアウト ---
app.layout = html.Div([
    dcc.Store(id='data-loaded', storage_type='memory'),

    # ヘッダー
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

    # アップロードエリア
    html.Div([
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                '分析結果のZIPファイルをドラッグ＆ドロップ または ',
                html.A('クリックして選択', style={'textDecoration': 'underline'})
            ]),
            style={
                'width': '100%',
                'height': '100px',
                'lineHeight': '100px',
                'borderWidth': '2px',
                'borderStyle': 'dashed',
                'borderRadius': '10px',
                'textAlign': 'center',
                'margin': '20px 0',
                'backgroundColor': '#f8f9fa',
                'cursor': 'pointer'
            },
            multiple=False
        ),
    ], style={'padding': '0 20px'}),

    # メインコンテンツ
    html.Div(id='main-content', style={'padding': '20px'}),

], style={'backgroundColor': '#f5f5f5', 'minHeight': '100vh'})

# --- コールバック関数 ---
@app.callback(
    Output('data-loaded', 'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def process_upload(contents, filename):
    """ZIPファイルをアップロード・処理"""
    if contents is None:
        raise PreventUpdate

    global DATA_STORE, TEMP_DIR

    # 一時ディレクトリ作成
    if TEMP_DIR:
        import shutil
        shutil.rmtree(TEMP_DIR, ignore_errors=True)

    TEMP_DIR = Path(tempfile.mkdtemp(prefix="shift_suite_dash_"))

    # ZIPファイルを展開
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        with zipfile.ZipFile(io.BytesIO(decoded)) as zf:
            zf.extractall(TEMP_DIR)

        # データディレクトリを探す
        data_dir = None
        if (TEMP_DIR / 'out').exists():
            data_dir = TEMP_DIR / 'out'
        elif (TEMP_DIR / 'heat_ALL.parquet').exists():
            data_dir = TEMP_DIR
        else:
            # 再帰的に探す
            for p in TEMP_DIR.rglob('heat_ALL.parquet'):
                data_dir = p.parent
                break

        if not data_dir:
            return {'error': 'データファイルが見つかりません'}

        # データを読み込む
        DATA_STORE = {}

        # Parquetファイル
        parquet_files = [
            'heat_ALL.parquet',
            'shortage_role_summary.parquet',
            'shortage_employment_summary.parquet',
            'shortage_time.parquet',
            'shortage_ratio.parquet',
            'shortage_freq.parquet',
            'excess_time.parquet',
            'excess_ratio.parquet',
            'excess_freq.parquet',
            'fatigue_score.parquet',
            'fairness_before.parquet',
            'fairness_after.parquet',
            'staff_stats.parquet',
            'stats_alerts.parquet',
            'hire_plan.parquet',
            'optimal_hire_plan.parquet',
            'daily_cost.parquet',
            'forecast.parquet',
            'cost_benefit.parquet'
        ]

        for file in parquet_files:
            if (data_dir / file).exists():
                df = safe_read_parquet(data_dir / file)
                if not df.empty:
                    DATA_STORE[file.replace('.parquet', '')] = df

        # CSVファイル
        csv_files = [
            'leave_analysis.csv',
            'demand_series.csv'
        ]

        for file in csv_files:
            if (data_dir / file).exists():
                df = safe_read_csv(data_dir / file)
                if not df.empty:
                    DATA_STORE[file.replace('.csv', '')] = df

        # 動的ヒートマップファイル
        for p in data_dir.glob('heat_role_*.parquet'):
            df = safe_read_parquet(p)
            if not df.empty:
                DATA_STORE[safe_filename(p.stem)] = df

        for p in data_dir.glob('heat_emp_*.parquet'):
            df = safe_read_parquet(p)
            if not df.empty:
                DATA_STORE[safe_filename(p.stem)] = df

        # メタデータ読み込み
        roles, employments = load_shortage_meta(data_dir)
        DATA_STORE['roles'] = roles
        DATA_STORE['employments'] = employments

        log.info(f"Loaded {len(DATA_STORE)} data files")
        return {'success': True, 'files': len(DATA_STORE)}

    except Exception as e:
        log.error(f"Error processing ZIP: {e}", exc_info=True)
        return {'error': str(e)}


@app.callback(
    Output('main-content', 'children'),
    Input('data-loaded', 'data')
)
def update_main_content(data_status):
    """メインコンテンツを更新"""
    if not data_status:
        return html.Div([
            html.P("分析結果のZIPファイルをアップロードしてください。",
                  style={'textAlign': 'center', 'fontSize': '18px', 'color': '#666'})
        ])

    if 'error' in data_status:
        return html.Div([
            html.P(f"エラー: {data_status['error']}",
                  style={'color': 'red', 'textAlign': 'center'})
        ])

    # タブを作成
    tabs = dcc.Tabs(id='main-tabs', value='overview', children=[
        dcc.Tab(label='概要', value='overview'),
        dcc.Tab(label='ヒートマップ', value='heatmap'),
        dcc.Tab(label='不足分析', value='shortage'),
        dcc.Tab(label='最適化分析', value='optimization'),
        dcc.Tab(label='休暇分析', value='leave'),
        dcc.Tab(label='コスト分析', value='cost'),
        dcc.Tab(label='採用計画', value='hire_plan'),
    ])

    return html.Div([
        tabs,
        html.Div(id='tab-content', style={'marginTop': '20px'})
    ])


@app.callback(
    Output('tab-content', 'children'),
    Input('main-tabs', 'value')
)
def update_tab_content(active_tab):
    """タブコンテンツを更新"""
    if active_tab == 'overview':
        return create_overview_tab()
    elif active_tab == 'heatmap':
        return create_heatmap_tab()
    elif active_tab == 'shortage':
        return create_shortage_tab()
    elif active_tab == 'optimization':
        return create_optimization_tab()
    elif active_tab == 'leave':
        return create_leave_analysis_tab()
    elif active_tab == 'cost':
        return create_cost_analysis_tab()
    elif active_tab == 'hire_plan':
        return create_hire_plan_tab()
    else:
        return html.Div("タブが選択されていません")


@app.callback(
    Output('heatmap-detail', 'options'),
    Output('heatmap-detail', 'style'),
    Input('heatmap-scope', 'value')
)
def update_heatmap_detail_options(scope):
    """ヒートマップの詳細選択オプションを更新"""
    if scope == 'overall':
        return [], {'display': 'none'}
    if scope == 'role':
        roles = DATA_STORE.get('roles', [])
        return [{'label': r, 'value': r} for r in roles], {'display': 'block'}
    if scope == 'employment':
        employments = DATA_STORE.get('employments', [])
        return [{'label': e, 'value': e} for e in employments], {'display': 'block'}
    return [], {'display': 'none'}


@app.callback(
    Output('heatmap-content', 'children'),
    Input('heatmap-scope', 'value'),
    Input('heatmap-detail', 'value'),
    Input('heatmap-mode', 'value')
)
def update_heatmap_content(scope, detail, mode):
    """ヒートマップコンテンツを更新"""
    # データキーを決定
    if scope == 'overall':
        heat_key = 'heat_ALL'
    elif scope == 'role' and detail:
        heat_key = f'heat_role_{safe_filename(detail)}'
    elif scope == 'employment' and detail:
        heat_key = f'heat_emp_{safe_filename(detail)}'
    else:
        return html.Div("データを選択してください")

    df_heat = DATA_STORE.get(heat_key)
    if df_heat is None:
        for key in DATA_STORE.keys():
            if key.startswith('heat_role_') and detail in key:
                df_heat = DATA_STORE[key]
                break
            if key.startswith('heat_emp_') and detail in key:
                df_heat = DATA_STORE[key]
                break
    if df_heat is None or df_heat.empty:
        return html.Div(f"データが見つかりません: {detail}")

    # モードに応じて処理
    if mode == 'Ratio':
        # 不足率を計算
        display_df = calc_ratio_from_heatmap(df_heat)
        title = f"充足率ヒートマップ - {scope}"
        color_scale = 'RdBu_r'
    else:
        # 生データから必要な列だけ抽出
        date_cols = [c for c in df_heat.columns if pd.to_datetime(c, errors='coerce') is not pd.NaT]
        display_df = df_heat[date_cols] if date_cols else pd.DataFrame()
        title = f"人員配置ヒートマップ - {scope}"
        color_scale = 'Blues'

    if detail:
        title += f" ({detail})"

    if display_df.empty:
        return html.Div("表示可能なデータがありません")

    # ヒートマップ作成
    fig = px.imshow(
        display_df,
        aspect='auto',
        color_continuous_scale=color_scale,
        title=title,
        labels={'x': '日付', 'y': '時間', 'color': mode}
    )

    # X軸ラベルに曜日を追加
    fig.update_xaxes(
        ticktext=[date_with_weekday(c) for c in display_df.columns],
        tickvals=list(range(len(display_df.columns)))
    )

    return dcc.Graph(figure=fig)


@app.callback(
    Output('shortage-heatmap-detail-container', 'children'),
    Input('shortage-heatmap-scope', 'value')
)
def update_shortage_heatmap_detail(scope):
    """不足率ヒートマップの詳細選択を更新"""
    if scope == 'overall':
        return None
    elif scope == 'role':
        roles = DATA_STORE.get('roles', [])
        return html.Div([
            html.Label("職種選択"),
            dcc.Dropdown(
                id={'type': 'shortage-detail', 'index': 'role'},
                options=[{'label': r, 'value': r} for r in roles],
                value=roles[0] if roles else None,
                style={'width': '200px'}
            )
        ], style={'marginBottom': '10px'})
    elif scope == 'employment':
        employments = DATA_STORE.get('employments', [])
        return html.Div([
            html.Label("雇用形態選択"),
            dcc.Dropdown(
                id={'type': 'shortage-detail', 'index': 'employment'},
                options=[{'label': e, 'value': e} for e in employments],
                value=employments[0] if employments else None,
                style={'width': '200px'}
            )
        ], style={'marginBottom': '10px'})
    return None


@app.callback(
    Output('shortage-ratio-heatmap', 'children'),
    Input('shortage-heatmap-scope', 'value'),
    Input({'type': 'shortage-detail', 'index': ALL}, 'value')
)
def update_shortage_ratio_heatmap(scope, detail_values):
    """不足率ヒートマップを更新"""
    # データキーを決定
    if scope == 'overall':
        heat_key = 'heat_ALL'
    else:
        detail = detail_values[0] if detail_values else None
        if not detail:
            return html.Div("詳細を選択してください")
        if scope == 'role':
            heat_key = f'heat_role_{safe_filename(detail)}'
        else:
            heat_key = f'heat_emp_{safe_filename(detail)}'

    df_heat = DATA_STORE.get(heat_key)
    if df_heat is None:
        for key in DATA_STORE.keys():
            if key.startswith('heat_role_') and detail in key:
                df_heat = DATA_STORE[key]
                break
            if key.startswith('heat_emp_') and detail in key:
                df_heat = DATA_STORE[key]
                break
    if df_heat is None or df_heat.empty:
        return html.Div("データが見つかりません")

    # 不足率を計算
    ratio_df = calc_ratio_from_heatmap(df_heat)
    if ratio_df.empty:
        return html.Div("不足率の計算ができません")

    # タイトル設定
    title = "不足率ヒートマップ"
    if scope != 'overall' and detail_values:
        title += f" - {detail_values[0]}"

    # ヒートマップ作成
    fig = px.imshow(
        ratio_df,
        aspect='auto',
        color_continuous_scale='RdBu_r',
        title=title,
        labels={'x': '日付', 'y': '時間', 'color': '不足率'}
    )

    # X軸ラベルに曜日を追加
    fig.update_xaxes(
        ticktext=[date_with_weekday(c) for c in ratio_df.columns],
        tickvals=list(range(len(ratio_df.columns)))
    )

    return dcc.Graph(figure=fig)


@app.callback(
    Output('opt-detail-container', 'children'),
    Input('opt-scope', 'value')
)
def update_opt_detail(scope):
    """最適化分析の詳細選択を更新"""
    if scope == 'overall':
        return None
    elif scope == 'role':
        roles = DATA_STORE.get('roles', [])
        return html.Div([
            html.Label("職種選択"),
            dcc.Dropdown(
                id={'type': 'opt-detail', 'index': 'role'},
                options=[{'label': r, 'value': r} for r in roles],
                value=roles[0] if roles else None,
                style={'width': '300px', 'marginBottom': '20px'}
            )
        ])
    elif scope == 'employment':
        employments = DATA_STORE.get('employments', [])
        return html.Div([
            html.Label("雇用形態選択"),
            dcc.Dropdown(
                id={'type': 'opt-detail', 'index': 'employment'},
                options=[{'label': e, 'value': e} for e in employments],
                value=employments[0] if employments else None,
                style={'width': '300px', 'marginBottom': '20px'}
            )
        ])
    return None


@app.callback(
    Output('optimization-content', 'children'),
    Input('opt-scope', 'value'),
    Input({'type': 'opt-detail', 'index': ALL}, 'value')
)
def update_optimization_content(scope, detail_values):
    """最適化分析コンテンツを更新"""
    # データキーを決定
    if scope == 'overall':
        heat_key = 'heat_ALL'
    else:
        detail = detail_values[0] if detail_values else None
        if not detail:
            return html.Div("詳細を選択してください")
        if scope == 'role':
            heat_key = f'heat_role_{safe_filename(detail)}'
        else:
            heat_key = f'heat_emp_{safe_filename(detail)}'

    df_heat = DATA_STORE.get(heat_key)
    if df_heat is None:
        for key in DATA_STORE.keys():
            if key.startswith('heat_role_') and detail in key:
                df_heat = DATA_STORE[key]
                break
            if key.startswith('heat_emp_') and detail in key:
                df_heat = DATA_STORE[key]
                break
    if df_heat is None or df_heat.empty:
        return html.Div("データが見つかりません")

    # 日付列を抽出
    date_cols = [c for c in df_heat.columns if pd.to_datetime(c, errors='coerce') is not pd.NaT]
    if not date_cols:
        return html.Div("日付データが見つかりません")

    # 必要なデータを計算
    staff_df = df_heat[date_cols].fillna(0)
    need_series = df_heat.get('need', pd.Series()).fillna(0)
    upper_series = df_heat.get('upper', pd.Series()).fillna(0)

    # DataFrameに変換
    need_df = pd.DataFrame(
        np.repeat(need_series.values[:, np.newaxis], len(date_cols), axis=1),
        index=df_heat.index,
        columns=date_cols
    )
    upper_df = pd.DataFrame(
        np.repeat(upper_series.values[:, np.newaxis], len(date_cols), axis=1),
        index=df_heat.index,
        columns=date_cols
    )

    # 各指標を計算
    surplus_df = (staff_df - need_df).clip(lower=0)
    margin_df = (upper_df - staff_df).clip(lower=0)

    # スコア計算（不足と過剰のペナルティ）
    lack_ratio = ((need_df - staff_df) / need_df.replace(0, np.nan)).clip(lower=0).fillna(0)
    excess_ratio = ((staff_df - upper_df) / upper_df.replace(0, np.nan)).clip(lower=0).fillna(0)
    score_df = 1 - (0.6 * lack_ratio + 0.4 * excess_ratio)
    score_df = score_df.clip(lower=0, upper=1)

    content = []

    # 1. 必要人数に対する余剰
    content.append(html.Div([
        html.H4("1. 必要人数に対する余剰 (Surplus vs Need)"),
        html.P("各時間帯で必要人数（need）に対して何人多くスタッフがいたかを示します。"),
        dcc.Graph(figure=px.imshow(
            surplus_df,
            aspect='auto',
            color_continuous_scale='Blues',
            title='必要人数に対する余剰人員ヒートマップ',
            labels={'x': '日付', 'y': '時間', 'color': '余剰人数'}
        ).update_xaxes(
            ticktext=[date_with_weekday(c) for c in surplus_df.columns],
            tickvals=list(range(len(surplus_df.columns)))
        ))
    ]))

    # 2. 上限に対する余白
    content.append(html.Div([
        html.H4("2. 上限に対する余白 (Margin to Upper)", style={'marginTop': '30px'}),
        html.P("各時間帯で配置人数の上限（upper）まであと何人の余裕があったかを示します。"),
        dcc.Graph(figure=px.imshow(
            margin_df,
            aspect='auto',
            color_continuous_scale='Greens',
            title='上限人数までの余白ヒートマップ',
            labels={'x': '日付', 'y': '時間', 'color': '余白人数'}
        ).update_xaxes(
            ticktext=[date_with_weekday(c) for c in margin_df.columns],
            tickvals=list(range(len(margin_df.columns)))
        ))
    ]))

    # 3. 最適化スコア
    content.append(html.Div([
        html.H4("3. 人員配置 最適化スコア", style={'marginTop': '30px'}),
        html.P("人員配置の効率性を0から1のスコアで示します（1が最も良い）。"),
        dcc.Graph(figure=px.imshow(
            score_df,
            aspect='auto',
            color_continuous_scale='RdYlGn',
            zmin=0,
            zmax=1,
            title='最適化スコア ヒートマップ',
            labels={'x': '日付', 'y': '時間', 'color': 'スコア'}
        ).update_xaxes(
            ticktext=[date_with_weekday(c) for c in score_df.columns],
            tickvals=list(range(len(score_df.columns)))
        ))
    ]))

    return html.Div(content)

# --- アプリケーション起動 ---
if __name__ == '__main__':
    app.run_server(debug=True, port=8050, host='127.0.0.1')
