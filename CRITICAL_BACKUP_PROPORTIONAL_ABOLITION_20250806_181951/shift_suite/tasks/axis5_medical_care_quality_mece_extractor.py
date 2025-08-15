#!/usr/bin/env python3
"""
軸5: 医療・ケア品質 MECE事実抽出エンジン

12軸分析フレームワークの軸5を担当
過去シフト実績から医療・ケア品質向上に関する制約を抽出

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

class MedicalCareQualityMECEFactExtractor:
    """軸5: 医療・ケア品質のMECE事実抽出器"""
    
    def __init__(self):
        self.axis_number = 5
        self.axis_name = "医療・ケア品質"
        
    def extract_axis5_medical_care_quality_rules(self, long_df: pd.DataFrame, wt_df: pd.DataFrame = None) -> Dict[str, Any]:
        """
        軸5: 医療・ケア品質ルールをMECE分解により抽出
        
        Args:
            long_df: 過去のシフト実績データ
            wt_df: 勤務区分マスタ（オプション）
            
        Returns:
            Dict: 抽出結果（human_readable, machine_readable, extraction_metadata）
        """
        log.info(f"🎯 軸5: {self.axis_name} MECE事実抽出を開始")
        
        try:
            # データ品質チェック
            if long_df.empty:
                raise ValueError("長期データが空です")
            
            # 軸5のMECE分解カテゴリー（8つ）
            mece_facts = {
                "医療安全制約": self._extract_medical_safety_constraints(long_df, wt_df),
                "ケア継続性制約": self._extract_care_continuity_constraints(long_df, wt_df),
                "専門性配置制約": self._extract_expertise_placement_constraints(long_df, wt_df),
                "品質監督制約": self._extract_quality_supervision_constraints(long_df, wt_df),
                "利用者適応制約": self._extract_user_adaptation_constraints(long_df, wt_df),
                "医療連携制約": self._extract_medical_coordination_constraints(long_df, wt_df),
                "ケア記録制約": self._extract_care_documentation_constraints(long_df, wt_df),
                "品質向上制約": self._extract_quality_improvement_constraints(long_df, wt_df)
            }
            
            # 人間可読形式の結果生成
            human_readable = self._generate_human_readable_results(mece_facts, long_df)
            
            # 機械可読形式の制約生成
            machine_readable = self._generate_machine_readable_constraints(mece_facts, long_df)
            
            # 抽出メタデータ
            extraction_metadata = self._generate_extraction_metadata(long_df, wt_df, mece_facts)
            
            log.info(f"✅ 軸5: {self.axis_name} MECE事実抽出完了")
            
            return {
                'human_readable': human_readable,
                'machine_readable': machine_readable,
                'extraction_metadata': extraction_metadata
            }
            
        except Exception as e:
            log.error(f"❌ 軸5: {self.axis_name} 抽出エラー: {str(e)}")
            raise e
    
    def _extract_medical_safety_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """医療安全制約の抽出"""
        constraints = []
        
        try:
            # 夜勤帯での複数配置（医療安全）
            if 'code' in long_df.columns and 'ds' in long_df.columns:
                # 夜勤コードを特定
                night_shift_codes = ['夜勤', 'ナイト', 'night', 'N', '夜間']
                night_shifts = long_df[long_df['code'].str.contains('|'.join(night_shift_codes), case=False, na=False)]
                
                if not night_shifts.empty:
                    # 夜勤帯での配置人数分析
                    night_staff_counts = night_shifts.groupby('ds')['staff'].nunique()
                    single_night_days = sum(night_staff_counts == 1)
                    total_night_days = len(night_staff_counts)
                    
                    if single_night_days > 0:
                        safety_risk_ratio = single_night_days / total_night_days
                        constraints.append(f"夜勤単独配置リスク: {single_night_days}/{total_night_days}日 ({safety_risk_ratio:.1%}) - 医療安全のため複数配置推奨")
                    else:
                        constraints.append("夜勤複数配置確保: 医療安全基準遵守")
            
            # 医療資格者の配置パターン
            if 'role' in long_df.columns:
                medical_roles = ['看護師', '准看護師', '医師', 'ナース', 'nurse']
                medical_staff = long_df[long_df['role'].str.contains('|'.join(medical_roles), case=False, na=False)]
                
                if not medical_staff.empty:
                    # 医療資格者の連続勤務パターン
                    if 'ds' in medical_staff.columns and 'staff' in medical_staff.columns:
                        for staff_id in medical_staff['staff'].unique():
                            staff_shifts = medical_staff[medical_staff['staff'] == staff_id]['ds'].sort_values()
                            if len(staff_shifts) > 1:
                                # 連続勤務日数の計算
                                consecutive_days = self._calculate_consecutive_workdays(staff_shifts)
                                if consecutive_days > 5:
                                    constraints.append(f"医療資格者連続勤務: {staff_id} - {consecutive_days}日連続 (疲労による医療安全リスク)")
                
                # 医療資格者の配置頻度
                total_shifts = len(long_df)
                medical_shifts = len(medical_staff)
                medical_coverage = medical_shifts / total_shifts if total_shifts > 0 else 0
                constraints.append(f"医療資格者配置率: {medical_coverage:.1%} - 医療安全確保レベル")
            
            # 緊急時対応可能者の配置
            if 'employment' in long_df.columns and 'role' in long_df.columns:
                # 正規雇用×医療資格の組み合わせ
                regular_medical = long_df[
                    (long_df['employment'].str.contains('正社員|正規|常勤', case=False, na=False)) &
                    (long_df['role'].str.contains('看護師|医師|ナース', case=False, na=False))
                ]
                
                if not regular_medical.empty and 'ds' in long_df.columns:
                    coverage_days = regular_medical['ds'].nunique()
                    total_days = long_df['ds'].nunique()
                    emergency_coverage = coverage_days / total_days if total_days > 0 else 0
                    
                    if emergency_coverage < 0.8:
                        constraints.append(f"緊急対応体制不足: {emergency_coverage:.1%}カバレッジ - 正規医療資格者の配置強化必要")
                    else:
                        constraints.append(f"緊急対応体制良好: {emergency_coverage:.1%}カバレッジ")
                
        except Exception as e:
            log.warning(f"医療安全制約抽出エラー: {e}")
            constraints.append("医療安全制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["医療安全に関する制約は検出されませんでした"]
    
    def _extract_care_continuity_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """ケア継続性制約の抽出"""
        constraints = []
        
        try:
            # 同一利用者担当の継続性分析
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                # スタッフの勤務頻度と継続性
                staff_frequency = long_df['staff'].value_counts()
                regular_staff = staff_frequency[staff_frequency >= 5]  # 5日以上勤務を継続性の基準
                
                continuity_ratio = len(regular_staff) / len(staff_frequency) if len(staff_frequency) > 0 else 0
                constraints.append(f"ケア継続性: {continuity_ratio:.1%}のスタッフが継続勤務 (5日以上)")
                
                # 勤務間隔の分析
                for staff_id in regular_staff.index[:5]:  # 上位5名を分析
                    staff_dates = pd.to_datetime(long_df[long_df['staff'] == staff_id]['ds']).sort_values()
                    if len(staff_dates) > 1:
                        intervals = staff_dates.diff().dt.days.dropna()
                        avg_interval = intervals.mean()
                        if avg_interval <= 2:
                            constraints.append(f"高継続性スタッフ: {staff_id} (平均{avg_interval:.1f}日間隔)")
            
            # シフト引き継ぎパターン
            if 'code' in long_df.columns and 'ds' in long_df.columns and 'staff' in long_df.columns:
                # 日勤→夜勤の引き継ぎ分析
                day_codes = ['日勤', 'デイ', 'day', 'D', '日中']
                night_codes = ['夜勤', 'ナイト', 'night', 'N', '夜間']
                
                day_shifts = long_df[long_df['code'].str.contains('|'.join(day_codes), case=False, na=False)]
                night_shifts = long_df[long_df['code'].str.contains('|'.join(night_codes), case=False, na=False)]
                
                if not day_shifts.empty and not night_shifts.empty:
                    # 同日の引き継ぎパターン
                    for date in day_shifts['ds'].dt.date.unique():
                        day_staff = set(day_shifts[day_shifts['ds'].dt.date == date]['staff'].unique())
                        night_staff = set(night_shifts[night_shifts['ds'].dt.date == date]['staff'].unique())
                        
                        if day_staff and night_staff:
                            overlap = len(day_staff.intersection(night_staff))
                            if overlap > 0:
                                constraints.append(f"引き継ぎ重複: {date} - {overlap}名が日勤・夜勤両方担当 (継続性向上)")
                
                # 週単位での担当者変更頻度
                weekly_changes = self._analyze_weekly_staff_changes(long_df)
                if weekly_changes:
                    avg_changes = np.mean(weekly_changes)
                    constraints.append(f"週次担当者変更: 平均{avg_changes:.1f}名/週 - ケア継続性への影響")
                
        except Exception as e:
            log.warning(f"ケア継続性制約抽出エラー: {e}")
            constraints.append("ケア継続性制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["ケア継続性に関する制約は検出されませんでした"]
    
    def _extract_expertise_placement_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """専門性配置制約の抽出"""
        constraints = []
        
        try:
            # 職種別専門性分析
            if 'role' in long_df.columns:
                role_distribution = long_df['role'].value_counts()
                
                # 専門職種の特定
                specialized_roles = ['看護師', '准看護師', '理学療法士', 'PT', 'OT', '作業療法士', '言語聴覚士', 'ST', '医師']
                specialized_count = 0
                
                for role in role_distribution.index:
                    for spec_role in specialized_roles:
                        if spec_role in role:
                            specialized_count += role_distribution[role]
                            break
                
                total_shifts = len(long_df)
                specialization_ratio = specialized_count / total_shifts if total_shifts > 0 else 0
                constraints.append(f"専門職配置率: {specialization_ratio:.1%} - 専門ケア提供レベル")
                
                # 職種多様性の分析
                role_diversity = len(role_distribution) / total_shifts if total_shifts > 0 else 0
                if role_diversity > 0.1:
                    constraints.append(f"職種多様性高: {len(role_distribution)}職種 - 多角的ケア提供可能")
                else:
                    constraints.append(f"職種集中配置: {len(role_distribution)}職種 - 専門性の集約")
            
            # 時間帯別専門性配置
            if 'role' in long_df.columns and 'ds' in long_df.columns:
                long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                
                # 日中時間帯（9-17時）での専門職配置
                daytime_hours = range(9, 18)
                daytime_shifts = long_df[long_df['hour'].isin(daytime_hours)]
                
                if not daytime_shifts.empty:
                    daytime_roles = daytime_shifts['role'].value_counts()
                    specialized_daytime = sum(
                        count for role, count in daytime_roles.items()
                        if any(spec in role for spec in ['看護師', 'PT', 'OT', 'ST', '療法士'])
                    )
                    daytime_specialization = specialized_daytime / len(daytime_shifts) if len(daytime_shifts) > 0 else 0
                    constraints.append(f"日中専門職配置: {daytime_specialization:.1%} - リハビリ・治療時間帯の専門性")
                
                # 夜間・休日での基本ケア体制
                nighttime_hours = list(range(0, 7)) + list(range(22, 24))
                nighttime_shifts = long_df[long_df['hour'].isin(nighttime_hours)]
                
                if not nighttime_shifts.empty:
                    basic_care_roles = ['介護士', '介護福祉士', 'ヘルパー', '看護師']
                    nighttime_basic_care = sum(
                        nighttime_shifts['role'].str.contains(role, case=False, na=False).sum()
                        for role in basic_care_roles
                    )
                    nighttime_coverage = nighttime_basic_care / len(nighttime_shifts) if len(nighttime_shifts) > 0 else 0
                    constraints.append(f"夜間基本ケア配置: {nighttime_coverage:.1%} - 安全・快適な夜間ケア")
            
            # 経験年数・雇用形態と専門性の関係
            if 'employment' in long_df.columns and 'role' in long_df.columns:
                # 正規雇用での専門職比率
                regular_staff = long_df[long_df['employment'].str.contains('正社員|正規|常勤', case=False, na=False)]
                if not regular_staff.empty:
                    regular_specialized = sum(
                        regular_staff['role'].str.contains(role, case=False, na=False).sum()
                        for role in ['看護師', '療法士', 'PT', 'OT', 'ST']
                    )
                    regular_specialization = regular_specialized / len(regular_staff) if len(regular_staff) > 0 else 0
                    constraints.append(f"正規雇用専門職率: {regular_specialization:.1%} - 専門性の安定確保")
                
        except Exception as e:
            log.warning(f"専門性配置制約抽出エラー: {e}")
            constraints.append("専門性配置制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["専門性配置に関する制約は検出されませんでした"]
    
    def _extract_quality_supervision_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """品質監督制約の抽出"""
        constraints = []
        
        try:
            # 管理者・リーダーの配置分析
            if 'role' in long_df.columns:
                supervisor_roles = ['主任', 'リーダー', '管理者', '師長', 'チーフ', '統括', 'supervisor', 'manager']
                supervisors = long_df[
                    long_df['role'].str.contains('|'.join(supervisor_roles), case=False, na=False)
                ]
                
                if not supervisors.empty:
                    # 監督者の勤務頻度
                    if 'ds' in long_df.columns:
                        total_days = long_df['ds'].nunique()
                        supervisor_days = supervisors['ds'].nunique()
                        supervision_coverage = supervisor_days / total_days if total_days > 0 else 0
                        
                        constraints.append(f"監督者配置率: {supervision_coverage:.1%} - 品質管理体制")
                        
                        if supervision_coverage < 0.7:
                            constraints.append("監督体制強化必要: 品質監督が不十分な日が存在")
                        else:
                            constraints.append("監督体制良好: 継続的な品質管理実現")
                
                # 監督者と一般スタッフの比率
                total_staff_shifts = len(long_df)
                supervisor_shifts = len(supervisors)
                supervision_ratio = supervisor_shifts / total_staff_shifts if total_staff_shifts > 0 else 0
                
                if supervision_ratio < 0.1:
                    constraints.append(f"監督者比率低: {supervision_ratio:.1%} - 監督体制の充実が必要")
                elif supervision_ratio > 0.3:
                    constraints.append(f"監督者比率高: {supervision_ratio:.1%} - 管理コスト要検討")
                else:
                    constraints.append(f"監督者比率適正: {supervision_ratio:.1%}")
            
            # 品質チェック体制（シフト重複による確認）
            if 'ds' in long_df.columns and 'staff' in long_df.columns:
                # 同日複数スタッフでの相互チェック可能性
                daily_staff_counts = long_df.groupby('ds')['staff'].nunique()
                multi_staff_days = sum(daily_staff_counts >= 2)
                total_days = len(daily_staff_counts)
                
                quality_check_coverage = multi_staff_days / total_days if total_days > 0 else 0
                constraints.append(f"相互チェック可能日: {quality_check_coverage:.1%} - 品質確認体制")
                
                # 3名以上での高品質チェック
                high_quality_days = sum(daily_staff_counts >= 3)
                high_quality_coverage = high_quality_days / total_days if total_days > 0 else 0
                if high_quality_coverage > 0.5:
                    constraints.append(f"高品質チェック体制: {high_quality_coverage:.1%}の日で3名以上配置")
            
            # 新人・ベテラン混在による品質向上
            if 'employment' in long_df.columns:
                # 雇用形態での経験推定
                veteran_types = ['正社員', '正規', '常勤']
                newcomer_types = ['パート', 'アルバイト', '非常勤', '派遣']
                
                veteran_shifts = sum(
                    long_df['employment'].str.contains(vet_type, case=False, na=False).sum()
                    for vet_type in veteran_types
                )
                newcomer_shifts = sum(
                    long_df['employment'].str.contains(new_type, case=False, na=False).sum()
                    for new_type in newcomer_types
                )
                
                if veteran_shifts > 0 and newcomer_shifts > 0:
                    veteran_ratio = veteran_shifts / (veteran_shifts + newcomer_shifts)
                    if 0.3 <= veteran_ratio <= 0.7:
                        constraints.append(f"ベテラン・新人バランス良好: ベテラン{veteran_ratio:.1%} - 教育・品質向上環境")
                    elif veteran_ratio < 0.3:
                        constraints.append(f"ベテラン不足: {veteran_ratio:.1%} - 品質指導体制の強化必要")
                    else:
                        constraints.append(f"ベテラン過多: {veteran_ratio:.1%} - 新人育成機会の確保必要")
                
        except Exception as e:
            log.warning(f"品質監督制約抽出エラー: {e}")
            constraints.append("品質監督制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["品質監督に関する制約は検出されませんでした"]
    
    def _extract_user_adaptation_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """利用者適応制約の抽出"""
        constraints = []
        
        try:
            # 担当者変更頻度による利用者への影響
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                # 週ごとの担当者変更パターン
                long_df['week'] = pd.to_datetime(long_df['ds']).dt.isocalendar().week
                weekly_staff_changes = []
                
                for week in long_df['week'].unique():
                    week_data = long_df[long_df['week'] == week]
                    unique_staff = week_data['staff'].nunique()
                    weekly_staff_changes.append(unique_staff)
                
                if weekly_staff_changes:
                    avg_weekly_changes = np.mean(weekly_staff_changes)
                    if avg_weekly_changes > 10:
                        constraints.append(f"担当者変更頻度高: 週平均{avg_weekly_changes:.1f}名 - 利用者の適応負担大")
                    elif avg_weekly_changes < 5:
                        constraints.append(f"担当者固定度高: 週平均{avg_weekly_changes:.1f}名 - 利用者の安心感向上")
                    else:
                        constraints.append(f"担当者変更適度: 週平均{avg_weekly_changes:.1f}名")
            
            # 時間帯別ケア提供の一貫性
            if 'ds' in long_df.columns and 'staff' in long_df.columns:
                long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                
                # 朝・昼・夕・夜の主要時間帯での担当者分析
                time_periods = {
                    '朝': [6, 7, 8, 9],
                    '昼': [11, 12, 13, 14],
                    '夕': [17, 18, 19, 20],
                    '夜': [21, 22, 23, 0]
                }
                
                for period_name, hours in time_periods.items():
                    period_data = long_df[long_df['hour'].isin(hours)]
                    if not period_data.empty:
                        period_staff_consistency = period_data['staff'].value_counts()
                        most_frequent_staff = period_staff_consistency.iloc[0] if len(period_staff_consistency) > 0 else 0
                        total_period_shifts = len(period_data)
                        consistency_ratio = most_frequent_staff / total_period_shifts if total_period_shifts > 0 else 0
                        
                        if consistency_ratio > 0.5:
                            constraints.append(f"{period_name}時間帯一貫性高: {consistency_ratio:.1%} - 利用者の生活リズム安定")
                        else:
                            constraints.append(f"{period_name}時間帯変動大: {consistency_ratio:.1%} - 適応支援必要")
            
            # 利用者特性に応じた配置（推定）
            if 'role' in long_df.columns:
                # 認知症ケア専門性
                dementia_care_roles = ['認知症', 'デイサービス', '訪問', 'グループホーム']
                dementia_specialists = long_df[
                    long_df['role'].str.contains('|'.join(dementia_care_roles), case=False, na=False)
                ]
                
                if not dementia_specialists.empty:
                    dementia_care_ratio = len(dementia_specialists) / len(long_df)
                    constraints.append(f"認知症ケア専門配置: {dementia_care_ratio:.1%} - 特性に応じたケア提供")
                
                # 重度ケア対応
                intensive_care_roles = ['看護師', '医師', '准看護師']
                intensive_care_staff = long_df[
                    long_df['role'].str.contains('|'.join(intensive_care_roles), case=False, na=False)
                ]
                
                if not intensive_care_staff.empty:
                    intensive_care_ratio = len(intensive_care_staff) / len(long_df)
                    constraints.append(f"重度ケア対応配置: {intensive_care_ratio:.1%} - 医療ニーズへの対応")
                
        except Exception as e:
            log.warning(f"利用者適応制約抽出エラー: {e}")
            constraints.append("利用者適応制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["利用者適応に関する制約は検出されませんでした"]
    
    def _extract_medical_coordination_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """医療連携制約の抽出"""
        constraints = []
        
        try:
            # 医療職種間の連携パターン
            if 'role' in long_df.columns and 'ds' in long_df.columns:
                medical_roles = ['看護師', '准看護師', '医師', '薬剤師', '理学療法士', '作業療法士']
                
                # 同日勤務での医療職種連携
                daily_medical_teams = []
                for date in long_df['ds'].dt.date.unique():
                    daily_data = long_df[long_df['ds'].dt.date == date]
                    daily_medical_roles = []
                    
                    for role in medical_roles:
                        if daily_data['role'].str.contains(role, case=False, na=False).any():
                            daily_medical_roles.append(role)
                    
                    if len(daily_medical_roles) >= 2:
                        daily_medical_teams.append(len(daily_medical_roles))
                
                if daily_medical_teams:
                    avg_team_size = np.mean(daily_medical_teams)
                    coordination_days = len(daily_medical_teams)
                    total_days = long_df['ds'].dt.date.nunique()
                    coordination_ratio = coordination_days / total_days if total_days > 0 else 0
                    
                    constraints.append(f"医療チーム連携: {coordination_ratio:.1%}の日で複数医療職配置 (平均{avg_team_size:.1f}職種)")
                    
                    if coordination_ratio > 0.7:
                        constraints.append("医療連携体制充実: 包括的ケア提供可能")
                    else:
                        constraints.append("医療連携強化必要: 職種間協働の向上余地")
            
            # 看護師とリハビリ専門職の協働
            if 'role' in long_df.columns and 'ds' in long_df.columns:
                nursing_staff = long_df[long_df['role'].str.contains('看護師', case=False, na=False)]
                rehab_staff = long_df[long_df['role'].str.contains('理学療法士|作業療法士|PT|OT|ST', case=False, na=False)]
                
                if not nursing_staff.empty and not rehab_staff.empty:
                    # 同日配置での協働機会
                    nursing_dates = set(nursing_staff['ds'].dt.date)
                    rehab_dates = set(rehab_staff['ds'].dt.date)
                    collaboration_dates = nursing_dates.intersection(rehab_dates)
                    
                    collaboration_ratio = len(collaboration_dates) / len(nursing_dates.union(rehab_dates)) if nursing_dates.union(rehab_dates) else 0
                    constraints.append(f"看護・リハビリ協働: {collaboration_ratio:.1%} - 総合的ケア計画実施")
            
            # 医療情報共有のためのシフト重複
            if 'ds' in long_df.columns and 'staff' in long_df.columns:
                # シフト重複時間での情報共有機会
                overlap_opportunities = 0
                total_shift_transitions = 0
                
                for date in long_df['ds'].dt.date.unique():
                    daily_shifts = long_df[long_df['ds'].dt.date == date]
                    if len(daily_shifts) > 1:
                        # 時間帯重複の推定
                        morning_shift = daily_shifts[daily_shifts['ds'].dt.hour < 12]
                        afternoon_shift = daily_shifts[daily_shifts['ds'].dt.hour >= 12]
                        
                        if not morning_shift.empty and not afternoon_shift.empty:
                            total_shift_transitions += 1
                            
                            # スタッフの重複確認
                            morning_staff = set(morning_shift['staff'])
                            afternoon_staff = set(afternoon_shift['staff'])
                            if morning_staff.intersection(afternoon_staff):
                                overlap_opportunities += 1
                
                if total_shift_transitions > 0:
                    overlap_ratio = overlap_opportunities / total_shift_transitions
                    constraints.append(f"シフト引き継ぎ重複: {overlap_ratio:.1%} - 医療情報共有機会")
                
        except Exception as e:
            log.warning(f"医療連携制約抽出エラー: {e}")
            constraints.append("医療連携制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["医療連携に関する制約は検出されませんでした"]
    
    def _extract_care_documentation_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """ケア記録制約の抽出"""
        constraints = []
        
        try:
            # 記録作成に必要な時間確保（シフト長分析）
            if 'ds' in long_df.columns:
                # 勤務時間の推定（同一日の最大・最小時間差）
                long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                
                daily_shift_spans = []
                for date in long_df['ds'].dt.date.unique():
                    daily_data = long_df[long_df['ds'].dt.date == date]
                    if len(daily_data) > 1:
                        min_hour = daily_data['hour'].min()
                        max_hour = daily_data['hour'].max()
                        span = max_hour - min_hour
                        daily_shift_spans.append(span)
                
                if daily_shift_spans:
                    avg_shift_span = np.mean(daily_shift_spans)
                    if avg_shift_span >= 8:
                        constraints.append(f"記録作成時間確保: 平均{avg_shift_span:.1f}時間勤務 - 十分な記録時間")
                    else:
                        constraints.append(f"記録時間制限: 平均{avg_shift_span:.1f}時間勤務 - 効率的記録作成必要")
            
            # 記録責任者の配置
            if 'role' in long_df.columns:
                documentation_roles = ['看護師', '准看護師', '管理者', '主任', 'リーダー']
                record_keepers = long_df[
                    long_df['role'].str.contains('|'.join(documentation_roles), case=False, na=False)
                ]
                
                if not record_keepers.empty:
                    record_coverage = len(record_keepers) / len(long_df)
                    constraints.append(f"記録責任者配置: {record_coverage:.1%} - ケア記録の品質確保")
                    
                    # 記録責任者の勤務継続性
                    if 'ds' in long_df.columns:
                        record_keeper_days = record_keepers['ds'].dt.date.nunique()
                        total_days = long_df['ds'].dt.date.nunique()
                        documentation_continuity = record_keeper_days / total_days if total_days > 0 else 0
                        
                        if documentation_continuity > 0.8:
                            constraints.append("記録継続性良好: 一貫したケア記録管理")
                        else:
                            constraints.append(f"記録継続性要改善: {documentation_continuity:.1%}カバレッジ")
            
            # 多職種記録の必要性
            if 'role' in long_df.columns and 'ds' in long_df.columns:
                # 日別の職種多様性
                daily_role_diversity = []
                for date in long_df['ds'].dt.date.unique():
                    daily_data = long_df[long_df['ds'].dt.date == date]
                    unique_roles = daily_data['role'].nunique()
                    daily_role_diversity.append(unique_roles)
                
                if daily_role_diversity:
                    avg_role_diversity = np.mean(daily_role_diversity)
                    if avg_role_diversity >= 3:
                        constraints.append(f"多職種記録必要: 平均{avg_role_diversity:.1f}職種/日 - 包括的記録作成")
                    else:
                        constraints.append(f"職種集約記録: 平均{avg_role_diversity:.1f}職種/日 - 効率的記録管理")
                
        except Exception as e:
            log.warning(f"ケア記録制約抽出エラー: {e}")
            constraints.append("ケア記録制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["ケア記録に関する制約は検出されませんでした"]
    
    def _extract_quality_improvement_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """品質向上制約の抽出"""
        constraints = []
        
        try:
            # 研修・教育機会の確保（ベテラン・新人混在分析）
            if 'employment' in long_df.columns and 'ds' in long_df.columns:
                # 雇用形態による経験推定
                experienced_types = ['正社員', '正規', '常勤']
                learning_types = ['パート', 'アルバイト', '非常勤']
                
                # 同日配置での教育機会
                education_days = 0
                total_days = long_df['ds'].dt.date.nunique()
                
                for date in long_df['ds'].dt.date.unique():
                    daily_data = long_df[long_df['ds'].dt.date == date]
                    
                    has_experienced = daily_data['employment'].str.contains('|'.join(experienced_types), case=False, na=False).any()
                    has_learning = daily_data['employment'].str.contains('|'.join(learning_types), case=False, na=False).any()
                    
                    if has_experienced and has_learning:
                        education_days += 1
                
                education_ratio = education_days / total_days if total_days > 0 else 0
                constraints.append(f"教育機会提供: {education_ratio:.1%}の日でベテラン・新人混在 - 技能向上環境")
                
                if education_ratio > 0.6:
                    constraints.append("継続的教育体制: 品質向上の基盤確立")
                else:
                    constraints.append("教育機会拡大必要: 混在配置の増加検討")
            
            # 品質改善のための振り返り時間
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                # 同一スタッフの連続勤務での振り返り機会
                reflection_opportunities = 0
                
                for staff_id in long_df['staff'].unique():
                    staff_dates = pd.to_datetime(long_df[long_df['staff'] == staff_id]['ds']).sort_values()
                    if len(staff_dates) > 1:
                        consecutive_periods = self._find_consecutive_work_periods(staff_dates)
                        reflection_opportunities += len([p for p in consecutive_periods if p >= 3])  # 3日以上連続
                
                total_staff = long_df['staff'].nunique()
                reflection_ratio = reflection_opportunities / total_staff if total_staff > 0 else 0
                constraints.append(f"振り返り機会: {reflection_ratio:.1%}のスタッフに連続勤務期間 - 継続的改善")
            
            # 品質指標モニタリング体制
            if 'role' in long_df.columns:
                # 品質管理担当者の配置
                quality_roles = ['主任', 'リーダー', '品質', 'QC', '管理者', '統括']
                quality_staff = long_df[
                    long_df['role'].str.contains('|'.join(quality_roles), case=False, na=False)
                ]
                
                if not quality_staff.empty:
                    quality_monitoring_ratio = len(quality_staff) / len(long_df)
                    constraints.append(f"品質監視体制: {quality_monitoring_ratio:.1%} - 継続的品質改善")
                    
                    # 品質管理者の定期配置
                    if 'ds' in long_df.columns:
                        quality_coverage_days = quality_staff['ds'].dt.date.nunique()
                        total_days = long_df['ds'].dt.date.nunique()
                        quality_coverage = quality_coverage_days / total_days if total_days > 0 else 0
                        
                        if quality_coverage > 0.5:
                            constraints.append("定期品質監視: 継続的改善体制確立")
                        else:
                            constraints.append("品質監視強化必要: 定期的なモニタリング体制構築")
            
            # イノベーション・改善提案の環境
            if 'role' in long_df.columns and 'employment' in long_df.columns:
                # 多様な背景を持つスタッフの混在
                role_variety = long_df['role'].nunique()
                employment_variety = long_df['employment'].nunique()
                
                diversity_score = (role_variety + employment_variety) / len(long_df) * 100
                if diversity_score > 10:
                    constraints.append(f"多様性環境: スコア{diversity_score:.1f} - イノベーション創出可能")
                else:
                    constraints.append(f"均質性環境: スコア{diversity_score:.1f} - 安定性重視")
                
        except Exception as e:
            log.warning(f"品質向上制約抽出エラー: {e}")
            constraints.append("品質向上制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["品質向上に関する制約は検出されませんでした"]
    
    def _calculate_consecutive_workdays(self, dates: pd.Series) -> int:
        """連続勤務日数の計算"""
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
    
    def _analyze_weekly_staff_changes(self, long_df: pd.DataFrame) -> List[int]:
        """週次スタッフ変更数の分析"""
        if 'ds' not in long_df.columns or 'staff' not in long_df.columns:
            return []
        
        long_df['week'] = pd.to_datetime(long_df['ds']).dt.isocalendar().week
        weekly_changes = []
        
        weeks = sorted(long_df['week'].unique())
        for i in range(1, len(weeks)):
            prev_week_staff = set(long_df[long_df['week'] == weeks[i-1]]['staff'])
            curr_week_staff = set(long_df[long_df['week'] == weeks[i]]['staff'])
            
            # 新規追加されたスタッフ数
            new_staff = len(curr_week_staff - prev_week_staff)
            weekly_changes.append(new_staff)
        
        return weekly_changes
    
    def _find_consecutive_work_periods(self, dates: pd.Series) -> List[int]:
        """連続勤務期間の発見"""
        if len(dates) <= 1:
            return [len(dates)]
        
        sorted_dates = sorted(dates)
        periods = []
        current_period = 1
        
        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
                current_period += 1
            else:
                periods.append(current_period)
                current_period = 1
        
        periods.append(current_period)
        return periods
    
    def _generate_human_readable_results(self, mece_facts: Dict[str, List[str]], long_df: pd.DataFrame) -> Dict[str, Any]:
        """人間可読形式の結果生成"""
        
        # 事実総数計算
        total_facts = sum(len(facts) for facts in mece_facts.values())
        
        # 品質重要度別分類
        high_importance = [fact for facts in mece_facts.values() for fact in facts if any(keyword in fact for keyword in ['安全', '継続', '専門', '監督'])]
        medium_importance = [fact for facts in mece_facts.values() for fact in facts if any(keyword in fact for keyword in ['連携', '記録', '適応'])]
        improvement_focus = [fact for facts in mece_facts.values() for fact in facts if any(keyword in fact for keyword in ['向上', '改善', '教育', '品質'])]
        
        return {
            '抽出事実サマリー': {
                '総事実数': total_facts,
                '分析軸': f'軸{self.axis_number}: {self.axis_name}',
                '分析対象レコード数': len(long_df),
                'MECEカテゴリー数': len(mece_facts),
                **{category: len(facts) for category, facts in mece_facts.items()}
            },
            'MECE分解事実': mece_facts,
            '品質重要度別分類': {
                '高重要度事実（安全・継続性）': high_importance,
                '中重要度事実（連携・記録）': medium_importance,
                '改善重点事実（向上・教育）': improvement_focus,
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
                constraint_id = f"axis5_{category.lower().replace('制約', '')}_{i+1}"
                
                # 医療・ケア品質の制約強度判定
                if any(keyword in fact for keyword in ['安全', '必要', '監督', '継続性', '専門']):
                    hard_constraints.append({
                        'id': constraint_id,
                        'type': 'medical_care_quality',
                        'category': category,
                        'description': fact,
                        'priority': 'high',
                        'confidence': 0.9,
                        'quality_aspect': self._categorize_quality_aspect(fact)
                    })
                elif any(keyword in fact for keyword in ['改善', '向上', '最適化', '教育', '連携']):
                    soft_constraints.append({
                        'id': constraint_id,
                        'type': 'medical_care_quality',
                        'category': category,
                        'description': fact,
                        'priority': 'medium',
                        'confidence': 0.7,
                        'quality_aspect': self._categorize_quality_aspect(fact)
                    })
                else:
                    preferences.append({
                        'id': constraint_id,
                        'type': 'medical_care_quality',
                        'category': category,
                        'description': fact,
                        'priority': 'low',
                        'confidence': 0.5,
                        'quality_aspect': self._categorize_quality_aspect(fact)
                    })
        
        return {
            'hard_constraints': hard_constraints,
            'soft_constraints': soft_constraints,
            'preferences': preferences,
            'constraint_relationships': [
                {
                    'relationship_id': 'safety_supervision_dependency',
                    'type': 'requires',
                    'from_category': '医療安全制約',
                    'to_category': '品質監督制約',
                    'description': '医療安全の確保には品質監督が必要'
                },
                {
                    'relationship_id': 'continuity_expertise_synergy',
                    'type': 'enhances',
                    'from_category': 'ケア継続性制約',
                    'to_category': '専門性配置制約',
                    'description': 'ケア継続性と専門性配置の相乗効果'
                }
            ],
            'validation_rules': [
                {
                    'rule_id': 'axis5_medical_safety_check',
                    'description': '医療安全基準が満たされていることを確認',
                    'validation_type': 'safety_compliance'
                },
                {
                    'rule_id': 'axis5_care_continuity_check',
                    'description': 'ケア継続性が適切に保たれていることを確認',
                    'validation_type': 'continuity_maintenance'
                },
                {
                    'rule_id': 'axis5_quality_supervision_check',
                    'description': '品質監督体制が機能していることを確認',
                    'validation_type': 'quality_oversight'
                }
            ]
        }
    
    def _categorize_quality_aspect(self, fact: str) -> str:
        """品質側面の分類"""
        if any(keyword in fact for keyword in ['安全', 'safety', '医療安全']):
            return 'safety'
        elif any(keyword in fact for keyword in ['継続', '一貫', 'continuity']):
            return 'continuity'
        elif any(keyword in fact for keyword in ['専門', '技能', 'expertise']):
            return 'expertise'
        elif any(keyword in fact for keyword in ['監督', '管理', 'supervision']):
            return 'supervision'
        elif any(keyword in fact for keyword in ['連携', '協働', 'coordination']):
            return 'coordination'
        elif any(keyword in fact for keyword in ['記録', '文書', 'documentation']):
            return 'documentation'
        elif any(keyword in fact for keyword in ['改善', '向上', 'improvement']):
            return 'improvement'
        else:
            return 'general'
    
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
        
        # 医療・ケア品質指標
        quality_indicators = {
            'medical_staff_ratio': len(long_df[long_df['role'].str.contains('看護師|医師', case=False, na=False)]) / len(long_df) if len(long_df) > 0 else 0,
            'specialized_care_coverage': len([f for facts in mece_facts.values() for f in facts if '専門' in f]) / sum(len(facts) for facts in mece_facts.values()) if sum(len(facts) for facts in mece_facts.values()) > 0 else 0,
            'safety_concern_ratio': len([f for facts in mece_facts.values() for f in facts if '安全' in f or 'リスク' in f]) / sum(len(facts) for facts in mece_facts.values()) if sum(len(facts) for facts in mece_facts.values()) > 0 else 0
        }
        
        # データ品質指標
        data_quality = {
            'completeness': 1.0 - (long_df.isnull().sum().sum() / (len(long_df) * len(long_df.columns))),
            'record_count': len(long_df),
            'unique_staff_count': long_df['staff'].nunique() if 'staff' in long_df.columns else 0,
            'unique_roles_count': long_df['role'].nunique() if 'role' in long_df.columns else 0,
            'quality_focus_ratio': len([f for facts in mece_facts.values() for f in facts if any(q in f for q in ['品質', '安全', '継続', '専門'])]) / sum(len(facts) for facts in mece_facts.values()) if sum(len(facts) for facts in mece_facts.values()) > 0 else 0
        }
        
        return {
            'extraction_timestamp': datetime.now().isoformat(),
            'axis_info': {
                'axis_number': self.axis_number,
                'axis_name': self.axis_name,
                'mece_categories': list(mece_facts.keys()),
                'focus_area': '医療・ケア品質向上制約'
            },
            'data_period': date_range,
            'quality_indicators': quality_indicators,
            'data_quality': data_quality,
            'extraction_statistics': {
                'total_facts_extracted': sum(len(facts) for facts in mece_facts.values()),
                'safety_related_facts': len([f for facts in mece_facts.values() for f in facts if '安全' in f]),
                'quality_improvement_facts': len([f for facts in mece_facts.values() for f in facts if '改善' in f or '向上' in f]),
                'categories_with_facts': len([cat for cat, facts in mece_facts.items() if facts and not any('検出されませんでした' in f for f in facts)])
            }
        }