# shift_suite/tasks/leave_analyzer.py
from __future__ import annotations
import pandas as pd
from typing import Dict, List, Literal, Union  # Union を追加
import logging

logger = logging.getLogger(__name__)
if not logger.handlers:  # ログハンドラが重複しないように設定
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s [%(module)s.%(funcName)s:%(lineno)d] - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)


# --- 定数 ---
LEAVE_TYPE_PAID = "有給"
LEAVE_TYPE_REQUESTED = "希望休"
# DEFAULT_HOLIDAY_TYPE = '通常勤務' # io_excel.py で定義されているものを参照する形でも良い


# --- Helper Functions ---
def _is_full_day_leave(parsed_slots_count_val: Union[int, float]) -> bool:
    """
    parsed_slots_count が0またはそれに近い場合に終日休暇と判定する。
    （io_excel.pyのparsed_slots_countはintのはずだが、念のためfloatも許容）
    """
    return pd.isna(parsed_slots_count_val) or parsed_slots_count_val == 0


# --- Core Analysis Functions ---


def get_daily_leave_counts(
    long_df: pd.DataFrame,
    target_leave_types: List[str] = [LEAVE_TYPE_REQUESTED, LEAVE_TYPE_PAID],
) -> pd.DataFrame:
    """
    日別・職員別・休暇タイプ別の休暇取得「日数」（1日単位）を集計する。
    - 希望休: その日に該当コードがあれば1日としてカウント。
    - 有給休暇: 終日有給(parsed_slots_count=0)の場合に1日としてカウント。
               一部勤務・一部有給(P有など parsed_slots_count > 0)は、
               ここでは有給休暇日数としてはカウントしない。
    """
    if long_df.empty or "ds" not in long_df.columns:
        logger.warning("入力されたlong_dfが空またはds列がありません。")
        return pd.DataFrame(columns=["date", "staff", "leave_type", "leave_day_flag"])

    # 対象の休暇タイプレコードのみ抽出
    # holiday_type列が存在することを確認
    if "holiday_type" not in long_df.columns:
        logger.error(
            "long_dfにholiday_type列が存在しません。休暇分析を実行できません。"
        )
        return pd.DataFrame(columns=["date", "staff", "leave_type", "leave_day_flag"])

    leave_df = long_df[long_df["holiday_type"].isin(target_leave_types)].copy()
    if leave_df.empty:
        logger.info("対象となる休暇タイプレコードが見つかりませんでした。")
        return pd.DataFrame(columns=["date", "staff", "leave_type", "leave_day_flag"])

    leave_df["date"] = leave_df["ds"].dt.normalize()  # 日付部分のみに正規化

    # 休暇日フラグ（その日にそのタイプの休暇を取得したか）を立てる
    processed_records = []
    for _, row in leave_df.iterrows():
        is_target_leave = False
        if row["holiday_type"] == LEAVE_TYPE_REQUESTED:
            # 希望休は parsed_slots_count == 0 であることを前提とする
            if _is_full_day_leave(row["parsed_slots_count"]):
                is_target_leave = True
        elif row["holiday_type"] == LEAVE_TYPE_PAID:
            # 有給は parsed_slots_count == 0 (終日有給) の場合のみカウント
            if _is_full_day_leave(row["parsed_slots_count"]):
                is_target_leave = True

        if is_target_leave:
            processed_records.append(
                {
                    "date": row["date"],
                    "staff": row["staff"],
                    "leave_type": row["holiday_type"],
                    "leave_day_flag": 1,  # 休暇取得日としてフラグを立てる
                }
            )

    if not processed_records:
        return pd.DataFrame(columns=["date", "staff", "leave_type", "leave_day_flag"])

    # 日付と職員と休暇タイプで重複を除去（例：long_dfが時間スロットごとなので、1日の休暇は複数行になるため）
    daily_leave_df = pd.DataFrame(processed_records).drop_duplicates(
        subset=["date", "staff", "leave_type"]
    )

    return daily_leave_df.sort_values(by=["date", "staff", "leave_type"]).reset_index(
        drop=True
    )


