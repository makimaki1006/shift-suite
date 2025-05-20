# ─────────────────────────────  app.py  (Part 1 / 3)  ──────────────────────────

from __future__ import annotations

import datetime as dt
import io
import json
import logging
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import List, Tuple, Optional, Any

import pandas as pd
import numpy as np
import streamlit as st
from streamlit.runtime import exists as st_runtime_exists
import openpyxl

from shift_suite.tasks.io_excel import ingest_excel
from shift_suite.tasks.utils import _parse_as_date
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
from shift_suite.tasks.constants import SUMMARY5 as SUMMARY5_CONST
from shift_suite.tasks import leave_analyzer # ★ 新規インポート
from shift_suite.tasks.leave_analyzer import LEAVE_TYPE_REQUESTED, LEAVE_TYPE_PAID # ★ 定数もインポート
# ──────────────────────────────────────────────────────────────────────────────

log = logging.getLogger("shift_suite_app")
if not log.handlers:
    log.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s [%(module)s.%(funcName)s:%(lineno)d] - %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)

    from shift_suite.tasks.utils import log as tasks_log
    if not tasks_log.handlers:
        tasks_log.addHandler(handler)
        tasks_log.setLevel(logging.DEBUG)

JP = {
    "Overview": "概要", "Heatmap": "ヒートマップ", "Shortage": "不足分析",
    "Fatigue": "疲労", "Forecast": "需要予測", "Fairness": "公平性",
    "Cost Sim": "コスト試算", "Hire Plan": "採用計画", "PPT Report": "PPTレポート",
    "Leave Analysis": "休暇分析",  # ★ 追加
    "Slot (min)": "スロット (分)",
    "Need Calculation Settings (Day of Week Pattern)": "📊 Need算出設定 (曜日パターン別)",
    "Reference Period for Need Calculation": "参照期間 (Need算出用)",
    "Start Date": "開始日", "End Date": "終了日",
    "Statistical Metric for Need": "統計的指標 (Need算出用)",
    "Remove Outliers for Need Calculation": "外れ値を除去してNeedを算出",
    "(Optional) Upper Limit Calculation Method": "(オプション) 上限値算出方法",
    "Min-staff method (for Upper)": "最少人数算出法 (上限値用)",
    "Max-staff method (for Upper)": "最大人数算出法 (上限値用)",
    "Extra modules": "追加モジュール", "Save method": "保存方法",
    "ZIP Download": "ZIP形式でダウンロード", "Save to folder": "フォルダに保存",
    "Run Analysis": "▶ 解析実行", "Cost & Hire Parameters": "💰 コスト・採用計画パラメータ",
    "Standard work hours (h/month)": "所定労働時間 (h/月)",
    "Safety factor (shortage h multiplier)": "安全係数 (不足h上乗せ)",
    "Target coverage rate": "目標充足率",
    "Direct employee labor cost (¥/h)": "正職員 人件費 (¥/h)",
    "Temporary staff labor cost (¥/h)": "派遣 人件費 (¥/h)",
    "One-time hiring cost (¥/person)": "採用一時コスト (¥/人)",
    "Penalty for shortage (¥/h)": "不足ペナルティ (¥/h)",
    "Upload Excel shift file (*.xlsx)": "Excel シフト表 (*.xlsx) をアップロード",
    "Select shift sheets to analyze (multiple)": "解析するシフトシート（複数可）",
    "Header start row (1-indexed)": "ヘッダー開始行 (1-indexed)",
    "File Preview (first 8 rows)": "ファイルプレビュー (先頭8行)",
    "Error during preview display": "プレビューの表示中にエラーが発生しました",
    "Error saving Excel file": "Excelファイルの保存中にエラーが発生しました",
    "Error getting sheet names from Excel": "Excelファイルからシート名の取得中にエラーが発生しました",
    "No analysis target sheets found": "勤務区分シート以外の解析対象シートが見つからないか、全てのシート名に「勤務区分」が含まれています。",
    "Analysis in progress...": "解析準備中...",
    "Ingest: Reading Excel data...": "Excelデータ読み込み中…",
    "Heatmap: Generating heatmap...": "Heatmap生成中…",
    "Shortage: Analyzing shortage...": "Shortage (不足分析) 中…",
    "Stats: Processing...": "Stats (統計情報) 生成中…",
    "Anomaly: Processing...": "Anomaly (異常検知) 中…",
    "Fatigue: Processing...": "Fatigue (疲労分析) 中…",
    "Cluster: Processing...": "Cluster (クラスタリング) 中…",
    "Skill: Processing...": "Skill (スキルNMF) 中…",
    "Fairness: Processing...": "Fairness (公平性分析) 中…",
    "Leave Analysis: Processing...": "Leave Analysis (休暇分析) 中…",  # ★ 追加
    "Need forecast: Processing...": "Need forecast (需要予測) 中…",
    "RL roster (PPO): Processing...": "RL roster (強化学習シフト) 中…",
    "Hire plan: Processing...": "Hire plan (採用計画) 中…",
    "Cost / Benefit: Processing...": "Cost / Benefit (コスト便益分析) 中…",
    "Ingest: Excel data read complete.": "✅ Excelデータ読み込み完了",
    "All processes complete!": "🎉 全ての解析が完了しました！",
    "Error during analysis (ValueError)": "解析中にエラーが発生しました (ValueError)",
    "Required file not found": "必要なファイルが見つかりませんでした",
    "Unexpected error occurred": "予期せぬエラーが発生しました",
    "Save Analysis Results": "📁 解析結果の保存",
    "Output folder": "出力先フォルダ",
    "Open the above path in Explorer.": "エクスプローラーで上記のパスを開いてご確認ください。",
    "Download analysis results as ZIP": "📥 解析結果をZIPでダウンロード",
    "Error creating ZIP file": "ZIPファイルの作成中にエラーが発生しました",
    "Dashboard (Upload ZIP)": "📊 ダッシュボード (ZIP アップロード)",
    "Upload ZIP file of 'out' folder": "out フォルダを ZIP 圧縮してアップロード",
    "heat_ALL.xlsx not found in ZIP": "アップロードされたZIPファイル内に heat_ALL.xlsx が見つかりません。ZIPの構造を確認してください。",
    "Failed to extract ZIP file.": "ZIPファイルの展開に失敗しました。",
    "Uploaded file is not a valid ZIP file.": "アップロードされたファイルは有効なZIPファイルではありません。",
    "Error during ZIP file extraction": "ZIPファイルの展開中にエラーが発生しました",
    "Display Mode": "表示モード", "Raw Count": "人数", "Ratio (staff ÷ need)": "Ratio (staff ÷ need)",
    "Color Scale Max (zmax)": "カラースケール上限 (zmax)",
    "Shortage by Role (hours)": "職種別不足時間 (h)",
    "Shortage by Time (count per day)": "時間帯別不足人数 (日別)",
    "Select date to display": "表示する日付を選択",
    "No date columns in shortage data.": "不足時間データに日付列がありません。",
    "Display all time-slot shortage data": "全時間帯別不足データ表示",
    "Fatigue Score per Staff": "スタッフ別疲労スコア",
    "Demand Forecast (yhat)": "需要予測結果 (yhat)", "Actual (y)": "実績 (y)",
    "Display forecast data": "予測データ表示",
    "Fairness (Night Shift Ratio)": "公平性 (夜勤比率)",
    "Cost Simulation (Million ¥)": "コスト試算 (百万円)",
    "Hiring Plan (Needed FTE)": "採用計画 (必要採用人数)",
    "Hiring Plan Parameters": "採用計画パラメータ",
    "Generate PowerPoint Report (β)": "📊 PowerPointレポート生成 (β版)",
    "Generating PowerPoint report...": "PowerPointレポートを生成中です... 少々お待ちください。",
    "PowerPoint report ready.": "PowerPointレポートの準備ができました。",
    "Download Report (PPTX)": "📥 レポート(PPTX)をダウンロード",
    "python-pptx library required for PPT": "PowerPointレポートの生成には `python-pptx` ライブラリが必要です。\nインストールしてください: `pip install python-pptx`",
    "Error generating PowerPoint report": "PowerPointレポートの生成中にエラーが発生しました",
    "Click button to generate report.": "ボタンをクリックすると、主要な分析結果を含むPowerPointレポートが生成されます（現在はβ版です）。",
}
def _(text_key: str) -> str:
    return JP.get(text_key, text_key)

