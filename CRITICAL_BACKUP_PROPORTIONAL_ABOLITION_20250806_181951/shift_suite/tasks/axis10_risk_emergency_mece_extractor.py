#!/usr/bin/env python3
"""
軸10: リスク・緊急時対応 MECE事実抽出エンジン

12軸分析フレームワークの軸10を担当
過去シフト実績からリスク管理・緊急時対応に関する制約を抽出
軸7（法的要件）の実践的適用として安全確保の要となる軸

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

class RiskEmergencyMECEFactExtractor:
    """軸10: リスク・緊急時対応のMECE事実抽出器"""
    
    def __init__(self):
        self.axis_number = 10
        self.axis_name = "リスク・緊急時対応"
        
        # リスク管理基準値
        self.risk_standards = {
            'min_emergency_staff': 2,          # 緊急時最低人員
            'max_response_time_minutes': 5,    # 緊急対応時間（分）
            'min_24h_coverage_ratio': 0.95,   # 24時間カバレッジ最低比率
            'max_single_staff_hours': 4,      # 単独勤務最大時間
            'min_medical_qualified_ratio': 0.3, # 医療資格者最低比率
            'max_continuous_risk_days': 3,    # 連続リスク状態最大日数
            'min_backup_staff_ratio': 0.2,    # バックアップ要員最低比率
            'emergency_contact_response_hours': 1  # 緊急連絡対応時間
        }
        
    def extract_axis10_risk_emergency_rules(self, long_df: pd.DataFrame, wt_df: pd.DataFrame = None) -> Dict[str, Any]:
        """
        軸10: リスク・緊急時対応ルールをMECE分解により抽出
        
        Args:
            long_df: 過去のシフト実績データ
            wt_df: 勤務区分マスタ（オプション）
            
        Returns:
            Dict: 抽出結果（human_readable, machine_readable, extraction_metadata）
        """
        log.info(f"🚨 軸10: {self.axis_name} MECE事実抽出を開始")
        
        try:
            # データ品質チェック
            if long_df.empty:
                raise ValueError("長期データが空です")
            
            # 軸10のMECE分解カテゴリー（8つ）
            mece_facts = {
                "緊急事態対応制約": self._extract_emergency_response_constraints(long_df, wt_df),
                "事故防止制約": self._extract_accident_prevention_constraints(long_df, wt_df),
                "医療緊急対応制約": self._extract_medical_emergency_constraints(long_df, wt_df),
                "災害対策制約": self._extract_disaster_preparedness_constraints(long_df, wt_df),
                "セキュリティ制約": self._extract_security_constraints(long_df, wt_df),
                "事業継続制約": self._extract_business_continuity_constraints(long_df, wt_df),
                "リスク監視制約": self._extract_risk_monitoring_constraints(long_df, wt_df),
                "危機管理制約": self._extract_crisis_management_constraints(long_df, wt_df)
            }
            
            # 人間可読形式の結果生成
            human_readable = self._generate_human_readable_results(mece_facts, long_df)
            
            # 機械可読形式の制約生成
            machine_readable = self._generate_machine_readable_constraints(mece_facts, long_df)
            
            # 抽出メタデータ
            extraction_metadata = self._generate_extraction_metadata(long_df, wt_df, mece_facts)
            
            log.info(f"✅ 軸10: {self.axis_name} MECE事実抽出完了")
            
            return {
                'human_readable': human_readable,
                'machine_readable': machine_readable,
                'extraction_metadata': extraction_metadata
            }
            
        except Exception as e:
            log.error(f"❌ 軸10: {self.axis_name} 抽出エラー: {str(e)}")
            raise e
    
    def _extract_emergency_response_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """緊急事態対応制約の抽出"""
        constraints = []
        
        try:
            # 24時間緊急対応体制の確保
            if 'ds' in long_df.columns and 'staff' in long_df.columns:
                long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                
                # 各時間帯での人員配置
                hourly_staff_counts = long_df.groupby('hour')['staff'].nunique()
                
                # 無人時間帯の検出
                zero_staff_hours = hourly_staff_counts[hourly_staff_counts == 0]
                single_staff_hours = hourly_staff_counts[hourly_staff_counts == 1]
                
                if len(zero_staff_hours) > 0:
                    constraints.append(f"【重大リスク】無人時間帯: {len(zero_staff_hours)}時間 - 緊急対応不可")
                    constraints.append("緊急事態対応体制未確立 - 24時間人員配置必須")
                else:
                    constraints.append("24時間人員配置確保: 緊急対応体制基盤確立")
                
                # 単独勤務リスク
                if len(single_staff_hours) > 0:
                    single_risk_ratio = len(single_staff_hours) / 24
                    constraints.append(f"単独勤務時間: {single_risk_ratio:.1%} ({len(single_staff_hours)}時間)")
                    
                    if single_risk_ratio > 0.3:
                        constraints.append("【リスク】単独勤務多発 - 緊急時協力体制不足")
                    else:
                        constraints.append("単独勤務制限良好: 緊急時協力体制確保")
                
                # 緊急対応可能な人員数
                multi_staff_hours = hourly_staff_counts[hourly_staff_counts >= 2]
                emergency_ready_ratio = len(multi_staff_hours) / 24
                constraints.append(f"緊急対応可能時間: {emergency_ready_ratio:.1%} (2名以上配置)")
                
                if emergency_ready_ratio >= 0.8:
                    constraints.append("緊急対応体制充実: 高度な緊急事態対応可能")
                elif emergency_ready_ratio >= 0.5:
                    constraints.append("緊急対応体制基本: 標準的緊急事態対応可能")
                else:
                    constraints.append("【要強化】緊急対応体制 - 人員増強による体制強化必要")
            
            # 緊急時リーダーシップ体制
            if 'role' in long_df.columns:
                leadership_roles = ['管理者', '主任', 'リーダー', '師長', 'チーフ', '看護師']
                emergency_leaders = long_df[
                    long_df['role'].str.contains('|'.join(leadership_roles), case=False, na=False)
                ]
                
                if not emergency_leaders.empty:
                    leader_coverage_ratio = len(emergency_leaders) / len(long_df)
                    constraints.append(f"緊急時リーダー配置: {leader_coverage_ratio:.1%} - 指揮命令系統")
                    
                    # リーダーの時間帯カバレッジ
                    if 'ds' in long_df.columns:
                        leader_time_coverage = emergency_leaders.groupby(
                            pd.to_datetime(emergency_leaders['ds']).dt.hour
                        )['staff'].nunique()
                        leader_hour_coverage = (leader_time_coverage > 0).sum() / 24
                        
                        constraints.append(f"リーダー時間カバレッジ: {leader_hour_coverage:.1%}")
                        
                        if leader_hour_coverage >= 0.7:
                            constraints.append("リーダーシップ体制良好: 継続的指揮可能")
                        else:
                            constraints.append("【要改善】リーダーシップ継続性 - 指揮体制強化必要")
                else:
                    constraints.append("【重大リスク】緊急時リーダー不在 - 指揮命令系統未確立")
            
            # 緊急連絡・通報体制
            if 'employment' in long_df.columns:
                # 常勤職員による緊急時継続対応
                permanent_staff = long_df[
                    long_df['employment'].str.contains('正社員|正規|常勤', case=False, na=False)
                ]
                
                if not permanent_staff.empty:
                    permanent_ratio = len(permanent_staff) / len(long_df)
                    constraints.append(f"常勤緊急対応要員: {permanent_ratio:.1%} - 緊急連絡継続性")
                    
                    if permanent_ratio >= 0.5:
                        constraints.append("緊急連絡体制安定: 継続的緊急対応可能")
                    else:
                        constraints.append("【要強化】緊急連絡体制 - 常勤要員増強必要")
                else:
                    constraints.append("【リスク】常勤緊急対応要員不足 - 連絡体制継続性リスク")
            
            # 夜間・休日緊急対応体制
            if 'ds' in long_df.columns:
                long_df['weekday'] = pd.to_datetime(long_df['ds']).dt.day_name()
                long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                
                # 夜間緊急対応（22時-6時）
                night_hours = list(range(22, 24)) + list(range(0, 6))
                night_emergency_data = long_df[long_df['hour'].isin(night_hours)]
                
                if not night_emergency_data.empty:
                    night_staff_adequacy = night_emergency_data.groupby('hour')['staff'].nunique()
                    adequate_night_hours = (night_staff_adequacy >= 2).sum()
                    night_adequacy_ratio = adequate_night_hours / len(night_hours)
                    
                    constraints.append(f"夜間緊急対応体制: {night_adequacy_ratio:.1%} - 深夜緊急事態対応")
                    
                    if night_adequacy_ratio >= 0.6:
                        constraints.append("夜間緊急体制良好: 深夜緊急事態対応可能")
                    else:
                        constraints.append("【リスク】夜間緊急体制不足 - 深夜対応強化必要")
                
                # 休日緊急対応
                weekend_data = long_df[long_df['weekday'].isin(['Saturday', 'Sunday'])]
                if not weekend_data.empty:
                    weekend_emergency_ratio = len(weekend_data) / len(long_df)
                    constraints.append(f"休日緊急対応配置: {weekend_emergency_ratio:.1%}")
                    
                    if weekend_emergency_ratio >= 0.15:  # 週7日中2日=約28%、最低15%
                        constraints.append("休日緊急体制確保: 週末緊急事態対応可能")
                    else:
                        constraints.append("【要検討】休日緊急体制 - 週末対応強化検討")
                
        except Exception as e:
            log.warning(f"緊急事態対応制約抽出エラー: {e}")
            constraints.append("緊急事態対応制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["緊急事態対応に関する制約は検出されませんでした"]
    
    def _extract_accident_prevention_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """事故防止制約の抽出"""
        constraints = []
        
        try:
            # 疲労による事故リスクの防止
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                # 連続勤務による疲労蓄積リスク
                high_risk_staff = []
                
                for staff_id in long_df['staff'].unique():
                    staff_dates = pd.to_datetime(long_df[long_df['staff'] == staff_id]['ds']).sort_values()
                    
                    if len(staff_dates) > 1:
                        # 連続勤務期間の計算
                        consecutive_periods = self._find_consecutive_work_periods(staff_dates)
                        max_consecutive = max(consecutive_periods) if consecutive_periods else 0
                        
                        # 7日以上連続勤務を高リスクとする
                        if max_consecutive >= 7:
                            high_risk_staff.append((staff_id, max_consecutive))
                
                if high_risk_staff:
                    risk_ratio = len(high_risk_staff) / long_df['staff'].nunique()
                    max_risk_days = max([days for _, days in high_risk_staff])
                    constraints.append(f"疲労事故リスク: {risk_ratio:.1%}のスタッフ (最大{max_risk_days}日連続)")
                    constraints.append("【安全リスク】過度連続勤務による事故リスク - 休息確保必要")
                else:
                    constraints.append("疲労事故リスク低: 適切な休息による事故防止")
            
            # 夜間事故防止体制
            if 'ds' in long_df.columns and 'code' in long_df.columns:
                # 夜勤時の安全確保
                night_shift_codes = ['夜勤', 'ナイト', 'night', 'N', '夜間']
                night_shifts = long_df[
                    long_df['code'].str.contains('|'.join(night_shift_codes), case=False, na=False)
                ]
                
                if not night_shifts.empty:
                    # 夜勤時の複数人員配置（事故防止）
                    night_multi_staff_days = night_shifts.groupby('ds')['staff'].nunique()
                    safe_night_days = (night_multi_staff_days >= 2).sum()
                    total_night_days = len(night_multi_staff_days)
                    
                    if total_night_days > 0:
                        night_safety_ratio = safe_night_days / total_night_days
                        constraints.append(f"夜間安全体制: {night_safety_ratio:.1%} (複数人員配置)")
                        
                        if night_safety_ratio >= 0.8:
                            constraints.append("夜間事故防止体制良好: 相互見守り・支援可能")
                        elif night_safety_ratio >= 0.5:
                            constraints.append("夜間事故防止体制標準: 基本的安全確保")
                        else:
                            constraints.append("【安全リスク】夜間単独勤務多発 - 事故防止体制強化必要")
            
            # 新人・未熟練者の事故防止
            if 'employment' in long_df.columns and 'staff' in long_df.columns:
                # 非正規雇用を新人・未熟練者の代理指標とする
                inexperienced_types = ['パート', 'アルバイト', '派遣', '契約']
                inexperienced_staff = long_df[
                    long_df['employment'].str.contains('|'.join(inexperienced_types), case=False, na=False)
                ]
                
                if not inexperienced_staff.empty:
                    inexperienced_ratio = len(inexperienced_staff) / len(long_df)
                    
                    # 未熟練者の単独配置リスク
                    if 'ds' in long_df.columns:
                        daily_inexperienced = inexperienced_staff.groupby('ds')['staff'].nunique()
                        daily_total_staff = long_df.groupby('ds')['staff'].nunique()
                        
                        # 未熟練者のみの日を特定
                        risky_days = 0
                        for date in daily_inexperienced.index:
                            if date in daily_total_staff.index:
                                if daily_inexperienced[date] == daily_total_staff[date]:
                                    risky_days += 1
                        
                        if risky_days > 0:
                            risk_day_ratio = risky_days / len(daily_total_staff)
                            constraints.append(f"【安全リスク】未熟練者のみ配置: {risk_day_ratio:.1%} - 指導者配置必要")
                        else:
                            constraints.append("未熟練者指導体制良好: 経験者との混在配置")
                    
                    constraints.append(f"未熟練者配置率: {inexperienced_ratio:.1%} - 事故防止指導必要")
                else:
                    constraints.append("熟練者中心配置: 事故リスク最小化")
            
            # 利用者事故防止体制
            if 'role' in long_df.columns:
                # 見守り・観察可能な職種配置
                observation_roles = ['看護師', '介護士', '介護福祉士', 'ヘルパー']
                observation_staff = long_df[
                    long_df['role'].str.contains('|'.join(observation_roles), case=False, na=False)
                ]
                
                if not observation_staff.empty:
                    observation_ratio = len(observation_staff) / len(long_df)
                    constraints.append(f"利用者見守り体制: {observation_ratio:.1%} - 事故防止観察")
                    
                    if observation_ratio >= 0.8:
                        constraints.append("利用者事故防止体制充実: 継続的見守り可能")
                    elif observation_ratio >= 0.6:
                        constraints.append("利用者事故防止体制基本: 標準的見守り実施")
                    else:
                        constraints.append("【要強化】利用者見守り不足 - 事故防止体制強化必要")
                else:
                    constraints.append("【重大リスク】見守り要員不足 - 利用者事故リスク高")
            
            # 転倒・転落事故防止（移動支援体制）
            if 'role' in long_df.columns and 'ds' in long_df.columns:
                # 移動支援可能な職種の配置
                mobility_support_roles = ['介護士', '介護福祉士', 'PT', '理学療法士', 'OT', '作業療法士']
                mobility_staff = long_df[
                    long_df['role'].str.contains('|'.join(mobility_support_roles), case=False, na=False)
                ]
                
                if not mobility_staff.empty:
                    # 日中時間帯での移動支援体制
                    long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                    daytime_hours = range(8, 18)
                    daytime_mobility = mobility_staff[
                        pd.to_datetime(mobility_staff['ds']).dt.hour.isin(daytime_hours)
                    ]
                    
                    if not daytime_mobility.empty:
                        daytime_mobility_coverage = len(daytime_mobility) / len(
                            long_df[pd.to_datetime(long_df['ds']).dt.hour.isin(daytime_hours)]
                        )
                        constraints.append(f"日中移動支援体制: {daytime_mobility_coverage:.1%} - 転倒防止")
                        
                        if daytime_mobility_coverage >= 0.7:
                            constraints.append("転倒防止体制良好: 十分な移動支援可能")
                        else:
                            constraints.append("【要注意】転倒防止体制 - 移動支援強化検討")
                else:
                    constraints.append("【リスク】移動支援要員不足 - 転倒事故リスク")
            
            # 薬剤事故防止体制
            if 'role' in long_df.columns:
                medication_roles = ['看護師', '准看護師', '薬剤師']
                medication_staff = long_df[
                    long_df['role'].str.contains('|'.join(medication_roles), case=False, na=False)
                ]
                
                if not medication_staff.empty:
                    medication_safety_ratio = len(medication_staff) / len(long_df)
                    constraints.append(f"薬剤管理体制: {medication_safety_ratio:.1%} - 投薬事故防止")
                    
                    if medication_safety_ratio >= 0.3:
                        constraints.append("薬剤事故防止体制良好: 適切な投薬管理可能")
                    else:
                        constraints.append("【要検討】薬剤管理体制 - 投薬事故防止強化検討")
                else:
                    constraints.append("薬剤管理要員なし: 外部管理または投薬なし")
                
        except Exception as e:
            log.warning(f"事故防止制約抽出エラー: {e}")
            constraints.append("事故防止制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["事故防止に関する制約は検出されませんでした"]
    
    def _extract_medical_emergency_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """医療緊急対応制約の抽出"""
        constraints = []
        
        try:
            # 医療緊急事態対応可能職種の配置
            if 'role' in long_df.columns:
                medical_emergency_roles = ['看護師', '准看護師', '医師', '救急救命士']
                medical_responders = long_df[
                    long_df['role'].str.contains('|'.join(medical_emergency_roles), case=False, na=False)
                ]
                
                if not medical_responders.empty:
                    medical_response_ratio = len(medical_responders) / len(long_df)
                    constraints.append(f"医療緊急対応要員: {medical_response_ratio:.1%} - 医療緊急事態対応")
                    
                    # 24時間医療緊急対応体制
                    if 'ds' in long_df.columns:
                        long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                        medical_hourly_coverage = medical_responders.groupby(
                            pd.to_datetime(medical_responders['ds']).dt.hour
                        )['staff'].nunique()
                        
                        covered_hours = (medical_hourly_coverage > 0).sum()
                        medical_time_coverage = covered_hours / 24
                        
                        constraints.append(f"医療緊急時間カバレッジ: {medical_time_coverage:.1%}")
                        
                        if medical_time_coverage >= 0.8:
                            constraints.append("医療緊急体制充実: 24時間医療対応可能")
                        elif medical_time_coverage >= 0.5:
                            constraints.append("医療緊急体制部分: 主要時間帯医療対応可能")
                        else:
                            constraints.append("【医療リスク】医療緊急体制不足 - 医療対応強化必要")
                else:
                    constraints.append("【重大医療リスク】医療緊急対応要員不在 - 外部医療連携必須")
            
            # 心肺蘇生・応急処置対応
            if 'role' in long_df.columns and 'employment' in long_df.columns:
                # 医療資格者または訓練済みスタッフの推定
                cpr_capable_roles = ['看護師', '准看護師', '医師', '救急', '介護福祉士']
                cpr_staff = long_df[
                    long_df['role'].str.contains('|'.join(cpr_capable_roles), case=False, na=False)
                ]
                
                if not cpr_staff.empty:
                    cpr_capability_ratio = len(cpr_staff) / len(long_df)
                    constraints.append(f"心肺蘇生対応要員: {cpr_capability_ratio:.1%} - 生命救急対応")
                    
                    # 常時心肺蘇生対応可能体制
                    if 'ds' in long_df.columns:
                        daily_cpr_coverage = cpr_staff.groupby('ds')['staff'].nunique()
                        cpr_covered_days = (daily_cpr_coverage > 0).sum()
                        total_days = long_df['ds'].dt.date.nunique()
                        cpr_day_coverage = cpr_covered_days / total_days
                        
                        constraints.append(f"心肺蘇生日次カバレッジ: {cpr_day_coverage:.1%}")
                        
                        if cpr_day_coverage >= 0.95:
                            constraints.append("心肺蘇生体制完備: 常時生命救急対応可能")
                        elif cpr_day_coverage >= 0.8:
                            constraints.append("心肺蘇生体制良好: ほぼ常時対応可能")
                        else:
                            constraints.append("【生命リスク】心肺蘇生体制不足 - 緊急時生命救急リスク")
                else:
                    constraints.append("【重大生命リスク】心肺蘇生対応要員不在 - 緊急時生命危険")
            
            # 医療機器操作・管理体制
            if 'role' in long_df.columns:
                medical_equipment_roles = ['看護師', '准看護師', '医師', '臨床工学技士']
                equipment_operators = long_df[
                    long_df['role'].str.contains('|'.join(medical_equipment_roles), case=False, na=False)
                ]
                
                if not equipment_operators.empty:
                    equipment_capability = len(equipment_operators) / len(long_df)
                    constraints.append(f"医療機器操作要員: {equipment_capability:.1%} - 医療機器緊急対応")
                    
                    if equipment_capability >= 0.4:
                        constraints.append("医療機器緊急対応良好: 機器トラブル対応可能")
                    else:
                        constraints.append("【要注意】医療機器対応 - 機器緊急時対応強化検討")
                else:
                    constraints.append("医療機器対応要員なし: 機器使用制限または外部対応")
            
            # 感染症緊急対応体制
            if 'role' in long_df.columns:
                infection_control_roles = ['看護師', '医師', '感染管理認定看護師', 'ICN']
                infection_responders = long_df[
                    long_df['role'].str.contains('|'.join(infection_control_roles), case=False, na=False)
                ]
                
                if not infection_responders.empty:
                    infection_response_ratio = len(infection_responders) / len(long_df)
                    constraints.append(f"感染症緊急対応: {infection_response_ratio:.1%} - 感染拡大防止")
                    
                    # 感染症対応の継続性
                    if 'ds' in long_df.columns:
                        infection_daily_coverage = infection_responders.groupby('ds')['staff'].nunique()
                        infection_coverage_days = (infection_daily_coverage > 0).sum()
                        total_days = long_df['ds'].dt.date.nunique()
                        infection_continuity = infection_coverage_days / total_days
                        
                        if infection_continuity >= 0.8:
                            constraints.append("感染症対応継続性良好: 常時感染防止対応可能")
                        else:
                            constraints.append("【感染リスク】感染症対応継続性不足 - 感染拡大リスク")
                else:
                    constraints.append("【感染リスク】感染症対応専門要員不足 - 感染拡大防止体制要強化")
            
            # 精神科緊急対応体制
            if 'role' in long_df.columns:
                psychiatric_roles = ['精神保健福祉士', 'PSW', '精神科医', '臨床心理士']
                psychiatric_responders = long_df[
                    long_df['role'].str.contains('|'.join(psychiatric_roles), case=False, na=False)
                ]
                
                if not psychiatric_responders.empty:
                    psychiatric_ratio = len(psychiatric_responders) / len(long_df)
                    constraints.append(f"精神科緊急対応: {psychiatric_ratio:.1%} - 精神的危機対応")
                    constraints.append("精神科緊急体制配備: 精神的危機・行動障害対応可能")
                else:
                    # 一般職員による対応体制
                    general_responders = long_df[
                        long_df['role'].str.contains('介護士|看護師', case=False, na=False)
                    ]
                    if not general_responders.empty:
                        constraints.append("精神科緊急対応: 一般職員対応 - 専門対応強化検討")
                    else:
                        constraints.append("【要検討】精神科緊急対応体制 - 危機対応準備必要")
            
            # 小児・高齢者特別医療緊急対応
            if 'role' in long_df.columns:
                # 高齢者医療に特化した対応
                geriatric_roles = ['老人看護', 'geriatric', '高齢者', '認知症']
                geriatric_responders = long_df[
                    long_df['role'].str.contains('|'.join(geriatric_roles), case=False, na=False)
                ]
                
                if not geriatric_responders.empty:
                    geriatric_ratio = len(geriatric_responders) / len(long_df)
                    constraints.append(f"高齢者医療緊急対応: {geriatric_ratio:.1%} - 高齢者特有緊急事態対応")
                else:
                    # 一般的な医療緊急対応での代替
                    general_medical = long_df[
                        long_df['role'].str.contains('看護師|医師', case=False, na=False)
                    ]
                    if not general_medical.empty:
                        constraints.append("高齢者緊急対応: 一般医療職対応 - 高齢者特化訓練推奨")
                    else:
                        constraints.append("【高齢者リスク】高齢者医療緊急対応不足 - 専門対応体制整備必要")
                
        except Exception as e:
            log.warning(f"医療緊急対応制約抽出エラー: {e}")
            constraints.append("医療緊急対応制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["医療緊急対応に関する制約は検出されませんでした"]
    
    def _extract_disaster_preparedness_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """災害対策制約の抽出"""
        constraints = []
        
        try:
            # 災害時継続運営体制
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                # 災害時最低限必要人員の確保
                daily_staff_counts = long_df.groupby('ds')['staff'].nunique()
                min_daily_staff = daily_staff_counts.min()
                avg_daily_staff = daily_staff_counts.mean()
                
                # 最低人員での運営可能性
                disaster_continuity_ratio = min_daily_staff / avg_daily_staff if avg_daily_staff > 0 else 0
                constraints.append(f"災害時運営継続性: 最低{min_daily_staff}名 (平均の{disaster_continuity_ratio:.1%})")
                
                if disaster_continuity_ratio >= 0.6:
                    constraints.append("災害時運営継続可能: 最低限人員で基本サービス維持")
                elif disaster_continuity_ratio >= 0.4:
                    constraints.append("災害時運営制限: 縮小サービスでの継続可能")
                else:
                    constraints.append("【災害リスク】運営継続困難 - 災害時人員確保計画必要")
            
            # 災害対応リーダーシップ体制
            if 'role' in long_df.columns and 'employment' in long_df.columns:
                # 災害時指揮可能な管理職
                disaster_leaders = long_df[
                    (long_df['role'].str.contains('管理者|主任|リーダー|師長', case=False, na=False)) &
                    (long_df['employment'].str.contains('正社員|正規|常勤', case=False, na=False))
                ]
                
                if not disaster_leaders.empty:
                    disaster_leadership_ratio = len(disaster_leaders) / len(long_df)
                    constraints.append(f"災害時指揮体制: {disaster_leadership_ratio:.1%} - 災害時リーダーシップ")
                    
                    # 災害時指揮の継続性
                    if 'ds' in long_df.columns:
                        leader_coverage_days = disaster_leaders['ds'].dt.date.nunique()
                        total_days = long_df['ds'].dt.date.nunique()
                        leader_continuity = leader_coverage_days / total_days
                        
                        if leader_continuity >= 0.8:
                            constraints.append("災害時指揮継続性良好: 常時災害対応指揮可能")
                        else:
                            constraints.append("【要強化】災害時指揮継続性 - 指揮体制強化必要")
                else:
                    constraints.append("【災害リスク】災害時指揮要員不足 - 災害対応指揮体制未整備")
            
            # 避難支援体制
            if 'role' in long_df.columns:
                # 避難支援可能職種
                evacuation_support_roles = ['介護士', '介護福祉士', 'PT', 'OT', '看護師']
                evacuation_supporters = long_df[
                    long_df['role'].str.contains('|'.join(evacuation_support_roles), case=False, na=False)
                ]
                
                if not evacuation_supporters.empty:
                    evacuation_support_ratio = len(evacuation_supporters) / len(long_df)
                    constraints.append(f"避難支援体制: {evacuation_support_ratio:.1%} - 災害時避難誘導")
                    
                    if evacuation_support_ratio >= 0.7:
                        constraints.append("避難支援体制充実: 十分な避難誘導・支援可能")
                    elif evacuation_support_ratio >= 0.5:
                        constraints.append("避難支援体制基本: 標準的避難支援可能")
                    else:
                        constraints.append("【災害リスク】避難支援不足 - 災害時避難支援強化必要")
                else:
                    constraints.append("【重大災害リスク】避難支援要員不在 - 災害時避難困難")
            
            # 災害時医療継続体制
            if 'role' in long_df.columns:
                disaster_medical_roles = ['看護師', '准看護師', '医師']
                disaster_medical_staff = long_df[
                    long_df['role'].str.contains('|'.join(disaster_medical_roles), case=False, na=False)
                ]
                
                if not disaster_medical_staff.empty:
                    disaster_medical_ratio = len(disaster_medical_staff) / len(long_df)
                    constraints.append(f"災害時医療継続: {disaster_medical_ratio:.1%} - 災害時医療サービス")
                    
                    if disaster_medical_ratio >= 0.3:
                        constraints.append("災害時医療継続可能: 基本医療サービス維持")
                    else:
                        constraints.append("【医療災害リスク】災害時医療不足 - 医療継続体制強化必要")
                else:
                    constraints.append("【重大医療災害リスク】災害時医療要員不在 - 医療継続不可")
            
            # 災害時通信・連絡体制
            if 'employment' in long_df.columns:
                # 災害時連絡責任者（常勤職員）
                disaster_communication = long_df[
                    long_df['employment'].str.contains('正社員|正規|常勤', case=False, na=False)
                ]
                
                if not disaster_communication.empty:
                    communication_ratio = len(disaster_communication) / len(long_df)
                    constraints.append(f"災害時連絡体制: {communication_ratio:.1%} - 災害時情報伝達")
                    
                    if communication_ratio >= 0.5:
                        constraints.append("災害時連絡体制良好: 安定した情報伝達可能")
                    else:
                        constraints.append("【要強化】災害時連絡体制 - 情報伝達強化必要")
                else:
                    constraints.append("【災害リスク】災害時連絡要員不足 - 情報伝達体制未整備")
            
            # 災害時物資・設備管理
            if 'role' in long_df.columns:
                facility_management_roles = ['管理者', '施設長', '事務', '総務']
                facility_managers = long_df[
                    long_df['role'].str.contains('|'.join(facility_management_roles), case=False, na=False)
                ]
                
                if not facility_managers.empty:
                    facility_management_ratio = len(facility_managers) / len(long_df)
                    constraints.append(f"災害時設備管理: {facility_management_ratio:.1%} - 災害時施設管理")
                    
                    if facility_management_ratio >= 0.1:
                        constraints.append("災害時施設管理体制確保: 設備・物資管理可能")
                    else:
                        constraints.append("【要検討】災害時施設管理 - 設備管理体制整備検討")
                else:
                    constraints.append("災害時施設管理要員なし: 外部管理または分散管理")
            
            # 近隣施設・地域との連携体制（推定）
            if 'ds' in long_df.columns:
                # 勤務パターンから地域連携の可能性を推定
                operation_days = long_df['ds'].dt.date.nunique()
                operation_period = (long_df['ds'].max() - long_df['ds'].min()).days + 1
                operation_continuity = operation_days / operation_period if operation_period > 0 else 0
                
                if operation_continuity >= 0.9:
                    constraints.append("運営継続性高: 地域災害時連携基盤良好")
                elif operation_continuity >= 0.7:
                    constraints.append("運営継続性中: 地域災害時連携可能")
                else:
                    constraints.append("【要検討】運営継続性 - 地域災害時連携体制整備必要")
                
        except Exception as e:
            log.warning(f"災害対策制約抽出エラー: {e}")
            constraints.append("災害対策制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["災害対策に関する制約は検出されませんでした"]
    
    def _extract_security_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """セキュリティ制約の抽出"""
        constraints = []
        
        try:
            # 施設セキュリティ管理体制
            if 'role' in long_df.columns:
                security_roles = ['管理者', '警備', 'セキュリティ', '受付', '事務']
                security_staff = long_df[
                    long_df['role'].str.contains('|'.join(security_roles), case=False, na=False)
                ]
                
                if not security_staff.empty:
                    security_ratio = len(security_staff) / len(long_df)
                    constraints.append(f"セキュリティ管理体制: {security_ratio:.1%} - 施設安全管理")
                    
                    # 24時間セキュリティ体制
                    if 'ds' in long_df.columns:
                        long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                        security_hourly = security_staff.groupby(
                            pd.to_datetime(security_staff['ds']).dt.hour
                        )['staff'].nunique()
                        
                        secured_hours = (security_hourly > 0).sum()
                        security_coverage = secured_hours / 24
                        
                        constraints.append(f"セキュリティ時間カバレッジ: {security_coverage:.1%}")
                        
                        if security_coverage >= 0.8:
                            constraints.append("24時間セキュリティ体制良好: 常時安全管理")
                        elif security_coverage >= 0.5:
                            constraints.append("部分セキュリティ体制: 主要時間帯安全管理")
                        else:
                            constraints.append("【セキュリティリスク】安全管理不足 - セキュリティ強化必要")
                else:
                    constraints.append("【セキュリティリスク】専門セキュリティ要員不在 - 安全管理体制要整備")
            
            # 夜間セキュリティ体制
            if 'ds' in long_df.columns and 'staff' in long_df.columns:
                long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                
                # 夜間（22時-6時）のセキュリティ
                night_hours = list(range(22, 24)) + list(range(0, 6))
                night_security = long_df[long_df['hour'].isin(night_hours)]
                
                if not night_security.empty:
                    night_staff_counts = night_security.groupby('hour')['staff'].nunique()
                    min_night_staff = night_staff_counts.min()
                    
                    constraints.append(f"夜間セキュリティ: 最低{min_night_staff}名配置")
                    
                    if min_night_staff >= 2:
                        constraints.append("夜間セキュリティ良好: 複数名による安全確保")
                    elif min_night_staff >= 1:
                        constraints.append("夜間セキュリティ基本: 単独警備・要注意")
                    else:
                        constraints.append("【重大セキュリティリスク】夜間無人 - 施設安全確保不可")
                else:
                    constraints.append("【セキュリティリスク】夜間セキュリティデータなし")
            
            # 利用者・訪問者管理体制
            if 'role' in long_df.columns:
                reception_roles = ['受付', '事務', '管理者', '相談員']
                reception_staff = long_df[
                    long_df['role'].str.contains('|'.join(reception_roles), case=False, na=False)
                ]
                
                if not reception_staff.empty:
                    reception_ratio = len(reception_staff) / len(long_df)
                    constraints.append(f"受付・管理体制: {reception_ratio:.1%} - 出入管理")
                    
                    # 日中時間帯での受付体制
                    if 'ds' in long_df.columns:
                        long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                        business_hours = range(9, 17)
                        business_reception = reception_staff[
                            pd.to_datetime(reception_staff['ds']).dt.hour.isin(business_hours)
                        ]
                        
                        if not business_reception.empty:
                            business_reception_coverage = len(business_reception) / len(
                                long_df[pd.to_datetime(long_df['ds']).dt.hour.isin(business_hours)]
                            )
                            constraints.append(f"日中受付体制: {business_reception_coverage:.1%}")
                            
                            if business_reception_coverage >= 0.7:
                                constraints.append("受付管理体制良好: 出入管理・セキュリティ確保")
                            else:
                                constraints.append("【要改善】受付管理 - 出入管理強化必要")
                else:
                    constraints.append("【セキュリティリスク】受付管理要員不足 - 出入管理体制未整備")
            
            # 情報セキュリティ管理
            if 'employment' in long_df.columns and 'role' in long_df.columns:
                # 情報管理責任者（常勤管理職）
                info_security_managers = long_df[
                    (long_df['employment'].str.contains('正社員|正規|常勤', case=False, na=False)) &
                    (long_df['role'].str.contains('管理者|事務|システム', case=False, na=False))
                ]
                
                if not info_security_managers.empty:
                    info_security_ratio = len(info_security_managers) / len(long_df)
                    constraints.append(f"情報セキュリティ管理: {info_security_ratio:.1%} - 個人情報保護")
                    
                    if info_security_ratio >= 0.1:
                        constraints.append("情報セキュリティ体制確保: 個人情報保護管理可能")
                    else:
                        constraints.append("【要強化】情報セキュリティ - 個人情報保護体制強化必要")
                else:
                    constraints.append("【情報セキュリティリスク】情報管理要員不足 - データ保護体制未整備")
            
            # 金庫・貴重品管理体制
            if 'role' in long_df.columns:
                valuables_management_roles = ['管理者', '事務', '経理', '会計']
                valuables_managers = long_df[
                    long_df['role'].str.contains('|'.join(valuables_management_roles), case=False, na=False)
                ]
                
                if not valuables_managers.empty:
                    valuables_ratio = len(valuables_managers) / len(long_df)
                    constraints.append(f"貴重品管理体制: {valuables_ratio:.1%} - 金銭・貴重品管理")
                    
                    if valuables_ratio >= 0.05:  # 少数でも専門管理
                        constraints.append("貴重品管理体制確保: 適切な金銭管理可能")
                    else:
                        constraints.append("【要検討】貴重品管理 - 金銭管理体制整備検討")
                else:
                    constraints.append("貴重品管理要員なし: 外部管理または取扱なし")
            
            # 緊急時避難・誘導体制
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                # セキュリティ緊急時の避難誘導可能人員
                daily_staff_for_evacuation = long_df.groupby('ds')['staff'].nunique()
                evacuation_capable_days = (daily_staff_for_evacuation >= 3).sum()  # 3名以上で避難誘導可能
                total_days = long_df['ds'].dt.date.nunique()
                
                evacuation_readiness = evacuation_capable_days / total_days if total_days > 0 else 0
                constraints.append(f"緊急避難誘導体制: {evacuation_readiness:.1%} (3名以上配置日)")
                
                if evacuation_readiness >= 0.8:
                    constraints.append("緊急避難体制良好: 適切な避難誘導可能")
                elif evacuation_readiness >= 0.6:
                    constraints.append("緊急避難体制基本: 標準的避難誘導可能")
                else:
                    constraints.append("【要強化】緊急避難体制 - 避難誘導人員確保必要")
                
        except Exception as e:
            log.warning(f"セキュリティ制約抽出エラー: {e}")
            constraints.append("セキュリティ制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["セキュリティに関する制約は検出されませんでした"]
    
    def _extract_business_continuity_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """事業継続制約の抽出"""
        constraints = []
        
        try:
            # 事業継続のための最低限人員確保
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                daily_staff_counts = long_df.groupby('ds')['staff'].nunique()
                min_staff = daily_staff_counts.min()
                max_staff = daily_staff_counts.max()
                avg_staff = daily_staff_counts.mean()
                
                # 事業継続可能な最低人員比率
                continuity_ratio = min_staff / avg_staff if avg_staff > 0 else 0
                constraints.append(f"事業継続最低人員: {min_staff}名 (平均の{continuity_ratio:.1%})")
                
                if continuity_ratio >= 0.7:
                    constraints.append("事業継続性高: 最低人員でも標準的サービス継続可能")
                elif continuity_ratio >= 0.5:
                    constraints.append("事業継続性中: 最低人員で基本サービス継続可能")
                else:
                    constraints.append("【継続リスク】事業継続困難 - 最低人員確保計画必要")
                
                # 人員変動の安定性
                staff_cv = daily_staff_counts.std() / avg_staff if avg_staff > 0 else 0
                constraints.append(f"人員配置安定性: CV={staff_cv:.2f}")
                
                if staff_cv <= 0.2:
                    constraints.append("人員配置安定: 事業継続性確保")
                elif staff_cv <= 0.4:
                    constraints.append("人員配置やや変動: 事業継続性に注意")
                else:
                    constraints.append("【継続リスク】人員配置不安定 - 事業継続性リスク")
            
            # 核となる常勤職員の確保
            if 'employment' in long_df.columns:
                permanent_staff = long_df[
                    long_df['employment'].str.contains('正社員|正規|常勤', case=False, na=False)
                ]
                
                if not permanent_staff.empty:
                    permanent_ratio = len(permanent_staff) / len(long_df)
                    constraints.append(f"常勤職員比率: {permanent_ratio:.1%} - 事業継続核人員")
                    
                    if permanent_ratio >= 0.6:
                        constraints.append("事業継続核人員充実: 安定した事業継続可能")
                    elif permanent_ratio >= 0.4:
                        constraints.append("事業継続核人員標準: 基本的事業継続可能")
                    else:
                        constraints.append("【継続リスク】核人員不足 - 事業継続性リスク高")
                    
                    # 常勤職員の継続性
                    if 'ds' in long_df.columns:
                        permanent_coverage_days = permanent_staff['ds'].dt.date.nunique()
                        total_days = long_df['ds'].dt.date.nunique()
                        permanent_continuity = permanent_coverage_days / total_days
                        
                        if permanent_continuity >= 0.9:
                            constraints.append("常勤職員継続性良好: 事業運営安定")
                        else:
                            constraints.append("【要注意】常勤職員継続性 - 事業運営安定性要改善")
                else:
                    constraints.append("【重大継続リスク】常勤職員不在 - 事業継続性確保困難")
            
            # 管理機能の継続性
            if 'role' in long_df.columns:
                management_roles = ['管理者', '施設長', '主任', 'リーダー', 'ケアマネ']
                management_staff = long_df[
                    long_df['role'].str.contains('|'.join(management_roles), case=False, na=False)
                ]
                
                if not management_staff.empty:
                    management_ratio = len(management_staff) / len(long_df)
                    constraints.append(f"管理機能継続: {management_ratio:.1%} - 事業運営管理")
                    
                    # 管理機能の日次継続性
                    if 'ds' in long_df.columns:
                        mgmt_daily_coverage = management_staff.groupby('ds')['staff'].nunique()
                        mgmt_covered_days = (mgmt_daily_coverage > 0).sum()
                        total_days = long_df['ds'].dt.date.nunique()
                        mgmt_continuity = mgmt_covered_days / total_days
                        
                        constraints.append(f"管理機能日次継続: {mgmt_continuity:.1%}")
                        
                        if mgmt_continuity >= 0.9:
                            constraints.append("管理機能継続性良好: 事業運営管理安定")
                        elif mgmt_continuity >= 0.7:
                            constraints.append("管理機能継続性標準: 基本的事業管理継続")
                        else:
                            constraints.append("【継続リスク】管理機能不足 - 事業運営管理継続困難")
                else:
                    constraints.append("【重大継続リスク】管理機能不在 - 事業運営管理不可")
            
            # サービス継続のための職種多様性
            if 'role' in long_df.columns:
                role_diversity = long_df['role'].nunique()
                total_shifts = len(long_df)
                diversity_score = role_diversity / total_shifts * 100
                
                constraints.append(f"職種多様性: {role_diversity}職種 (多様性スコア: {diversity_score:.1f})")
                
                if role_diversity >= 5:
                    constraints.append("職種多様性高: 包括的サービス継続可能")
                elif role_diversity >= 3:
                    constraints.append("職種多様性中: 基本サービス継続可能")
                else:
                    constraints.append("【継続リスク】職種多様性低 - サービス継続制限リスク")
            
            # 代替要員・バックアップ体制
            if 'staff' in long_df.columns:
                staff_frequency = long_df['staff'].value_counts()
                
                # 複数回勤務（代替可能）スタッフ
                backup_capable_staff = staff_frequency[staff_frequency >= 3]  # 3回以上勤務
                backup_ratio = len(backup_capable_staff) / len(staff_frequency)
                
                constraints.append(f"代替要員比率: {backup_ratio:.1%} - バックアップ体制")
                
                if backup_ratio >= 0.7:
                    constraints.append("代替要員充実: 十分なバックアップ体制")
                elif backup_ratio >= 0.5:
                    constraints.append("代替要員標準: 基本的バックアップ体制")
                else:
                    constraints.append("【継続リスク】代替要員不足 - バックアップ体制強化必要")
            
            # 外部依存度の分析
            if 'employment' in long_df.columns:
                # 派遣・外部依存度
                external_types = ['派遣', '業務委託', '外部']
                external_staff = long_df[
                    long_df['employment'].str.contains('|'.join(external_types), case=False, na=False)
                ]
                
                if not external_staff.empty:
                    external_dependency = len(external_staff) / len(long_df)
                    constraints.append(f"外部依存度: {external_dependency:.1%} - 事業継続リスク要因")
                    
                    if external_dependency > 0.3:
                        constraints.append("【継続リスク】外部依存度高 - 自立的事業継続強化必要")
                    else:
                        constraints.append("外部依存度適正: 自立的事業継続可能")
                else:
                    constraints.append("外部依存なし: 完全自立的事業継続")
            
            # 事業継続期間の実績
            if 'ds' in long_df.columns:
                operation_period = (long_df['ds'].max() - long_df['ds'].min()).days
                operation_days = long_df['ds'].dt.date.nunique()
                operation_rate = operation_days / (operation_period + 1) if operation_period > 0 else 1
                
                constraints.append(f"事業継続実績: {operation_period}日間中{operation_days}日稼働 ({operation_rate:.1%})")
                
                if operation_rate >= 0.95:
                    constraints.append("事業継続実績優秀: 高い継続性実証")
                elif operation_rate >= 0.85:
                    constraints.append("事業継続実績良好: 安定した継続性")
                else:
                    constraints.append("【要改善】事業継続実績 - 継続性改善必要")
                
        except Exception as e:
            log.warning(f"事業継続制約抽出エラー: {e}")
            constraints.append("事業継続制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["事業継続に関する制約は検出されませんでした"]
    
    def _extract_risk_monitoring_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """リスク監視制約の抽出"""
        constraints = []
        
        try:
            # リスク監視要員の配置
            if 'role' in long_df.columns:
                risk_monitoring_roles = ['管理者', '看護師', '主任', 'リーダー', '安全管理者']
                risk_monitors = long_df[
                    long_df['role'].str.contains('|'.join(risk_monitoring_roles), case=False, na=False)
                ]
                
                if not risk_monitors.empty:
                    risk_monitoring_ratio = len(risk_monitors) / len(long_df)
                    constraints.append(f"リスク監視要員: {risk_monitoring_ratio:.1%} - 危険察知・予防")
                    
                    # 24時間リスク監視体制
                    if 'ds' in long_df.columns:
                        long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                        risk_hourly_coverage = risk_monitors.groupby(
                            pd.to_datetime(risk_monitors['ds']).dt.hour
                        )['staff'].nunique()
                        
                        monitored_hours = (risk_hourly_coverage > 0).sum()
                        monitoring_coverage = monitored_hours / 24
                        
                        constraints.append(f"リスク監視時間カバレッジ: {monitoring_coverage:.1%}")
                        
                        if monitoring_coverage >= 0.8:
                            constraints.append("24時間リスク監視体制良好: 常時危険察知可能")
                        elif monitoring_coverage >= 0.6:
                            constraints.append("部分リスク監視体制: 主要時間帯危険察知可能")
                        else:
                            constraints.append("【監視リスク】リスク監視不足 - 危険察知体制強化必要")
                else:
                    constraints.append("【重大監視リスク】リスク監視要員不在 - 危険察知体制未整備")
            
            # 医療リスク監視体制
            if 'role' in long_df.columns:
                medical_risk_monitors = ['看護師', '准看護師', '医師']
                medical_monitors = long_df[
                    long_df['role'].str.contains('|'.join(medical_risk_monitors), case=False, na=False)
                ]
                
                if not medical_monitors.empty:
                    medical_monitoring_ratio = len(medical_monitors) / len(long_df)
                    constraints.append(f"医療リスク監視: {medical_monitoring_ratio:.1%} - 医療事故予防")
                    
                    # 医療リスク監視の継続性
                    if 'ds' in long_df.columns:
                        medical_coverage_days = medical_monitors['ds'].dt.date.nunique()
                        total_days = long_df['ds'].dt.date.nunique()
                        medical_monitoring_continuity = medical_coverage_days / total_days
                        
                        if medical_monitoring_continuity >= 0.9:
                            constraints.append("医療リスク監視継続性良好: 常時医療事故予防可能")
                        elif medical_monitoring_continuity >= 0.7:
                            constraints.append("医療リスク監視継続性標準: 基本的医療事故予防")
                        else:
                            constraints.append("【医療監視リスク】医療リスク監視不足 - 医療事故予防強化必要")
                else:
                    constraints.append("【重大医療監視リスク】医療リスク監視要員不在 - 医療事故予防不可")
            
            # 転倒・転落リスク監視
            if 'role' in long_df.columns:
                fall_risk_monitors = ['介護士', '介護福祉士', '看護師', 'PT', 'OT']
                fall_monitors = long_df[
                    long_df['role'].str.contains('|'.join(fall_risk_monitors), case=False, na=False)
                ]
                
                if not fall_monitors.empty:
                    fall_monitoring_ratio = len(fall_monitors) / len(long_df)
                    constraints.append(f"転倒リスク監視: {fall_monitoring_ratio:.1%} - 転倒事故予防")
                    
                    if fall_monitoring_ratio >= 0.7:
                        constraints.append("転倒リスク監視充実: 十分な転倒事故予防可能")
                    elif fall_monitoring_ratio >= 0.5:
                        constraints.append("転倒リスク監視標準: 基本的転倒事故予防")
                    else:
                        constraints.append("【転倒監視リスク】転倒リスク監視不足 - 転倒事故予防強化必要")
                else:
                    constraints.append("【重大転倒監視リスク】転倒リスク監視要員不在 - 転倒事故高リスク")
            
            # 感染症リスク監視
            if 'role' in long_df.columns:
                infection_monitors = ['看護師', '医師', '感染管理', 'ICN']
                infection_risk_monitors = long_df[
                    long_df['role'].str.contains('|'.join(infection_monitors), case=False, na=False)
                ]
                
                if not infection_risk_monitors.empty:
                    infection_monitoring_ratio = len(infection_risk_monitors) / len(long_df)
                    constraints.append(f"感染リスク監視: {infection_monitoring_ratio:.1%} - 感染症予防")
                    
                    if infection_monitoring_ratio >= 0.3:
                        constraints.append("感染リスク監視良好: 感染症拡大予防可能")
                    else:
                        constraints.append("【感染監視リスク】感染リスク監視不足 - 感染症予防強化必要")
                else:
                    constraints.append("【重大感染監視リスク】感染リスク監視要員不在 - 感染症拡大リスク高")
            
            # 行動・精神リスク監視
            if 'role' in long_df.columns:
                behavioral_monitors = ['精神保健福祉士', 'PSW', '臨床心理士', '看護師', '介護士']
                behavioral_risk_monitors = long_df[
                    long_df['role'].str.contains('|'.join(behavioral_monitors), case=False, na=False)
                ]
                
                if not behavioral_risk_monitors.empty:
                    behavioral_monitoring_ratio = len(behavioral_risk_monitors) / len(long_df)
                    constraints.append(f"行動リスク監視: {behavioral_monitoring_ratio:.1%} - 行動障害予防")
                    
                    if behavioral_monitoring_ratio >= 0.6:
                        constraints.append("行動リスク監視良好: 行動障害・精神的危機予防可能")
                    else:
                        constraints.append("【行動監視リスク】行動リスク監視不足 - 行動障害予防強化必要")
                else:
                    constraints.append("行動リスク監視要員なし: 一般対応または外部専門連携")
            
            # 設備・環境リスク監視
            if 'role' in long_df.columns:
                facility_monitors = ['管理者', '事務', '設備', '施設管理']
                facility_risk_monitors = long_df[
                    long_df['role'].str.contains('|'.join(facility_monitors), case=False, na=False)
                ]
                
                if not facility_risk_monitors.empty:
                    facility_monitoring_ratio = len(facility_risk_monitors) / len(long_df)
                    constraints.append(f"設備リスク監視: {facility_monitoring_ratio:.1%} - 設備事故予防")
                    
                    if facility_monitoring_ratio >= 0.1:
                        constraints.append("設備リスク監視確保: 設備関連事故予防可能")
                    else:
                        constraints.append("【設備監視リスク】設備リスク監視不足 - 設備事故予防強化必要")
                else:
                    constraints.append("設備リスク監視要員なし: 外部管理または分散監視")
            
            # リスク情報共有・報告体制
            if 'employment' in long_df.columns and 'role' in long_df.columns:
                # リスク情報管理者（常勤管理職）
                risk_info_managers = long_df[
                    (long_df['employment'].str.contains('正社員|正規|常勤', case=False, na=False)) &
                    (long_df['role'].str.contains('管理者|看護師|主任', case=False, na=False))
                ]
                
                if not risk_info_managers.empty:
                    risk_info_ratio = len(risk_info_managers) / len(long_df)
                    constraints.append(f"リスク情報管理: {risk_info_ratio:.1%} - リスク情報共有体制")
                    
                    if risk_info_ratio >= 0.3:
                        constraints.append("リスク情報管理良好: 組織的リスク情報共有可能")
                    else:
                        constraints.append("【情報監視リスク】リスク情報管理不足 - 情報共有体制強化必要")
                else:
                    constraints.append("【重大情報監視リスク】リスク情報管理要員不在 - 組織的リスク管理不可")
                
        except Exception as e:
            log.warning(f"リスク監視制約抽出エラー: {e}")
            constraints.append("リスク監視制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["リスク監視に関する制約は検出されませんでした"]
    
    def _extract_crisis_management_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> List[str]:
        """危機管理制約の抽出"""
        constraints = []
        
        try:
            # 危機管理指揮体制
            if 'role' in long_df.columns and 'employment' in long_df.columns:
                # 危機管理責任者（管理職・常勤）
                crisis_commanders = long_df[
                    (long_df['role'].str.contains('管理者|施設長|統括|director', case=False, na=False)) &
                    (long_df['employment'].str.contains('正社員|正規|常勤', case=False, na=False))
                ]
                
                if not crisis_commanders.empty:
                    crisis_command_ratio = len(crisis_commanders) / len(long_df)
                    constraints.append(f"危機管理指揮体制: {crisis_command_ratio:.1%} - 危機時意思決定")
                    
                    # 危機管理指揮の継続性
                    if 'ds' in long_df.columns:
                        command_coverage_days = crisis_commanders['ds'].dt.date.nunique()
                        total_days = long_df['ds'].dt.date.nunique()
                        command_continuity = command_coverage_days / total_days
                        
                        constraints.append(f"危機管理指揮継続性: {command_continuity:.1%}")
                        
                        if command_continuity >= 0.8:
                            constraints.append("危機管理指揮体制良好: 常時危機対応指揮可能")
                        elif command_continuity >= 0.6:
                            constraints.append("危機管理指揮体制標準: 基本的危機対応指揮可能")
                        else:
                            constraints.append("【危機管理リスク】指揮体制不足 - 危機時意思決定困難")
                else:
                    constraints.append("【重大危機管理リスク】危機管理指揮要員不在 - 危機時意思決定不可")
            
            # 多重危機対応体制
            if 'staff' in long_df.columns and 'ds' in long_df.columns:
                # 同時多重危機対応可能人員
                daily_crisis_response_capacity = long_df.groupby('ds')['staff'].nunique()
                
                # 3名以上で多重危機対応可能とする
                multi_crisis_ready_days = (daily_crisis_response_capacity >= 3).sum()
                total_days = long_df['ds'].dt.date.nunique()
                multi_crisis_readiness = multi_crisis_ready_days / total_days if total_days > 0 else 0
                
                constraints.append(f"多重危機対応体制: {multi_crisis_readiness:.1%} (3名以上配置日)")
                
                if multi_crisis_readiness >= 0.8:
                    constraints.append("多重危機対応体制良好: 同時多発危機対応可能")
                elif multi_crisis_readiness >= 0.6:
                    constraints.append("多重危機対応体制標準: 基本的多重危機対応可能")
                else:
                    constraints.append("【多重危機リスク】多重危機対応不足 - 同時危機対応困難")
            
            # 外部機関連携体制
            if 'role' in long_df.columns:
                external_liaison_roles = ['管理者', '相談員', 'MSW', '看護師']
                external_liaisons = long_df[
                    long_df['role'].str.contains('|'.join(external_liaison_roles), case=False, na=False)
                ]
                
                if not external_liaisons.empty:
                    external_liaison_ratio = len(external_liaisons) / len(long_df)
                    constraints.append(f"外部機関連携体制: {external_liaison_ratio:.1%} - 危機時外部協力")
                    
                    if external_liaison_ratio >= 0.3:
                        constraints.append("外部機関連携良好: 危機時外部協力・支援要請可能")
                    else:
                        constraints.append("【連携リスク】外部機関連携不足 - 危機時外部協力困難")
                else:
                    constraints.append("【重大連携リスク】外部機関連携要員不在 - 危機時孤立リスク")
            
            # 家族・関係者連絡体制
            if 'role' in long_df.columns:
                family_contact_roles = ['相談員', 'MSW', '看護師', '管理者', 'ケアマネ']
                family_contacts = long_df[
                    long_df['role'].str.contains('|'.join(family_contact_roles), case=False, na=False)
                ]
                
                if not family_contacts.empty:
                    family_contact_ratio = len(family_contacts) / len(long_df)
                    constraints.append(f"家族連絡体制: {family_contact_ratio:.1%} - 危機時家族連絡")
                    
                    # 24時間家族連絡体制
                    if 'ds' in long_df.columns:
                        long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
                        family_hourly_coverage = family_contacts.groupby(
                            pd.to_datetime(family_contacts['ds']).dt.hour
                        )['staff'].nunique()
                        
                        family_covered_hours = (family_hourly_coverage > 0).sum()
                        family_time_coverage = family_covered_hours / 24
                        
                        constraints.append(f"家族連絡時間カバレッジ: {family_time_coverage:.1%}")
                        
                        if family_time_coverage >= 0.6:
                            constraints.append("家族連絡体制良好: 危機時迅速家族連絡可能")
                        else:
                            constraints.append("【家族連絡リスク】連絡体制不足 - 危機時家族連絡困難")
                else:
                    constraints.append("【重大家族連絡リスク】家族連絡要員不在 - 危機時家族連絡不可")
            
            # 危機時記録・文書化体制
            if 'role' in long_df.columns:
                documentation_roles = ['事務', '管理者', '看護師', '相談員']
                crisis_documenters = long_df[
                    long_df['role'].str.contains('|'.join(documentation_roles), case=False, na=False)
                ]
                
                if not crisis_documenters.empty:
                    documentation_ratio = len(crisis_documenters) / len(long_df)
                    constraints.append(f"危機時記録体制: {documentation_ratio:.1%} - 危機対応記録")
                    
                    if documentation_ratio >= 0.4:
                        constraints.append("危機時記録体制良好: 危機対応の適切な記録・報告可能")
                    else:
                        constraints.append("【記録リスク】危機時記録不足 - 危機対応記録体制強化必要")
                else:
                    constraints.append("【重大記録リスク】危機時記録要員不在 - 危機対応記録不可")
            
            # 危機後復旧・正常化体制
            if 'role' in long_df.columns and 'employment' in long_df.columns:
                # 復旧責任者（管理職・常勤・多職種）
                recovery_leaders = long_df[
                    (long_df['employment'].str.contains('正社員|正規|常勤', case=False, na=False)) &
                    (long_df['role'].str.contains('管理者|看護師|相談員|事務', case=False, na=False))
                ]
                
                if not recovery_leaders.empty:
                    recovery_ratio = len(recovery_leaders) / len(long_df)
                    constraints.append(f"危機後復旧体制: {recovery_ratio:.1%} - 正常化・復旧管理")
                    
                    # 復旧体制の職種多様性
                    recovery_roles = recovery_leaders['role'].nunique()
                    if recovery_roles >= 3:
                        constraints.append("復旧体制多職種: 包括的危機後復旧可能")
                    elif recovery_roles >= 2:
                        constraints.append("復旧体制複数職種: 基本的危機後復旧可能")
                    else:
                        constraints.append("【復旧リスク】復旧体制単一職種 - 包括的復旧困難")
                    
                    if recovery_ratio >= 0.4:
                        constraints.append("危機後復旧体制良好: 迅速な正常化・復旧可能")
                    else:
                        constraints.append("【復旧リスク】復旧体制不足 - 危機後復旧困難")
                else:
                    constraints.append("【重大復旧リスク】復旧体制要員不在 - 危機後復旧不可")
            
            # 危機時代替リソース確保
            if 'staff' in long_df.columns:
                # バックアップ・代替要員の確保状況
                staff_frequency = long_df['staff'].value_counts()
                flexible_staff = staff_frequency[staff_frequency >= 2]  # 複数回勤務で代替可能
                
                flexibility_ratio = len(flexible_staff) / len(staff_frequency)
                constraints.append(f"危機時代替要員: {flexibility_ratio:.1%} - 危機時人員代替")
                
                if flexibility_ratio >= 0.7:
                    constraints.append("危機時代替要員充実: 危機時人員確保可能")
                elif flexibility_ratio >= 0.5:
                    constraints.append("危機時代替要員標準: 基本的危機時人員確保可能")
                else:
                    constraints.append("【代替要員リスク】代替要員不足 - 危機時人員確保困難")
            
            # 危機時意思決定速度（推定）
            if 'role' in long_df.columns and 'employment' in long_df.columns:
                # 迅速意思決定可能者（管理職・常勤・現場経験）
                quick_decision_makers = long_df[
                    (long_df['role'].str.contains('管理者|主任|リーダー|看護師', case=False, na=False)) &
                    (long_df['employment'].str.contains('正社員|正規|常勤', case=False, na=False))
                ]
                
                if not quick_decision_makers.empty:
                    quick_decision_ratio = len(quick_decision_makers) / len(long_df)
                    constraints.append(f"迅速意思決定要員: {quick_decision_ratio:.1%} - 危機時即断即決")
                    
                    if quick_decision_ratio >= 0.3:
                        constraints.append("迅速意思決定体制良好: 危機時即座の判断・行動可能")
                    else:
                        constraints.append("【意思決定リスク】迅速判断困難 - 危機時意思決定遅延リスク")
                else:
                    constraints.append("【重大意思決定リスク】迅速意思決定要員不在 - 危機時判断不可")
                
        except Exception as e:
            log.warning(f"危機管理制約抽出エラー: {e}")
            constraints.append("危機管理制約の抽出でエラーが発生しました")
        
        return constraints if constraints else ["危機管理に関する制約は検出されませんでした"]
    
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
        
        # リスク重要度別分類
        critical_risks = [fact for facts in mece_facts.values() for fact in facts if any(keyword in fact for keyword in ['重大リスク', '重大', '危険'])]
        high_risks = [fact for facts in mece_facts.values() for fact in facts if any(keyword in fact for keyword in ['リスク', '要強化', '困難'])]
        good_safety = [fact for facts in mece_facts.values() for fact in facts if any(keyword in fact for keyword in ['良好', '充実', '確保'])]
        
        return {
            '抽出事実サマリー': {
                '総事実数': total_facts,
                '分析軸': f'軸{self.axis_number}: {self.axis_name}',
                '分析対象レコード数': len(long_df),
                'MECEカテゴリー数': len(mece_facts),
                **{category: len(facts) for category, facts in mece_facts.items()}
            },
            'MECE分解事実': mece_facts,
            'リスク重要度別分類': {
                '重大リスク事実': critical_risks,
                '高リスク事実': high_risks,
                '安全確保事実': good_safety,
                '要検証事実': [fact for facts in mece_facts.values() for fact in facts if 'エラー' in fact or '検出されませんでした' in fact]
            },
            'リスク対応分野': {
                '緊急対応': [fact for facts in mece_facts.values() for fact in facts if '緊急' in fact],
                '医療安全': [fact for facts in mece_facts.values() for fact in facts if '医療' in fact and ('リスク' in fact or '安全' in fact)],
                '災害対策': [fact for facts in mece_facts.values() for fact in facts if '災害' in fact],
                '事業継続': [fact for facts in mece_facts.values() for fact in facts if '継続' in fact],
                'セキュリティ': [fact for facts in mece_facts.values() for fact in facts if 'セキュリティ' in fact or '安全管理' in fact]
            }
        }
    
    def _generate_machine_readable_constraints(self, mece_facts: Dict[str, List[str]], long_df: pd.DataFrame) -> Dict[str, Any]:
        """機械可読形式の制約生成"""
        
        hard_constraints = []
        soft_constraints = []
        preferences = []
        
        # MECEカテゴリー別制約分類（リスク・安全制約は高優先度）
        for category, facts in mece_facts.items():
            for i, fact in enumerate(facts):
                constraint_id = f"axis10_{category.lower().replace('制約', '')}_{i+1}"
                
                # リスク・安全制約の強度判定
                if any(keyword in fact for keyword in ['重大リスク', '重大', '危険', '不可', '不在']):
                    hard_constraints.append({
                        'id': constraint_id,
                        'type': 'risk_emergency',
                        'category': category,
                        'description': fact,
                        'priority': 'critical',
                        'confidence': 0.9,
                        'risk_level': self._assess_risk_level(fact),
                        'emergency_type': self._categorize_emergency_type(fact),
                        'response_urgency': self._assess_response_urgency(fact)
                    })
                elif any(keyword in fact for keyword in ['リスク', '要強化', '困難', '不足']):
                    soft_constraints.append({
                        'id': constraint_id,
                        'type': 'risk_emergency',
                        'category': category,
                        'description': fact,
                        'priority': 'high',
                        'confidence': 0.75,
                        'risk_level': self._assess_risk_level(fact),
                        'emergency_type': self._categorize_emergency_type(fact),
                        'response_urgency': self._assess_response_urgency(fact)
                    })
                else:
                    preferences.append({
                        'id': constraint_id,
                        'type': 'risk_emergency',
                        'category': category,
                        'description': fact,
                        'priority': 'medium',
                        'confidence': 0.6,
                        'risk_level': self._assess_risk_level(fact),
                        'emergency_type': self._categorize_emergency_type(fact),
                        'response_urgency': self._assess_response_urgency(fact)
                    })
        
        return {
            'hard_constraints': hard_constraints,
            'soft_constraints': soft_constraints,
            'preferences': preferences,
            'constraint_relationships': [
                {
                    'relationship_id': 'legal_safety_synergy',
                    'type': 'reinforces',
                    'from_category': 'リスク・緊急時対応',
                    'to_category': '法的・規制要件',
                    'description': 'リスク管理は法的要件の実践的履行'
                },
                {
                    'relationship_id': 'emergency_medical_dependency',
                    'type': 'requires',
                    'from_category': '医療緊急対応制約',
                    'to_category': '医療・ケア品質',
                    'description': '医療緊急対応は医療品質基盤が必要'
                },
                {
                    'relationship_id': 'continuity_staffing_dependency',
                    'type': 'requires',
                    'from_category': '事業継続制約',
                    'to_category': '職員ルール',
                    'description': '事業継続は適切な職員配置が前提'
                }
            ],
            'validation_rules': [
                {
                    'rule_id': 'axis10_emergency_response_readiness',
                    'description': '24時間緊急対応体制の確保を確認',
                    'validation_type': 'emergency_readiness',
                    'severity': 'critical'
                },
                {
                    'rule_id': 'axis10_medical_emergency_capability',
                    'description': '医療緊急事態対応能力の確保を確認',
                    'validation_type': 'medical_emergency_check',
                    'severity': 'critical'
                },
                {
                    'rule_id': 'axis10_business_continuity_planning',
                    'description': '事業継続計画の実行可能性を確認',
                    'validation_type': 'business_continuity_check',
                    'severity': 'high'
                },
                {
                    'rule_id': 'axis10_risk_monitoring_coverage',
                    'description': 'リスク監視体制の網羅性を確認',
                    'validation_type': 'risk_monitoring_check',
                    'severity': 'high'
                }
            ],
            'risk_categories': {
                '生命リスク': {
                    'severity': 'critical',
                    'response_time': 'immediate',
                    'examples': ['心肺蘇生', '医療緊急事態', '重篤事故']
                },
                '安全リスク': {
                    'severity': 'high',
                    'response_time': 'urgent',
                    'examples': ['転倒事故', '感染症', '薬剤事故']
                },
                '継続リスク': {
                    'severity': 'medium',
                    'response_time': 'planned',
                    'examples': ['人員不足', '設備故障', '外部依存']
                },
                'セキュリティリスク': {
                    'severity': 'medium',
                    'response_time': 'planned',
                    'examples': ['不審者', '情報漏洩', '施設侵入']
                }
            }
        }
    
    def _assess_risk_level(self, fact: str) -> str:
        """リスクレベルの評価"""
        if any(keyword in fact for keyword in ['重大リスク', '重大', '危険', '生命']):
            return 'critical'
        elif any(keyword in fact for keyword in ['リスク', '要強化', '困難']):
            return 'high'
        elif any(keyword in fact for keyword in ['要注意', '要検討', '改善']):
            return 'medium'
        elif any(keyword in fact for keyword in ['良好', '確保', '充実']):
            return 'low'
        else:
            return 'unknown'
    
    def _categorize_emergency_type(self, fact: str) -> str:
        """緊急事態タイプの分類"""
        if any(keyword in fact for keyword in ['医療', '心肺蘇生', '感染']):
            return 'medical_emergency'
        elif any(keyword in fact for keyword in ['災害', '避難', '火災']):
            return 'disaster_emergency'
        elif any(keyword in fact for keyword in ['事故', '転倒', '怪我']):
            return 'accident_emergency'
        elif any(keyword in fact for keyword in ['セキュリティ', '侵入', '不審']):
            return 'security_emergency'
        elif any(keyword in fact for keyword in ['継続', '停電', '設備']):
            return 'continuity_emergency'
        else:
            return 'general_emergency'
    
    def _assess_response_urgency(self, fact: str) -> str:
        """対応緊急度の評価"""
        if any(keyword in fact for keyword in ['重大', '生命', '危険', '不可']):
            return 'immediate'
        elif any(keyword in fact for keyword in ['リスク', '強化必要', '困難']):
            return 'urgent'
        elif any(keyword in fact for keyword in ['要注意', '改善', '検討']):
            return 'planned'
        else:
            return 'monitoring'
    
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
        
        # リスク・緊急対応指標
        risk_emergency_indicators = {
            'critical_risks': len([f for facts in mece_facts.values() for f in facts if '重大リスク' in f]),
            'high_risks': len([f for facts in mece_facts.values() for f in facts if 'リスク' in f and '重大' not in f]),
            'safety_achievements': len([f for facts in mece_facts.values() for f in facts if any(safe in f for safe in ['良好', '確保', '充実'])]),
            'emergency_readiness_ratio': len([f for facts in mece_facts.values() for f in facts if '緊急' in f and ('良好' in f or '確保' in f)]) / len([f for facts in mece_facts.values() for f in facts if '緊急' in f]) if len([f for facts in mece_facts.values() for f in facts if '緊急' in f]) > 0 else 0,
            'medical_emergency_coverage': len([f for facts in mece_facts.values() for f in facts if '医療緊急' in f]) / sum(len(facts) for facts in mece_facts.values()) if sum(len(facts) for facts in mece_facts.values()) > 0 else 0,
            'business_continuity_score': len([f for facts in mece_facts.values() for f in facts if '継続' in f and ('良好' in f or '可能' in f)]) / len([f for facts in mece_facts.values() for f in facts if '継続' in f]) if len([f for facts in mece_facts.values() for f in facts if '継続' in f]) > 0 else 0
        }
        
        # データ品質指標
        data_quality = {
            'completeness': 1.0 - (long_df.isnull().sum().sum() / (len(long_df) * len(long_df.columns))),
            'record_count': len(long_df),
            'unique_staff_count': long_df['staff'].nunique() if 'staff' in long_df.columns else 0,
            'unique_roles_count': long_df['role'].nunique() if 'role' in long_df.columns else 0,
            'risk_focus_ratio': len([f for facts in mece_facts.values() for f in facts if any(r in f for r in ['リスク', '緊急', '安全', '危機'])]) / sum(len(facts) for facts in mece_facts.values()) if sum(len(facts) for facts in mece_facts.values()) > 0 else 0
        }
        
        return {
            'extraction_timestamp': datetime.now().isoformat(),
            'axis_info': {
                'axis_number': self.axis_number,
                'axis_name': self.axis_name,
                'mece_categories': list(mece_facts.keys()),
                'focus_area': 'リスク管理・緊急時対応制約',
                'priority_level': 'critical'  # 安全確保は最高優先度
            },
            'data_period': date_range,
            'risk_emergency_indicators': risk_emergency_indicators,
            'data_quality': data_quality,
            'risk_assessment_standards': {
                '緊急対応時間': '5分以内',
                '24時間体制': '95%以上カバレッジ',
                '医療緊急対応': '30%以上医療資格者',
                '事業継続人員': '平均の50%以上'
            },
            'extraction_statistics': {
                'total_facts_extracted': sum(len(facts) for facts in mece_facts.values()),
                'critical_risk_facts': len([f for facts in mece_facts.values() for f in facts if '重大リスク' in f]),
                'emergency_preparedness_facts': len([f for facts in mece_facts.values() for f in facts if '緊急' in f]),
                'safety_assurance_facts': len([f for facts in mece_facts.values() for f in facts if '安全' in f or '確保' in f]),
                'business_continuity_facts': len([f for facts in mece_facts.values() for f in facts if '継続' in f]),
                'categories_with_facts': len([cat for cat, facts in mece_facts.items() if facts and not any('検出されませんでした' in f for f in facts)])
            }
        }