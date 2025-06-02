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
