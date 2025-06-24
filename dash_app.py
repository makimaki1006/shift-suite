# dash_app.py - Shift-Suite高速分析ビューア (app.py機能完全再現版)
import base64
import io
import json
import logging
import tempfile
import zipfile
from pathlib import Path
from typing import List, Tuple
from functools import lru_cache
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
from shift_suite.tasks.daily_cost import calculate_daily_cost

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
    try:  # noqa: E722
        date = pd.to_datetime(date_str)
        weekdays = ['月', '火', '水', '木', '金', '土', '日']
        return f"{date.strftime('%m/%d')}({weekdays[date.weekday()]})"
    except Exception:
        return str(date_str)


def safe_read_parquet(filepath: Path) -> pd.DataFrame:
    """Parquetファイルを安全に読み込む"""
    try:
        return pd.read_parquet(filepath)  # type: ignore
    except Exception as e:
        log.warning(f"Failed to read {filepath}: {e}")
        return pd.DataFrame()


def safe_read_csv(filepath: Path) -> pd.DataFrame:
    """CSVファイルを安全に読み込む"""
    try:
        return pd.read_csv(filepath)  # type: ignore
    except Exception as e:
        log.warning(f"Failed to read {filepath}: {e}")
        return pd.DataFrame()


@lru_cache(maxsize=32)
def cached_read_parquet(path: str) -> pd.DataFrame:
    """Cached reader for Parquet files."""
    return safe_read_parquet(Path(path))


@lru_cache(maxsize=32)
def cached_read_csv(path: str) -> pd.DataFrame:
    """Cached reader for CSV files."""
    return safe_read_csv(Path(path))


def load_parquet_from_session(session_data: dict, scenario: str, name: str) -> pd.DataFrame:
    """Load a Parquet file for a given scenario using caching."""
    if not session_data or 'scenario_paths' not in session_data:
        return pd.DataFrame()
    scenario_path = session_data['scenario_paths'].get(scenario)
    if not scenario_path:
        return pd.DataFrame()
    fp = Path(scenario_path) / f"{name}.parquet"
    if fp.exists():
        return cached_read_parquet(str(fp))
    return pd.DataFrame()


def load_csv_from_session(session_data: dict, scenario: str, name: str) -> pd.DataFrame:
    """Load a CSV file for a given scenario using caching."""
    if not session_data or 'scenario_paths' not in session_data:
        return pd.DataFrame()
    scenario_path = session_data['scenario_paths'].get(scenario)
    if not scenario_path:
        return pd.DataFrame()
    fp = Path(scenario_path) / f"{name}.csv"
    if fp.exists():
        return cached_read_csv(str(fp))
    return pd.DataFrame()


def _valid_df(df: pd.DataFrame) -> bool:
    """Return True if ``df`` is a non-empty :class:`~pandas.DataFrame`."""
    return isinstance(df, pd.DataFrame) and not df.empty


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


