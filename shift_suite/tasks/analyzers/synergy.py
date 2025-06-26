from __future__ import annotations
import pandas as pd

def analyze_synergy(long_df: pd.DataFrame, shortage_df: pd.DataFrame, target_staff: str) -> pd.DataFrame:
    """
    指定された職員（target_staff）と他の職員とのシナジーを分析する。

    Args:
        long_df: 全員の勤務実績データ。
        shortage_df: 日付・時間帯ごとの不足人数データ。
        target_staff: 分析対象の職員名。

    Returns:
        シナジースコアを含むDataFrame。
    """
    if long_df.empty or shortage_df.empty or not target_staff:
        return pd.DataFrame()

    # 1. 日付・時間帯ごとの総不足人数を計算
    shortage_long = shortage_df.melt(var_name='date_str', value_name='shortage_count', ignore_index=False).reset_index().rename(columns={'index':'time'})
    if 'date_str' not in shortage_long.columns or 'time' not in shortage_long.columns:
        return pd.DataFrame()
    shortage_long['ds'] = pd.to_datetime(shortage_long['date_str'] + ' ' + shortage_long['time'], errors='coerce')
    shortage_long.dropna(subset=['ds'], inplace=True)
    total_shortage_per_slot = shortage_long.groupby('ds')['shortage_count'].sum()

    if total_shortage_per_slot.empty:
        return pd.DataFrame()

    # 2. 全体の平均不足人数を計算（比較基準）
    overall_avg_shortage = total_shortage_per_slot.mean()

    # 3. 対象職員が勤務した日時を特定
    my_work_slots = long_df[long_df['staff'] == target_staff]['ds'].unique()

    # 4. 各同僚とのシナジーを計算
    synergy_scores = []
    coworkers = long_df[long_df['staff'] != target_staff]['staff'].unique()

    for coworker in coworkers:
        # その同僚が勤務した日時
        coworker_work_slots = long_df[long_df['staff'] == coworker]['ds'].unique()
        
        # 2人が一緒に勤務した日時
        together_slots = pd.Series(list(set(my_work_slots) & set(coworker_work_slots)))
        
        if len(together_slots) < 5: # 統計的に意味のある回数（例:5スロット以上）だけを対象
            continue

        # 一緒に働いた日の平均不足人数
        pair_avg_shortage = total_shortage_per_slot.reindex(together_slots).mean()
        
        if pd.isna(pair_avg_shortage):
            continue

        # シナジースコア = (全体の平均不足 - ペアの平均不足)
        synergy_score = overall_avg_shortage - pair_avg_shortage
        
        synergy_scores.append({
            "相手の職員": coworker,
            "シナジースコア": synergy_score,
            "共働スロット数": len(together_slots)
        })

    if not synergy_scores:
        return pd.DataFrame()

    result_df = pd.DataFrame(synergy_scores).sort_values("シナジースコア", ascending=False).reset_index(drop=True)
    return result_df
