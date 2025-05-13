# ─────────────────────────────  app.py  (Part 1 / 3)  ──────────────────────────
# Shift-Suite Streamlit GUI + 内蔵ダッシュボード  v1.27-hf
# ==============================================================================
# 変更履歴
#   • 2025-05-12  ingestion header_row hot-fix に追従
#   • 2025-05-11  master_sheet 概念を廃止し ingest_excel 新 API に準拠
#   • 末尾に CLI デバッグブロックを追加（Streamlit 実行時は無視）
# ==============================================================================

from __future__ import annotations

import datetime as dt
import io
import json
import re
import sys
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Shift-Suite task modules ─────────────────────────────────────────────────
from shift_suite.tasks.io_excel import ingest_excel
from shift_suite.tasks.heatmap import build_heatmap
from shift_suite.tasks.shortage import shortage_and_brief
from shift_suite.tasks.build_stats import build_stats
from shift_suite.tasks.anomaly import detect_anomaly
from shift_suite.tasks.fatigue import train_fatigue
from shift_suite.tasks.cluster import cluster_staff
from shift_suite.tasks.skill_nmf import build_skill_matrix
from shift_suite.tasks.fairness import run_fairness
from shift_suite.tasks.forecast import build_demand_series, forecast_need
from shift_suite.tasks.rl import learn_roster
from shift_suite.tasks.hire_plan import build_hire_plan
from shift_suite.tasks.cost_benefit import analyze_cost_benefit
from shift_suite.tasks.utils import calculate_jain_index, safe_make_archive

# ── 日本語ラベル辞書 & _() ───────────────────────────────────────────────────
JP = {
    # タブ
    "Overview": "概要",
    "Heatmap": "ヒートマップ",
    "Shortage": "不足分析",
    "Fatigue": "疲労",
    "Forecast": "需要予測",
    "Fairness": "公平性",
    "Cost Sim": "コスト試算",
    "Hire Plan": "採用計画",
    "PPT Report": "レポート",
    # サイドバー
    "Slot (min)": "スロット (分)",
    "Min-staff method": "最少人数の算出方法",
    "Extra modules": "追加モジュール",
    "保存方法": "保存方法",
    "ZIP ダウンロード": "ZIP ダウンロード",
    "フォルダに保存": "フォルダに保存",
    # Plotly labels
    "Date": "日付",
    "Time": "時間",
    "人数": "人数",
    "staff/need": "スタッフ÷必要数",
    "不足人数": "不足人数",
    "不足時間(h)": "不足時間 (h)",
    "職種": "職種",
    "Fatigue Score": "疲労スコア",
    "シフト回数": "シフト回数",
    "夜勤比率": "夜勤比率",
}
def _(text: str) -> str:
    """英語→日本語; 未登録なら原文を返す"""
    return JP.get(text, text)

# ───────────── Streamlit 全体設定 ────────────────────────────────────────────
st.set_page_config(page_title="Shift-Suite", layout="wide")
st.header("🗂  Shift-Suite 解析")

# ─────────── 左サイドバー（共通）─────────────────────────────────────────
slot = st.sidebar.number_input("Slot (min)", 5, 60, 30, 5)
min_method = st.sidebar.selectbox(
    "Min-staff method", ["mean-1s", "p25", "mode"], index=1
)
ext_opts = st.sidebar.multiselect(
    "Extra modules",
    [
        "Stats", "Anomaly", "Fatigue", "Cluster",
        "Skill", "Fairness", "Need forecast", "RL roster (PPO)",
        "Hire plan", "Cost / Benefit",
    ],
)
save_mode = st.sidebar.selectbox("保存方法", ["ZIP ダウンロード", "フォルダに保存"])

# ★ 新モジュール用パラメータ
with st.sidebar.expander("💰 Cost & Hire Parameters"):
    std_work_hours   = st.number_input("所定労働時間 (h/月)",   120, 200, 160, 4)
    safety_factor    = st.slider      ("安全係数（不足 h 上乗せ）", 1.00, 1.30, 1.10, 0.01)
    target_coverage  = st.slider      ("目標充足率", 0.80, 1.00, 0.95, 0.01)
    wage_direct      = st.number_input("正職員 人件費 (¥/h)",   800, 4000, 1500, 50)
    wage_temp        = st.number_input("派遣 人件費 (¥/h)",   1000, 6000, 2200, 50)
    hiring_cost_once = st.number_input("採用一時コスト (¥/人)", 0, 500000, 180_000, 10000)
    penalty_per_lack = st.number_input("不足ペナルティ (¥/h)", 0, 10000, 4000, 500)

# ─────────────── Excel 入力 ───────────────────────────────────────────────
uf = st.file_uploader("Excel シフト表 (*.xlsx)", type=["xlsx"])
if uf:
    work_root  = Path(tempfile.mkdtemp())
    excel_path = work_root / uf.name
    excel_path.write_bytes(uf.read())

    all_sheets = pd.ExcelFile(excel_path, engine="openpyxl").sheet_names
    shift_candidates = [s for s in all_sheets if "勤務区分" not in s]

    shift_sheets = st.sidebar.multiselect(
        "解析するシフトシート（複数可）",
        shift_candidates,
        default=shift_candidates,
    )
    header_row = st.sidebar.number_input(
        "ヘッダー開始行 (1-indexed)", 1, 10, 3, 1
    )

