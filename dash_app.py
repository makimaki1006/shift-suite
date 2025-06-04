"""
dash_app.py  – summary5 列を完全除外したダッシュ版
────────────────────────────────────────────────────────
v2025-05-16 (カラースキーム変更)
* Heatmap Raw 表示で summary5 を除外 (既存)
* 共通関数 drop_summary_cols(df) を導入 (既存)
* Heatmap Raw 表示のカラースキームを "YlOrRd" に変更
* 他ページ(Shortage 他)の雛形はそのまま
"""

from __future__ import annotations
import pathlib

import dash
import pandas as pd
import plotly.express as px
from dash import dcc, html, Input, Output, callback
import numpy as np  # ★ 追加: np.nan のため
import logging
from shift_suite.tasks.constants import SUMMARY5 as SUMMARY5_CONST

# --- 簡易日本語ラベル辞書 -----------------------------------------------
JP = {
    "Overview": "概要",
    "Heatmap": "ヒートマップ",
    "Shortage": "不足分析",
    "Heatmap Data Not Found": "ヒートマップデータが見つかりません",
    "Please run the analysis via the Streamlit app first and ensure 'out/heat_ALL.xlsx' exists.": "Streamlit app.py を先に実行し 'out/heat_ALL.xlsx' を生成してください。",
    "Shortage Ratio Data Not Found": "不足率データが見つかりません",
    "Run analysis via the Streamlit app to generate shortage_ratio.xlsx": "Streamlit app で解析を実行し shortage_ratio.xlsx を生成してください",
    "Shortage Ratio Heatmap": "不足率ヒートマップ",
    "Time Slot Shortage Ratio": "時間帯別不足率",
    "Date": "日付",
    "Time": "時間帯",
    "Shortage Ratio": "不足率",
    "Manual": "手動",
    "90th %tile": "90パーセンタイル",
    "95th %tile": "95パーセンタイル",
    "99th %tile": "99パーセンタイル",
}


def _(text: str) -> str:
    """Translate ``text`` using ``JP`` dictionary."""
    return JP.get(text, text)

logger = logging.getLogger(__name__)

# ────────────────── 1. 定数 & ヘルパ ──────────────────
DATA_DIR = pathlib.Path(__file__).resolve().parents[1] / "out"  # ★ .resolve() を追加


def drop_summary_cols(df: pd.DataFrame) -> pd.DataFrame:
    """need / upper / staff / lack / excess を除外した DF を返す"""
    cols_to_check = df.columns.str.strip().str.lower()  # ★ 変数名変更
    return df.loc[:, ~cols_to_check.isin(SUMMARY5_CONST)]


# ────────────────── 2. データロード (エラーハンドリングを少し追加) ──────────────────
try:
    heat_all_df = pd.read_excel(DATA_DIR / "heat_ALL.xlsx", index_col=0)
    need_series_for_ratio = heat_all_df["need"].replace(0, np.nan)

    heat_staff_data = drop_summary_cols(heat_all_df)
    ratio_calculated_df = heat_staff_data.div(need_series_for_ratio, axis=0).clip(
        lower=0, upper=2
    )

    RAW_ZMAX_DEFAULT_CALC = 10.0
    RAW_ZMAX_P90 = RAW_ZMAX_DEFAULT_CALC
    RAW_ZMAX_P95 = RAW_ZMAX_DEFAULT_CALC
    RAW_ZMAX_P99 = RAW_ZMAX_DEFAULT_CALC
    if not heat_staff_data.empty:
        positive_values = heat_staff_data[heat_staff_data > 0].stack()
        if not positive_values.empty:
            RAW_ZMAX_P90 = float(positive_values.quantile(0.90))
            RAW_ZMAX_P95 = float(positive_values.quantile(0.95))
            RAW_ZMAX_P99 = float(positive_values.quantile(0.99))
            RAW_ZMAX_DEFAULT_CALC = max(10.0, min(50.0, RAW_ZMAX_P95))

    shortage_time_df = (
        pd.read_excel(DATA_DIR / "shortage_time.xlsx", index_col=0)
        if (DATA_DIR / "shortage_time.xlsx").exists()
        else pd.DataFrame()
    )
    shortage_ratio_df = (
        pd.read_excel(DATA_DIR / "shortage_ratio.xlsx", index_col=0)
        if (DATA_DIR / "shortage_ratio.xlsx").exists()
        else pd.DataFrame()
    )
    kpi_lack_h = None
    jain_index_val = None
    if (DATA_DIR / "shortage_role.xlsx").exists():
        try:
            df_sr = pd.read_excel(DATA_DIR / "shortage_role.xlsx")
            if "lack_h" in df_sr:
                kpi_lack_h = float(df_sr["lack_h"].sum())
        except Exception as e:
            logger.error("shortage_role.xlsx 読込エラー: %s", e)
    if (DATA_DIR / "fairness_before.xlsx").exists():
        try:
            df_fb = pd.read_excel(
                DATA_DIR / "fairness_before.xlsx", sheet_name="meta_summary"
            )
            row = df_fb[df_fb["metric"] == "jain_index"]
            if not row.empty:
                jain_index_val = float(row["value"].iloc[0])
        except Exception as e:
            logger.error("fairness_before.xlsx 読込エラー: %s", e)

