"""
シフト作成者の暗黙知を深く分析する拡張ブループリント分析エンジン

このモジュールは、シフト作成者の思考プロセスと判断基準を逆算・可視化することを目的とし、
以下のような「作成ルール」を統計的・論理的に発見・可視化します：

1. 個人レベルのルール:
   - 週○日勤務制限 (例: ○○さんは週3日まで勤務)
   - 曜日制限 (例: ○○さんは火曜、水曜、日曜しか勤務していない)
   - 勤務区分制限 (例: ○○さんはこの勤務区分記号しか対応していない)
   - 時間帯制限 (例: ○○さんは午前中のみ、夜勤なし)

2. ペア・グループレベルのルール:
   - 組み合わせ禁止 (例: ○○さんと△さんは組み合わせて勤務していない)
   - 組み合わせ優遇 (例: ○○さんと△さんは頻繁に組まれる)

3. セグメント別ルール:
   - 施設全体のルール
   - 各職種セグメント内のルール
   - 各勤務区分セグメント内のルール

4. 統計的暗黙知:
   - 期待値からの有意な乖離パターン
   - 時系列での行動変化パターン
   - 例外的状況での特別ルール

Author: Claude Code Assistant
Created: 2025-01-14
"""

from __future__ import annotations

import logging
from collections import defaultdict, Counter
from itertools import combinations
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats
from .constants import STATISTICAL_THRESHOLDS

log = logging.getLogger(__name__)

# 統計的分析の閾値設定
STATISTICAL_CONFIDENCE = STATISTICAL_THRESHOLDS["confidence_level"]  # 95%信頼区間
MIN_SAMPLE_SIZE = STATISTICAL_THRESHOLDS["min_sample_size"]          # 最小サンプルサイズ
SIGNIFICANT_DEVIATION = STATISTICAL_THRESHOLDS["significant_deviation"]    # 標準偏差の何倍で有意とするか


@dataclass
class ShiftRule:
    """発見されたシフト作成ルールを表すクラス"""
    staff_name: str
    rule_type: str
    rule_description: str
    confidence_score: float
    statistical_evidence: Dict[str, Any]
    segment: str = "全体"  # 全体、職種別、勤務区分別
    

