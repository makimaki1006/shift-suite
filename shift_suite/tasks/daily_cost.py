from __future__ import annotations

from typing import Mapping, Literal

import pandas as pd

from .constants import DEFAULT_SLOT_MINUTES, SLOT_HOURS

SLOT_MINUTES = DEFAULT_SLOT_MINUTES  # Backward compatibility


def calculate_daily_cost(
    long_df: pd.DataFrame,
    wages: Mapping[str, float],
    *,
    by: Literal["staff", "role", "employment"],
    slot_minutes: int = SLOT_MINUTES,
) -> pd.DataFrame:
    """Calculate daily labour cost from long format shift data.

    Parameters
    ----------
    long_df : DataFrame
        Shift records returned by :func:`ingest_excel`.
    wages : Mapping[str, float]
        Hourly wage keyed by the value of ``by`` column.
    by : {'staff', 'role', 'employment'}
        Column used to look up hourly wage.
    slot_minutes : int, default 30
        Minutes per timeslot represented by each row.

    Returns
    -------
    DataFrame
        ``date`` and ``cost`` columns with daily totals.
    """
    if by not in {"staff", "role", "employment"}:
        raise ValueError("by must be 'staff', 'role' or 'employment'")
    if "ds" not in long_df.columns:
        raise ValueError("long_df must contain 'ds' column")
    if by not in long_df.columns:
        raise ValueError(f"long_df must contain '{by}' column")

    df = long_df.copy()
    df["date"] = pd.to_datetime(df["ds"]).dt.date
    if "parsed_slots_count" in df.columns:
        df = df[df["parsed_slots_count"] > 0]

    hours_per_slot = SLOT_HOURS
    df["wage"] = df[by].map(wages).fillna(0)
    df["cost"] = df["wage"] * hours_per_slot

    result = df.groupby("date")["cost"].sum().reset_index()
    return result
