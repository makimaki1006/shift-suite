from __future__ import annotations

import logging
from collections import defaultdict
from itertools import combinations
from typing import Any, Dict

import numpy as np
import pandas as pd
from shift_suite.tasks.constants import STATISTICAL_THRESHOLDS, FATIGUE_PARAMETERS, NIGHT_START_HOUR, NIGHT_END_HOUR
from shift_suite.tasks.utils import validate_and_convert_slot_minutes, safe_slot_calculation

# --- analysis thresholds (統一された定数を使用) ---
SYNERGY_HIGH_THRESHOLD = STATISTICAL_THRESHOLDS["synergy_high_threshold"]
SYNERGY_LOW_THRESHOLD = STATISTICAL_THRESHOLDS["synergy_low_threshold"]
VETERAN_RATIO_THRESHOLD = STATISTICAL_THRESHOLDS["veteran_ratio_threshold"]
ROLE_RATIO_THRESHOLD = STATISTICAL_THRESHOLDS["role_ratio_threshold"]
MONTH_END_RATIO_THRESHOLD = STATISTICAL_THRESHOLDS["month_end_ratio_threshold"]
WEEKEND_RATIO_THRESHOLD = STATISTICAL_THRESHOLDS["weekend_ratio_threshold"]
EARLY_MONTH_RATIO_THRESHOLD = STATISTICAL_THRESHOLDS["early_month_ratio_threshold"]
ROLE_COMBO_RATIO_THRESHOLD = STATISTICAL_THRESHOLDS["role_combo_ratio_threshold"]
NEW_STAFF_ONLY_RATIO_THRESHOLD = STATISTICAL_THRESHOLDS["new_staff_only_ratio_threshold"]

log = logging.getLogger(__name__)


def _analyze_skill_synergy(long_df: pd.DataFrame) -> list:
    """スキル相性マトリクス分析：誰と誰を組ませると上手くいくか"""
    rules = []

    if 'staff' not in long_df.columns:
        return rules

    # 同時勤務の実績を集計
    daily_staff = long_df[long_df['parsed_slots_count'] > 0].groupby(
        ['ds', 'code']
    )['staff'].apply(list).reset_index()

    # ペアごとの共働回数をカウント
    pair_counts = defaultdict(int)
    total_shifts_per_staff = long_df.groupby('staff')['ds'].nunique()

    for _, row in daily_staff.iterrows():
        staff_list = row['staff']
        if len(staff_list) >= 2:
            for pair in combinations(sorted(set(staff_list)), 2):
                pair_counts[pair] += 1

    # 期待値との乖離を計算
    for (staff1, staff2), actual_count in pair_counts.items():
        if staff1 not in total_shifts_per_staff.index or staff2 not in total_shifts_per_staff.index:
            continue

        # 独立した場合の期待共働回数
        total_days = long_df['ds'].dt.date.nunique()
        prob1 = total_shifts_per_staff[staff1] / total_days
        prob2 = total_shifts_per_staff[staff2] / total_days
        expected_count = prob1 * prob2 * total_days

        if expected_count > 0:
            synergy_score = actual_count / expected_count

            # 期待値から大きく乖離している組み合わせを検出
            if synergy_score > SYNERGY_HIGH_THRESHOLD:
                rules.append({
                    "法則のカテゴリー": "スキル相性",
                    "発見された法則": f"「{staff1}」と「{staff2}」は意図的に同じシフトに配置される（相性◎）",
                    "法則の強度": round(min(synergy_score / 2, 1.0), 2),
                    "詳細データ": {"実績": actual_count, "期待値": round(expected_count, 1)}
                })
            elif synergy_score < SYNERGY_LOW_THRESHOLD:
                rules.append({
                    "法則のカテゴリー": "スキル相性",
                    "発見された法則": f"「{staff1}」と「{staff2}」は意図的に別シフトに配置される（相性×）",
                    "法則の強度": round(1.0 - synergy_score, 2),
                    "詳細データ": {"実績": actual_count, "期待値": round(expected_count, 1)}
                })

    return rules


