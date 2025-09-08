"""
リアルタイム洞察検出システム
分析実行中に自動的に深い洞察を検出し、レポートする
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import json
from datetime import datetime
import logging
from dataclasses import dataclass, asdict
from enum import Enum

# ログ設定
logger = logging.getLogger(__name__)


class InsightSeverity(Enum):
    """洞察の重要度レベル"""
    CRITICAL = "critical"  # 経営判断が必要
    HIGH = "high"  # 即対応推奨
    MEDIUM = "medium"  # 改善機会
    LOW = "low"  # 参考情報
    INFO = "info"  # 情報提供


class InsightCategory(Enum):
    """洞察のカテゴリ"""
    COST_WASTE = "cost_waste"  # コスト無駄
    RISK = "risk"  # リスク
    OPPORTUNITY = "opportunity"  # 改善機会
    ANOMALY = "anomaly"  # 異常値
    PATTERN = "pattern"  # パターン発見
    CONSTRAINT = "constraint"  # 制約問題
    FAIRNESS = "fairness"  # 公平性問題
    EFFICIENCY = "efficiency"  # 効率性問題


@dataclass
class Insight:
    """検出された洞察"""
    id: str
    timestamp: datetime
    category: InsightCategory
    severity: InsightSeverity
    title: str
    description: str
    data_evidence: Dict[str, Any]
    financial_impact: Optional[float]  # 万円/月
    affected_staff: Optional[List[str]]
    recommended_action: Optional[str]
    confidence_score: float  # 0-1
    
    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        result = asdict(self)
        result['category'] = self.category.value
        result['severity'] = self.severity.value
        result['timestamp'] = self.timestamp.isoformat()
        return result


class RealTimeInsightDetector:
    """リアルタイム洞察検出エンジン"""
    
    def __init__(self, threshold_config: Optional[Dict] = None):
        """
        Args:
            threshold_config: 検出閾値の設定
        """
        self.insights: List[Insight] = []
        self.threshold_config = threshold_config or self._default_thresholds()
        self.detection_rules = self._initialize_detection_rules()
        
    def _default_thresholds(self) -> Dict:
        """デフォルトの検出閾値"""
        return {
            'cost_waste_threshold': 10,  # 10万円/月以上を無駄と判定
            'workload_imbalance_ratio': 2.0,  # 2倍以上の差を不均衡と判定
            'fatigue_critical_hours': 200,  # 200時間/月以上を危険と判定
            'skill_concentration_ratio': 0.8,  # 80%以上の集中を問題と判定
            'time_slot_excess_ratio': 1.3,  # 130%以上を過剰配置と判定
            'absence_pattern_days': 3,  # 3日以上の連続欠勤をパターンと判定
            'minimum_guarantee_waste_ratio': 0.2,  # 20%以上を無駄と判定
        }
    
    def _initialize_detection_rules(self) -> Dict:
        """検出ルールの初期化"""
        return {
            'employment_constraint': self._detect_employment_constraint,
            'time_mismatch': self._detect_time_mismatch,
            'skill_bottleneck': self._detect_skill_bottleneck,
            'workload_imbalance': self._detect_workload_imbalance,
            'fatigue_risk': self._detect_fatigue_risk,
            'cost_anomaly': self._detect_cost_anomaly,
            'pattern_discovery': self._detect_hidden_patterns,
            'fairness_issue': self._detect_fairness_issues,
        }
    
    def analyze_shortage_data(self, 
                             shortage_data: pd.DataFrame,
                             intermediate_data: pd.DataFrame,
                             need_data: Optional[pd.DataFrame] = None) -> List[Insight]:
        """
        不足分析データから洞察を検出
        
        Args:
            shortage_data: 不足分析結果
            intermediate_data: 中間データ
            need_data: 需要データ
            
        Returns:
            検出された洞察のリスト
        """
        logger.info("リアルタイム洞察検出を開始")
        
        # 各検出ルールを実行
        for rule_name, rule_func in self.detection_rules.items():
            try:
                detected = rule_func(shortage_data, intermediate_data, need_data)
                if detected:
                    self.insights.extend(detected)
                    logger.info(f"{rule_name}: {len(detected)}個の洞察を検出")
            except Exception as e:
                logger.error(f"{rule_name}の実行中にエラー: {e}")
        
        # 重要度でソート
        self.insights.sort(key=lambda x: (
            ['critical', 'high', 'medium', 'low', 'info'].index(x.severity.value),
            -x.financial_impact if x.financial_impact else 0
        ))
        
        logger.info(f"合計 {len(self.insights)} 個の洞察を検出")
        return self.insights
    
    def _detect_employment_constraint(self, 
                                     shortage_df: pd.DataFrame,
                                     intermediate_df: pd.DataFrame,
                                     need_df: Optional[pd.DataFrame]) -> List[Insight]:
        """雇用契約制約による無駄を検出"""
        insights = []
        
        if 'employment' not in intermediate_df.columns:
            return insights
        
        # 雇用形態別の分析
        emp_stats = intermediate_df.groupby('employment').agg({
            'staff': 'nunique',
            'ds': 'count'
        }).rename(columns={'staff': 'staff_count', 'ds': 'total_slots'})
        
        # 最低保証時間の設定（仮定）
        min_guarantee = {
            '正社員': 160,
            'パート': 80,
            '契約社員': 120
        }
        
        for emp_type, min_hours in min_guarantee.items():
            if emp_type in emp_stats.index:
                actual_hours = emp_stats.loc[emp_type, 'total_slots'] * 0.5
                staff_count = emp_stats.loc[emp_type, 'staff_count']
                required_hours = staff_count * min_hours
                
                if actual_hours > required_hours * 1.2:  # 20%以上の超過
                    waste_hours = actual_hours - required_hours
                    waste_cost = waste_hours * 2000 / 10000  # 万円
                    
                    insight = Insight(
                        id=f"emp_constraint_{emp_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        timestamp=datetime.now(),
                        category=InsightCategory.CONSTRAINT,
                        severity=InsightSeverity.HIGH if waste_cost > 50 else InsightSeverity.MEDIUM,
                        title=f"{emp_type}の最低保証時間による過剰配置",
                        description=f"{emp_type}の最低保証時間制約により、月{waste_hours:.0f}時間（{waste_cost:.1f}万円）の過剰配置が発生しています。",
                        data_evidence={
                            'employment_type': emp_type,
                            'staff_count': int(staff_count),
                            'required_hours': required_hours,
                            'actual_hours': actual_hours,
                            'waste_hours': waste_hours
                        },
                        financial_impact=waste_cost,
                        affected_staff=None,
                        recommended_action=f"{emp_type}の比率を見直し、より柔軟な雇用形態へのシフトを検討してください。",
                        confidence_score=0.85
                    )
                    insights.append(insight)
        
        return insights
    
    def _detect_time_mismatch(self,
                             shortage_df: pd.DataFrame,
                             intermediate_df: pd.DataFrame,
                             need_df: Optional[pd.DataFrame]) -> List[Insight]:
        """時間帯ミスマッチを検出"""
        insights = []
        
        if 'slot' not in intermediate_df.columns:
            return insights
        
        # 時間帯別の集計
        slot_stats = intermediate_df.groupby('slot').size()
        
        # 朝・昼・夕の時間帯を定義（仮定）
        morning_slots = range(12, 20)  # 6:00-10:00
        afternoon_slots = range(28, 36)  # 14:00-18:00
        
        morning_count = slot_stats[slot_stats.index.isin(morning_slots)].sum()
        afternoon_count = slot_stats[slot_stats.index.isin(afternoon_slots)].sum()
        
        # 不均衡を検出
        if afternoon_count > morning_count * 1.5:
            excess_count = afternoon_count - morning_count
            excess_cost = excess_count * 0.5 * 2000 / 10000  # 万円
            
            insight = Insight(
                id=f"time_mismatch_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                timestamp=datetime.now(),
                category=InsightCategory.EFFICIENCY,
                severity=InsightSeverity.HIGH,
                title="朝の人員不足と午後の過剰配置",
                description=f"朝（6-10時）に比べて午後（14-18時）に{excess_count}スロット分の過剰配置があります。",
                data_evidence={
                    'morning_slots': int(morning_count),
                    'afternoon_slots': int(afternoon_count),
                    'excess_slots': int(excess_count)
                },
                financial_impact=excess_cost,
                affected_staff=None,
                recommended_action="シフトパターンを見直し、朝の時間帯への人員シフトを検討してください。",
                confidence_score=0.9
            )
            insights.append(insight)
        
        return insights
    
    def _detect_skill_bottleneck(self,
                                shortage_df: pd.DataFrame,
                                intermediate_df: pd.DataFrame,
                                need_df: Optional[pd.DataFrame]) -> List[Insight]:
        """スキルボトルネックを検出"""
        insights = []
        
        if 'role' not in intermediate_df.columns:
            return insights
        
        # 役割別の集計
        role_stats = intermediate_df.groupby('role').agg({
            'staff': lambda x: x.nunique() if 'staff' in intermediate_df.columns else 0,
            'ds': 'count'
        })
        
        # 特定役割への集中を検出
        total_slots = role_stats['ds'].sum()
        
        for role, row in role_stats.iterrows():
            concentration = row['ds'] / total_slots
            
            if concentration > self.threshold_config['skill_concentration_ratio']:
                insight = Insight(
                    id=f"skill_bottleneck_{role}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    timestamp=datetime.now(),
                    category=InsightCategory.RISK,
                    severity=InsightSeverity.HIGH,
                    title=f"{role}への過度な依存",
                    description=f"{role}が全体の{concentration*100:.0f}%を占めており、スキルボトルネックとなっています。",
                    data_evidence={
                        'role': role,
                        'concentration_ratio': concentration,
                        'total_slots': int(row['ds']),
                        'unique_staff': int(row['staff'])
                    },
                    financial_impact=None,
                    affected_staff=None,
                    recommended_action=f"{role}のスキルを持つスタッフを増やすか、クロストレーニングを実施してください。",
                    confidence_score=0.8
                )
                insights.append(insight)
        
        return insights
    
    def _detect_workload_imbalance(self,
                                  shortage_df: pd.DataFrame,
                                  intermediate_df: pd.DataFrame,
                                  need_df: Optional[pd.DataFrame]) -> List[Insight]:
        """作業負荷の不均衡を検出"""
        insights = []
        
        if 'staff' not in intermediate_df.columns:
            return insights
        
        # スタッフ別の負荷を計算
        staff_workload = intermediate_df.groupby('staff').size()
        
        # 統計値を計算
        mean_workload = staff_workload.mean()
        std_workload = staff_workload.std()
        
        # 極端な負荷を検出
        for staff, workload in staff_workload.items():
            if workload > mean_workload + 2 * std_workload:
                # 過負荷
                insight = Insight(
                    id=f"overload_{staff}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    timestamp=datetime.now(),
                    category=InsightCategory.RISK,
                    severity=InsightSeverity.CRITICAL,
                    title=f"{staff}の過負荷状態",
                    description=f"{staff}の勤務時間（{workload*0.5:.0f}時間）が平均の{workload/mean_workload:.1f}倍となっています。",
                    data_evidence={
                        'staff': staff,
                        'workload_hours': workload * 0.5,
                        'average_hours': mean_workload * 0.5,
                        'ratio': workload / mean_workload
                    },
                    financial_impact=None,
                    affected_staff=[staff],
                    recommended_action=f"{staff}の負荷を他のスタッフに分散させ、離職リスクを軽減してください。",
                    confidence_score=0.95
                )
                insights.append(insight)
            
            elif workload < mean_workload - 2 * std_workload and workload < mean_workload * 0.5:
                # 過少負荷
                underutilized_hours = (mean_workload - workload) * 0.5
                potential_savings = underutilized_hours * 2000 / 10000
                
                insight = Insight(
                    id=f"underload_{staff}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    timestamp=datetime.now(),
                    category=InsightCategory.OPPORTUNITY,
                    severity=InsightSeverity.MEDIUM,
                    title=f"{staff}の稼働率が低い",
                    description=f"{staff}の稼働率が平均の{workload/mean_workload*100:.0f}%で、活用余地があります。",
                    data_evidence={
                        'staff': staff,
                        'workload_hours': workload * 0.5,
                        'average_hours': mean_workload * 0.5,
                        'underutilized_hours': underutilized_hours
                    },
                    financial_impact=potential_savings,
                    affected_staff=[staff],
                    recommended_action=f"{staff}により多くのシフトを割り当てるか、雇用形態の見直しを検討してください。",
                    confidence_score=0.7
                )
                insights.append(insight)
        
        return insights
    
    def _detect_fatigue_risk(self,
                            shortage_df: pd.DataFrame,
                            intermediate_df: pd.DataFrame,
                            need_df: Optional[pd.DataFrame]) -> List[Insight]:
        """疲労リスクを検出"""
        insights = []
        
        if 'staff' not in intermediate_df.columns:
            return insights
        
        # スタッフ別の連続勤務を分析
        staff_schedule = intermediate_df.sort_values(['staff', 'ds'])
        
        for staff in staff_schedule['staff'].unique():
            staff_data = staff_schedule[staff_schedule['staff'] == staff]
            total_hours = len(staff_data) * 0.5
            
            # 月200時間以上を危険と判定
            if total_hours > self.threshold_config['fatigue_critical_hours']:
                # 連続勤務日数を計算（簡易版）
                dates = pd.to_datetime(staff_data['ds']).dt.date.unique()
                consecutive_days = self._count_consecutive_days(dates)
                
                insight = Insight(
                    id=f"fatigue_risk_{staff}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    timestamp=datetime.now(),
                    category=InsightCategory.RISK,
                    severity=InsightSeverity.CRITICAL,
                    title=f"{staff}の疲労蓄積リスク",
                    description=f"{staff}は月{total_hours:.0f}時間勤務、最大{consecutive_days}日連続勤務で、離職リスクが高い状態です。",
                    data_evidence={
                        'staff': staff,
                        'total_hours': total_hours,
                        'consecutive_days': consecutive_days,
                        'shift_count': len(staff_data)
                    },
                    financial_impact=100,  # 離職時の採用コスト
                    affected_staff=[staff],
                    recommended_action=f"{staff}に休暇を与え、シフトローテーションを導入してください。",
                    confidence_score=0.9
                )
                insights.append(insight)
        
        return insights
    
    def _detect_cost_anomaly(self,
                            shortage_df: pd.DataFrame,
                            intermediate_df: pd.DataFrame,
                            need_df: Optional[pd.DataFrame]) -> List[Insight]:
        """コスト異常を検出"""
        insights = []
        
        # 曜日別のコスト分析（仮定）
        if 'ds' in intermediate_df.columns:
            intermediate_df['weekday'] = pd.to_datetime(intermediate_df['ds']).dt.dayofweek
            weekday_counts = intermediate_df.groupby('weekday').size()
            
            # 水曜日（2）の異常を検出
            avg_count = weekday_counts[weekday_counts.index != 2].mean()
            wednesday_count = weekday_counts.get(2, 0)
            
            if wednesday_count > avg_count * 1.3:
                excess = wednesday_count - avg_count
                monthly_cost = excess * 0.5 * 2000 * 4 / 10000  # 万円/月
                
                insight = Insight(
                    id=f"wednesday_anomaly_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    timestamp=datetime.now(),
                    category=InsightCategory.ANOMALY,
                    severity=InsightSeverity.HIGH,
                    title="水曜日の異常な過剰配置",
                    description=f"水曜日に他の曜日より{excess:.0f}スロット多い配置があり、月{monthly_cost:.1f}万円の無駄が発生しています。",
                    data_evidence={
                        'wednesday_slots': int(wednesday_count),
                        'average_slots': float(avg_count),
                        'excess_slots': float(excess)
                    },
                    financial_impact=monthly_cost,
                    affected_staff=None,
                    recommended_action="水曜日の配置理由を調査し、適正化してください。",
                    confidence_score=0.85
                )
                insights.append(insight)
        
        return insights
    
    def _detect_hidden_patterns(self,
                               shortage_df: pd.DataFrame,
                               intermediate_df: pd.DataFrame,
                               need_df: Optional[pd.DataFrame]) -> List[Insight]:
        """隠れたパターンを検出"""
        insights = []
        
        # 特定スタッフの専門化パターンを検出
        if 'staff' in intermediate_df.columns and 'role' in intermediate_df.columns:
            staff_role_matrix = intermediate_df.groupby(['staff', 'role']).size().unstack(fill_value=0)
            
            for staff in staff_role_matrix.index:
                staff_roles = staff_role_matrix.loc[staff]
                total = staff_roles.sum()
                
                if total > 0:
                    # 最も多い役割
                    main_role = staff_roles.idxmax()
                    concentration = staff_roles[main_role] / total
                    
                    if concentration > 0.9:  # 90%以上の専門化
                        insight = Insight(
                            id=f"specialization_{staff}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            timestamp=datetime.now(),
                            category=InsightCategory.PATTERN,
                            severity=InsightSeverity.MEDIUM,
                            title=f"{staff}の{main_role}専門化",
                            description=f"{staff}は{main_role}に{concentration*100:.0f}%集中しており、柔軟性が失われています。",
                            data_evidence={
                                'staff': staff,
                                'main_role': main_role,
                                'concentration': concentration,
                                'total_shifts': int(total)
                            },
                            financial_impact=None,
                            affected_staff=[staff],
                            recommended_action=f"{staff}に他の役割も経験させ、多能工化を進めてください。",
                            confidence_score=0.8
                        )
                        insights.append(insight)
        
        return insights
    
    def _detect_fairness_issues(self,
                               shortage_df: pd.DataFrame,
                               intermediate_df: pd.DataFrame,
                               need_df: Optional[pd.DataFrame]) -> List[Insight]:
        """公平性の問題を検出"""
        insights = []
        
        if 'staff' not in intermediate_df.columns:
            return insights
        
        # 休憩時間の不公平を検出（仮定）
        staff_counts = intermediate_df.groupby('staff').size()
        
        # ジニ係数を計算
        gini = self._calculate_gini_coefficient(staff_counts.values)
        
        if gini > 0.3:  # ジニ係数0.3以上を不公平と判定
            min_staff = staff_counts.idxmin()
            max_staff = staff_counts.idxmax()
            ratio = staff_counts[max_staff] / staff_counts[min_staff]
            
            insight = Insight(
                id=f"fairness_issue_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                timestamp=datetime.now(),
                category=InsightCategory.FAIRNESS,
                severity=InsightSeverity.HIGH if ratio > 3 else InsightSeverity.MEDIUM,
                title="シフト配分の不公平",
                description=f"スタッフ間の負荷に{ratio:.1f}倍の差があり、公平性に問題があります（ジニ係数: {gini:.2f}）。",
                data_evidence={
                    'gini_coefficient': gini,
                    'min_workload_staff': min_staff,
                    'max_workload_staff': max_staff,
                    'workload_ratio': ratio
                },
                financial_impact=None,
                affected_staff=[min_staff, max_staff],
                recommended_action="シフト配分アルゴリズムを見直し、公平性を改善してください。",
                confidence_score=0.85
            )
            insights.append(insight)
        
        return insights
    
    def _count_consecutive_days(self, dates: np.ndarray) -> int:
        """連続日数をカウント"""
        if len(dates) == 0:
            return 0
        
        dates = sorted(dates)
        max_consecutive = 1
        current_consecutive = 1
        
        for i in range(1, len(dates)):
            if (dates[i] - dates[i-1]).days == 1:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 1
        
        return max_consecutive
    
    def _calculate_gini_coefficient(self, values: np.ndarray) -> float:
        """ジニ係数を計算"""
        if len(values) == 0:
            return 0
        
        sorted_values = np.sort(values)
        n = len(values)
        cumsum = np.cumsum(sorted_values)
        
        return (2 * np.sum((np.arange(1, n + 1)) * sorted_values)) / (n * cumsum[-1]) - (n + 1) / n
    
    def generate_insight_report(self, output_path: Optional[Path] = None) -> Dict:
        """
        洞察レポートを生成
        
        Args:
            output_path: 出力先パス
            
        Returns:
            レポート辞書
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_insights': len(self.insights),
            'by_severity': {},
            'by_category': {},
            'total_financial_impact': 0,
            'critical_actions': [],
            'insights': []
        }
        
        # 重要度別集計
        for severity in InsightSeverity:
            severity_insights = [i for i in self.insights if i.severity == severity]
            report['by_severity'][severity.value] = len(severity_insights)
        
        # カテゴリ別集計
        for category in InsightCategory:
            category_insights = [i for i in self.insights if i.category == category]
            report['by_category'][category.value] = len(category_insights)
        
        # 財務影響の合計
        report['total_financial_impact'] = sum(
            i.financial_impact for i in self.insights 
            if i.financial_impact is not None
        )
        
        # 重要アクション
        critical_insights = [i for i in self.insights 
                            if i.severity in [InsightSeverity.CRITICAL, InsightSeverity.HIGH]]
        report['critical_actions'] = [
            {
                'title': i.title,
                'action': i.recommended_action,
                'impact': i.financial_impact
            }
            for i in critical_insights[:5]  # Top 5
        ]
        
        # 全洞察
        report['insights'] = [i.to_dict() for i in self.insights]
        
        # ファイル出力
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"洞察レポートを出力: {output_path}")
        
        return report
    
    def generate_executive_summary(self) -> str:
        """
        経営層向けサマリーを生成
        
        Returns:
            サマリーテキスト
        """
        if not self.insights:
            return "分析中に特筆すべき洞察は検出されませんでした。"
        
        critical_count = sum(1 for i in self.insights if i.severity == InsightSeverity.CRITICAL)
        high_count = sum(1 for i in self.insights if i.severity == InsightSeverity.HIGH)
        total_impact = sum(i.financial_impact for i in self.insights if i.financial_impact)
        
        summary = f"""
【シフト分析 洞察サマリー】

■ 検出された重要課題
- 緊急対応必要: {critical_count}件
- 要対応: {high_count}件
- 財務インパクト: {total_impact:.1f}万円/月

■ 最重要課題 TOP3
"""
        
        for i, insight in enumerate(self.insights[:3], 1):
            summary += f"""
{i}. {insight.title}
   {insight.description}
   推奨アクション: {insight.recommended_action}
   財務影響: {insight.financial_impact:.1f}万円/月
"""
        
        summary += f"""
■ カテゴリ別の問題
"""
        
        category_counts = {}
        for insight in self.insights:
            category = insight.category.value
            if category not in category_counts:
                category_counts[category] = 0
            category_counts[category] += 1
        
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            summary += f"- {category}: {count}件\n"
        
        summary += """
詳細は個別の洞察レポートをご確認ください。
"""
        
        return summary


