from __future__ import annotations

import pandas as pd
import plotly.express as px

JP = {
    "Staff": "スタッフ",
    "Score": "スコア",
    "Role": "職種",
    "Month": "月",
    "Shortage Hours": "不足時間(h)",
    "Total Leave Days": "総休暇日数",
    "Shift Code": "勤務区分",
    "Ratio": "比率",
}


def _(text: str) -> str:
    return JP.get(text, text)


def employee_overview(score_df: pd.DataFrame):
    """Return a bar chart of final scores per staff."""
    if score_df is None or score_df.empty:
        return px.bar(title="No data")
    fig = px.bar(
        score_df,
        x="staff",
        y="final_score",
        title="Combined Score by Staff",
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
        return px.bar(title="No data")
    mapping = long_df[["staff", "role"]].drop_duplicates()
    merged = mapping.merge(score_df, on="staff", how="left")
    dept = merged.groupby("role")["final_score"].mean().reset_index()
    fig = px.bar(
        dept,
        x="role",
        y="final_score",
        title="Average Score by Role",
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
        title="Fatigue Score Distribution",
    )
    fig.update_layout(yaxis_title="Count")
    return fig


def fairness_histogram(summary_df: pd.DataFrame):
    """Return histogram of night shift ratios."""
    if (
        summary_df is None
        or summary_df.empty
        or "night_ratio" not in summary_df.columns
    ):
        return px.histogram(pd.DataFrame(), nbins=10)

    fig = px.histogram(
        summary_df,
        x="night_ratio",
        nbins=20,
        labels={"night_ratio": _("Ratio")},
        title="Night Shift Ratio Distribution",
    )
    fig.update_layout(yaxis_title="Count")
    return fig
