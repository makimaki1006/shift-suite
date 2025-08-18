import pandas as pd


def calculate_all_statistical_needs(
    actual_df: pd.DataFrame,
    time_unit_minutes: int
) -> pd.DataFrame:
    """
    過去のシフト実績データから、時間単位、職種、雇用形態のグループごとに
    3つの統計的Need値（平均、中央値、25パーセンタイル）を一度に算出する。

    Args:
        actual_df (pd.DataFrame): タイムスタンプと職員情報を持つ実績データ。
        time_unit_minutes (int): app.pyで指定された分析の時間単位（分）。

    Returns:
        pd.DataFrame: 各グループの3つの統計的Need値を含むデータフレーム。
    """
    df = actual_df.copy()
    freq = f"{time_unit_minutes}min"

    # 時間単位で丸め、集計用のキーを作成
    df['time_group'] = df['timestamp'].dt.floor(freq)

    # 時間、職種、雇用形態ごとに勤務人数を集計
    grouped_counts = df.groupby(
        ['time_group', '職種', '雇用形態']
    ).size().reset_index(name='actual_count')

    # 各グループにおける人数の統計分布から、3つのNeed値を一括で計算
    needs_df = grouped_counts.groupby(['職種', '雇用形態', 'time_group'])['actual_count'].agg(
        need_mean='mean',
        need_median='median',
        need_p25=lambda x: x.quantile(0.25)
    ).reset_index()

    return needs_df