def summarize_leave_by_day_count(
    daily_leave_df: pd.DataFrame,  # get_daily_leave_counts の出力
    period: Literal["dayofweek", "month", "month_period", "date"] = "dayofweek",
) -> pd.DataFrame:
    """指定した期間単位で休暇取得日数を集計する。

    Parameters
    ----------
    daily_leave_df:
        :func:`get_daily_leave_counts` の出力データフレーム。
    period:
        集計単位を ``"dayofweek"``、 ``"month"``、 ``"month_period"``、
        ``"date"`` から選ぶ。 ``"date"`` を指定した場合は ``date`` 列が返る。

    Returns
    -------
    pandas.DataFrame
        ``period_unit`` (または ``date``)、 ``leave_type``、 ``total_leave_days``、
        ``num_days_in_period_unit``、 ``avg_leave_days_per_day`` の各列を含む。
    """
    if daily_leave_df.empty or "leave_day_flag" not in daily_leave_df.columns:
        logger.warning(
            "入力されたdaily_leave_dfが空またはleave_day_flag列がありません。"
        )
        return pd.DataFrame()

    df_to_agg = daily_leave_df.copy()
    df_to_agg["date"] = pd.to_datetime(df_to_agg["date"])

    if period == "dayofweek":
        df_to_agg["period_unit"] = df_to_agg["date"].dt.day_name()
        days_of_week = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        # 日本語対応
        day_name_map_jp = {
            "Monday": "月曜日",
            "Tuesday": "火曜日",
            "Wednesday": "水曜日",
            "Thursday": "木曜日",
            "Friday": "金曜日",
            "Saturday": "土曜日",
            "Sunday": "日曜日",
        }
        days_of_week_jp = [day_name_map_jp[d] for d in days_of_week]
        df_to_agg["period_unit"] = pd.Categorical(
            df_to_agg["period_unit"].map(day_name_map_jp),
            categories=days_of_week_jp,
            ordered=True,
        )

    elif period == "month":
        df_to_agg["period_unit"] = df_to_agg["date"].dt.to_period("M").astype(str)
    elif period == "month_period":

        def get_month_period(day_val: int) -> str:
            if day_val <= 10:
                return "月初(1-10日)"
            elif day_val <= 20:
                return "月中(11-20日)"
            else:
                return "月末(21-末日)"

        df_to_agg["period_unit"] = df_to_agg["date"].dt.day.apply(get_month_period)
        month_periods_order = ["月初(1-10日)", "月中(11-20日)", "月末(21-末日)"]
        df_to_agg["period_unit"] = pd.Categorical(
            df_to_agg["period_unit"], categories=month_periods_order, ordered=True
        )
    elif period == "date":  # 日別の集計
        df_to_agg["period_unit"] = df_to_agg["date"]
    else:
        logger.error(f"未対応の集計期間: {period}")
        return pd.DataFrame()

    summary = (
        df_to_agg.groupby(["period_unit", "leave_type"], observed=False)[
            "leave_day_flag"
        ]
        .sum()
        .reset_index(name="total_leave_days")
    )

    # 各 period_unit 内の日付数を数える
    unique_dates = (
        df_to_agg[["period_unit", "date"]]
        .drop_duplicates()
        .groupby("period_unit")
        .size()
        .reset_index(name="num_days_in_period_unit")
    )

    summary = summary.merge(unique_dates, on="period_unit", how="left")
    summary["avg_leave_days_per_day"] = (
        summary["total_leave_days"] / summary["num_days_in_period_unit"]
    )

    if period == "date":  # 日別の場合、日付でソート
        summary = summary.sort_values(by=["period_unit", "leave_type"]).reset_index(
            drop=True
        )
        summary.rename(columns={"period_unit": "date"}, inplace=True)
    else:  # それ以外の期間の場合
        summary = summary.sort_values(by=["period_unit", "leave_type"]).reset_index(
            drop=True
        )

    return summary


