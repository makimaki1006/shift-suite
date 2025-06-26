from __future__ import annotations
import pandas as pd


def _calculate_role_first_rules(long_df: pd.DataFrame) -> list:
    """役割軸の法則を抽出する"""
    rules = []
    if 'role' not in long_df.columns:
        return rules

    for role, group_df in long_df.groupby('role'):
        total_days = group_df['ds'].dt.date.nunique()
        unique_staff = group_df['staff'].nunique()
        if total_days > 0 and unique_staff > 0:
            # 「固定度スコア」を計算
            stability_score = 1 - (unique_staff / total_days)
            rules.append({
                "法則のカテゴリー": "役割軸",
                "発見された法則": f"「{role}」は、少数の固定メンバーで担当されている",
                "法則の強度": round(stability_score, 2)
            })
    return rules


def _calculate_person_first_rules(long_df: pd.DataFrame) -> list:
    """個人軸の法則を抽出する"""
    rules = []
    if long_df.empty:
        return rules

    daily_work = long_df.drop_duplicates(subset=['ds', 'staff'])

    for staff, group_df in daily_work.groupby('staff'):
        if len(group_df) < 2:
            stability_score = 1.0  # 勤務が1日だけならパターンは固定的とみなす
        else:
            weekday_std = group_df['ds'].dt.dayofweek.std()
            stability_score = 1 / (1 + weekday_std) if not pd.isna(weekday_std) else 0

        rules.append({
            "法則のカテゴリー": "個人軸",
            "発見された法則": f"「{staff}」さんは、毎週ほぼ同じ曜日に勤務している",
            "法則の強度": round(stability_score, 2)
        })
    return rules


def _calculate_sequential_rules(long_df: pd.DataFrame) -> list:
    """順序の法則を抽出する"""
    rules = []
    if 'is_night' not in long_df.columns or not long_df['is_night'].any():
        return rules

    night_shifts = long_df[long_df['is_night']].sort_values('ds')
    if night_shifts.empty:
        return rules

    total_night_shifts = len(night_shifts)
    off_after_night = 0

    for index, row in night_shifts.iterrows():
        next_day = row['ds'].date() + pd.Timedelta(days=1)
        next_day_shifts = long_df[
            (long_df['staff'] == row['staff']) &
            (long_df['ds'].dt.date == next_day)
        ]
        if next_day_shifts.empty or next_day_shifts['parsed_slots_count'].sum() == 0:
            off_after_night += 1

    off_after_night_ratio = off_after_night / total_night_shifts if total_night_shifts > 0 else 0

    rules.append({
        "法則のカテゴリー": "順序の法則",
        "発見された法則": "「夜勤」の翌日は「休み」が割り当てられる傾向がある",
        "法則の強度": round(off_after_night_ratio, 2)
    })
    return rules



def create_blueprint_list(long_df: pd.DataFrame) -> dict:
    """シフトデータから法則を網羅的に抽出し、強度順のリストとして返す。"""
    if long_df.empty:
        return {"error": "分析対象の勤務データがありません。"}

    # --- データ準備 ---
    long_df['date'] = pd.to_datetime(long_df['ds'].dt.date)
    long_df['is_night'] = long_df['code'].astype(str).str.contains("夜", na=False)

    # --- 全カテゴリーの法則を無条件に抽出 ---
    role_rules = _calculate_role_first_rules(long_df)
    person_rules = _calculate_person_first_rules(long_df)
    sequential_rules = _calculate_sequential_rules(long_df)

    all_rules = role_rules + person_rules + sequential_rules

    if not all_rules:
        return {
            "summary": "分析可能な法則が見つかりませんでした。",
            "rules_df": pd.DataFrame()
        }

    # --- 法則を強度順にソート ---
    rules_df = pd.DataFrame(all_rules).sort_values("法則の強度", ascending=False).reset_index(drop=True)

    # --- 総合的な洞察サマリーを生成 ---
    summary_text = "このシフトの作成プロセスは、複数の法則が組み合わさってできています。\n"
    if not rules_df.empty:
        top_rule = rules_df.iloc[0]
        summary_text += f"最も強い影響力を持つのは、**『{top_rule['法則のカテゴリー']}』**の法則、具体的には**「{top_rule['発見された法則']}」**（強度: {top_rule['法則の強度']}）です。"
        if len(rules_df) > 1:
            second_rule = rules_df.iloc[1]
            summary_text += f"\n次いで、**『{second_rule['法則のカテゴリー']}』**の**「{second_rule['発見された法則']}」**（強度: {second_rule['法則の強度']}）も重要なルールとなっています。"

    summary_text += "\n\n以下のリスト全体を眺めることで、あなたの職場のシフト作成における『暗黙の優先順位』をより深く理解できます。"

    return {
        "summary": summary_text,
        "rules_df": rules_df
    }
