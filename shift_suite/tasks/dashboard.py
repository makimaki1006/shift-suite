from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import plotly.express as px
from shift_suite.i18n import translate as _
from .constants import SUMMARY5 as SUMMARY5_CONST
from . import leave_analyzer


def employee_overview(score_df: pd.DataFrame):
    """Return a bar chart of final scores per staff."""
    if score_df is None or score_df.empty:
        return px.bar(title=_("No data"))
    fig = px.bar(
        score_df,
        x="staff",
        y="final_score",
        title=_("Combined Score by Staff"),
        labels={"staff": _("Staff"), "final_score": _("Score")},
    )
    fig.update_layout(xaxis_title=_("Staff"), yaxis_title=_("Score"))
    return fig


def department_overview(score_df: pd.DataFrame, long_df: pd.DataFrame):
    """Return a bar chart of average score per role."""
    if (
        score_df is None
        or score_df.empty
        or long_df is None
        or long_df.empty
        or "role" not in long_df.columns
    ):
        return px.bar(title=_("No data"))
    mapping = long_df[["staff", "role"]].drop_duplicates()
    merged = mapping.merge(score_df, on="staff", how="left")
    dept = merged.groupby("role")["final_score"].mean().reset_index()
    fig = px.bar(
        dept,
        x="role",
        y="final_score",
        title=_("Average Score by Role"),
        labels={"role": _("Role"), "final_score": _("Score")},
    )
    fig.update_layout(xaxis_title=_("Role"), yaxis_title=_("Score"))
    return fig


def work_pattern_heatmap(df: pd.DataFrame):
    """Return heatmap of shift-code ratios per staff."""
    if df is None or df.empty or "staff" not in df.columns:
        return px.imshow(pd.DataFrame(), aspect="auto")

    ratio_cols = [c for c in df.columns if c.endswith("_ratio")]
    if not ratio_cols:
        return px.imshow(pd.DataFrame(), aspect="auto")

    heat_df = df.set_index("staff")[ratio_cols].copy()
    heat_df.columns = [c.replace("_ratio", "") for c in heat_df.columns]

    fig = px.imshow(
        heat_df,
        aspect="auto",
        zmin=0,
        zmax=1,
        color_continuous_scale="Blues",
        labels={"x": _("Shift Code"), "y": _("Staff"), "color": _("Ratio")},
    )
    return fig


def shortage_heatmap(lack_ratio_df: pd.DataFrame):
    """Return heatmap visualising shortage ratio for all dates."""
    if lack_ratio_df is None or lack_ratio_df.empty:
        return px.imshow(pd.DataFrame(), aspect="auto")

    fig = px.imshow(
        lack_ratio_df,
        aspect="auto",
        color_continuous_scale="Reds",
        labels={"x": _("Date"), "y": _("Time"), "color": _("Shortage Ratio")},
    )
    return fig


def fatigue_distribution(fatigue_df: pd.DataFrame):
    """Return histogram of fatigue scores."""
    if (
        fatigue_df is None
        or fatigue_df.empty
        or "fatigue_score" not in fatigue_df.columns
    ):
        return px.histogram(pd.DataFrame(), nbins=10)

    fig = px.histogram(
        fatigue_df,
        x="fatigue_score",
        nbins=20,
        labels={"fatigue_score": _("Score")},
        title=_("Fatigue Score Distribution"),
    )
    fig.update_layout(yaxis_title=_("Count"))
    return fig


def fairness_histogram(summary_df: pd.DataFrame, metric: str = "night_ratio"):
    """Return histogram of fairness metric values."""
    if summary_df is None or summary_df.empty or metric not in summary_df.columns:
        return px.histogram(pd.DataFrame(), nbins=10)

    fig = px.histogram(
        summary_df,
        x=metric,
        nbins=20,
        labels={metric: _("Ratio") if metric == "night_ratio" else _(metric)},
        title=_("Night Shift Ratio Distribution") if metric == "night_ratio" else f"{metric} Distribution",
    )
    fig.update_layout(yaxis_title=_("Count"))
    return fig


def _valid_df(df: pd.DataFrame) -> bool:
    """Return True if ``df`` is a non-empty ``pd.DataFrame``."""
    return isinstance(df, pd.DataFrame) and not df.empty


log = logging.getLogger(__name__)


