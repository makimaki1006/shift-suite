"""
Dash アプリケーション: ヒートマップ表示とパフォーマンス最適化
"""

import logging
import pathlib
from functools import lru_cache

import dash
import numpy as np
import pandas as pd
import plotly.express as px
from dash import Input, Output, callback, dcc, html

from shift_suite.tasks.dashboard import load_leave_results_from_dir
from shift_suite.tasks.utils import date_with_weekday

log = logging.getLogger(__name__)

SUMMARY5_CONST = ["need", "upper", "staff", "lack", "excess"]

DATA_DIR = pathlib.Path(__file__).resolve().parents[1] / "out"

leave_results: dict[str, pd.DataFrame] = {}


def drop_summary_cols(df: pd.DataFrame) -> pd.DataFrame:
    """need / upper / staff / lack / excess を除外した DF を返す"""
    cols_to_check = df.columns.str.strip().str.lower()
    return df.loc[:, ~cols_to_check.isin(SUMMARY5_CONST)]


@lru_cache(maxsize=32)
def get_cached_heatmap_data(mode: str, zmax_val: float, zmode: str, data_hash: str):
    """Cache heatmap figure generation to avoid recomputation."""
    if mode == "raw":
        if zmode == "p90":
            zmax_val = RAW_ZMAX_P90
        elif zmode == "p95":
            zmax_val = RAW_ZMAX_P95
        elif zmode == "p99":
            zmax_val = RAW_ZMAX_P99

        slider_disabled = zmode != "manual"
        fig = px.imshow(
            heat_staff_data,
            aspect="auto",
            color_continuous_scale="Blues",
            zmin=0,
            zmax=zmax_val,
            labels=dict(x="日付", y="時間帯", color="配置人数"),
            x=[date_with_weekday(c) for c in heat_staff_data.columns],
            title="スタッフ配置ヒートマップ",
        )
        return fig, slider_disabled, zmax_val
    else:
        fig = px.imshow(
            ratio_calculated_df,
            aspect="auto",
            color_continuous_scale=px.colors.sequential.RdBu_r,
            zmin=0,
            zmax=2,
            labels=dict(x="日付", y="時間帯", color="充足率 (実績/必要)"),
            x=[date_with_weekday(c) for c in ratio_calculated_df.columns],
            title="充足率ヒートマップ",
        )
        return fig, True, zmax_val


try:
    heat_all_df = pd.read_parquet(DATA_DIR / "heat_ALL.parquet")
    need_series_for_ratio = heat_all_df["need"].replace(0, np.nan)

    heat_staff_data = drop_summary_cols(heat_all_df)
    ratio_calculated_df = heat_staff_data.div(need_series_for_ratio, axis=0).clip(
        lower=0, upper=2
    )

    data_hash = str(
        hash(
            str(heat_staff_data.values.tobytes())
            + str(ratio_calculated_df.values.tobytes())
        )
    )

    RAW_ZMAX_DEFAULT_CALC = 10.0
    RAW_ZMAX_P90 = RAW_ZMAX_DEFAULT_CALC
    RAW_ZMAX_P95 = RAW_ZMAX_DEFAULT_CALC
    RAW_ZMAX_P99 = RAW_ZMAX_DEFAULT_CALC

    if not heat_staff_data.empty:
        try:
            RAW_ZMAX_P90 = heat_staff_data.quantile(0.9).max()
            RAW_ZMAX_P95 = heat_staff_data.quantile(0.95).max()
            RAW_ZMAX_P99 = heat_staff_data.quantile(0.99).max()
        except Exception as e:
            log.warning("quantile計算エラー: %s", e)

    kpi_lack_h = None
    jain_index_val = None
    if (DATA_DIR / "shortage_role.parquet").exists():
        shortage_role_df = pd.read_parquet(DATA_DIR / "shortage_role.parquet")
    else:
        shortage_role_df = pd.DataFrame()

    if (DATA_DIR / "fairness_before.parquet").exists():
        try:
            fairness_before_df = pd.read_parquet(DATA_DIR / "fairness_before.parquet")
            if (
                not fairness_before_df.empty
                and "jain_index" in fairness_before_df.columns
            ):
                jain_index_val = fairness_before_df["jain_index"].iloc[0]
        except Exception as e:
            log.error("fairness_before.parquet 読込エラー: %s", e)

    leave_results = load_leave_results_from_dir(DATA_DIR)
    shortage_time_df = (
        pd.read_parquet(DATA_DIR / "shortage_time.parquet")
        if (DATA_DIR / "shortage_time.parquet").exists()
        else pd.DataFrame()
    )
    shortage_ratio_df = (
        pd.read_parquet(DATA_DIR / "shortage_ratio.parquet")
        if (DATA_DIR / "shortage_ratio.parquet").exists()
        else pd.DataFrame()
    )

