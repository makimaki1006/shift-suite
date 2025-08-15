#!/usr/bin/env python3
"""
軸7: 法的・規制要件 MECE事実抽出エンジン

12軸分析フレームワークの軸7を担当
過去シフト実績から法的・規制要件への適合性に関する制約を抽出
他の全軸の基盤となる最高優先度制約

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

class LegalRegulatoryMECEFactExtractor:
    """軸7: 法的・規制要件のMECE事実抽出器"""
    
    def __init__(self):
        self.axis_number = 7
        self.axis_name = "法的・規制要件"
        
        # 法的基準値（日本の労働基準法等に基づく）
        self.legal_standards = {
            'max_weekly_hours': 40,  # 週40時間制限
            'max_daily_hours': 8,    # 日8時間制限  
            'min_rest_between_shifts': 11,  # 勤務間インターバル（努力義務）
            'max_continuous_work_days': 6,   # 連続勤務日数制限
            'min_weekly_rest_hours': 24,    # 週休（最低24時間）
            'night_shift_start': 22,        # 夜勤開始時刻
            'night_shift_end': 5,           # 夜勤終了時刻
            'overtime_threshold': 8,        # 残業開始時間
            'max_monthly_overtime': 45      # 月間残業上限（36協定）
        }
        
    def extract_axis7_legal_regulatory_rules(self, long_df: pd.DataFrame, wt_df: pd.DataFrame = None) -> Dict[str, Any]:
        """
        軸7: 法的・規制要件ルールをMECE分解により抽出
        
        Args:
            long_df: 過去のシフト実績データ
            wt_df: 勤務区分マスタ（オプション）
            
        Returns:
            Dict: 抽出結果（human_readable, machine_readable, extraction_metadata）
        """
        log.info(f"⚖️ 軸7: {self.axis_name} MECE事実抽出を開始")
        
        try:
            # データ品質チェック
            if long_df.empty:
                raise ValueError("長期データが空です")
            
            # 軸7のMECE分解カテゴリー（8つ）
            mece_facts = {
                "労働時間制約": self._extract_working_hours_constraints(long_df, wt_df),
                "休憩・休日制約": self._extract_rest_break_constraints(long_df, wt_df),
                "人員配置基準制約": self._extract_staffing_standard_constraints(long_df, wt_df),
                "資格・免許制約": self._extract_qualification_license_constraints(long_df, wt_df),
                "安全衛生制約": self._extract_safety_health_constraints(long_df, wt_df),
                "記録・報告制約": self._extract_documentation_reporting_constraints(long_df, wt_df),
                "契約・雇用制約": self._extract_employment_contract_constraints(long_df, wt_df),
                "規制遵守制約": self._extract_regulatory_compliance_constraints(long_df, wt_df)
            }
            
            # 人間可読形式の結果生成
            human_readable = self._generate_human_readable_results(mece_facts, long_df)
            
            # 機械可読形式の制約生成（法的制約は最高優先度）
            machine_readable = self._generate_machine_readable_constraints(mece_facts, long_df)
            
            # 抽出メタデータ
            extraction_metadata = self._generate_extraction_metadata(long_df, wt_df, mece_facts)
            
            log.info(f"✅ 軸7: {self.axis_name} MECE事実抽出完了")
            
            return {
                'human_readable': human_readable,
                'machine_readable': machine_readable,
                'extraction_metadata': extraction_metadata
            }
            
        except Exception as e:
            log.error(f"❌ 軸7: {self.axis_name} 抽出エラー: {str(e)}")
            raise e
    
    def _extract_working_hours_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """労働時間制約の抽出"""
        constraints = []
        
        try:
            # 労働基準法第32条: 週40時間制限
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                long_df['week'] = pd.to_datetime(long_df['ds']).dt.isocalendar().week
                long_df['year'] = pd.to_datetime(long_df['ds']).dt.year
                
                # 週次労働時間分析
                weekly_violations = []
                for staff_id in long_df['staff'].unique():
                    staff_data = long_df[long_df['staff'] == staff_id]
                    weekly_hours = staff_data.groupby(['year', 'week']).size()
                    
                    # 週40時間超過の検出（1日8時間想定）
                    violations = weekly_hours[weekly_hours > 5]  # 5日×8時間=40時間
                    if len(violations) > 0:
                        max_violation = violations.max()
                        weekly_violations.append((staff_id, max_violation, len(violations)))
                
                if weekly_violations:
                    violation_ratio = len(weekly_violations) / long_df['staff'].nunique()
                    avg_violation_days = np.mean([days for _, days, _ in weekly_violations])
                    constraints.append(f"週40時間制限違反: {violation_ratio:.1%}のスタッフ (平均{avg_violation_days:.1f}日/週)")
                    constraints.append("【法的リスク】労働基準法第32条違反の可能性 - 即座の是正必要")
                else:
                    constraints.append("週40時間制限遵守: 労働基準法第32条適合")
            
            # 労働基準法第32条の2: 日8時間制限
            if 'ds' in long_df.columns and 'staff' in long_df.columns:
                # 日別勤務時間の推定分析
                daily_shift_counts = long_df.groupby(['ds', 'staff']).size()
                
                # 1日2シフト以上を長時間勤務とみなす
                long_shift_days = daily_shift_counts[daily_shift_counts >= 2]
                
                if len(long_shift_days) > 0:
                    total_staff_days = daily_shift_counts.count()
                    long_shift_ratio = len(long_shift_days) / total_staff_days
                    constraints.append(f"長時間勤務検出: {long_shift_ratio:.1%} (複数シフト担当)")
                    
                    if long_shift_ratio > 0.1:
                        constraints.append("【法的リスク】日8時間制限超過の可能性 - 勤務時間記録確認必要")
                else:
                    constraints.append("日8時間制限適合: 単一シフト勤務体制")
            
            # 36協定（時間外労働制限）
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                long_df['month'] = pd.to_datetime(long_df['ds']).dt.to_period('M')
                
                # 月間勤務日数分析（22日を基準とする）
                monthly_workdays = long_df.groupby(['staff', 'month']).size()
                overtime_months = monthly_workdays[monthly_workdays > 22]  # 22日×8時間=176時間
                
                if len(overtime_months) > 0:
                    overtime_staff_ratio = overtime_months.index.get_level_values('staff').nunique() / long_df['staff'].nunique()
                    avg_overtime_days = overtime_months.mean() - 22
                    constraints.append(f"月間残業推定: {overtime_staff_ratio:.1%}のスタッフ (平均{avg_overtime_days:.1f}日超過)")
                    constraints.append("【法的リスク】36協定確認必要 - 時間外労働上限遵守")
                else:
                    constraints.append("月間労働時間適正: 36協定範囲内と推定")
                
        except Exception as e:
            log.warning(f"労働時間制約抽出エラー: {e}")
            constraints.append("労働時間制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["労働時間に関する制約は検出されませんでした"]
    
    def _extract_rest_break_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """休憩・休日制約の抽出"""
        constraints = []
        
        try:
            # 労働基準法第35条: 週休制
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                long_df['week'] = pd.to_datetime(long_df['ds']).dt.isocalendar().week
                long_df['year'] = pd.to_datetime(long_df['ds']).dt.year
                
                # 週7日連続勤務の検出
                weekly_violations = []
                for staff_id in long_df['staff'].unique():
                    staff_data = long_df[long_df['staff'] == staff_id]
                    weekly_workdays = staff_data.groupby(['year', 'week']).size()
                    
                    # 週7日勤務（週休なし）の検出
                    no_rest_weeks = weekly_workdays[weekly_workdays >= 7]
                    if len(no_rest_weeks) > 0:
                        weekly_violations.append((staff_id, len(no_rest_weeks)))
                
                if weekly_violations:
                    violation_ratio = len(weekly_violations) / long_df['staff'].nunique()
                    constraints.append(f"週休制違反: {violation_ratio:.1%}のスタッフで週7日勤務")
                    constraints.append("【法的リスク】労働基準法第35条違反 - 週1日の休日確保必要")
                else:
                    constraints.append("週休制遵守: 労働基準法第35条適合")
            
            # 勤務間インターバル（努力義務）
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                # 連続勤務日の分析
                interval_violations = []
                
                for staff_id in long_df['staff'].unique():
                    staff_dates = pd.to_datetime(long_df[long_df['staff'] == staff_id]['ds']).sort_values()
                    
                    if len(staff_dates) > 1:
                        # 連続勤務の検出
                        consecutive_periods = self._find_consecutive_work_periods(staff_dates)
                        long_consecutive = [p for p in consecutive_periods if p >= 7]  # 7日以上連続
                        
                        if long_consecutive:
                            interval_violations.append((staff_id, max(long_consecutive)))
                
                if interval_violations:
                    violation_ratio = len(interval_violations) / long_df['staff'].nunique()
                    max_consecutive = max([days for _, days in interval_violations])
                    constraints.append(f"長期連続勤務: {violation_ratio:.1%}のスタッフ (最大{max_consecutive}日連続)")
                    
                    if max_consecutive >= 10:
                        constraints.append("【健康リスク】過度の連続勤務 - 勤務間インターバル確保推奨")
                else:
                    constraints.append("勤務間隔適正: 過度の連続勤務なし")
            
            # 夜勤従事者の特別休憩（深夜業に関する制約）
            if 'ds' in long_df.columns and 'code' in long_df.columns:
                # 夜勤シフトの特定
                night_shift_codes = ['夜勤', 'ナイト', 'night', 'N', '夜間']
                night_shifts = long_df[
                    long_df['code'].str.contains('|'.join(night_shift_codes), case=False, na=False)
                ]
                
                if not night_shifts.empty:
                    # 夜勤従事者の休憩分析
                    night_workers = night_shifts['staff'].unique()
                    night_worker_ratio = len(night_workers) / long_df['staff'].nunique()
                    
                    constraints.append(f"夜勤従事者: {night_worker_ratio:.1%} ({len(night_workers)}名)")
                    
                    # 夜勤頻度分析
                    night_frequency = night_shifts.groupby('staff').size()
                    high_frequency_night = night_frequency[night_frequency >= 10]  # 月10回以上
                    
                    if len(high_frequency_night) > 0:
                        high_freq_ratio = len(high_frequency_night) / len(night_workers)
                        constraints.append(f"高頻度夜勤者: {high_freq_ratio:.1%} - 健康管理強化必要")
                    else:
                        constraints.append("夜勤頻度適正: 深夜業健康管理基準適合")
            
            # 年次有給休暇（推定分析）
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                # 勤務パターンから有給取得の推定
                total_days = long_df['ds'].dt.date.nunique()
                
                # 各スタッフの勤務率から有給使用を推定
                staff_attendance_rates = {}
                for staff_id in long_df['staff'].unique():
                    staff_workdays = long_df[long_df['staff'] == staff_id]['ds'].dt.date.nunique()
                    attendance_rate = staff_workdays / total_days
                    staff_attendance_rates[staff_id] = attendance_rate
                
                # 出勤率80%未満を有給使用ありとみなす
                low_attendance = [rate for rate in staff_attendance_rates.values() if rate < 0.8]
                
                if low_attendance:
                    avg_attendance = np.mean(list(staff_attendance_rates.values()))
                    constraints.append(f"有給使用推定: 平均出勤率{avg_attendance:.1%} - 年休管理良好")
                else:
                    constraints.append("【要確認】高出勤率 - 年次有給休暇取得状況確認必要")
                
        except Exception as e:
            log.warning(f"休憩・休日制約抽出エラー: {e}")
            constraints.append("休憩・休日制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["休憩・休日に関する制約は検出されませんでした"]
    
    def _extract_staffing_standard_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """人員配置基準制約の抽出"""
        constraints = []
        
        try:
            # 介護保険法による人員配置基準
            if 'role' in long_df.columns and 'ds' in long_df.columns:
                # 日別職種配置分析
                daily_role_counts = pd.crosstab(long_df['ds'].dt.date, long_df['role'])
                
                # 管理者・責任者の配置確認
                manager_roles = ['管理者', '施設長', 'ケアマネ', 'ケアマネージャー', 'CM']
                manager_days = 0
                
                for role in daily_role_counts.columns:
                    if any(mgr_role in role for mgr_role in manager_roles):
                        manager_days = (daily_role_counts[role] > 0).sum()
                        break
                
                total_days = len(daily_role_counts)
                if manager_days > 0:
                    manager_coverage = manager_days / total_days
                    constraints.append(f"管理者配置率: {manager_coverage:.1%} - 介護保険法第78条対応")
                    
                    if manager_coverage < 0.8:
                        constraints.append("【法的リスク】管理者配置不足 - 常勤管理者確保必要")
                else:
                    constraints.append("【重大リスク】管理者未配置 - 介護保険法違反")
                
                # 看護師配置基準（特定施設）
                nursing_roles = ['看護師', '准看護師', 'ナース', 'nurse']
                nursing_coverage = 0
                
                for role in daily_role_counts.columns:
                    if any(nurse_role in role for nurse_role in nursing_roles):
                        nursing_days = (daily_role_counts[role] > 0).sum()
                        nursing_coverage = max(nursing_coverage, nursing_days / total_days)
                
                if nursing_coverage > 0:
                    constraints.append(f"看護師配置率: {nursing_coverage:.1%} - 医療対応体制")
                    
                    if nursing_coverage < 0.5:
                        constraints.append("【要確認】看護師配置 - 医療ニーズ対応基準確認必要")
                else:
                    constraints.append("看護師未配置 - 一般介護施設として運営")
            
            # 最低人員配置（安全確保）
            if 'ds' in long_df.columns and 'staff' in long_df.columns:
                # 時間帯別最低人員確認
                long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                hourly_staff_counts = long_df.groupby(['ds', 'hour'])['staff'].nunique().reset_index()
                
                # 夜間帯の最低人員
                night_hours = list(range(22, 24)) + list(range(0, 6))
                night_staff_counts = hourly_staff_counts[hourly_staff_counts['hour'].isin(night_hours)]
                
                if not night_staff_counts.empty:
                    min_night_staff = night_staff_counts['staff'].min()
                    constraints.append(f"夜間最低人員: {min_night_staff}名 - 安全確保基準")
                    
                    if min_night_staff < 1:
                        constraints.append("【重大リスク】夜間無人時間帯存在 - 安全確保基準違反")
                    elif min_night_staff == 1:
                        constraints.append("【要注意】夜間単独勤務 - 緊急時対応体制確認必要")
                
                # 日中帯の人員配置
                day_hours = list(range(8, 18))
                day_staff_counts = hourly_staff_counts[hourly_staff_counts['hour'].isin(day_hours)]
                
                if not day_staff_counts.empty:
                    avg_day_staff = day_staff_counts['staff'].mean()
                    min_day_staff = day_staff_counts['staff'].min()
                    constraints.append(f"日中人員配置: 平均{avg_day_staff:.1f}名、最低{min_day_staff}名")
            
            # 資格者比率（介護保険法施行規則）
            if 'role' in long_df.columns:
                total_shifts = len(long_df)
                
                # 介護福祉士・ヘルパー有資格者
                qualified_roles = ['介護福祉士', 'ヘルパー1級', 'ヘルパー2級', '実務者研修', '初任者研修']
                qualified_count = 0
                
                for role in long_df['role'].unique():
                    if any(qual in role for qual in qualified_roles):
                        qualified_count += (long_df['role'] == role).sum()
                
                if total_shifts > 0:
                    qualified_ratio = qualified_count / total_shifts
                    constraints.append(f"有資格者比率: {qualified_ratio:.1%} - 介護サービス品質基準")
                    
                    if qualified_ratio < 0.5:
                        constraints.append("【品質リスク】有資格者不足 - 研修・資格取得促進必要")
                    else:
                        constraints.append("有資格者配置良好: 品質基準適合")
                
        except Exception as e:
            log.warning(f"人員配置基準制約抽出エラー: {e}")
            constraints.append("人員配置基準制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["人員配置基準に関する制約は検出されませんでした"]
    
    def _extract_qualification_license_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """資格・免許制約の抽出"""
        constraints = []
        
        try:
            # 医療行為可能資格者の配置
            if 'role' in long_df.columns:
                medical_qualified_roles = ['看護師', '准看護師', '医師', '薬剤師']
                medical_staff_count = 0
                
                for role in long_df['role'].unique():
                    if any(med_role in role for med_role in medical_qualified_roles):
                        medical_staff_count += (long_df['role'] == role).sum()
                
                total_shifts = len(long_df)
                if medical_staff_count > 0:
                    medical_ratio = medical_staff_count / total_shifts
                    constraints.append(f"医療資格者配置: {medical_ratio:.1%} - 医療行為対応可能")
                    
                    # 医療行為の頻度分析
                    if medical_ratio > 0.3:
                        constraints.append("高医療ニーズ対応: 医療的ケア充実")
                    else:
                        constraints.append("基本医療対応: 緊急時医療連携体制確保")
                else:
                    constraints.append("医療資格者未配置: 医療行為制限・外部連携必須")
            
            # 運転免許（送迎サービス）の確認
            if 'role' in long_df.columns:
                # 運転手・送迎担当者の分析
                driver_roles = ['運転手', 'ドライバー', '送迎', 'driver']
                driver_count = 0
                
                for role in long_df['role'].unique():
                    if any(driver_role in role for driver_role in driver_roles):
                        driver_count += (long_df['role'] == role).sum()
                
                if driver_count > 0:
                    driver_ratio = driver_count / total_shifts
                    constraints.append(f"運転担当者配置: {driver_ratio:.1%} - 送迎サービス対応")
                    constraints.append("【法的確認】運転免許・任意保険・車両管理確認必要")
                else:
                    constraints.append("運転担当者未配置: 送迎サービス外部委託または未実施")
            
            # 介護支援専門員（ケアマネージャー）
            if 'role' in long_df.columns:
                care_manager_roles = ['ケアマネ', 'ケアマネージャー', 'CM', '介護支援専門員']
                cm_count = 0
                
                for role in long_df['role'].unique():
                    if any(cm_role in role for cm_role in care_manager_roles):
                        cm_count += (long_df['role'] == role).sum()
                
                if cm_count > 0:
                    cm_ratio = cm_count / total_shifts
                    constraints.append(f"ケアマネ配置: {cm_ratio:.1%} - ケアプラン作成対応")
                    
                    # ケアマネの配置頻度
                    if 'ds' in long_df.columns:
                        cm_data = long_df[long_df['role'].str.contains('|'.join(care_manager_roles), case=False, na=False)]
                        if not cm_data.empty:
                            cm_coverage_days = cm_data['ds'].dt.date.nunique()
                            total_days = long_df['ds'].dt.date.nunique()
                            cm_coverage = cm_coverage_days / total_days
                            
                            constraints.append(f"ケアマネ稼働率: {cm_coverage:.1%} - 継続的ケア管理")
                else:
                    constraints.append("ケアマネ未配置: 居宅介護支援事業外または外部委託")
            
            # 生活相談員（特定施設等）
            if 'role' in long_df.columns:
                counselor_roles = ['生活相談員', '相談員', 'MSW', 'ソーシャルワーカー']
                counselor_count = 0
                
                for role in long_df['role'].unique():
                    if any(counselor_role in role for counselor_role in counselor_roles):
                        counselor_count += (long_df['role'] == role).sum()
                
                if counselor_count > 0:
                    counselor_ratio = counselor_count / total_shifts
                    constraints.append(f"生活相談員配置: {counselor_ratio:.1%} - 相談支援体制")
                else:
                    constraints.append("生活相談員未配置: 相談支援機能の確認必要")
            
            # 機能訓練指導員
            if 'role' in long_df.columns:
                trainer_roles = ['理学療法士', 'PT', '作業療法士', 'OT', '言語聴覚士', 'ST', '機能訓練指導員']
                trainer_count = 0
                
                for role in long_df['role'].unique():
                    if any(trainer_role in role for trainer_role in trainer_roles):
                        trainer_count += (long_df['role'] == role).sum()
                
                if trainer_count > 0:
                    trainer_ratio = trainer_count / total_shifts
                    constraints.append(f"機能訓練指導員配置: {trainer_ratio:.1%} - リハビリ対応")
                    
                    # リハビリ専門職の多様性
                    trainer_types = []
                    for role in long_df['role'].unique():
                        if any(t_role in role for t_role in trainer_roles):
                            trainer_types.append(role)
                    
                    if len(trainer_types) >= 2:
                        constraints.append("多職種リハビリ体制: 包括的機能訓練対応")
                    else:
                        constraints.append("単一リハビリ職種: 専門分野特化型対応")
                else:
                    constraints.append("機能訓練指導員未配置: 維持期リハビリ未実施")
            
            # 資格更新・研修受講状況（推定分析）
            if 'employment' in long_df.columns and 'role' in long_df.columns:
                # 正規雇用での資格者配置（資格管理の観点）
                regular_qualified = long_df[
                    (long_df['employment'].str.contains('正社員|正規', case=False, na=False)) &
                    (long_df['role'].str.contains('看護師|介護福祉士|ケアマネ', case=False, na=False))
                ]
                
                if not regular_qualified.empty:
                    reg_qual_ratio = len(regular_qualified) / len(long_df)
                    constraints.append(f"正規資格者比率: {reg_qual_ratio:.1%} - 資格管理体制安定")
                    
                    if reg_qual_ratio > 0.3:
                        constraints.append("資格管理良好: 継続的専門性確保")
                    else:
                        constraints.append("【要注意】資格管理 - 更新・研修受講状況確認必要")
                
        except Exception as e:
            log.warning(f"資格・免許制約抽出エラー: {e}")
            constraints.append("資格・免許制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["資格・免許に関する制約は検出されませんでした"]
    
    def _extract_safety_health_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """安全衛生制約の抽出"""
        constraints = []
        
        try:
            # 労働安全衛生法による健康管理
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                # 過重労働の検出
                staff_workload = long_df['staff'].value_counts()
                
                # 過重労働基準（月30日以上勤務）
                overwork_threshold = 30
                overworked_staff = staff_workload[staff_workload >= overwork_threshold]
                
                if len(overworked_staff) > 0:
                    overwork_ratio = len(overworked_staff) / len(staff_workload)
                    max_workdays = overworked_staff.max()
                    constraints.append(f"過重労働者: {overwork_ratio:.1%} (最大{max_workdays}日勤務)")
                    constraints.append("【健康リスク】労働安全衛生法 - 健康診断・面接指導実施必要")
                else:
                    constraints.append("過重労働なし: 労働安全衛生法適合")
            
            # 夜勤従事者の健康管理
            if 'ds' in long_df.columns and 'code' in long_df.columns:
                night_shift_codes = ['夜勤', 'ナイト', 'night', 'N', '夜間']
                night_shifts = long_df[
                    long_df['code'].str.contains('|'.join(night_shift_codes), case=False, na=False)
                ]
                
                if not night_shifts.empty:
                    # 夜勤頻度別健康リスク分析
                    night_frequency = night_shifts.groupby('staff').size()
                    
                    # 月8回以上夜勤を高頻度とする
                    high_night_freq = night_frequency[night_frequency >= 8]
                    
                    if len(high_night_freq) > 0:
                        high_night_ratio = len(high_night_freq) / len(night_frequency)
                        avg_night_freq = high_night_freq.mean()
                        constraints.append(f"高頻度夜勤者: {high_night_ratio:.1%} (平均{avg_night_freq:.1f}回/月)")
                        constraints.append("【健康管理】深夜業健診・睡眠指導実施推奨")
                    else:
                        constraints.append("夜勤頻度適正: 深夜業健康管理基準内")
            
            # 感染症対策体制（新型コロナ等）
            if 'role' in long_df.columns:
                # 感染対策責任者の配置確認
                infection_control_roles = ['看護師', '管理者', '感染管理', 'ICT']
                ic_staff_count = 0
                
                for role in long_df['role'].unique():
                    if any(ic_role in role for ic_role in infection_control_roles):
                        ic_staff_count += (long_df['role'] == role).sum()
                
                if ic_staff_count > 0:
                    ic_ratio = ic_staff_count / len(long_df)
                    constraints.append(f"感染対策要員: {ic_ratio:.1%} - 感染症対応体制")
                    
                    # 感染対策の継続性確認
                    if 'ds' in long_df.columns:
                        ic_data = long_df[long_df['role'].str.contains('看護師|管理者', case=False, na=False)]
                        if not ic_data.empty:
                            ic_coverage_days = ic_data['ds'].dt.date.nunique()
                            total_days = long_df['ds'].dt.date.nunique()
                            ic_coverage = ic_coverage_days / total_days
                            
                            if ic_coverage > 0.8:
                                constraints.append("感染対策継続性良好: 常時対応体制")
                            else:
                                constraints.append("【要強化】感染対策継続性 - 体制強化必要")
                else:
                    constraints.append("【リスク】感染対策専門要員不足 - 研修・体制整備必要")
            
            # 事故・緊急時対応体制
            if 'ds' in long_df.columns and 'staff' in long_df.columns:
                # 24時間体制での安全確保
                long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                
                # 全時間帯での人員配置確認
                hourly_coverage = long_df.groupby('hour')['staff'].nunique()
                uncovered_hours = hourly_coverage[hourly_coverage == 0]
                
                if len(uncovered_hours) > 0:
                    constraints.append(f"無人時間帯: {len(uncovered_hours)}時間 - 緊急時対応不可")
                    constraints.append("【重大リスク】24時間安全体制未確立 - 緊急時対応体制整備必要")
                else:
                    constraints.append("24時間安全体制: 常時緊急対応可能")
                
                # 複数名配置による安全確保
                multi_staff_hours = hourly_coverage[hourly_coverage >= 2]
                multi_staff_ratio = len(multi_staff_hours) / 24
                
                constraints.append(f"複数名配置時間: {multi_staff_ratio:.1%} - 相互安全確認体制")
            
            # 職場環境の安全性（間接指標）
            if 'staff' in long_df.columns:
                # スタッフの定着率（安全な職場環境の指標）
                total_staff = long_df['staff'].nunique()
                
                # 勤務頻度による定着度分析
                staff_frequency = long_df['staff'].value_counts()
                regular_staff = staff_frequency[staff_frequency >= 10]  # 10日以上勤務
                retention_rate = len(regular_staff) / total_staff
                
                constraints.append(f"スタッフ定着率: {retention_rate:.1%} - 職場環境安全性指標")
                
                if retention_rate > 0.7:
                    constraints.append("職場環境良好: 安全で働きやすい環境")
                elif retention_rate < 0.5:
                    constraints.append("【要改善】職場環境 - 安全衛生管理体制見直し必要")
                else:
                    constraints.append("職場環境標準: 継続的改善推進")
                
        except Exception as e:
            log.warning(f"安全衛生制約抽出エラー: {e}")
            constraints.append("安全衛生制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["安全衛生に関する制約は検出されませんでした"]
    
    def _extract_documentation_reporting_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """記録・報告制約の抽出"""
        constraints = []
        
        try:
            # 勤務記録の完全性確認
            if 'ds' in long_df.columns and 'staff' in long_df.columns:
                # 記録の連続性分析
                total_days = long_df['ds'].dt.date.nunique()
                total_records = len(long_df)
                
                # 1日平均記録数
                avg_records_per_day = total_records / total_days if total_days > 0 else 0
                constraints.append(f"勤務記録密度: {avg_records_per_day:.1f}件/日 - 記録管理状況")
                
                # 記録の欠損日分析
                all_dates = pd.date_range(
                    start=long_df['ds'].min(),
                    end=long_df['ds'].max(),
                    freq='D'
                )
                recorded_dates = set(long_df['ds'].dt.date)
                missing_dates = len(all_dates) - len(recorded_dates)
                
                if missing_dates > 0:
                    missing_ratio = missing_dates / len(all_dates)
                    constraints.append(f"記録欠損: {missing_ratio:.1%} ({missing_dates}日) - 記録管理改善必要")
                    constraints.append("【法的リスク】勤務記録保存義務 - 労働基準法第109条違反リスク")
                else:
                    constraints.append("記録完全性良好: 労働基準法第109条適合")
            
            # 介護記録・報告書作成体制
            if 'role' in long_df.columns:
                # 記録作成責任者の配置
                record_responsible_roles = ['看護師', '介護福祉士', '管理者', 'ケアマネ']
                record_staff_count = 0
                
                for role in long_df['role'].unique():
                    if any(rec_role in role for rec_role in record_responsible_roles):
                        record_staff_count += (long_df['role'] == role).sum()
                
                if record_staff_count > 0:
                    record_ratio = record_staff_count / len(long_df)
                    constraints.append(f"記録責任者配置: {record_ratio:.1%} - 介護記録作成体制")
                    
                    # 記録品質確保のための配置分析
                    if record_ratio > 0.5:
                        constraints.append("記録体制充実: 高品質記録作成可能")
                    else:
                        constraints.append("【要改善】記録体制 - 責任者配置強化必要")
                else:
                    constraints.append("【重大リスク】記録責任者不在 - 介護記録作成体制未整備")
            
            # 事故報告・ヒヤリハット記録体制
            if 'employment' in long_df.columns and 'role' in long_df.columns:
                # 常勤職員による継続的記録管理
                permanent_record_staff = long_df[
                    (long_df['employment'].str.contains('正社員|正規', case=False, na=False)) &
                    (long_df['role'].str.contains('看護師|介護福祉士|管理者', case=False, na=False))
                ]
                
                if not permanent_record_staff.empty:
                    perm_record_ratio = len(permanent_record_staff) / len(long_df)
                    constraints.append(f"常勤記録担当: {perm_record_ratio:.1%} - 継続的記録管理")
                    
                    # 記録継続性の確保
                    if 'ds' in long_df.columns:
                        perm_coverage_days = permanent_record_staff['ds'].dt.date.nunique()
                        total_days = long_df['ds'].dt.date.nunique()
                        perm_coverage = perm_coverage_days / total_days
                        
                        if perm_coverage > 0.8:
                            constraints.append("記録継続性確保: 事故報告体制整備")
                        else:
                            constraints.append("【要強化】記録継続性 - 事故報告体制強化必要")
                else:
                    constraints.append("【リスク】常勤記録担当不在 - 事故報告継続性リスク")
            
            # 監査対応記録の整備状況
            if 'ds' in long_df.columns:
                # 記録期間の法的要件確認
                record_period_days = (long_df['ds'].max() - long_df['ds'].min()).days
                
                # 労働基準法：3年保存、介護保険法：2年保存
                if record_period_days >= 1095:  # 3年
                    constraints.append("記録保存期間: 3年以上 - 労働基準法対応十分")
                elif record_period_days >= 730:  # 2年
                    constraints.append("記録保存期間: 2年以上 - 介護保険法対応済み")
                else:
                    constraints.append("【要注意】記録保存期間不足 - 法的保存義務確認必要")
            
            # 労働時間記録の詳細性
            if 'ds' in long_df.columns and 'code' in long_df.columns:
                # シフトコードの多様性（記録の詳細度）
                shift_variety = long_df['code'].nunique()
                total_records = len(long_df)
                
                record_detail_ratio = shift_variety / total_records * 100
                constraints.append(f"記録詳細度: {shift_variety}種類のシフト記録 (詳細度: {record_detail_ratio:.1f})")
                
                if shift_variety >= 5:
                    constraints.append("記録詳細性良好: 労働時間管理精密")
                elif shift_variety <= 2:
                    constraints.append("【要改善】記録詳細性 - より詳細な勤務記録必要")
                else:
                    constraints.append("記録詳細性標準: 基本的労働時間管理")
            
            # 電子化・システム化対応（推定）
            if 'ds' in long_df.columns:
                # データの規則性から電子化レベルを推定
                date_continuity = len(long_df['ds'].dt.date.unique())
                total_period = (long_df['ds'].max() - long_df['ds'].min()).days + 1
                
                digitalization_score = date_continuity / total_period if total_period > 0 else 0
                
                if digitalization_score > 0.9:
                    constraints.append("記録電子化: 高度 - デジタル記録管理体制")
                elif digitalization_score > 0.7:
                    constraints.append("記録電子化: 中程度 - 部分的デジタル化")
                else:
                    constraints.append("【近代化】記録電子化推進 - システム導入検討")
                
        except Exception as e:
            log.warning(f"記録・報告制約抽出エラー: {e}")
            constraints.append("記録・報告制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["記録・報告に関する制約は検出されませんでした"]
    
    def _extract_employment_contract_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """契約・雇用制約の抽出"""
        constraints = []
        
        try:
            # 雇用形態の法的適合性
            if 'employment' in long_df.columns:
                employment_distribution = long_df['employment'].value_counts()
                total_shifts = len(long_df)
                
                # 正規雇用比率（安定雇用の観点）
                regular_keywords = ['正社員', '正規', '常勤', 'フルタイム']
                regular_count = sum(
                    employment_distribution[emp] for emp in employment_distribution.index
                    if any(keyword in emp for keyword in regular_keywords)
                )
                
                regular_ratio = regular_count / total_shifts if total_shifts > 0 else 0
                constraints.append(f"正規雇用比率: {regular_ratio:.1%} - 雇用安定性")
                
                # 労働契約法への適合
                if regular_ratio < 0.3:
                    constraints.append("【要注意】非正規雇用多数 - 労働契約法・同一労働同一賃金確認必要")
                elif regular_ratio > 0.7:
                    constraints.append("正規雇用中心: 雇用安定・キャリア形成良好")
                else:
                    constraints.append("雇用形態バランス: 柔軟性と安定性の調和")
                
                # 有期雇用の5年ルール対応
                contract_keywords = ['契約', '有期', 'パート', 'アルバイト']
                contract_count = sum(
                    employment_distribution[emp] for emp in employment_distribution.index
                    if any(keyword in emp for keyword in contract_keywords)
                )
                
                if contract_count > 0:
                    contract_ratio = contract_count / total_shifts
                    constraints.append(f"有期雇用比率: {contract_ratio:.1%} - 無期転換ルール対象")
                    
                    if contract_ratio > 0.5:
                        constraints.append("【法的対応】有期雇用5年ルール - 無期転換申込権発生対応必要")
            
            # 労働時間と雇用形態の整合性
            if 'employment' in long_df.columns and 'staff' in long_df.columns:
                # パートタイム労働者の労働時間確認
                part_time_keywords = ['パート', 'アルバイト', '非常勤']
                part_time_staff = []
                
                for emp_type in long_df['employment'].unique():
                    if any(pt_keyword in emp_type for pt_keyword in part_time_keywords):
                        pt_staff_data = long_df[long_df['employment'] == emp_type]
                        for staff_id in pt_staff_data['staff'].unique():
                            staff_workdays = pt_staff_data[pt_staff_data['staff'] == staff_id].shape[0]
                            part_time_staff.append((staff_id, staff_workdays))
                
                if part_time_staff:
                    # パートタイム労働者の労働時間分析
                    avg_pt_workdays = np.mean([days for _, days in part_time_staff])
                    long_hour_pt = [(staff, days) for staff, days in part_time_staff if days >= 20]  # 月20日以上
                    
                    constraints.append(f"パートタイム平均勤務: {avg_pt_workdays:.1f}日/月")
                    
                    if long_hour_pt:
                        long_hour_ratio = len(long_hour_pt) / len(part_time_staff)
                        constraints.append(f"長時間パートタイム: {long_hour_ratio:.1%} - 社会保険適用確認必要")
                        constraints.append("【法的確認】パートタイム労働法 - 処遇均等・社会保険対応")
                    else:
                        constraints.append("パートタイム労働時間適正: 法的基準内")
            
            # 最低賃金対応（間接確認）
            if 'role' in long_df.columns and 'employment' in long_df.columns:
                # 最低賃金対象となりうる雇用形態の分析
                minimum_wage_target = long_df[
                    long_df['employment'].str.contains('パート|アルバイト|時給', case=False, na=False)
                ]
                
                if not minimum_wage_target.empty:
                    mw_ratio = len(minimum_wage_target) / len(long_df)
                    constraints.append(f"最低賃金対象: {mw_ratio:.1%} - 最低賃金法遵守確認必要")
                    
                    # 地域別最低賃金対応の必要性
                    constraints.append("【法的確認】地域別最低賃金 - 都道府県基準確認必要")
                else:
                    constraints.append("最低賃金対象なし: 月給制・年俸制中心")
            
            # 労働者派遣法対応
            if 'employment' in long_df.columns:
                # 派遣労働者の確認
                dispatch_keywords = ['派遣', 'dispatch', '紹介']
                dispatch_count = sum(
                    long_df['employment'].str.contains(keyword, case=False, na=False).sum()
                    for keyword in dispatch_keywords
                )
                
                if dispatch_count > 0:
                    dispatch_ratio = dispatch_count / len(long_df)
                    constraints.append(f"派遣労働者: {dispatch_ratio:.1%} - 労働者派遣法対応")
                    constraints.append("【法的確認】派遣3年ルール・同一労働同一賃金対応必要")
                    
                    # 派遣労働者の期間制限
                    if dispatch_ratio > 0.3:
                        constraints.append("【要注意】派遣依存度高 - 期間制限・直接雇用転換検討")
                else:
                    constraints.append("派遣労働者なし: 直接雇用中心")
            
            # 外国人労働者雇用（技能実習・特定技能）
            if 'staff' in long_df.columns:
                # 外国人労働者推定（スタッフ名等から推定は困難なため、雇用形態から推定）
                # 実際の実装では在留資格データが必要
                constraints.append("【確認事項】外国人労働者雇用 - 在留資格・労働許可確認必要")
                constraints.append("【法的確認】出入国管理法・労働基準法（外国人労働者版）適合")
            
            # 育児・介護休業法対応
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                # 長期欠勤者の分析（育児・介護休業の可能性）
                staff_attendance = long_df.groupby('staff')['ds'].count()
                total_days = long_df['ds'].dt.date.nunique()
                
                # 出勤率50%未満を長期休業の可能性とする
                low_attendance_staff = staff_attendance[staff_attendance < total_days * 0.5]
                
                if len(low_attendance_staff) > 0:
                    low_attendance_ratio = len(low_attendance_staff) / long_df['staff'].nunique()
                    constraints.append(f"長期休業可能性: {low_attendance_ratio:.1%} - 育児介護休業法対応確認")
                    constraints.append("【法的確認】復職支援・代替要員確保体制整備")
                else:
                    constraints.append("長期休業者なし: 安定勤務継続")
                
        except Exception as e:
            log.warning(f"契約・雇用制約抽出エラー: {e}")
            constraints.append("契約・雇用制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["契約・雇用に関する制約は検出されませんでした"]
    
    def _extract_regulatory_compliance_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """規制遵守制約の抽出"""
        constraints = []
        
        try:
            # 介護保険法遵守状況の総合評価
            if 'role' in long_df.columns and 'ds' in long_df.columns:
                # 介護サービス提供体制の評価
                care_service_indicators = {
                    'management_coverage': 0,  # 管理者配置率
                    'nursing_coverage': 0,    # 看護師配置率
                    'certified_ratio': 0,     # 有資格者比率
                    'service_continuity': 0   # サービス継続性
                }
                
                # 管理者配置率
                manager_roles = ['管理者', '施設長', 'ケアマネ']
                manager_data = long_df[
                    long_df['role'].str.contains('|'.join(manager_roles), case=False, na=False)
                ]
                if not manager_data.empty:
                    care_service_indicators['management_coverage'] = manager_data['ds'].dt.date.nunique() / long_df['ds'].dt.date.nunique()
                
                # 看護師配置率
                nursing_roles = ['看護師', '准看護師']
                nursing_data = long_df[
                    long_df['role'].str.contains('|'.join(nursing_roles), case=False, na=False)
                ]
                if not nursing_data.empty:
                    care_service_indicators['nursing_coverage'] = len(nursing_data) / len(long_df)
                
                # 有資格者比率
                qualified_roles = ['介護福祉士', 'ヘルパー', '看護師', 'ケアマネ']
                qualified_data = long_df[
                    long_df['role'].str.contains('|'.join(qualified_roles), case=False, na=False)
                ]
                if not qualified_data.empty:
                    care_service_indicators['certified_ratio'] = len(qualified_data) / len(long_df)
                
                # サービス継続性（24時間365日）
                daily_coverage = long_df.groupby(long_df['ds'].dt.date)['staff'].nunique()
                care_service_indicators['service_continuity'] = (daily_coverage > 0).mean()
                
                # 総合評価
                compliance_score = sum(care_service_indicators.values()) / len(care_service_indicators)
                constraints.append(f"介護保険法遵守度: {compliance_score:.1%} - 総合評価")
                
                if compliance_score >= 0.8:
                    constraints.append("高遵守度: 介護保険法基準クリア")
                elif compliance_score >= 0.6:
                    constraints.append("中遵守度: 一部改善で基準達成可能")
                else:
                    constraints.append("【要改善】低遵守度 - 基準適合のための体制強化必要")
            
            # 労働基準法遵守状況の総合評価
            labor_law_violations = 0
            total_checks = 0
            
            # 週40時間制限チェック
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                long_df['week'] = pd.to_datetime(long_df['ds']).dt.isocalendar().week
                weekly_workdays = long_df.groupby(['staff', 'week']).size()
                weekly_violations = (weekly_workdays > 5).sum()  # 5日×8時間=40時間
                total_weekly_records = len(weekly_workdays)
                
                if total_weekly_records > 0:
                    weekly_violation_rate = weekly_violations / total_weekly_records
                    labor_law_violations += weekly_violation_rate
                total_checks += 1
            
            # 週休制チェック
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                weekly_rest_violations = (weekly_workdays >= 7).sum()  # 週7日勤務
                if total_weekly_records > 0:
                    rest_violation_rate = weekly_rest_violations / total_weekly_records
                    labor_law_violations += rest_violation_rate
                total_checks += 1
            
            if total_checks > 0:
                labor_compliance_score = 1 - (labor_law_violations / total_checks)
                constraints.append(f"労働基準法遵守度: {labor_compliance_score:.1%} - 総合評価")
                
                if labor_compliance_score >= 0.9:
                    constraints.append("労働基準法高遵守: 法的リスク低")
                elif labor_compliance_score >= 0.7:
                    constraints.append("労働基準法中遵守: 一部改善必要")
                else:
                    constraints.append("【重要】労働基準法要改善 - 法的リスク高・即座の対応必要")
            
            # 監査対応準備状況
            if 'ds' in long_df.columns:
                # 記録の網羅性
                record_completeness = len(long_df) / long_df['ds'].dt.date.nunique()
                
                # 監査対応評価指標
                audit_readiness_factors = {
                    'record_completeness': min(record_completeness / 10, 1.0),  # 1日10記録を基準
                    'period_coverage': min((long_df['ds'].max() - long_df['ds'].min()).days / 365, 1.0),  # 1年カバレッジ
                    'staff_diversity': min(long_df['staff'].nunique() / 20, 1.0),  # 20名体制を基準
                    'role_diversity': min(long_df['role'].nunique() / 5, 1.0)   # 5職種を基準
                }
                
                audit_readiness = sum(audit_readiness_factors.values()) / len(audit_readiness_factors)
                constraints.append(f"監査対応準備度: {audit_readiness:.1%} - 総合評価")
                
                if audit_readiness >= 0.8:
                    constraints.append("監査対応準備良好: 十分な記録・体制整備")
                elif audit_readiness >= 0.6:
                    constraints.append("監査対応準備中程度: 一部強化で対応可能")
                else:
                    constraints.append("【要強化】監査対応準備 - 記録・体制整備急務")
            
            # 地域包括ケアシステム対応
            if 'role' in long_df.columns:
                # 多職種連携体制の評価
                community_care_roles = ['看護師', 'ケアマネ', '相談員', 'リハビリ', 'PT', 'OT']
                community_care_count = sum(
                    long_df['role'].str.contains(role, case=False, na=False).sum()
                    for role in community_care_roles
                )
                
                if community_care_count > 0:
                    community_care_ratio = community_care_count / len(long_df)
                    constraints.append(f"地域包括ケア対応: {community_care_ratio:.1%} - 多職種連携体制")
                    
                    if community_care_ratio >= 0.3:
                        constraints.append("地域包括ケア体制充実: 包括的サービス提供可能")
                    else:
                        constraints.append("地域包括ケア体制基本: 外部連携強化で対応")
                else:
                    constraints.append("地域包括ケア対応限定: 基本介護サービス中心")
            
            # 情報セキュリティ・個人情報保護対応
            constraints.append("【確認必須】個人情報保護法遵守 - プライバシーマーク・ISMS対応確認")
            constraints.append("【確認必須】介護記録電子化 - セキュリティ対策・バックアップ体制確認")
            
            # 新型コロナウイルス感染症対策（特別措置）
            if 'ds' in long_df.columns:
                # 感染症対策期間の特別運営
                recent_period = long_df['ds'].max() - pd.Timedelta(days=90)  # 直近3ヶ月
                recent_data = long_df[long_df['ds'] >= recent_period]
                
                if not recent_data.empty:
                    recent_operations = len(recent_data) / len(long_df)
                    constraints.append(f"感染症対策期間運営: {recent_operations:.1%} - 特別措置対応")
                    constraints.append("【確認必須】感染症対策 - 厚労省ガイドライン遵守確認")
                
        except Exception as e:
            log.warning(f"規制遵守制約抽出エラー: {e}")
            constraints.append("規制遵守制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["規制遵守に関する制約は検出されませんでした"]
    
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
        
        # 法的重要度別分類
        critical_legal = [fact for facts in mece_facts.values() for fact in facts if any(keyword in fact for keyword in ['重大リスク', '法的リスク', '違反'])]
        compliance_required = [fact for facts in mece_facts.values() for fact in facts if any(keyword in fact for keyword in ['確認必須', '要改善', '強化必要'])]
        good_compliance = [fact for facts in mece_facts.values() for fact in facts if any(keyword in fact for keyword in ['遵守', '適合', '良好'])]
        
        return {
            '抽出事実サマリー': {
                '総事実数': total_facts,
                '分析軸': f'軸{self.axis_number}: {self.axis_name}',
                '分析対象レコード数': len(long_df),
                'MECEカテゴリー数': len(mece_facts),
                **{category: len(facts) for category, facts in mece_facts.items()}
            },
            'MECE分解事実': mece_facts,
            '法的重要度別分類': {
                '重大法的リスク事実': critical_legal,
                '対応必須事実': compliance_required, 
                '遵守良好事実': good_compliance,
                '要検証事実': [fact for facts in mece_facts.values() for fact in facts if 'エラー' in fact or '検出されませんでした' in fact]
            },
            '法的基準適用': {
                '労働基準法': [fact for facts in mece_facts.values() for fact in facts if '労働基準法' in fact],
                '介護保険法': [fact for facts in mece_facts.values() for fact in facts if '介護保険法' in fact or '介護' in fact],
                '労働安全衛生法': [fact for facts in mece_facts.values() for fact in facts if '安全衛生' in fact or '健康管理' in fact],
                'その他法規': [fact for facts in mece_facts.values() for fact in facts if any(law in fact for law in ['派遣法', '契約法', '個人情報保護'])]
            }
        }
    
    def _generate_machine_readable_constraints(self, mece_facts: Dict[str, List[str]], long_df: pd.DataFrame) -> Dict[str, Any]:
        """機械可読形式の制約生成"""
        
        hard_constraints = []
        soft_constraints = []
        preferences = []
        
        # MECEカテゴリー別制約分類（法的制約は最高優先度）
        for category, facts in mece_facts.items():
            for i, fact in enumerate(facts):
                constraint_id = f"axis7_{category.lower().replace('制約', '')}_{i+1}"
                
                # 法的制約の強度判定（最高優先度）
                if any(keyword in fact for keyword in ['重大リスク', '法的リスク', '違反', '必須', '義務']):
                    hard_constraints.append({
                        'id': constraint_id,
                        'type': 'legal_regulatory',
                        'category': category,
                        'description': fact,
                        'priority': 'critical',  # 法的制約は最高優先度
                        'confidence': 0.95,
                        'legal_basis': self._identify_legal_basis(fact),
                        'compliance_level': self._assess_compliance_level(fact),
                        'enforcement_risk': self._assess_enforcement_risk(fact)
                    })
                elif any(keyword in fact for keyword in ['要改善', '確認必要', '強化必要', '対応']):
                    soft_constraints.append({
                        'id': constraint_id,
                        'type': 'legal_regulatory',
                        'category': category,
                        'description': fact,
                        'priority': 'high',
                        'confidence': 0.8,
                        'legal_basis': self._identify_legal_basis(fact),
                        'compliance_level': self._assess_compliance_level(fact),
                        'enforcement_risk': self._assess_enforcement_risk(fact)
                    })
                else:
                    preferences.append({
                        'id': constraint_id,
                        'type': 'legal_regulatory',
                        'category': category,
                        'description': fact,
                        'priority': 'medium',
                        'confidence': 0.6,
                        'legal_basis': self._identify_legal_basis(fact),
                        'compliance_level': self._assess_compliance_level(fact),
                        'enforcement_risk': self._assess_enforcement_risk(fact)
                    })
        
        return {
            'hard_constraints': hard_constraints,
            'soft_constraints': soft_constraints,
            'preferences': preferences,
            'constraint_relationships': [
                {
                    'relationship_id': 'legal_hierarchy',
                    'type': 'dominates',
                    'from_category': '法的・規制要件',
                    'to_category': 'all_other_axes',
                    'description': '法的制約は他の全制約に優先する'
                },
                {
                    'relationship_id': 'labor_safety_synergy',
                    'type': 'reinforces',
                    'from_category': '労働時間制約',
                    'to_category': '安全衛生制約',
                    'description': '労働時間制限と安全衛生の相互強化'
                },
                {
                    'relationship_id': 'qualification_staffing_dependency',
                    'type': 'requires',
                    'from_category': '人員配置基準制約',
                    'to_category': '資格・免許制約',
                    'description': '人員配置基準は適切な資格者配置を要求'
                }
            ],
            'validation_rules': [
                {
                    'rule_id': 'axis7_labor_law_compliance',
                    'description': '労働基準法の全条項遵守を確認',
                    'validation_type': 'legal_compliance',
                    'severity': 'critical'
                },
                {
                    'rule_id': 'axis7_care_insurance_compliance', 
                    'description': '介護保険法の人員配置基準遵守を確認',
                    'validation_type': 'regulatory_compliance',
                    'severity': 'critical'
                },
                {
                    'rule_id': 'axis7_qualification_verification',
                    'description': '必要資格・免許の保有・更新状況を確認',
                    'validation_type': 'credential_check',
                    'severity': 'high'
                },
                {
                    'rule_id': 'axis7_documentation_audit',
                    'description': '法定記録の完全性・保存期間遵守を確認',
                    'validation_type': 'documentation_audit',
                    'severity': 'high'
                }
            ],
            'legal_frameworks': {
                '労働基準法': {
                    'scope': '労働時間、休憩、休日、残業等',
                    'enforcement_authority': '労働基準監督署',
                    'penalty_risk': 'high'
                },
                '介護保険法': {
                    'scope': '人員配置基準、サービス提供体制等',
                    'enforcement_authority': '都道府県・市町村',
                    'penalty_risk': 'high'
                },
                '労働安全衛生法': {
                    'scope': '職場安全、健康管理、労働環境等',
                    'enforcement_authority': '労働基準監督署',
                    'penalty_risk': 'medium'
                },
                '労働契約法': {
                    'scope': '雇用契約、有期雇用、同一労働同一賃金等',
                    'enforcement_authority': '労働局',
                    'penalty_risk': 'medium'
                }
            }
        }
    
    def _identify_legal_basis(self, fact: str) -> str:
        """法的根拠の特定"""
        if '労働基準法' in fact:
            return 'labor_standards_act'
        elif '介護保険法' in fact or '介護' in fact:
            return 'long_term_care_insurance_act'
        elif '安全衛生' in fact or '健康管理' in fact:
            return 'occupational_safety_health_act'
        elif '派遣' in fact:
            return 'worker_dispatching_act'
        elif '契約' in fact or '雇用' in fact:
            return 'labor_contract_act'
        elif '個人情報' in fact:
            return 'personal_information_protection_act'
        else:
            return 'general_regulatory_framework'
    
    def _assess_compliance_level(self, fact: str) -> str:
        """遵守レベルの評価"""
        if any(keyword in fact for keyword in ['遵守', '適合', '良好']):
            return 'compliant'
        elif any(keyword in fact for keyword in ['違反', 'リスク', '重大']):
            return 'non_compliant'
        elif any(keyword in fact for keyword in ['要改善', '確認必要', '強化']):
            return 'requires_improvement'
        else:
            return 'under_review'
    
    def _assess_enforcement_risk(self, fact: str) -> str:
        """法的執行リスクの評価"""
        if any(keyword in fact for keyword in ['重大リスク', '法的リスク', '違反']):
            return 'high'
        elif any(keyword in fact for keyword in ['要改善', '確認必要']):
            return 'medium'
        elif any(keyword in fact for keyword in ['遵守', '適合']):
            return 'low'
        else:
            return 'unknown'
    
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
        
        # 法的コンプライアンス指標
        legal_compliance_indicators = {
            'labor_law_violations': len([f for facts in mece_facts.values() for f in facts if '労働基準法' in f and ('違反' in f or 'リスク' in f)]),
            'care_law_violations': len([f for facts in mece_facts.values() for f in facts if '介護保険法' in f and ('違反' in f or 'リスク' in f)]),
            'safety_violations': len([f for facts in mece_facts.values() for f in facts if '安全衛生' in f and ('違反' in f or 'リスク' in f)]),
            'total_compliance_issues': len([f for facts in mece_facts.values() for f in facts if any(risk in f for risk in ['リスク', '違反', '要改善'])]),
            'compliance_achievements': len([f for facts in mece_facts.values() for f in facts if any(good in f for good in ['遵守', '適合', '良好'])]),
            'regulatory_coverage_ratio': len([f for facts in mece_facts.values() for f in facts if any(law in f for law in ['法', '基準', '規制'])]) / sum(len(facts) for facts in mece_facts.values()) if sum(len(facts) for facts in mece_facts.values()) > 0 else 0
        }
        
        # データ品質指標
        data_quality = {
            'completeness': 1.0 - (long_df.isnull().sum().sum() / (len(long_df) * len(long_df.columns))),
            'record_count': len(long_df),
            'unique_staff_count': long_df['staff'].nunique() if 'staff' in long_df.columns else 0,
            'unique_roles_count': long_df['role'].nunique() if 'role' in long_df.columns else 0,
            'legal_focus_ratio': len([f for facts in mece_facts.values() for f in facts if any(l in f for l in ['法的', '規制', '基準', '義務'])]) / sum(len(facts) for facts in mece_facts.values()) if sum(len(facts) for facts in mece_facts.values()) > 0 else 0
        }
        
        return {
            'extraction_timestamp': datetime.now().isoformat(),
            'axis_info': {
                'axis_number': self.axis_number,
                'axis_name': self.axis_name,
                'mece_categories': list(mece_facts.keys()),
                'focus_area': '法的・規制要件遵守制約',
                'priority_level': 'critical'  # 最高優先度
            },
            'data_period': date_range,
            'legal_compliance_indicators': legal_compliance_indicators,
            'data_quality': data_quality,
            'regulatory_frameworks': [
                '労働基準法',
                '介護保険法', 
                '労働安全衛生法',
                '労働契約法',
                '労働者派遣法',
                '個人情報保護法'
            ],
            'extraction_statistics': {
                'total_facts_extracted': sum(len(facts) for facts in mece_facts.values()),
                'critical_violations': len([f for facts in mece_facts.values() for f in facts if '重大リスク' in f]),
                'legal_compliance_facts': len([f for facts in mece_facts.values() for f in facts if '遵守' in f or '適合' in f]),
                'improvement_required_facts': len([f for facts in mece_facts.values() for f in facts if '要改善' in f or '確認必要' in f]),
                'categories_with_facts': len([cat for cat, facts in mece_facts.items() if facts and not any('検出されませんでした' in f for f in facts)])
            }
        }