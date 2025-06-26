from __future__ import annotations
import pandas as pd


def create_blueprint(
    long_df: pd.DataFrame,
    fairness_df: pd.DataFrame,
    fatigue_df: pd.DataFrame,
    shortage_df: pd.DataFrame,
) -> dict:
    """質の高いシフトに共通する作成パターンを分析しブループリントを生成。"""
    if long_df.empty or fairness_df.empty or fatigue_df.empty or shortage_df.empty:
        return {"error": "必要な分析データが不足しています。"}

    # --- ステップ1: 「良いシフト（お手本シフト）」を定義する ---
    daily_scores = pd.DataFrame(index=pd.to_datetime(shortage_df.columns))
    daily_scores["shortage"] = shortage_df.sum().values

    long_df["date"] = pd.to_datetime(long_df["ds"].dt.date)
    fairness_df = fairness_df.set_index("staff")

    # `fatigue_df` may already use staff names as the index depending on how it
    # was saved. Only set the index when a `staff` column exists to avoid a
    # KeyError.
    if "staff" in fatigue_df.columns:
        fatigue_df = fatigue_df.set_index("staff")

    daily_avg_fairness = (
        long_df.groupby("date")["staff"]
        .apply(lambda x: fairness_df.reindex(x.unique())["unfairness_score"].mean())
        .rename("avg_fairness")
    )
    daily_avg_fatigue = (
        long_df.groupby("date")["staff"]
        .apply(lambda x: fatigue_df.reindex(x.unique())["fatigue_score"].mean())
        .rename("avg_fatigue")
    )

    daily_scores = daily_scores.join(daily_avg_fairness).join(daily_avg_fatigue).fillna(0)
    daily_scores["rank_shortage"] = daily_scores["shortage"].rank(pct=True)
    daily_scores["rank_fairness"] = daily_scores["avg_fairness"].rank(pct=True)
    daily_scores["rank_fatigue"] = daily_scores["avg_fatigue"].rank(pct=True)
    daily_scores["total_rank"] = daily_scores[["rank_shortage", "rank_fairness", "rank_fatigue"]].mean(axis=1)
    good_shift_dates = daily_scores[daily_scores["total_rank"] <= 0.2].index

    if good_shift_dates.empty:
        return {"error": "分析に適した「お手本シフト」が見つかりませんでした。"}

    # --- ステップ2: シフトピースの「制約の強さ」を定量化 ---
    long_df["is_night"] = long_df["code"].astype(str).str.contains("夜", na=False)
    long_df["is_part_time"] = long_df.get("employment", "").astype(str).str.contains("パート", na=False)

    def get_constraint_score(row):
        if row["is_night"]:
            return 3
        if row["is_part_time"]:
            return 2
        return 1

    long_df["constraint"] = long_df.apply(get_constraint_score, axis=1)

    # --- ステップ3: シーケンス・マイニングで「思考の連鎖」を発見 ---
    good_shifts_df = long_df[long_df["date"].isin(good_shift_dates)]
    first_move_counts = (
        good_shifts_df.sort_values(["date", "constraint"], ascending=[True, False])
        .drop_duplicates("date")["code"].value_counts()
    )

    first_move_code = first_move_counts.index[0]
    dates_with_first_move = good_shifts_df[good_shifts_df["code"] == first_move_code]["date"].unique()
    second_move_candidates = good_shifts_df[
        good_shifts_df["date"].isin(dates_with_first_move) & (good_shifts_df["code"] != first_move_code)
    ]
    second_move_counts = second_move_candidates["code"].value_counts()

    blueprint = {
        "お手本シフトの日数": len(good_shift_dates),
        "推奨される初手": first_move_code,
        f"「{first_move_code}」の後の推奨される次の一手": second_move_counts.head(3).to_dict() if not second_move_counts.empty else "特になし",
        "解説": f"質の高いシフトの多くは、まず「{first_move_code}」勤務を確定させてから、他のシフトを組む傾向にあります。",
    }

    return blueprint
