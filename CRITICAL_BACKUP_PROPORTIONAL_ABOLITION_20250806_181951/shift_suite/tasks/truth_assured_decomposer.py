#!/usr/bin/env python3
"""
Truth-Assured Data Decomposer
真実性保証データ分解システム - Need File優先の高精度分解
"""

from __future__ import annotations  # 型ヒント互換性のため保持

# import json  # JSON出力で将来使用される可能性
import logging
from datetime import datetime  # , timedelta  # timedelta は現在未使用
from pathlib import Path
from typing import Any, Dict, List, Optional
# from typing import Tuple  # 未使用のためコメントアウト

import numpy as np
import pandas as pd
from pandas import DataFrame

# from .constants import DEFAULT_SLOT_MINUTES  # 現在未使用だが設定系で使用される可能性
from .enhanced_data_ingestion import QualityAssuredDataset
from .utils import log

# Analysis logger
analysis_logger = logging.getLogger('analysis')


class NeedFileAnalysisResult:
    """Need File分析結果"""
    
    def __init__(self):
        self.care_demands_by_time: Dict[str, float] = {}
        self.care_demands_by_role: Dict[str, float] = {}
        self.care_demands_by_day: Dict[str, float] = {}
        self.total_care_hours: float = 0.0
        self.peak_hours: List[str] = []
        self.low_hours: List[str] = []
        self.confidence_score: float = 0.0
        self.data_completeness: float = 0.0
        self.detected_patterns: List[Dict[str, Any]] = []


class StaffConstraintLearning:
    """スタッフ制約学習システム"""
    
    def __init__(self):
        self.learned_constraints: Dict[str, Dict[str, Any]] = {}
        self.constraint_confidence: Dict[str, float] = {}
        self.learning_metadata: Dict[str, Any] = {}
    
    def learn_from_actual_patterns(self, schedule_data: DataFrame) -> Dict[str, Dict[str, Any]]:
        """実際のスケジュールパターンから制約を学習"""
        analysis_logger.info("[CONSTRAINT_LEARNING] 制約学習開始")
        
        try:
            constraints = {}
            
            if 'staff' not in schedule_data.columns:
                return constraints
            
            # 各スタッフの勤務パターン分析
            for staff_name in schedule_data['staff'].unique():
                if pd.isna(staff_name) or self._is_rest_marker(staff_name):
                    continue
                
                staff_data = schedule_data[schedule_data['staff'] == staff_name]
                staff_constraints = self._analyze_staff_patterns(staff_name, staff_data)
                
                if staff_constraints:
                    constraints[staff_name] = staff_constraints
                    analysis_logger.debug(f"[CONSTRAINT] {staff_name}: {len(staff_constraints)}個の制約を学習")
            
            self.learned_constraints = constraints
            analysis_logger.info(f"[CONSTRAINT_LEARNING] 完了: {len(constraints)}名の制約を学習")
            
            return constraints
            
        except Exception as e:
            log.error(f"制約学習エラー: {e}")
            return {}
    
    def _analyze_staff_patterns(self, staff_name: str, staff_data: DataFrame) -> Dict[str, Any]:
        """個別スタッフのパターン分析"""
        constraints = {}
        
        try:
            # 勤務可能時間帯分析
            if 'time_slot' in staff_data.columns:
                working_hours = staff_data['time_slot'].unique()
                constraints['preferred_hours'] = list(working_hours)
                
                # 夜勤対応可否判定
                night_hours = [h for h in working_hours if self._is_night_hour(h)]
                constraints['night_shift_capable'] = len(night_hours) > 0
            
            # 勤務頻度分析
            if 'date' in staff_data.columns or 'ds' in staff_data.columns:
                date_col = 'date' if 'date' in staff_data.columns else 'ds'
                working_dates = pd.to_datetime(staff_data[date_col]).dt.date.unique()
                
                # 週勤務日数推定
                date_range = max(working_dates) - min(working_dates)
                weeks = max(1, date_range.days / 7)
                avg_days_per_week = len(working_dates) / weeks
                constraints['avg_working_days_per_week'] = round(avg_days_per_week, 1)
            
            # 職種情報
            if 'role' in staff_data.columns:
                roles = staff_data['role'].unique()
                constraints['primary_role'] = roles[0] if len(roles) > 0 else None
                constraints['multi_role_capable'] = len(roles) > 1
            
            # 雇用形態情報
            if 'employment' in staff_data.columns:
                employment_types = staff_data['employment'].unique()
                constraints['employment_type'] = employment_types[0] if len(employment_types) > 0 else None
            
            # 連続勤務パターン分析
            consecutive_work_days = self._analyze_consecutive_patterns(staff_data)
            if consecutive_work_days:
                constraints['max_consecutive_days'] = consecutive_work_days
            
            return constraints
            
        except Exception as e:
            log.error(f"スタッフパターン分析エラー ({staff_name}): {e}")
            return {}
    
    def _is_rest_marker(self, value: Any) -> bool:
        """休暇マーカー判定"""
        if pd.isna(value):
            return True
        
        rest_patterns = ['×', 'X', 'x', '休', '休み', '休暇', '欠', '欠勤', 'OFF', 'off', 'Off', '-', '−', '―']
        return str(value).strip() in rest_patterns
    
    def _is_night_hour(self, hour_str: str) -> bool:
        """夜勤時間判定"""
        try:
            if ':' in str(hour_str):
                hour = int(str(hour_str).split(':')[0])
                return hour >= 22 or hour <= 6
            return False
        except:
            return False
    
    def _analyze_consecutive_patterns(self, staff_data: DataFrame) -> Optional[int]:
        """連続勤務パターン分析"""
        try:
            if 'date' not in staff_data.columns and 'ds' not in staff_data.columns:
                return None
            
            date_col = 'date' if 'date' in staff_data.columns else 'ds'
            working_dates = pd.to_datetime(staff_data[date_col]).dt.date
            working_dates_sorted = sorted(working_dates.unique())
            
            max_consecutive = 1
            current_consecutive = 1
            
            for i in range(1, len(working_dates_sorted)):
                if (working_dates_sorted[i] - working_dates_sorted[i-1]).days == 1:
                    current_consecutive += 1
                    max_consecutive = max(max_consecutive, current_consecutive)
                else:
                    current_consecutive = 1
            
            return max_consecutive if max_consecutive > 1 else None
            
        except Exception as e:
            log.error(f"連続勤務パターン分析エラー: {e}")
            return None


