# app.py – Shift-Suite Streamlit GUI + 内蔵ダッシュボード  v1.09

from __future__ import annotations
import datetime as dt
import io
import json
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

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
from shift_suite.tasks.utils import safe_make_archive

# ────────────────── Streamlit 設定 ──────────────────
st.set_page_config(page_title="Shift-Suite", layout="wide")
st.header("🗂  Shift-Suite 解析")

# ──────────────── サイドバー入力 ────────────────
slot = st.sidebar.number_input("Slot (min)", 5, 60, 30, 5)
min_method = st.sidebar.selectbox("Min-staff method", ["mean-1s", "p25", "mode"], index=1)
ext_opts = st.sidebar.multiselect(
    "Extra modules",
    ["Stats", "Anomaly", "Fatigue", "Cluster", "Skill", "Fairness", "Need forecast", "RL roster (PPO)"]
)
save_mode = st.sidebar.selectbox("保存方法", ["ZIP ダウンロード", "フォルダに保存"])

# ──────────────── Excel 入力 ────────────────
uf = st.file_uploader("Excel シフト表 (*.xlsx)", type=["xlsx"])
if uf:
    # 一時保存
    work_root = Path(tempfile.mkdtemp())
    excel_path = work_root / uf.name
    excel_path.write_bytes(uf.read())

    # シート一覧取得
    all_sheets = pd.ExcelFile(excel_path, engine="openpyxl").sheet_names
    master_sheet = st.sidebar.selectbox("マスターシート", [s for s in all_sheets if "勤務" in s])
    shift_sheets = st.sidebar.multiselect(
        "解析するシフトシート（複数可）",
        [s for s in all_sheets if s != master_sheet],
        default=[s for s in all_sheets if s != master_sheet]
    )

    header_row = st.sidebar.number_input(
        "ヘッダー開始行 (1-indexed)",
        min_value=1, max_value=10, value=3
    )

run = st.button("▶ 解析実行")

if run and uf:
    out_dir = work_root / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1/8 Ingest
    st.info("1/8  Ingest …")
    long_df, wt_df = ingest_excel(
        excel_path,
        shift_sheets=shift_sheets,
        master_sheet=master_sheet,
        header_row=header_row
    )

    # 2/8 Heatmap
    st.info("2/8  Heatmap …")
    build_heatmap(long_df, wt_df, out_dir, slot, min_method=min_method)

    # 3/8 Shortage
    st.info("3/8  Shortage …")
    shortage_and_brief(out_dir, slot, min_method=min_method)

    # 4/8 Stats (optional)
    if "Stats" in ext_opts:
        st.info("4/8  Stats …")
        build_stats(out_dir)

    # 5/8 Anomaly
    if "Anomaly" in ext_opts:
        st.info("5/8  Anomaly …")
        detect_anomaly(out_dir)

    # 6/8 Fatigue
    if "Fatigue" in ext_opts:
        st.info("6/8  Fatigue …")
        train_fatigue(long_df, out_dir)

    # 7/8 Cluster
    if "Cluster" in ext_opts:
        st.info("7/8  Cluster …")
        cluster_staff(long_df, out_dir)

    # 8/8 Skill
    if "Skill" in ext_opts:
        st.info("8/8  Skill …")
        build_skill_matrix(long_df, out_dir)

    # Fairness
    if "Fairness" in ext_opts:
        st.info("Fairness …")
        run_fairness(long_df, out_dir)

    # Need forecast
    if "Need forecast" in ext_opts:
        st.info("Forecast …")
        csv = build_demand_series(out_dir / "heat_ALL.xlsx", out_dir / "demand_series.csv")
        forecast_need(csv, out_dir / "forecast.xlsx", choose="auto")

    # RL roster
    if "RL roster (PPO)" in ext_opts:
        st.info("RL roster …")
        learn_roster(out_dir / "demand_series.csv", out_dir / "rl_roster.xlsx")

    st.success("解析完了 🎉")

    # 出力
    if save_mode == "フォルダに保存":
        st.write(f"出力先: `{out_dir}`")
    else:
        zip_p = work_root / "out.zip"
        safe_make_archive(out_dir, zip_p)
        st.download_button(
            "Download OUT.zip",
            data=zip_p.read_bytes(),
            file_name="out.zip",
            mime="application/zip"
        )

st.divider()

# ──────────────── 2. ダッシュボード ────────────────
st.header("📊 ダッシュボード (ZIP アップロード)")

zip_file = st.file_uploader("out フォルダを ZIP 圧縮してアップロード", type=["zip"], key="dash_zip")