run = st.button("▶ 解析実行")
# ─────────────────────────────  app.py  (Part 2 / 3)  ──────────────────────────
# 1st フロー : Excel → out フォルダ
# ------------------------------------------------------------------------------
if run and uf:
    out_dir = work_root / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    # デバッグ表示（先頭 8 行）
    tmp_prev = pd.read_excel(excel_path, sheet_name=shift_sheets[0],
                             header=None, nrows=8)
    st.write("▼ 先頭 8 行プレビュー", tmp_prev)

    # 1/8  Ingest --------------------------------------------------------------
    st.info("1/8  Ingest …")
    long_df, wt_df = ingest_excel(
        excel_path,
        shift_sheets=shift_sheets,
        header_row=header_row,     # ← v2.4.4 で有効に
    )

    # 2/8  Heatmap -------------------------------------------------------------
    st.info("2/8  Heatmap …")
    build_heatmap(long_df, wt_df, out_dir, slot, min_method=min_method)

    # 3/8  Shortage ------------------------------------------------------------
    st.info("3/8  Shortage …")
    shortage_and_brief(out_dir, slot, min_method=min_method)

    # optional modules ---------------------------------------------------------
    if "Stats" in ext_opts:
        st.info("Stats …");          build_stats(out_dir)
    if "Anomaly" in ext_opts:
        st.info("Anomaly …");        detect_anomaly(out_dir)
    if "Fatigue" in ext_opts:
        st.info("Fatigue …");        train_fatigue(long_df, out_dir)
    if "Cluster" in ext_opts:
        st.info("Cluster …");        cluster_staff(long_df, out_dir)
    if "Skill" in ext_opts:
        st.info("Skill …");          build_skill_matrix(long_df, out_dir)
    if "Fairness" in ext_opts:
        st.info("Fairness …");       run_fairness(long_df, out_dir)
    if "Need forecast" in ext_opts:
        st.info("Forecast …")
        csv = build_demand_series(out_dir / "heat_ALL.xlsx",
                                  out_dir / "demand_series.csv")
        forecast_need(csv, out_dir / "forecast.xlsx", choose="auto")
    if "RL roster (PPO)" in ext_opts:
        st.info("RL roster …")
        learn_roster(out_dir / "demand_series.csv", out_dir / "rl_roster.xlsx")

    # Hire / Cost --------------------------------------------------------------
    if "Hire plan" in ext_opts:
        st.info("Hire plan …")
        build_hire_plan(
            out_dir / "demand_series.csv",
            out_dir / "hire_plan.xlsx",
            std_work_hours=std_work_hours,
            safety_factor=safety_factor,
            target_coverage=target_coverage,
        )
    if "Cost / Benefit" in ext_opts:
        st.info("Cost / Benefit …")
        analyze_cost_benefit(
            out_dir,
            wage_direct=wage_direct,
            wage_temp=wage_temp,
            hiring_cost_once=hiring_cost_once,
            penalty_per_lack_h=penalty_per_lack,
        )

    st.success("解析完了 🎉")

    # 出力方法 ---------------------------------------------------------------
    if save_mode == "フォルダに保存":
        st.write(f"出力先: `{out_dir}`")
    else:
        zip_p = work_root / "out.zip"
        safe_make_archive(out_dir, zip_p)
        st.download_button(
            "Download OUT.zip",
            data=zip_p.read_bytes(),
            file_name="out.zip",
            mime="application/zip",
        )

st.divider()

# ───────── 2nd フロー : out.zip → ダッシュボード ─────────────────────────────
st.header("📊 ダッシュボード (ZIP アップロード)")

