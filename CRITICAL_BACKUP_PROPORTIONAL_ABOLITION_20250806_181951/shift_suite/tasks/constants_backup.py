# shift_suite/tasks/constants.py
"""
プロジェクト全体で使用する共通の定数を定義します。
"""

# ヒートマップや各種集計で使用される集計列のリスト
SUMMARY5 = ["need", "upper", "staff", "lack", "excess"]

# 他にも共通で使いたい定数があればここに追加できます。
# 例:
# DEFAULT_SLOT_MINUTES = 30
# NIGHT_START_TIME = dt.time(22, 0)
# NIGHT_END_TIME = dt.time(5, 59)

# スロット時間の定義
DEFAULT_SLOT_MINUTES = 30
SLOT_HOURS = DEFAULT_SLOT_MINUTES / 60.0  # スロットを時間に変換する係数

# 時間帯定義の統一
import datetime as dt
NIGHT_START_TIME = dt.time(22, 0)  # 夜勤開始時刻 22:00
NIGHT_END_TIME = dt.time(5, 59)    # 夜勤終了時刻 05:59
NIGHT_START_HOUR = 22              # 夜勤開始時（時のみ）
NIGHT_END_HOUR = 6                 # 夜勤終了時（時のみ）
EARLY_MORNING_THRESHOLD = dt.time(6, 0)  # 早朝判定基準 06:00

# 夜勤判定関数
def is_night_shift_time(time_obj):
    """時刻が夜勤時間帯かどうか判定"""
    if isinstance(time_obj, int):
        # 時（int）で判定
        return time_obj >= NIGHT_START_HOUR or time_obj < NIGHT_END_HOUR
    elif hasattr(time_obj, 'hour'):
        # datetime.time または datetime.datetime で判定
        hour = time_obj.hour
        return hour >= NIGHT_START_HOUR or hour < NIGHT_END_HOUR
    else:
        return False

# 賃金体系の統一
WAGE_RATES = {
    "regular_staff": 1500,           # 正規職員時給（円）
    "temporary_staff": 2200,         # 派遣職員時給（円）
    "average_hourly_wage": 1300,     # 平均時給（円）
    "night_differential": 1.25,      # 夜勤手当倍率（25%増）
    "overtime_multiplier": 1.25,     # 残業代倍率（25%増）
    "weekend_differential": 1.1      # 休日手当倍率（10%増）
}

# コスト計算パラメータ
COST_PARAMETERS = {
    "recruit_cost_per_hire": 200_000,    # 採用コスト（円）
    "hiring_cost_once": 180_000,         # 一時的採用コスト（円）
    "penalty_per_shortage_hour": 4_000,  # 不足時間あたりペナルティ（円）
    "monthly_hours_fte": 160             # 月間労働時間（FTE）
}

# 統計的閾値の標準化
STATISTICAL_THRESHOLDS = {
    "confidence_level": 0.95,            # 統計的信頼水準（95%）
    "significance_alpha": 0.05,          # 有意水準（5%）
    "correlation_threshold": 0.7,        # 相関分析閾値（70%）
    "synergy_high_threshold": 1.5,       # 高シナジー検出閾値
    "synergy_low_threshold": 0.3,        # 低シナジー/競合検出閾値
    "veteran_ratio_threshold": 0.7,      # ベテラン優先閾値（70%）
    "role_ratio_threshold": 0.4,         # 役割配分閾値（40%）
    "month_end_ratio_threshold": 1.2,    # 月末人員倍率（1.2倍）
    "weekend_ratio_threshold": 0.7,      # 週末人員比率（70%）
    "early_month_ratio_threshold": 0.1,  # 月初回避閾値（10%）
    "min_sample_size": 10,               # 最小サンプルサイズ
    "significant_deviation": 2.0,        # 有意な偏差倍率（2σ）
    "high_confidence_threshold": 0.8,    # 高信頼度判定閾値（80%）
    "code_restriction_threshold": 0.5,   # コード制限判定閾値（50%）
    "quantile_95": 0.95,                 # 95%分位数
    "synergy_detection_high": 2.0,       # シナジー検出高閾値（2倍）
    "synergy_detection_low": 0.5,        # シナジー検出低閾値（0.5倍）
    "role_combo_ratio_threshold": 0.1,   # 役割組み合わせ比率閾値（10%）
    "new_staff_only_ratio_threshold": 0.01,  # 新人のみ配置比率閾値（1%）
    "quantile_75": 0.75,                 # 75%分位数
    "quantile_25": 0.25,                 # 25%分位数
    "appearance_expectation": 0.8,       # 出現期待値（80%）
    "low_appearance_threshold": 0.2,     # 低出現閾値（20%）
    "high_frequency_threshold": 0.7,     # 高頻度閾値（70%）
    "pair_ratio_threshold": 0.5,         # ペア比率閾値（50%）
    "low_work_ratio": 0.2,               # 低勤務比率（20%）
    "high_work_ratio": 0.8,              # 高勤務比率（80%）
    "negative_correlation_threshold": -0.5  # 負の相関閾値（-0.5）
}

# 疲労度・勤務評価パラメータ
FATIGUE_PARAMETERS = {
    "min_rest_hours": 11,                # 最小休憩時間（法的要件）
    "consecutive_3_days_weight": 0.6,    # 3連勤重み
    "consecutive_4_days_weight": 0.3,    # 4連勤重み
    "consecutive_5_days_weight": 0.1,    # 5連勤重み
    "night_shift_threshold": 0.3,        # 夜勤比率閾値（30%）
    "early_morning_threshold": 0.3,      # 早朝勤務比率閾値（30%）
    "fatigue_alert_threshold": 0.8       # 疲労アラート閾値（80%）
}

