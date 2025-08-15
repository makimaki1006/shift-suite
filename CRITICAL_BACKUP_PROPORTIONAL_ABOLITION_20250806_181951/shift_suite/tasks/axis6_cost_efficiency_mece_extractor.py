#!/usr/bin/env python3
"""
軸6: コスト・効率性 MECE事実抽出エンジン

12軸分析フレームワークの軸6を担当
過去シフト実績からコスト最適化と効率性向上に関する制約を抽出

作成日: 2025年7月
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import json

log = logging.getLogger(__name__)

class CostEfficiencyMECEFactExtractor:
    """軸6: コスト・効率性のMECE事実抽出器"""
    
    def __init__(self):
        self.axis_number = 6
        self.axis_name = "コスト・効率性"
        
    def extract_axis6_cost_efficiency_rules(self, long_df: pd.DataFrame, wt_df: pd.DataFrame = None) -> Dict[str, Any]:
        """
        軸6: コスト・効率性ルールをMECE分解により抽出
        
        Args:
            long_df: 過去のシフト実績データ
            wt_df: 勤務区分マスタ（オプション）
            
        Returns:
            Dict: 抽出結果（human_readable, machine_readable, extraction_metadata）
        """
        log.info(f"🎯 軸6: {self.axis_name} MECE事実抽出を開始")
        
        try:
            # データ品質チェック
            if long_df.empty:
                raise ValueError("長期データが空です")
            
            # 軸6のMECE分解カテゴリー（8つ）
            mece_facts = {
                "人件費最適化制約": self._extract_labor_cost_optimization_constraints(long_df, wt_df),
                "雇用形態効率制約": self._extract_employment_efficiency_constraints(long_df, wt_df),
                "時間効率制約": self._extract_time_efficiency_constraints(long_df, wt_df),
                "残業・超過制約": self._extract_overtime_control_constraints(long_df, wt_df),
                "生産性向上制約": self._extract_productivity_enhancement_constraints(long_df, wt_df),
                "リソース活用制約": self._extract_resource_utilization_constraints(long_df, wt_df),
                "運営効率制約": self._extract_operational_efficiency_constraints(long_df, wt_df),
                "コスト削減制約": self._extract_cost_reduction_constraints(long_df, wt_df)
            }
            
            # 人間可読形式の結果生成
            human_readable = self._generate_human_readable_results(mece_facts, long_df)
            
            # 機械可読形式の制約生成
            machine_readable = self._generate_machine_readable_constraints(mece_facts, long_df)
            
            # 抽出メタデータ
            extraction_metadata = self._generate_extraction_metadata(long_df, wt_df, mece_facts)
            
            log.info(f"✅ 軸6: {self.axis_name} MECE事実抽出完了")
            
            return {
                'human_readable': human_readable,
                'machine_readable': machine_readable,
                'extraction_metadata': extraction_metadata
            }
            
        except Exception as e:
            log.error(f"❌ 軸6: {self.axis_name} 抽出エラー: {str(e)}")
            raise e
    
    def _extract_labor_cost_optimization_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """人件費最適化制約の抽出"""
        constraints = []
        
        try:
            # 雇用形態別のコスト推定
            if 'employment' in long_df.columns:
                employment_distribution = long_df['employment'].value_counts()
                total_shifts = len(long_df)
                
                # 正規雇用と非正規雇用の比率
                regular_keywords = ['正社員', '正規', '常勤', 'フルタイム']
                irregular_keywords = ['パート', 'アルバイト', '非常勤', '派遣', '契約']
                
                regular_count = sum(
                    employment_distribution[emp] for emp in employment_distribution.index
                    if any(keyword in emp for keyword in regular_keywords)
                )
                irregular_count = sum(
                    employment_distribution[emp] for emp in employment_distribution.index
                    if any(keyword in emp for keyword in irregular_keywords)
                )
                
                if regular_count + irregular_count > 0:
                    regular_ratio = regular_count / (regular_count + irregular_count)
                    
                    if regular_ratio > 0.7:
                        constraints.append(f"高人件費構造: 正規雇用{regular_ratio:.1%} - コスト最適化の余地")
                    elif regular_ratio < 0.3:
                        constraints.append(f"柔軟人件費構造: 正規雇用{regular_ratio:.1%} - コスト変動リスク管理必要")
                    else:
                        constraints.append(f"バランス人件費構造: 正規雇用{regular_ratio:.1%}")
            
            # 職種別コスト効率分析
            if 'role' in long_df.columns:
                role_distribution = long_df['role'].value_counts()
                
                # 高コスト専門職の配置効率
                high_cost_roles = ['看護師', '医師', '理学療法士', '作業療法士', 'PT', 'OT', 'ST']
                high_cost_count = sum(
                    role_distribution[role] for role in role_distribution.index
                    if any(hc_role in role for hc_role in high_cost_roles)
                )
                
                if high_cost_count > 0:
                    high_cost_ratio = high_cost_count / total_shifts
                    constraints.append(f"専門職コスト比率: {high_cost_ratio:.1%} - 専門性とコストのバランス")
                    
                    if high_cost_ratio > 0.4:
                        constraints.append("専門職集約配置: 高効率活用が重要")
                    else:
                        constraints.append("専門職適正配置: コスト効率良好")
            
            # 時間外・割増賃金の推定
            if 'ds' in long_df.columns:
                long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                long_df['weekday'] = pd.to_datetime(long_df['ds']).dt.day_name()
                
                # 夜間・早朝（割増対象時間）
                premium_hours = list(range(22, 24)) + list(range(0, 6))
                premium_shifts = long_df[long_df['hour'].isin(premium_hours)]
                premium_ratio = len(premium_shifts) / total_shifts if total_shifts > 0 else 0
                
                constraints.append(f"割増時間帯比率: {premium_ratio:.1%} - 人件費増加要因")
                
                # 土日勤務（休日割増）
                weekend_shifts = long_df[long_df['weekday'].isin(['Saturday', 'Sunday'])]
                weekend_ratio = len(weekend_shifts) / total_shifts if total_shifts > 0 else 0
                
                constraints.append(f"休日勤務比率: {weekend_ratio:.1%} - 休日割増コスト")
                
                if premium_ratio + weekend_ratio > 0.3:
                    constraints.append("割増賃金高: シフト最適化でコスト削減可能")
                else:
                    constraints.append("割増賃金適正: 効率的シフト配置")
                
        except Exception as e:
            log.warning(f"人件費最適化制約抽出エラー: {e}")
            constraints.append("人件費最適化制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["人件費最適化に関する制約は検出されませんでした"]
    
    def _extract_employment_efficiency_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """雇用形態効率制約の抽出"""
        constraints = []
        
        try:
            # 雇用形態の多様性と効率性
            if 'employment' in long_df.columns:
                employment_types = long_df['employment'].nunique()
                employment_distribution = long_df['employment'].value_counts()
                
                # 最適な雇用形態ミックスの分析
                total_shifts = len(long_df)
                diversity_score = employment_types / total_shifts * 100
                
                constraints.append(f"雇用形態多様性: {employment_types}種類 (多様性スコア: {diversity_score:.1f})")
                
                if employment_types >= 4:
                    constraints.append("高多様性雇用: 柔軟性高いが管理コスト増")
                elif employment_types <= 2:
                    constraints.append("低多様性雇用: 管理効率良いが柔軟性制限")
                else:
                    constraints.append("適度多様性雇用: バランス良い雇用形態")
                
                # 雇用形態別の稼働効率
                for emp_type in employment_distribution.index[:3]:  # 上位3種類
                    emp_shifts = employment_distribution[emp_type]
                    emp_ratio = emp_shifts / total_shifts
                    
                    if emp_ratio > 0.4:
                        constraints.append(f"{emp_type}主力: {emp_ratio:.1%} - 安定稼働・高依存リスク")
                    elif emp_ratio < 0.1:
                        constraints.append(f"{emp_type}補助: {emp_ratio:.1%} - 特定用途活用")
            
            # フルタイム・パートタイムの効率的配置
            if 'employment' in long_df.columns and 'ds' in long_df.columns:
                # 時間帯別雇用形態分析
                long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                
                # 日中時間帯でのパートタイム活用
                daytime_hours = range(9, 17)
                daytime_data = long_df[long_df['hour'].isin(daytime_hours)]
                
                if not daytime_data.empty:
                    part_time_keywords = ['パート', 'アルバイト', '非常勤']
                    part_time_daytime = sum(
                        daytime_data['employment'].str.contains(keyword, case=False, na=False).sum()
                        for keyword in part_time_keywords
                    )
                    
                    part_time_efficiency = part_time_daytime / len(daytime_data) if len(daytime_data) > 0 else 0
                    constraints.append(f"日中パートタイム活用: {part_time_efficiency:.1%} - コスト効率的配置")
                
                # 夜間・休日でのフルタイム配置
                night_weekend_hours = list(range(22, 24)) + list(range(0, 6))
                long_df['weekday'] = pd.to_datetime(long_df['ds']).dt.day_name()
                
                challenging_shifts = long_df[
                    (long_df['hour'].isin(night_weekend_hours)) |
                    (long_df['weekday'].isin(['Saturday', 'Sunday']))
                ]
                
                if not challenging_shifts.empty:
                    full_time_keywords = ['正社員', '正規', '常勤']
                    full_time_challenging = sum(
                        challenging_shifts['employment'].str.contains(keyword, case=False, na=False).sum()
                        for keyword in full_time_keywords
                    )
                    
                    full_time_coverage = full_time_challenging / len(challenging_shifts) if len(challenging_shifts) > 0 else 0
                    constraints.append(f"困難時間帯正規雇用: {full_time_coverage:.1%} - 責任体制確保")
                
        except Exception as e:
            log.warning(f"雇用形態効率制約抽出エラー: {e}")
            constraints.append("雇用形態効率制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["雇用形態効率に関する制約は検出されませんでした"]
    
    def _extract_time_efficiency_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """時間効率制約の抽出"""
        constraints = []
        
        try:
            # シフト長の効率性分析
            if 'ds' in long_df.columns:
                # 1日のシフト時間分布推定
                long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                
                daily_shift_spans = []
                for date in long_df['ds'].dt.date.unique():
                    daily_data = long_df[long_df['ds'].dt.date == date]
                    if len(daily_data) > 1:
                        min_hour = daily_data['hour'].min()
                        max_hour = daily_data['hour'].max()
                        span = max_hour - min_hour + 1  # +1 for inclusive range
                        daily_shift_spans.append(span)
                
                if daily_shift_spans:
                    avg_operational_hours = np.mean(daily_shift_spans)
                    constraints.append(f"平均稼働時間: {avg_operational_hours:.1f}時間/日")
                    
                    if avg_operational_hours >= 16:
                        constraints.append("長時間稼働: 24時間体制に近い効率的運営")
                    elif avg_operational_hours <= 8:
                        constraints.append("短時間稼働: 集中的・効率的運営")
                    else:
                        constraints.append("中時間稼働: 一般的な運営時間")
            
            # スタッフ稼働効率
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                # スタッフごとの稼働頻度
                staff_workload = long_df['staff'].value_counts()
                
                # 稼働効率の分析
                high_utilization_staff = staff_workload[staff_workload >= staff_workload.quantile(0.8)]
                low_utilization_staff = staff_workload[staff_workload <= staff_workload.quantile(0.2)]
                
                total_staff = len(staff_workload)
                high_util_ratio = len(high_utilization_staff) / total_staff if total_staff > 0 else 0
                low_util_ratio = len(low_utilization_staff) / total_staff if total_staff > 0 else 0
                
                constraints.append(f"高稼働スタッフ: {high_util_ratio:.1%} - 効率活用")
                constraints.append(f"低稼働スタッフ: {low_util_ratio:.1%} - 活用余地")
                
                # 稼働のばらつき
                workload_cv = staff_workload.std() / staff_workload.mean() if staff_workload.mean() > 0 else 0
                if workload_cv > 0.5:
                    constraints.append(f"稼働不均等: CV={workload_cv:.2f} - 効率性改善余地")
                else:
                    constraints.append(f"稼働均等: CV={workload_cv:.2f} - 効率的人員活用")
            
            # 時間帯別効率性
            if 'ds' in long_df.columns and 'staff' in long_df.columns:
                long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                hourly_staff_count = long_df.groupby('hour')['staff'].nunique()
                
                # ピーク効率の分析
                peak_hours = hourly_staff_count.nlargest(3).index.tolist()
                off_peak_hours = hourly_staff_count.nsmallest(3).index.tolist()
                
                peak_efficiency = hourly_staff_count.max() / hourly_staff_count.mean() if hourly_staff_count.mean() > 0 else 0
                constraints.append(f"時間帯効率差: ピーク{peak_efficiency:.1f}倍 - 需要変動対応")
                
                # 24時間効率性
                if len(hourly_staff_count) >= 12:  # 半日以上のデータ
                    night_hours = [22, 23, 0, 1, 2, 3, 4, 5]
                    night_efficiency = hourly_staff_count[hourly_staff_count.index.isin(night_hours)].mean()
                    day_efficiency = hourly_staff_count[~hourly_staff_count.index.isin(night_hours)].mean()
                    
                    if day_efficiency > 0:
                        night_day_ratio = night_efficiency / day_efficiency
                        constraints.append(f"夜間効率比: {night_day_ratio:.2f} - 24時間運営効率")
                
        except Exception as e:
            log.warning(f"時間効率制約抽出エラー: {e}")
            constraints.append("時間効率制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["時間効率に関する制約は検出されませんでした"]
    
    def _extract_overtime_control_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """残業・超過制約の抽出"""
        constraints = []
        
        try:
            # 連続勤務による残業リスク
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                overtime_risks = []
                
                for staff_id in long_df['staff'].unique():
                    staff_dates = pd.to_datetime(long_df[long_df['staff'] == staff_id]['ds']).sort_values()
                    
                    if len(staff_dates) > 1:
                        # 連続勤務日数
                        consecutive_days = self._calculate_max_consecutive_days(staff_dates)
                        if consecutive_days >= 5:
                            overtime_risks.append(consecutive_days)
                
                if overtime_risks:
                    avg_consecutive = np.mean(overtime_risks)
                    risk_staff_ratio = len(overtime_risks) / long_df['staff'].nunique()
                    
                    constraints.append(f"残業リスクスタッフ: {risk_staff_ratio:.1%} (平均{avg_consecutive:.1f}日連続)")
                    
                    if risk_staff_ratio > 0.3:
                        constraints.append("高残業リスク: 連続勤務制限の強化必要")
                    else:
                        constraints.append("残業リスク管理良好: 適切な休憩配置")
                else:
                    constraints.append("残業リスク低: 効果的な勤務分散")
            
            # 時間外勤務の頻度推定
            if 'ds' in long_df.columns:
                long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                
                # 法定時間外（22時-6時）
                overtime_hours = list(range(22, 24)) + list(range(0, 6))
                overtime_shifts = long_df[long_df['hour'].isin(overtime_hours)]
                overtime_ratio = len(overtime_shifts) / len(long_df) if len(long_df) > 0 else 0
                
                constraints.append(f"時間外勤務率: {overtime_ratio:.1%} - 超過勤務手当対象")
                
                if overtime_ratio > 0.25:
                    constraints.append("高時間外比率: 勤務時間最適化でコスト削減可能")
                elif overtime_ratio < 0.1:
                    constraints.append("低時間外比率: 効率的勤務時間管理")
                else:
                    constraints.append("適正時間外比率: バランス良い勤務配置")
            
            # 週40時間超過推定
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                long_df['week'] = pd.to_datetime(long_df['ds']).dt.isocalendar().week
                
                weekly_overtime_staff = []
                for staff_id in long_df['staff'].unique():
                    staff_data = long_df[long_df['staff'] == staff_id]
                    weekly_hours = staff_data.groupby('week').size()
                    
                    # 1週5日以上を超過勤務とみなす（8時間×5日=40時間）
                    overtime_weeks = weekly_hours[weekly_hours > 5]
                    if len(overtime_weeks) > 0:
                        weekly_overtime_staff.append(staff_id)
                
                if long_df['staff'].nunique() > 0:
                    weekly_overtime_ratio = len(weekly_overtime_staff) / long_df['staff'].nunique()
                    constraints.append(f"週次超過勤務率: {weekly_overtime_ratio:.1%} - 労働基準法対応")
                    
                    if weekly_overtime_ratio > 0.2:
                        constraints.append("週次超過多: 勤務時間管理の改善必要")
                    else:
                        constraints.append("週次超過管理良好: 適正勤務時間維持")
                
        except Exception as e:
            log.warning(f"残業・超過制約抽出エラー: {e}")
            constraints.append("残業・超過制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["残業・超過に関する制約は検出されませんでした"]
    
    def _extract_productivity_enhancement_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """生産性向上制約の抽出"""
        constraints = []
        
        try:
            # スタッフ配置の生産性分析
            if 'staff' in long_df.columns and 'role' in long_df.columns:
                # 職種ごとの人員配置効率
                role_staff_matrix = pd.crosstab(long_df['role'], long_df['staff'])
                
                # 多技能スタッフの活用
                multi_role_staff = []
                for staff_id in role_staff_matrix.columns:
                    roles_count = (role_staff_matrix[staff_id] > 0).sum()
                    if roles_count > 1:
                        multi_role_staff.append((staff_id, roles_count))
                
                if multi_role_staff:
                    multi_role_ratio = len(multi_role_staff) / len(role_staff_matrix.columns)
                    avg_roles_per_staff = np.mean([roles for _, roles in multi_role_staff])
                    
                    constraints.append(f"多技能スタッフ: {multi_role_ratio:.1%} (平均{avg_roles_per_staff:.1f}職種)")
                    
                    if multi_role_ratio > 0.3:
                        constraints.append("高多技能活用: 柔軟性・生産性向上")
                    else:
                        constraints.append("専門性重視配置: 専門特化による効率化")
                else:
                    constraints.append("単一職種配置: 専門性集中による生産性確保")
            
            # チームワーク効率
            if 'ds' in long_df.columns and 'staff' in long_df.columns:
                # 同日勤務でのチーム編成
                daily_team_sizes = []
                team_stability_scores = []
                
                for date in long_df['ds'].dt.date.unique():
                    daily_staff = long_df[long_df['ds'].dt.date == date]['staff'].unique()
                    daily_team_sizes.append(len(daily_staff))
                
                if daily_team_sizes:
                    avg_team_size = np.mean(daily_team_sizes)
                    team_size_cv = np.std(daily_team_sizes) / avg_team_size if avg_team_size > 0 else 0
                    
                    constraints.append(f"平均チームサイズ: {avg_team_size:.1f}名 (変動CV={team_size_cv:.2f})")
                    
                    if 3 <= avg_team_size <= 7:
                        constraints.append("最適チームサイズ: 効果的コミュニケーション・協働")
                    elif avg_team_size > 7:
                        constraints.append("大規模チーム: 管理コスト増・効率性要検討")
                    else:
                        constraints.append("小規模チーム: 高密度連携・専門性活用")
                
                # チーム安定性（固定メンバー比率）
                if len(daily_team_sizes) > 7:  # 1週間以上のデータ
                    all_dates = sorted(long_df['ds'].dt.date.unique())
                    stable_pairs = 0
                    total_pairs = 0
                    
                    for i in range(len(all_dates) - 1):
                        today_staff = set(long_df[long_df['ds'].dt.date == all_dates[i]]['staff'])
                        tomorrow_staff = set(long_df[long_df['ds'].dt.date == all_dates[i+1]]['staff'])
                        
                        if today_staff and tomorrow_staff:
                            overlap = len(today_staff.intersection(tomorrow_staff))
                            total = len(today_staff.union(tomorrow_staff))
                            
                            if total > 0:
                                stability = overlap / total
                                if stability >= 0.5:
                                    stable_pairs += 1
                                total_pairs += 1
                    
                    if total_pairs > 0:
                        team_stability = stable_pairs / total_pairs
                        constraints.append(f"チーム安定性: {team_stability:.1%} - 継続性による生産性")
            
            # 専門性活用効率
            if 'role' in long_df.columns:
                specialized_roles = ['看護師', '理学療法士', '作業療法士', 'PT', 'OT', 'ST', '医師']
                general_roles = ['介護士', '介護福祉士', 'ヘルパー', 'ケアワーカー']
                
                specialized_count = sum(
                    long_df['role'].str.contains(role, case=False, na=False).sum()
                    for role in specialized_roles
                )
                general_count = sum(
                    long_df['role'].str.contains(role, case=False, na=False).sum()
                    for role in general_roles
                )
                
                total_shifts = len(long_df)
                if total_shifts > 0:
                    specialization_ratio = specialized_count / total_shifts
                    constraints.append(f"専門性活用率: {specialization_ratio:.1%} - 高付加価値業務比率")
                    
                    if specialization_ratio > 0.4:
                        constraints.append("高専門性配置: 付加価値創出・コスト効果要検証")
                    elif specialization_ratio < 0.2:
                        constraints.append("汎用性重視配置: コスト効率・柔軟性確保")
                    else:
                        constraints.append("専門性バランス配置: 効率性と専門性の調和")
                
        except Exception as e:
            log.warning(f"生産性向上制約抽出エラー: {e}")
            constraints.append("生産性向上制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["生産性向上に関する制約は検出されませんでした"]
    
    def _extract_resource_utilization_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """リソース活用制約の抽出"""
        constraints = []
        
        try:
            # 人的リソースの稼働率
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                total_staff = long_df['staff'].nunique()
                total_days = long_df['ds'].dt.date.nunique()
                total_possible_shifts = total_staff * total_days
                actual_shifts = len(long_df)
                
                if total_possible_shifts > 0:
                    utilization_rate = actual_shifts / total_possible_shifts
                    constraints.append(f"人員稼働率: {utilization_rate:.1%} - リソース活用効率")
                    
                    if utilization_rate > 0.7:
                        constraints.append("高稼働率: 効率的人員活用・過労リスク要注意")
                    elif utilization_rate < 0.3:
                        constraints.append("低稼働率: 人員余剰・コスト最適化余地")
                    else:
                        constraints.append("適正稼働率: バランス良いリソース活用")
                
                # スタッフ個別の稼働効率
                staff_utilization = long_df['staff'].value_counts()
                avg_workdays = staff_utilization.mean()
                max_workdays = staff_utilization.max()
                min_workdays = staff_utilization.min()
                
                utilization_range = max_workdays - min_workdays
                constraints.append(f"個人稼働差: 最大{max_workdays}日 - 最小{min_workdays}日 (差{utilization_range}日)")
                
                if utilization_range > total_days * 0.5:
                    constraints.append("稼働格差大: 人員配置の均等化要検討")
                else:
                    constraints.append("稼働格差小: 均等なリソース活用")
            
            # 時間帯別リソース効率
            if 'ds' in long_df.columns:
                long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                hourly_distribution = long_df['hour'].value_counts().sort_index()
                
                # 稼働時間帯の集中度
                if len(hourly_distribution) > 0:
                    peak_hours = hourly_distribution.nlargest(6).index.tolist()  # 上位6時間
                    peak_concentration = hourly_distribution.nlargest(6).sum() / len(long_df)
                    
                    constraints.append(f"ピーク時間集中: {peak_concentration:.1%} (時間帯: {sorted(peak_hours)})")
                    
                    if peak_concentration > 0.6:
                        constraints.append("高時間集中: 効率的だが柔軟性制限")
                    else:
                        constraints.append("分散時間配置: 柔軟性高・効率性要検討")
            
            # 職種リソースの活用バランス
            if 'role' in long_df.columns:
                role_distribution = long_df['role'].value_counts()
                role_concentration = role_distribution.iloc[0] / len(long_df) if len(role_distribution) > 0 else 0
                
                constraints.append(f"主要職種集中: {role_concentration:.1%} - リソース集約度")
                
                # 職種多様性指標
                role_diversity = len(role_distribution) / len(long_df) * 100
                if role_diversity > 15:
                    constraints.append("高職種多様性: 多角的サービス・管理コスト増")
                elif role_diversity < 5:
                    constraints.append("低職種多様性: 効率的管理・専門性制限")
                else:
                    constraints.append("適度職種多様性: バランス良いリソース構成")
            
            # 雇用形態リソースの効率活用
            if 'employment' in long_df.columns and 'ds' in long_df.columns:
                # 雇用形態別の時間帯活用
                employment_time_matrix = pd.crosstab(
                    long_df['employment'], 
                    pd.to_datetime(long_df['ds']).dt.hour
                )
                
                # 各雇用形態の時間分散度
                for emp_type in employment_time_matrix.index[:3]:  # 上位3種類
                    time_distribution = employment_time_matrix.loc[emp_type]
                    time_cv = time_distribution.std() / time_distribution.mean() if time_distribution.mean() > 0 else 0
                    
                    if time_cv > 1.0:
                        constraints.append(f"{emp_type}時間集中配置: CV={time_cv:.2f} - 特定時間帯活用")
                    else:
                        constraints.append(f"{emp_type}時間分散配置: CV={time_cv:.2f} - 均等時間活用")
                
        except Exception as e:
            log.warning(f"リソース活用制約抽出エラー: {e}")
            constraints.append("リソース活用制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["リソース活用に関する制約は検出されませんでした"]
    
    def _extract_operational_efficiency_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """運営効率制約の抽出"""
        constraints = []
        
        try:
            # シフト変更・調整の頻度推定
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                # スタッフの勤務パターン分析
                staff_patterns = {}
                for staff_id in long_df['staff'].unique():
                    staff_dates = pd.to_datetime(long_df[long_df['staff'] == staff_id]['ds'])
                    if len(staff_dates) > 1:
                        # 勤務間隔の標準偏差（規則性の指標）
                        intervals = staff_dates.sort_values().diff().dt.days.dropna()
                        if len(intervals) > 0:
                            pattern_regularity = intervals.std()
                            staff_patterns[staff_id] = pattern_regularity
                
                if staff_patterns:
                    avg_irregularity = np.mean(list(staff_patterns.values()))
                    regular_staff_ratio = sum(1 for irregularity in staff_patterns.values() if irregularity <= 2) / len(staff_patterns)
                    
                    constraints.append(f"勤務パターン規則性: {regular_staff_ratio:.1%}のスタッフが規則的 (平均不規則度: {avg_irregularity:.1f}日)")
                    
                    if regular_staff_ratio > 0.7:
                        constraints.append("高規則性勤務: 運営効率良・予測可能性高")
                    else:
                        constraints.append("不規則勤務多: 柔軟性高・管理コスト増")
            
            # 引き継ぎ効率
            if 'ds' in long_df.columns and 'staff' in long_df.columns and 'code' in long_df.columns:
                # シフト間の重複・引き継ぎ分析
                handover_opportunities = 0
                total_shift_changes = 0
                
                for date in long_df['ds'].dt.date.unique():
                    daily_data = long_df[long_df['ds'].dt.date == date]
                    
                    # 異なるシフトコードの組み合わせ
                    shift_codes = daily_data['code'].unique()
                    if len(shift_codes) > 1:
                        total_shift_changes += 1
                        
                        # スタッフの重複（引き継ぎ機会）
                        shift_staff_overlap = False
                        for i, code1 in enumerate(shift_codes):
                            for code2 in shift_codes[i+1:]:
                                staff1 = set(daily_data[daily_data['code'] == code1]['staff'])
                                staff2 = set(daily_data[daily_data['code'] == code2]['staff'])
                                if staff1.intersection(staff2):
                                    shift_staff_overlap = True
                                    break
                            if shift_staff_overlap:
                                break
                        
                        if shift_staff_overlap:
                            handover_opportunities += 1
                
                if total_shift_changes > 0:
                    handover_efficiency = handover_opportunities / total_shift_changes
                    constraints.append(f"引き継ぎ効率: {handover_efficiency:.1%} - 情報共有機会")
                    
                    if handover_efficiency > 0.6:
                        constraints.append("高引き継ぎ効率: 情報共有充実・運営継続性確保")
                    else:
                        constraints.append("引き継ぎ機会少: 情報共有体制の改善余地")
            
            # 管理負荷の推定
            if 'staff' in long_df.columns and 'employment' in long_df.columns and 'role' in long_df.columns:
                # 管理対象の複雑性
                unique_staff = long_df['staff'].nunique()
                unique_employments = long_df['employment'].nunique()
                unique_roles = long_df['role'].nunique()
                
                management_complexity = (unique_staff * unique_employments * unique_roles) / len(long_df) * 100
                constraints.append(f"管理複雑度: {management_complexity:.1f} - 運営管理負荷指標")
                
                if management_complexity > 50:
                    constraints.append("高管理複雑度: システム化・標準化で効率化必要")
                elif management_complexity < 10:
                    constraints.append("低管理複雑度: シンプル運営・効率性確保")
                else:
                    constraints.append("適度管理複雑度: バランス良い運営体制")
            
            # 運営の安定性
            if 'ds' in long_df.columns:
                # 日別の勤務者数の安定性
                daily_staff_counts = long_df.groupby(long_df['ds'].dt.date)['staff'].nunique()
                
                if len(daily_staff_counts) > 1:
                    stability_cv = daily_staff_counts.std() / daily_staff_counts.mean()
                    constraints.append(f"運営安定性: 日別人員変動CV={stability_cv:.2f}")
                    
                    if stability_cv < 0.2:
                        constraints.append("高運営安定性: 予測可能・効率的運営")
                    elif stability_cv > 0.5:
                        constraints.append("運営変動大: 需要対応力高・管理負荷増")
                    else:
                        constraints.append("適度運営変動: 柔軟性と安定性のバランス")
                
        except Exception as e:
            log.warning(f"運営効率制約抽出エラー: {e}")
            constraints.append("運営効率制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["運営効率に関する制約は検出されませんでした"]
    
    def _extract_cost_reduction_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """コスト削減制約の抽出"""
        constraints = []
        
        try:
            # 無駄な人員配置の特定
            if 'ds' in long_df.columns and 'staff' in long_df.columns:
                # 最小限人員での運営可能性
                daily_staff_counts = long_df.groupby(long_df['ds'].dt.date)['staff'].nunique()
                min_staff_needed = daily_staff_counts.min()
                max_staff_used = daily_staff_counts.max()
                avg_staff = daily_staff_counts.mean()
                
                efficiency_ratio = min_staff_needed / avg_staff if avg_staff > 0 else 0
                constraints.append(f"人員効率化余地: 最小{min_staff_needed}名 vs 平均{avg_staff:.1f}名 (効率比{efficiency_ratio:.2f})")
                
                if efficiency_ratio < 0.7:
                    constraints.append("人員削減余地: 最小配置基準での運営検討可能")
                else:
                    constraints.append("効率的人員配置: 適正レベルの人員活用")
                
                # 過剰配置日の特定
                median_staff = daily_staff_counts.median()
                excess_days = sum(daily_staff_counts > median_staff * 1.5)
                total_days = len(daily_staff_counts)
                excess_ratio = excess_days / total_days if total_days > 0 else 0
                
                if excess_ratio > 0.2:
                    constraints.append(f"過剰配置日: {excess_ratio:.1%} - コスト削減機会")
                else:
                    constraints.append(f"適正配置維持: 過剰配置{excess_ratio:.1%}のみ")
            
            # 高コスト時間帯の最適化
            if 'ds' in long_df.columns:
                long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                long_df['weekday'] = pd.to_datetime(long_df['ds']).dt.day_name()
                
                # 割増時間帯のコスト効率
                premium_hours = list(range(22, 24)) + list(range(0, 6))  # 夜間割増
                weekend_days = ['Saturday', 'Sunday']  # 休日割増
                
                premium_time_shifts = long_df[long_df['hour'].isin(premium_hours)]
                weekend_shifts = long_df[long_df['weekday'].isin(weekend_days)]
                
                total_shifts = len(long_df)
                premium_time_ratio = len(premium_time_shifts) / total_shifts if total_shifts > 0 else 0
                weekend_ratio = len(weekend_shifts) / total_shifts if total_shifts > 0 else 0
                
                total_premium_cost_ratio = premium_time_ratio + weekend_ratio
                constraints.append(f"高コスト時間比率: 夜間{premium_time_ratio:.1%} + 休日{weekend_ratio:.1%} = {total_premium_cost_ratio:.1%}")
                
                if total_premium_cost_ratio > 0.4:
                    constraints.append("高コスト時間多: 日中・平日シフトへの移行でコスト削減")
                elif total_premium_cost_ratio < 0.2:
                    constraints.append("低コスト時間中心: 効率的コスト管理")
                else:
                    constraints.append("バランス時間配置: 必要性に応じたコスト負担")
            
            # 雇用形態最適化によるコスト削減
            if 'employment' in long_df.columns and 'role' in long_df.columns:
                # 正規雇用の必要性分析
                regular_keywords = ['正社員', '正規', '常勤']
                non_regular_keywords = ['パート', 'アルバイト', '非常勤', '派遣']
                
                regular_shifts = sum(
                    long_df['employment'].str.contains(keyword, case=False, na=False).sum()
                    for keyword in regular_keywords
                )
                non_regular_shifts = sum(
                    long_df['employment'].str.contains(keyword, case=False, na=False).sum()
                    for keyword in non_regular_keywords
                )
                
                if regular_shifts + non_regular_shifts > 0:
                    regular_ratio = regular_shifts / (regular_shifts + non_regular_shifts)
                    
                    # 職種別の雇用形態適正性
                    specialist_roles = ['看護師', '医師', '理学療法士', '作業療法士']
                    general_roles = ['介護士', 'ヘルパー', 'ケアワーカー']
                    
                    specialist_count = sum(
                        long_df['role'].str.contains(role, case=False, na=False).sum()
                        for role in specialist_roles
                    )
                    general_count = sum(
                        long_df['role'].str.contains(role, case=False, na=False).sum()
                        for role in general_roles
                    )
                    
                    if specialist_count > 0 and general_count > 0:
                        specialist_ratio = specialist_count / (specialist_count + general_count)
                        
                        if regular_ratio > specialist_ratio + 0.2:
                            constraints.append(f"正規雇用過多可能性: 正規{regular_ratio:.1%} vs 専門職{specialist_ratio:.1%}")
                        else:
                            constraints.append(f"雇用形態適正: 正規{regular_ratio:.1%}・専門職{specialist_ratio:.1%}バランス")
            
            # 交通費・諸手当削減機会
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                # 短時間・短期間勤務の分析
                staff_workdays = long_df['staff'].value_counts()
                
                # 月4日未満勤務（交通費効率悪）
                low_frequency_staff = staff_workdays[staff_workdays < 4]
                low_frequency_ratio = len(low_frequency_staff) / len(staff_workdays) if len(staff_workdays) > 0 else 0
                
                if low_frequency_ratio > 0.3:
                    constraints.append(f"低頻度勤務スタッフ: {low_frequency_ratio:.1%} - 交通費効率要検討")
                else:
                    constraints.append(f"効率的勤務頻度: 低頻度{low_frequency_ratio:.1%}のみ")
                
                # 勤務集約による効率化
                total_staff = long_df['staff'].nunique()
                total_workdays = len(long_df)
                consolidation_potential = total_workdays / total_staff
                
                constraints.append(f"勤務集約度: 平均{consolidation_potential:.1f}日/人 - 効率化指標")
                
                if consolidation_potential < 5:
                    constraints.append("勤務分散: 集約化でコスト削減余地")
                else:
                    constraints.append("勤務集約済: 効率的スタッフ活用")
                
        except Exception as e:
            log.warning(f"コスト削減制約抽出エラー: {e}")
            constraints.append("コスト削減制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["コスト削減に関する制約は検出されませんでした"]
    
    def _calculate_max_consecutive_days(self, dates: pd.Series) -> int:
        """最大連続勤務日数の計算"""
        if len(dates) <= 1:
            return len(dates)
        
        sorted_dates = sorted(dates)
        max_consecutive = 1
        current_consecutive = 1
        
        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 1
        
        return max_consecutive
    
    def _generate_human_readable_results(self, mece_facts: Dict[str, List[str]], long_df: pd.DataFrame) -> Dict[str, Any]:
        """人間可読形式の結果生成"""
        
        # 事実総数計算
        total_facts = sum(len(facts) for facts in mece_facts.values())
        
        # コスト・効率性重要度別分類
        high_impact = [fact for facts in mece_facts.values() for fact in facts if any(keyword in fact for keyword in ['削減', '最適化', '効率', '余地'])]
        cost_focus = [fact for facts in mece_facts.values() for fact in facts if any(keyword in fact for keyword in ['コスト', '人件費', '割増', '超過'])]
        efficiency_focus = [fact for facts in mece_facts.values() for fact in facts if any(keyword in fact for keyword in ['生産性', '稼働', '活用', '効率'])]
        
        return {
            '抽出事実サマリー': {
                '総事実数': total_facts,
                '分析軸': f'軸{self.axis_number}: {self.axis_name}',
                '分析対象レコード数': len(long_df),
                'MECEカテゴリー数': len(mece_facts),
                **{category: len(facts) for category, facts in mece_facts.items()}
            },
            'MECE分解事実': mece_facts,
            'コスト・効率性分類': {
                '高インパクト事実（削減・最適化）': high_impact,
                'コスト重点事実（人件費・割増）': cost_focus,
                '効率性重点事実（生産性・稼働）': efficiency_focus,
                '要検証事実': [fact for facts in mece_facts.values() for fact in facts if 'エラー' in fact or '検出されませんでした' in fact]
            }
        }
    
    def _generate_machine_readable_constraints(self, mece_facts: Dict[str, List[str]], long_df: pd.DataFrame) -> Dict[str, Any]:
        """機械可読形式の制約生成"""
        
        hard_constraints = []
        soft_constraints = []
        preferences = []
        
        # MECEカテゴリー別制約分類
        for category, facts in mece_facts.items():
            for i, fact in enumerate(facts):
                constraint_id = f"axis6_{category.lower().replace('制約', '')}_{i+1}"
                
                # コスト・効率性の制約強度判定
                if any(keyword in fact for keyword in ['削減', '最適化', '超過', '必要', '制限']):
                    hard_constraints.append({
                        'id': constraint_id,
                        'type': 'cost_efficiency',
                        'category': category,
                        'description': fact,
                        'priority': 'high',
                        'confidence': 0.8,
                        'cost_impact': self._assess_cost_impact(fact),
                        'efficiency_aspect': self._categorize_efficiency_aspect(fact)
                    })
                elif any(keyword in fact for keyword in ['改善', '向上', '効率化', '活用', '検討']):
                    soft_constraints.append({
                        'id': constraint_id,
                        'type': 'cost_efficiency',
                        'category': category,
                        'description': fact,
                        'priority': 'medium',
                        'confidence': 0.6,
                        'cost_impact': self._assess_cost_impact(fact),
                        'efficiency_aspect': self._categorize_efficiency_aspect(fact)
                    })
                else:
                    preferences.append({
                        'id': constraint_id,
                        'type': 'cost_efficiency',
                        'category': category,
                        'description': fact,
                        'priority': 'low',
                        'confidence': 0.4,
                        'cost_impact': self._assess_cost_impact(fact),
                        'efficiency_aspect': self._categorize_efficiency_aspect(fact)
                    })
        
        return {
            'hard_constraints': hard_constraints,
            'soft_constraints': soft_constraints,
            'preferences': preferences,
            'constraint_relationships': [
                {
                    'relationship_id': 'cost_efficiency_tradeoff',
                    'type': 'conflicts',
                    'from_category': '人件費最適化制約',
                    'to_category': '生産性向上制約',
                    'description': 'コスト削減と生産性向上のトレードオフ関係'
                },
                {
                    'relationship_id': 'efficiency_synergy',
                    'type': 'enhances',
                    'from_category': '時間効率制約',
                    'to_category': 'リソース活用制約',
                    'description': '時間効率とリソース活用の相乗効果'
                }
            ],
            'validation_rules': [
                {
                    'rule_id': 'axis6_cost_threshold_check',
                    'description': 'コスト上限を超えないことを確認',
                    'validation_type': 'cost_control'
                },
                {
                    'rule_id': 'axis6_efficiency_minimum_check',
                    'description': '最低効率基準を満たすことを確認',
                    'validation_type': 'efficiency_compliance'
                },
                {
                    'rule_id': 'axis6_overtime_limit_check',
                    'description': '残業時間制限を遵守することを確認',
                    'validation_type': 'overtime_control'
                }
            ]
        }
    
    def _assess_cost_impact(self, fact: str) -> str:
        """コストインパクトの評価"""
        if any(keyword in fact for keyword in ['削減', '余地', '過多', '超過']):
            return 'high_reduction_potential'
        elif any(keyword in fact for keyword in ['最適化', '効率化', '改善']):
            return 'medium_optimization'
        elif any(keyword in fact for keyword in ['増', 'リスク', '負担']):
            return 'cost_increase_risk'
        else:
            return 'neutral'
    
    def _categorize_efficiency_aspect(self, fact: str) -> str:
        """効率性側面の分類"""
        if any(keyword in fact for keyword in ['人件費', 'コスト', '割増']):
            return 'cost_efficiency'
        elif any(keyword in fact for keyword in ['時間', '稼働', '活用']):
            return 'time_efficiency'
        elif any(keyword in fact for keyword in ['生産性', 'チーム', '協働']):
            return 'productivity'
        elif any(keyword in fact for keyword in ['残業', '超過', '連続']):
            return 'overtime_control'
        elif any(keyword in fact for keyword in ['雇用', '形態', '配置']):
            return 'employment_optimization'
        elif any(keyword in fact for keyword in ['運営', '管理', '安定']):
            return 'operational_efficiency'
        else:
            return 'general_efficiency'
    
    def _generate_extraction_metadata(self, long_df: pd.DataFrame, wt_df: pd.DataFrame, 
                                     mece_facts: Dict[str, List[str]]) -> Dict[str, Any]:
        """抽出メタデータの生成"""
        
        # データ期間の計算
        date_range = {}
        if 'ds' in long_df.columns:
            dates = pd.to_datetime(long_df['ds'])
            date_range = {
                'start_date': dates.min().isoformat(),
                'end_date': dates.max().isoformat(),
                'total_days': (dates.max() - dates.min()).days
            }
        
        # コスト・効率性指標
        cost_efficiency_indicators = {
            'regular_employment_ratio': len(long_df[long_df['employment'].str.contains('正社員|正規', case=False, na=False)]) / len(long_df) if 'employment' in long_df.columns and len(long_df) > 0 else 0,
            'overtime_shift_ratio': len(long_df[pd.to_datetime(long_df['ds']).dt.hour.isin(list(range(22, 24)) + list(range(0, 6)))]) / len(long_df) if 'ds' in long_df.columns and len(long_df) > 0 else 0,
            'staff_utilization_cv': long_df['staff'].value_counts().std() / long_df['staff'].value_counts().mean() if 'staff' in long_df.columns and long_df['staff'].value_counts().mean() > 0 else 0,
            'cost_optimization_potential': len([f for facts in mece_facts.values() for f in facts if '削減' in f or '余地' in f]) / sum(len(facts) for facts in mece_facts.values()) if sum(len(facts) for facts in mece_facts.values()) > 0 else 0
        }
        
        # データ品質指標
        data_quality = {
            'completeness': 1.0 - (long_df.isnull().sum().sum() / (len(long_df) * len(long_df.columns))),
            'record_count': len(long_df),
            'unique_staff_count': long_df['staff'].nunique() if 'staff' in long_df.columns else 0,
            'unique_employment_types': long_df['employment'].nunique() if 'employment' in long_df.columns else 0,
            'efficiency_focus_ratio': len([f for facts in mece_facts.values() for f in facts if any(e in f for e in ['効率', 'コスト', '削減', '最適'])]) / sum(len(facts) for facts in mece_facts.values()) if sum(len(facts) for facts in mece_facts.values()) > 0 else 0
        }
        
        return {
            'extraction_timestamp': datetime.now().isoformat(),
            'axis_info': {
                'axis_number': self.axis_number,
                'axis_name': self.axis_name,
                'mece_categories': list(mece_facts.keys()),
                'focus_area': 'コスト最適化・効率性向上制約'
            },
            'data_period': date_range,
            'cost_efficiency_indicators': cost_efficiency_indicators,
            'data_quality': data_quality,
            'extraction_statistics': {
                'total_facts_extracted': sum(len(facts) for facts in mece_facts.values()),
                'cost_reduction_facts': len([f for facts in mece_facts.values() for f in facts if '削減' in f or 'コスト' in f]),
                'efficiency_improvement_facts': len([f for facts in mece_facts.values() for f in facts if '効率' in f or '生産性' in f]),
                'optimization_opportunities': len([f for facts in mece_facts.values() for f in facts if '最適化' in f or '余地' in f]),
                'categories_with_facts': len([cat for cat, facts in mece_facts.items() if facts and not any('検出されませんでした' in f for f in facts)])
            }
        }