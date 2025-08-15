#!/usr/bin/env python3
"""
軸4: 需要・負荷管理 MECE事実抽出エンジン

12軸分析フレームワークの軸4を担当
過去シフト実績から需要変動パターンと負荷分散に関する制約を抽出

作成日: 2025年7月
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import json

log = logging.getLogger(__name__)

class DemandLoadMECEFactExtractor:
    """軸4: 需要・負荷管理のMECE事実抽出器"""
    
    def __init__(self):
        self.axis_number = 4
        self.axis_name = "需要・負荷管理"
        
    def extract_axis4_demand_load_rules(self, long_df: pd.DataFrame, wt_df: pd.DataFrame = None) -> Dict[str, Any]:
        """
        軸4: 需要・負荷管理ルールをMECE分解により抽出
        
        Args:
            long_df: 過去のシフト実績データ
            wt_df: 勤務区分マスタ（オプション）
            
        Returns:
            Dict: 抽出結果（human_readable, machine_readable, extraction_metadata）
        """
        log.info(f"🎯 軸4: {self.axis_name} MECE事実抽出を開始")
        
        try:
            # データ品質チェック
            if long_df.empty:
                raise ValueError("長期データが空です")
            
            # 軸4のMECE分解カテゴリー（8つ）
            mece_facts = {
                "需要予測制約": self._extract_demand_forecasting_constraints(long_df, wt_df),
                "ピーク負荷制約": self._extract_peak_load_constraints(long_df, wt_df),
                "負荷分散制約": self._extract_load_distribution_constraints(long_df, wt_df),
                "需要変動対応制約": self._extract_demand_variation_constraints(long_df, wt_df),
                "リソース配分制約": self._extract_resource_allocation_constraints(long_df, wt_df),
                "キャパシティ制約": self._extract_capacity_constraints(long_df, wt_df),
                "需要パターン制約": self._extract_demand_pattern_constraints(long_df, wt_df),
                "負荷平準化制約": self._extract_load_leveling_constraints(long_df, wt_df)
            }
            
            # 人間可読形式の結果生成
            human_readable = self._generate_human_readable_results(mece_facts, long_df)
            
            # 機械可読形式の制約生成
            machine_readable = self._generate_machine_readable_constraints(mece_facts, long_df)
            
            # 抽出メタデータ
            extraction_metadata = self._generate_extraction_metadata(long_df, wt_df, mece_facts)
            
            log.info(f"✅ 軸4: {self.axis_name} MECE事実抽出完了")
            
            return {
                'human_readable': human_readable,
                'machine_readable': machine_readable,
                'extraction_metadata': extraction_metadata
            }
            
        except Exception as e:
            log.error(f"❌ 軸4: {self.axis_name} 抽出エラー: {str(e)}")
            raise e
    
    def _extract_demand_forecasting_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """需要予測制約の抽出"""
        constraints = []
        
        try:
            # 時間帯別需要パターン分析
            if 'ds' in long_df.columns and 'role' in long_df.columns:
                # 時間帯別スタッフ配置数を分析
                long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                hourly_demand = long_df.groupby(['hour', 'role']).size().reset_index(name='demand_count')
                
                # 高需要時間帯の特定
                peak_hours = hourly_demand.groupby('hour')['demand_count'].sum().nlargest(3).index.tolist()
                constraints.append(f"高需要時間帯: {peak_hours}時に集中的な人員配置が必要")
                
                # 職種別需要変動
                role_variations = {}
                for role in long_df['role'].unique():
                    role_hourly = hourly_demand[hourly_demand['role'] == role]['demand_count']
                    if len(role_hourly) > 1:
                        cv = role_hourly.std() / role_hourly.mean() if role_hourly.mean() > 0 else 0
                        role_variations[role] = cv
                
                # 変動の大きい職種
                high_variation_roles = [role for role, cv in role_variations.items() if cv > 0.5]
                if high_variation_roles:
                    constraints.append(f"需要変動の大きい職種: {', '.join(high_variation_roles)} - 予測精度向上が重要")
            
            # 曜日別需要パターン
            if 'ds' in long_df.columns:
                long_df['weekday'] = pd.to_datetime(long_df['ds']).dt.day_name()
                daily_demand = long_df.groupby('weekday').size()
                peak_day = daily_demand.idxmax()
                low_day = daily_demand.idxmin()
                constraints.append(f"曜日別需要: {peak_day}が最高、{low_day}が最低需要")
                
        except Exception as e:
            log.warning(f"需要予測制約抽出エラー: {e}")
            constraints.append("需要予測制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["需要予測に関する制約は検出されませんでした"]
    
    def _extract_peak_load_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """ピーク負荷制約の抽出"""
        constraints = []
        
        try:
            # 日別スタッフ数でピーク負荷を分析
            if 'ds' in long_df.columns:
                daily_staff_count = long_df.groupby(long_df['ds'].dt.date)['staff'].nunique()
                peak_threshold = daily_staff_count.quantile(0.9)
                peak_days = daily_staff_count[daily_staff_count >= peak_threshold]
                
                constraints.append(f"ピーク負荷日数: {len(peak_days)}日 (閾値: {peak_threshold:.1f}人以上)")
                
                # ピーク負荷の曜日パターン
                if len(peak_days) > 0:
                    peak_weekdays = pd.to_datetime(peak_days.index).day_name().value_counts()
                    most_common_peak = peak_weekdays.index[0]
                    constraints.append(f"ピーク負荷頻発曜日: {most_common_peak} ({peak_weekdays.iloc[0]}回)")
            
            # 時間帯別ピーク負荷
            if 'ds' in long_df.columns:
                long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                hourly_load = long_df.groupby('hour')['staff'].nunique()
                peak_hour = hourly_load.idxmax()
                peak_count = hourly_load.max()
                constraints.append(f"ピーク負荷時間: {peak_hour}時 ({peak_count}人)")
                
        except Exception as e:
            log.warning(f"ピーク負荷制約抽出エラー: {e}")
            constraints.append("ピーク負荷制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["ピーク負荷に関する制約は検出されませんでした"]
    
    def _extract_load_distribution_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """負荷分散制約の抽出"""
        constraints = []
        
        try:
            # スタッフ間の負荷分散を分析
            if 'staff' in long_df.columns:
                staff_workload = long_df['staff'].value_counts()
                workload_cv = staff_workload.std() / staff_workload.mean() if staff_workload.mean() > 0 else 0
                
                if workload_cv > 0.3:
                    constraints.append(f"負荷不均衡検出: CV={workload_cv:.2f} - 負荷分散の改善が必要")
                else:
                    constraints.append(f"負荷分散良好: CV={workload_cv:.2f}")
                
                # 過負荷スタッフの特定
                workload_threshold = staff_workload.quantile(0.8)
                overloaded_staff = staff_workload[staff_workload >= workload_threshold]
                if len(overloaded_staff) > 0:
                    constraints.append(f"高負荷スタッフ数: {len(overloaded_staff)}人 (閾値: {workload_threshold:.1f}勤務以上)")
            
            # 職種間負荷分散
            if 'role' in long_df.columns:
                role_workload = long_df['role'].value_counts()
                role_cv = role_workload.std() / role_workload.mean() if role_workload.mean() > 0 else 0
                constraints.append(f"職種間負荷分散: CV={role_cv:.2f}")
                
        except Exception as e:
            log.warning(f"負荷分散制約抽出エラー: {e}")
            constraints.append("負荷分散制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["負荷分散に関する制約は検出されませんでした"]
    
    def _extract_demand_variation_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """需要変動対応制約の抽出"""
        constraints = []
        
        try:
            # 需要変動の分析
            if 'ds' in long_df.columns:
                # 日別スタッフ数の変動
                daily_count = long_df.groupby(long_df['ds'].dt.date).size()
                if len(daily_count) > 1:
                    variation_cv = daily_count.std() / daily_count.mean()
                    
                    if variation_cv > 0.2:
                        constraints.append(f"高需要変動: CV={variation_cv:.2f} - 柔軟な人員調整が必要")
                    else:
                        constraints.append(f"安定需要: CV={variation_cv:.2f}")
                
                # 短期変動（週単位）
                if len(daily_count) >= 7:
                    weekly_means = []
                    for i in range(0, len(daily_count), 7):
                        week_data = daily_count.iloc[i:i+7]
                        if len(week_data) >= 3:  # 最低3日のデータがある週のみ
                            weekly_means.append(week_data.mean())
                    
                    if len(weekly_means) > 1:
                        weekly_cv = np.std(weekly_means) / np.mean(weekly_means)
                        constraints.append(f"週次需要変動: CV={weekly_cv:.2f}")
                
        except Exception as e:
            log.warning(f"需要変動対応制約抽出エラー: {e}")
            constraints.append("需要変動対応制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["需要変動対応に関する制約は検出されませんでした"]
    
    def _extract_resource_allocation_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """リソース配分制約の抽出"""
        constraints = []
        
        try:
            # 職種別リソース配分
            if 'role' in long_df.columns and 'employment' in long_df.columns:
                role_employment_matrix = pd.crosstab(long_df['role'], long_df['employment'])
                
                # 各職種の雇用形態分散度
                for role in role_employment_matrix.index:
                    role_data = role_employment_matrix.loc[role]
                    if role_data.sum() > 0:
                        employment_ratio = role_data / role_data.sum()
                        dominant_employment = employment_ratio.idxmax()
                        dominant_ratio = employment_ratio.max()
                        
                        if dominant_ratio > 0.8:
                            constraints.append(f"{role}: {dominant_employment}に偏重 ({dominant_ratio:.1%})")
                        else:
                            constraints.append(f"{role}: バランス良い雇用形態配分")
            
            # 時間帯別リソース配分
            if 'ds' in long_df.columns and 'role' in long_df.columns:
                long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                hourly_role_count = pd.crosstab(long_df['hour'], long_df['role'])
                
                # 各時間帯でのリソース配分の偏り
                for hour in hourly_role_count.index:
                    hour_data = hourly_role_count.loc[hour]
                    if hour_data.sum() > 0:
                        hour_cv = hour_data.std() / hour_data.mean()
                        if hour_cv > 1.0:
                            constraints.append(f"{hour}時: 職種配分に偏り (CV={hour_cv:.2f})")
                
        except Exception as e:
            log.warning(f"リソース配分制約抽出エラー: {e}")
            constraints.append("リソース配分制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["リソース配分に関する制約は検出されませんでした"]
    
    def _extract_capacity_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """キャパシティ制約の抽出"""
        constraints = []
        
        try:
            # 最大キャパシティの分析
            if 'staff' in long_df.columns:
                total_unique_staff = long_df['staff'].nunique()
                constraints.append(f"総スタッフ数: {total_unique_staff}人")
                
                # 同時勤務最大人数
                if 'ds' in long_df.columns:
                    simultaneous_staff = long_df.groupby('ds')['staff'].nunique()
                    max_simultaneous = simultaneous_staff.max()
                    avg_simultaneous = simultaneous_staff.mean()
                    utilization_rate = max_simultaneous / total_unique_staff
                    
                    constraints.append(f"最大同時勤務: {max_simultaneous}人 (稼働率: {utilization_rate:.1%})")
                    constraints.append(f"平均同時勤務: {avg_simultaneous:.1f}人")
                    
                    # キャパシティ制約の厳しさ
                    if utilization_rate > 0.8:
                        constraints.append("キャパシティ制約: 厳しい - 人員増員の検討が必要")
                    elif utilization_rate < 0.5:
                        constraints.append("キャパシティ制約: 余裕あり - 効率化の余地")
                    else:
                        constraints.append("キャパシティ制約: 適正レベル")
            
            # 職種別キャパシティ
            if 'role' in long_df.columns and 'staff' in long_df.columns:
                role_capacity = long_df.groupby('role')['staff'].nunique()
                for role, capacity in role_capacity.items():
                    constraints.append(f"{role}キャパシティ: {capacity}人")
                
        except Exception as e:
            log.warning(f"キャパシティ制約抽出エラー: {e}")
            constraints.append("キャパシティ制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["キャパシティに関する制約は検出されませんでした"]
    
    def _extract_demand_pattern_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """需要パターン制約の抽出"""
        constraints = []
        
        try:
            # 繰り返しパターンの検出
            if 'ds' in long_df.columns:
                long_df['date'] = long_df['ds'].dt.date
                daily_pattern = long_df.groupby('date').size()
                
                # 週単位パターン
                long_df['weekday'] = pd.to_datetime(long_df['ds']).dt.day_name()
                weekday_pattern = long_df.groupby('weekday').size()
                
                # 最高・最低需要曜日
                peak_weekday = weekday_pattern.idxmax()
                low_weekday = weekday_pattern.idxmin()
                ratio = weekday_pattern.max() / weekday_pattern.min() if weekday_pattern.min() > 0 else float('inf')
                
                constraints.append(f"週次需要パターン: {peak_weekday}最高, {low_weekday}最低 (比率: {ratio:.1f}倍)")
                
                # 月単位パターン（データが十分にある場合）
                if len(daily_pattern) >= 30:
                    long_df['month'] = pd.to_datetime(long_df['ds']).dt.month
                    monthly_pattern = long_df.groupby('month').size()
                    peak_month = monthly_pattern.idxmax()
                    constraints.append(f"月次需要ピーク: {peak_month}月")
            
            # 時間帯別需要パターン
            if 'ds' in long_df.columns:
                long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                hourly_pattern = long_df.groupby('hour').size()
                peak_hours = hourly_pattern.nlargest(3).index.tolist()
                low_hours = hourly_pattern.nsmallest(3).index.tolist()
                
                constraints.append(f"需要ピーク時間帯: {peak_hours}")
                constraints.append(f"需要低下時間帯: {low_hours}")
                
        except Exception as e:
            log.warning(f"需要パターン制約抽出エラー: {e}")
            constraints.append("需要パターン制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["需要パターンに関する制約は検出されませんでした"]
    
    def _extract_load_leveling_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """負荷平準化制約の抽出"""
        constraints = []
        
        try:
            # 負荷平準化の必要性分析
            if 'ds' in long_df.columns and 'staff' in long_df.columns:
                # 日別負荷の変動
                daily_load = long_df.groupby(long_df['ds'].dt.date)['staff'].nunique()
                if len(daily_load) > 1:
                    load_cv = daily_load.std() / daily_load.mean()
                    
                    if load_cv > 0.3:
                        constraints.append(f"負荷平準化必要: 日別変動CV={load_cv:.2f}")
                        
                        # 平準化の提案
                        high_load_days = daily_load[daily_load > daily_load.mean() + daily_load.std()]
                        low_load_days = daily_load[daily_load < daily_load.mean() - daily_load.std()]
                        
                        if len(high_load_days) > 0 and len(low_load_days) > 0:
                            constraints.append(f"平準化機会: 高負荷日{len(high_load_days)}日 → 低負荷日{len(low_load_days)}日への分散")
                    else:
                        constraints.append(f"負荷平準化良好: 日別変動CV={load_cv:.2f}")
            
            # スタッフ個人レベルの負荷平準化
            if 'staff' in long_df.columns:
                staff_workdays = long_df['staff'].value_counts()
                staff_cv = staff_workdays.std() / staff_workdays.mean() if staff_workdays.mean() > 0 else 0
                
                if staff_cv > 0.5:
                    constraints.append(f"個人負荷平準化必要: スタッフ間変動CV={staff_cv:.2f}")
                else:
                    constraints.append(f"個人負荷平準化良好: スタッフ間変動CV={staff_cv:.2f}")
                
        except Exception as e:
            log.warning(f"負荷平準化制約抽出エラー: {e}")
            constraints.append("負荷平準化制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["負荷平準化に関する制約は検出されませんでした"]
    
    def _generate_human_readable_results(self, mece_facts: Dict[str, List[str]], long_df: pd.DataFrame) -> Dict[str, Any]:
        """人間可読形式の結果生成"""
        
        # 事実総数計算
        total_facts = sum(len(facts) for facts in mece_facts.values())
        
        return {
            '抽出事実サマリー': {
                '総事実数': total_facts,
                '分析軸': f'軸{self.axis_number}: {self.axis_name}',
                '分析対象レコード数': len(long_df),
                'MECEカテゴリー数': len(mece_facts),
                **{category: len(facts) for category, facts in mece_facts.items()}
            },
            'MECE分解事実': mece_facts,
            '確信度別分類': {
                '高確信度事実': [fact for facts in mece_facts.values() for fact in facts if 'CV=' in fact or '人' in fact],
                '中確信度事実': [fact for facts in mece_facts.values() for fact in facts if 'パターン' in fact or '時間' in fact],
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
                constraint_id = f"axis4_{category.lower().replace('制約', '')}_{i+1}"
                
                # 制約の強度判定
                if any(keyword in fact for keyword in ['必要', '最大', '最小', 'キャパシティ']):
                    hard_constraints.append({
                        'id': constraint_id,
                        'type': 'demand_load',
                        'category': category,
                        'description': fact,
                        'priority': 'high',
                        'confidence': 0.8
                    })
                elif any(keyword in fact for keyword in ['改善', '最適化', '効率']):
                    soft_constraints.append({
                        'id': constraint_id,
                        'type': 'demand_load',
                        'category': category,
                        'description': fact,
                        'priority': 'medium',
                        'confidence': 0.6
                    })
                else:
                    preferences.append({
                        'id': constraint_id,
                        'type': 'demand_load',
                        'category': category,
                        'description': fact,
                        'priority': 'low',
                        'confidence': 0.4
                    })
        
        return {
            'hard_constraints': hard_constraints,
            'soft_constraints': soft_constraints,
            'preferences': preferences,
            'constraint_relationships': [],
            'validation_rules': [
                {
                    'rule_id': 'axis4_demand_capacity_check',
                    'description': '需要がキャパシティを超えないことを確認',
                    'validation_type': 'capacity_constraint'
                },
                {
                    'rule_id': 'axis4_load_distribution_check',
                    'description': '負荷分散が適切に行われていることを確認',
                    'validation_type': 'load_balancing'
                }
            ]
        }
    
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
        
        # データ品質指標
        data_quality = {
            'completeness': 1.0 - (long_df.isnull().sum().sum() / (len(long_df) * len(long_df.columns))),
            'record_count': len(long_df),
            'unique_staff_count': long_df['staff'].nunique() if 'staff' in long_df.columns else 0,
            'unique_roles_count': long_df['role'].nunique() if 'role' in long_df.columns else 0,
            'demand_coverage_ratio': len([f for facts in mece_facts.values() for f in facts if '人' in f or 'CV=' in f]) / sum(len(facts) for facts in mece_facts.values()) if sum(len(facts) for facts in mece_facts.values()) > 0 else 0
        }
        
        return {
            'extraction_timestamp': datetime.now().isoformat(),
            'axis_info': {
                'axis_number': self.axis_number,
                'axis_name': self.axis_name,
                'mece_categories': list(mece_facts.keys())
            },
            'data_period': date_range,
            'data_quality': data_quality,
            'extraction_statistics': {
                'total_facts_extracted': sum(len(facts) for facts in mece_facts.values()),
                'high_confidence_facts': len([f for facts in mece_facts.values() for f in facts if 'CV=' in f or '人' in f]),
                'categories_with_facts': len([cat for cat, facts in mece_facts.items() if facts and not any('検出されませんでした' in f for f in facts)])
            }
        }