def _analyze_workload_distribution(long_df: pd.DataFrame) -> list:
    """負荷バランシング戦略：繁忙時間帯での人員配置パターン"""
    rules = []

    if not {'staff', 'role'}.issubset(long_df.columns):
        return rules

    # 時間帯別の平均人員数を計算
    time_staff_counts = long_df[long_df['parsed_slots_count'] > 0].groupby(
        long_df['ds'].dt.time
    )['staff'].nunique().reset_index()
    time_staff_counts.columns = ['time', 'avg_staff']

    # 繁忙時間帯を特定（上位25%）
    threshold = time_staff_counts['avg_staff'].quantile(STATISTICAL_THRESHOLDS["quantile_75"])
    busy_times = time_staff_counts[time_staff_counts['avg_staff'] >= threshold]['time'].tolist()

    if not busy_times:
        return rules

    # 繁忙時間帯での職員の経験値分布を分析
    busy_df = long_df[long_df['ds'].dt.time.isin(busy_times)]

    # 各職員の総勤務日数（経験値の代理指標）
    staff_experience = long_df.groupby('staff')['ds'].nunique().sort_values(ascending=False)
    median_exp = staff_experience.median()

    # 繁忙時間帯でのベテラン配置率
    busy_staff = busy_df['staff'].unique()
    veteran_staff = staff_experience[staff_experience > median_exp].index
    veteran_ratio = len(set(busy_staff) & set(veteran_staff)) / len(busy_staff) if len(busy_staff) > 0 else 0

    if veteran_ratio > VETERAN_RATIO_THRESHOLD:
        rules.append({
            "法則のカテゴリー": "負荷分散戦略",
            "発見された法則": "繁忙時間帯には必ずベテラン職員を優先配置している",
            "法則の強度": round(veteran_ratio, 2),
            "詳細データ": {"繁忙時間帯": [str(t) for t in busy_times[:5]], "ベテラン配置率": f"{veteran_ratio:.1%}"}
        })

    # 役割別の分布も分析
    for role in busy_df['role'].unique():
        role_ratio = len(busy_df[busy_df['role'] == role]) / len(busy_df)
        if role_ratio > ROLE_RATIO_THRESHOLD:
            rules.append({
                "法則のカテゴリー": "負荷分散戦略",
                "発見された法則": f"繁忙時間帯では「{role}」の配置を重視している",
                "法則の強度": round(role_ratio, 2),
                "詳細データ": {"役割比率": f"{role_ratio:.1%}"}
            })

    return rules


def _analyze_personal_consideration(long_df: pd.DataFrame) -> list:
    """個人事情配慮パターン：特定職員への定期的な配慮"""
    rules = []

    if 'staff' not in long_df.columns:
        return rules

    # 各職員の勤務パターンを分析
    for staff in long_df['staff'].unique():
        staff_df = long_df[long_df['staff'] == staff].copy()

        # 曜日×時間帯の勤務頻度を計算
        staff_df['dow'] = staff_df['ds'].dt.dayofweek
        staff_df['hour'] = staff_df['ds'].dt.hour

        # 特定の曜日・時間帯を避けているパターンを検出
        dow_hour_counts = staff_df.groupby(['dow', 'hour']).size()
        total_weeks = staff_df['ds'].dt.isocalendar().week.nunique()

        # 期待頻度と実際の頻度を比較
        for (dow, hour), count in dow_hour_counts.items():
            expected_count = total_weeks * 0.8  # 80%の出現を期待値とする

            if count < expected_count * 0.2:  # 期待値の20%未満
                dow_names = ['月', '火', '水', '木', '金', '土', '日']
                rules.append({
                    "法則のカテゴリー": "個人配慮",
                    "発見された法則": f"「{staff}」は{dow_names[dow]}曜日の{hour}時台をほぼ避けている（個人事情？）",
                    "法則の強度": round(1.0 - (count / expected_count if expected_count > 0 else 0), 2),
                    "詳細データ": {"出現回数": count, "期待回数": round(expected_count, 1)}
                })

        # 月初・月末パターンも分析
        staff_df['day'] = staff_df['ds'].dt.day
        month_pattern = staff_df.groupby(staff_df['day'] <= 5)['ds'].count()

        if len(month_pattern) == 2:
            early_month_ratio = month_pattern[True] / month_pattern.sum()
            if early_month_ratio < EARLY_MONTH_RATIO_THRESHOLD:
                rules.append({
                    "法則のカテゴリー": "個人配慮",
                    "発見された法則": f"「{staff}」は月初（1-5日）の勤務をほぼ避けている",
                    "法則の強度": round(1.0 - early_month_ratio, 2),
                    "詳細データ": {"月初勤務率": f"{early_month_ratio:.1%}"}
                })

    return rules


def _analyze_rotation_strategy(long_df: pd.DataFrame) -> list:
    """ローテーション戦略：公平性を保つための複雑なルール"""
    rules = []

    if not {'staff', 'code'}.issubset(long_df.columns):
        return rules

    # 各職員の勤務パターンの連続性を分析
    for staff in long_df['staff'].unique():
        staff_df = long_df[long_df['staff'] == staff].sort_values('ds')

        # 連続勤務日数の計算
        staff_dates = staff_df[staff_df['parsed_slots_count'] > 0]['ds'].dt.date.unique()

        if len(staff_dates) < 2:
            continue

        # 連続勤務のカウント
        consecutive_counts = []
        current_streak = 1

        for i in range(1, len(staff_dates)):
            if (staff_dates[i] - staff_dates[i-1]).days == 1:
                current_streak += 1
            else:
                if current_streak > 1:
                    consecutive_counts.append(current_streak)
                current_streak = 1

        if current_streak > 1:
            consecutive_counts.append(current_streak)

        # 長期連勤の検出
        if consecutive_counts:
            max_consecutive = max(consecutive_counts)
            avg_consecutive = np.mean(consecutive_counts)

            if max_consecutive <= 3 and avg_consecutive < 2.5:
                rules.append({
                    "法則のカテゴリー": "ローテーション戦略",
                    "発見された法則": f"「{staff}」の連続勤務は必ず3日以内に制限されている",
                    "法則の強度": round(1.0 - (max_consecutive - 3) / 7, 2),
                    "詳細データ": {"最大連続": max_consecutive, "平均連続": round(avg_consecutive, 1)}
                })

        # 勤務コードのローテーションパターン
        code_sequence = staff_df[staff_df['parsed_slots_count'] > 0]['code'].tolist()

        if len(code_sequence) >= 3:
            # 同じコードの連続を避けているか
            same_code_runs = []
            current_run = 1

            for i in range(1, len(code_sequence)):
                if code_sequence[i] == code_sequence[i-1]:
                    current_run += 1
                else:
                    if current_run > 1:
                        same_code_runs.append(current_run)
                    current_run = 1

            if same_code_runs and max(same_code_runs) <= 2:
                rules.append({
                    "法則のカテゴリー": "ローテーション戦略",
                    "発見された法則": f"「{staff}」は同じ勤務パターンが3日以上続かないようローテーションされている",
                    "法則の強度": 0.8,
                    "詳細データ": {"最大連続同一勤務": max(same_code_runs)}
                })

    return rules