st.set_page_config(page_title="Shift-Suite", layout="wide", initial_sidebar_state="expanded")
st.title("🗂️ Shift-Suite : 勤務シフト分析ツール")

master_sheet_keyword = "勤務区分"

if "app_initialized" not in st.session_state:
    st.session_state.app_initialized = True
    st.session_state.analysis_done = False
    st.session_state.work_root_path_str = None
    st.session_state.out_dir_path_str = None
    st.session_state.current_step_for_progress = 0

    today_val = datetime.date.today()

    st.session_state.slot_input_widget = 30
    st.session_state.header_row_input_widget = 3
    st.session_state.candidate_sheet_list_for_ui = []
    st.session_state.shift_sheets_multiselect_widget = []
    st.session_state._force_update_multiselect_flag = False

    st.session_state.need_ref_start_date_widget = today_val - datetime.timedelta(days=59) # 初期デフォルト
    st.session_state.need_ref_end_date_widget = today_val - datetime.timedelta(days=1)   # 初期デフォルト
    st.session_state._force_update_need_ref_dates_flag = False
    st.session_state._intended_need_ref_start_date = None
    st.session_state._intended_need_ref_end_date = None

    st.session_state.need_stat_method_options_widget = ["10パーセンタイル", "25パーセンタイル", "中央値", "平均値"]
    st.session_state.need_stat_method_widget = "中央値"
    st.session_state.need_remove_outliers_widget = True

    st.session_state.min_method_for_upper_options_widget = ["mean-1s", "p25", "mode"]
    st.session_state.min_method_for_upper_widget = "p25"
    st.session_state.max_method_for_upper_options_widget = ["mean+1s", "p75"]
    st.session_state.max_method_for_upper_widget = "p75"

    st.session_state.available_ext_opts_widget = [
        "Stats", "Anomaly", "Fatigue", "Cluster", "Skill", "Fairness",
        _("Leave Analysis"), # ★ "休暇分析" を追加
        "Need forecast", "RL roster (PPO)", "Hire plan", "Cost / Benefit"
    ]
    st.session_state.ext_opts_multiselect_widget = st.session_state.available_ext_opts_widget[:] 

    st.session_state.save_mode_selectbox_options_widget = [_("ZIP Download"), _("Save to folder")]
    st.session_state.save_mode_selectbox_widget = _("ZIP Download")

    st.session_state.std_work_hours_widget = 160
    st.session_state.safety_factor_widget = 1.10
    st.session_state.target_coverage_widget = 0.95
    st.session_state.wage_direct_widget = 1500
    st.session_state.wage_temp_widget = 2200
    st.session_state.hiring_cost_once_widget = 180000
    st.session_state.penalty_per_lack_widget = 4000

    st.session_state.excel_path_for_run_script_str = None
    st.session_state.last_uploaded_file_name = None
    st.session_state.last_uploaded_file_size = None

    st.session_state.leave_analysis_target_types_widget = [LEAVE_TYPE_REQUESTED, LEAVE_TYPE_PAID] # デフォルトで両方
    st.session_state.leave_concentration_threshold_widget = 3 # 希望休集中度閾値のデフォルト

    st.session_state.leave_analysis_results = {}
    
    log.info("セッションステートを初期化しました。")

with st.sidebar:
    st.header("🛠️ 解析設定")

    st.number_input(_("Slot (min)"), 5, 120,
                    key="slot_input_widget", help="分析の時間間隔（分）")

    st.subheader("📄 シート選択とヘッダー")

    if st.session_state.get("_force_update_multiselect_flag", False):
        new_options = st.session_state.candidate_sheet_list_for_ui
        current_selection = st.session_state.get("shift_sheets_multiselect_widget", [])
        valid_selection = [s for s in current_selection if s in new_options]
        if not valid_selection and new_options:
             st.session_state.shift_sheets_multiselect_widget = new_options[:]
        elif valid_selection:
             st.session_state.shift_sheets_multiselect_widget = valid_selection
        else:
             st.session_state.shift_sheets_multiselect_widget = []
        st.session_state._force_update_multiselect_flag = False

    st.multiselect(
        _("Select shift sheets to analyze (multiple)"),
        options=st.session_state.candidate_sheet_list_for_ui,
        default=st.session_state.shift_sheets_multiselect_widget,
        key="shift_sheets_multiselect_widget"
    )
    st.number_input(
        _("Header start row (1-indexed)"), 1, 20,
        key="header_row_input_widget"
    )

    st.subheader(_("Need Calculation Settings (Day of Week Pattern)"))

    if st.session_state.get("_force_update_need_ref_dates_flag", False):
        if st.session_state.get("_intended_need_ref_start_date"):
            st.session_state.need_ref_start_date_widget = st.session_state._intended_need_ref_start_date
        if st.session_state.get("_intended_need_ref_end_date"):
            st.session_state.need_ref_end_date_widget = st.session_state._intended_need_ref_end_date
        st.session_state._force_update_need_ref_dates_flag = False
        if "_intended_need_ref_start_date" in st.session_state: del st.session_state["_intended_need_ref_start_date"]
        if "_intended_need_ref_end_date" in st.session_state: del st.session_state["_intended_need_ref_end_date"]

    c1_need_ui, c2_need_ui = st.columns(2)
    with c1_need_ui:
        st.date_input(
            _("Start Date"),
            key="need_ref_start_date_widget", help="Need算出の参照期間の開始日"
        )
    with c2_need_ui:
        st.date_input(
            _("End Date"),
            key="need_ref_end_date_widget", help="Need算出の参照期間の終了日"
        )
    st.caption(_("Reference Period for Need Calculation"))

    current_need_stat_method_idx_val = 0
    try:
        current_need_stat_method_idx_val = st.session_state.need_stat_method_options_widget.index(st.session_state.need_stat_method_widget)
    except (ValueError, AttributeError):
        current_need_stat_method_idx_val = 2
    st.selectbox(
        _("Statistical Metric for Need"), options=st.session_state.need_stat_method_options_widget,
        index=current_need_stat_method_idx_val,
        key="need_stat_method_widget", help="曜日別・時間帯別のNeedを算出する際の統計指標"
    )
    st.checkbox(
        _("Remove Outliers for Need Calculation"),
        key="need_remove_outliers_widget", help="IQR法で外れ値を除去してから統計量を計算します"
    )

    with st.expander(_("(Optional) Upper Limit Calculation Method"), expanded=False):
        current_min_method_upper_idx_val = 0
        try: current_min_method_upper_idx_val = st.session_state.min_method_for_upper_options_widget.index(st.session_state.min_method_for_upper_widget)
        except (ValueError, AttributeError): current_min_method_upper_idx_val = 1
        st.selectbox(
            _("Min-staff method (for Upper)"), options=st.session_state.min_method_for_upper_options_widget,
            index=current_min_method_upper_idx_val, key="min_method_for_upper_widget",
            help="（オプション）ヒートマップの『代表的な上限スタッフ数』の算出方法の一部"
        )
        current_max_method_upper_idx_val = 0
        try: current_max_method_upper_idx_val = st.session_state.max_method_for_upper_options_widget.index(st.session_state.max_method_for_upper_widget)
        except (ValueError, AttributeError): current_max_method_upper_idx_val = 0
        st.selectbox(
            _("Max-staff method (for Upper)"), options=st.session_state.max_method_for_upper_options_widget,
            index=current_max_method_upper_idx_val, key="max_method_for_upper_widget",
            help="（オプション）ヒートマップの『代表的な上限スタッフ数』の算出方法"
        )

    st.divider()
    st.subheader("追加分析モジュール")

    st.multiselect(
        _("Extra modules"), st.session_state.available_ext_opts_widget,
        default=st.session_state.ext_opts_multiselect_widget, # 初期値はセッションステートから
        key="ext_opts_multiselect_widget", help="実行する追加の分析モジュールを選択します。"
    )

    if _("Leave Analysis") in st.session_state.ext_opts_multiselect_widget:
        with st.expander("📊 " + _("Leave Analysis") + " 設定", expanded=True):
            st.multiselect(
                "分析対象の休暇タイプ",
                options=[LEAVE_TYPE_REQUESTED, LEAVE_TYPE_PAID], # 将来的に 'その他休暇' なども追加可能
                key="leave_analysis_target_types_widget",
                help="分析する休暇の種類を選択します。"
            )
            if LEAVE_TYPE_REQUESTED in st.session_state.leave_analysis_target_types_widget:
                st.number_input(
                    "希望休 集中度判定閾値 (人)", 
                    min_value=1, 
                    step=1,
                    key="leave_concentration_threshold_widget",
                    help="同日にこの人数以上の希望休があった場合に「集中」とみなします。"
                )

    current_save_mode_idx_val = 0
    try: current_save_mode_idx_val = st.session_state.save_mode_selectbox_options_widget.index(st.session_state.save_mode_selectbox_widget)
    except (ValueError, AttributeError): current_save_mode_idx_val = 0
    st.selectbox(
        _("Save method"), options=st.session_state.save_mode_selectbox_options_widget,
        index=current_save_mode_idx_val,
        key="save_mode_selectbox_widget", help="解析結果の保存方法を選択します。"
    )

    with st.expander(_("Cost & Hire Parameters")):
        st.number_input(_("Standard work hours (h/month)"),   100, 300, key="std_work_hours_widget")
        st.slider      (_("Safety factor (shortage h multiplier)"), 1.00, 2.00, key="safety_factor_widget")
        st.slider      (_("Target coverage rate"), 0.50, 1.00, key="target_coverage_widget")
        st.number_input(_("Direct employee labor cost (¥/h)"),   500, 10000, key="wage_direct_widget")
        st.number_input(_("Temporary staff labor cost (¥/h)"),   800, 12000, key="wage_temp_widget")
        st.number_input(_("One-time hiring cost (¥/person)"), 0, 1000000, key="hiring_cost_once_widget")
        st.number_input(_("Penalty for shortage (¥/h)"), 0, 20000, key="penalty_per_lack_widget")