except Exception as e:
    logging.error(f"Data loading error: {e}")
    heat_all_df = pd.DataFrame()
    heat_staff_data = pd.DataFrame()
    ratio_calculated_df = pd.DataFrame()
    shortage_time_df = pd.DataFrame()
    shortage_ratio_df = pd.DataFrame()
    shortage_role_df = pd.DataFrame()
    data_hash = "empty"
    RAW_ZMAX_DEFAULT_CALC = 10.0
    RAW_ZMAX_P90 = RAW_ZMAX_DEFAULT_CALC
    RAW_ZMAX_P95 = RAW_ZMAX_DEFAULT_CALC
    RAW_ZMAX_P99 = RAW_ZMAX_DEFAULT_CALC
    kpi_lack_h = None
    jain_index_val = None
    leave_results = {}

app = dash.Dash(__name__)


def page_overview():
    return html.Div(
        [
            html.H2("概要"),
            html.P("このダッシュボードでは、シフト分析の結果を表示します。"),
            html.Ul(
                [
                    html.Li("ヒートマップ: スタッフ配置状況を可視化"),
                    html.Li("不足分析: 時間帯別の人員不足状況"),
                    html.Li("休暇分析: 休暇取得パターンの分析"),
                ]
            ),
            html.Hr(),
            html.P("データ読み込み状況:"),
            html.Ul(
                [
                    html.Li(
                        f"ヒートマップデータ: {'✓' if not heat_staff_data.empty else '✗'}"
                    ),
                    html.Li(
                        f"不足データ: {'✓' if not shortage_time_df.empty else '✗'}"
                    ),
                    html.Li(f"休暇データ: {'✓' if leave_results else '✗'}"),
                ]
            ),
            html.P(
                f"Jain Index: {jain_index_val:.3f}"
                if jain_index_val is not None
                else "Jain Index: N/A"
            ),
        ]
    )


def page_heat():
    return html.Div(
        [
            html.H2("ヒートマップ"),
            html.Div(
                [
                    html.Label("表示モード:"),
                    dcc.RadioItems(
                        id="hm-mode-radio",
                        options=[
                            {"label": "Raw Count", "value": "raw"},
                            {"label": "Ratio (staff ÷ need)", "value": "ratio"},
                        ],
                        value="raw",
                        inline=True,
                    ),
                ],
                style={"margin": "10px"},
            ),
            html.Div(
                [
                    html.Label("Z軸最大値モード:"),
                    dcc.RadioItems(
                        id="hm-zmax-mode",
                        options=[
                            {"label": "Manual", "value": "manual"},
                            {"label": "P90", "value": "p90"},
                            {"label": "P95", "value": "p95"},
                            {"label": "P99", "value": "p99"},
                        ],
                        value="p90",
                        inline=True,
                    ),
                ],
                style={"margin": "10px"},
            ),
            html.Div(
                [
                    html.Label("Z軸最大値 (Manual時のみ有効):"),
                    dcc.Slider(
                        id="hm-zmax-slider",
                        min=1,
                        max=50,
                        step=1,
                        value=10,
                        marks={i: str(i) for i in range(0, 51, 10)},
                        disabled=True,
                    ),
                ],
                style={"margin": "10px"},
            ),
            dcc.Graph(id="hm-main-graph"),
        ]
    )


def page_shortage():
    return html.Div(
        [
            html.H2("不足分析"),
            html.Div(
                [
                    html.Label("日付選択:"),
                    dcc.Dropdown(
                        id="hm-shortage-date-dropdown",
                        options=[
                            {"label": col, "value": col}
                            for col in shortage_time_df.columns
                        ]
                        if not shortage_time_df.empty
                        else [],
                        value=shortage_time_df.columns[0]
                        if not shortage_time_df.empty
                        else None,
                        placeholder="日付を選択してください",
                    ),
                ],
                style={"margin": "10px"},
            ),
            dcc.Graph(id="hm-shortage-bar-graph"),
            html.Hr(),
            html.H3("不足率"),
            html.Div(
                [
                    html.Label("日付選択:"),
                    dcc.Dropdown(
                        id="shortage-ratio-date-dropdown",
                        options=[
                            {"label": col, "value": col}
                            for col in shortage_ratio_df.columns
                        ]
                        if not shortage_ratio_df.empty
                        else [],
                        value=shortage_ratio_df.columns[0]
                        if not shortage_ratio_df.empty
                        else None,
                        placeholder="日付を選択してください",
                    ),
                ],
                style={"margin": "10px"},
            ),
            dcc.Graph(id="shortage-ratio-bar-graph"),
        ]
    )


