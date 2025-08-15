"""
build_stats.py ― KPI 集約＋全体／月別集計 (改修案)
----------------------------------------
v0.6.4 (休業日対応の稼働日数計算の確実性向上、集計対象フィルタリング)
- v0.6.3: デバッグログ強化。
- v0.6.2: pd.Categorical の categories 引数の重複エラーを修正。
- v0.6.0: heatmap.meta.json から推定休業日を読み込み、
          need計算と稼働日数計算に反映。
----------------------------------------
"""

from __future__ import annotations

import datetime as dt
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

import numpy as np
import pandas as pd

from .constants import SUMMARY5, SLOT_HOURS, BUILD_STATS_PARAMETERS
from .utils import _parse_as_date

log = logging.getLogger(__name__)
if not log.handlers:
    if not logging.getLogger().hasHandlers():  # pragma: no cover
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] %(levelname)s - %(name)s [%(module)s.%(funcName)s:%(lineno)d] - %(message)s"
            )
        )
        log.addHandler(handler)
    log.setLevel(logging.DEBUG)


def _check_files_exist(out_dir: Path, required: Iterable[str]) -> List[str]:
    missing = [f for f in required if not (out_dir / f).exists()]
    if missing:
        log.error(f"Missing upstream outputs: {missing}")
    else:
        log.debug("All required upstream files exist.")
    return missing


