from __future__ import annotations

import pandas as pd
import plotly.express as px


def employee_overview(score_df: pd.DataFrame):
    """Return a bar chart of final scores per staff."""
    if score_df is None or score_df.empty:
        return px.bar(title="No data")
    fig = px.bar(score_df, x="staff", y="final_score", title="Combined Score by Staff")
    fig.update_layout(xaxis_title="Staff", yaxis_title="Score")
    return fig


def department_overview(score_df: pd.DataFrame, long_df: pd.DataFrame):
    """Return a bar chart of average score per role."""
    if score_df is None or score_df.empty or long_df is None or long_df.empty or "role" not in long_df.columns:
        return px.bar(title="No data")
    mapping = long_df[["staff", "role"]].drop_duplicates()
    merged = mapping.merge(score_df, on="staff", how="left")
    dept = merged.groupby("role")["final_score"].mean().reset_index()
    fig = px.bar(dept, x="role", y="final_score", title="Average Score by Role")
    fig.update_layout(xaxis_title="Role", yaxis_title="Score")
    return fig
