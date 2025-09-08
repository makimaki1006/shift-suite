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

    # カラム名の正規化：英語→日本語に統一
    column_mapping = {
        'role': '職種',
        'employment': '雇用形態',
        'employment_type': '雇用形態'
    }
    
    # 存在するカラムのみをリネーム
    rename_dict = {}
    for eng_col, jp_col in column_mapping.items():
        if eng_col in df.columns:
            rename_dict[eng_col] = jp_col
    
    if rename_dict:
        df = df.rename(columns=rename_dict)
    
    # 必須カラムが存在するかチェック
    required_columns = ['職種', '雇用形態']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        # 欠損カラムをデフォルト値で補完
        for col in missing_columns:
            if col == '職種':
                df['職種'] = 'unknown_role'
            elif col == '雇用形態':
                df['雇用形態'] = 'unknown_employment'

    # 時間単位で丸め、時間帯情報を追加
    df['time_group'] = df['timestamp'].dt.floor(freq)
    df['time_of_day'] = df['time_group'].dt.time

    # 日付ごとに時間帯・職種・雇用形態別の実績人数を算出
    daily_counts = df.groupby(
        [df['time_group'].dt.date.rename('date'), 'time_of_day', '職種', '雇用形態']
    ).size().reset_index(name='actual_count')

    # 時間帯ごとに歴史的なNeed値を計算
    needs_by_time = daily_counts.groupby(['time_of_day', '職種', '雇用形態'])['actual_count'].agg(
        need_mean='mean',
        need_median='median',
        need_p25=lambda x: x.quantile(0.25)
    ).reset_index()

    # 全てのタイムスロットにNeed値を紐付け
    all_slots = df[['time_group', 'time_of_day', '職種', '雇用形態']].drop_duplicates()
    needs_df = pd.merge(
        all_slots,
        needs_by_time,
        on=['time_of_day', '職種', '雇用形態'],
        how='left'
    ).drop(columns=['time_of_day'])

    # Need列の欠損を0で補完
    needs_df[['need_mean', 'need_median', 'need_p25']] = needs_df[
        ['need_mean', 'need_median', 'need_p25']
    ].fillna(0)

    return needs_df