st.header("1. ファイルアップロードと設定")
uploaded_file = st.file_uploader(
    _("Upload Excel shift file (*.xlsx)"),
    type=["xlsx"],
    key="excel_uploader_main_content_area_key",
    help="勤務実績と勤務区分が記載されたExcelファイルをアップロードしてください。"
)

if uploaded_file:
    if st.session_state.get("last_uploaded_file_name") != uploaded_file.name or \
       st.session_state.get("last_uploaded_file_size") != uploaded_file.size:

        st.session_state.last_uploaded_file_name = uploaded_file.name
        st.session_state.last_uploaded_file_size = uploaded_file.size

        if st.session_state.work_root_path_str is None or not Path(st.session_state.work_root_path_str).exists():
            st.session_state.work_root_path_str = tempfile.mkdtemp(prefix="ShiftSuite_")
            log.info(f"新しい一時ディレクトリを作成しました: {st.session_state.work_root_path_str}")

        st.session_state.analysis_done = False
        work_root_on_upload = Path(st.session_state.work_root_path_str)
        st.session_state.excel_path_for_run_script_str = str(work_root_on_upload / uploaded_file.name)

        excel_path_for_processing = Path(st.session_state.excel_path_for_run_script_str)

        try:
            with open(excel_path_for_processing, "wb") as f_wb:
                f_wb.write(uploaded_file.getbuffer())
            log.info(f"アップロードされたExcelファイルを保存しました: {excel_path_for_processing}")

            current_header_for_est = st.session_state.header_row_input_widget - 1
            try:
                temp_sheets_data = pd.read_excel(excel_path_for_processing, sheet_name=None, header=current_header_for_est, nrows=1)
                all_sheet_names_from_file = list(temp_sheets_data.keys())

                candidate_sheets_from_file = [s_name for s_name in all_sheet_names_from_file if master_sheet_keyword.lower() not in s_name.lower()]
                st.session_state.candidate_sheet_list_for_ui = candidate_sheets_from_file
                st.session_state._force_update_multiselect_flag = True

                first_content_sheet_name = next((s for s in candidate_sheets_from_file if s in temp_sheets_data), None)
                if first_content_sheet_name:
                    df_sample = temp_sheets_data[first_content_sheet_name]
                    parsed_dates_in_sample: List[datetime.date] = []
                    for col_header in df_sample.columns:
                        parsed_date = _parse_as_date(str(col_header))
                        if parsed_date: parsed_dates_in_sample.append(parsed_date)

                    valid_dates_final = sorted([d for d in parsed_dates_in_sample if d is not pd.NaT and d is not None])
                    if valid_dates_final:
                        st.session_state._intended_need_ref_start_date = valid_dates_final[0]
                        st.session_state._intended_need_ref_end_date = valid_dates_final[-1]
                        st.session_state._force_update_need_ref_dates_flag = True
                        log.info(f"Excel日付範囲推定(Need参照期間デフォルト用): {valid_dates_final[0]} - {valid_dates_final[-1]}")
                    else: log.warning("Excelから有効な日付列が見つからず、日付範囲を推定できませんでした。")
                else: log.warning("勤務区分シート以外の解析対象シートが見つからず、日付範囲を推定できませんでした。")

                st.rerun()

            except Exception as e_date_range_process:
                log.warning(f"Excelの日付範囲・シート名取得中に予期せぬエラー: {e_date_range_process}", exc_info=True)
        except Exception as e_save_file_process:
            st.error(_("Error saving Excel file") + f": {e_save_file_process}")

run_button_disabled_status = not st.session_state.get("excel_path_for_run_script_str") or \
                               not st.session_state.get("shift_sheets_multiselect_widget", [])
run_button_clicked = st.button(
    _("Run Analysis"), key="run_analysis_button_final_trigger", use_container_width=True, type="primary",
    disabled=run_button_disabled_status
)