def _analyze_risk_mitigation(long_df: pd.DataFrame) -> list:
    """リスク回避ルール：トラブル防止のための暗黙の配置ルール"""
    rules = []

    if not {'staff', 'role'}.issubset(long_df.columns):
        return rules

    # 各時間帯での新人比率を分析
    staff_experience = long_df.groupby('staff')['ds'].nunique()
    experience_threshold = staff_experience.quantile(0.25)  # 下位25%を新人とする
    new_staff = staff_experience[staff_experience <= experience_threshold].index

    # 時間帯別の新人比率
    time_groups = long_df[long_df['parsed_slots_count'] > 0].groupby(
        [long_df['ds'].dt.date, long_df['ds'].dt.hour]
    )

    new_staff_only_count = 0
    total_time_slots = 0

    for (date, hour), group in time_groups:
        unique_staff = group['staff'].unique()
        if len(unique_staff) > 1:  # 複数人勤務の場合のみ
            total_time_slots += 1
            if all(s in new_staff for s in unique_staff):
                new_staff_only_count += 1

    if total_time_slots > 0:
        new_staff_only_ratio = new_staff_only_count / total_time_slots

        if new_staff_only_ratio < NEW_STAFF_ONLY_RATIO_THRESHOLD:
            rules.append({
                "法則のカテゴリー": "リスク回避",
                "発見された法則": "新人だけのシフトは絶対に作らない（必ずベテランを1人は配置）",
                "法則の強度": round(1.0 - new_staff_only_ratio, 2),
                "詳細データ": {"新人のみシフト発生率": f"{new_staff_only_ratio:.1%}"}
            })

    # 特定の役割の組み合わせ分析
    role_combinations = defaultdict(int)

    for (date, time), group in long_df.groupby([long_df['ds'].dt.date, long_df['ds'].dt.time]):
        roles = group['role'].unique()
        if len(roles) >= 2:
            for combo in combinations(sorted(roles), 2):
                role_combinations[combo] += 1

    # 期待値と比較して異常に少ない組み合わせを検出
    if role_combinations:
        avg_count = np.mean(list(role_combinations.values()))
        for combo, count in role_combinations.items():
            if count < avg_count * ROLE_COMBO_RATIO_THRESHOLD:
                rules.append({
                    "法則のカテゴリー": "リスク回避",
                    "発見された法則": f"「{combo[0]}」と「{combo[1]}」は同時配置を避けている（業務上の理由？）",
                    "法則の強度": round(1.0 - (count / avg_count if avg_count > 0 else 0), 2),
                    "詳細データ": {"出現回数": count, "平均": round(avg_count, 1)}
                })

    return rules


