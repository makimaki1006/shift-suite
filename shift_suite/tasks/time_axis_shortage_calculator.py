import pandas as pd


def calculate_time_axis_shortage(
    actual_df: pd.DataFrame,
    needs_df: pd.DataFrame,
    time_unit_minutes: int
) -> pd.DataFrame:
    """
    実績データと統計的Need値を突き合わせて、
    各時間帯・職種・雇用形態ごとの過不足を計算する。

    Args:
        actual_df (pd.DataFrame): 個々の勤務記録を含む実績データ。
        needs_df (pd.DataFrame): ``calculate_all_statistical_needs`` の結果。
        time_unit_minutes (int): 解析に用いる時間単位（分）。

    Returns:
        pd.DataFrame: need値と過不足列を含むデータフレーム。
    """
    freq = f"{time_unit_minutes}min"

    work_df = actual_df.copy()
    work_df['time_group'] = work_df['timestamp'].dt.floor(freq)

    actual_counts = (
        work_df.groupby(['time_group', '職種', '雇用形態'])
        .size()
        .reset_index(name='actual_count')
    )

    merged = needs_df.merge(
        actual_counts,
        on=['time_group', '職種', '雇用形態'],
        how='left'
    ).fillna({'actual_count': 0})

    merged['shortage_mean'] = merged['actual_count'] - merged['need_mean']
    merged['shortage_median'] = merged['actual_count'] - merged['need_median']
    merged['shortage_p25'] = merged['actual_count'] - merged['need_p25']

    return merged