class ContextualPatternDetector:
    """文脈的パターン検出システム"""
    
    def __init__(self):
        self.detected_patterns: List[Dict[str, Any]] = []
        self.facility_characteristics: Dict[str, Any] = {}
    
    def detect_facility_patterns(self, dataset: QualityAssuredDataset) -> Dict[str, Any]:
        """施設特性パターンの検出"""
        analysis_logger.info("[PATTERN_DETECTION] 施設パターン検出開始")
        
        try:
            patterns = {}
            data = dataset.data
            
            # 施設規模推定
            patterns['facility_scale'] = self._estimate_facility_scale(data)
            
            # 勤務パターン分析
            patterns['shift_patterns'] = self._analyze_shift_patterns(data)
            
            # 職種構成分析
            patterns['role_composition'] = self._analyze_role_composition(data)
            
            # 時間帯別需要パターン
            patterns['time_demand_patterns'] = self._analyze_time_demand_patterns(data)
            
            # 曜日別パターン
            patterns['weekday_patterns'] = self._analyze_weekday_patterns(data)
            
            self.facility_characteristics = patterns
            analysis_logger.info("[PATTERN_DETECTION] 完了")
            
            return patterns
            
        except Exception as e:
            log.error(f"施設パターン検出エラー: {e}")
            return {}
    
    def _estimate_facility_scale(self, data: DataFrame) -> Dict[str, Any]:
        """施設規模推定"""
        try:
            # スタッフ数カウント
            if 'staff' in data.columns:
                unique_staff = data[data['staff'].notna()]['staff'].unique()
                valid_staff = [s for s in unique_staff if not self._is_rest_marker(s)]
                staff_count = len(valid_staff)
            else:
                staff_count = 0
            
            # 施設規模分類
            if staff_count <= 10:
                scale_category = "small"  # 小規模施設
            elif staff_count <= 30:
                scale_category = "medium"  # 中規模施設
            else:
                scale_category = "large"  # 大規模施設
            
            return {
                "staff_count": staff_count,
                "scale_category": scale_category,
                "confidence": 0.9 if staff_count > 0 else 0.3
            }
            
        except Exception as e:
            log.error(f"施設規模推定エラー: {e}")
            return {"staff_count": 0, "scale_category": "unknown", "confidence": 0.0}
    
    def _analyze_shift_patterns(self, data: DataFrame) -> Dict[str, Any]:
        """勤務パターン分析"""
        try:
            patterns = {"detected_shifts": [], "coverage_24h": False}
            
            # 時間列の検出
            time_columns = [col for col in data.columns if self._is_time_column(col)]
            
            if time_columns:
                # 24時間カバー判定
                hours = set()
                for col in time_columns:
                    hour = self._extract_hour_from_column(col)
                    if hour is not None:
                        hours.add(hour)
                
                patterns["coverage_24h"] = len(hours) >= 16  # 16時間以上なら24h施設とみなす
                patterns["covered_hours"] = len(hours)
                
                # シフトパターン推定
                if any(h >= 22 or h <= 6 for h in hours):
                    patterns["detected_shifts"].append("night_shift")
                if any(6 <= h <= 10 for h in hours):
                    patterns["detected_shifts"].append("morning_shift")
                if any(10 <= h <= 18 for h in hours):
                    patterns["detected_shifts"].append("day_shift")
                if any(18 <= h <= 22 for h in hours):
                    patterns["detected_shifts"].append("evening_shift")
            
            return patterns
            
        except Exception as e:
            log.error(f"勤務パターン分析エラー: {e}")
            return {"detected_shifts": [], "coverage_24h": False}
    
    def _analyze_role_composition(self, data: DataFrame) -> Dict[str, Any]:
        """職種構成分析"""
        try:
            if 'role' not in data.columns:
                return {"roles": [], "primary_role": None}
            
            role_counts = data[data['role'].notna()]['role'].value_counts()
            total_role_records = role_counts.sum()
            
            role_composition = {}
            for role, count in role_counts.items():
                role_composition[role] = {
                    "count": count,
                    "percentage": (count / total_role_records * 100) if total_role_records > 0 else 0
                }
            
            primary_role = role_counts.index[0] if not role_counts.empty else None
            
            return {
                "roles": list(role_counts.index),
                "primary_role": primary_role,
                "composition": role_composition,
                "diversity_score": len(role_counts) / max(1, total_role_records) * 100
            }
            
        except Exception as e:
            log.error(f"職種構成分析エラー: {e}")
            return {"roles": [], "primary_role": None}
    
    def _analyze_time_demand_patterns(self, data: DataFrame) -> Dict[str, Any]:
        """時間帯別需要パターン分析"""
        try:
            time_patterns = {"peak_hours": [], "low_hours": [], "demand_curve": {}}
            
            # 時間列からスタッフ配置数を集計
            time_columns = [col for col in data.columns if self._is_time_column(col)]
            
            for col in time_columns:
                hour = self._extract_hour_from_column(col)
                if hour is not None:
                    # その時間帯の実際のスタッフ配置数
                    staff_count = data[col].notna().sum()
                    time_patterns["demand_curve"][f"{hour:02d}:00"] = staff_count
            
            if time_patterns["demand_curve"]:
                # ピーク時間と閑散時間の特定
                sorted_hours = sorted(time_patterns["demand_curve"].items(), key=lambda x: x[1])
                
                # 上位25%をピーク、下位25%を閑散とする
                total_hours = len(sorted_hours)
                peak_threshold = int(total_hours * 0.75)
                low_threshold = int(total_hours * 0.25)
                
                time_patterns["peak_hours"] = [h[0] for h in sorted_hours[peak_threshold:]]
                time_patterns["low_hours"] = [h[0] for h in sorted_hours[:low_threshold]]
            
            return time_patterns
            
        except Exception as e:
            log.error(f"時間帯別需要パターン分析エラー: {e}")
            return {"peak_hours": [], "low_hours": [], "demand_curve": {}}
    
    def _analyze_weekday_patterns(self, data: DataFrame) -> Dict[str, Any]:
        """曜日別パターン分析"""
        try:
            weekday_patterns = {"weekday_demand": {}, "weekend_different": False}
            
            # 日付列の検出
            date_columns = [col for col in data.columns if self._is_date_column(col)]
            
            for col in date_columns:
                date_obj = self._parse_date_column(col)
                if date_obj:
                    weekday = date_obj.strftime("%A")
                    staff_on_day = data[col].notna().sum()
                    
                    if weekday not in weekday_patterns["weekday_demand"]:
                        weekday_patterns["weekday_demand"][weekday] = []
                    weekday_patterns["weekday_demand"][weekday].append(staff_on_day)
            
            # 平日と週末の差異分析
            if weekday_patterns["weekday_demand"]:
                weekday_avg = np.mean([np.mean(v) for k, v in weekday_patterns["weekday_demand"].items() 
                                     if k not in ["Saturday", "Sunday"]])
                weekend_avg = np.mean([np.mean(v) for k, v in weekday_patterns["weekday_demand"].items() 
                                      if k in ["Saturday", "Sunday"]])
                
                if abs(weekday_avg - weekend_avg) > weekday_avg * 0.1:  # 10%以上の差
                    weekday_patterns["weekend_different"] = True
            
            return weekday_patterns
            
        except Exception as e:
            log.error(f"曜日別パターン分析エラー: {e}")
            return {"weekday_demand": {}, "weekend_different": False}
    
    def _is_rest_marker(self, value: Any) -> bool:
        """休暇マーカー判定"""
        if pd.isna(value):
            return True
        rest_patterns = ['×', 'X', 'x', '休', '休み', '休暇', '欠', '欠勤', 'OFF', 'off', 'Off', '-', '−', '―']
        return str(value).strip() in rest_patterns
    
    def _is_time_column(self, col: Any) -> bool:
        """時間列判定"""
        col_str = str(col)
        return bool(':' in col_str and any(c.isdigit() for c in col_str))
    
    def _is_date_column(self, col: Any) -> bool:
        """日付列判定"""
        col_str = str(col)
        return bool(re.search(r'\d{1,2}[/-]\d{1,2}', col_str))
    
    def _extract_hour_from_column(self, col: Any) -> Optional[int]:
        """列名から時間を抽出"""
        try:
            import re
            col_str = str(col)
            match = re.search(r'(\d{1,2}):', col_str)
            if match:
                return int(match.group(1))
            return None
        except:
            return None
    
    def _parse_date_column(self, col: Any) -> Optional[datetime]:
        """日付列パース"""
        try:
            import re
            col_str = str(col)
            match = re.search(r'(\d{1,2})[/-](\d{1,2})', col_str)
            if match:
                month, day = map(int, match.groups())
                year = datetime.now().year
                return datetime(year, month, day)
            return None
        except:
            return None