def _analyze_temporal_context(long_df: pd.DataFrame) -> list:
    """時系列コンテキスト分析：時期による配置戦略の変化"""
    rules = []

    if 'ds' not in long_df.columns:
        return rules

    # 月別の傾向分析
    long_df['month'] = long_df['ds'].dt.month
    long_df['day'] = long_df['ds'].dt.day

    # 月初・月中・月末での人員配置の違い
    long_df['period'] = pd.cut(long_df['day'], bins=[0, 10, 20, 31], labels=['月初', '月中', '月末'])

    period_stats = long_df[long_df['parsed_slots_count'] > 0].groupby(['period']).agg({
        'staff': 'nunique',
        'ds': 'count'
    })

    if len(period_stats) > 1 and '月末' in period_stats.index:
        period_stats['avg_staff_per_slot'] = period_stats['ds'] / period_stats['staff']

        mean_staff_per_slot = period_stats['avg_staff_per_slot'].mean()
        if mean_staff_per_slot > 0:
            month_end_ratio = period_stats.loc['月末', 'avg_staff_per_slot'] / mean_staff_per_slot
            if month_end_ratio > MONTH_END_RATIO_THRESHOLD:
                rules.append({
                    "法則のカテゴリー": "時系列戦略",
                    "発見された法則": "月末は通常より手厚い人員配置を行っている（締め作業対応？）",
                    "法則の強度": round(min(month_end_ratio - 1.0, 1.0), 2),
                    "詳細データ": {"月末配置倍率": f"{month_end_ratio:.2f}倍"}
                })

    # 曜日による戦略の違い
    long_df['dow'] = long_df['ds'].dt.dayofweek

    dow_stats = long_df[long_df['parsed_slots_count'] > 0].groupby('dow').agg({
        'staff': 'nunique',
        'code': lambda x: x.value_counts().to_dict()
    })

    # 週末の特別な配置パターン
    if 5 in dow_stats.index and 6 in dow_stats.index:  # 土日
        weekend_staff = dow_stats.loc[[5, 6], 'staff'].mean()
        weekday_staff = dow_stats.loc[[0, 1, 2, 3, 4], 'staff'].mean() if len(dow_stats) > 2 else 0

        if weekday_staff > 0:
            weekend_ratio = weekend_staff / weekday_staff
            if weekend_ratio < WEEKEND_RATIO_THRESHOLD:
                rules.append({
                    "法則のカテゴリー": "時系列戦略",
                    "発見された法則": "週末は平日の70%以下の省力体制で運営している",
                    "法則の強度": round(1.0 - weekend_ratio, 2),
                    "詳細データ": {"週末/平日比": f"{weekend_ratio:.1%}"}
                })

    return rules


def _extract_surprising_insights(rules_df: pd.DataFrame) -> list:
    """意外性の高い発見をピックアップ"""
    if rules_df.empty:
        return []

    surprising = []

    # 個人配慮カテゴリーから意外なものを抽出
    personal_rules = rules_df[rules_df['法則のカテゴリー'] == '個人配慮']
    if not personal_rules.empty:
        top_personal = personal_rules.nlargest(3, '法則の強度')
        for _, rule in top_personal.iterrows():
            surprising.append({
                "発見": rule['発見された法則'],
                "意外性": "特定個人への配慮が明確にデータに現れている"
            })

    # スキル相性で相性が悪いペア
    bad_synergy = rules_df[
        (rules_df['法則のカテゴリー'] == 'スキル相性') &
        (rules_df['発見された法則'].str.contains('別シフト'))
    ]
    if not bad_synergy.empty:
        for _, rule in bad_synergy.iterrows():
            surprising.append({
                "発見": rule['発見された法則'],
                "意外性": "意図的に組み合わせを避けている職員ペアの存在"
            })

    return surprising


def _generate_deep_insights_summary(rules_df: pd.DataFrame) -> str:
    """より洞察的なサマリーを生成"""
    if rules_df.empty:
        return "分析可能な法則が見つかりませんでした。"

    summary_parts = []

    # カテゴリー別の法則数をカウント
    category_counts = rules_df['法則のカテゴリー'].value_counts()

    summary_parts.append("## 🔍 シフト作成の深層分析結果\n")
    summary_parts.append(f"合計 **{len(rules_df)}個** の暗黙のルールを発見しました。\n")

    # 最も強い法則トップ3
    top_rules = rules_df.nlargest(3, '法則の強度')
    summary_parts.append("\n### 📊 最も影響力の強いルール TOP3\n")
    for i, (_, rule) in enumerate(top_rules.iterrows(), 1):
        summary_parts.append(f"{i}. **{rule['発見された法則']}** (強度: {rule['法則の強度']})")

    # カテゴリー別の特徴
    summary_parts.append("\n### 🎯 カテゴリー別の特徴\n")

    if 'スキル相性' in category_counts:
        summary_parts.append(f"- **人間関係への配慮**: {category_counts['スキル相性']}個のルール")
    if '個人配慮' in category_counts:
        summary_parts.append(f"- **個人事情への対応**: {category_counts['個人配慮']}個のルール")
    if 'リスク回避' in category_counts:
        summary_parts.append(f"- **トラブル防止策**: {category_counts['リスク回避']}個のルール")

    # 総括
    summary_parts.append("\n### 💡 総括")
    summary_parts.append("このシフトは、表面的なルールだけでなく、")
    summary_parts.append("職員間の相性、個人の事情、リスク管理など、")
    summary_parts.append("**多次元的な配慮**が複雑に組み合わさって作成されています。")

    return "\n".join(summary_parts)


def _calculate_fairness_score(daily_shift_df: pd.DataFrame) -> float:
    """その日のシフトの公平性スコアを計算"""
    work_hours = daily_shift_df.groupby("staff")["ds"].count()
    if work_hours.empty:
        return 0.0
    return 1.0 - (work_hours.std() / (work_hours.mean() + 1e-6))


def _calculate_cost_score(daily_shift_df: pd.DataFrame, max_staff: int) -> float:
    """その日のシフトのコストスコアを計算"""
    staff_count = daily_shift_df["staff"].nunique()
    if max_staff == 0:
        return 1.0
    return 1.0 - (staff_count / max_staff)


