from __future__ import annotations

import logging
from collections import defaultdict
from itertools import combinations

import numpy as np
import pandas as pd

# --- analysis thresholds ---
SYNERGY_HIGH_THRESHOLD = 1.5
SYNERGY_LOW_THRESHOLD = 0.3
VETERAN_RATIO_THRESHOLD = 0.7
ROLE_RATIO_THRESHOLD = 0.4
MONTH_END_RATIO_THRESHOLD = 1.2
WEEKEND_RATIO_THRESHOLD = 0.7
EARLY_MONTH_RATIO_THRESHOLD = 0.1
ROLE_COMBO_RATIO_THRESHOLD = 0.1
NEW_STAFF_ONLY_RATIO_THRESHOLD = 0.01

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
    threshold = time_staff_counts['avg_staff'].quantile(0.75)
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


def create_blueprint_list(long_df: pd.DataFrame) -> dict:
    """シフトデータから深層的な法則を抽出し、作成者の暗黙知を可視化する"""
    if long_df.empty:
        return {"error": "分析対象の勤務データがありません。"}

    log.info("ブループリント分析を開始します...")

    # データ準備
    long_df = long_df.copy()
    long_df['date'] = pd.to_datetime(long_df['ds']).dt.date
    long_df['is_night'] = long_df['code'].astype(str).str.contains("夜", na=False)

    # 全カテゴリーの法則を抽出
    all_rules = []

    try:
        # 1. スキル相性分析
        log.info("スキル相性分析を実行中...")
        synergy_rules = _analyze_skill_synergy(long_df)
        all_rules.extend(synergy_rules)
        log.info(f"スキル相性: {len(synergy_rules)}個のルールを発見")

        # 2. 負荷分散戦略
        log.info("負荷分散戦略分析を実行中...")
        workload_rules = _analyze_workload_distribution(long_df)
        all_rules.extend(workload_rules)
        log.info(f"負荷分散: {len(workload_rules)}個のルールを発見")

        # 3. 個人配慮パターン
        log.info("個人配慮パターン分析を実行中...")
        personal_rules = _analyze_personal_consideration(long_df)
        all_rules.extend(personal_rules)
        log.info(f"個人配慮: {len(personal_rules)}個のルールを発見")

        # 4. ローテーション戦略
        log.info("ローテーション戦略分析を実行中...")
        rotation_rules = _analyze_rotation_strategy(long_df)
        all_rules.extend(rotation_rules)
        log.info(f"ローテーション: {len(rotation_rules)}個のルールを発見")

        # 5. リスク回避ルール
        log.info("リスク回避ルール分析を実行中...")
        risk_rules = _analyze_risk_mitigation(long_df)
        all_rules.extend(risk_rules)
        log.info(f"リスク回避: {len(risk_rules)}個のルールを発見")

        # 6. 時系列パターン
        log.info("時系列パターン分析を実行中...")
        temporal_rules = _analyze_temporal_context(long_df)
        all_rules.extend(temporal_rules)
        log.info(f"時系列: {len(temporal_rules)}個のルールを発見")

    except Exception as e:
        log.error(f"分析中にエラーが発生しました: {e}", exc_info=True)
        return {"error": f"分析中にエラーが発生しました: {str(e)}"}

    if not all_rules:
        return {
            "summary": "分析可能な法則が見つかりませんでした。データ量が不足している可能性があります。",
            "rules_df": pd.DataFrame(),
            "hidden_gems": []
        }

    # 法則を強度順にソート
    rules_df = pd.DataFrame(all_rules).sort_values("法則の強度", ascending=False).reset_index(drop=True)

    # 総合的な洞察サマリーを生成
    summary_text = _generate_deep_insights_summary(rules_df)

    # 意外な発見を抽出
    hidden_gems = _extract_surprising_insights(rules_df)

    log.info(f"分析完了: 合計{len(rules_df)}個のルールを発見")

    return {
        "summary": summary_text,
        "rules_df": rules_df,
        "hidden_gems": hidden_gems
    }