# ─────────────────────────────  app.py  (Part 2 / 3)  ──────────────────────────
if run_button_clicked:
    st.session_state.analysis_done = False
    st.session_state.current_step_for_progress = 0

    excel_path_to_use = Path(st.session_state.excel_path_for_run_script_str) if st.session_state.excel_path_for_run_script_str else None
    if st.session_state.work_root_path_str is None or excel_path_to_use is None :
        st.error("Excelファイルが正しくアップロードされていません。ファイルを再アップロードしてください。")
        st.stop()

    work_root_exec = Path(st.session_state.work_root_path_str)
    st.session_state.out_dir_path_str = str(work_root_exec / "out")
    out_dir_exec = Path(st.session_state.out_dir_path_str)
    out_dir_exec.mkdir(parents=True, exist_ok=True)
    log.info(f"解析出力ディレクトリ: {out_dir_exec}")

    param_selected_sheets = st.session_state.shift_sheets_multiselect_widget
    param_header_row = st.session_state.header_row_input_widget
    param_slot = st.session_state.slot_input_widget
    param_ref_start = st.session_state.need_ref_start_date_widget
    param_ref_end = st.session_state.need_ref_end_date_widget
    param_need_stat = st.session_state.need_stat_method_widget
    param_need_outlier = st.session_state.need_remove_outliers_widget
    param_min_method_upper = st.session_state.min_method_for_upper_widget
    param_max_method_upper = st.session_state.max_method_for_upper_widget
    param_ext_opts = st.session_state.ext_opts_multiselect_widget
    param_save_mode = st.session_state.save_mode_selectbox_widget
    param_std_work_hours = st.session_state.std_work_hours_widget
    param_safety_factor = st.session_state.safety_factor_widget
    param_target_coverage = st.session_state.target_coverage_widget
    param_wage_direct = st.session_state.wage_direct_widget
    param_wage_temp = st.session_state.wage_temp_widget
    param_hiring_cost = st.session_state.hiring_cost_once_widget
    param_penalty_lack = st.session_state.penalty_per_lack_widget
    
    param_leave_target_types = st.session_state.leave_analysis_target_types_widget
    param_leave_concentration_threshold = st.session_state.leave_concentration_threshold_widget
    
    st.session_state.leave_analysis_results = {}

    progress_text_area = st.empty()
    progress_bar_val = st.progress(0)
    total_steps_exec_run = 3 + len(param_ext_opts)

    def update_progress_exec_run(step_name_key_exec: str):
        st.session_state.current_step_for_progress += 1
        progress_percentage_exec_run = int((st.session_state.current_step_for_progress / total_steps_exec_run) * 100)
        progress_percentage_exec_run = min(progress_percentage_exec_run, 100)
        try:
            progress_bar_val.progress(progress_percentage_exec_run)
            progress_text_area.info(f"⚙️ {st.session_state.current_step_for_progress}/{total_steps_exec_run} - {_(step_name_key_exec)}")
        except Exception as e_prog_exec_run: 
            log.warning(f"進捗表示の更新中にエラー: {e_prog_exec_run}")

    st.markdown("---")
    st.header("2. 解析処理")
    try:
        if param_selected_sheets and excel_path_to_use:
            update_progress_exec_run("File Preview (first 8 rows)")
            st.subheader(_("File Preview (first 8 rows)"))
            try:
                preview_df_exec_run = pd.read_excel(excel_path_to_use, sheet_name=param_selected_sheets[0], header=None, nrows=8)
                st.dataframe(preview_df_exec_run.astype(str), use_container_width=True)
            except Exception as e_prev_exec_run: 
                st.warning(_("Error during preview display") + f": {e_prev_exec_run}")
                log.warning(f"プレビュー表示エラー: {e_prev_exec_run}", exc_info=True)
        else: 
            st.warning("プレビューを表示するシートが選択されていないか、ファイルパスが無効です。")

        update_progress_exec_run("Ingest: Reading Excel data...")
        long_df, wt_df = ingest_excel(excel_path_to_use, shift_sheets=param_selected_sheets, header_row=param_header_row)
        log.info(f"Ingest完了. long_df shape: {long_df.shape}, wt_df shape: {wt_df.shape if wt_df is not None else 'N/A'}")
        st.success(_("Ingest: Excel data read complete."))

        update_progress_exec_run("Heatmap: Generating heatmap...")
        build_heatmap(
            long_df, out_dir_exec, param_slot,
            ref_start_date_for_need=param_ref_start,
            ref_end_date_for_need=param_ref_end,
            need_statistic_method=param_need_stat,
            need_remove_outliers=param_need_outlier,
            need_iqr_multiplier=1.5,
            min_method=param_min_method_upper,
            max_method=param_max_method_upper
        )
        st.success("✅ Heatmap生成完了")

        update_progress_exec_run("Shortage: Analyzing shortage...")
        shortage_result_exec_run = shortage_and_brief(out_dir_exec, param_slot)
        if shortage_result_exec_run is None: 
            st.warning("Shortage (不足分析) の一部または全てが完了しませんでした。")
        else: 
            st.success("✅ Shortage (不足分析) 完了")

        if _("Leave Analysis") in param_ext_opts:
            update_progress_exec_run("Leave Analysis: Processing...")
            st.info(f"{_('Leave Analysis')} 処理中…")
            
            try:
                if 'long_df' in locals() and not long_df.empty:
                    daily_leave_df = leave_analyzer.get_daily_leave_counts(
                        long_df,
                        target_leave_types=param_leave_target_types
                    )
                    
                    leave_results_temp = {}
                    
                    if LEAVE_TYPE_REQUESTED in param_leave_target_types:
                        requested_leave_daily = daily_leave_df[daily_leave_df['leave_type'] == LEAVE_TYPE_REQUESTED].copy()
                        
                        daily_requested_applicants_counts = leave_analyzer.count_daily_leave_applicants(
                            requested_leave_daily,
                            leave_type_to_count=LEAVE_TYPE_REQUESTED
                        )
                        leave_results_temp['daily_requested_applicants_counts'] = daily_requested_applicants_counts
                        
                        leave_results_temp['summary_dow_requested'] = leave_analyzer.summarize_leave_by_day_count(
                            requested_leave_daily.copy(),
                            period='dayofweek'
                        )
                        
                        leave_results_temp['summary_month_period_requested'] = leave_analyzer.summarize_leave_by_day_count(
                            requested_leave_daily.copy(),
                            period='month_period'
                        )
                        
                        leave_results_temp['summary_month_requested'] = leave_analyzer.summarize_leave_by_day_count(
                            requested_leave_daily.copy(),
                            period='month'
                        )
                        
                        leave_results_temp['concentration_requested'] = leave_analyzer.analyze_leave_concentration(
                            daily_requested_applicants_counts,
                            leave_type_to_analyze=LEAVE_TYPE_REQUESTED,
                            concentration_threshold=param_leave_concentration_threshold
                        )
                    
                    if LEAVE_TYPE_PAID in param_leave_target_types:
                        paid_leave_daily = daily_leave_df[daily_leave_df['leave_type'] == LEAVE_TYPE_PAID].copy()
                        
                        daily_paid_applicants_counts = leave_analyzer.count_daily_leave_applicants(
                            paid_leave_daily,
                            leave_type_to_count=LEAVE_TYPE_PAID
                        )
                        leave_results_temp['daily_paid_applicants_counts'] = daily_paid_applicants_counts
                        
                        leave_results_temp['summary_dow_paid'] = leave_analyzer.summarize_leave_by_day_count(
                            paid_leave_daily.copy(),
                            period='dayofweek'
                        )
                        
                        leave_results_temp['summary_month_period_paid'] = leave_analyzer.summarize_leave_by_day_count(
                            paid_leave_daily.copy(),
                            period='month_period'
                        )
                        
                        leave_results_temp['summary_month_paid'] = leave_analyzer.summarize_leave_by_day_count(
                            paid_leave_daily.copy(),
                            period='month'
                        )
                        
                        leave_results_temp['concentration_paid'] = leave_analyzer.analyze_leave_concentration(
                            daily_paid_applicants_counts,
                            leave_type_to_analyze=LEAVE_TYPE_PAID,
                            concentration_threshold=param_leave_concentration_threshold
                        )
                    
                    leave_results_temp['staff_leave_list'] = leave_analyzer.get_staff_leave_list(long_df, target_leave_types=param_leave_target_types)
                    leave_results_temp['daily_leave_counts'] = daily_leave_df.copy()
                    
                    st.session_state.leave_analysis_results.update(leave_results_temp)
                    st.success(f"✅ {_('Leave Analysis')} 完了")
                else:
                    st.info(f"{_('Leave Analysis')}: 分析対象となる休暇データが見つかりませんでした。")
            except Exception as e_leave:
                st.error(f"{_('Leave Analysis')} の処理中にエラーが発生しました: {e_leave}")
                log.error(f"休暇分析エラー: {e_leave}", exc_info=True)
        for opt_module_name_exec_run in st.session_state.available_ext_opts_widget:
            if opt_module_name_exec_run in param_ext_opts and opt_module_name_exec_run != _("Leave Analysis"):
                progress_key_exec_run = f"{opt_module_name_exec_run}: Processing..."
                update_progress_exec_run(progress_key_exec_run)
                st.info(f"{_(opt_module_name_exec_run)} 処理中…")
                try:
                    if opt_module_name_exec_run == "Stats": 
                        build_stats(out_dir_exec)
                    elif opt_module_name_exec_run == "Anomaly": 
                        detect_anomaly(out_dir_exec)
                    elif opt_module_name_exec_run == "Fatigue": 
                        train_fatigue(long_df, out_dir_exec)
                    elif opt_module_name_exec_run == "Cluster": 
                        cluster_staff(long_df, out_dir_exec)
                    elif opt_module_name_exec_run == "Skill": 
                        build_skill_matrix(long_df, out_dir_exec)
                    elif opt_module_name_exec_run == "Fairness": 
                        run_fairness(long_df, out_dir_exec)
                    elif opt_module_name_exec_run == "Need forecast":
                        demand_csv_exec_run_fc = out_dir_exec / "demand_series.csv"
                        forecast_xls_exec_run_fc = out_dir_exec / "forecast.xlsx"
                        heat_all_for_fc_exec_run_fc = out_dir_exec / "heat_ALL.xlsx"
                        if not heat_all_for_fc_exec_run_fc.exists(): 
                            st.warning(f"Need forecast: 必須ファイル {heat_all_for_fc_exec_run_fc.name} が見つかりません。")
                        else:
                            build_demand_series(heat_all_for_fc_exec_run_fc, demand_csv_exec_run_fc)
                            if demand_csv_exec_run_fc.exists(): 
                                forecast_need(demand_csv_exec_run_fc, forecast_xls_exec_run_fc)
                            else: 
                                st.warning("Need forecast: demand_series.csv の生成に失敗しました。")
                    elif opt_module_name_exec_run == "RL roster (PPO)":
                        demand_csv_rl_exec_run_rl = out_dir_exec / "demand_series.csv"
                        rl_roster_xls_exec_run_rl = out_dir_exec / "rl_roster.xlsx"
                        if demand_csv_rl_exec_run_rl.exists(): 
                            learn_roster(demand_csv_rl_exec_run_rl, rl_roster_xls_exec_run_rl)
                        else: 
                            st.warning("RL Roster: 需要予測データ (demand_series.csv) がありません。")
                    elif opt_module_name_exec_run == "Hire plan":
                        demand_csv_hp_exec_run_hp = out_dir_exec / "demand_series.csv"
                        hire_xls_exec_run_hp = out_dir_exec / "hire_plan.xlsx"
                        if demand_csv_hp_exec_run_hp.exists(): 
                            build_hire_plan(demand_csv_hp_exec_run_hp, hire_xls_exec_run_hp, param_std_work_hours, param_safety_factor, param_target_coverage)
                        else: 
                            st.warning("Hire Plan: 需要予測データ (demand_series.csv) がありません。")
                    elif opt_module_name_exec_run == "Cost / Benefit":
                        analyze_cost_benefit(out_dir_exec, param_wage_direct, param_wage_temp, param_hiring_cost, param_penalty_lack)
                    st.success(f"✅ {_(opt_module_name_exec_run)} 完了")
                except FileNotFoundError as fe_opt_exec_run_loop:
                    st.error(f"{_(opt_module_name_exec_run)} の処理中にエラー (ファイル未検出): {fe_opt_exec_run_loop}")
                    log.error(f"{opt_module_name_exec_run} 処理エラー (FileNotFoundError): {fe_opt_exec_run_loop}", exc_info=True)
                except Exception as e_opt_exec_run_loop:
                    st.error(f"{_(opt_module_name_exec_run)} の処理中にエラーが発生しました: {e_opt_exec_run_loop}")
                    log.error(f"{opt_module_name_exec_run} 処理エラー: {e_opt_exec_run_loop}", exc_info=True)

        progress_bar_val.progress(100)
        progress_text_area.success("✨ 全工程完了！")
        st.balloons()
        st.success(_("All processes complete!"))
        st.session_state.analysis_done = True
    except ValueError as ve_exec_run_main:
        st.error(_("Error during analysis (ValueError)") + f": {ve_exec_run_main}")
        log.error(f"解析エラー (ValueError): {ve_exec_run_main}", exc_info=True)
        st.session_state.analysis_done = False
    except FileNotFoundError as fe_exec_run_main:
        st.error(_("Required file not found") + f": {fe_exec_run_main}")
        log.error(f"ファイル未検出エラー: {fe_exec_run_main}", exc_info=True)
        st.session_state.analysis_done = False
    except Exception as e_exec_run_main:
        st.error(_("Unexpected error occurred") + f": {e_exec_run_main}")
        log.error(f"予期せぬエラー: {e_exec_run_main}", exc_info=True)
        st.session_state.analysis_done = False
    finally:
        if 'progress_bar_val' in locals() and progress_bar_val is not None: 
            progress_bar_val.empty()
        if 'progress_text_area' in locals() and progress_text_area is not None: 
            progress_text_area.empty()

    if st.session_state.analysis_done and st.session_state.out_dir_path_str:
        out_dir_to_save_exec_main_run = Path(st.session_state.out_dir_path_str)
        if out_dir_to_save_exec_main_run.exists():
            st.markdown("---")
            st.header("3. " + _("Save Analysis Results"))
            current_save_mode_exec_main_run = st.session_state.save_mode_selectbox_widget
            if current_save_mode_exec_main_run == _("Save to folder"):
                st.info(_("Output folder") + f": `{out_dir_to_save_exec_main_run}`")
                st.markdown(_("Open the above path in Explorer."))
            else: # ZIP Download
                zip_base_name_exec_main_run = f"ShiftSuite_Analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                if st.session_state.work_root_path_str is None:
                    st.error("一時作業ディレクトリが見つかりません。ZIPファイルの作成に失敗しました。")
                else:
                    work_root_for_zip_dl_exec_main_run = Path(st.session_state.work_root_path_str)
                    zip_path_obj_to_download_exec_main_run = work_root_for_zip_dl_exec_main_run / f"{zip_base_name_exec_main_run}.zip"
                    try:
                        with zipfile.ZipFile(zip_path_obj_to_download_exec_main_run, 'w', zipfile.ZIP_DEFLATED) as zf_dl_exec_main_run:
                            for file_to_zip_dl_exec_main_run in out_dir_to_save_exec_main_run.rglob('*'):
                                if file_to_zip_dl_exec_main_run.is_file():
                                    zf_dl_exec_main_run.write(file_to_zip_dl_exec_main_run, file_to_zip_dl_exec_main_run.relative_to(out_dir_to_save_exec_main_run))
                        with open(zip_path_obj_to_download_exec_main_run, "rb") as fp_zip_data_to_download_dl_exec_main_run:
                            st.download_button(label=_("Download analysis results as ZIP"), data=fp_zip_data_to_download_dl_exec_main_run,
                                               file_name=f"{zip_base_name_exec_main_run}.zip", mime="application/zip", use_container_width=True)
                        log.info(f"ZIPファイルを作成し、ダウンロードボタンを表示しました: {zip_path_obj_to_download_exec_main_run}")
                    except Exception as e_zip_final_exec_run_main_ex_v3:
                        st.error(_("Error creating ZIP file") + f": {e_zip_final_exec_run_main_ex_v3}")
                        log.error(f"ZIP作成エラー (最終段階): {e_zip_final_exec_run_main_ex_v3}", exc_info=True)
        else: 
            log.warning(f"解析は完了しましたが、出力ディレクトリ '{out_dir_to_save_exec_main_run}' が見つかりません。")