def load_data_from_dir(data_dir: Path) -> Tuple[dict, dict]:
    """Load analysis data from the given directory and its base directory."""
    global DATA_STORE
    DATA_STORE = {}

    base_dir = data_dir.parent
    search_dirs = [data_dir, base_dir]
    log.info(f"データ読み込み開始: {search_dirs}")

    # Parquet files
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
        'work_patterns.parquet',
    ]

    for file in parquet_files:
        for directory in search_dirs:
            fp = directory / file
            if fp.exists():
                df = safe_read_parquet(fp)
                if not df.empty:
                    DATA_STORE[file.replace('.parquet', '')] = df
                break
            elif file == 'daily_cost.parquet' and (directory / 'daily_cost.xlsx').exists():
                df = safe_read_excel(directory / 'daily_cost.xlsx')
                if not df.empty:
                    DATA_STORE['daily_cost'] = df
                break

    csv_files = [
        'leave_analysis.csv',
        'staff_balance_daily.csv',
        'concentration_requested.csv',
        'leave_ratio_breakdown.csv',
        'demand_series.csv',
    ]

    for file in csv_files:
        for directory in search_dirs:
            fp = directory / file
            if fp.exists():
                df = safe_read_csv(fp)
                if not df.empty:
                    key = file.replace('.csv', '')
                    DATA_STORE[key] = df
                break

    # Fallback: extract from leave_analysis.csv if others are missing
    if 'leave_analysis' in DATA_STORE and 'staff_balance_daily' not in DATA_STORE:
        leave_df = DATA_STORE['leave_analysis']
        if 'leave_type' in leave_df.columns:
            DATA_STORE['daily_summary'] = leave_df

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

    intermediate_fp = data_dir / 'intermediate_data.parquet'
    if intermediate_fp.exists():
        log.info('intermediate_data.parquet を long_df として読み込みます。')
        df = safe_read_parquet(intermediate_fp)
        if not df.empty:
            DATA_STORE['long_df'] = df
    else:
        DATA_STORE['long_df'] = None
        log.warning('動的ヒートマップの元となる intermediate_data.parquet が見つかりませんでした。')

    pre_aggr_fp = data_dir / 'pre_aggregated_data.parquet'
    if pre_aggr_fp.exists():
        DATA_STORE['pre_aggregated_data'] = safe_read_parquet(pre_aggr_fp)

    for name in ['gap_summary', 'gap_heatmap']:
        excel_fp = data_dir / f'{name}.xlsx'
        parquet_fp = data_dir / f'{name}.parquet'
        df = pd.DataFrame()
        if excel_fp.exists():
            try:
                df = safe_read_excel(excel_fp)
            except Exception as e:
                log.warning(f'Failed to read {excel_fp}: {e}')
        elif parquet_fp.exists():
            df = safe_read_parquet(parquet_fp)
        if not df.empty:
            DATA_STORE[name] = df

    report_files = sorted(data_dir.glob('OverShortage_SummaryReport_*.md'))
    if report_files:
        latest = report_files[-1]
        try:
            DATA_STORE['summary_report'] = latest.read_text(encoding='utf-8')
        except Exception as e:
            log.warning(f'Failed to read {latest}: {e}')

    roles, employments = load_shortage_meta(data_dir)
    DATA_STORE['roles'] = roles
    DATA_STORE['employments'] = employments

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

    log.info(f"Loaded files: {list(DATA_STORE.keys())}")
    log.info(f"Available in {data_dir}: {[f.name for f in data_dir.iterdir() if f.is_file()]}")
    log.info(
        f"Loaded {len(DATA_STORE)} data files and calculated {len(kpi_data)} KPIs."
    )
    return kpi_data, {'success': True, 'files': len(DATA_STORE)}


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
    display_df_renamed = display_df.copy()
    display_df_renamed.columns = [date_with_weekday(c) for c in display_df.columns]

    fig = px.imshow(
        display_df_renamed,
        aspect='auto',
        color_continuous_scale=px.colors.sequential.Viridis,
        title=title,
        labels={'x': '日付', 'y': '時間', 'color': '人数'}
    )
    fig.update_xaxes(tickvals=list(range(len(display_df.columns))))
    return fig