def _calculate_risk_score(daily_shift_df: pd.DataFrame, new_staff: set[str]) -> float:
    """新人だけのシフトを避けられているかでリスクを評価"""
    time_groups = daily_shift_df.groupby(daily_shift_df["ds"].dt.hour)
    new_only = 0
    total = 0
    for _, group in time_groups:
        staff = set(group["staff"].unique())
        if len(staff) > 1:
            total += 1
            if all(s in new_staff for s in staff):
                new_only += 1
    if total == 0:
        return 1.0
    return 1.0 - new_only / total


def _calculate_satisfaction_score(date: pd.Timestamp, long_df: pd.DataFrame) -> float:
    """連勤の長さから満足度を推定"""
    day_df = long_df[long_df["ds"].dt.date == date.date()]
    staff_list = day_df["staff"].unique()
    long_run = 0
    for staff in staff_list:
        staff_dates = (
            long_df[long_df["staff"] == staff]["ds"].dt.date.drop_duplicates().sort_values()
        )
        indices = [i for i, d in enumerate(staff_dates) if d == date.date()]
        for idx in indices:
            left = idx
            while left > 0 and (staff_dates.iloc[left] - staff_dates.iloc[left - 1]).days == 1:
                left -= 1
            right = idx
            while right < len(staff_dates) - 1 and (
                staff_dates.iloc[right + 1] - staff_dates.iloc[right]
            ).days == 1:
                right += 1
            if right - left + 1 >= 4:
                long_run += 1
                break
    if len(staff_list) == 0:
        return 1.0
    return 1.0 - long_run / len(staff_list)


