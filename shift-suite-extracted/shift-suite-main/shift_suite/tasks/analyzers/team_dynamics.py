from __future__ import annotations
import pandas as pd


def analyze_team_dynamics(
    long_df: pd.DataFrame,
    fatigue_df: pd.DataFrame,
    fairness_df: pd.DataFrame,
    team_criteria: dict,
) -> pd.DataFrame:
    """指定された基準で動的なチームを定義し、その健全性指標を時系列で分析する。"""

    if long_df.empty or team_criteria is None:
        return pd.DataFrame()

    # 1. 基準に基づいてチームメンバーを特定
    team_members_df = long_df.copy()
    for key, value in team_criteria.items():
        if key in team_members_df.columns:
            team_members_df = team_members_df[team_members_df[key] == value]

    # 日付ごとに、その日に勤務したチームメンバーのリストを作成
    team_daily = team_members_df.groupby(team_members_df['ds'].dt.date)['staff'].unique().reset_index()
    team_daily = team_daily.rename(columns={'ds': 'date', 'staff': 'members'})

    if team_daily.empty:
        return pd.DataFrame()

    # 2. 各日のチームのスコアを計算
    daily_stats = []
    for _, row in team_daily.iterrows():
        date = row['date']
        members = row['members']

        # 疲労スコアの平均とばらつき
        fatigue_scores = (
            fatigue_df[fatigue_df.index.isin(members)]['fatigue_score']
            if not fatigue_df.empty
            else pd.Series()
        )

        # 不公平スコアの平均とばらつき
        fairness_scores = (
            fairness_df[fairness_df['staff'].isin(members)]['unfairness_score']
            if not fairness_df.empty
            else pd.Series()
        )

        daily_stats.append(
            {
                'date': date,
                'member_count': len(members),
                'avg_fatigue': fatigue_scores.mean(),
                'std_fatigue': fatigue_scores.std(),
                'avg_unfairness': fairness_scores.mean(),
                'std_unfairness': fairness_scores.std(),
            }
        )

    result_df = pd.DataFrame(daily_stats).set_index('date').fillna(0)
    return result_df