except FileNotFoundError:
    logger.error(
        "エラー: %s が見つかりません。先にstreamlit app.pyで解析を実行してください。",
        DATA_DIR / "heat_ALL.xlsx",
    )
    # Dashアプリ起動前に終了させるか、エラーメッセージを表示するコンポーネントを返す
    heat_all_df = pd.DataFrame()  # 空のDFで初期化
    heat_staff_data = pd.DataFrame()
    ratio_calculated_df = pd.DataFrame()
    RAW_ZMAX_DEFAULT_CALC = 10.0
    shortage_time_df = pd.DataFrame()
    shortage_ratio_df = pd.DataFrame()
    # ... (他のDFも空で初期化)
except Exception as e:
    logger.error("データロード中に予期せぬエラーが発生しました: %s", e)
    heat_all_df = pd.DataFrame()
    heat_staff_data = pd.DataFrame()
    ratio_calculated_df = pd.DataFrame()
    RAW_ZMAX_DEFAULT_CALC = 10.0
    shortage_time_df = pd.DataFrame()
    shortage_ratio_df = pd.DataFrame()


# ────────────────── 3. Dash App ──────────────────
app = dash.Dash(
    __name__, suppress_callback_exceptions=True, title="ShiftSuite Dashboard"
)  # ★ title変更
server = app.server

NAV = html.Div(
    [
        dcc.Link(
            _("Overview"), href="/", className="nav-link me-2"
        ),  # ★ class変更 (Bootstrap風)
        dcc.Link(_("Heatmap"), href="/heat", className="nav-link me-2"),
        dcc.Link(_("Shortage"), href="/short", className="nav-link me-2"),
        # ... (他のナビゲーションリンクも同様に)
    ],
    className="d-flex flex-wrap p-2 bg-light border-bottom",  # ★ Bootstrapクラス追加
)

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),  # refresh=False はデフォルト
        NAV,
        html.Div(
            id="page-content", className="container-fluid p-3"
        ),  # ★ id変更, Bootstrapクラス追加
    ]
)


# ─────────── 4. ページレイアウト (雛形) ───────────
def page_overview():
    cards = []
    if kpi_lack_h is not None:
        cards.append(
            html.Div(
                [
                    html.H6("不足時間(h)", className="card-title"),
                    html.H2(f"{kpi_lack_h:.1f}", className="card-text"),
                ],
                className="card p-3 me-3",
            )
        )
    if jain_index_val is not None:
        cards.append(
            html.Div(
                [
                    html.H6("夜勤 Jain指数", className="card-title"),
                    html.H2(f"{jain_index_val:.3f}", className="card-text"),
                ],
                className="card p-3 me-3",
            )
        )
    if not cards:
        cards.append(html.Div("KPIデータがありません", className="p-3"))
    return html.Div([html.H3(_("Overview")), html.Div(cards, className="d-flex")])


def page_heat():
    if heat_staff_data.empty:  # ★ データロード失敗時の表示
        return html.Div(
            [
                html.H4(_("Heatmap Data Not Found")),
                html.P(
                    _(
                        "Please run the analysis via the Streamlit app first and ensure 'out/heat_ALL.xlsx' exists."
                    )
                ),
            ]
        )

    return html.Div(
        [
            html.Div(
                [
                    dcc.RadioItems(
                        id="hm-mode-radio",  # ★ id変更 (他のhm-modeと区別)
                        options=[
                            {"label": "Raw 人数", "value": "raw"},
                            {"label": "Ratio (staff ÷ need)", "value": "ratio"},
                        ],
                        value="raw",
                        inline=True,
                        className="me-3",  # ★ Bootstrapクラス追加
                    ),
                    dcc.Dropdown(
                        id="hm-zmax-mode",
                        options=[
                            {"label": _("Manual"), "value": "manual"},
                            {"label": _("90th %tile"), "value": "p90"},
                            {"label": _("95th %tile"), "value": "p95"},
                            {"label": _("99th %tile"), "value": "p99"},
                        ],
                        value="manual",
                        clearable=False,
                        style={"width": "150px"},
                        className="me-2",
                    ),
                    html.Label(
                        "カラースケール上限(zmax):", className="me-2"
                    ),  # ★ ラベル追加
                    dcc.Slider(
                        id="hm-zmax-slider",
                        min=5,
                        max=50,
                        step=1,
                        value=RAW_ZMAX_DEFAULT_CALC,
                        tooltip={"placement": "bottom", "always_visible": True},
                        className="flex-grow-1",
                        disabled=False,
                    ),
                ],
                className="d-flex align-items-center mb-3 p-2 border rounded bg-light",  # ★ Bootstrapクラス追加
            ),
            dcc.Graph(id="hm-main-graph"),  # ★ id変更
            html.Hr(),
            html.H4("時間帯別不足人数 (選択日)", className="mt-3"),  # ★ タイトル追加
            dcc.Dropdown(
                id="hm-shortage-date-dropdown",  # ★ id変更
                options=[
                    {"label": str(d), "value": str(d)} for d in shortage_time_df.columns
                ]
                if not shortage_time_df.empty
                else [],
                value=str(shortage_time_df.columns[0])
                if not shortage_time_df.empty and len(shortage_time_df.columns) > 0
                else None,
                className="mb-2",  # ★ Bootstrapクラス追加
                style={"width": "300px"},
            ),
            dcc.Graph(id="hm-shortage-bar-graph"),  # ★ id変更
        ]
    )