def create_scored_blueprint(long_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate daily scores representing shift creator preferences."""
    if long_df.empty:
        return pd.DataFrame()

    df = long_df.copy()
    df["ds"] = pd.to_datetime(df["ds"])

    daily_groups = df.groupby(df["ds"].dt.date)
    max_staff = daily_groups["staff"].nunique().max()

    staff_experience = df.groupby("staff")["ds"].nunique()
    threshold = staff_experience.quantile(0.25)
    new_staff = set(staff_experience[staff_experience <= threshold].index)

    scored_days = []
    for date, group in daily_groups:
        scores = {
            "date": pd.to_datetime(date),
            "fairness_score": _calculate_fairness_score(group),
            "cost_score": _calculate_cost_score(group, int(max_staff)),
            "risk_score": _calculate_risk_score(group, new_staff),
            "satisfaction_score": _calculate_satisfaction_score(pd.to_datetime(date), df),
        }
        scored_days.append(scores)

    return pd.DataFrame(scored_days).set_index("date")


def analyze_tradeoffs(scored_blueprint_df: pd.DataFrame) -> dict:
    """スコア間のトレードオフを分析する"""
    if scored_blueprint_df.empty:
        return {}

    corr = scored_blueprint_df.corr()
    tradeoff_pairs = {}
    for col1 in corr.columns:
        for col2 in corr.columns:
            if col1 != col2 and corr.loc[col1, col2] < -0.5:
                tradeoff_pairs[f"{col1}_vs_{col2}"] = float(corr.loc[col1, col2])

    scatter_cols = {"fairness_score", "cost_score"}
    scatter_data = (
        scored_blueprint_df[list(scatter_cols)].reset_index().to_dict("records")
        if scatter_cols.issubset(scored_blueprint_df.columns)
        else []
    )

    return {
        "correlation_matrix": corr.to_dict(),
        "strongest_tradeoffs": tradeoff_pairs,
        "scatter_data": scatter_data,
    }


def create_staff_level_blueprint(
    long_df: pd.DataFrame, score_df: pd.DataFrame
) -> pd.DataFrame:
    """スタッフ毎のブループリントスコアを集計"""
    if long_df.empty or score_df.empty:
        return pd.DataFrame()

    staff_by_day = long_df[["ds", "staff"]].copy()
    staff_by_day["date"] = staff_by_day["ds"].dt.date

    score_df_reset = score_df.reset_index()

    # staff_by_dayの'date'列を、score_df_resetに合わせて日付型(datetime64[ns])に変換します。
    staff_by_day["date"] = pd.to_datetime(staff_by_day["date"])

    merged = staff_by_day.merge(score_df_reset, on="date", how="left")

    if merged.empty or "staff" not in merged.columns:
        return pd.DataFrame()

    score_cols = [
        "fairness_score",
        "cost_score",
        "risk_score",
        "satisfaction_score",
    ]
    return merged.groupby("staff")[score_cols].mean()


# backward compatibility
def create_blueprint_list(long_df: pd.DataFrame) -> dict:
    """Return discovered rules and scoring analysis as a single dictionary."""
    if long_df.empty:
        return {}

    # --- legacy implicit rule discovery logic ---
    log.info("ブループリント分析（ルール発見）を開始します...")
    all_rules: list[dict] = []
    all_rules.extend(_analyze_skill_synergy(long_df))
    all_rules.extend(_analyze_workload_distribution(long_df))
    all_rules.extend(_analyze_personal_consideration(long_df))
    all_rules.extend(_analyze_rotation_strategy(long_df))
    all_rules.extend(_analyze_risk_mitigation(long_df))
    all_rules.extend(_analyze_temporal_context(long_df))

    rules_df = (
        pd.DataFrame(all_rules).sort_values("法則の強度", ascending=False).reset_index(drop=True)
        if all_rules
        else pd.DataFrame()
    )

    # --- scoring and trade-off analysis ---
    log.info("ブループリント分析（スコア化・トレードオフ分析）を開始します...")
    scored_df = create_scored_blueprint(long_df)
    tradeoff_info = analyze_tradeoffs(scored_df)

    # --- staff level scores ---
    staff_level_scores = create_staff_level_blueprint(long_df, scored_df)

    return {
        "rules_df": rules_df,
        "scored_df": scored_df,
        "tradeoffs": tradeoff_info,
        "staff_level_scores": staff_level_scores,
    }


# backward compatibility を保ちつつ拡張
_original_create_blueprint_list = create_blueprint_list


class FactExtractor:
    """シフトデータから客観的な事実を抽出するクラス"""

    def __init__(self, slot_minutes: int = 30) -> None:
        self.weekday_names = ['月', '火', '水', '木', '金', '土', '日']
        # 動的スロット設定
        self.slot_hours = validate_and_convert_slot_minutes(slot_minutes, "FactExtractor.__init__")
        self.slot_minutes = slot_minutes

    def extract_all_facts(self, long_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """全ての客観的事実を体系的に抽出"""

        if long_df.empty:
            return {}

        facts = {
            "勤務パターン事実": self._extract_work_pattern_facts(long_df),
            "曜日事実": self._extract_weekday_facts(long_df),
            "コード事実": self._extract_code_facts(long_df),
            "時間帯事実": self._extract_time_facts(long_df),
            "ペア事実": self._extract_pair_facts(long_df),
            "統計的事実": self._extract_statistical_facts(long_df),
        }

        return facts

    def _extract_work_pattern_facts(self, long_df: pd.DataFrame) -> pd.DataFrame:
        """勤務パターンに関するシンプルな事実を抽出"""
        return pd.DataFrame()

    def _extract_weekday_facts(self, long_df: pd.DataFrame) -> pd.DataFrame:
        """スタッフごとの曜日別勤務事実を抽出"""
        facts = []

        for staff in long_df['staff'].unique():
            staff_df = long_df[long_df['staff'] == staff]
            staff_df = staff_df[staff_df['parsed_slots_count'] > 0]

            if staff_df.empty:
                continue

            weekday_counts = staff_df.groupby(staff_df['ds'].dt.dayofweek).size()
            total_days = staff_df['ds'].dt.date.nunique()

            working_days = weekday_counts[weekday_counts > 0].index.tolist()

            if len(working_days) < 7:
                working_day_names = [self.weekday_names[d] for d in working_days]
                facts.append({
                    "スタッフ": staff,
                    "事実タイプ": "曜日限定勤務",
                    "詳細": f"{', '.join(working_day_names)}のみ勤務",
                    "勤務曜日数": len(working_days),
                    "総勤務日数": total_days,
                    "確信度": min(1.0, total_days / 10),
                })

            if len(weekday_counts) > 0 and total_days >= 5:
                for day, count in weekday_counts.items():
                    expected_ratio = 1 / 7
                    actual_ratio = count / total_days
                    if actual_ratio > expected_ratio * 2:
                        facts.append({
                            "スタッフ": staff,
                            "事実タイプ": "曜日偏重",
                            "詳細": f"{self.weekday_names[day]}曜日に{actual_ratio:.1%}が集中",
                            "実績比率": round(actual_ratio, 3),
                            "期待比率": round(expected_ratio, 3),
                            "偏重度": round(actual_ratio / expected_ratio, 2),
                            "確信度": min(1.0, total_days / 10),
                        })

        return pd.DataFrame(facts)

    def _extract_code_facts(self, long_df: pd.DataFrame) -> pd.DataFrame:
        """勤務コードに関する事実を抽出"""
        facts = []

        all_codes = sorted(long_df[long_df['code'] != '']['code'].unique())

        for staff in long_df['staff'].unique():
            staff_df = long_df[long_df['staff'] == staff]
            staff_df = staff_df[staff_df['code'] != '']

            if staff_df.empty:
                continue

            used_codes = sorted(staff_df['code'].unique())

            if len(used_codes) > 0 and len(used_codes) < len(all_codes) * 0.5:
                facts.append({
                    "スタッフ": staff,
                    "事実タイプ": "限定コード使用",
                    "詳細": f"使用コード: {', '.join(used_codes[:5])}{'...' if len(used_codes) > 5 else ''}",
                    "使用コード数": len(used_codes),
                    "全コード数": len(all_codes),
                    "使用率": round(len(used_codes) / len(all_codes), 3),
                    "確信度": 1.0,
                })

            avoided_codes = sorted(set(all_codes) - set(used_codes))
            if avoided_codes and len(avoided_codes) < len(all_codes) * 0.5:
                facts.append({
                    "スタッフ": staff,
                    "事実タイプ": "コード回避",
                    "詳細": f"未使用コード: {', '.join(avoided_codes[:5])}{'...' if len(avoided_codes) > 5 else ''}",
                    "回避コード数": len(avoided_codes),
                    "確信度": 1.0,
                })

            if len(staff_df) > 0:
                code_freq = staff_df['code'].value_counts(normalize=True)
                if len(code_freq) > 0 and code_freq.iloc[0] > 0.7:
                    facts.append({
                        "スタッフ": staff,
                        "事実タイプ": "主要コード依存",
                        "詳細": f"{code_freq.index[0]}が{code_freq.iloc[0]:.1%}を占める",
                        "主要コード": code_freq.index[0],
                        "依存度": round(code_freq.iloc[0], 3),
                        "確信度": min(1.0, len(staff_df) / 20),
                    })

        return pd.DataFrame(facts)

    def _extract_time_facts(self, long_df: pd.DataFrame) -> pd.DataFrame:
        """時間帯に関する事実を抽出"""
        facts = []

        for staff in long_df['staff'].unique():
            staff_df = long_df[long_df['staff'] == staff]
            staff_df = staff_df[staff_df['parsed_slots_count'] > 0]

            if staff_df.empty:
                continue

            hours = staff_df['ds'].dt.hour
            if len(hours) > 0:
                early_morning_ratio = (hours < 6).sum() / len(hours)
                if early_morning_ratio > FATIGUE_PARAMETERS["early_morning_threshold"]:
                    facts.append({
                        "スタッフ": staff,
                        "事実タイプ": "早朝勤務",
                        "詳細": f"全勤務の{early_morning_ratio:.1%}が6時前",
                        "比率": round(early_morning_ratio, 3),
                        "確信度": min(1.0, len(hours) / 50),
                    })

                night_hours_mask = hours.apply(lambda h: h >= NIGHT_START_HOUR or h < NIGHT_END_HOUR)
                night_ratio = night_hours_mask.sum() / len(hours)
                if night_ratio > FATIGUE_PARAMETERS["night_shift_threshold"]:
                    facts.append({
                        "スタッフ": staff,
                        "事実タイプ": "深夜勤務",
                        "詳細": f"全勤務の{night_ratio:.1%}が22時以降",
                        "比率": round(night_ratio, 3),
                        "確信度": min(1.0, len(hours) / 50),
                    })

                hour_std = hours.std()
                if hour_std < 2:
                    mode_hour = hours.mode()[0] if len(hours.mode()) > 0 else hours.mean()
                    facts.append({
                        "スタッフ": staff,
                        "事実タイプ": "固定時間帯勤務",
                        "詳細": f"主に{int(mode_hour)}時台を中心に勤務",
                        "中心時間": int(mode_hour),
                        "ばらつき": round(hour_std, 2),
                        "確信度": min(1.0, len(hours) / 30),
                    })

        return pd.DataFrame(facts)

    def _extract_pair_facts(self, long_df: pd.DataFrame) -> pd.DataFrame:
        """ペア勤務に関する事実を抽出"""
        facts = []

        daily_staff = long_df[long_df['parsed_slots_count'] > 0].groupby(
            ['ds', 'code']
        )['staff'].apply(list).reset_index()

        pair_counts = defaultdict(int)
        total_shifts_per_staff = long_df.groupby('staff')['ds'].nunique()

        for _, row in daily_staff.iterrows():
            staff_list = row['staff']
            if len(staff_list) >= 2:
                for pair in combinations(sorted(set(staff_list)), 2):
                    pair_counts[pair] += 1

        for (staff1, staff2), count in pair_counts.items():
            if staff1 in total_shifts_per_staff.index and staff2 in total_shifts_per_staff.index:
                min_shifts = min(total_shifts_per_staff[staff1], total_shifts_per_staff[staff2])
                if min_shifts > 0:
                    pair_ratio = count / min_shifts

                    if pair_ratio > 0.5:
                        facts.append({
                            "スタッフ": f"{staff1} & {staff2}",
                            "事実タイプ": "頻繁ペア",
                            "詳細": f"共働率{pair_ratio:.1%} ({count}回)",
                            "共働回数": count,
                            "共働率": round(pair_ratio, 3),
                            "確信度": min(1.0, count / 10),
                        })
                    elif count == 0:
                        facts.append({
                            "スタッフ": f"{staff1} & {staff2}",
                            "事実タイプ": "非共働ペア",
                            "詳細": "一度も同じシフトに入っていない",
                            "共働回数": 0,
                            "確信度": min(1.0, min_shifts / 10),
                        })

        return pd.DataFrame(facts)

    def _extract_statistical_facts(self, long_df: pd.DataFrame) -> pd.DataFrame:
        """統計的な事実を抽出"""
        facts = []

        total_staff = long_df['staff'].nunique()
        total_days = long_df['ds'].dt.date.nunique()

        if total_days > 0:
            daily_staff_counts = long_df[long_df['parsed_slots_count'] > 0].groupby(
                long_df['ds'].dt.date
            )['staff'].nunique()

            avg_daily_staff = daily_staff_counts.mean()

            facts.append({
                "スタッフ": "全体",
                "事実タイプ": "基本統計",
                "詳細": f"平均{avg_daily_staff:.1f}人/日（総勢{total_staff}人）",
                "平均日次スタッフ数": round(avg_daily_staff, 2),
                "総スタッフ数": total_staff,
                "分析期間日数": total_days,
                "確信度": 1.0,
            })

        for staff in long_df['staff'].unique():
            staff_df = long_df[long_df['staff'] == staff]
            work_days = staff_df[staff_df['parsed_slots_count'] > 0]['ds'].dt.date.nunique()

            if total_days > 0 and work_days > 0:
                work_ratio = work_days / total_days
                # 修正: 動的スロット設定対応
                avg_hours_per_day = safe_slot_calculation(
                    staff_df['parsed_slots_count'], 
                    self.slot_minutes, 
                    "sum", 
                    "extract_all_facts"
                ) / work_days

                if work_ratio < 0.2:
                    facts.append({
                        "スタッフ": staff,
                        "事実タイプ": "低頻度勤務",
                        "詳細": f"勤務率{work_ratio:.1%} ({work_days}/{total_days}日)",
                        "勤務日数": work_days,
                        "勤務率": round(work_ratio, 3),
                        "確信度": min(1.0, total_days / 20),
                    })
                elif work_ratio > 0.8:
                    facts.append({
                        "スタッフ": staff,
                        "事実タイプ": "高頻度勤務",
                        "詳細": f"勤務率{work_ratio:.1%} ({work_days}/{total_days}日)",
                        "勤務日数": work_days,
                        "勤務率": round(work_ratio, 3),
                        "確信度": min(1.0, total_days / 20),
                    })

                if avg_hours_per_day < 4:
                    facts.append({
                        "スタッフ": staff,
                        "事実タイプ": "短時間勤務",
                        "詳細": f"平均{avg_hours_per_day:.1f}時間/日",
                        "平均勤務時間": round(avg_hours_per_day, 2),
                        "確信度": min(1.0, work_days / 10),
                    })
                elif avg_hours_per_day > 10:
                    facts.append({
                        "スタッフ": staff,
                        "事実タイプ": "長時間勤務",
                        "詳細": f"平均{avg_hours_per_day:.1f}時間/日",
                        "平均勤務時間": round(avg_hours_per_day, 2),
                        "確信度": min(1.0, work_days / 10),
                    })

        return pd.DataFrame(facts)


def create_integrated_analysis(long_df: pd.DataFrame) -> Dict[str, Any]:
    """事実と暗黙知の統合分析"""

    blueprint_data = create_blueprint_list(long_df)

    fact_extractor = FactExtractor()
    facts_dict = fact_extractor.extract_all_facts(long_df)

    all_facts = []
    for fact_type, fact_df in facts_dict.items():
        if not fact_df.empty:
            fact_df['カテゴリー'] = fact_type
            all_facts.append(fact_df)

    combined_facts_df = pd.concat(all_facts, ignore_index=True) if all_facts else pd.DataFrame()

    connections = []
    if not combined_facts_df.empty and 'rules_df' in blueprint_data and not blueprint_data['rules_df'].empty:
        for _, fact in combined_facts_df.iterrows():
            staff_in_fact = fact.get('スタッフ', '')
            related_rules = blueprint_data['rules_df'][
                blueprint_data['rules_df']['発見された法則'].str.contains(staff_in_fact, na=False)
            ]

            for _, rule in related_rules.iterrows():
                connections.append({
                    "事実": fact['詳細'],
                    "関連ルール": rule['発見された法則'],
                    "関連性": "スタッフ名による関連",
                })

    result = blueprint_data.copy()
    result['facts_df'] = combined_facts_df
    result['facts_by_category'] = facts_dict
    result['fact_rule_connections'] = pd.DataFrame(connections)

    return result


def create_blueprint_list(long_df: pd.DataFrame) -> dict:
    """Return discovered rules and scoring analysis as a single dictionary."""
    result = _original_create_blueprint_list(long_df)

    try:
        fact_extractor = FactExtractor()
        facts_dict = fact_extractor.extract_all_facts(long_df)

        all_facts = []
        for fact_type, fact_df in facts_dict.items():
            if not fact_df.empty:
                fact_df['カテゴリー'] = fact_type
                all_facts.append(fact_df)

        combined_facts_df = pd.concat(all_facts, ignore_index=True) if all_facts else pd.DataFrame()

        result['facts_df'] = combined_facts_df
        result['facts_by_category'] = facts_dict
    except Exception as e:  # noqa: BLE001
        log.warning(f"事実抽出中にエラーが発生しました: {e}")
        result['facts_df'] = pd.DataFrame()
        result['facts_by_category'] = {}

    return result