def load_leave_results_from_dir(data_dir: Path) -> dict:
    """Load leave analysis CSV/Excel results from ``data_dir``."""

    results: dict[str, pd.DataFrame] = {}

    fp_daily = data_dir / "leave_analysis.csv"
    if fp_daily.exists():
        try:
            results["daily_summary"] = pd.read_csv(fp_daily, parse_dates=["date"])
        except Exception as e:  # pragma: no cover - I/O errors
            log.warning("leave_analysis.csv load error: %s", e)

    fp_staff_bal = data_dir / "staff_balance_daily.csv"
    if fp_staff_bal.exists():
        try:
            results["staff_balance_daily"] = pd.read_csv(
                fp_staff_bal, parse_dates=["date"]
            )
        except Exception as e:  # pragma: no cover - I/O errors
            log.warning("staff_balance_daily.csv load error: %s", e)

    fp_conc = data_dir / "concentration_requested.csv"
    if fp_conc.exists():
        try:
            results["concentration_requested"] = pd.read_csv(
                fp_conc, parse_dates=["date"]
            )
        except Exception as e:  # pragma: no cover - I/O errors
            log.warning("concentration_requested.csv load error: %s", e)

    fp_ratio = data_dir / "leave_ratio_breakdown.csv"
    if fp_ratio.exists():
        try:
            results["leave_ratio_breakdown"] = pd.read_csv(fp_ratio)
        except Exception as e:  # pragma: no cover - I/O errors
            log.warning("leave_ratio_breakdown.csv load error: %s", e)

    daily_df = results.get("daily_summary")

    if "staff_balance_daily" not in results and _valid_df(daily_df):
        heat_fp = data_dir / "heat_ALL.xlsx"
        if heat_fp.exists():
            try:
                heat = pd.read_excel(heat_fp, index_col=0)
                date_cols = [c for c in heat.columns if c not in SUMMARY5_CONST]
                total_staff = (
                    (heat[date_cols] > 0)
                    .astype(int)
                    .sum()
                    .reset_index()
                    .rename(columns={"index": "date", 0: "total_staff"})
                )
                total_staff["date"] = pd.to_datetime(total_staff["date"])
                req_df = (
                    daily_df[daily_df["leave_type"] == leave_analyzer.LEAVE_TYPE_REQUESTED]
                    .rename(columns={"total_leave_days": "leave_applicants_count"})
                )[["date", "leave_applicants_count"]]
                sb = total_staff.merge(req_df, on="date", how="left")
                sb["leave_applicants_count"] = sb["leave_applicants_count"].fillna(0).astype(int)
                sb["non_leave_staff"] = sb["total_staff"] - sb["leave_applicants_count"]
                sb["leave_ratio"] = sb["leave_applicants_count"] / sb["total_staff"]
                results["staff_balance_daily"] = sb
            except Exception as e:  # pragma: no cover - I/O errors
                log.warning("Failed to reconstruct staff_balance_daily: %s", e)

    if "concentration_requested" not in results and _valid_df(daily_df):
        try:
            conc_df = (
                daily_df[daily_df["leave_type"] == leave_analyzer.LEAVE_TYPE_REQUESTED]
                .rename(columns={"total_leave_days": "leave_applicants_count"})
            )[["date", "leave_applicants_count"]]
            if "staff_balance_daily" in results:
                conc_df = conc_df.merge(
                    results["staff_balance_daily"][["date", "leave_ratio"]],
                    on="date",
                    how="left",
                )
            conc_df["is_concentrated"] = conc_df["leave_applicants_count"] >= 3
            conc_df["staff_names"] = [[] for _ in range(len(conc_df))]
            results["concentration_requested"] = conc_df
        except Exception as e:  # pragma: no cover - I/O errors
            log.warning("Failed to reconstruct concentration_requested: %s", e)

    if "concentration_both" not in results and _valid_df(daily_df):
        try:
            conc_both = leave_analyzer.analyze_both_leave_concentration(
                daily_df.copy(), concentration_threshold=3
            )
            results["concentration_both"] = conc_both
        except Exception as e:  # pragma: no cover - I/O errors
            log.warning("Failed to reconstruct concentration_both: %s", e)

    if "leave_ratio_breakdown" not in results and _valid_df(daily_df):
        try:
            results["leave_ratio_breakdown"] = leave_analyzer.leave_ratio_by_period_and_weekday(
                daily_df
            )
        except Exception as e:  # pragma: no cover - I/O errors
            log.warning("Failed to reconstruct leave_ratio_breakdown: %s", e)

    return results