# (他のページの雛形は省略。必要なら同様に調整)
def page_shortage():
    if shortage_ratio_df.empty:
        return html.Div(
            [
                html.H4(_("Shortage Ratio Data Not Found")),
                html.P(
                    _(
                        "Run analysis via the Streamlit app to generate shortage_ratio.xlsx"
                    )
                ),
            ]
        )

    return html.Div(
        [
            html.H3(_("Shortage Ratio Heatmap")),
            dcc.Graph(
                id="shortage-ratio-heatmap",
                figure=px.imshow(
                    shortage_ratio_df,
                    aspect="auto",
                    color_continuous_scale=px.colors.sequential.OrRd,
                    zmin=0,
                    zmax=1,
                    labels=dict(x=_("Date"), y=_("Time"), color=_("Shortage Ratio")),
                ),
            ),
            html.Hr(),
            html.H4(_("Time Slot Shortage Ratio")),
            dcc.Dropdown(
                id="shortage-ratio-date-dropdown",
                options=[
                    {"label": str(d), "value": str(d)}
                    for d in shortage_ratio_df.columns
                ],
                value=str(shortage_ratio_df.columns[0])
                if len(shortage_ratio_df.columns) > 0
                else None,
                style={"width": "300px"},
                className="mb-2",
            ),
            dcc.Graph(id="shortage-ratio-bar-graph"),
        ]
    )


# ...


# ─────────── 5. ルーティング ───────────
@callback(
    Output("page-content", "children"), Input("url", "pathname")
)  # ★ Output id変更
def router(path):
    if path == "/heat":
        return page_heat()
    if path == "/short":
        return page_shortage()
    # ... (他のルート)
    return page_overview()


# ─────────── 6. Heatmap コールバック ───────────
@callback(
    Output("hm-main-graph", "figure"),
    Output("hm-zmax-slider", "disabled"),
    Output("hm-zmax-slider", "value"),
    Input("hm-mode-radio", "value"),
    Input("hm-zmax-slider", "value"),
    Input("hm-zmax-mode", "value"),
)
def update_heatmap(mode: str, zmax_val: float, zmode: str):
    if heat_staff_data.empty and mode == "raw":  # ★ データなしの場合のフォールバック
        return px.imshow(pd.DataFrame()), True, zmax_val
    if ratio_calculated_df.empty and mode == "ratio":
        return px.imshow(pd.DataFrame()), True, zmax_val

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
        )
        return fig, slider_disabled, zmax_val

    # Ratio モード
    fig = px.imshow(
        ratio_calculated_df,  # 計算済みRatioデータを使用
        aspect="auto",
        color_continuous_scale=px.colors.sequential.RdBu_r,  # 変更なし
        zmin=0,
        zmax=2,  # Ratioモードのデフォルトzmaxは2 (固定、スライダーは無効化)
        labels=dict(
            x="日付", y="時間帯", color="充足率 (実績/必要)"
        ),  # ★ ラベル日本語化
    )
    return fig, True, zmax_val


@callback(
    Output("hm-shortage-bar-graph", "figure"),  # ★ id変更
    Input("hm-shortage-date-dropdown", "value"),  # ★ id変更
)
def update_shortage_bar(selected_date_str: str | None):  # ★ 引数名変更、型ヒント追加
    if (
        selected_date_str is None
        or shortage_time_df.empty
        or selected_date_str not in shortage_time_df.columns
    ):
        # データがない場合や日付が選択されていない場合は空のグラフを返す
        fig_empty = px.bar(title="日付を選択してください")
        fig_empty.update_layout(showlegend=False, height=300)
        return fig_empty

    series_data = shortage_time_df[selected_date_str]  # ★ 変数名変更
    fig = px.bar(
        x=series_data.index,
        y=series_data.values,
        labels={"x": "時間帯", "y": "不足人数"},  # ★ ラベル日本語化
        title=f"{selected_date_str} の時間帯別不足人数",  # ★ タイトル追加
        # template="plotly_dark", # ダークテーマはオプション
    )
    fig.update_layout(
        showlegend=False, xaxis_tickangle=-45, height=350
    )  # ★ tickangle調整, height調整
    return fig


@callback(
    Output("shortage-ratio-bar-graph", "figure"),
    Input("shortage-ratio-date-dropdown", "value"),
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


# ────────────────── 7. Main ──────────────────
if __name__ == "__main__":
    # 開発時のポート指定など
    app.run_server(debug=True, port=8055)
