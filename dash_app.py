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
import pathlib, json

import dash
import pandas as pd
import plotly.express as px
from dash import dcc, html, Input, Output, callback
import numpy as np # ★ 追加: np.nan のため

# ────────────────── 1. 定数 & ヘルパ ──────────────────
DATA_DIR = pathlib.Path(__file__).resolve().parents[1] / "out" # ★ .resolve() を追加

SUMMARY5_CONST = {"need", "upper", "staff", "lack", "excess"} # ★ SUMMARY5 -> SUMMARY5_CONST に変更 (app.pyと合わせる)


def drop_summary_cols(df: pd.DataFrame) -> pd.DataFrame:
    """need / upper / staff / lack / excess を除外した DF を返す"""
    cols_to_check = df.columns.str.strip().str.lower() # ★ 変数名変更
    return df.loc[:, ~cols_to_check.isin(SUMMARY5_CONST)]


# ────────────────── 2. データロード (エラーハンドリングを少し追加) ──────────────────
try:
    heat_all_df = pd.read_excel(DATA_DIR / "heat_ALL.xlsx", index_col=0) # ★ 変数名変更
    # need_ser は ratio_df 計算にのみ使用
    need_series_for_ratio = heat_all_df["need"].replace(0, np.nan) # ★ 変数名変更, 0をnanに(0除算対策)

    heat_staff_data = drop_summary_cols(heat_all_df) # ★ 変数名変更

    # ratio_df の計算: heat_staff_data (日付列のみ) を need_series_for_ratio で割る
    # heat_staff_data の各列に対して、対応する行(時間帯)のneedで割る
    ratio_calculated_df = heat_staff_data.div(need_series_for_ratio, axis=0).clip(lower=0, upper=2) # ★ clipにlower=0追加, 変数名変更

    RAW_ZMAX_DEFAULT_CALC = 10.0 # デフォルト値を設定
    if not heat_staff_data.empty: # 空でない場合のみ計算
        positive_values = heat_staff_data[heat_staff_data > 0].stack()
        if not positive_values.empty:
            RAW_ZMAX_DEFAULT_CALC = float(positive_values.quantile(0.95))
            RAW_ZMAX_DEFAULT_CALC = max(10.0, min(50.0, RAW_ZMAX_DEFAULT_CALC)) # ★ .0 を追加してfloatに
    
    # 他のファイルも存在チェックをしてから読み込むようにする (オプション)
    shortage_time_df = pd.read_excel(DATA_DIR / "shortage_time.xlsx", index_col=0) if (DATA_DIR / "shortage_time.xlsx").exists() else pd.DataFrame()
    # ... (他のファイルのロードも同様に if exists() を追加推奨)

except FileNotFoundError:
    print(f"エラー: {DATA_DIR / 'heat_ALL.xlsx'} が見つかりません。先にstreamlit app.pyで解析を実行してください。")
    # Dashアプリ起動前に終了させるか、エラーメッセージを表示するコンポーネントを返す
    heat_all_df = pd.DataFrame() # 空のDFで初期化
    heat_staff_data = pd.DataFrame()
    ratio_calculated_df = pd.DataFrame()
    RAW_ZMAX_DEFAULT_CALC = 10.0
    shortage_time_df = pd.DataFrame()
    # ... (他のDFも空で初期化)
except Exception as e:
    print(f"データロード中に予期せぬエラーが発生しました: {e}")
    heat_all_df = pd.DataFrame(); heat_staff_data = pd.DataFrame(); ratio_calculated_df = pd.DataFrame(); RAW_ZMAX_DEFAULT_CALC = 10.0; shortage_time_df = pd.DataFrame()


# ────────────────── 3. Dash App ──────────────────
app = dash.Dash(__name__, suppress_callback_exceptions=True, title="ShiftSuite Dashboard") # ★ title変更
server = app.server

NAV = html.Div(
    [
        dcc.Link("Overview", href="/", className="nav-link me-2"), # ★ class変更 (Bootstrap風)
        dcc.Link("Heatmap", href="/heat", className="nav-link me-2"),
        dcc.Link("Shortage", href="/short", className="nav-link me-2"),
        # ... (他のナビゲーションリンクも同様に)
    ],
    className="d-flex flex-wrap p-2 bg-light border-bottom", # ★ Bootstrapクラス追加
)

app.layout = html.Div([
    dcc.Location(id="url", refresh=False), # refresh=False はデフォルト
    NAV,
    html.Div(id="page-content", className="container-fluid p-3") # ★ id変更, Bootstrapクラス追加
])

# ─────────── 4. ページレイアウト (雛形) ───────────
def page_overview():
    return html.H3("Overview Page - TODO: KPI Cards") # ★ 少し具体的に