# チームダイナミクス分析パラメータ
TEAM_DYNAMICS_PARAMETERS = {
    # 相性分析閾値
    "compatibility_threshold_good": 0.7,     # 相性良好の閾値
    "compatibility_threshold_excellent": 0.9, # 相性優秀の閾値
    "compatibility_threshold_risky": 0.3,    # 相性問題の閾値
    "compatibility_threshold_acceptable": 0.4, # 相性許容の閾値
    "compatibility_threshold_decent": 0.6,   # 相性適切の閾値
    "compatibility_threshold_high": 0.8,     # 相性高の閾値
    
    # 緊急対応能力閾値
    "emergency_score_threshold": 0.6,        # 緊急対応基本閾値
    "emergency_ready_threshold": 0.8,        # 緊急対応準備完了閾値
    
    # 重み係数
    "adaptation_weight": 0.3,                # 適応性重み
    "consecutive_tolerance_weight": 0.4,     # 連続勤務耐性重み
    "peak_performance_weight": 0.3,          # ピーク時パフォーマンス重み
    "frequency_weight": 0.3,                 # 頻度重み
    "pattern_weight": 0.4,                   # パターン重み
    "performance_weight": 0.3,               # パフォーマンス重み
    
    # 学習・成長パラメータ
    "learning_default_speed": 0.5,           # デフォルト学習速度
    "mentoring_capacity_default": 0.5,       # デフォルト指導能力
    "mentoring_capacity_low": 0.1,           # 低指導能力
    "slope_normalization_factor": 2.0,       # 傾き正規化係数
    
    # その他閾値
    "overlap_ratio_high": 0.7,               # 高重複比率
    "overlap_ratio_low": 0.3,                # 低重複比率
    "peak_performance_default": 0.5,         # デフォルトピークパフォーマンス
    "combined_score_high": 0.8,              # 高総合スコア
    "overall_resilience_high": 0.8,          # 高総合レジリエンス
    
    # 新規追加パラメータ
    "performance_default_score": 0.7,        # デフォルトパフォーマンススコア
    "impact_normalization_days": 20,         # 影響度正規化日数
    "experience_newcomer_days": 20,          # 新人判定日数
    "experience_newcomer_span": 60,          # 新人判定期間（日）
    "experience_midlevel_days": 50,          # 中堅判定日数
    "experience_midlevel_span": 180,         # 中堅判定期間（日）
    "skill_growth_min_frequency": 2,         # スキル成長最小出現頻度
    "max_growth_areas": 3,                   # 最大成長領域数
    "mentoring_diversity_factor": 10,        # 指導能力多様性係数
    "max_mentors_per_person": 2,             # 一人あたり最大メンター数
    "flexibility_code_factor": 10,           # 柔軟性コード係数
    "flexibility_variance_weight": 2,        # 柔軟性分散重み
    "cross_training_normalization_factor": 15,  # クロストレーニング正規化係数
    "stress_consecutive_days_factor": 7,     # ストレス連続日数係数
    "emergency_availability_factor": 2,      # 緊急対応可能性係数
    "response_time_instant_threshold": 0.8,  # 即座対応閾値
    "response_time_quick_threshold": 0.6,    # 短時間対応閾値  
    "response_time_adjusted_threshold": 0.4, # 調整後対応閾値
    "month_end_threshold": 21,               # 月末判定日
    "stress_high_threshold": 0.8,            # 高ストレス耐性閾値
    "stress_medium_threshold": 0.6,          # 中ストレス耐性閾値
    "stress_low_threshold": 0.4,             # 低ストレス耐性閾値
    "consecutive_tolerance_factor": 7,       # 連続勤務耐性係数
}

# 制約分析パラメータ
CONSTRAINT_ANALYSIS_PARAMETERS = {
    # 観測・分析期間
    "min_observation_weeks": 8,              # 最小観測期間（週）
    "confidence_threshold": 0.7,             # 信頼度閾値
    
    # 変動判定閾値
    "low_variation_threshold": 0.5,          # 低変動閾値
    "low_variation_evidence_weight": 0.4,    # 低変動証拠重み
    "no_exceed_evidence_weight": 0.3,        # 未超過証拠重み
    "high_concentration_weight": 0.2,        # 高集中度重み
    "consistency_bonus_weight": 0.1,         # 一貫性ボーナス重み
    
    # 判定閾値
    "near_max_ratio_threshold": 0.6,         # 最大値近辺比率閾値
    "below_min_ratio_threshold": 0.1,        # 最小値以下比率閾値
    "mode_concentration_threshold": 0.7,      # 最頻値集中度閾値
    
    # 追加分析パラメータ
    "skewness_threshold": 0.5,               # 歪度閾値（右寄り分布判定）
    "trend_slope_threshold": 0.01,           # トレンド傾き閾値（上昇判定）
    "deviation_balance_threshold": 0.3,      # 両側分散バランス閾値
    "range_variation_threshold": 0.3,        # 範囲変動閾値（30%変動）
    "flexibility_std_threshold": 1.0,        # 柔軟性標準偏差閾値
    "max_concentration_threshold": 0.5,      # 最大集中度閾値（50%）
    "random_pattern_tolerance": 0.3          # ランダムパターン許容範囲（30%）
}

# 統計レポート・分析パラメータ  
BUILD_STATS_PARAMETERS = {
    "night_shift_ratio_threshold": 0.5,      # 夜勤比率判定閾値
    "consecutive_shortage_months": 2,         # 連続不足判定月数
}
