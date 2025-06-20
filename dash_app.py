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
from shift_suite.tasks.utils import safe_read_excel, gen_labels
from shift_suite.tasks.shortage_factor_analyzer import ShortageFactorAnalyzer
from shift_suite.tasks import over_shortage_log

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


def load_and_sum_heatmaps(data_dir: Path, keys: List[str]) -> pd.DataFrame:
    """Load multiple heatmap files and aggregate them."""
    dfs = []
    for key in keys:
        df = DATA_STORE.get(key)
        if df is None and data_dir:
            fp = Path(data_dir) / f"{key}.parquet"
            if fp.exists():
                df = safe_read_parquet(fp)
                if not df.empty:
                    DATA_STORE[key] = df
        if isinstance(df, pd.DataFrame) and not df.empty:
            dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    total = dfs[0].copy()
    for df in dfs[1:]:
        total = total.add(df, fill_value=0)

    if {"need", "staff"}.issubset(total.columns):
        total["lack"] = (total["need"] - total["staff"]).clip(lower=0)
    if {"staff", "upper"}.issubset(total.columns):
        total["excess"] = (total["staff"] - total["upper"]).clip(lower=0)

    return total


def generate_heatmap_figure(df_heat: pd.DataFrame, title: str) -> go.Figure:
    """指定されたデータフレームからヒートマップグラフを生成する"""
    if df_heat is None or df_heat.empty:
        return go.Figure().update_layout(title_text=f"{title}: データなし", height=300)

    date_cols = [c for c in df_heat.columns if pd.to_datetime(c, errors='coerce') is not pd.NaT]
    if not date_cols:
        return go.Figure().update_layout(title_text=f"{title}: 表示可能な日付データなし", height=300)

    display_df = df_heat[date_cols]
    time_labels = gen_labels(30)
    display_df = display_df.reindex(time_labels, fill_value=0)

    fig = px.imshow(
        display_df,
        aspect='auto',
        color_continuous_scale=px.colors.sequential.Viridis,
        title=title,
        labels={'x': '日付', 'y': '時間', 'color': '人数'}
    )
    fig.update_xaxes(
        ticktext=[date_with_weekday(c) for c in display_df.columns],
        tickvals=list(range(len(display_df.columns)))
    )
    return fig

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
        html.Div(id='overview-insights', style={
            'padding': '15px',
            'backgroundColor': '#e9f2fa',
            'borderRadius': '8px',
            'marginBottom': '20px',
            'border': '1px solid #cce5ff'
        }),
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
    """ヒートマップタブのレイアウトを生成します。上下2つの比較エリアを持ちます。"""
    roles = DATA_STORE.get('roles', [])
    employments = DATA_STORE.get('employments', [])

    # 比較エリアを1つ生成するヘルパー関数
    def create_comparison_area(area_id: int):
        return html.Div([
            html.H4(f"比較エリア {area_id}", style={'marginTop': '20px', 'borderTop': '2px solid #ddd', 'paddingTop': '20px'}),

            # --- 各エリアに職種と雇用形態の両方のフィルターを設置 ---
            html.Div([
                html.Div([
                    html.Label("職種フィルター"),
                    dcc.Dropdown(
                        id={'type': 'heatmap-filter-role', 'index': area_id},
                        options=[{'label': 'すべて', 'value': 'all'}] + [{'label': r, 'value': r} for r in roles],
                        value='all',
                        clearable=False
                    )
                ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),

                html.Div([
                    html.Label("雇用形態フィルター"),
                    dcc.Dropdown(
                        id={'type': 'heatmap-filter-employment', 'index': area_id},
                        options=[{'label': 'すべて', 'value': 'all'}] + [{'label': e, 'value': e} for e in employments],
                        value='all',
                        clearable=False
                    )
                ], style={'width': '48%', 'display': 'inline-block'}),
            ], style={'marginBottom': '10px'}),

            # --- グラフ描画領域 ---
            dcc.Loading(
                id={'type': 'loading-heatmap', 'index': area_id},
                children=html.Div(id={'type': 'graph-output-heatmap', 'index': area_id})
            )
        ], style={'padding': '10px', 'backgroundColor': '#f9f9f9', 'borderRadius': '5px', 'marginBottom': '10px'})

    return html.Div([
        html.H3("ヒートマップ比較分析", style={'marginBottom': '20px'}),
        html.P("上下のエリアでそれぞれ「職種」と「雇用形態」の組み合わせを選択し、ヒートマップを比較してください。"),
        create_comparison_area(1),
        create_comparison_area(2)
    ])


def create_shortage_tab() -> html.Div:
    """不足分析タブを作成"""
    df_shortage_role = DATA_STORE.get('shortage_role_summary', pd.DataFrame())
    df_shortage_emp = DATA_STORE.get('shortage_employment_summary', pd.DataFrame())

    content = [html.Div(id='shortage-insights', style={
        'padding': '15px',
        'backgroundColor': '#e9f2fa',
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("不足分析", style={'marginBottom': '20px'}),
        html.Div(
            dcc.Markdown(
                "\n".join(
                    [
                        "### 計算に使用したパラメータ",
                        f"- Need算出方法: {DATA_STORE.get('need_method', 'N/A')}",
                        f"- Upper算出方法: {DATA_STORE.get('upper_method', 'N/A')}",
                        f"- 直接雇用単価: ¥{DATA_STORE.get('wage_direct', 0):,.0f}/h",
                        f"- 派遣単価: ¥{DATA_STORE.get('wage_temp', 0):,.0f}/h",
                        f"- 採用コスト: ¥{DATA_STORE.get('hiring_cost', 0):,}/人",
                        f"- 不足ペナルティ: ¥{DATA_STORE.get('penalty_cost', 0):,.0f}/h",
                    ]
                )
            ),
            style={
                'backgroundColor': '#e9f2fa',
                'padding': '10px',
                'borderRadius': '8px',
                'border': '1px solid #cce5ff',
                'marginBottom': '20px'
            },
        )]

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

    # Factor Analysis section
    content.append(html.Hr())
    content.append(html.H4('Factor Analysis (AI)', style={'marginTop': '30px'}))
    content.append(html.Button('Train factor model', id='factor-train-button', n_clicks=0))
    content.append(html.Div(id='factor-output'))

    # Over/Short Log section
    events_df = DATA_STORE.get('shortage_events', pd.DataFrame())
    if not events_df.empty:
        content.append(html.Hr())
        content.append(html.H4('Over/Short Log', style={'marginTop': '30px'}))
        content.append(dash_table.DataTable(
            id='over-shortage-table',
            data=events_df.to_dict('records'),
            columns=[{'name': c, 'id': c, 'presentation': 'input'} for c in events_df.columns],
            editable=True,
        ))
        content.append(dcc.RadioItems(
            id='log-save-mode',
            options=[{'label': 'Append', 'value': 'append'}, {'label': 'Overwrite', 'value': 'overwrite'}],
            value='append',
            inline=True,
            style={'marginTop': '10px'}
        ))
        content.append(html.Button('Save log', id='save-log-button', n_clicks=0, style={'marginTop': '10px'}))
        content.append(html.Div(id='save-log-msg'))

    return html.Div(content)


def create_optimization_tab() -> html.Div:
    """最適化分析タブを作成"""
    return html.Div([
        html.Div(id='optimization-insights', style={
            'padding': '15px',
            'backgroundColor': '#e9f2fa',
            'borderRadius': '8px',
            'marginBottom': '20px',
            'border': '1px solid #cce5ff'
        }),
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
    content = [html.Div(id='leave-insights', style={
        'padding': '15px',
        'backgroundColor': '#e9f2fa',
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("休暇分析", style={'marginBottom': '20px'})]

    df_staff_balance = DATA_STORE.get('staff_balance_daily', pd.DataFrame())
    df_daily_summary = DATA_STORE.get('daily_summary', pd.DataFrame())
    df_concentration = DATA_STORE.get('concentration_requested', pd.DataFrame())
    df_ratio_breakdown = DATA_STORE.get('leave_ratio_breakdown', pd.DataFrame())

    if not df_staff_balance.empty:
        fig_balance = px.line(
            df_staff_balance,
            x='date',
            y=['total_staff', 'leave_applicants_count', 'non_leave_staff'],
            title='勤務予定人数と全休暇取得者数の推移',
            labels={'value': '人数', 'variable': '項目', 'date': '日付'},
            markers=True
        )
        fig_balance.update_xaxes(tickformat="%m/%d(%a)")
        content.append(dcc.Graph(figure=fig_balance))
        content.append(dash_table.DataTable(
            data=df_staff_balance.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df_staff_balance.columns]
        ))

    if not df_daily_summary.empty:
        fig_breakdown = px.bar(
            df_daily_summary,
            x='date',
            y='total_leave_days',
            color='leave_type',
            barmode='stack',
            title='日別 休暇取得者数（内訳）',
            labels={'date': '日付', 'total_leave_days': '休暇取得者数', 'leave_type': '休暇タイプ'}
        )
        fig_breakdown.update_xaxes(tickformat="%m/%d(%a)")
        content.append(dcc.Graph(figure=fig_breakdown))

    if not df_ratio_breakdown.empty:
        fig_ratio_break = px.bar(
            df_ratio_breakdown,
            x='dayofweek',
            y='leave_ratio',
            color='leave_type',
            facet_col='month_period',
            category_orders={
                'dayofweek': ['月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日', '日曜日'],
                'month_period': ['月初(1-10日)', '月中(11-20日)', '月末(21-末日)'],
            },
            labels={'dayofweek': '曜日', 'leave_ratio': '割合', 'leave_type': '休暇タイプ', 'month_period': '月期間'},
            title='曜日・月期間別休暇取得率'
        )
        content.append(dcc.Graph(figure=fig_ratio_break))

    if not df_concentration.empty:
        fig_conc = go.Figure()
        fig_conc.add_trace(go.Scatter(
            x=df_concentration['date'],
            y=df_concentration['leave_applicants_count'],
            mode='lines+markers',
            name='休暇申請者数',
            line=dict(shape='spline', smoothing=0.5),
            marker=dict(size=6)
        ))
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
        fig_conc.update_xaxes(tickformat="%m/%d(%a)")
        content.append(dcc.Graph(figure=fig_conc))

    return html.Div(content)


def create_cost_analysis_tab() -> html.Div:
    """コスト分析タブを作成"""
    content = [html.Div(id='cost-insights', style={
        'padding': '15px',
        'backgroundColor': '#e9f2fa',
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("人件費分析", style={'marginBottom': '20px'})]

    df_cost = DATA_STORE.get('daily_cost', pd.DataFrame())
    if not df_cost.empty:
        df_cost['date'] = pd.to_datetime(df_cost['date'])
        if not {'day_of_week', 'total_staff', 'role_breakdown', 'staff_list_summary'} <= set(df_cost.columns):
            long_df = DATA_STORE.get('long_df', pd.DataFrame())
            if not long_df.empty and 'ds' in long_df.columns:
                details = (
                    long_df[long_df.get('parsed_slots_count', 1) > 0]
                    .assign(date=lambda x: pd.to_datetime(x['ds']).dt.normalize())
                    .groupby('date')
                    .agg(
                        day_of_week=(
                            'ds',
                            lambda x: ['月', '火', '水', '木', '金', '土', '日'][x.iloc[0].weekday()],
                        ),
                        total_staff=('staff', 'nunique'),
                        role_breakdown=(
                            'role',
                            lambda s: ', '.join(f"{r}:{c}" for r, c in s.value_counts().items()),
                        ),
                        staff_list=('staff', lambda s: ', '.join(sorted(s.unique()))),
                    )
                    .reset_index()
                )

                def summarize(names: str, limit: int = 5) -> str:
                    lst = names.split(', ')
                    if len(lst) > limit:
                        return ', '.join(lst[:limit]) + f", ...他{len(lst) - limit}名"
                    return names

                details['staff_list_summary'] = details['staff_list'].apply(summarize)
                df_cost = pd.merge(df_cost, details, on='date', how='left')
        # 日別コストグラフ
        fig_daily = px.bar(
            df_cost,
            x='date',
            y='cost',
            title='日別発生人件費',
            labels={'date': '日付', 'cost': 'コスト(円)'}
        )
        fig_daily.update_xaxes(tickformat="%m/%d(%a)")

        # カスタムホバーテンプレートを追加
        custom_cols = [c for c in ['day_of_week', 'total_staff', 'role_breakdown', 'staff_list_summary'] if c in df_cost.columns]
        if set(['day_of_week', 'total_staff', 'role_breakdown']).issubset(custom_cols):
            fig_daily.update_traces(
                customdata=df_cost[custom_cols],
                hovertemplate='<b>%{x|%Y-%m-%d} (%{customdata[0]})</b><br><br>' +
                             'コスト: %{y:,.0f}円<br>' +
                             '構成人数: %{customdata[1]}人<br>' +
                             '職種一覧: %{customdata[2]}<br>' +
                             ('スタッフ: %{customdata[3]}' if 'staff_list_summary' in custom_cols else '') +
                             '<extra></extra>'
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
            fig_cumulative.update_xaxes(tickformat="%m/%d(%a)")
            content.append(dcc.Graph(figure=fig_cumulative))

    return html.Div(content)


def create_hire_plan_tab() -> html.Div:
    """採用計画タブを作成"""
    content = [html.Div(id='hire-plan-insights', style={
        'padding': '15px',
        'backgroundColor': '#e9f2fa',
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("採用計画", style={'marginBottom': '20px'})]

    df_hire = DATA_STORE.get('hire_plan', pd.DataFrame())
    df_shortage_role = DATA_STORE.get('shortage_role_summary', pd.DataFrame())
    df_work_patterns = DATA_STORE.get('work_patterns', pd.DataFrame())
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

    if not df_hire.empty and not df_shortage_role.empty:
        content.append(html.Div([
            html.H4("What-if 採用シミュレーション", style={'marginTop': '30px'}),
            html.P("スライダーを動かして、追加採用による不足時間の削減効果とコストの変化を確認できます。"),
            dcc.Dropdown(
                id='sim-work-pattern-dropdown',
                options=[{'label': i, 'value': i} for i in df_work_patterns['code'].unique()] if not df_work_patterns.empty else [],
                value=df_work_patterns['code'].iloc[0] if not df_work_patterns.empty else None,
                clearable=False,
            ),
            dcc.Slider(
                id='sim-hire-fte-slider',
                min=0,
                max=10,
                step=1,
                value=0,
                marks={i: str(i) for i in range(11)},
            ),
        ], style={'padding': '20px', 'backgroundColor': '#f0f0f0', 'borderRadius': '8px'}))
        content.append(dcc.Graph(id='sim-shortage-graph'))
        content.append(html.Div(id='sim-cost-text'))

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


def create_fatigue_tab() -> html.Div:
    """疲労分析タブを作成"""
    explanation = """
    #### 疲労分析の評価方法
    スタッフの疲労スコアは、以下の要素を総合的に評価して算出されます。各要素は、全スタッフ内での相対的な位置（偏差）に基づいてスコア化され、重み付けされて合計されます。
    - **勤務開始時刻のばらつき:** 出勤時刻が不規則であるほどスコアが高くなります。
    - **業務の多様性:** 担当する業務（勤務コード）の種類が多いほどスコアが高くなります。
    - **労働時間のばらつき:** 日々の労働時間が不規則であるほどスコアが高くなります。
    - **短い休息期間:** 勤務間のインターバルが短い頻度が高いほどスコアが高くなります。
    - **連勤:** 3連勤以上の連続勤務が多いほどスコアが高くなります。
    - **夜勤比率:** 全勤務に占める夜勤の割合が高いほどスコアが高くなります。

    *デフォルトでは、これらの要素は均等な重み（各1.0）で評価されます。*
    """
    content = [
        html.Div(
            dcc.Markdown(explanation),
            style={
                'padding': '15px',
                'backgroundColor': '#e9f2fa',
                'borderRadius': '8px',
                'marginBottom': '20px',
                'border': '1px solid #cce5ff',
            },
        ),
        html.H3("疲労分析", style={'marginBottom': '20px'}),
    ]
    df_fatigue = DATA_STORE.get('fatigue_score', pd.DataFrame())

    if not df_fatigue.empty:
        df_fatigue_for_plot = df_fatigue.reset_index().rename(columns={'index': 'staff'})
        fig = px.bar(
            df_fatigue_for_plot,
            x='staff',
            y='fatigue_score',
            title='スタッフ別疲労スコア',
            labels={'staff': 'スタッフ', 'fatigue_score': '疲労スコア'}
        )
        content.append(dcc.Graph(figure=fig))
        content.append(dash_table.DataTable(
            data=df_fatigue_for_plot.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df_fatigue_for_plot.columns]
        ))
    else:
        content.append(html.P("疲労分析データが見つかりません。"))

    return html.Div(content)


def create_forecast_tab() -> html.Div:
    """需要予測タブを作成"""
    content = [html.Div(id='forecast-insights', style={
        'padding': '15px',
        'backgroundColor': '#e9f2fa',
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("需要予測", style={'marginBottom': '20px'})]
    df_fc = DATA_STORE.get('forecast', pd.DataFrame())
    df_actual = DATA_STORE.get('demand_series', pd.DataFrame())

    if not df_fc.empty:
        fig = go.Figure()
        if {'ds', 'yhat'}.issubset(df_fc.columns):
            fig.add_trace(go.Scatter(x=df_fc['ds'], y=df_fc['yhat'], mode='lines+markers', name='予測'))
        if not df_actual.empty and {'ds', 'y'}.issubset(df_actual.columns):
            fig.add_trace(go.Scatter(x=df_actual['ds'], y=df_actual['y'], mode='lines', name='実績', line=dict(dash='dash')))
        fig.update_layout(title='需要予測と実績', xaxis_title='日付', yaxis_title='需要')
        content.append(dcc.Graph(figure=fig))
        content.append(dash_table.DataTable(
            data=df_fc.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df_fc.columns]
        ))
    else:
        content.append(html.P("需要予測データが見つかりません。"))

    return html.Div(content)


def create_fairness_tab() -> html.Div:
    """公平性タブを作成"""
    explanation = """
    #### 公平性分析の評価方法
    スタッフ間の「不公平感」は、各個人の働き方が全体の平均からどれだけ乖離しているかに基づいてスコア化されます。以下の要素の乖離度を均等に評価し、その平均値を「不公平感スコア」としています。
    - **夜勤比率の乖離:** 他のスタッフと比較して、夜勤の割合が極端に多い、または少ない。
    - **総労働時間（スロット数）の乖離:** 他のスタッフと比較して、総労働時間が極端に多い、または少ない。
    - **希望休の承認率の乖離:** 他のスタッフと比較して、希望休の通りやすさに差がある。
    - **連休取得頻度の乖リ:** 他のスタッフと比較して、連休の取得しやすさに差がある。

    *スコアが高いほど、これらの要素において平均からの乖離が大きい（＝不公平感を感じやすい可能性がある）ことを示します。*
    """
    content = [
        html.Div(
            dcc.Markdown(explanation),
            style={
                'padding': '15px',
                'backgroundColor': '#f0f0f0',
                'borderRadius': '8px',
                'marginBottom': '20px',
                'border': '1px solid #ddd',
            },
        ),
        html.H3("公平性 (不公平感スコア)", style={'marginBottom': '20px'}),
    ]
    df_fair = DATA_STORE.get('fairness_after', pd.DataFrame())

    if not df_fair.empty:
        metric_col = (
            'unfairness_score'
            if 'unfairness_score' in df_fair.columns
            else ('fairness_score' if 'fairness_score' in df_fair.columns else 'night_ratio')
        )
        fig_bar = px.bar(
            df_fair,
            x='staff',
            y=metric_col,
            labels={'staff': 'スタッフ', metric_col: 'スコア'},
            color_discrete_sequence=['#FF8C00']
        )
        avg_val = df_fair[metric_col].mean()
        fig_bar.add_hline(y=avg_val, line_dash='dash', line_color='red')
        content.append(dcc.Graph(figure=fig_bar))

        fig_hist = px.histogram(
            df_fair,
            x=metric_col,
            nbins=20,
            title="公平性スコア分布",
            labels={metric_col: 'スコア'}
        )
        fig_hist.update_layout(yaxis_title="人数")
        fig_hist.add_vline(x=avg_val, line_dash='dash', line_color='red')
        content.append(dcc.Graph(figure=fig_hist))

        if 'unfairness_score' in df_fair.columns:
            ranking = df_fair.sort_values('unfairness_score', ascending=False)[['staff', 'unfairness_score']]
            ranking.index += 1
            content.append(html.H4('不公平感ランキング'))
            content.append(dash_table.DataTable(
                data=ranking.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in ranking.columns]
            ))
        content.append(dash_table.DataTable(
            data=df_fair.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df_fair.columns]
        ))
    else:
        content.append(html.P("公平性データが見つかりません。"))

    return html.Div(content)


def create_gap_analysis_tab() -> html.Div:
    """基準乖離分析タブを作成"""
    content = [html.Div(id='gap-insights', style={
        'padding': '15px',
        'backgroundColor': '#e9f2fa',
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("基準乖離分析", style={'marginBottom': '20px'})]
    df_summary = DATA_STORE.get('gap_summary', pd.DataFrame())
    df_heat = DATA_STORE.get('gap_heatmap', pd.DataFrame())

    if not df_summary.empty:
        content.append(dash_table.DataTable(
            data=df_summary.to_dict('records'),
            columns=[{'name': c, 'id': c} for c in df_summary.columns]
        ))
    if not df_heat.empty:
        fig = px.imshow(
            df_heat,
            aspect='auto',
            color_continuous_scale='RdBu_r',
            labels={'x': '時間帯', 'y': '職種', 'color': '乖離'}
        )
        content.append(dcc.Graph(figure=fig))
    if df_summary.empty and df_heat.empty:
        content.append(html.P("基準乖離データが見つかりません。"))

    return html.Div(content)


def create_summary_report_tab() -> html.Div:
    """サマリーレポートタブを作成"""
    content = [html.Div(id='summary-report-insights', style={
        'padding': '15px',
        'backgroundColor': '#e9f2fa',
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("Summary Report", style={'marginBottom': '20px'})]
    report_text = DATA_STORE.get('summary_report')
    if report_text:
        content.append(dcc.Markdown(report_text))
    else:
        content.append(html.P("レポートが見つかりません。"))
    return html.Div(content)


def create_ppt_report_tab() -> html.Div:
    """PowerPointレポートタブを作成"""
    return html.Div([
        html.Div(id='ppt-report-insights', style={
            'padding': '15px',
            'backgroundColor': '#e9f2fa',
            'borderRadius': '8px',
            'marginBottom': '20px',
            'border': '1px solid #cce5ff'
        }),
        html.H3("PPT Report", style={'marginBottom': '20px'}),
        html.P("ボタンを押してPowerPointレポートを生成してください。"),
        html.Button('Generate PPT', id='ppt-generate', n_clicks=0)
    ])

# --- メインレイアウト ---
app.layout = html.Div([
    dcc.Store(id='kpi-data-store', storage_type='memory'),
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
    Output('kpi-data-store', 'data'),
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
            return {}, {'error': 'データファイルが見つかりません'}

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
            'cost_benefit.parquet',
            'work_patterns.parquet'
        ]

        for file in parquet_files:
            if (data_dir / file).exists():
                df = safe_read_parquet(data_dir / file)
                if not df.empty:
                    DATA_STORE[file.replace('.parquet', '')] = df
            elif file == 'daily_cost.parquet' and (data_dir / 'daily_cost.xlsx').exists():
                df = safe_read_excel(data_dir / 'daily_cost.xlsx')
                if not df.empty:
                    DATA_STORE['daily_cost'] = df

        # CSVファイル
        csv_files = [
            'leave_analysis.csv',
            'staff_balance_daily.csv',
            'concentration_requested.csv',
            'leave_ratio_breakdown.csv',
            'demand_series.csv'
        ]

        for file in csv_files:
            if (data_dir / file).exists():
                df = safe_read_csv(data_dir / file)
                if not df.empty:
                    DATA_STORE[file.replace('.csv', '')] = df

        # 動的ヒートマップファイル
        for p in data_dir.glob('heat_*.parquet'):
            if p.name == 'heat_ALL.parquet' or p.name.startswith('heat_emp_'):
                continue
            df = safe_read_parquet(p)
            if not df.empty:
                DATA_STORE[safe_filename(p.stem)] = df

        for p in data_dir.glob('heat_emp_*.parquet'):
            df = safe_read_parquet(p)
            if not df.empty:
                DATA_STORE[safe_filename(p.stem)] = df

        # long_df は intermediate_data.parquet から読み込む
        intermediate_fp = data_dir / 'intermediate_data.parquet'
        if intermediate_fp.exists():
            log.info("intermediate_data.parquet を long_df として読み込みます。")
            df = safe_read_parquet(intermediate_fp)
            if not df.empty:
                DATA_STORE['long_df'] = df
        else:
            DATA_STORE['long_df'] = None
            log.warning(
                '動的ヒートマップの元となる intermediate_data.parquet が見つかりませんでした。'
            )

        # Gap analysis files (excel or parquet)
        for name in ['gap_summary', 'gap_heatmap']:
            excel_fp = data_dir / f'{name}.xlsx'
            parquet_fp = data_dir / f'{name}.parquet'
            df = pd.DataFrame()
            if excel_fp.exists():
                try:
                    df = safe_read_excel(excel_fp)
                except Exception as e:  # noqa: BLE001
                    log.warning(f'Failed to read {excel_fp}: {e}')
            elif parquet_fp.exists():
                df = safe_read_parquet(parquet_fp)
            if not df.empty:
                DATA_STORE[name] = df

        # Summary report markdown
        report_files = sorted(data_dir.glob('OverShortage_SummaryReport_*.md'))
        if report_files:
            latest = report_files[-1]
            try:
                DATA_STORE['summary_report'] = latest.read_text(encoding='utf-8')
            except Exception as e:  # noqa: BLE001
                log.warning(f'Failed to read {latest}: {e}')

        # メタデータ読み込み
        roles, employments = load_shortage_meta(data_dir)
        DATA_STORE['roles'] = roles
        DATA_STORE['employments'] = employments

        # Over/Shortage events and log
        events_df = over_shortage_log.list_events(data_dir)
        if not events_df.empty:
            log_fp = data_dir / 'over_shortage_log.csv'
            existing = over_shortage_log.load_log(log_fp)
            merged = events_df.merge(
                existing,
                on=['date', 'time', 'type'],
                how='left',
                suffixes=('', '_log'),
            )
            for col in ['reason', 'staff', 'memo']:
                if col not in merged.columns:
                    merged[col] = ''
            DATA_STORE['shortage_events'] = merged
            DATA_STORE['shortage_log_path'] = str(log_fp)

        kpi_data = {}
        df_shortage_role = DATA_STORE.get('shortage_role_summary', pd.DataFrame())
        if not df_shortage_role.empty and 'lack_h' in df_shortage_role.columns:
            total_lack_h = df_shortage_role['lack_h'].sum()
            most_lacking_role = df_shortage_role.loc[df_shortage_role['lack_h'].idxmax()]
            kpi_data['total_lack_h'] = total_lack_h
            kpi_data['most_lacking_role_name'] = most_lacking_role['role']
            kpi_data['most_lacking_role_hours'] = most_lacking_role['lack_h']

        log.info(
            f"Loaded {len(DATA_STORE)} data files and calculated {len(kpi_data)} KPIs."
        )
        return kpi_data, {'success': True, 'files': len(DATA_STORE)}

    except Exception as e:
        log.error(f"Error processing ZIP: {e}", exc_info=True)
        return {}, {'error': str(e)}


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
        dcc.Tab(label='疲労分析', value='fatigue'),
        dcc.Tab(label='需要予測', value='forecast'),
        dcc.Tab(label='公平性', value='fairness'),
        dcc.Tab(label='基準乖離分析', value='gap'),
        dcc.Tab(label='Summary Report', value='summary_report'),
        dcc.Tab(label='PPT Report', value='ppt_report'),
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
    elif active_tab == 'fatigue':
        return create_fatigue_tab()
    elif active_tab == 'forecast':
        return create_forecast_tab()
    elif active_tab == 'fairness':
        return create_fairness_tab()
    elif active_tab == 'gap':
        return create_gap_analysis_tab()
    elif active_tab == 'summary_report':
        return create_summary_report_tab()
    elif active_tab == 'ppt_report':
        return create_ppt_report_tab()
    else:
        return html.Div("タブが選択されていません")


@app.callback(
    Output({'type': 'graph-output-heatmap', 'index': 1}, 'children'),
    Output({'type': 'graph-output-heatmap', 'index': 2}, 'children'),
    Input({'type': 'heatmap-filter-role', 'index': 1}, 'value'),
    Input({'type': 'heatmap-filter-employment', 'index': 1}, 'value'),
    Input({'type': 'heatmap-filter-role', 'index': 2}, 'value'),
    Input({'type': 'heatmap-filter-employment', 'index': 2}, 'value'),
)
def update_comparison_heatmaps(role1, emp1, role2, emp2):
    """【新ロジック】生データから動的にヒートマップを生成し、2エリアを更新"""

    # 分析の元となる生データをDATA_STOREから取得
    long_df = DATA_STORE.get('long_df')
    if long_df is None or long_df.empty:
        error_message = html.Div("ヒートマップの元となる生データ(long_df)が見つかりません。")
        return error_message, error_message

    # 'ds' 列をdatetime型に変換し、'time' と 'date_lbl' 列を準備
    if 'date_lbl' not in long_df.columns:
        long_df['ds'] = pd.to_datetime(long_df['ds'])
        long_df['time'] = long_df['ds'].dt.strftime('%H:%M')
        long_df['date_lbl'] = long_df['ds'].dt.strftime('%Y-%m-%d')

    def generate_dynamic_heatmap(selected_role, selected_emp):
        """選択された条件でlong_dfをフィルタし、ピボットテーブルを作成する内部関数"""

        filtered_df = long_df.copy()
        title_parts = []

        # 職種でフィルタリング
        if selected_role and selected_role != 'all':
            filtered_df = filtered_df[filtered_df['role'] == selected_role]
            title_parts.append(f"職種: {selected_role}")

        # 雇用形態でフィルタリング
        if selected_emp and selected_emp != 'all':
            filtered_df = filtered_df[filtered_df['employment'] == selected_emp]
            title_parts.append(f"雇用形態: {selected_emp}")

        title = " AND ".join(title_parts) if title_parts else "全体"

        if filtered_df.empty:
            return generate_heatmap_figure(pd.DataFrame(), f"{title} (データなし)")

        dynamic_heatmap_df = filtered_df.pivot_table(
            index='time',
            columns='date_lbl',
            values='staff',
            aggfunc='nunique',
            fill_value=0
        )
        time_labels = gen_labels(30)
        dynamic_heatmap_df = dynamic_heatmap_df.reindex(time_labels, fill_value=0)

        fig = generate_heatmap_figure(dynamic_heatmap_df, title)
        return dcc.Graph(figure=fig)

    output1 = generate_dynamic_heatmap(role1, emp1)
    output2 = generate_dynamic_heatmap(role2, emp2)

    return output1, output2


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
                options=[{'label': '全体', 'value': 'ALL'}] + [{'label': r, 'value': r} for r in roles],
                value='ALL',
                style={'width': '200px'}
            )
        ], style={'marginBottom': '10px'})
    elif scope == 'employment':
        employments = DATA_STORE.get('employments', [])
        return html.Div([
            html.Label("雇用形態選択"),
            dcc.Dropdown(
                id={'type': 'shortage-detail', 'index': 'employment'},
                options=[{'label': '全体', 'value': 'ALL'}] + [{'label': e, 'value': e} for e in employments],
                value='ALL',
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
        if not detail or detail == 'ALL':
            heat_key = 'heat_ALL'
        elif scope == 'role':
            heat_key = f'heat_{safe_filename(detail)}'
        else:
            heat_key = f'heat_emp_{safe_filename(detail)}'

    df_heat = DATA_STORE.get(heat_key)
    if df_heat is None:
        for key in DATA_STORE.keys():
            if (
                key.startswith('heat_')
                and not key.startswith('heat_emp_')
                and key != 'heat_ALL'
                and detail in key
            ):
                df_heat = DATA_STORE[key]
                break
            if key.startswith('heat_emp_') and detail in key:
                df_heat = DATA_STORE[key]
                break
    if df_heat is None or df_heat.empty:
        return html.Div("データが見つかりません")

    # 不足率を計算
    date_cols = [c for c in df_heat.columns if pd.to_datetime(c, errors='coerce') is not pd.NaT]
    if not date_cols:
        return html.Div("日付データが見つかりません")

    time_labels = gen_labels(30)
    staff_df = df_heat[date_cols].fillna(0).reindex(time_labels, fill_value=0)
    need_series = df_heat.get('need', pd.Series()).fillna(0)
    need_df = pd.DataFrame(
        np.repeat(need_series.values[:, np.newaxis], len(date_cols), axis=1),
        index=time_labels,
        columns=date_cols,
    )
    upper_series = df_heat.get('upper', pd.Series()).fillna(0)
    upper_df = pd.DataFrame(
        np.repeat(upper_series.values[:, np.newaxis], len(date_cols), axis=1),
        index=time_labels,
        columns=date_cols,
    )

    lack_count_df = (need_df - staff_df).clip(lower=0)
    excess_count_df = (staff_df - upper_df).clip(lower=0)
    ratio_df = calc_ratio_from_heatmap(df_heat)
    ratio_df = ratio_df.reindex(time_labels, fill_value=0)

    fig_lack = px.imshow(
        lack_count_df,
        aspect='auto',
        color_continuous_scale='Oranges',
        title='不足人数ヒートマップ',
        labels={'x': '日付', 'y': '時間', 'color': '人数'},
    )
    fig_lack.update_xaxes(
        ticktext=[date_with_weekday(c) for c in lack_count_df.columns],
        tickvals=list(range(len(lack_count_df.columns)))
    )

    fig_excess = px.imshow(
        excess_count_df,
        aspect='auto',
        color_continuous_scale='Blues',
        title='過剰人数ヒートマップ',
        labels={'x': '日付', 'y': '時間', 'color': '人数'},
    )
    fig_excess.update_xaxes(
        ticktext=[date_with_weekday(c) for c in excess_count_df.columns],
        tickvals=list(range(len(excess_count_df.columns)))
    )

    fig_ratio = px.imshow(
        ratio_df,
        aspect='auto',
        color_continuous_scale='RdBu_r',
        title='不足率ヒートマップ',
        labels={'x': '日付', 'y': '時間', 'color': '不足率'},
    )
    fig_ratio.update_xaxes(
        ticktext=[date_with_weekday(c) for c in ratio_df.columns],
        tickvals=list(range(len(ratio_df.columns)))
    )

    return html.Div([
        html.H4('不足人数ヒートマップ'),
        dcc.Graph(figure=fig_lack),
        html.H4('過剰人数ヒートマップ', style={'marginTop': '30px'}),
        dcc.Graph(figure=fig_excess),
        html.H4('不足率ヒートマップ', style={'marginTop': '30px'}),
        dcc.Graph(figure=fig_ratio),
    ])


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
                options=[{'label': '全体', 'value': 'ALL'}] + [{'label': r, 'value': r} for r in roles],
                value='ALL',
                style={'width': '300px', 'marginBottom': '20px'}
            )
        ])
    elif scope == 'employment':
        employments = DATA_STORE.get('employments', [])
        return html.Div([
            html.Label("雇用形態選択"),
            dcc.Dropdown(
                id={'type': 'opt-detail', 'index': 'employment'},
                options=[{'label': '全体', 'value': 'ALL'}] + [{'label': e, 'value': e} for e in employments],
                value='ALL',
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
        if not detail or detail == 'ALL':
            heat_key = 'heat_ALL'
        elif scope == 'role':
            heat_key = f'heat_{safe_filename(detail)}'
        else:
            heat_key = f'heat_emp_{safe_filename(detail)}'

    df_heat = DATA_STORE.get(heat_key)
    if df_heat is None:
        for key in DATA_STORE.keys():
            if (
                key.startswith('heat_')
                and not key.startswith('heat_emp_')
                and key != 'heat_ALL'
                and detail in key
            ):
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

    time_labels = gen_labels(30)
    # 必要なデータを計算
    staff_df = df_heat[date_cols].fillna(0).reindex(time_labels, fill_value=0)
    need_series = df_heat.get('need', pd.Series()).fillna(0)
    upper_series = df_heat.get('upper', pd.Series()).fillna(0)

    # DataFrameに変換
    need_df = pd.DataFrame(
        np.repeat(need_series.values[:, np.newaxis], len(date_cols), axis=1),
        index=time_labels,
        columns=date_cols
    )
    upper_df = pd.DataFrame(
        np.repeat(upper_series.values[:, np.newaxis], len(date_cols), axis=1),
        index=time_labels,
        columns=date_cols
    )

    # 各指標を計算
    surplus_df = (staff_df - need_df).clip(lower=0)
    margin_df = (upper_df - staff_df).clip(lower=0)
    surplus_df = surplus_df.reindex(time_labels, fill_value=0)
    margin_df = margin_df.reindex(time_labels, fill_value=0)

    # スコア計算（不足と過剰のペナルティ）
    lack_ratio = ((need_df - staff_df) / need_df.replace(0, np.nan)).clip(lower=0).fillna(0)
    excess_ratio = ((staff_df - upper_df) / upper_df.replace(0, np.nan)).clip(lower=0).fillna(0)
    score_df = 1 - (0.6 * lack_ratio + 0.4 * excess_ratio)
    score_df = score_df.clip(lower=0, upper=1)
    score_df = score_df.reindex(time_labels, fill_value=0)

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
        )),
        dcc.Markdown(
            "注: この余白は、過去の実績から算出された上限人数と実際の配置人数の差を示します。"\
            "需要が低い日や休業日（例: 日曜日）は、過去のデータに基づく上限値が高めに算出"\
            "されることで、見かけ上の余白が大きくなる場合があります。これは、潜在的な過"\
            "剰人員やコスト発生の可能性を示唆しています。",
            style={'marginTop': '10px'}
        )
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


@app.callback(
    Output('overview-insights', 'children'),
    Input('kpi-data-store', 'data'),
)
def update_overview_insights(kpi_data):
    if not kpi_data:
        return ""

    total_lack_h = kpi_data.get('total_lack_h', 0)

    if total_lack_h > 0:
        most_lacking_role = kpi_data.get('most_lacking_role_name', 'N/A')
        most_lacking_hours = kpi_data.get('most_lacking_role_hours', 0)
        insight_text = f"""
        #### 📈 分析ハイライト
        - **総不足時間:** {total_lack_h:.1f} 時間
        - **最重要課題:** **{most_lacking_role}** の不足が **{most_lacking_hours:.1f}時間** と最も深刻です。この職種の採用または配置転換が急務と考えられます。
        """
        return dcc.Markdown(insight_text)
    return html.P(
        "👍 人員不足は発生していません。素晴らしい勤務体制です！",
        style={'fontWeight': 'bold'},
    )


@app.callback(
    Output('shortage-insights', 'children'),
    Input('kpi-data-store', 'data'),
)
def update_shortage_insights(kpi_data):
    explanation = """
    #### 不足分析の評価方法
    - **不足 (Shortage):** `不足人数 = 必要人数 (Need) - 実績人数` で計算されます。値がプラスの場合、その時間帯は人員が不足していたことを示します。
    - **過剰 (Excess):** `過剰人数 = 実績人数 - 上限人数 (Upper)` で計算されます。値がプラスの場合、過剰な人員が配置されていたことを示します。

    *「必要人数」と「上限人数」は、サイドバーの「分析基準設定」で指定した方法（過去実績の統計、または人員配置基準）に基づいて算出されます。*
    """
    return dcc.Markdown(explanation)


@app.callback(
    Output('hire-plan-insights', 'children'),
    Input('kpi-data-store', 'data'),
)
def update_hire_plan_insights(kpi_data):
    if not kpi_data:
        return ""
    total_lack_h = kpi_data.get('total_lack_h', 0)
    if total_lack_h == 0:
        return html.P("追加採用の必要はありません。")
    role = kpi_data.get('most_lacking_role_name', 'N/A')
    return dcc.Markdown(
        f"最も不足している **{role}** の補充を優先的に検討してください。"
    )


@app.callback(
    Output('optimization-insights', 'children'),
    Input('kpi-data-store', 'data'),
)
def update_optimization_insights(kpi_data):
    explanation = """
    #### 最適化分析の評価方法
    人員配置の効率性は、以下の2つの観点からペナルティを計算し、最終的なスコアを算出します。
    - **不足ペナルティ (重み: 60%):** `(必要人数 - 実績人数) / 必要人数`
    - **過剰ペナルティ (重み: 40%):** `(実績人数 - 上限人数) / 上限人数`

    **最適化スコア = 1 - (不足ペナルティ × 0.6 + 過剰ペナルティ × 0.4)**

    *スコアが1に近いほど、不足も過剰もなく、効率的な人員配置ができている状態を示します。*
    """
    return dcc.Markdown(explanation)


@app.callback(
    Output('leave-insights', 'children'),
    Input('kpi-data-store', 'data'),
)
def update_leave_insights(kpi_data):
    explanation = """
    #### 休暇分析の評価方法
    - **休暇取得者数:** `holiday_type`が休暇関連（希望休、有給など）に設定され、かつ勤務時間がない（`parsed_slots_count = 0`）場合に「1日」としてカウントされます。
    - **集中日:** 「希望休」の取得者数が、サイドバーで設定した閾値（デフォルト: 3人）以上になった日を「集中日」としてハイライトします。
    """
    return dcc.Markdown(explanation)


@app.callback(
    Output('cost-insights', 'children'),
    Input('kpi-data-store', 'data'),
)
def update_cost_insights(kpi_data):
    explanation = """
    #### コスト分析の評価方法
    日々の人件費は、各スタッフの勤務時間（スロット数 × スロット長）に、サイドバーで設定した単価基準（職種別、雇用形態別など）の時給を乗じて算出されます。
    """
    return dcc.Markdown(explanation)


@app.callback(
    Output('sim-shortage-graph', 'figure'),
    Output('sim-cost-text', 'children'),
    Input('sim-work-pattern-dropdown', 'value'),
    Input('sim-hire-fte-slider', 'value'),
    State('kpi-data-store', 'data'),
)
def update_hire_simulation(selected_pattern, added_fte, kpi_data):
    if not kpi_data or not selected_pattern:
        raise PreventUpdate

    from shift_suite.tasks.h2hire import (
        AVG_HOURLY_WAGE,
        RECRUIT_COST_PER_HIRE,
    )

    df_work_patterns = DATA_STORE.get('work_patterns', pd.DataFrame())
    df_shortage_role = DATA_STORE.get('shortage_role_summary', pd.DataFrame()).copy()

    pattern_info = df_work_patterns[df_work_patterns['code'] == selected_pattern]
    if pattern_info.empty:
        raise PreventUpdate
    slots_per_day = pattern_info['parsed_slots_count'].iloc[0]
    hours_per_day = slots_per_day * 0.5
    reduction_hours = added_fte * hours_per_day * 20

    if not df_shortage_role.empty:
        most_lacking_role_index = df_shortage_role['lack_h'].idxmax()
        original_hours = df_shortage_role.loc[most_lacking_role_index, 'lack_h']
        df_shortage_role.loc[most_lacking_role_index, 'lack_h'] = max(0, original_hours - reduction_hours)

    fig = px.bar(
        df_shortage_role,
        x='role',
        y='lack_h',
        title=f'シミュレーション後: {selected_pattern}勤務者を{added_fte}人追加採用した場合の残存不足時間',
        labels={'lack_h': '残存不足時間(h)'},
    )

    new_total_lack_h = df_shortage_role['lack_h'].sum()
    original_total_lack_h = kpi_data.get('total_lack_h', 0)

    cost_before = original_total_lack_h * 2200
    cost_after_temp = new_total_lack_h * 2200

    added_labor_cost = reduction_hours * AVG_HOURLY_WAGE
    added_recruit_cost = added_fte * RECRUIT_COST_PER_HIRE
    cost_after_hire = cost_after_temp + added_labor_cost + added_recruit_cost

    cost_text = f"""
    #### シミュレーション結果
    - **採用コスト:** {added_recruit_cost:,.0f} 円 (一時)
    - **追加人件費:** {added_labor_cost:,.0f} 円 (期間中)
    - **総コスト (採用シナリオ):** {cost_after_hire:,.0f} 円
    - **比較 (全て派遣で補填した場合):** {cost_before:,.0f} 円
    """

    return fig, dcc.Markdown(cost_text)


@app.callback(
    Output('factor-output', 'children'),
    Input('factor-train-button', 'n_clicks')
)
def run_factor_analysis(n_clicks):
    if not n_clicks:
        raise PreventUpdate

    heat_df = DATA_STORE.get('heat_ALL', pd.DataFrame())
    short_df = DATA_STORE.get('shortage_time', pd.DataFrame())
    leave_df = DATA_STORE.get('leave_analysis', pd.DataFrame())

    if heat_df.empty or short_df.empty:
        return html.Div('必要なデータがありません')

    analyzer = ShortageFactorAnalyzer()
    feat_df = analyzer.generate_features(pd.DataFrame(), heat_df, short_df, leave_df, set())
    model, fi_df = analyzer.train_and_get_feature_importance(feat_df)
    DATA_STORE['factor_features'] = feat_df
    DATA_STORE['factor_importance'] = fi_df

    table = dash_table.DataTable(
        data=fi_df.head(5).to_dict('records'),
        columns=[{'name': c, 'id': c} for c in fi_df.columns]
    )
    return html.Div([html.H5('Top factors'), table])


@app.callback(
    Output('save-log-msg', 'children'),
    Input('save-log-button', 'n_clicks'),
    State('over-shortage-table', 'data'),
    State('log-save-mode', 'value')
)
def save_over_shortage_log(n_clicks, table_data, mode):
    if not n_clicks:
        raise PreventUpdate

    log_path = DATA_STORE.get('shortage_log_path')
    if not log_path:
        return 'ログファイルパスが見つかりません'

    df = pd.DataFrame(table_data)
    over_shortage_log.save_log(df, log_path, mode=mode)
    return 'ログを保存しました'

# --- アプリケーション起動 ---
if __name__ == '__main__':
    app.run_server(debug=True, port=8050, host='127.0.0.1')
