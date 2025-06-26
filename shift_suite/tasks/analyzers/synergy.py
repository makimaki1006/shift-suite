from __future__ import annotations

import pandas as pd


def analyze_synergy(long_df: pd.DataFrame, shortage_df: pd.DataFrame, target_staff: str) -> pd.DataFrame:
    """Analyze synergy between the target staff and colleagues.

    Parameters
    ----------
    long_df : pd.DataFrame
        Long format working record for all staff.
    shortage_df : pd.DataFrame
        DataFrame of shortage counts per day/time slot.
    target_staff : str
        Staff identifier to analyze.

    Returns
    -------
    pd.DataFrame
        DataFrame containing synergy score per coworker.
    """

    if long_df.empty or shortage_df.empty or not target_staff:
        return pd.DataFrame()

    shortage_long = (
        shortage_df.melt(var_name="date_str", value_name="shortage_count", ignore_index=False)
        .reset_index()
        .rename(columns={"index": "time"})
    )
    shortage_long["ds"] = pd.to_datetime(shortage_long["date_str"] + " " + shortage_long["time"])
    total_shortage_per_slot = shortage_long.groupby("ds")["shortage_count"].sum()

    overall_avg_shortage = total_shortage_per_slot.mean()

    my_work_slots = long_df[long_df["staff"] == target_staff]["ds"].unique()

    synergy_scores = []
    coworkers = long_df[long_df["staff"] != target_staff]["staff"].unique()

    for coworker in coworkers:
        coworker_work_slots = long_df[long_df["staff"] == coworker]["ds"].unique()
        together_slots = pd.Series(list(set(my_work_slots) & set(coworker_work_slots)))
        if len(together_slots) < 5:
            continue
        pair_avg_shortage = total_shortage_per_slot.reindex(together_slots).mean()
        synergy_score = overall_avg_shortage - pair_avg_shortage
        synergy_scores.append(
            {
                "相手の職員": coworker,
                "シナジースコア": synergy_score,
                "共働スロット数": len(together_slots),
            }
        )

    if not synergy_scores:
        return pd.DataFrame()

    result_df = pd.DataFrame(synergy_scores).sort_values("シナジースコア", ascending=False).reset_index(drop=True)
    return result_df