if st.session_state.get("analysis_done", False) and \
   _("Leave Analysis") in st.session_state.get("ext_opts_multiselect_widget", []) and \
   st.session_state.get("leave_analysis_results"):
    st.divider()
    st.header("📊 " + _("Leave Analysis") + " 結果")
    results = st.session_state.leave_analysis_results
    
    tab_leave_requested, tab_leave_paid, tab_leave_staff_detail = st.tabs([
        "希望休 分析", 
        "有給休暇 分析", 
        "職員別 休暇リスト"
    ])
    
    with tab_leave_requested:
        st.subheader("希望休の傾向")
        if LEAVE_TYPE_REQUESTED in st.session_state.get("leave_analysis_target_types_widget", []):
            summary_dow_req = results.get('summary_dow_requested')
            if summary_dow_req is not None and not summary_dow_req.empty:
                st.write("曜日別の希望休取得件数:")
                st.bar_chart(summary_dow_req.set_index('period_unit')['total_leave_days'])
            else:
                st.write("曜日別の希望休データはありません。")
            
            summary_month_period_req = results.get('summary_month_period_requested')
            if summary_month_period_req is not None and not summary_month_period_req.empty:
                st.write("月初・月中・月末別の希望休取得件数:")
                st.bar_chart(summary_month_period_req.set_index('period_unit')['total_leave_days'])
            else:
                st.write("月初・月中・月末別の希望休データはありません。")
            
            summary_month_req = results.get('summary_month_requested')
            if summary_month_req is not None and not summary_month_req.empty:
                st.write("月別の希望休取得件数:")
                st.line_chart(summary_month_req.set_index('period_unit')['total_leave_days'])
            else:
                st.write("月別の希望休データはありません。")
            
            concentration_req = results.get('concentration_requested')
            if concentration_req is not None and not concentration_req.empty:
                concentrated_days_req = concentration_req[concentration_req['is_concentrated']]
                if not concentrated_days_req.empty:
                    st.write(f"希望休が {st.session_state.leave_concentration_threshold_widget} 人以上集中している日:")
                    st.dataframe(
                        concentrated_days_req[['date', 'leave_applicants_count']].rename(
                            columns={'date':'日付', 'leave_applicants_count':'希望休取得者数'}
                        ).reset_index(drop=True)
                    )
                else:
                    st.write(f"希望休が {st.session_state.leave_concentration_threshold_widget} 人以上集中している日はありませんでした。")
            else:
                st.write("希望休の集中度データはありません。")
        else:
            st.info("希望休は分析対象として選択されていません。")
            
        if LEAVE_TYPE_REQUESTED in st.session_state.get("leave_analysis_target_types_widget", []):
            daily_leave_df = results.get('daily_leave_counts')
            if daily_leave_df is not None and not daily_leave_df.empty:
                requested_leave_daily = daily_leave_df[daily_leave_df['leave_type'] == LEAVE_TYPE_REQUESTED].copy()
                
                if not requested_leave_daily.empty:
                    st.subheader("期間別の希望休取得職員")
                    
                    with st.expander("曜日別の希望休取得職員", expanded=False):
                        staff_by_dow = leave_analyzer.get_staff_by_period(
                            requested_leave_daily,
                            period='dayofweek',
                            leave_type=LEAVE_TYPE_REQUESTED
                        )
                        
                        for dow, staff_list in staff_by_dow.items():
                            st.write(f"**{dow}**")
                            if staff_list:
                                st.write(", ".join(staff_list))
                            else:
                                st.write("（該当する職員はいません）")
                            st.divider()
                    
                    with st.expander("月内期間別の希望休取得職員", expanded=False):
                        staff_by_month_period = leave_analyzer.get_staff_by_period(
                            requested_leave_daily,
                            period='month_period',
                            leave_type=LEAVE_TYPE_REQUESTED
                        )
                        
                        for period, staff_list in staff_by_month_period.items():
                            st.write(f"**{period}**")
                            if staff_list:
                                st.write(", ".join(staff_list))
                            else:
                                st.write("（該当する職員はいません）")
                            st.divider()
    
    with tab_leave_paid:
        st.subheader("有給休暇の傾向 (終日のみ)")
        if LEAVE_TYPE_PAID in st.session_state.get("leave_analysis_target_types_widget", []):
            summary_dow_paid = results.get('summary_dow_paid')
            if summary_dow_paid is not None and not summary_dow_paid.empty:
                st.write("曜日別の有給休暇取得日数:")
                st.bar_chart(summary_dow_paid.set_index('period_unit')['total_leave_days'])
            else:
                st.write("曜日別の有給休暇データはありません。")
            
            summary_month_paid = results.get('summary_month_paid')
            if summary_month_paid is not None and not summary_month_paid.empty:
                st.write("月別の有給休暇取得日数:")
                st.line_chart(summary_month_paid.set_index('period_unit')['total_leave_days'])
            else:
                st.write("月別の有給休暇データはありません。")
        else:
            st.info("有給休暇は分析対象として選択されていません。")
            
        if LEAVE_TYPE_PAID in st.session_state.get("leave_analysis_target_types_widget", []):
            daily_leave_df = results.get('daily_leave_counts')
            if daily_leave_df is not None and not daily_leave_df.empty:
                paid_leave_daily = daily_leave_df[daily_leave_df['leave_type'] == LEAVE_TYPE_PAID].copy()
                
                if not paid_leave_daily.empty:
                    st.subheader("期間別の有給休暇取得職員")
                    
                    with st.expander("曜日別の有給休暇取得職員", expanded=False):
                        staff_by_dow = leave_analyzer.get_staff_by_period(
                            paid_leave_daily,
                            period='dayofweek',
                            leave_type=LEAVE_TYPE_PAID
                        )
                        
                        for dow, staff_list in staff_by_dow.items():
                            st.write(f"**{dow}**")
                            if staff_list:
                                st.write(", ".join(staff_list))
                            else:
                                st.write("（該当する職員はいません）")
                            st.divider()
                    
                    with st.expander("月内期間別の有給休暇取得職員", expanded=False):
                        staff_by_month_period = leave_analyzer.get_staff_by_period(
                            paid_leave_daily,
                            period='month_period',
                            leave_type=LEAVE_TYPE_PAID
                        )
                        
                        for period, staff_list in staff_by_month_period.items():
                            st.write(f"**{period}**")
                            if staff_list:
                                st.write(", ".join(staff_list))
                            else:
                                st.write("（該当する職員はいません）")
                            st.divider()
            
    with tab_leave_staff_detail:
        st.subheader("職員別 休暇リスト (終日希望休・終日有給)")
        staff_leave_list_df = results.get('staff_leave_list')
        if staff_leave_list_df is not None and not staff_leave_list_df.empty:
            all_staff_names = sorted(staff_leave_list_df['staff'].unique())
            selected_staff_for_detail = st.selectbox(
                "詳細を表示する職員を選択", 
                options=["全員表示"] + all_staff_names, 
                key="leave_detail_staff_select"
            )
            if selected_staff_for_detail == "全員表示":
                st.dataframe(staff_leave_list_df, height=400, use_container_width=True)
            else:
                filtered_df = staff_leave_list_df[staff_leave_list_df['staff'] == selected_staff_for_detail]
                st.dataframe(
                    filtered_df, 
                    height=400, use_container_width=True
                )
                
                if not filtered_df.empty:
                    st.subheader(f"{selected_staff_for_detail}の休暇傾向分析")
                    
                    daily_leave_df = results.get('daily_leave_counts')
                    if daily_leave_df is not None and not daily_leave_df.empty:
                        staff_daily_leave = daily_leave_df[daily_leave_df['staff'] == selected_staff_for_detail].copy()
                        
                        if not staff_daily_leave.empty:
                            leave_types = sorted(staff_daily_leave['leave_type'].unique())
                            for leave_type in leave_types:
                                st.write(f"### {leave_type}の傾向")
                                type_data = staff_daily_leave[staff_daily_leave['leave_type'] == leave_type]
                                
                                dow_summary = leave_analyzer.summarize_leave_by_day_count(type_data, period='dayofweek')
                                if not dow_summary.empty:
                                    st.write("曜日別の取得件数:")
                                    st.bar_chart(dow_summary.set_index('period_unit')['total_leave_days'])
                                else:
                                    st.write("曜日別データはありません。")
                                
                                month_period_summary = leave_analyzer.summarize_leave_by_day_count(type_data, period='month_period')
                                if not month_period_summary.empty:
                                    st.write("月初・月中・月末別の取得件数:")
                                    st.bar_chart(month_period_summary.set_index('period_unit')['total_leave_days'])
                                else:
                                    st.write("月内期間別データはありません。")
                                
                                month_summary = leave_analyzer.summarize_leave_by_day_count(type_data, period='month')
                                if not month_summary.empty:
                                    st.write("月別の取得件数:")
                                    st.line_chart(month_summary.set_index('period_unit')['total_leave_days'])
                                else:
                                    st.write("月別データはありません。")
                        else:
                            st.info(f"{selected_staff_for_detail}の休暇データがありません。")
                    else:
                        st.info("職員別の傾向分析に必要なデータがありません。")
        else:
            st.write("表示できる職員別の休暇データがありません。")