class AnomalyDetector:
    """異常パターン検出システム"""
    
    def __init__(self):
        self.detected_anomalies: List[Dict[str, Any]] = []
    
    def detect_anomalies(self, dataset: QualityAssuredDataset) -> List[Dict[str, Any]]:
        """異常パターンの検出"""
        analysis_logger.info("[ANOMALY_DETECTION] 異常パターン検出開始")
        
        anomalies = []
        data = dataset.data
        
        try:
            # 1. 極端な偏りの検出
            anomalies.extend(self._detect_extreme_imbalance(data))
            
            # 2. 時間軸の不連続性検出
            anomalies.extend(self._detect_time_discontinuity(data))
            
            # 3. スタッフ配置異常検出
            anomalies.extend(self._detect_staffing_anomalies(data))
            
            # 4. データ品質異常検出
            anomalies.extend(self._detect_data_quality_issues(data))
            
            self.detected_anomalies = anomalies
            analysis_logger.info(f"[ANOMALY_DETECTION] 完了: {len(anomalies)}件の異常を検出")
            
            return anomalies
            
        except Exception as e:
            log.error(f"異常検出エラー: {e}")
            return []
    
    def _detect_extreme_imbalance(self, data: DataFrame) -> List[Dict[str, Any]]:
        """極端な偏り検出"""
        anomalies = []
        
        try:
            # 職種別偏り検出
            if 'role' in data.columns:
                role_counts = data[data['role'].notna()]['role'].value_counts()
                if not role_counts.empty:
                    max_count = role_counts.max()
                    min_count = role_counts.min()
                    
                    if max_count > min_count * 10:  # 10倍以上の差
                        anomalies.append({
                            "type": "extreme_role_imbalance",
                            "severity": "warning",
                            "description": f"職種間の極端な偏り: 最大{max_count}人 vs 最小{min_count}人",
                            "affected_roles": list(role_counts.index)
                        })
            
            return anomalies
            
        except Exception as e:
            log.error(f"極端偏り検出エラー: {e}")
            return []
    
    def _detect_time_discontinuity(self, data: DataFrame) -> List[Dict[str, Any]]:
        """時間軸不連続性検出"""
        anomalies = []
        
        try:
            # 時間列の連続性チェック
            time_columns = [col for col in data.columns if self._is_time_column(col)]
            
            if len(time_columns) > 1:
                hours = []
                for col in time_columns:
                    hour = self._extract_hour_from_column(col)
                    if hour is not None:
                        hours.append(hour)
                
                hours.sort()
                gaps = []
                for i in range(1, len(hours)):
                    gap = hours[i] - hours[i-1]
                    if gap > 2:  # 2時間以上の空白
                        gaps.append((hours[i-1], hours[i]))
                
                if gaps:
                    anomalies.append({
                        "type": "time_discontinuity",
                        "severity": "warning", 
                        "description": f"時間軸に{len(gaps)}箇所の不連続を検出",
                        "gaps": gaps
                    })
            
            return anomalies
            
        except Exception as e:
            log.error(f"時間軸不連続検出エラー: {e}")
            return []
    
    def _detect_staffing_anomalies(self, data: DataFrame) -> List[Dict[str, Any]]:
        """スタッフ配置異常検出"""
        anomalies = []
        
        try:
            if 'staff' in data.columns:
                # 単一スタッフによる極端な集中
                staff_workload = data[data['staff'].notna()]['staff'].value_counts()
                
                if not staff_workload.empty:
                    avg_workload = staff_workload.mean()
                    max_workload = staff_workload.max()
                    
                    if max_workload > avg_workload * 3:  # 平均の3倍以上
                        overworked_staff = staff_workload[staff_workload > avg_workload * 2].index.tolist()
                        anomalies.append({
                            "type": "extreme_workload_concentration",
                            "severity": "warning",
                            "description": f"{len(overworked_staff)}名のスタッフに業務が集中",
                            "affected_staff": overworked_staff[:5]  # 最大5名表示
                        })
            
            return anomalies
            
        except Exception as e:
            log.error(f"スタッフ配置異常検出エラー: {e}")
            return []
    
    def _detect_data_quality_issues(self, data: DataFrame) -> List[Dict[str, Any]]:
        """データ品質問題検出"""
        anomalies = []
        
        try:
            # 極端な欠損率
            total_cells = data.size
            missing_cells = data.isna().sum().sum()
            missing_rate = missing_cells / total_cells if total_cells > 0 else 0
            
            if missing_rate > 0.5:  # 50%以上欠損
                anomalies.append({
                    "type": "high_missing_rate",
                    "severity": "error",
                    "description": f"データ欠損率が{missing_rate:.1%}と高い",
                    "missing_rate": missing_rate
                })
            
            return anomalies
            
        except Exception as e:
            log.error(f"データ品質問題検出エラー: {e}")
            return []
    
    def _is_time_column(self, col: Any) -> bool:
        """時間列判定"""
        col_str = str(col)
        return bool(':' in col_str and any(c.isdigit() for c in col_str))
    
    def _extract_hour_from_column(self, col: Any) -> Optional[int]:
        """列名から時間抽出"""
        try:
            import re
            col_str = str(col)
            match = re.search(r'(\d{1,2}):', col_str)
            if match:
                return int(match.group(1))
            return None
        except:
            return None