zip_file = st.file_uploader(
    "out フォルダを ZIP 圧縮してアップロード", type=["zip"], key="dash_zip"
)
if zip_file:
    tmp_dir = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(io.BytesIO(zip_file.read())) as zf:
        zf.extractall(tmp_dir)
    try:
        out_dir = next(tmp_dir.rglob("heat_ALL.xlsx")).parent
    except StopIteration:
        st.error("heat_ALL.xlsx が ZIP に見つかりません")
        st.stop()

    tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
        ["Overview", "Heatmap", "Shortage", "Fatigue",
         "Forecast", "Fairness", "Cost Sim", "Hire Plan", "PPT Report"]
    )

    # ------------------------------------------------------------------ 0) Overview
    with tab0:
        kpi_fp = out_dir / "shortage_role.xlsx"
        lack_h = pd.read_excel(kpi_fp)["lack_h"].sum() if kpi_fp.exists() else 0
        fair_fp = out_dir / "fairness_after.xlsx"
        jain = (calculate_jain_index(pd.read_excel(fair_fp)["night_ratio"])
                if fair_fp.exists() else "–")
        c1, c2 = st.columns(2)
        c1.metric(_("不足時間(h)"), f"{lack_h:.1f}")
        c2.metric("夜勤 Jain", jain)

    # ------------------------------------------------------------- 1) Heatmap
    with tab1:
        heat_all = pd.read_excel(out_dir / "heat_ALL.xlsx", index_col=0)
        mode = st.radio("表示モード", ["Raw", "Ratio"], horizontal=True)
        zmax = st.slider("zmax", 1.0 if mode == "Ratio" else 10,
                         3.0 if mode == "Ratio" else 50,
                         1.5 if mode == "Ratio" else 11,
                         0.1 if mode == "Ratio" else 1)
        target = heat_all if mode == "Raw" else (
            heat_all.div(heat_all["need"]).clip(upper=2)
        )
        fig = px.imshow(
            target.drop(columns=["need","upper","staff","lack","excess"],
                        errors="ignore"),
            aspect="auto",
            color_continuous_scale=("Blues" if mode == "Raw"
                                    else px.colors.sequential.RdBu_r),
            zmax=zmax,
            labels=dict(x=_("Date"), y=_("Time"),
                        color=_("人数") if mode == "Raw" else _("staff/need")),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------- 2) Shortage
    with tab2:
        fp = out_dir / "shortage_role.xlsx"
        if fp.exists():
            df = pd.read_excel(fp)
            st.dataframe(df, use_container_width=True)
            st.bar_chart(df, x="role", y="lack_h")
        else:
            st.info("shortage_role.xlsx がありません")

    # ------------------------------------------------------------- 3) Fatigue
    with tab3:
        fp = out_dir / "fatigue_score.xlsx"
        st.dataframe(pd.read_excel(fp), use_container_width=True) if fp.exists() \
            else st.info("fatigue_score.xlsx がありません")

    # ------------------------------------------------------------- 4) Forecast
    with tab4:
        fc_fp = out_dir / "forecast.xlsx"
        if fc_fp.exists() and fc_fp.stat().st_size:
            fc = pd.read_excel(fc_fp)
            st.line_chart(fc, x="ds", y="yhat", use_container_width=True)
        else:
            st.info("forecast.xlsx がありません")

    # ------------------------------------------------------------- 5) Fairness
    with tab5:
        fp = out_dir / "fairness_after.xlsx"
        st.dataframe(pd.read_excel(fp), use_container_width=True) if fp.exists() \
            else st.info("fairness_after.xlsx がありません")

    # ------------------------------------------------------------- 6) Cost Sim
    with tab6:
        fp = out_dir / "cost_benefit.xlsx"
        if fp.exists():
            cb = pd.read_excel(fp, index_col=0)
            st.bar_chart(cb["Cost_Million"])
            st.dataframe(cb, use_container_width=True)
        else:
            st.info("cost_benefit.xlsx がありません")

    # ------------------------------------------------------------- 7) Hire Plan
    with tab7:
        fp = out_dir / "hire_plan.xlsx"
        if fp.exists():
            hp = pd.read_excel(fp, sheet_name="hire_plan")
            st.dataframe(hp, use_container_width=True)
        else:
            st.info("hire_plan.xlsx がありません")

    # ------------------------------------------------------------- 8) PPT Export
    with tab8:
        if st.button("Generate PPT"):
            from pptx import Presentation
            prs = Presentation()
            prs.slides.add_slide(prs.slide_layouts[5]).shapes.title.text = \
                f"Shift-Suite Report {dt.date.today()}"
            ppt_fp = out_dir / "report.pptx"
            prs.save(ppt_fp)
            st.download_button(
                "Download PPT",
                data=ppt_fp.read_bytes(),
                file_name="report.pptx",
                mime=("application/vnd.openxmlformats-officedocument."
                      "presentationml.presentation"),
            )
# ─────────────────────────────  app.py  (Part 3 / 3)  ──────────────────────────
# ------------------------------------------------------------------
# CLI デバッグ用:  python app.py book.xlsx --sheets Sheet1 Sheet2 ...
# （Streamlit 経由のときは実行されない）
# ------------------------------------------------------------------
if __name__ == "__main__" and not any("streamlit" in a.lower()
                                      for a in sys.argv[:2]):
    import argparse
    p = argparse.ArgumentParser(description="CLI デバッグ – Excel → long_df")
    p.add_argument("xlsx",               help="Excel シフト原本 (.xlsx)")
    p.add_argument("--sheets", nargs="+", required=True, help="対象シート名")
    p.add_argument("--header", type=int, default=3,
                   help="ヘッダー開始行 (1-indexed)")
    cli = p.parse_args()

    ld, wt = ingest_excel(
        Path(cli.xlsx),
        shift_sheets=cli.sheets,
        header_row=cli.header,
    )
    print(ld.head())
    print("-----")
    print(wt.head())
# ─────────────────────────────  END OF FILE  ──────────────────────────────