# ─────────────────────────────  app.py  (Part 3 / 3)  ──────────────────────────



def display_overview_tab(tab_container, data_dir):
    with tab_container:
        st.subheader(_("Overview"))
        fp_overview = data_dir / "overview.xlsx"
        if fp_overview.exists():
            try:
                df_overview = pd.read_excel(fp_overview, index_col=0)
                st.dataframe(df_overview, use_container_width=True)
            except Exception as e: st.error(f"overview.xlsx 表示エラー: {e}")
        else: st.info(_("Overview") + " (overview.xlsx) " + _("が見つかりません。"))

def display_heatmap_tab(tab_container, data_dir):
    with tab_container:
        st.subheader(_("Heatmap"))
        fp_heat = data_dir / "heat_ALL.xlsx"
        if fp_heat.exists():
            try:
                df_heat = pd.read_excel(fp_heat, index_col=0)
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    display_option = st.radio(_("Display Option"), ["Staff", "Need", "Ratio"], key="dash_heat_display_option")
                with col2:
                    if display_option == "Ratio":
                        zmax = st.slider(_("Max Ratio Value"), min_value=1.0, max_value=5.0, value=2.0, step=0.1, key="dash_heat_zmax")
                
                if display_option == "Staff":
                    if "staff" in df_heat.columns and not df_heat.empty:
                        staff_display_df = df_heat.pivot(index="time", columns="date", values="staff")
                        fig = px.imshow(staff_display_df, aspect="auto", color_continuous_scale=px.colors.sequential.Viridis, labels={"x":_("Date"),"y":_("Time"),"color":_("Staff Count")})
                    else:
                        st.warning("Staff表示に必要な'staff'列または日付データが見つかりません。")
                        fig = go.Figure()
                elif display_option == "Need":
                    if "need" in df_heat.columns and not df_heat.empty:
                        need_display_df = df_heat.pivot(index="time", columns="date", values="need")
                        fig = px.imshow(need_display_df, aspect="auto", color_continuous_scale=px.colors.sequential.Plasma, labels={"x":_("Date"),"y":_("Time"),"color":_("Need Count")})
                    else:
                        st.warning("Need表示に必要な'need'列または日付データが見つかりません。")
                        fig = go.Figure()
                else:  # Ratio
                    if "staff" in df_heat.columns and "need" in df_heat.columns and not df_heat.empty:
                        staff_display_df = df_heat.pivot(index="time", columns="date", values="staff")
                        need_display_df = df_heat.pivot(index="time", columns="date", values="need")
                        if not need_display_df.empty and (need_display_df > 0).any().any():
                            ratio_display_df = staff_display_df / need_display_df
                            ratio_display_df = ratio_display_df.clip(upper=zmax)
                            fig = px.imshow(ratio_display_df, aspect="auto", color_continuous_scale=px.colors.sequential.RdBu_r, zmin=0, zmax=zmax, labels={"x":_("Date"),"y":_("Time"),"color":_("Ratio (staff ÷ need)")})
                        else:
                            st.warning("Ratio表示に必要な'need'列データが0または存在しません。")
                            fig = go.Figure()
                    else:
                        st.warning("Ratio表示に必要な'staff'列、'need'列、または日付データが見つかりません。")
                        fig = go.Figure()
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e: st.error(f"ヒートマップ表示エラー: {e}")
        else: st.info(_("Heatmap") + " (heat_ALL.xlsx) " + _("が見つかりません。"))