def integrate_with_shortage_analysis(shortage_func):
    """
    既存のshortage分析関数にリアルタイム検出を統合するデコレータ
    
    使用例:
        @integrate_with_shortage_analysis
        def shortage_and_brief(out_dir, ...):
            ...
    """
    def wrapper(*args, **kwargs):
        # 元の関数を実行
        result = shortage_func(*args, **kwargs)
        
        # 出力ディレクトリを取得
        out_dir = args[0] if args else kwargs.get('out_dir')
        if not out_dir:
            return result
        
        out_dir = Path(out_dir)
        
        try:
            # データを読み込み
            shortage_role_path = out_dir / 'shortage_role_summary.parquet'
            intermediate_path = out_dir / 'intermediate_data.parquet'
            
            if shortage_role_path.exists() and intermediate_path.exists():
                shortage_df = pd.read_parquet(shortage_role_path)
                intermediate_df = pd.read_parquet(intermediate_path)
                
                # リアルタイム検出を実行
                detector = RealTimeInsightDetector()
                insights = detector.analyze_shortage_data(
                    shortage_df, 
                    intermediate_df
                )
                
                # レポート生成
                report_path = out_dir / 'insight_report.json'
                detector.generate_insight_report(report_path)
                
                # サマリー出力
                summary = detector.generate_executive_summary()
                summary_path = out_dir / 'executive_insight_summary.txt'
                with open(summary_path, 'w', encoding='utf-8') as f:
                    f.write(summary)
                
                logger.info(f"洞察検出完了: {len(insights)}個の洞察を発見")
                
                # 重要な洞察をログ出力
                for insight in insights[:3]:
                    if insight.severity in [InsightSeverity.CRITICAL, InsightSeverity.HIGH]:
                        logger.warning(f"重要な洞察: {insight.title}")
                
        except Exception as e:
            logger.error(f"リアルタイム洞察検出でエラー: {e}")
        
        return result
    
    return wrapper