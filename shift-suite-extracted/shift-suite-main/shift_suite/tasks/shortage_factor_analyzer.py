"""Shortage factor analysis utilities."""

from __future__ import annotations

import datetime as dt
from typing import Set, Tuple

import pandas as pd
from pandas import DataFrame
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split

from .leave_analyzer import LEAVE_TYPE_PAID, LEAVE_TYPE_REQUESTED
from .utils import _parse_as_date


def _time_slot_category(hhmm: str) -> str:
    try:
        h = int(hhmm.split(":")[0])
    except Exception:
        return "unknown"
    if 0 <= h < 7:
        return "early_morning"
    if 7 <= h < 12:
        return "morning"
    if 12 <= h < 18:
        return "afternoon"
    return "evening"


class ShortageFactorAnalyzer:
    """Generate features from shift data and train a simple model."""

    def generate_features(
        self,
        long_df: DataFrame,
        heat_all_df: DataFrame,
        shortage_time_df: DataFrame,
        leave_analysis_df: DataFrame,
        holidays_set: Set[dt.date],
    ) -> DataFrame:
        """Return feature DataFrame indexed by (date, time_slot)."""
        shortage_long = (
            shortage_time_df.reset_index()
            .melt(
                id_vars=shortage_time_df.index.name or "time_slot",
                var_name="date",
                value_name="shortage_count",
            )
            .rename(columns={shortage_time_df.index.name or "time_slot": "time_slot"})
        )
        shortage_long["date"] = pd.to_datetime(shortage_long["date"]).dt.date

        heat_date_cols = [
            c
            for c in heat_all_df.columns
            if c not in ("need", "upper", "staff", "lack", "excess")
            and _parse_as_date(str(c)) is not None
        ]
        heat_long = (
            heat_all_df[heat_date_cols]
            .reset_index()
            .melt(
                id_vars=heat_all_df.index.name or "time_slot",
                var_name="date",
                value_name="total_staff_actual",
            )
            .rename(columns={heat_all_df.index.name or "time_slot": "time_slot"})
        )
        heat_long["date"] = pd.to_datetime(heat_long["date"]).dt.date

        df = shortage_long.merge(heat_long, on=["date", "time_slot"], how="left")

        if not long_df.empty and {
            "ds",
            "role",
            "holiday_type",
            "parsed_slots_count",
        }.issubset(long_df.columns):
            tmp = long_df.copy()
            tmp["date"] = tmp["ds"].dt.date
            tmp["time_slot"] = tmp["ds"].dt.strftime("%H:%M")
            staff_role = (
                tmp.groupby(["date", "time_slot", "role"])["staff"]
                .nunique()
                .unstack("role")
            )
            staff_role.columns = [f"role_{c}_staff_actual" for c in staff_role.columns]
            df = df.merge(staff_role, on=["date", "time_slot"], how="left")

            leave_df = tmp[
                (tmp["holiday_type"].isin([LEAVE_TYPE_REQUESTED, LEAVE_TYPE_PAID]))
                & (tmp["parsed_slots_count"] == 0)
            ]
            leave_total = (
                leave_df.groupby("date")["staff"]
                .nunique()
                .rename("total_leave_applicants_today")
            )
            leave_role = (
                leave_df.groupby(["date", "role"])["staff"].nunique().unstack("role")
            )
            leave_role.columns = [
                f"role_{c}_leave_applicants_today" for c in leave_role.columns
            ]
            df = df.merge(leave_total, on="date", how="left")
            df = df.merge(leave_role, on="date", how="left")
        else:
            df["total_leave_applicants_today"] = (
                leave_analysis_df.set_index("date")
                .reindex(df["date"])
                .fillna(0)["total_leave_days"]
                .values
                if not leave_analysis_df.empty
                else 0
            )

        df["day_of_week"] = pd.to_datetime(df["date"]).dt.dayofweek
        df["is_holiday"] = df["date"].isin(holidays_set).astype(int)
        df["time_slot_category"] = df["time_slot"].apply(_time_slot_category)

        df = df.sort_values(["time_slot", "date"]).reset_index(drop=True)
        df["shortage_count_prev_day_same_slot"] = (
            df.groupby("time_slot")["shortage_count"].shift(1).fillna(0)
        )
        df["shortage_count_avg_last_7days_same_slot"] = (
            df.groupby("time_slot")["shortage_count"]
            .rolling(window=7, min_periods=1)
            .mean()
            .shift(1)
            .reset_index(level=0, drop=True)
            .fillna(0)
        )
        df["is_shortage"] = (df["shortage_count"] > 0).astype(int)

        df.set_index(["date", "time_slot"], inplace=True)
        df.fillna(0, inplace=True)
        return df

    def train_and_get_feature_importance(
        self,
        feature_df: DataFrame,
        target_column_name: str = "is_shortage",
    ) -> Tuple[object, DataFrame]:
        """Train model and return feature importance."""
        X = feature_df.drop(columns=[target_column_name])
        y = feature_df[target_column_name]
        X_train, X_test, y_train, _ = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
        if y.nunique() <= 2 and sorted(y.unique()) in ([0, 1], [0], [1]):
            model = RandomForestClassifier(random_state=0)
        else:
            model = RandomForestRegressor(random_state=0)
        model.fit(X_train, y_train)
        importances = model.feature_importances_
        fi_df = (
            pd.DataFrame({"feature": X.columns, "importance": importances})
            .sort_values("importance", ascending=False)
            .reset_index(drop=True)
        )
        return model, fi_df