class DecompositionResult:
    """分解結果クラス"""
    
    def __init__(self):
        self.need_analysis: Optional[NeedFileAnalysisResult] = None
        self.learned_constraints: Dict[str, Dict[str, Any]] = {}
        self.facility_patterns: Dict[str, Any] = {}
        self.detected_anomalies: List[Dict[str, Any]] = []
        self.decomposition_metadata: Dict[str, Any] = {}
        self.confidence_score: float = 0.0
        self.processing_timestamp: datetime = datetime.now()
    
    def get_summary_report(self) -> str:
        """分解結果サマリーレポート"""
        report = f"""
🔧 データ分解結果サマリー
{'='*60}
⏰ 処理時刻: {self.processing_timestamp.strftime('%Y-%m-%d %H:%M:%S')}
🎯 信頼度: {self.confidence_score:.1f}%

📊 Need分析結果:
├─ 総ケア時間: {self.need_analysis.total_care_hours:.1f}時間 (推定)
├─ ピーク時間帯: {', '.join(self.need_analysis.peak_hours) if self.need_analysis else 'N/A'}
└─ データ完全性: {self.need_analysis.data_completeness:.1f}% (推定)

🧠 学習した制約: {len(self.learned_constraints)}名分
📈 施設パターン: {len(self.facility_patterns)}種類検出
⚠️  検出した異常: {len(self.detected_anomalies)}件

🏥 施設特性:
├─ 規模: {self.facility_patterns.get('facility_scale', {}).get('scale_category', 'unknown')}
├─ 24時間運営: {'Yes' if self.facility_patterns.get('shift_patterns', {}).get('coverage_24h', False) else 'No'}
└─ 主要職種: {self.facility_patterns.get('role_composition', {}).get('primary_role', 'unknown')}
"""
        return report