def analyze_leave_concentration(
    daily_leave_counts_df: pd.DataFrame,  # summarize_leave_by_day_count(period='date') の出力など、日別・休暇タイプ別の取得総日数
    leave_type_to_analyze: str = LEAVE_TYPE_REQUESTED,
    concentration_threshold: int = 3,
    daily_leave_df: pd.DataFrame
    | None = None,  # get_daily_leave_counts の出力 (スタッフ名取得用)
) -> pd.DataFrame:
    """指定された休暇タイプ（主に希望休）の日ごとの取得者数を評価し、
    閾値を超える日（集中日）を特定する。スタッフ名リストも付与する。"""

    if (
        daily_leave_counts_df.empty
        or "total_leave_days" not in daily_leave_counts_df.columns
    ):
        logger.warning(
            "入力されたdaily_leave_counts_dfが空またはtotal_leave_days列がありません。"
        )
        return pd.DataFrame(
            columns=["date", "leave_applicants_count", "is_concentrated", "staff_names"]
        )

    target_df = daily_leave_counts_df[
        daily_leave_counts_df["leave_type"] == leave_type_to_analyze
    ].copy()
    if target_df.empty:
        logger.info(
            f"{leave_type_to_analyze} のデータが見つかりません。集中度分析をスキップします。"
        )
        return pd.DataFrame(
            columns=["date", "leave_applicants_count", "is_concentrated", "staff_names"]
        )

    concentration_df = target_df.rename(
        columns={"total_leave_days": "leave_applicants_count"}
    )
    concentration_df["is_concentrated"] = (
        concentration_df["leave_applicants_count"] >= concentration_threshold
    )

    # staff_names を取得
    if daily_leave_df is not None and not daily_leave_df.empty:
        if {"date", "staff", "leave_type"}.issubset(daily_leave_df.columns):
            names_df = (
                daily_leave_df[daily_leave_df["leave_type"] == leave_type_to_analyze]
                .groupby("date")["staff"]
                .unique()
                .apply(lambda x: sorted(x))
                .reset_index(name="staff_names")
            )
            concentration_df = concentration_df.merge(names_df, on="date", how="left")
        else:
            concentration_df["staff_names"] = [[] for _ in range(len(concentration_df))]
    else:
        concentration_df["staff_names"] = [[] for _ in range(len(concentration_df))]

    return (
        concentration_df[
            ["date", "leave_applicants_count", "is_concentrated", "staff_names"]
        ]
        .sort_values(by="date")
        .reset_index(drop=True)
    )


def analyze_both_leave_concentration(
    daily_leave_counts_df: pd.DataFrame,
    concentration_threshold: int = 3,
) -> pd.DataFrame:
    """Evaluate days where both requested and paid leave counts exceed the threshold.

    Parameters
    ----------
    daily_leave_counts_df : pd.DataFrame
        Output from :func:`summarize_leave_by_day_count` with ``period='date'``.
    concentration_threshold : int, default 3
        Minimum count for both leave types to mark a day as concentrated.

    Returns
    -------
    pd.DataFrame
        Columns ``date``, ``requested_count``, ``paid_count`` and ``is_concentrated``.
    """

    required_cols = {"date", "leave_type", "total_leave_days"}
    if daily_leave_counts_df.empty or not required_cols.issubset(
        daily_leave_counts_df.columns
    ):
        logger.warning(
            "Invalid daily_leave_counts_df for analyze_both_leave_concentration"
        )
        return pd.DataFrame(
            columns=["date", "requested_count", "paid_count", "is_concentrated"]
        )

    pivot = (
        daily_leave_counts_df.pivot(
            index="date", columns="leave_type", values="total_leave_days"
        )
        .fillna(0)
        .rename(
            columns={
                LEAVE_TYPE_REQUESTED: "requested_count",
                LEAVE_TYPE_PAID: "paid_count",
            }
        )
    )

    for col in ["requested_count", "paid_count"]:
        if col not in pivot.columns:
            pivot[col] = 0

    pivot = pivot.reset_index()
    pivot["is_concentrated"] = (pivot["requested_count"] >= concentration_threshold) & (
        pivot["paid_count"] >= concentration_threshold
    )

    return (
        pivot[["date", "requested_count", "paid_count", "is_concentrated"]]
        .sort_values("date")
        .reset_index(drop=True)
    )