# --- UIコンポーネント生成関数 ---
def create_metric_card(label: str, value: str, color: str = "#1f77b4") -> html.Div:
    """メトリクスカードを作成"""
    return html.Div([
        html.Div(label, style={  # type: ignore
            'fontSize': '14px',
            'color': '#666',
            'marginBottom': '5px'
        }),
        html.Div(value, style={  # type: ignore
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
        html.Div(id='overview-insights', style={  # type: ignore
            'padding': '15px',
            'backgroundColor': '#e9f2fa',
            'borderRadius': '8px',
            'marginBottom': '20px',
            'border': '1px solid #cce5ff'
        }),
        html.H3("分析概要", style={'marginBottom': '20px'}),  # type: ignore
        html.Div([  # type: ignore
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
        return html.Div([  # type: ignore
            html.H4(f"比較エリア {area_id}", style={'marginTop': '20px', 'borderTop': '2px solid #ddd', 'paddingTop': '20px'}),  # type: ignore

            # --- 各エリアに職種と雇用形態の両方のフィルターを設置 ---
            html.Div([  # type: ignore
                html.Div([  # type: ignore
                    html.Label("職種フィルター"),  # type: ignore
                    dcc.Dropdown(
                        id={'type': 'heatmap-filter-role', 'index': area_id},
                        options=[{'label': 'すべて', 'value': 'all'}] + [{'label': r, 'value': r} for r in roles],
                        value='all',
                        clearable=False
                    )
                ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),

                html.Div([  # type: ignore
                    html.Label("雇用形態フィルター"),  # type: ignore
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
        html.H3("ヒートマップ比較分析", style={'marginBottom': '20px'}),  # type: ignore
        html.P("上下のエリアでそれぞれ「職種」と「雇用形態」の組み合わせを選択し、ヒートマップを比較してください。"),  # type: ignore
        create_comparison_area(1),
        create_comparison_area(2)
    ])


def create_shortage_tab() -> html.Div:
    """不足分析タブを作成"""
    df_shortage_role = DATA_STORE.get('shortage_role_summary', pd.DataFrame())
    df_shortage_emp = DATA_STORE.get('shortage_employment_summary', pd.DataFrame())

    content = [html.Div(id='shortage-insights', style={  # type: ignore
        'padding': '15px',
        'backgroundColor': '#e9f2fa',
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("不足分析", style={'marginBottom': '20px'}),  # type: ignore
        html.Div(  # type: ignore
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
        content.append(html.H4("職種別不足時間"))  # type: ignore

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
                        create_metric_card(f"不足Top{i+1}", f"{row.role}: {row.lack_h:.1f}h")  # type: ignore
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
        content.append(html.H4("雇用形態別不足時間", style={'marginTop': '30px'}))  # type: ignore

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
        html.H4("不足率ヒートマップ", style={'marginTop': '30px'}),  # type: ignore
        html.P("各時間帯で必要人数に対してどれくらいの割合で人員が不足していたかを示します。"),  # type: ignore
        html.Div([  # type: ignore
            html.Label("表示範囲"),  # type: ignore
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
    content.append(html.H4('要因分析 (AI)', style={'marginTop': '30px'}))  # type: ignore
    content.append(html.Button('要因分析モデルを学習', id='factor-train-button', n_clicks=0))  # type: ignore
    content.append(html.Div(id='factor-output'))  # type: ignore

    # Over/Short Log section
    events_df = DATA_STORE.get('shortage_events', pd.DataFrame())
    if not events_df.empty:
        content.append(html.Hr())  # type: ignore
        content.append(html.H4('過不足手動ログ', style={'marginTop': '30px'}))  # type: ignore
        content.append(dash_table.DataTable(
            id='over-shortage-table',
            data=events_df.to_dict('records'),
            columns=[{'name': c, 'id': c, 'presentation': 'input'} for c in events_df.columns],
            editable=True,
        ))
        content.append(dcc.RadioItems(
            id='log-save-mode',
            options=[{'label': '追記', 'value': 'append'}, {'label': '上書き', 'value': 'overwrite'}],
            value='追記',
            inline=True,
            style={'marginTop': '10px'}
        ))
        content.append(html.Button('ログを保存', id='save-log-button', n_clicks=0, style={'marginTop': '10px'}))  # type: ignore
        content.append(html.Div(id='save-log-msg'))  # type: ignore

    return html.Div(content)


def create_optimization_tab() -> html.Div:
    """最適化分析タブを作成"""
    return html.Div([  # type: ignore
        html.Div(id='optimization-insights', style={
            'padding': '15px',
            'backgroundColor': '#e9f2fa',
            'borderRadius': '8px',
            'marginBottom': '20px',
            'border': '1px solid #cce5ff'
        }),
        html.H3("最適化分析", style={'marginBottom': '20px'}),  # type: ignore
        html.Div([  # type: ignore
            html.Label("表示範囲"),  # type: ignore
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
        html.Div(id='opt-detail-container'),  # type: ignore
        html.Div(id='optimization-content')  # type: ignore
    ])


def create_leave_analysis_tab() -> html.Div:
    """休暇分析タブを作成"""
    content = [html.Div(id='leave-insights', style={  # type: ignore
        'padding': '15px',
        'backgroundColor': '#e9f2fa',
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("休暇分析", style={'marginBottom': '20px'})]  # type: ignore

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
    content = [html.Div(id='cost-insights', style={  # type: ignore
        'padding': '15px',
        'backgroundColor': '#e9f2fa',
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("人件費分析", style={'marginBottom': '20px'})]  # type: ignore

    df_cost = DATA_STORE.get('daily_cost', pd.DataFrame())
    if not df_cost.empty:
        df_cost['date'] = pd.to_datetime(df_cost['date'])

        # long_dfから詳細情報を取得して結合
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

        df_cost = df_cost.sort_values('date')

        total_cost = df_cost['cost'].sum()
        avg_daily_cost = df_cost['cost'].mean()
        max_cost_day = df_cost.loc[df_cost['cost'].idxmax()]

        summary_cards = html.Div([
            create_metric_card("総コスト", f"¥{total_cost:,.0f}"),
            create_metric_card("日平均コスト", f"¥{avg_daily_cost:,.0f}"),
            create_metric_card(
                "最高コスト日",
                f"{max_cost_day['date'].strftime('%m/%d')}<br>¥{max_cost_day['cost']:,.0f}"
            ),
        ], style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '20px'})
        content.append(summary_cards)

        df_cost['cumulative_cost'] = df_cost['cost'].cumsum()
        fig_cumulative = px.area(
            df_cost,
            x='date',
            y='cumulative_cost',
            title='累計人件費の推移',
            labels={'date': '日付', 'cumulative_cost': '累計コスト (円)'},
        )
        fig_cumulative.update_xaxes(tickformat="%m/%d(%a)")
        content.append(dcc.Graph(figure=fig_cumulative))

        # 既存の日別総コスト棒グラフ
        fig_daily = px.bar(
            df_cost,
            x='date',
            y='cost',
            title='日別発生人件費（総額）',
            labels={'date': '日付', 'cost': 'コスト(円)'},
            color_discrete_sequence=['#1f77b4']
        )
        fig_daily.update_xaxes(tickformat="%m/%d(%a)")

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

        # 2. 職種別積み上げグラフ
        if 'role_breakdown' in df_cost.columns:
            role_data = []
            for _, row in df_cost.iterrows():
                if pd.notna(row.get('role_breakdown')):
                    date_total_cost = row['cost']
                    role_counts: dict[str, int] = {}
                    total_count = 0
                    for role_count in row['role_breakdown'].split(', '):
                        if ':' in role_count:
                            role, count = role_count.split(':')
                            role_counts[role] = int(count)
                            total_count += int(count)

                    for role, count in role_counts.items():
                        role_cost = (count / total_count) * date_total_cost if total_count > 0 else 0
                        role_data.append({'date': row['date'], 'role': role, 'count': count, 'cost': role_cost})

            if role_data:
                role_df = pd.DataFrame(role_data)

                fig_stacked = px.bar(
                    role_df,
                    x='date',
                    y='cost',
                    color='role',
                    title='日別人件費（職種別内訳）',
                    labels={'date': '日付', 'cost': 'コスト(円)', 'role': '職種'},
                    hover_data=['count']
                )
                fig_stacked.update_xaxes(tickformat="%m/%d(%a)")
                fig_stacked.update_traces(
                    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>' +
                                 '職種: %{fullData.name}<br>' +
                                 'コスト: %{y:,.0f}円<br>' +
                                 '人数: %{customdata[0]}人' +
                                 '<extra></extra>'
                )
                content.append(dcc.Graph(figure=fig_stacked))

                # 3. 月次職種別積み上げグラフ
                role_df['month'] = pd.to_datetime(role_df['date']).dt.to_period('M').astype(str)
                monthly_role = role_df.groupby(['month', 'role'])['cost'].sum().reset_index()

                fig_monthly = px.bar(
                    monthly_role,
                    x='month',
                    y='cost',
                    color='role',
                    title='月次人件費（職種別内訳）',
                    labels={'month': '月', 'cost': 'コスト(円)', 'role': '職種'}
                )
                content.append(dcc.Graph(figure=fig_monthly))

                # 4. 職種別コスト比率の円グラフ
                total_by_role = role_df.groupby('role')['cost'].sum().reset_index()

                fig_pie = px.pie(
                    total_by_role,
                    values='cost',
                    names='role',
                    title='職種別コスト構成比（全期間）'
                )
                fig_pie.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate='%{label}<br>%{value:,.0f}円<br>%{percent}<extra></extra>'
                )
                content.append(dcc.Graph(figure=fig_pie))

        # 累計コストグラフは上で生成済み

    # --- 動的再計算UI ---
    content.append(html.H4("動的コストシミュレーション", style={'marginTop': '30px'}))  # type: ignore
    content.append(dcc.RadioItems(
        id='cost-by-radio',
        options=[
            {'label': '職種別', 'value': 'role'},
            {'label': '雇用形態別', 'value': 'employment'},
            {'label': 'スタッフ別', 'value': 'staff'},
        ],
        value='role',
        inline=True,
    ))
    content.append(html.Div(id='wage-input-container'))
    content.append(dcc.Graph(id='dynamic-cost-graph'))

    return html.Div(content)


def create_hire_plan_tab() -> html.Div:
    """採用計画タブを作成"""
    content = [html.Div(id='hire-plan-insights', style={  # type: ignore
        'padding': '15px',
        'backgroundColor': '#e9f2fa',
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("採用計画", style={'marginBottom': '20px'})]  # type: ignore

    df_hire = DATA_STORE.get('hire_plan', pd.DataFrame())
    df_shortage_role = DATA_STORE.get('shortage_role_summary', pd.DataFrame())
    df_work_patterns = DATA_STORE.get('work_patterns', pd.DataFrame())
    if not df_hire.empty:
        content.append(html.H4("必要FTE（職種別）"))  # type: ignore

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
            html.H4("What-if 採用シミュレーション", style={'marginTop': '30px'}),  # type: ignore
            html.P("スライダーを動かして、追加採用による不足時間の削減効果とコストの変化を確認できます。"),  # type: ignore
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
        content.append(html.Div(id='sim-cost-text'))  # type: ignore

    # 最適採用計画
    df_optimal = DATA_STORE.get('optimal_hire_plan', pd.DataFrame())
    if not df_optimal.empty:
        content.append(html.H4("最適採用計画", style={'marginTop': '30px'}))  # type: ignore
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
        html.Div(  # type: ignore
            dcc.Markdown(explanation),
            style={
                'padding': '15px',
                'backgroundColor': '#e9f2fa',
                'borderRadius': '8px',
                'marginBottom': '20px',
                'border': '1px solid #cce5ff',
            },
        ),
        html.H3("疲労分析", style={'marginBottom': '20px'}),  # type: ignore
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
        content.append(html.P("疲労分析データが見つかりません。"))  # type: ignore

    return html.Div(content)


def create_forecast_tab() -> html.Div:
    """需要予測タブを作成"""
    content = [html.Div(id='forecast-insights', style={  # type: ignore
        'padding': '15px',
        'backgroundColor': '#e9f2fa',
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("需要予測", style={'marginBottom': '20px'})]  # type: ignore
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
        content.append(html.P("需要予測データが見つかりません。"))  # type: ignore

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
        html.Div(  # type: ignore
            dcc.Markdown(explanation),
            style={
                'padding': '15px',
                'backgroundColor': '#f0f0f0',
                'borderRadius': '8px',
                'marginBottom': '20px',
                'border': '1px solid #ddd',
            },
        ),
        html.H3("公平性 (不公平感スコア)", style={'marginBottom': '20px'}),  # type: ignore
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
            content.append(html.H4('不公平感ランキング'))  # type: ignore
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
    content = [html.Div(id='gap-insights', style={  # type: ignore
        'padding': '15px',
        'backgroundColor': '#e9f2fa',
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("基準乖離分析", style={'marginBottom': '20px'})]  # type: ignore
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
        content.append(html.P("基準乖離データが見つかりません。"))  # type: ignore

    return html.Div(content)


def create_summary_report_tab() -> html.Div:
    """サマリーレポートタブを作成"""
    content = [html.Div(id='summary-report-insights', style={  # type: ignore
        'padding': '15px',
        'backgroundColor': '#e9f2fa',
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("サマリーレポート", style={'marginBottom': '20px'})]  # type: ignore
    report_text = DATA_STORE.get('summary_report')
    if report_text:
        content.append(dcc.Markdown(report_text))
    else:
        content.append(html.P("レポートが見つかりません。"))
    return html.Div(content)


def create_ppt_report_tab() -> html.Div:
    """PowerPointレポートタブを作成"""
    return html.Div([  # type: ignore
        html.Div(id='ppt-report-insights', style={
            'padding': '15px',
            'backgroundColor': '#e9f2fa',
            'borderRadius': '8px',
            'marginBottom': '20px',
            'border': '1px solid #cce5ff'
        }),
        html.H3("PowerPointレポート", style={'marginBottom': '20px'}),  # type: ignore
        html.P("ボタンを押してPowerPointレポートを生成してください。"),  # type: ignore
        html.Button('PPTレポートを生成', id='ppt-generate', n_clicks=0)  # type: ignore
    ])

# --- メインレイアウト ---
app.layout = html.Div([
    dcc.Store(id='kpi-data-store', storage_type='memory'),
    dcc.Store(id='session-data-store', storage_type='memory'),

    # ヘッダー
    html.Div([  # type: ignore
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
    html.Div([  # type: ignore
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

    html.Div([  # type: ignore
        html.H3("分析シナリオ選択", style={'textAlign': 'center'}),
        dcc.Dropdown(
            id='scenario-dropdown',
            placeholder="まず分析結果のZIPファイルをアップロードしてください",
            style={'width': '60%', 'margin': 'auto'}
        )
    ], id='scenario-selector-div', style={'display': 'none'}),

    # メインコンテンツ
    html.Div(id='main-content', style={'padding': '20px'}),  # type: ignore

], style={'backgroundColor': '#f5f5f5', 'minHeight': '100vh'})

# --- コールバック関数 ---
@app.callback(
    Output('session-data-store', 'data'),
    Output('scenario-dropdown', 'options'),
    Output('scenario-dropdown', 'value'),
    Output('scenario-selector-div', 'style'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def process_upload(contents, filename):
    """ZIPファイルをアップロードしてシナリオを検出"""
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

        scenarios = [d.name for d in TEMP_DIR.iterdir() if d.is_dir() and d.name.startswith('out_')]
        if not scenarios:
            return {'error': '分析シナリオのフォルダが見つかりません'}, [], None, {'display': 'none'}

        # 日本語ラベル用のマッピング
        scenario_name_map = {
            'out_median_based': '中央値ベース',
            'out_mean_based': '平均値ベース',
            'out_p25_based': '25パーセンタイルベース',
        }

        scenario_options = [
            {'label': scenario_name_map.get(s, s.replace('out_', '')), 'value': s}
            for s in scenarios
        ]
        first_scenario = scenarios[0]
        scenario_paths = {s: str(TEMP_DIR / s) for s in scenarios}
        return {'scenario_paths': scenario_paths}, scenario_options, first_scenario, {'display': 'block'}

    except Exception as e:
        log.error(f"Error processing ZIP: {e}", exc_info=True)
        return {'error': str(e)}, [], None, {'display': 'none'}


@app.callback(
    Output('kpi-data-store', 'data'),
    Output('main-content', 'children'),
    Input('scenario-dropdown', 'value'),
    State('session-data-store', 'data')
)
def update_content_for_scenario(selected_scenario, session_data):
    """シナリオ選択に応じてデータを読み込み、メインUIを更新"""
    if not selected_scenario or not session_data:
        raise PreventUpdate

    scenario_paths = session_data.get('scenario_paths', {})
    scenario_dir = scenario_paths.get(selected_scenario)
    if not scenario_dir:
        raise PreventUpdate

    data_dir = Path(scenario_dir)
    if not data_dir.exists():
        raise PreventUpdate

    # 既存データをクリアし読み込み直す
    global DATA_STORE
    kpi_data, _ = load_data_from_dir(data_dir)

    # 高速化用の事前集計データを読み込み
    aggregated_fp = data_dir / 'pre_aggregated_data.parquet'
    if aggregated_fp.exists():
        DATA_STORE['pre_aggregated_data'] = pd.read_parquet(aggregated_fp)
    else:
        return kpi_data, html.Div(f"エラー: {aggregated_fp} が見つかりません。")  # type: ignore

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
        dcc.Tab(label='サマリーレポート', value='summary_report'),
        dcc.Tab(label='PPTレポート', value='ppt_report'),
    ])

    main_layout = html.Div([
        tabs,
        html.Div(id='tab-content', style={'marginTop': '20px'})
    ])

    return kpi_data, main_layout


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
        return create_ppt_report_tab()  # type: ignore
    else:
        return html.Div("タブが選択されていません")


@app.callback(
    Output({'type': 'heatmap-filter-employment', 'index': ALL}, 'options'),
    Output({'type': 'heatmap-filter-employment', 'index': ALL}, 'value'),
    Input({'type': 'heatmap-filter-role', 'index': ALL}, 'value'),
)
def update_employment_options(selected_roles):
    """職種選択に応じて雇用形態フィルターを更新"""
    aggregated_df = DATA_STORE.get('pre_aggregated_data')
    if aggregated_df is None or aggregated_df.empty:
        default_options = [{'label': 'すべて', 'value': 'all'}]
        return [default_options, default_options], ['all', 'all']

    output_options = []
    for role in selected_roles:
        if role and role != 'all':
            employments = aggregated_df[aggregated_df['role'] == role][
                'employment'
            ].unique()
            new_options = (
                [{'label': 'すべて', 'value': 'all'}]
                + [{'label': emp, 'value': emp} for emp in sorted(employments)]
            )
        else:
            all_employments = aggregated_df['employment'].unique()
            new_options = (
                [{'label': 'すべて', 'value': 'all'}]
                + [{'label': emp, 'value': emp} for emp in sorted(all_employments)]
            )
        output_options.append(new_options)

    return output_options, ['all', 'all']


@app.callback(
    Output({'type': 'graph-output-heatmap', 'index': 1}, 'children'),
    Output({'type': 'graph-output-heatmap', 'index': 2}, 'children'),
    Input({'type': 'heatmap-filter-role', 'index': 1}, 'value'),
    Input({'type': 'heatmap-filter-employment', 'index': 1}, 'value'),
    Input({'type': 'heatmap-filter-role', 'index': 2}, 'value'),
    Input({'type': 'heatmap-filter-employment', 'index': 2}, 'value'),
)
def update_comparison_heatmaps(role1, emp1, role2, emp2):
    """事前集計データから動的にヒートマップを生成し、2エリアを更新"""

    aggregated_df = DATA_STORE.get('pre_aggregated_data')
    if aggregated_df is None or aggregated_df.empty:
        error_message = html.Div("ヒートマップの元データが見つかりません。")  # type: ignore
        return error_message, error_message

    def generate_dynamic_heatmap(selected_role, selected_emp):
        """選択された条件で事前集計データをフィルタしピボット化"""

        filtered_df = aggregated_df.copy()
        title_parts = []

        if selected_role and selected_role != 'all':
            filtered_df = filtered_df[filtered_df['role'] == selected_role]
            title_parts.append(f"職種: {selected_role}")

        if selected_emp and selected_emp != 'all':
            filtered_df = filtered_df[filtered_df['employment'] == selected_emp]
            title_parts.append(f"雇用形態: {selected_emp}")

        title = " AND ".join(title_parts) if title_parts else "全体"

        if filtered_df.empty:
            time_labels = gen_labels(30)
            all_dates = sorted(aggregated_df['date_lbl'].unique())
            empty_heatmap = pd.DataFrame(index=time_labels, columns=all_dates).fillna(0)
            fig_empty = generate_heatmap_figure(empty_heatmap, f"{title} (勤務データなし)")
            return dcc.Graph(figure=fig_empty)

        dynamic_heatmap_df = filtered_df.pivot_table(
            index='time',
            columns='date_lbl',
            values='staff_count',
            aggfunc='sum',
            fill_value=0,
        )

        time_labels = gen_labels(30)
        all_dates = sorted(aggregated_df['date_lbl'].unique())
        dynamic_heatmap_df = dynamic_heatmap_df.reindex(index=time_labels, columns=all_dates, fill_value=0)

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
        return html.Div([  # type: ignore
            html.Label("職種選択"),  # type: ignore
            dcc.Dropdown(
                id={'type': 'shortage-detail', 'index': 'role'},
                options=[{'label': '全体', 'value': 'ALL'}] + [{'label': r, 'value': r} for r in roles],
                value='ALL',
                style={'width': '200px'}
            )
        ], style={'marginBottom': '10px'})
    elif scope == 'employment':
        employments = DATA_STORE.get('employments', [])
        return html.Div([  # type: ignore
            html.Label("雇用形態選択"),  # type: ignore
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
    Input('session-data-store', 'data'),
    Input('scenario-dropdown', 'value'),
    Input('shortage-heatmap-scope', 'value'),
    Input({'type': 'shortage-detail', 'index': ALL}, 'value')
)
def update_shortage_ratio_heatmap(session_data, selected_scenario, scope, detail_values):
    """不足率ヒートマップを更新"""
    if not session_data or not selected_scenario:
        raise PreventUpdate

    lack_count_df = load_parquet_from_session(session_data, selected_scenario, 'shortage_time')
    excess_count_df = load_parquet_from_session(session_data, selected_scenario, 'excess_time')
    ratio_df = load_parquet_from_session(session_data, selected_scenario, 'shortage_ratio')

    if lack_count_df.empty:
        return html.Div("不足分析データが見つかりません")  # type: ignore

    lack_count_df_renamed = lack_count_df.copy()
    lack_count_df_renamed.columns = [date_with_weekday(c) for c in lack_count_df_renamed.columns]
    fig_lack = px.imshow(
        lack_count_df_renamed,
        aspect='auto',
        color_continuous_scale='Oranges',
        title='不足人数ヒートマップ',
        labels={'x': '日付', 'y': '時間', 'color': '人数'},
    )
    fig_lack.update_xaxes(tickvals=list(range(len(lack_count_df.columns))))

    fig_excess = go.Figure()
    if not excess_count_df.empty:
        excess_count_df_renamed = excess_count_df.copy()
        excess_count_df_renamed.columns = [date_with_weekday(c) for c in excess_count_df_renamed.columns]
        fig_excess = px.imshow(
            excess_count_df_renamed,
            aspect='auto',
            color_continuous_scale='Blues',
            title='過剰人数ヒートマップ',
            labels={'x': '日付', 'y': '時間', 'color': '人数'},
        )
        fig_excess.update_xaxes(tickvals=list(range(len(excess_count_df.columns))))

    fig_ratio = go.Figure()
    if not ratio_df.empty:
        ratio_df_renamed = ratio_df.copy()
        ratio_df_renamed.columns = [date_with_weekday(c) for c in ratio_df_renamed.columns]
        fig_ratio = px.imshow(
            ratio_df_renamed,
            aspect='auto',
            color_continuous_scale='RdBu_r',
            title='不足率ヒートマップ',
            labels={'x': '日付', 'y': '時間', 'color': '不足率'},
        )
        fig_ratio.update_xaxes(tickvals=list(range(len(ratio_df.columns))))

    return html.Div([  # type: ignore
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
        return html.Div([  # type: ignore
            html.Label("職種選択"),  # type: ignore
            dcc.Dropdown(
                id={'type': 'opt-detail', 'index': 'role'},
                options=[{'label': '全体', 'value': 'ALL'}] + [{'label': r, 'value': r} for r in roles],
                value='ALL',
                style={'width': '300px', 'marginBottom': '20px'}
            )
        ])
    elif scope == 'employment':
        employments = DATA_STORE.get('employments', [])
        return html.Div([  # type: ignore
            html.Label("雇用形態選択"),  # type: ignore
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
    df_surplus = DATA_STORE.get('surplus_vs_need_time', pd.DataFrame())
    df_margin = DATA_STORE.get('margin_vs_upper_time', pd.DataFrame())
    df_score = DATA_STORE.get('optimization_score_time', pd.DataFrame())

    if not (_valid_df(df_surplus) and _valid_df(df_margin) and _valid_df(df_score)):
        return html.Div("最適化分析データが見つかりません。")

    surplus_df_renamed = df_surplus.copy()
    surplus_df_renamed.columns = [date_with_weekday(c) for c in surplus_df_renamed.columns]

    margin_df_renamed = df_margin.copy()
    margin_df_renamed.columns = [date_with_weekday(c) for c in margin_df_renamed.columns]

    score_df_renamed = df_score.copy()
    score_df_renamed.columns = [date_with_weekday(c) for c in score_df_renamed.columns]

    content = [
        html.Div([
            html.H4("1. 必要人数に対する余剰 (Surplus vs Need)"),
            html.P("各時間帯で必要人数（need）に対して何人多くスタッフがいたかを示します。"),
            dcc.Graph(
                figure=px.imshow(
                    surplus_df_renamed,
                    aspect='auto',
                    color_continuous_scale='Blues',
                    title='必要人数に対する余剰人員ヒートマップ',
                    labels={'x': '日付', 'y': '時間', 'color': '余剰人数'},
                ).update_xaxes(tickvals=list(range(len(df_surplus.columns))))
            ),
        ]),
        html.Div([
            html.H4("2. 上限に対する余白 (Margin to Upper)", style={'marginTop': '30px'}),
            html.P("各時間帯で配置人数の上限（upper）まであと何人の余裕があったかを示します。"),
            dcc.Graph(
                figure=px.imshow(
                    margin_df_renamed,
                    aspect='auto',
                    color_continuous_scale='Greens',
                    title='上限人数までの余白ヒートマップ',
                    labels={'x': '日付', 'y': '時間', 'color': '余白人数'},
                ).update_xaxes(tickvals=list(range(len(df_margin.columns))))
            ),
        ]),
        html.Div([
            html.H4("3. 人員配置 最適化スコア", style={'marginTop': '30px'}),
            html.P("人員配置の効率性を0から1のスコアで示します（1が最も良い）。"),
            dcc.Graph(
                figure=px.imshow(
                    score_df_renamed,
                    aspect='auto',
                    color_continuous_scale='RdYlGn',
                    zmin=0,
                    zmax=1,
                    title='最適化スコア ヒートマップ',
                    labels={'x': '日付', 'y': '時間', 'color': 'スコア'},
                ).update_xaxes(tickvals=list(range(len(df_score.columns))))
            ),
        ]),
    ]

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
        style={'fontWeight': 'bold'},  # type: ignore
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
    Output('wage-input-container', 'children'),
    Input('cost-by-radio', 'value')
)
def update_wage_inputs(by_key):
    """単価入力欄を生成"""
    long_df = DATA_STORE.get('long_df')
    if long_df is None or long_df.empty or by_key not in long_df.columns:
        return html.P("単価設定のためのデータがありません。")

    unique_keys: list[str] = sorted(long_df[by_key].dropna().unique())
    inputs = []
    for key in unique_keys:
        inputs.append(html.Div([
            html.Label(f'時給: {key}'),
            dcc.Input(
                id={'type': 'wage-input', 'index': key},
                value=1500,
                type='number',
                debounce=True,
            )
        ], style={'padding': '5px', 'display': 'inline-block'}))
    return inputs


@app.callback(
    Output('dynamic-cost-graph', 'figure'),
    Input('cost-by-radio', 'value'),
    Input({'type': 'wage-input', 'index': ALL}, 'value'),
    State({'type': 'wage-input', 'index': ALL}, 'id'),
)
def update_dynamic_cost_graph(by_key, all_wages, all_wage_ids):
    """単価変更に応じてコストグラフを更新"""
    long_df = DATA_STORE.get('long_df')
    if long_df is None or long_df.empty or not all_wages:
        raise PreventUpdate

    wages = {
        wage_id['index']: (wage_val or 0) for wage_id, wage_val in zip(all_wage_ids, all_wages)
    }

    cost_df = calculate_daily_cost(long_df, wages, by=by_key)
    if cost_df.empty:
        return go.Figure().update_layout(title='コスト計算結果がありません')

    fig = px.bar(
        cost_df,
        x='date',
        y='cost',
        title=f'【シミュレーション】日別発生人件費 ({by_key}別単価)',
        labels={'date': '日付', 'cost': 'コスト(円)'},
    )
    fig.update_xaxes(tickformat='%m/%d(%a)')
    return fig


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

    heat_df = DATA_STORE.get('heat_ALL')
    short_df = DATA_STORE.get('shortage_time')
    leave_df = DATA_STORE.get('leave_analysis')

    if heat_df is None or heat_df.empty or short_df is None or short_df.empty:
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
    return html.Div([html.H5('影響度の高い要因 トップ5'), table])  # type: ignore


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
        return 'ログファイルパスが見つかりません'  # type: ignore

    df = pd.DataFrame(table_data)
    over_shortage_log.save_log(df, log_path, mode=mode)
    return 'ログを保存しました'

# --- アプリケーション起動 ---
if __name__ == '__main__':
    app.run_server(debug=True, port=8050, host='127.0.0.1')