def page_heat():
    if heat_staff_data.empty: # ★ データロード失敗時の表示
        return html.Div([
            html.H4("Heatmap Data Not Found"),
            html.P("Please run the analysis via the Streamlit app first and ensure 'out/heat_ALL.xlsx' exists.")
        ])

    return html.Div(
        [
            html.Div(
                [
                    dcc.RadioItems(
                        id="hm-mode-radio", # ★ id変更 (他のhm-modeと区別)
                        options=[
                            {"label": "Raw 人数", "value": "raw"},
                            {"label": "Ratio (staff ÷ need)", "value": "ratio"},
                        ],
                        value="raw",
                        inline=True,
                        className="me-3" # ★ Bootstrapクラス追加
                    ),
                    html.Label("カラースケール上限(zmax):", className="me-2"), # ★ ラベル追加
                    dcc.Slider(
                        id="hm-zmax-slider", # ★ id変更
                        min=5, # ★ min調整
                        max=50,
                        step=1, # ★ step調整
                        value=RAW_ZMAX_DEFAULT_CALC,
                        tooltip={"placement": "bottom", "always_visible": True},
                        className="flex-grow-1" # ★ Bootstrapクラス追加
                    ),
                ],
                className="d-flex align-items-center mb-3 p-2 border rounded bg-light" # ★ Bootstrapクラス追加
            ),
            dcc.Graph(id="hm-main-graph"), # ★ id変更
            html.Hr(),
            html.H4("時間帯別不足人数 (選択日)", className="mt-3"), # ★ タイトル追加
            dcc.Dropdown(
                id="hm-shortage-date-dropdown", # ★ id変更
                options=[{"label": str(d), "value": str(d)} for d in shortage_time_df.columns] if not shortage_time_df.empty else [],
                value=str(shortage_time_df.columns[0]) if not shortage_time_df.empty and len(shortage_time_df.columns) > 0 else None,
                className="mb-2", # ★ Bootstrapクラス追加
                style={"width": "300px"}
            ),
            dcc.Graph(id="hm-shortage-bar-graph"), # ★ id変更
        ]
    )

# (他のページの雛形は省略。必要なら同様に調整)
def page_shortage(): return html.Div("TODO: shortage page content") 
# ...

# ─────────── 5. ルーティング ───────────
@callback(Output("page-content", "children"), Input("url", "pathname")) # ★ Output id変更
def router(path):
    if path == "/heat": return page_heat()
    if path == "/short": return page_shortage()
    # ... (他のルート)
    return page_overview()

# ─────────── 6. Heatmap コールバック ───────────
@callback(
    Output("hm-main-graph", "figure"), # ★ id変更
    Output("hm-zmax-slider", "disabled"), # ★ id変更
    Input("hm-mode-radio", "value"), # ★ id変更
    Input("hm-zmax-slider", "value"), # ★ id変更
)
def update_heatmap(mode: str, zmax_val: float): # ★ 引数名変更
    if heat_staff_data.empty and mode == "raw": # ★ データなしの場合のフォールバック
        return px.imshow(pd.DataFrame()), True # 空のグラフとスライダー無効化
    if ratio_calculated_df.empty and mode == "ratio":
        return px.imshow(pd.DataFrame()), True

    if mode == "raw":
        # ★カラースキーム変更 (Raw人数)
        fig = px.imshow(
            heat_staff_data, # SUMMARY5除去済みデータを使用
            aspect="auto",
            color_continuous_scale="YlOrRd", # "Blues" から "YlOrRd" に変更
            zmin=0,
            zmax=zmax_val,
            labels=dict(x="日付", y="時間帯", color="配置人数"), # ★ ラベル日本語化
        )
        return fig, False # スライダー有効

    # Ratio モード
    fig = px.imshow(
        ratio_calculated_df, # 計算済みRatioデータを使用
        aspect="auto",
        color_continuous_scale=px.colors.sequential.RdBu_r, # 変更なし
        zmin=0,
        zmax=2, # Ratioモードのデフォルトzmaxは2 (固定、スライダーは無効化)
        labels=dict(x="日付", y="時間帯", color="充足率 (実績/必要)"), # ★ ラベル日本語化
    )
    return fig, True # スライダー無効


@callback(
    Output("hm-shortage-bar-graph", "figure"), # ★ id変更
    Input("hm-shortage-date-dropdown", "value") # ★ id変更
)
def update_shortage_bar(selected_date_str: str | None): # ★ 引数名変更、型ヒント追加
    if selected_date_str is None or shortage_time_df.empty or selected_date_str not in shortage_time_df.columns:
        # データがない場合や日付が選択されていない場合は空のグラフを返す
        fig_empty = px.bar(title="日付を選択してください")
        fig_empty.update_layout(showlegend=False, height=300)
        return fig_empty

    series_data = shortage_time_df[selected_date_str] # ★ 変数名変更
    fig = px.bar(
        x=series_data.index,
        y=series_data.values,
        labels={"x": "時間帯", "y": "不足人数"}, # ★ ラベル日本語化
        title=f"{selected_date_str} の時間帯別不足人数" # ★ タイトル追加
        # template="plotly_dark", # ダークテーマはオプション
    )
    fig.update_layout(showlegend=False, xaxis_tickangle=-45, height=350) # ★ tickangle調整, height調整
    return fig

# ────────────────── 7. Main ──────────────────
if __name__ == "__main__":
    # 開発時のポート指定など
    app.run_server(debug=True, port=8055)
