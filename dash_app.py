"""
dash_app.py  – summary5 列を完全除外したダッシュ版
────────────────────────────────────────────────────────
v2025-05-06
* Heatmap Raw / Ratio 表示で summary5 を除外
* 共通関数 drop_summary_cols(df) を導入
* 他ページ(Shortage 他)の雛形はそのまま
"""

from __future__ import annotations
import pathlib, json

import dash
import pandas as pd
import plotly.express as px
from dash import dcc, html, Input, Output, callback

# ────────────────── 1. 定数 & ヘルパ ──────────────────
DATA_DIR = pathlib.Path(__file__).parents[1] / "out"

SUMMARY5 = {"need", "upper", "staff", "lack", "excess"}


def drop_summary_cols(df: pd.DataFrame) -> pd.DataFrame:
    """need / upper / staff / lack / excess を除外した DF を返す"""
    cols = df.columns.str.strip().str.lower()
    return df.loc[:, ~cols.isin(SUMMARY5)]


# ────────────────── 2. データロード ──────────────────
heat_all = pd.read_excel(DATA_DIR / "heat_ALL.xlsx", index_col=0)
need_ser = heat_all["need"].replace(0, 1)

# ★ summary5 を完全除去
heat_staff = drop_summary_cols(heat_all)

ratio_df = (heat_staff / need_ser.values[:, None]).clip(upper=2)

# Raw 表示の自動上限 (95% 分位を下限 10・上限 50 でクリップ)
RAW_ZMAX_DEFAULT = float(heat_staff[heat_staff > 0].stack().quantile(0.95))
RAW_ZMAX_DEFAULT = max(10, min(50, RAW_ZMAX_DEFAULT))

shortage_time = pd.read_excel(DATA_DIR / "shortage_time.xlsx", index_col=0)
shortage_role = pd.read_excel(DATA_DIR / "shortage_role.xlsx")
fair_before = pd.read_excel(DATA_DIR / "fairness_before.xlsx")
fair_after = pd.read_excel(DATA_DIR / "fairness_after.xlsx")
fatigue_df = pd.read_excel(DATA_DIR / "fatigue_score.xlsx")
skill_df = pd.read_excel(DATA_DIR / "skill_matrix.xlsx", index_col=0)
forecast_df = pd.read_excel(DATA_DIR / "forecast.xlsx", index_col=0)
with open(DATA_DIR / "forecast.json") as f:
    forecast_meta = json.load(f)
anomaly_df = pd.read_excel(DATA_DIR / "anomaly_days.xlsx")
cluster_df = pd.read_excel(DATA_DIR / "staff_cluster.xlsx")
stats_sheets = pd.read_excel(DATA_DIR / "stats.xlsx", sheet_name=None)

# ────────────────── 3. Dash App ──────────────────
app = dash.Dash(__name__, suppress_callback_exceptions=True, title="ShiftSuite")
server = app.server

NAV = html.Div(
    [
        dcc.Link("Overview", href="/", className="nav"),
        dcc.Link("Heatmap", href="/heat", className="nav"),
        dcc.Link("Shortage", href="/short", className="nav"),
        dcc.Link("Fairness", href="/fair", className="nav"),
        dcc.Link("Fatigue/Skill", href="/fat", className="nav"),
        dcc.Link("Forecast", href="/fcst", className="nav"),
        dcc.Link("Anomaly", href="/anom", className="nav"),
        dcc.Link("Cluster", href="/clu", className="nav"),
        dcc.Link("Stats", href="/stats", className="nav"),
    ],
    style={"display": "flex", "gap": "1rem", "marginBottom": "1rem"},
)

app.layout = html.Div([dcc.Location(id="url"), NAV, html.Div(id="page")])

# ─────────── 4. ページレイアウト (雛形) ───────────
def page_overview():
    return html.Div("TODO: KPI カード")

def page_heat():
    return html.Div(
        [
            html.Div(
                [
                    dcc.RadioItems(
                        id="hm-mode",
                        options=[
                            {"label": "Raw 人数", "value": "raw"},
                            {"label": "Ratio (staff ÷ need)", "value": "ratio"},
                        ],
                        value="raw",
                        inline=True,
                        style={"marginRight": "2rem"},
                    ),
                    dcc.Slider(
                        id="hm-zmax",
                        min=10,
                        max=50,
                        step=5,
                        value=RAW_ZMAX_DEFAULT,
                        tooltip={"placement": "bottom"},
                    ),
                ],
                style={"display": "flex", "alignItems": "center"},
            ),
            dcc.Graph(id="hm-graph"),
            html.Hr(),
            dcc.Dropdown(
                id="hm-date",
                options=[{"label": d, "value": d} for d in shortage_time.columns],
                value=shortage_time.columns[0],
                style={"width": "240px"},
            ),
            dcc.Graph(id="hm-short"),
        ]
    )

def page_shortage(): return html.Div("TODO: shortage")
def page_fair():     return html.Div("TODO: fairness")
def page_fat():      return html.Div("TODO: fatigue / skill")
def page_forecast(): return html.Div("TODO: forecast")
def page_anom():     return html.Div("TODO: anomaly")
def page_clu():      return html.Div("TODO: cluster")
def page_stats():    return html.Div("TODO: stats")

# ─────────── 5. ルーティング ───────────
@callback(Output("page", "children"), Input("url", "pathname"))
def router(path):
    if path == "/heat": return page_heat()
    if path == "/short": return page_shortage()
    if path == "/fair": return page_fair()
    if path == "/fat": return page_fat()
    if path == "/fcst": return page_forecast()
    if path == "/anom": return page_anom()
    if path == "/clu": return page_clu()
    if path == "/stats": return page_stats()
    return page_overview()

# ─────────── 6. Heatmap コールバック ───────────
@callback(
    Output("hm-graph", "figure"),
    Output("hm-zmax", "disabled"),
    Input("hm-mode", "value"),
    Input("hm-zmax", "value"),
)
def update_heatmap(mode: str, zmax: float):
    if mode == "raw":
        fig = px.imshow(
            heat_staff,
            aspect="auto",
            color_continuous_scale="Blues",
            zmin=0,
            zmax=zmax,
            labels=dict(x="Date", y="Time", color="人数"),
        )
        return fig, False

    # Ratio
    fig = px.imshow(
        ratio_df,
        aspect="auto",
        color_continuous_scale=px.colors.sequential.RdBu_r,
        zmin=0,
        zmax=2,
        labels=dict(x="Date", y="Time", color="staff / need"),
    )
    return fig, True

@callback(Output("hm-short", "figure"), Input("hm-date", "value"))
def update_shortage_bar(date: str):
    ser = shortage_time[date]
    fig = px.bar(
        x=ser.index,
        y=ser.values,
        labels={"x": "Time", "y": "不足人数"},
        template="plotly_dark",
    )
    fig.update_layout(showlegend=False, xaxis_tickangle=-90, height=300)
    return fig

# ─────────── 7. Main ───────────
if __name__ == "__main__":
    app.run_server(debug=True, port=8055)