if zip_file:
    tmp_dir = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(io.BytesIO(zip_file.read())) as zf:
        zf.extractall(tmp_dir)

    try:
        out_dir = next(tmp_dir.rglob("heat_ALL.xlsx")).parent
    except StopIteration:
        st.error("heat_ALL.xlsx が ZIP に見つかりません")
        st.stop()

    tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        ["Overview", "Heatmap", "Role Min-staff", "Cost Sim", "Forecast", "Fairness", "Multi-Fac", "PPT Report"]
    )

    # Overview
    with tab0:
        lack_h = 0
        kpi_fp = out_dir / "shortage_role.xlsx"
        if kpi_fp.exists():
            kpi_df = pd.read_excel(kpi_fp)
            if "lack_h" in kpi_df.columns:
                lack_h = kpi_df["lack_h"].sum()
        col1, _ = st.columns([1, 5])
        col1.metric("不足時間 (h)", f"{lack_h:.1f}")

        fair_fp = out_dir / "fairness_after.xlsx"
        if fair_fp.exists():
            after = pd.read_excel(fair_fp)
            if "night_ratio" in after.columns:
                from shift_suite.tasks.utils import calculate_jain_index
                s = after["night_ratio"]
                jain = calculate_jain_index(s)
                col1.metric("夜勤 Jain", jain)
        st.caption("解析結果は一時フォルダに保存されています")

    # Heatmap
    with tab1:
        heat = pd.read_excel(out_dir / "heat_ALL.xlsx", index_col=0)
        fig = px.imshow(
            heat,
            aspect="auto",
            color_continuous_scale="Blues",
            labels=dict(x="Date", y="Time", color="人数"),
        )
        st.plotly_chart(fig, use_container_width=True)

        date = st.selectbox("日付を選択すると不足を表示", heat.columns, index=0)
        lack_fp = out_dir / "shortage_time.xlsx"
        if lack_fp.exists():
            lack = pd.read_excel(lack_fp, index_col=0)
            if date in lack.columns:
                st.bar_chart(lack[date], y=date)

    # Role Min-staff
    with tab2:
        roles = sorted(p.stem.replace("min_", "") for p in out_dir.glob("min_*.csv"))
        if roles:
            role = st.selectbox("職種", roles)
            need = pd.read_csv(out_dir / f"min_{role}.csv", index_col=0)
            st.line_chart(need["min_staff"])
        else:
            st.info("min_<role>.csv がありません")

    # Cost Sim
    with tab3:
        wage = st.slider("平均時給 (¥)", 1000, 3000, 1500, 50)
        hire = st.slider("追加採用人数", 0, 10, 0)
        lack_all = 0
        if (out_dir / "shortage_role.xlsx").exists():
            df_k = pd.read_excel(out_dir / "shortage_role.xlsx")
            if "lack_h" in df_k.columns:
                lack_all = df_k["lack_h"].sum()
        hrs = max(lack_all - hire * 160, 0)
        st.metric("派遣補填コスト", f"¥{hrs * wage:,}")

    # Forecast vs Real
    with tab4:
        fc_fp = out_dir / "forecast.xlsx"
        meta_fp = out_dir / "forecast.meta.json"
        if fc_fp.exists() and fc_fp.stat().st_size > 0:
            meta = json.load(open(meta_fp, encoding="utf-8")) if meta_fp.exists() else {}
            st.info(f"採用モデル: **{meta.get('selected_model','–')}**, MAPE={meta.get('mape_selected')}")
            fc = pd.read_excel(fc_fp)
            heat = pd.read_excel(out_dir / "heat_ALL.xlsx", index_col=0)
            date_cols = [c for c in heat.columns if re.match(r"^\d{1,2}/\d{1,2}", str(c))]
            real_long = (
                heat[date_cols]
                .stack()
                .reset_index()
                .rename(columns={"level_0": "time", "level_1": "date", 0: "need"})
            )
            real_long["date"] = real_long["date"].str.replace(r"\s*\(.*?\)", "", regex=True)
            real_long["ds"] = pd.to_datetime(real_long["date"] + " " + real_long["time"], format="%m/%d %H:%M")
            df_compare = pd.merge(fc[["ds", "yhat"]], real_long[["ds", "need"]], on="ds")
            st.plotly_chart(px.line(df_compare, x="ds", y=["yhat", "need"]), use_container_width=True)
        else:
            st.info("forecast.xlsx がありません、または空です")

    # Fairness
    with tab5:
        fair_fp = out_dir / "fairness_after.xlsx"
        if fair_fp.exists():
            after = pd.read_excel(fair_fp)
            if "night_ratio" in after.columns:
                max_ratio = st.slider("許容夜勤比率", 0.0, 0.5, 0.2, 0.05)
                adj = after["night_ratio"].clip(upper=max_ratio)
                jain2 = calculate_jain_index(adj)
                st.metric("調整後 Jain", jain2)
                st.dataframe(after, use_container_width=True)
        else:
            st.info("fairness_after.xlsx がありません")

    # Multi-Facility
    with tab6:
        st.write("複数施設比較は今後の拡張予定です")

    # PPT Report
    with tab7:
        if st.button("Generate PPT"):
            from pptx import Presentation
            prs = Presentation()
            slide = prs.slides.add_slide(prs.slide_layouts[5])
            slide.shapes.title.text = f"Shift-Suite Report {dt.date.today()}"
            ppt_fp = out_dir / "report.pptx"
            prs.save(ppt_fp)
            st.download_button(
                "Download PPT",
                data=ppt_fp.read_bytes(),
                file_name="report.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )

# （任意）外部 Dash 起動リンク
dash_url = "http://127.0.0.1:8502"
st.markdown(f"### 👉 <a href='{dash_url}' target='_blank'>別窓で Dash ダッシュボード</a>", unsafe_allow_html=True)