def page_leave():
    if not leave_results:
        return html.Div(
            [
                html.H2("休暇分析"),
                html.P("休暇データが見つかりません。"),
            ]
        )

    leave_tabs = []
    for key, df in leave_results.items():
        if df.empty:
            continue
        leave_tabs.append(
            dcc.Tab(
                label=key,
                children=[
                    html.Div(
                        [
                            html.H3(f"休暇分析: {key}"),
                            html.P(f"データ件数: {len(df)}"),
                            html.P("詳細な分析結果をここに表示予定"),
                        ]
                    )
                ],
            )
        )

    if not leave_tabs:
        return html.Div(
            [
                html.H2("休暇分析"),
                html.P("有効な休暇データが見つかりません。"),
            ]
        )

    return html.Div(
        [
            html.H2("休暇分析"),
            dcc.Tabs(children=leave_tabs),
        ]
    )


app.layout = html.Div(
    [
        html.H1("シフト分析ダッシュボード", style={"textAlign": "center"}),
        dcc.Tabs(
            id="main-tabs",
            value="overview",
            children=[
                dcc.Tab(label="概要", value="overview"),
                dcc.Tab(label="ヒートマップ", value="heat"),
                dcc.Tab(label="不足分析", value="shortage"),
                dcc.Tab(label="休暇分析", value="leave"),
            ],
        ),
        html.Div(id="tab-content"),
    ]
)


@callback(
    Output("tab-content", "children"),
    Input("main-tabs", "value"),
    prevent_initial_call=False,
)
def router(active_tab: str):
    if active_tab == "overview":
        return page_overview()
    elif active_tab == "heat":
        return page_heat()
    elif active_tab == "shortage":
        return page_shortage()
    elif active_tab == "leave":
        return page_leave()
    return html.Div("Unknown tab")


@callback(
    Output("hm-main-graph", "figure"),
    Output("hm-zmax-slider", "disabled"),
    Output("hm-zmax-slider", "value"),
    Input("hm-mode-radio", "value"),
    Input("hm-zmax-slider", "value"),
    Input("hm-zmax-mode", "value"),
    prevent_initial_call=False,
)
def update_heatmap(mode: str, zmax_val: float, zmode: str):
    if heat_staff_data.empty and mode == "raw":
        return px.imshow(pd.DataFrame()), True, zmax_val
    if ratio_calculated_df.empty and mode == "ratio":
        return px.imshow(pd.DataFrame()), True, zmax_val

    try:
        return get_cached_heatmap_data(mode, zmax_val, zmode, data_hash)
    except Exception as e:
        logging.error(f"Heatmap generation error: {e}")
        return px.imshow(pd.DataFrame()), True, zmax_val


@callback(
    Output("hm-shortage-bar-graph", "figure"),
    Input("hm-shortage-date-dropdown", "value"),
    prevent_initial_call=False,
)
def update_shortage_bar(selected_date_str: str | None):
    if (
        selected_date_str is None
        or shortage_time_df.empty
        or selected_date_str not in shortage_time_df.columns
    ):
        fig_empty = px.bar(title="日付を選択してください")
        fig_empty.update_layout(showlegend=False, height=300)
        return fig_empty

    series_data = shortage_time_df[selected_date_str]
    fig = px.bar(
        x=series_data.index,
        y=series_data.values,
        labels={"x": "時間帯", "y": "不足人数"},
        title=f"{selected_date_str} の時間帯別不足人数",
    )
    fig.update_layout(showlegend=False, xaxis_tickangle=-45, height=350)
    return fig


@callback(
    Output("shortage-ratio-bar-graph", "figure"),
    Input("shortage-ratio-date-dropdown", "value"),
    prevent_initial_call=False,
)
def update_shortage_ratio_bar(date_str: str | None):
    if (
        date_str is None
        or shortage_ratio_df.empty
        or date_str not in shortage_ratio_df.columns
    ):
        fig_empty = px.bar(title="日付を選択してください")
        fig_empty.update_layout(showlegend=False, height=300)
        return fig_empty
    series = shortage_ratio_df[date_str]
    fig = px.bar(
        x=series.index,
        y=series.values,
        labels={"x": "時間帯", "y": "不足率"},
        title=f"{date_str} の時間帯別不足率",
    )
    fig.update_layout(showlegend=False, xaxis_tickangle=-45, height=350)
    return fig


if __name__ == "__main__":
    app.run_server(debug=True, port=8055)
