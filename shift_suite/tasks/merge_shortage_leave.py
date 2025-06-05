"""Utilities to merge shortage data with leave analysis."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def merge_shortage_leave(
    out_dir: Path | str,
    shortage_excel: str | Path = "shortage_time.xlsx",
    leave_csv: str | Path = "leave_analysis.csv",
    out_csv: str | Path = "shortage_leave.csv",
    *,
    log_csv: str | Path = "over_shortage_log.csv",
) -> Path:
    """Merge ``shortage_time.xlsx`` with ``leave_analysis.csv``.

    Parameters
    ----------
    out_dir:
        Directory containing the input files.
    shortage_excel:
        File name of ``shortage_time.xlsx``.
    leave_csv:
        File name of ``leave_analysis.csv``.
    out_csv:
        Output CSV file name.

    Returns
    -------
    Path
        Path to the merged CSV.
    """
    out_dir_path = Path(out_dir)
    shortage_fp = out_dir_path / shortage_excel
    leave_fp = out_dir_path / leave_csv

    if not shortage_fp.exists():
        raise FileNotFoundError(shortage_fp)
    if not leave_fp.exists():
        raise FileNotFoundError(leave_fp)

    lack_df = pd.read_excel(shortage_fp, index_col=0)
    lack_long = (
        lack_df.reset_index()
        .melt(id_vars=lack_df.index.name, var_name="date", value_name="lack")
        .rename(columns={lack_df.index.name: "time"})
    )
    lack_long["date"] = pd.to_datetime(lack_long["date"]).dt.date

    leave_df = pd.read_csv(leave_fp, parse_dates=["date"])
    leave_sum = (
        leave_df.groupby("date")["total_leave_days"]
        .sum()
        .reset_index()
        .rename(columns={"total_leave_days": "leave_applicants"})
    )

    merged = lack_long.merge(leave_sum, on="date", how="left")
    merged["leave_applicants"] = merged["leave_applicants"].fillna(0)
    merged["net_shortage"] = (merged["lack"] - merged["leave_applicants"]).clip(lower=0)

    log_fp = out_dir_path / log_csv
    if log_fp.exists():
        log_df = pd.read_csv(log_fp)
        log_df = log_df[log_df.get("type") == "shortage"].copy()
        if not log_df.empty:
            log_df["date"] = pd.to_datetime(log_df["date"]).dt.date
            other = (
                log_df[log_df.get("reason") != "Planned leave"]
                .groupby(["date", "time"])["count"]
                .sum()
                .reset_index(name="other_reason_lack")
            )
            merged = merged.merge(other, on=["date", "time"], how="left")
            merged["other_reason_lack"] = merged["other_reason_lack"].fillna(0)

    out_fp = out_dir_path / out_csv
    merged.to_csv(out_fp, index=False)
    return out_fp