def display_shortage_tab(tab_container, data_dir):
    with tab_container:
        st.subheader(_("Shortage"))
        fp_s_role = data_dir / "shortage_role.xlsx"
        if fp_s_role.exists():
            try:
                df_s_role = pd.read_excel(fp_s_role); st.dataframe(df_s_role,use_container_width=True,hide_index=True)
                if "role" in df_s_role and "lack_h" in df_s_role: st.bar_chart(df_s_role.set_index("role")["lack_h"], color="#FFA500")
            except Exception as e: st.error(f"shortage_role.xlsx 表示エラー: {e}")
        else: st.info(_("Shortage") + " (shortage_role.xlsx) " + _("が見つかりません。"))
        st.markdown("---")
        fp_s_time = data_dir / "shortage_time.xlsx"
        if fp_s_time.exists():
            try:
                df_s_time = pd.read_excel(fp_s_time, index_col=0)
                st.write(_("Shortage by Time (count per day)"))
                avail_dates = df_s_time.columns.tolist()
                if avail_dates:
                    sel_date = st.selectbox(_("Select date to display"), avail_dates, key="dash_short_time_date")
                    if sel_date: st.bar_chart(df_s_time[sel_date])
                else: st.info(_("No date columns in shortage data."))
                with st.expander(_("Display all time-slot shortage data")): st.dataframe(df_s_time, use_container_width=True)
            except Exception as e: st.error(f"shortage_time.xlsx 表示エラー: {e}")
        else: st.info(_("Shortage") + " (shortage_time.xlsx) " + _("が見つかりません。"))
        
def display_fatigue_tab(tab_container, data_dir):
    with tab_container:
        st.subheader(_("Fatigue Score per Staff"))
        fp = data_dir / "fatigue_score.xlsx"
        if fp.exists():
            try:
                df = pd.read_excel(fp) 
                st.dataframe(df, use_container_width=True, hide_index=True)
                if "fatigue_score" in df and "staff" in df: 
                    st.bar_chart(df.set_index("staff")["fatigue_score"])
            except Exception as e: st.error(f"fatigue_score.xlsx 表示エラー: {e}")
        else: st.info(_("Fatigue") + " (fatigue_score.xlsx) " + _("が見つかりません。"))

def display_forecast_tab(tab_container, data_dir):
    with tab_container:
        st.subheader(_("Demand Forecast (yhat)"))
        fp_fc = data_dir / "forecast.xlsx"
        if fp_fc.exists():
            try:
                df_fc = pd.read_excel(fp_fc, parse_dates=["ds"])
                fig = go.Figure()
                if "ds" in df_fc and "yhat" in df_fc:
                    fig.add_trace(go.Scatter(x=df_fc["ds"], y=df_fc["yhat"], mode='lines+markers', name=_("Demand Forecast (yhat)")))
                fp_demand = data_dir / "demand_series.csv"
                if fp_demand.exists():
                    df_actual = pd.read_csv(fp_demand, parse_dates=["ds"])
                    if "ds" in df_actual and "y" in df_actual:
                         fig.add_trace(go.Scatter(x=df_actual["ds"], y=df_actual["y"], mode='lines', name=_("Actual (y)"), line=dict(dash='dash')))
                fig.update_layout(title=_("Demand Forecast vs Actual"), xaxis_title=_("Date"), yaxis_title=_("Demand"))
                st.plotly_chart(fig, use_container_width=True)
                with st.expander(_("Display forecast data")): st.dataframe(df_fc, use_container_width=True, hide_index=True)
            except Exception as e: st.error(f"forecast.xlsx 表示エラー: {e}")
        else: st.info(_("Forecast") + " (forecast.xlsx) " + _("が見つかりません。"))