class EnhancedBlueprintAnalyzer:
    """シフト作成者の暗黙知を深く分析する拡張ブループリント分析エンジン"""
    
    def __init__(self):
        self.weekday_names = ['月', '火', '水', '木', '金', '土', '日']
        self.discovered_rules: List[ShiftRule] = []
        
    def analyze_shift_creation_blueprint(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """
        シフト作成者の暗黙知を包括的に分析
        
        Args:
            long_df: 勤務データ (ds, staff, role, code, parsed_slots_count等を含む)
            
        Returns:
            発見されたルールと分析結果の辞書
        """
        if long_df.empty:
            return {"rules": [], "segments": {}, "statistical_summary": {}}
            
        log.info("🔍 シフト作成者の暗黙知分析を開始します...")
        
        # 1. 個人レベルのルール発見
        personal_rules = self._discover_personal_rules(long_df)
        
        # 2. ペア・グループレベルのルール発見  
        pair_rules = self._discover_pair_rules(long_df)
        
        # 3. セグメント別ルール発見
        segment_rules = self._discover_segment_rules(long_df)
        
        # 4. 統計的暗黙知の抽出
        statistical_insights = self._extract_statistical_insights(long_df)
        
        # 5. 結果の統合と信頼度計算
        all_rules = personal_rules + pair_rules + segment_rules
        validated_rules = self._validate_and_score_rules(all_rules, long_df)
        
        return {
            "rules": validated_rules,
            "segments": self._analyze_by_segments(long_df),
            "statistical_summary": statistical_insights,
            "rule_count": len(validated_rules),
            "high_confidence_rules": [r for r in validated_rules if r.confidence_score >= STATISTICAL_THRESHOLDS["high_confidence_threshold"]]
        }
    
    def _discover_personal_rules(self, long_df: pd.DataFrame) -> List[ShiftRule]:
        """個人レベルのルール発見"""
        personal_rules = []
        
        # 週○日勤務制限の発見
        personal_rules.extend(self._discover_weekly_limit_rules(long_df))
        
        # 曜日制限の発見
        personal_rules.extend(self._discover_weekday_restriction_rules(long_df))
        
        # 勤務区分制限の発見
        personal_rules.extend(self._discover_code_restriction_rules(long_df))
        
        # 時間帯制限の発見  
        personal_rules.extend(self._discover_time_restriction_rules(long_df))
        
        return personal_rules
    
    def _discover_weekly_limit_rules(self, long_df: pd.DataFrame) -> List[ShiftRule]:
        """週○日勤務制限ルールの発見（高度な制約性質判別機能付き）"""
        rules = []
        
        # 🔍 高度な制約性質判別エンジンを使用
        try:
            from .constraint_nature_analyzer import analyze_constraint_nature
            constraint_results = analyze_constraint_nature(long_df)
            weekly_constraints = constraint_results.get('weekly_constraints', [])
            
            for analysis in weekly_constraints:
                if analysis.confidence_score >= STATISTICAL_THRESHOLDS["correlation_threshold"]:  # 70%以上の信頼度
                    # 制約の性質に応じたルール説明を生成
                    nature_desc = self._generate_constraint_description(analysis)
                    
                    rule = ShiftRule(
                        staff_name=analysis.staff_name,
                        rule_type=f"週勤務日数{analysis.constraint_type.value}",
                        rule_description=nature_desc,
                        confidence_score=analysis.confidence_score,
                        statistical_evidence={
                            "constraint_nature": analysis.constraint_type.value,
                            "threshold_value": analysis.threshold_value,
                            "detailed_evidence": analysis.evidence,
                            "recommendations": analysis.recommendations
                        },
                        segment="全体"
                    )
                    rules.append(rule)
                    
        except ImportError:
            log.warning("高度制約判別エンジンが利用できません。基本分析にフォールバック")
            # フォールバック：従来の簡易分析
            rules = self._discover_weekly_limit_rules_fallback(long_df)
        
        return rules
    
    def _generate_constraint_description(self, analysis) -> str:
        """制約分析結果から適切な説明文を生成"""
        staff = analysis.staff_name
        threshold = int(analysis.threshold_value)
        constraint_type = analysis.constraint_type
        confidence = analysis.confidence_score
        
        descriptions = {
            "上限制約": f"週{threshold}日が上限制約（超過不可・信頼度{confidence:.0%}）",
            "下限希望": f"週{threshold}日が下限希望（最低確保・信頼度{confidence:.0%}）", 
            "固定希望": f"週{threshold}日が固定希望（最適日数・信頼度{confidence:.0%}）",
            "柔軟パターン": f"柔軟な勤務パターン（平均{threshold:.1f}日・信頼度{confidence:.0%}）",
            "季節制約": f"季節的制約あり（平均{threshold:.1f}日・信頼度{confidence:.0%}）"
        }
        
        return descriptions.get(constraint_type.value, f"週{threshold}日勤務パターン（信頼度{confidence:.0%}）")
    
    def _discover_weekly_limit_rules_fallback(self, long_df: pd.DataFrame) -> List[ShiftRule]:
        """従来の簡易分析（フォールバック用）"""
        rules = []
        
        # 週ごとの勤務日数を計算
        long_df['week'] = long_df['ds'].dt.isocalendar().week
        long_df['year'] = long_df['ds'].dt.year
        
        working_df = long_df[long_df['parsed_slots_count'] > 0]
        
        for staff in working_df['staff'].unique():
            staff_df = working_df[working_df['staff'] == staff]
            
            # 週ごとの勤務日数集計
            weekly_days = staff_df.groupby(['year', 'week'])['ds'].nunique()
            
            if len(weekly_days) < MIN_SAMPLE_SIZE:
                continue
                
            # 統計的分析
            mean_days = weekly_days.mean()
            std_days = weekly_days.std()
            max_days = weekly_days.max()
            
            # 上限値の特定（平均 + 1σ以下で95%が収まる）
            upper_limit = mean_days + std_days
            consistent_limit = weekly_days.quantile(STATISTICAL_THRESHOLDS["quantile_95"])
            
            # ルールとして有効か判定
            if max_days <= consistent_limit and std_days < 1.0:  # 一貫性がある
                confidence = 1.0 - (std_days / mean_days) if mean_days > 0 else 0.0
                
                if confidence >= STATISTICAL_THRESHOLDS["correlation_threshold"]:  # 70%以上の信頼度
                    rule = ShiftRule(
                        staff_name=staff,
                        rule_type="週勤務日数制限（基本分析）",
                        rule_description=f"週{int(consistent_limit)}日以下の勤務に制限（詳細分析推奨）",
                        confidence_score=confidence,
                        statistical_evidence={
                            "mean_weekly_days": mean_days,
                            "max_weekly_days": max_days,
                            "consistency_limit": consistent_limit,
                            "standard_deviation": std_days,
                            "sample_weeks": len(weekly_days),
                            "note": "高度分析エンジン未使用"
                        }
                    )
                    rules.append(rule)
        
        return rules
    
    def _discover_weekday_restriction_rules(self, long_df: pd.DataFrame) -> List[ShiftRule]:
        """曜日制限ルールの発見"""
        rules = []
        
        working_df = long_df[long_df['parsed_slots_count'] > 0]
        
        for staff in working_df['staff'].unique():
            staff_df = working_df[working_df['staff'] == staff]
            
            if len(staff_df) < MIN_SAMPLE_SIZE:
                continue
                
            # 曜日別勤務回数
            weekday_counts = staff_df.groupby(staff_df['ds'].dt.dayofweek).size()
            total_possible_days = staff_df['ds'].dt.date.nunique()
            
            # 勤務している曜日を特定
            working_weekdays = weekday_counts[weekday_counts > 0].index.tolist()
            
            # 制限ルールの判定
            if len(working_weekdays) < 7:  # 全曜日勤務していない
                working_weekday_names = [self.weekday_names[d] for d in working_weekdays]
                
                # 統計的検定: 勤務曜日が有意に偏っているか
                expected_freq = total_possible_days / 7
                chi2_stat, p_value = stats.chisquare(weekday_counts.reindex(range(7), fill_value=0))
                
                if p_value < STATISTICAL_THRESHOLDS["significance_alpha"]:  # 有意な偏り
                    confidence = 1.0 - p_value
                    
                    rule = ShiftRule(
                        staff_name=staff,
                        rule_type="曜日制限勤務", 
                        rule_description=f"{', '.join(working_weekday_names)}のみ勤務",
                        confidence_score=confidence,
                        statistical_evidence={
                            "working_weekdays": working_weekdays,
                            "weekday_counts": weekday_counts.to_dict(),
                            "chi2_statistic": chi2_stat,
                            "p_value": p_value,
                            "total_days": total_possible_days
                        }
                    )
                    rules.append(rule)
        
        return rules
    
    def _discover_code_restriction_rules(self, long_df: pd.DataFrame) -> List[ShiftRule]:
        """勤務区分制限ルールの発見"""
        rules = []
        
        working_df = long_df[(long_df['parsed_slots_count'] > 0) & (long_df['code'] != '')]
        all_codes = sorted(working_df['code'].unique())
        
        for staff in working_df['staff'].unique():
            staff_df = working_df[working_df['staff'] == staff]
            
            if len(staff_df) < MIN_SAMPLE_SIZE:
                continue
                
            used_codes = sorted(staff_df['code'].unique())
            
            # 制限ルールの判定（全コードの50%未満しか使用していない）
            if len(used_codes) < len(all_codes) * STATISTICAL_THRESHOLDS["code_restriction_threshold"] and len(used_codes) >= 1:
                
                # 統計的検定: コード使用が有意に制限されているか
                code_usage_ratio = len(used_codes) / len(all_codes)
                confidence = 1.0 - code_usage_ratio  # 制限が強いほど信頼度が高い
                
                rule = ShiftRule(
                    staff_name=staff,
                    rule_type="勤務区分制限",
                    rule_description=f"使用コード: {', '.join(used_codes[:3])}{'...' if len(used_codes) > 3 else ''}のみ",
                    confidence_score=confidence,
                    statistical_evidence={
                        "used_codes": used_codes,
                        "total_available_codes": len(all_codes),
                        "usage_ratio": code_usage_ratio,
                        "total_shifts": len(staff_df)
                    }
                )
                rules.append(rule)
        
        return rules
    
    def _discover_time_restriction_rules(self, long_df: pd.DataFrame) -> List[ShiftRule]:
        """時間帯制限ルールの発見"""
        rules = []
        
        # TODO: 時刻情報がある場合の時間帯制限分析
        # 現在のデータ構造では時刻情報が限定的なため、将来の拡張として設計
        
        return rules
    
    def _discover_pair_rules(self, long_df: pd.DataFrame) -> List[ShiftRule]:
        """ペア・グループレベルのルール発見"""
        rules = []
        
        # 同日同時勤務の分析
        working_df = long_df[long_df['parsed_slots_count'] > 0]
        
        # 日付・勤務区分ごとのスタッフグループ
        daily_groups = working_df.groupby(['ds', 'code'])['staff'].apply(list).reset_index()
        
        # ペアの共起回数を計算
        pair_counts = defaultdict(int)
        total_shifts_per_staff = working_df.groupby('staff')['ds'].nunique()
        
        for _, row in daily_groups.iterrows():
            staff_list = row['staff']
            if len(staff_list) >= 2:
                for pair in combinations(sorted(set(staff_list)), 2):
                    pair_counts[pair] += 1
        
        # 統計的有意性の検定
        for (staff1, staff2), observed_count in pair_counts.items():
            if staff1 not in total_shifts_per_staff.index or staff2 not in total_shifts_per_staff.index:
                continue
                
            shifts1 = total_shifts_per_staff[staff1]
            shifts2 = total_shifts_per_staff[staff2]
            total_days = working_df['ds'].nunique()
            
            # 期待値計算（独立性を仮定）
            expected_count = (shifts1 * shifts2) / total_days
            
            if expected_count > 0:
                ratio = observed_count / expected_count
                
                # 統計的検定
                if observed_count >= MIN_SAMPLE_SIZE:
                    # ポアソン検定で有意性を確認
                    p_value = stats.poisson.sf(observed_count - 1, expected_count)
                    
                    if ratio >= STATISTICAL_THRESHOLDS["synergy_detection_high"] and p_value < STATISTICAL_THRESHOLDS["significance_alpha"]:  # 期待値の2倍以上で有意
                        rule = ShiftRule(
                            staff_name=f"{staff1} & {staff2}",
                            rule_type="組み合わせ優遇",
                            rule_description=f"頻繁にペア勤務（期待値の{ratio:.1f}倍）",
                            confidence_score=1.0 - p_value,
                            statistical_evidence={
                                "observed_count": observed_count,
                                "expected_count": expected_count,
                                "ratio": ratio,
                                "p_value": p_value,
                                "staff1_shifts": shifts1,
                                "staff2_shifts": shifts2
                            }
                        )
                        rules.append(rule)
                    
                    elif ratio <= STATISTICAL_THRESHOLDS["synergy_detection_low"] and observed_count == 0:  # 期待値の半分以下で共起なし
                        rule = ShiftRule(
                            staff_name=f"{staff1} & {staff2}",
                            rule_type="組み合わせ回避",
                            rule_description="ペア勤務を避けている（共起なし）",
                            confidence_score=min(0.9, expected_count / 10),  # 期待値が高いほど信頼度UP
                            statistical_evidence={
                                "observed_count": 0,
                                "expected_count": expected_count,
                                "ratio": 0.0,
                                "staff1_shifts": shifts1,
                                "staff2_shifts": shifts2
                            }
                        )
                        rules.append(rule)
        
        return rules
    
    def _discover_segment_rules(self, long_df: pd.DataFrame) -> List[ShiftRule]:
        """セグメント別ルール発見"""
        rules = []
        
        # 職種別セグメント分析
        if 'role' in long_df.columns:
            for role in long_df['role'].unique():
                role_df = long_df[long_df['role'] == role]
                role_rules = self._discover_personal_rules(role_df)
                
                # セグメント情報を追加
                for rule in role_rules:
                    rule.segment = f"職種:{role}"
                    rules.append(rule)
        
        # 勤務区分別セグメント分析
        if 'code' in long_df.columns:
            for code in long_df[long_df['code'] != '']['code'].unique():
                code_df = long_df[long_df['code'] == code]
                code_rules = self._discover_personal_rules(code_df)
                
                # セグメント情報を追加
                for rule in code_rules:
                    rule.segment = f"勤務区分:{code}"
                    rules.append(rule)
        
        return rules
    
    def _extract_statistical_insights(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """統計的暗黙知の抽出"""
        insights = {}
        
        working_df = long_df[long_df['parsed_slots_count'] > 0]
        
        # 時系列パターン分析
        insights['temporal_patterns'] = self._analyze_temporal_patterns(working_df)
        
        # 全体的な傾向分析
        insights['overall_trends'] = self._analyze_overall_trends(working_df)
        
        return insights
    
    def _analyze_temporal_patterns(self, working_df: pd.DataFrame) -> Dict[str, Any]:
        """時系列パターンの分析"""
        patterns = {}
        
        # 月内期間での勤務パターン
        working_df['month_period'] = working_df['ds'].dt.day.apply(
            lambda d: '月初' if d <= 10 else '月中' if d <= 20 else '月末'
        )
        
        period_counts = working_df.groupby(['staff', 'month_period']).size().unstack(fill_value=0)
        
        # 期間偏重の発見
        for staff in period_counts.index:
            staff_counts = period_counts.loc[staff]
            total = staff_counts.sum()
            
            if total >= MIN_SAMPLE_SIZE:
                max_period = staff_counts.idxmax()
                max_ratio = staff_counts.max() / total
                
                if max_ratio >= 0.6:  # 60%以上が特定期間に集中
                    patterns[staff] = {
                        'type': '月内期間偏重',
                        'pattern': f'{max_period}に集中（{max_ratio:.1%}）',
                        'confidence': max_ratio
                    }
        
        return patterns
    
    def _analyze_overall_trends(self, working_df: pd.DataFrame) -> Dict[str, Any]:
        """全体的な傾向分析"""
        trends = {}
        
        # スタッフ別の勤務頻度分析
        staff_frequency = working_df['staff'].value_counts()
        
        trends['staff_distribution'] = {
            'most_frequent_staff': staff_frequency.index[0],
            'max_frequency': staff_frequency.iloc[0],
            'frequency_variance': staff_frequency.var(),
            'total_staff': len(staff_frequency)
        }
        
        # 曜日別の全体傾向
        weekday_distribution = working_df.groupby(working_df['ds'].dt.dayofweek).size()
        weekday_names = [self.weekday_names[i] for i in weekday_distribution.index]
        
        trends['weekday_preferences'] = {
            'distribution': dict(zip(weekday_names, weekday_distribution.values)),
            'most_common_weekday': self.weekday_names[weekday_distribution.idxmax()],
            'least_common_weekday': self.weekday_names[weekday_distribution.idxmin()]
        }
        
        return trends
    
    def _analyze_by_segments(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """セグメント別の詳細分析"""
        segments = {}
        
        # 職種別分析
        if 'role' in long_df.columns:
            segments['by_role'] = {}
            for role in long_df['role'].unique():
                role_df = long_df[long_df['role'] == role]
                working_role_df = role_df[role_df['parsed_slots_count'] > 0]
                
                segments['by_role'][role] = {
                    'staff_count': role_df['staff'].nunique(),
                    'total_shifts': len(working_role_df),
                    'avg_shifts_per_staff': len(working_role_df) / role_df['staff'].nunique() if role_df['staff'].nunique() > 0 else 0
                }
        
        # 勤務区分別分析
        if 'code' in long_df.columns:
            segments['by_code'] = {}
            for code in long_df[long_df['code'] != '']['code'].unique():
                code_df = long_df[long_df['code'] == code]
                
                segments['by_code'][code] = {
                    'staff_count': code_df['staff'].nunique(),
                    'total_shifts': len(code_df),
                    'avg_shifts_per_staff': len(code_df) / code_df['staff'].nunique() if code_df['staff'].nunique() > 0 else 0
                }
        
        return segments
    
    def _validate_and_score_rules(self, rules: List[ShiftRule], long_df: pd.DataFrame) -> List[ShiftRule]:
        """ルールの妥当性検証と信頼度スコア計算"""
        validated_rules = []
        
        for rule in rules:
            # 基本的な妥当性チェック
            if rule.confidence_score >= 0.5:  # 50%以上の信頼度
                # 統計的証拠の存在確認
                if rule.statistical_evidence:
                    validated_rules.append(rule)
        
        # 信頼度順でソート
        validated_rules.sort(key=lambda r: r.confidence_score, reverse=True)
        
        return validated_rules


def create_enhanced_blueprint_analysis(long_df: pd.DataFrame) -> Dict[str, Any]:
    """
    シフト作成者の暗黙知を深く分析するメイン関数
    
    Args:
        long_df: 勤務データ
        
    Returns:
        発見されたルールと分析結果
    """
    analyzer = EnhancedBlueprintAnalyzer()
    return analyzer.analyze_shift_creation_blueprint(long_df)