def build_stats(
    out_dir: str | Path,
    *,
    holidays: Iterable[dt.date] | None = None,
    wage_direct: float = 0.0,
    wage_temp: float = 0.0,
    penalty_per_lack: float = 0.0,
) -> None:
    """Create stats.xlsx with optional cost estimation columns.

    Parameters
    ----------
    out_dir:
        Output directory containing heatmap files.
    holidays:
        Holiday dates to exclude from working day counts.
    wage_direct:
        Hourly wage for direct employees used for excess cost estimation.
    wage_temp:
        Hourly cost for temporary staff to fill shortages.
    penalty_per_lack:
        Penalty or opportunity cost per hour of shortage.
    """
    out_dir_path = Path(out_dir)
    stats_fp = out_dir_path / "stats_error.parquet"
    log.info(f"=== build_stats start (out_dir={out_dir_path}) ===")

    required_files = ["heat_ALL.parquet"]
    missing = _check_files_exist(out_dir_path, required_files)
    if missing:
        log.error(
            f"必要なファイルが見つからないため、stats処理をスキップします: {missing}"
        )
        try:
            pd.DataFrame(
                {"error": [f"Missing required files: {', '.join(missing)}"]}
            ).to_parquet(stats_fp, index=False)
        except Exception as e_write_err:
            log.error(f"エラーログ用 stats.xlsx の書き出し失敗: {e_write_err}")
        return

    estimated_holidays_set: Set[dt.date] = set(holidays or [])

    try:
        heat_all_df = pd.read_parquet(out_dir_path / "heat_ALL.parquet")
        log.debug(f"heat_ALL.parquet を読み込みました。Shape: {heat_all_df.shape}")
    except Exception as e:
        log.error(
            f"heat_ALL.parquet の読み込み中にエラーが発生しました: {e}", exc_info=True
        )
        try:
            pd.DataFrame(
                {"error": [f"Error reading heat_ALL.parquet: {e}"]}
            ).to_parquet(
                stats_fp,
                index=False,
            )
        except Exception as e_write_err_read:
            log.error(
                f"読み込みエラー時のエラーログ用 stats.xlsx の書き出し失敗: {e_write_err_read}"
            )
        return

    slot_hours = SLOT_HOURS
    if len(heat_all_df.index) > 1:
        try:
            time_index_dt_series = pd.to_datetime(
                heat_all_df.index, format="%H:%M", errors="coerce"
            )
            valid_times = time_index_dt_series.dropna()
            if len(valid_times) > 1:
                time1_dt = valid_times[0]
                time2_dt = valid_times[1]
                slot_hours = (time2_dt - time1_dt).total_seconds() / 3600
                if slot_hours <= 0:
                    slot_hours = SLOT_HOURS
                    log.warning(f"スロット幅計算結果0以下、{SLOT_HOURS}h使用")
            else:
                slot_hours = SLOT_HOURS
                log.warning(f"有効時間帯インデックス2未満、{SLOT_HOURS}h使用")
        except Exception as e_slot:
            slot_hours = SLOT_HOURS
            log.warning(f"スロット幅計算失敗({e_slot})、{SLOT_HOURS}h使用")
    log.info(f"計算に使用するスロット幅: {slot_hours} 時間")

    date_columns_in_heat = [
        str(col) for col in heat_all_df.columns if _parse_as_date(str(col)) is not None
    ]
    if not date_columns_in_heat:
        log.error(
            "heat_ALL.parquet に有効な日付列が見つかりません。統計処理を中止します。"
        )
        return

    num_total_date_columns = len(date_columns_in_heat)

    log.debug("--- 稼働日数計算デバッグ ---")
    log.debug(f"date_columns_in_heat (最初の5件): {date_columns_in_heat[:5]}")
    log.debug(
        f"estimated_holidays_set (読み込み結果, 最初の5件): {list(estimated_holidays_set)[:5]}"
    )

    actual_working_date_strs = []
    if date_columns_in_heat:
        for d_str in date_columns_in_heat:
            parsed_date_obj = _parse_as_date(d_str)
            is_holiday = False
            if parsed_date_obj:
                if estimated_holidays_set and parsed_date_obj in estimated_holidays_set:
                    is_holiday = True

            log.debug(
                f"  処理中日付列: '{d_str}' -> パース後: {parsed_date_obj} (型: {type(parsed_date_obj)}) -> 休業日か: {is_holiday}"
            )
            if parsed_date_obj and not is_holiday:
                actual_working_date_strs.append(d_str)
            elif not parsed_date_obj:
                log.warning(
                    f"    '{d_str}' は日付にパースできなかったため、稼働日数の計算から除外されます（要確認）。"
                )
    else:
        actual_working_date_strs = []

    num_actual_working_days = len(actual_working_date_strs)
    log.debug("--- デバッグ終了 ---")
    log.info(
        f"有効な日付列: {num_total_date_columns} 個。うち、推定休業日を除いた稼働日数: {num_actual_working_days} 日。"
    )

    if (
        num_actual_working_days == 0
        and num_total_date_columns > 0
        and not estimated_holidays_set
    ):  # 休業日セットが空なのに稼働日0はおかしい
        log.error(
            "稼働日数が0と計算されましたが、推定された休業日もありません。日付パースまたはデータに問題がある可能性があります。"
        )
    elif num_actual_working_days == 0 and num_total_date_columns > 0:
        log.warning(
            "全ての分析対象日が休業日と推定されたか、有効な稼働日がありませんでした。平均値の計算結果は0またはNaNになる可能性があります。"
        )

    time_labels = heat_all_df.index
    staff_actual_df = (
        heat_all_df[date_columns_in_heat].reindex(index=time_labels).fillna(0)
    )

    if "need" not in heat_all_df.columns or "upper" not in heat_all_df.columns:
        log.error(
            "'need' または 'upper' 列が heat_ALL.parquet に見つかりません。処理を中止します。"
        )
        return
    need_per_timeslot_series_orig = (
        heat_all_df["need"].reindex(index=time_labels).fillna(0).clip(lower=0)
    )
    upper_per_timeslot_series_orig = (
        heat_all_df["upper"].reindex(index=time_labels).fillna(0).clip(lower=0)
    )

    daily_lack_count_df = pd.DataFrame(
        index=staff_actual_df.index, columns=staff_actual_df.columns, dtype=float
    )
    daily_excess_count_df = pd.DataFrame(
        index=staff_actual_df.index, columns=staff_actual_df.columns, dtype=float
    )

    for date_col_str in staff_actual_df.columns:
        current_date_obj = _parse_as_date(date_col_str)
        #  休業日セットが空でないこと、かつ日付が有効であることも判定条件に加える
        if (
            estimated_holidays_set
            and current_date_obj
            and current_date_obj in estimated_holidays_set
        ):
            current_day_need = pd.Series(0, index=need_per_timeslot_series_orig.index)
            current_day_upper = staff_actual_df[date_col_str]
        else:
            current_day_need = need_per_timeslot_series_orig
            current_day_upper = upper_per_timeslot_series_orig
        daily_lack_count_df[date_col_str] = (
            current_day_need - staff_actual_df[date_col_str]
        ).clip(lower=0)
        daily_excess_count_df[date_col_str] = (
            staff_actual_df[date_col_str] - current_day_upper
        ).clip(lower=0)

    daily_metrics_data_for_df: List[Dict[str, Any]] = []  #  リストオブディクトに変更
    for date_col_name_original_str in date_columns_in_heat:
        parsed_date = _parse_as_date(date_col_name_original_str)
        if parsed_date is None:
            continue

        is_working_day_flag = 1 if parsed_date not in estimated_holidays_set else 0

        # 実績値は全日で計算するが、is_working_dayフラグで区別
        actual_slots_today = staff_actual_df[date_col_name_original_str].sum()
        # 不足と過剰は、休業日ならneed=0で再計算されたものに基づく
        lack_slots_today = daily_lack_count_df[date_col_name_original_str].sum()
        excess_slots_today = daily_excess_count_df[date_col_name_original_str].sum()

        daily_metrics_data_for_df.append(
            {
                "date": pd.to_datetime(
                    parsed_date
                ),  #  pd.to_datetimeでDatetimeIndex互換に
                "actual_slots": float(actual_slots_today),
                "actual_hours": float(actual_slots_today * slot_hours),
                "lack_slots": float(lack_slots_today),
                "lack_hours": float(lack_slots_today * slot_hours),
                "excess_slots": float(excess_slots_today),
                "excess_hours": float(excess_slots_today * slot_hours),
                "is_working_day": is_working_day_flag,
                "parsed_date_debug": parsed_date.isoformat(),  # デバッグ用にパースされた日付文字列も追加
            }
        )

    if not daily_metrics_data_for_df:
        log.error("日次メトリクスの計算結果が空になりました。処理を中止します。")
        try:
            pd.DataFrame({"error": ["No daily metrics were generated."]}).to_parquet(
                stats_fp,
                index=False,
            )
        except Exception as e_write_err_dm:
            log.error(
                f"日次メトリクス空エラー時のエラーログ用 stats.xlsx の書き出し失敗: {e_write_err_dm}"
            )
        return

    daily_metrics_df = pd.DataFrame(daily_metrics_data_for_df).set_index(
        "date"
    )  #  date列をindexに
    # is_working_day 以外を数値型に変換（既に行われているはずだが念のため）
    cols_to_numeric = [
        "actual_slots",
        "actual_hours",
        "lack_slots",
        "lack_hours",
        "excess_slots",
        "excess_hours",
    ]
    for col_to_num in cols_to_numeric:  #  変数名変更
        if col_to_num in daily_metrics_df.columns:
            daily_metrics_df[col_to_num] = pd.to_numeric(
                daily_metrics_df[col_to_num], errors="coerce"
            )
    daily_metrics_df["is_working_day"] = daily_metrics_df["is_working_day"].astype(int)

    log.debug(
        f"日次メトリクス計算完了 (daily_metrics_df):\n{daily_metrics_df.head().to_string()}"
    )

    # ══════════ Derived Indicators & Alerts ══════════
    alerts_rows: List[Dict[str, Any]] = []

    # --- night shift ratio per staff (threshold > 0.5) ---
    staff_stats_fp = out_dir_path / "staff_stats.xlsx"
    if staff_stats_fp.exists():
        try:
            df_staff_stats = pd.read_excel(staff_stats_fp, sheet_name="by_staff")
            if {"staff", "night_ratio"}.issubset(df_staff_stats.columns):
                high_night = df_staff_stats[df_staff_stats["night_ratio"] > BUILD_STATS_PARAMETERS["night_shift_ratio_threshold"]]
                for _, row in high_night.iterrows():
                    alerts_rows.append(
                        {
                            "category": "high_night_ratio",
                            "staff": row["staff"],
                            "value": float(row["night_ratio"]),
                        }
                    )
        except Exception as e:  # pragma: no cover - runtime warning only
            log.warning(f"night ratio alert calculation failed: {e}")

    # --- monthly shortage trend ---
    if not daily_metrics_df.empty and "lack_hours" in daily_metrics_df.columns:
        monthly_lack = (
            daily_metrics_df["lack_hours"]
            .groupby(daily_metrics_df.index.to_period("M"))
            .sum()
        )
        prev_period = None
        consecutive = 0
        for period, val in monthly_lack.items():
            alerts_rows.append(
                {
                    "category": "monthly_shortage",
                    "month": str(period),
                    "value": float(val),
                }
            )
            if val > 0:
                if prev_period is not None and (period - prev_period).n == 1:
                    consecutive += 1
                else:
                    consecutive = 1
                if consecutive >= BUILD_STATS_PARAMETERS["consecutive_shortage_months"]:
                    alerts_rows.append(
                        {
                            "category": "persistent_shortage",
                            "month": str(period),
                            "value": float(val),
                        }
                    )
            else:
                consecutive = 0
            prev_period = period

    alerts_df = pd.DataFrame(alerts_rows)

    overall_metrics = []
    denominator_for_avg = num_actual_working_days if num_actual_working_days > 0 else 1

    # Overall_Summary の集計対象は is_working_day == 1 の日のデータと、稼働日のDataFrameスライス
    daily_metrics_working_days_df = daily_metrics_df[
        daily_metrics_df["is_working_day"] == 1
    ]
    staff_actual_df_working_days = (
        staff_actual_df[actual_working_date_strs]
        if actual_working_date_strs
        else pd.DataFrame(index=staff_actual_df.index)
    )
    daily_lack_count_df_working_days = (
        daily_lack_count_df[actual_working_date_strs]
        if actual_working_date_strs
        else pd.DataFrame(index=daily_lack_count_df.index)
    )
    daily_excess_count_df_working_days = (
        daily_excess_count_df[actual_working_date_strs]
        if actual_working_date_strs
        else pd.DataFrame(index=daily_excess_count_df.index)
    )

    for (
        item_key,
        daily_values_df_cols_tuple,
        source_ts_df_filtered,
    ) in [  #  source_ts_df_key_part -> source_ts_df_filtered
        ("staff", ("actual_slots", "actual_hours"), staff_actual_df_working_days),
        ("lack", ("lack_slots", "lack_hours"), daily_lack_count_df_working_days),
        (
            "excess",
            ("excess_slots", "excess_hours"),
            daily_excess_count_df_working_days,
        ),
    ]:
        # daily_metrics_working_days_df から該当列を取得
        current_daily_values_subset_df = daily_metrics_working_days_df[
            list(daily_values_df_cols_tuple)
        ]

        total_period_slots = current_daily_values_subset_df[
            daily_values_df_cols_tuple[0]
        ].sum()
        total_period_hours = current_daily_values_subset_df[
            daily_values_df_cols_tuple[1]
        ].sum()

        sum_slots_per_working_day = (
            total_period_slots / denominator_for_avg if denominator_for_avg > 0 else 0
        )
        sum_hours_per_working_day = (
            total_period_hours / denominator_for_avg if denominator_for_avg > 0 else 0
        )

        overall_metrics.extend(
            [
                {
                    "summary_item": item_key,
                    "metric": "sum_value_per_working_day (slots)",
                    "value": sum_slots_per_working_day,
                },
                {
                    "summary_item": item_key,
                    "metric": "sum_value_per_working_day (hours)",
                    "value": sum_hours_per_working_day,
                },
                {
                    "summary_item": item_key,
                    "metric": f"total_value_working_period ({num_actual_working_days}days) (slots)",
                    "value": total_period_slots,
                },
                {
                    "summary_item": item_key,
                    "metric": f"total_value_working_period ({num_actual_working_days}days) (hours)",
                    "value": total_period_hours,
                },
            ]
        )
        if not source_ts_df_filtered.empty:
            all_values_flat = source_ts_df_filtered.values.flatten()
            all_values_flat_numeric = pd.to_numeric(all_values_flat, errors="coerce")
            all_values_flat_numeric = all_values_flat_numeric[
                ~np.isnan(all_values_flat_numeric)
            ]
            overall_metrics.extend(
                [
                    {
                        "summary_item": item_key,
                        "metric": "mean_value_per_timeslot_and_working_day",
                        "value": np.mean(all_values_flat_numeric)
                        if len(all_values_flat_numeric) > 0
                        else 0,
                    },
                    {
                        "summary_item": item_key,
                        "metric": "max_value_per_timeslot_and_working_day",
                        "value": np.max(all_values_flat_numeric)
                        if len(all_values_flat_numeric) > 0
                        else 0,
                    },
                    {
                        "summary_item": item_key,
                        "metric": "min_value_per_timeslot_and_working_day",
                        "value": np.min(all_values_flat_numeric)
                        if len(all_values_flat_numeric) > 0
                        else 0,
                    },
                ]
            )
        else:
            overall_metrics.extend(
                [
                    {
                        "summary_item": item_key,
                        "metric": "mean_value_per_timeslot_and_working_day",
                        "value": 0,
                    },
                    {
                        "summary_item": item_key,
                        "metric": "max_value_per_timeslot_and_working_day",
                        "value": 0,
                    },
                    {
                        "summary_item": item_key,
                        "metric": "min_value_per_timeslot_and_working_day",
                        "value": 0,
                    },
                ]
            )

    for item_key_repr, series_per_timeslot_repr in [
        ("need", need_per_timeslot_series_orig),
        ("upper", upper_per_timeslot_series_orig),
    ]:
        sum_slots_per_day_repr_val = (
            series_per_timeslot_repr.sum() if not series_per_timeslot_repr.empty else 0
        )
        sum_hours_per_day_repr_val = sum_slots_per_day_repr_val * slot_hours
        overall_metrics.extend(
            [
                {
                    "summary_item": item_key_repr,
                    "metric": "sum_value_per_day_representative (slots)",
                    "value": sum_slots_per_day_repr_val,
                },
                {
                    "summary_item": item_key_repr,
                    "metric": "sum_value_per_day_representative (hours)",
                    "value": sum_hours_per_day_repr_val,
                },
                {
                    "summary_item": item_key_repr,
                    "metric": f"total_value_period_representative ({num_total_date_columns}days) (slots)",
                    "value": sum_slots_per_day_repr_val * num_total_date_columns,
                },
                {
                    "summary_item": item_key_repr,
                    "metric": f"total_value_period_representative ({num_total_date_columns}days) (hours)",
                    "value": sum_hours_per_day_repr_val * num_total_date_columns,
                },
                {
                    "summary_item": item_key_repr,
                    "metric": "mean_value_per_timeslot_representative",
                    "value": series_per_timeslot_repr.mean()
                    if not series_per_timeslot_repr.empty
                    else 0,
                },
                {
                    "summary_item": item_key_repr,
                    "metric": "max_value_per_timeslot_representative",
                    "value": series_per_timeslot_repr.max()
                    if not series_per_timeslot_repr.empty
                    else 0,
                },
                {
                    "summary_item": item_key_repr,
                    "metric": "min_value_per_timeslot_representative",
                    "value": series_per_timeslot_repr.min()
                    if not series_per_timeslot_repr.empty
                    else 0,
                },
            ]
        )

    overall_df = pd.DataFrame(overall_metrics)
    if not overall_df.empty:
        overall_df["summary_item"] = pd.Categorical(
            overall_df["summary_item"], categories=SUMMARY5, ordered=True
        )
        overall_df = overall_df.sort_values("summary_item")
        mask_hours = overall_df["metric"].str.contains("(hours)")
        overall_df = overall_df.assign(
            estimated_excess_cost=lambda d: np.where(
                (d["summary_item"] == "excess") & mask_hours,
                d["value"] * wage_direct,
                np.nan,
            ),
            estimated_lack_cost_if_temporary_staff=lambda d: np.where(
                (d["summary_item"] == "lack") & mask_hours,
                d["value"] * wage_temp,
                np.nan,
            ),
            estimated_lack_penalty_cost=lambda d: np.where(
                (d["summary_item"] == "lack") & mask_hours,
                d["value"] * penalty_per_lack,
                np.nan,
            ),
        )
    log.debug(f"Overall summary 計算完了:\n{overall_df.head().to_string()}")

    monthly_summary_rows = []
    if daily_metrics_df.empty:
        log.warning(
            "Monthly_Summary: 日次メトリクスデータが空です。月別集計をスキップします。"
        )
        monthly_df = pd.DataFrame(
            {"message": ["No daily metrics for monthly summary."]}
        )
    else:
        if not isinstance(daily_metrics_df.index, pd.DatetimeIndex):
            daily_metrics_df.index = pd.to_datetime(daily_metrics_df.index)

        monthly_grouped = daily_metrics_df.groupby(
            daily_metrics_df.index.to_period("M")
        )
        for period_month, group_df_for_month_full in monthly_grouped:
            month_str_monthly = period_month.strftime("%Y-%m")
            group_df_for_month_working_days = group_df_for_month_full[
                group_df_for_month_full["is_working_day"] == 1
            ]
            total_days_with_data_in_month = len(group_df_for_month_full)
            working_days_in_month_for_avg = len(group_df_for_month_working_days)
            log.debug(
                f"Processing Monthly_Summary for month: {month_str_monthly}, total days with data: {total_days_with_data_in_month}, working days: {working_days_in_month_for_avg}"
            )
            denominator_for_monthly_avg_calc = (
                working_days_in_month_for_avg
                if working_days_in_month_for_avg > 0
                else 1
            )

            for item_key_monthly, slot_col_name_monthly, hour_col_name_monthly in [
                ("staff", "actual_slots", "actual_hours"),
                ("lack", "lack_slots", "lack_hours"),
                ("excess", "excess_slots", "excess_hours"),
            ]:
                row_data_monthly = {
                    "month": month_str_monthly,
                    "summary_item": item_key_monthly,
                    "days_in_month_with_data": total_days_with_data_in_month,
                    "working_days_in_month": working_days_in_month_for_avg,
                    "total_value_period_representative (slots)": np.nan,
                    "total_value_period_representative (hours)": np.nan,
                    "mean_daily_value_representative (slots)": np.nan,
                    "mean_daily_value_representative (hours)": np.nan,
                }
                if slot_col_name_monthly in group_df_for_month_working_days.columns:
                    slot_data_current_month = group_df_for_month_working_days[
                        slot_col_name_monthly
                    ].astype(float)
                    row_data_monthly["total_value_period (slots)"] = (
                        slot_data_current_month.sum()
                    )
                    row_data_monthly["mean_daily_value (slots)"] = (
                        slot_data_current_month.sum() / denominator_for_monthly_avg_calc
                        if denominator_for_monthly_avg_calc > 0
                        else 0
                    )
                else:
                    row_data_monthly["total_value_period (slots)"] = 0.0
                    row_data_monthly["mean_daily_value (slots)"] = 0.0

                if hour_col_name_monthly in group_df_for_month_working_days.columns:
                    hour_data_current_month = group_df_for_month_working_days[
                        hour_col_name_monthly
                    ].astype(float)
                    row_data_monthly["total_value_period (hours)"] = (
                        hour_data_current_month.sum()
                    )
                    row_data_monthly["mean_daily_value (hours)"] = (
                        hour_data_current_month.sum() / denominator_for_monthly_avg_calc
                        if denominator_for_monthly_avg_calc > 0
                        else 0
                    )
                else:
                    row_data_monthly["total_value_period (hours)"] = 0.0
                    row_data_monthly["mean_daily_value (hours)"] = 0.0
                monthly_summary_rows.append(row_data_monthly)

            for item_key_monthly_repr, series_per_timeslot_repr_val_monthly in [
                ("need", need_per_timeslot_series_orig),
                ("upper", upper_per_timeslot_series_orig),
            ]:
                daily_total_slots_repr_val_monthly = (
                    series_per_timeslot_repr_val_monthly.sum()
                    if not series_per_timeslot_repr_val_monthly.empty
                    else 0
                )
                daily_total_hours_repr_val_monthly = (
                    daily_total_slots_repr_val_monthly * slot_hours
                )
                total_slots_month_repr_val = (
                    daily_total_slots_repr_val_monthly * total_days_with_data_in_month
                )
                total_hours_month_repr_val = (
                    daily_total_hours_repr_val_monthly * total_days_with_data_in_month
                )
                monthly_summary_rows.append(
                    {
                        "month": month_str_monthly,
                        "summary_item": item_key_monthly_repr,
                        "days_in_month_with_data": total_days_with_data_in_month,
                        "working_days_in_month": working_days_in_month_for_avg,
                        "total_value_period (slots)": np.nan,
                        "total_value_period (hours)": np.nan,
                        "mean_daily_value (slots)": np.nan,
                        "mean_daily_value (hours)": np.nan,
                        "total_value_period_representative (slots)": total_slots_month_repr_val,
                        "total_value_period_representative (hours)": total_hours_month_repr_val,
                        "mean_daily_value_representative (slots)": daily_total_slots_repr_val_monthly,
                        "mean_daily_value_representative (hours)": daily_total_hours_repr_val_monthly,
                    }
                )

        monthly_df = pd.DataFrame(monthly_summary_rows)
        if not monthly_df.empty:
            expected_cols_monthly = [
                "month",
                "summary_item",
                "days_in_month_with_data",
                "working_days_in_month",
                "total_value_period (slots)",
                "total_value_period (hours)",
                "mean_daily_value (slots)",
                "mean_daily_value (hours)",
                "total_value_period_representative (slots)",
                "total_value_period_representative (hours)",
                "mean_daily_value_representative (slots)",
                "mean_daily_value_representative (hours)",
            ]
            for col_name_monthly_ex in expected_cols_monthly:
                if col_name_monthly_ex not in monthly_df.columns:
                    monthly_df[col_name_monthly_ex] = np.nan
            monthly_df["summary_item"] = pd.Categorical(
                monthly_df["summary_item"], categories=SUMMARY5, ordered=True
            )
            monthly_df = monthly_df.sort_values(
                by=["month", "summary_item"]
            ).reset_index(drop=True)

            def _cost_cols(d: pd.DataFrame) -> pd.DataFrame:
                mask_hours = d.columns.str.contains("(hours)")
                hour_col = next(
                    (
                        c
                        for c, m in zip(d.columns, mask_hours)
                        if m and c.startswith("total_value_period")
                    ),
                    None,
                )
                if hour_col:
                    d = d.assign(
                        estimated_excess_cost=lambda x: np.where(
                            x["summary_item"] == "excess",
                            x[hour_col] * wage_direct,
                            np.nan,
                        ),
                        estimated_lack_cost_if_temporary_staff=lambda x: np.where(
                            x["summary_item"] == "lack",
                            x[hour_col] * wage_temp,
                            np.nan,
                        ),
                        estimated_lack_penalty_cost=lambda x: np.where(
                            x["summary_item"] == "lack",
                            x[hour_col] * penalty_per_lack,
                            np.nan,
                        ),
                    )
                return d

            monthly_df = _cost_cols(monthly_df)
            log.debug(f"Monthly summary 計算完了:\n{monthly_df.head().to_string()}")
        else:
            log.warning("月別集計の結果が空になりました。")
            monthly_df = pd.DataFrame({"message": ["Monthly summary data is empty."]})

    try:
        if not overall_df.empty:
            overall_df.to_parquet(
                out_dir_path / "stats_overall_summary.parquet",
                index=False,
            )
        if not monthly_df.empty:
            monthly_df.to_parquet(
                out_dir_path / "stats_monthly_summary.parquet",
                index=False,
            )
        if not daily_metrics_df.empty:
            cols_to_output_dm = [
                col for col in daily_metrics_df.columns if col != "parsed_date_debug"
            ]
            daily_metrics_df[cols_to_output_dm].to_parquet(
                out_dir_path / "stats_daily_metrics_raw.parquet",
                index=True,
            )
        if not alerts_df.empty:
            alerts_df.to_parquet(
                out_dir_path / "stats_alerts.parquet",
                index=False,
            )
        log.info("✅ stats parquet files saved")
    except Exception as e:
        log.error(f"stats parquet export error: {e}", exc_info=True)

    # text summary
    try:
        summary_fp = out_dir_path / "stats_summary.txt"
        lack_total = int(
            round(
                overall_df.loc[
                    (overall_df["summary_item"] == "lack")
                    & overall_df["metric"].str.contains("(hours)"),
                    "value",
                ].sum()
            )
        )
        excess_total = int(
            round(
                overall_df.loc[
                    (overall_df["summary_item"] == "excess")
                    & overall_df["metric"].str.contains("(hours)"),
                    "value",
                ].sum()
            )
        )
        lines = [
            f"lack_hours_total: {lack_total}",
            f"excess_hours_total: {excess_total}",
        ]
        summary_fp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        log.debug(f"failed to write stats summary: {e}")

    log.info("=== build_stats end ===")