def staff_concentration_share(concentration_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate share of staff appearing on concentrated leave days."""
    if concentration_df.empty or not {"is_concentrated", "staff_names"}.issubset(
        concentration_df.columns
    ):
        return pd.DataFrame(columns=["staff", "concentrated_day_count", "share"])

    focused = concentration_df[concentration_df["is_concentrated"]]
    if focused.empty:
        return pd.DataFrame(columns=["staff", "concentrated_day_count", "share"])

    total_days = len(focused)
    counts: Dict[str, int] = {}
    for names in focused["staff_names"]:
        for name in names:
            counts[name] = counts.get(name, 0) + 1

    result = (
        pd.DataFrame(
            [(k, v, v / total_days) for k, v in counts.items()],
            columns=["staff", "concentrated_day_count", "share"],
        )
        .sort_values("share", ascending=False)
        .reset_index(drop=True)
    )
    return result


def get_staff_leave_list(
    long_df: pd.DataFrame,
    target_leave_types: List[str] = [LEAVE_TYPE_REQUESTED, LEAVE_TYPE_PAID],
) -> pd.DataFrame:
    """
    職員ごと・休暇タイプごとの休暇取得日リスト（終日休暇のみ）を作成する。
    """
    if long_df.empty or "ds" not in long_df.columns:
        return pd.DataFrame(columns=["staff", "role", "leave_type", "leave_date"])

    if "holiday_type" not in long_df.columns:
        return pd.DataFrame(columns=["staff", "role", "leave_type", "leave_date"])

    leave_df = long_df[
        long_df["holiday_type"].isin(target_leave_types)
        & (
            long_df.apply(
                lambda row: _is_full_day_leave(row["parsed_slots_count"]), axis=1
            )
        )
    ].copy()

    if leave_df.empty:
        return pd.DataFrame(columns=["staff", "role", "leave_type", "leave_date"])

    leave_df["leave_date"] = leave_df["ds"].dt.date

    # staff, role, holiday_type, leave_date でユニークなリストを作成
    staff_leave_list_df = (
        leave_df[["staff", "role", "holiday_type", "leave_date"]]
        .drop_duplicates()
        .sort_values(by=["staff", "role", "holiday_type", "leave_date"])
        .reset_index(drop=True)
    )

    return staff_leave_list_df


def leave_ratio_by_period_and_weekday(daily_summary_df: pd.DataFrame) -> pd.DataFrame:
    """Return leave ratios by month period and weekday for each leave type."""
    required_cols = {"date", "leave_type", "total_leave_days"}
    if daily_summary_df.empty or not required_cols.issubset(daily_summary_df.columns):
        return pd.DataFrame(
            columns=["month_period", "dayofweek", "leave_type", "leave_ratio"]
        )

    df = daily_summary_df.copy()
    df["date"] = pd.to_datetime(df["date"])

    def get_month_period(day_val: int) -> str:
        if day_val <= 10:
            return "月初(1-10日)"
        if day_val <= 20:
            return "月中(11-20日)"
        return "月末(21-末日)"

    df["month_period"] = df["date"].dt.day.apply(get_month_period)
    month_order = ["月初(1-10日)", "月中(11-20日)", "月末(21-末日)"]
    df["month_period"] = pd.Categorical(
        df["month_period"], categories=month_order, ordered=True
    )

    day_name_map = {
        "Monday": "月曜日",
        "Tuesday": "火曜日",
        "Wednesday": "水曜日",
        "Thursday": "木曜日",
        "Friday": "金曜日",
        "Saturday": "土曜日",
        "Sunday": "日曜日",
    }
    dow_order = [
        day_name_map[d]
        for d in [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
    ]
    df["dayofweek"] = pd.Categorical(
        df["date"].dt.day_name().map(day_name_map), categories=dow_order, ordered=True
    )

    grouped = (
        df.groupby(["month_period", "dayofweek", "leave_type"], observed=False)[
            "total_leave_days"
        ]
        .sum()
        .reset_index()
    )
    total_per_type = grouped.groupby("leave_type")["total_leave_days"].transform("sum")
    grouped["leave_ratio"] = (grouped["total_leave_days"] / total_per_type).fillna(0)
    return grouped.sort_values(["month_period", "dayofweek", "leave_type"]).reset_index(
        drop=True
    )


# --- CLI実行のためのダミーコード (app.pyから呼び出す際は不要) ---
if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    # ダミーデータ作成
    sample_data = {
        "ds": pd.to_datetime(
            [
                "2023-01-01 00:00",
                "2023-01-01 00:30",  # 山田 希望休
                "2023-01-01 00:00",
                "2023-01-01 00:30",  # 田中 有給
                "2023-01-02 09:00",
                "2023-01-02 09:30",  # 山田 P有 (午前勤務)
                "2023-01-02 00:00",  # 鈴木 希望休
                "2023-01-03 00:00",  # 田中 希望休
                "2023-01-08 00:00",  # 山田 希望休 (週明け月曜)
            ]
        ),
        "staff": [
            "山田太郎",
            "山田太郎",
            "田中花子",
            "田中花子",
            "山田太郎",
            "山田太郎",
            "鈴木一郎",
            "田中花子",
            "山田太郎",
        ],
        "role": ["A", "A", "B", "B", "A", "A", "A", "B", "A"],  # 配列長を合わせる
        "code": [
            "希",
            "希",
            "有",
            "有",
            "P有",
            "P有",
            "希",
            "希",
            "希",
        ],
        "holiday_type": [
            LEAVE_TYPE_REQUESTED,
            LEAVE_TYPE_REQUESTED,
            LEAVE_TYPE_PAID,
            LEAVE_TYPE_PAID,
            LEAVE_TYPE_PAID,
            LEAVE_TYPE_PAID,  # P有はholiday_type='有給'
            LEAVE_TYPE_REQUESTED,
            LEAVE_TYPE_REQUESTED,
            LEAVE_TYPE_REQUESTED,
        ],
        "parsed_slots_count": [
            0,
            0,
            0,
            0,
            2,
            2,  # P有は午前勤務2スロット(1時間)とする例
            0,
            0,
            0,
        ],
    }
    # staffとroleの配列長をdsに合わせる
    num_records = len(sample_data["ds"])
    sample_data["role"] = (
        sample_data["role"] * (num_records // len(sample_data["role"]) + 1)
    )[:num_records]

    sample_long_df = pd.DataFrame(sample_data)

    logger.info("--- get_daily_leave_counts ---")
    daily_counts = get_daily_leave_counts(sample_long_df)
    logger.info(daily_counts)
    # 期待される出力例 (P有は有給日数にはカウントされない):
    #          date   staff leave_type  leave_day_flag
    # 0  2023-01-01  田中花子         有給               1
    # 1  2023-01-01  山田太郎       希望休               1
    # 2  2023-01-02  鈴木一郎       希望休               1
    # 3  2023-01-03  田中花子       希望休               1
    # 4  2023-01-08  山田太郎       希望休               1

    logger.info("\n--- summarize_leave_by_day_count (dayofweek for 希望休) ---")
    requested_leave_daily = daily_counts[
        daily_counts["leave_type"] == LEAVE_TYPE_REQUESTED
    ]
    summary_dow_req = summarize_leave_by_day_count(
        requested_leave_daily, period="dayofweek"
    )
    logger.info(summary_dow_req)
    # 期待される出力例 (日本語曜日):
    #   period_unit leave_type  total_leave_days  num_days_in_period_unit  avg_leave_days_per_day
    # 0        月曜日       希望休                   2                        2                     1.0
    # 1        火曜日       希望休                   1                        1                     1.0
    # 2        日曜日       希望休                   1                        1                     1.0

    logger.info("\n--- summarize_leave_by_day_count (month_period for 有給) ---")
    paid_leave_daily = daily_counts[daily_counts["leave_type"] == LEAVE_TYPE_PAID]
    summary_month_period_paid = summarize_leave_by_day_count(
        paid_leave_daily, period="month_period"
    )
    logger.info(summary_month_period_paid)
    # 期待される出力例:
    #     period_unit leave_type  total_leave_days  num_days_in_period_unit  avg_leave_days_per_day
    # 0  月初(1-10日)         有給                   1                        1                     1.0

    logger.info("\n--- analyze_leave_concentration (希望休, threshold=2) ---")
    daily_requested_summary = summarize_leave_by_day_count(
        requested_leave_daily, period="date"
    )
    concentration = analyze_leave_concentration(
        daily_requested_summary, concentration_threshold=2
    )
    logger.info(concentration)
    # 期待される出力例 (2023-01-01 が集中日になるはずだが、get_daily_leave_countsの仕様変更でstaffでnuniqueするので、
    # このサンプルでは集中日は出ない。もし日別の総件数なら出る)
    # → get_daily_leave_counts は staff ごとのフラグなので、analyze_leave_concentration に渡す前に
    #    日付ごとに staff 数を再集計する必要がある。
    #    修正：summarize_leave_by_day_count(period='date') の出力をそのまま使えるように、
    #    analyze_leave_concentration は日別・タイプ別の合計日数（＝該当者数）を期待する。

    # analyze_leave_concentration のための日別取得者数データを作成
    daily_applicants_requested = (
        requested_leave_daily.groupby(["date", "leave_type"])["staff"]
        .nunique()
        .reset_index(name="total_leave_days")
    )
    logger.info(
        "\n--- analyze_leave_concentration (希望休, threshold=1) using re-aggregated data ---"
    )
    concentration_adj = analyze_leave_concentration(
        daily_applicants_requested, concentration_threshold=1
    )
    logger.info(concentration_adj[concentration_adj["is_concentrated"]])
    #          date  leave_applicants_count  is_concentrated
    # 0 2023-01-01                       1             True # 山田
    # 1 2023-01-02                       1             True # 鈴木
    # 2 2023-01-03                       1             True # 田中
    # 3 2023-01-08                       1             True # 山田

    logger.info("\n--- get_staff_leave_list (山田太郎) ---")
    staff_leaves = get_staff_leave_list(
        sample_long_df, target_leave_types=[LEAVE_TYPE_REQUESTED, LEAVE_TYPE_PAID]
    )
    logger.info(staff_leaves[staff_leaves["staff"] == "山田太郎"])
    # 期待される出力例 (P有の有給部分は終日ではないためリストされない):
    #          staff role leave_type  leave_date
    # 1  山田太郎    A       希望休  2023-01-01
    # 2  山田太郎    A       希望休  2023-01-08