class TruthAssuredDecomposer:
    """真実性保証データ分解システム"""
    
    def __init__(self):
        self.constraint_learner = StaffConstraintLearning() 
        self.pattern_detector = ContextualPatternDetector()
        self.anomaly_detector = AnomalyDetector()
    
    def decompose_with_truth_priority(self, dataset: QualityAssuredDataset) -> DecompositionResult:
        """Truth優先データ分解"""
        analysis_logger.info("[DECOMPOSITION] 真実性保証データ分解開始")
        
        result = DecompositionResult()
        
        try:
            # Step 1: Need File優先分析
            result.need_analysis = self._perform_need_analysis(dataset)
            
            # Step 2: 制約学習
            result.learned_constraints = self.constraint_learner.learn_from_actual_patterns(dataset.data)
            
            # Step 3: 施設パターン検出
            result.facility_patterns = self.pattern_detector.detect_facility_patterns(dataset)
            
            # Step 4: 異常検出
            result.detected_anomalies = self.anomaly_detector.detect_anomalies(dataset)
            
            # Step 5: メタデータ生成
            result.decomposition_metadata = self._generate_metadata(dataset, result)
            
            # Step 6: 信頼度計算
            result.confidence_score = self._calculate_confidence(dataset, result) 
            
            analysis_logger.info(f"[DECOMPOSITION] 完了: 信頼度{result.confidence_score:.1f}%")
            analysis_logger.info(result.get_summary_report())
            
            return result
            
        except Exception as e:
            log.error(f"データ分解エラー: {e}")
            result.decomposition_metadata["error"] = str(e)
            return result
    
    def _perform_need_analysis(self, dataset: QualityAssuredDataset) -> NeedFileAnalysisResult:
        """Need File分析実行"""
        analysis_logger.info("[NEED_ANALYSIS] Need File分析開始")
        
        need_result = NeedFileAnalysisResult()
        
        try:
            data = dataset.data
            
            # Need Fileシートの検出
            if dataset.schema.get("has_need_file", False):
                # Need File専用分析
                need_result = self._analyze_need_file_data(dataset)
            else:
                # 通常データからNeed推定
                need_result = self._estimate_needs_from_schedule(data)
            
            analysis_logger.info(f"[NEED_ANALYSIS] 完了: 信頼度{need_result.confidence_score:.1f}%")
            
            return need_result
            
        except Exception as e:
            log.error(f"Need分析エラー: {e}")
            return need_result
    
    def _analyze_need_file_data(self, dataset: QualityAssuredDataset) -> NeedFileAnalysisResult:
        """専用Need Fileデータ分析"""
        result = NeedFileAnalysisResult()
        
        try:
            # Need Fileを直接読み込み
            excel_path = Path(dataset.lineage.source_file)
            
            # Needシートを特定
            excel_file = pd.ExcelFile(excel_path)
            need_sheet = None
            for sheet in excel_file.sheet_names:
                if "Need" in sheet or "need" in sheet:
                    need_sheet = sheet
                    break
            
            if need_sheet:
                need_data = pd.read_excel(excel_path, sheet_name=need_sheet)
                
                # 時間別需要分析
                time_columns = [col for col in need_data.columns if self._is_time_column(col)]
                for col in time_columns:
                    total_need = need_data[col].sum() if col in need_data.columns else 0
                    result.care_demands_by_time[str(col)] = total_need
                
                # 職種別需要分析
                if 'role' in need_data.columns:
                    role_needs = need_data.groupby('role').sum().sum(axis=1)
                    result.care_demands_by_role = role_needs.to_dict()
                
                # 総ケア時間計算
                result.total_care_hours = sum(result.care_demands_by_time.values())
                
                # ピーク・閑散時間帯特定
                if result.care_demands_by_time:
                    sorted_times = sorted(result.care_demands_by_time.items(), key=lambda x: x[1])
                    total_times = len(sorted_times)
                    
                    peak_threshold = int(total_times * 0.8)
                    low_threshold = int(total_times * 0.2)
                    
                    result.peak_hours = [t[0] for t in sorted_times[peak_threshold:]]
                    result.low_hours = [t[0] for t in sorted_times[:low_threshold]]
                
                result.confidence_score = 95.0  # Need File直接分析は高信頼度
                result.data_completeness = (need_data.notna().sum().sum() / need_data.size) * 100
                
            return result
            
        except Exception as e:
            log.error(f"Need File分析エラー: {e}")
            result.confidence_score = 0.0
            return result
    
    def _estimate_needs_from_schedule(self, data: DataFrame) -> NeedFileAnalysisResult:
        """スケジュールデータからNeed推定"""
        result = NeedFileAnalysisResult()
        
        try:
            # 時間別スタッフ配置から需要推定
            time_columns = [col for col in data.columns if self._is_time_column(col)]
            
            for col in time_columns:
                staff_count = data[col].notna().sum()
                # 実際の配置人数から需要を推定（1.2倍を適正需要とする）
                estimated_need = staff_count * 1.2
                result.care_demands_by_time[str(col)] = estimated_need
            
            # 職種別推定
            if 'role' in data.columns:
                role_distribution = data[data['role'].notna()]['role'].value_counts()
                total_estimated_need = sum(result.care_demands_by_time.values())
                
                for role, count in role_distribution.items():
                    proportion = count / role_distribution.sum()
                    result.care_demands_by_role[role] = total_estimated_need * proportion
            
            result.total_care_hours = sum(result.care_demands_by_time.values())
            result.confidence_score = 60.0  # 推定値なので中程度の信頼度
            result.data_completeness = (data.notna().sum().sum() / data.size) * 100
            
            return result
            
        except Exception as e:
            log.error(f"Need推定エラー: {e}")
            result.confidence_score = 0.0
            return result
    
    def _generate_metadata(self, dataset: QualityAssuredDataset, result: DecompositionResult) -> Dict[str, Any]:
        """メタデータ生成"""
        return {
            "decomposition_timestamp": datetime.now().isoformat(),
            "source_quality_score": dataset.quality_result.overall_score,
            "source_recommended_method": dataset.quality_result.recommended_analysis_method,
            "constraints_learned": len(result.learned_constraints),
            "patterns_detected": len(result.facility_patterns),
            "anomalies_found": len(result.detected_anomalies),
            "processing_mode": "need_priority" if dataset.schema.get("has_need_file") else "schedule_estimation"
        }
    
    def _calculate_confidence(self, dataset: QualityAssuredDataset, result: DecompositionResult) -> float:
        """総合信頼度計算"""
        try:
            base_score = dataset.quality_result.overall_score
            
            # Need分析の信頼度
            need_confidence = result.need_analysis.confidence_score if result.need_analysis else 0.0
            
            # 制約学習の充実度
            constraint_completeness = min(100.0, len(result.learned_constraints) * 10)
            
            # 異常検出による減点
            anomaly_penalty = min(20.0, len(result.detected_anomalies) * 5)
            
            # 重み付き平均
            confidence = (
                base_score * 0.4 +
                need_confidence * 0.4 +
                constraint_completeness * 0.2 -
                anomaly_penalty
            )
            
            return max(0.0, min(100.0, confidence))
            
        except Exception as e:
            log.error(f"信頼度計算エラー: {e}")
            return 0.0
    
    def _is_time_column(self, col: Any) -> bool:
        """時間列判定"""
        col_str = str(col)
        return bool(':' in col_str and any(c.isdigit() for c in col_str))


# 便利関数
def decompose_with_truth_assurance(dataset: QualityAssuredDataset) -> DecompositionResult:
    """真実性保証データ分解（便利関数）"""
    decomposer = TruthAssuredDecomposer()
    return decomposer.decompose_with_truth_priority(dataset)


# Export
__all__ = [
    "DecompositionResult",
    "TruthAssuredDecomposer", 
    "decompose_with_truth_assurance"
]