def display_fairness_tab(tab_container, data_dir):
    with tab_container:
        st.subheader(_("Fairness (Night Shift Ratio)"))
        fp = data_dir / "fairness_after.xlsx"
        if fp.exists():
            try:
                df = pd.read_excel(fp); st.dataframe(df, use_container_width=True, hide_index=True)
                if "staff" in df and "night_ratio" in df: st.bar_chart(df.set_index("staff")["night_ratio"], color="#FF8C00")
            except Exception as e: st.error(f"fairness_after.xlsx 表示エラー: {e}")
        else: st.info(_("Fairness") + " (fairness_after.xlsx) " + _("が見つかりません。"))

def display_costsim_tab(tab_container, data_dir):
    with tab_container:
        st.subheader(_("Cost Simulation (Million ¥)"))
        fp = data_dir / "cost_benefit.xlsx"
        if fp.exists():
            try:
                df = pd.read_excel(fp, index_col=0)
                if "Cost_Million" in df: st.bar_chart(df["Cost_Million"])
                st.dataframe(df, use_container_width=True)
            except Exception as e: st.error(f"cost_benefit.xlsx 表示エラー: {e}")
        else: st.info(_("Cost Sim") + " (cost_benefit.xlsx) " + _("が見つかりません。"))

def display_hireplan_tab(tab_container, data_dir):
    with tab_container:
        st.subheader(_("Hiring Plan (Needed FTE)"))
        fp = data_dir / "hire_plan.xlsx"
        if fp.exists():
            try:
                xls = pd.ExcelFile(fp)
                if "hire_plan" in xls.sheet_names:
                    df_plan = xls.parse("hire_plan"); st.dataframe(df_plan, use_container_width=True, hide_index=True)
                    if "role" in df_plan and "hire_need" in df_plan: st.bar_chart(df_plan.set_index("role")["hire_need"])
                if "meta" in xls.sheet_names:
                    with st.expander(_("Hiring Plan Parameters")): st.table(xls.parse("meta"))
            except Exception as e: st.error(f"hire_plan.xlsx 表示エラー: {e}")
        else: st.info(_("Hire Plan") + " (hire_plan.xlsx) " + _("が見つかりません。"))

def display_ppt_tab(tab_container, data_dir_ignored): 
    with tab_container:
        st.subheader(_("PPT Report"))
        if st.button(_("Generate PowerPoint Report (β)"), key="dash_generate_ppt_button", use_container_width=True):
            st.info(_("Generating PowerPoint report..."))
            try:
                from pptx import Presentation 
                prs = Presentation()
                prs.slides.add_slide(prs.slide_layouts[5]).shapes.title.text = "ダッシュボードからのレポート"
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as tmp_ppt_dash:
                    temp_ppt_dash_path = tmp_ppt_dash.name
                prs.save(temp_ppt_dash_path)
                with open(temp_ppt_dash_path, "rb") as ppt_file_data_dash:
                    st.download_button(
                        label=_("Download Report (PPTX)"), data=ppt_file_data_dash,
                        file_name=f"ShiftSuite_Dashboard_Report_{dt.datetime.now().strftime('%Y%m%d_%H%M')}.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True
                    )
                Path(temp_ppt_dash_path).unlink()
                st.success(_("PowerPoint report ready."))
            except ImportError: st.error(_("python-pptx library required for PPT"))
            except Exception as e_ppt_dash: st.error(_("Error generating PowerPoint report") + f": {e_ppt_dash}")
        else:
            st.markdown(_("Click button to generate report."))

st.divider()
st.header(_("Dashboard (Upload ZIP)"))
zip_file_uploaded_dash_final_v3_display_main_dash = st.file_uploader(_("Upload ZIP file of 'out' folder"), type=["zip"], key="dashboard_zip_uploader_widget_final_v3_key_dash")

if zip_file_uploaded_dash_final_v3_display_main_dash:
    dashboard_temp_base = Path(tempfile.gettempdir()) / "ShiftSuite_Dash_Uploads"
    dashboard_temp_base.mkdir(parents=True, exist_ok=True)
    current_dash_tmp_dir = Path(tempfile.mkdtemp(prefix="dash_", dir=dashboard_temp_base))
    log.info(f"ダッシュボード用一時ディレクトリを作成: {current_dash_tmp_dir}")
    extracted_data_dir: Optional[Path] = None
    try:
        with zipfile.ZipFile(io.BytesIO(zip_file_uploaded_dash_final_v3_display_main_dash.read())) as zf:
            zf.extractall(current_dash_tmp_dir)
            if (current_dash_tmp_dir / "out").exists() and (current_dash_tmp_dir / "out" / "heat_ALL.xlsx").exists():
                extracted_data_dir = current_dash_tmp_dir / "out"
            elif (current_dash_tmp_dir / "heat_ALL.xlsx").exists():
                 extracted_data_dir = current_dash_tmp_dir
            else:
                found_heat_all = list(current_dash_tmp_dir.rglob("heat_ALL.xlsx"))
                if found_heat_all: 
                    extracted_data_dir = found_heat_all[0].parent
                else: 
                    st.error(_("heat_ALL.xlsx not found in ZIP"))
                    log.error(f"ZIP展開後、heat_ALL.xlsx が見つかりません in {current_dash_tmp_dir}")
                    st.stop()
        log.info(f"ダッシュボード表示用のデータディレクトリ: {extracted_data_dir}")
    except Exception as e_zip:
        st.error(_("Error during ZIP file extraction") + f": {e_zip}")
        log.error(f"ZIP展開中エラー: {e_zip}", exc_info=True)
        st.stop()

    import plotly.express as px
    import plotly.graph_objects as go

    tab_keys_en_dash = ["Overview", "Heatmap", "Shortage", "Fatigue", "Forecast", "Fairness", "Cost Sim", "Hire Plan", "PPT Report"]
    tab_labels_dash = [_(key) for key in tab_keys_en_dash]
    tabs_obj_dash = st.tabs(tab_labels_dash)

    if extracted_data_dir:
        display_overview_tab(tabs_obj_dash[0], extracted_data_dir)
        display_heatmap_tab(tabs_obj_dash[1], extracted_data_dir)
        display_shortage_tab(tabs_obj_dash[2], extracted_data_dir)
        display_fatigue_tab(tabs_obj_dash[3], extracted_data_dir)
        display_forecast_tab(tabs_obj_dash[4], extracted_data_dir)
        display_fairness_tab(tabs_obj_dash[5], extracted_data_dir)
        display_costsim_tab(tabs_obj_dash[6], extracted_data_dir)
        display_hireplan_tab(tabs_obj_dash[7], extracted_data_dir)
        display_ppt_tab(tabs_obj_dash[8], extracted_data_dir)
    else:
        st.warning("ダッシュボードを表示するためのデータがロードされていません。ZIPファイルをアップロードしてください。")

if __name__ == "__main__" and not st_runtime_exists():
    import argparse
    log.info("CLIモードでapp.pyを実行します。")
    parser = argparse.ArgumentParser(description="Shift-Suite CLI (app.py経由のデバッグ用)")
    parser.add_argument("xlsx_file_cli", help="Excel シフト原本 (.xlsx)")
    parser.add_argument("--sheets_cli", nargs="+", required=True, help="解析対象のシート名")
    parser.add_argument("--header_cli", type=int, default=3, help="ヘッダー開始行 (1-indexed)")
    try:
        cli_args = parser.parse_args()
        log.info(f"CLI Args: file='{cli_args.xlsx_file_cli}', sheets={cli_args.sheets_cli}, header={cli_args.header_cli}")
    except SystemExit: 
        pass
    except Exception as e_cli:
        log.error(f"CLIモードでの実行中にエラー: {e_cli}", exc_info=True)
