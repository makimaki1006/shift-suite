#!/usr/bin/env python3
"""
高度制約発見エンジン - 意図発見→制約昇華の2段階システム
目的：シフト作成者の暗黙意図を発見し、強制力のある制約として昇華
"""

import sys
import json
import logging
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import Enum

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class ConstraintType(Enum):
    """制約タイプの分類"""
    STATIC_HARD = "static_hard"      # 静的強制制約（違反=エラー）
    STATIC_SOFT = "static_soft"      # 静的推奨制約（違反=警告）
    DYNAMIC_HARD = "dynamic_hard"    # 動的強制制約（状況依存）
    DYNAMIC_SOFT = "dynamic_soft"    # 動的推奨制約（状況依存）

class ConstraintAxis(Enum):
    """制約軸の分類"""
    STAFF_AXIS = "staff"         # スタッフ軸
    TIME_AXIS = "time"           # 時間軸  
    TASK_AXIS = "task"           # 業務軸
    RELATIONSHIP_AXIS = "relationship"  # 関係性軸

@dataclass
class ConstraintRule:
    """制約ルール定義"""
    rule_id: str
    constraint_type: ConstraintType
    axis: ConstraintAxis
    condition: str          # IF部分
    action: str            # THEN部分
    confidence: float      # 確信度 0-1
    evidence: Dict[str, Any]  # 根拠データ
    measurement: float     # 定規値 0-100
    violation_penalty: str # 違反時の処理

class AdvancedIntentionDiscovery:
    """高度意図発見エンジン"""
    
    def __init__(self):
        self.engine_name = "高度意図発見エンジン"
        self.version = "2.0.0"
        
    def discover_deep_patterns(self, shift_data: List[List[Any]]) -> Dict[str, Any]:
        """深層パターン発見"""
        print(f"\n=== 深層パターン分析開始 ===")
        
        patterns = {
            "staff_specialization": {},    # スタッフ専門性
            "temporal_patterns": {},       # 時間的パターン
            "workload_distribution": {},   # 負荷分散パターン
            "relationship_patterns": {},   # 関係性パターン
            "anomaly_patterns": {},        # 異常パターン
            "sequence_patterns": {},       # 連続性パターン
            "frequency_patterns": {}       # 頻度パターン
        }
        
        # スタッフデータの抽出
        staff_shifts = self._extract_staff_data(shift_data)
        
        # 1. スタッフ専門性分析（向上版）
        patterns["staff_specialization"] = self._analyze_staff_specialization(staff_shifts)
        
        # 2. 時間的パターン分析
        patterns["temporal_patterns"] = self._analyze_temporal_patterns(staff_shifts)
        
        # 3. 負荷分散パターン分析
        patterns["workload_distribution"] = self._analyze_workload_distribution(staff_shifts)
        
        # 4. 関係性パターン分析
        patterns["relationship_patterns"] = self._analyze_relationship_patterns(staff_shifts)
        
        # 5. 異常パターン検知
        patterns["anomaly_patterns"] = self._detect_anomaly_patterns(staff_shifts)
        
        # 6. 連続性パターン分析
        patterns["sequence_patterns"] = self._analyze_sequence_patterns(staff_shifts)
        
        # 7. 頻度パターン分析
        patterns["frequency_patterns"] = self._analyze_frequency_patterns(staff_shifts)
        
        print(f"深層パターン分析完了: {len([p for p in patterns.values() if p])}カテゴリ")
        return patterns
    
    def _extract_staff_data(self, shift_data: List[List[Any]]) -> Dict[str, List[Dict]]:
        """スタッフデータ抽出の向上版"""
        staff_shifts = defaultdict(list)
        
        if len(shift_data) < 2:
            return {}
        
        # ヘッダー行とスタッフ列の特定（向上版）
        header_row_idx = self._find_header_row_advanced(shift_data)
        if header_row_idx is None:
            return {}
        
        headers = shift_data[header_row_idx]
        staff_col_idx = self._find_staff_column_advanced(headers)
        
        # データ抽出
        for row_idx in range(header_row_idx + 1, len(shift_data)):
            row = shift_data[row_idx]
            if not row or len(row) <= staff_col_idx or not row[staff_col_idx]:
                continue
            
            staff_name = str(row[staff_col_idx]).strip()
            
            # 各日のシフト情報を詳細記録
            for col_idx in range(staff_col_idx + 1, len(row)):
                if col_idx < len(headers) and row[col_idx]:
                    date_info = str(headers[col_idx]) if col_idx < len(headers) else f"Day{col_idx}"
                    shift_code = str(row[col_idx]).strip()
                    
                    if shift_code and shift_code not in ['', 'None', 'nan']:
                        staff_shifts[staff_name].append({
                            "date": date_info,
                            "shift": shift_code,
                            "col_index": col_idx,
                            "row_index": row_idx,
                            "sequence_position": len(staff_shifts[staff_name])
                        })
        
        return dict(staff_shifts)
    
    def _analyze_staff_specialization(self, staff_shifts: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """スタッフ専門性分析（高度版）"""
        specializations = {}
        
        for staff_name, shifts in staff_shifts.items():
            if not shifts:
                continue
            
            shift_counts = Counter(s["shift"] for s in shifts)
            total_shifts = len(shifts)
            
            # 専門性指標の計算
            specialization_scores = {}
            for shift_type, count in shift_counts.items():
                ratio = count / total_shifts
                
                # 専門性スコア = 比率 × 継続性 × 集中度
                continuity = self._calculate_continuity(shifts, shift_type)
                concentration = self._calculate_concentration(shifts, shift_type)
                
                specialization_score = ratio * continuity * concentration
                
                if specialization_score > 0.3:  # 30%以上で専門性認定
                    specialization_scores[shift_type] = {
                        "ratio": ratio,
                        "continuity": continuity,
                        "concentration": concentration,
                        "specialization_score": specialization_score,
                        "evidence_count": count,
                        "classification": self._classify_specialization(specialization_score)
                    }
            
            if specialization_scores:
                specializations[staff_name] = {
                    "primary_specializations": specialization_scores,
                    "versatility_index": len(shift_counts) / len(set(s["shift"] for s in shifts)),
                    "consistency_score": self._calculate_consistency(shifts)
                }
        
        return specializations
    
    def _analyze_temporal_patterns(self, staff_shifts: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """時間的パターン分析"""
        temporal_patterns = {
            "daily_patterns": {},
            "weekly_patterns": {},
            "sequence_patterns": {},
            "rhythm_patterns": {}
        }
        
        for staff_name, shifts in staff_shifts.items():
            if len(shifts) < 3:
                continue
            
            # 日次パターン分析
            daily_pattern = self._analyze_daily_pattern(shifts)
            if daily_pattern:
                temporal_patterns["daily_patterns"][staff_name] = daily_pattern
            
            # 週次パターン分析
            weekly_pattern = self._analyze_weekly_pattern(shifts)
            if weekly_pattern:
                temporal_patterns["weekly_patterns"][staff_name] = weekly_pattern
            
            # リズムパターン分析
            rhythm_pattern = self._analyze_rhythm_pattern(shifts)
            if rhythm_pattern:
                temporal_patterns["rhythm_patterns"][staff_name] = rhythm_pattern
        
        return temporal_patterns
    
    def _analyze_workload_distribution(self, staff_shifts: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """負荷分散パターン分析"""
        workload_patterns = {}
        
        # 全体の負荷分析
        total_shifts = sum(len(shifts) for shifts in staff_shifts.values())
        staff_count = len(staff_shifts)
        average_load = total_shifts / staff_count if staff_count > 0 else 0
        
        for staff_name, shifts in staff_shifts.items():
            load_ratio = len(shifts) / average_load if average_load > 0 else 0
            
            workload_patterns[staff_name] = {
                "absolute_load": len(shifts),
                "relative_load": load_ratio,
                "load_classification": self._classify_workload(load_ratio),
                "load_consistency": self._calculate_load_consistency(shifts),
                "peak_periods": self._identify_peak_periods(shifts)
            }
        
        return workload_patterns
    
    def _detect_anomaly_patterns(self, staff_shifts: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """異常パターン検知"""
        anomalies = {
            "staff_anomalies": {},
            "shift_anomalies": {},
            "pattern_anomalies": {}
        }
        
        # スタッフレベルの異常検知
        for staff_name, shifts in staff_shifts.items():
            staff_anomalies = []
            
            # 急激な変化の検知
            if self._detect_sudden_change(shifts):
                staff_anomalies.append("sudden_pattern_change")
            
            # 異常な集中の検知
            if self._detect_unusual_concentration(shifts):
                staff_anomalies.append("unusual_concentration")
            
            # 不規則性の検知
            if self._detect_irregularity(shifts):
                staff_anomalies.append("high_irregularity")
            
            if staff_anomalies:
                anomalies["staff_anomalies"][staff_name] = staff_anomalies
        
        return anomalies
    
    # ヘルパーメソッド群
    def _find_header_row_advanced(self, data: List[List[Any]]) -> Optional[int]:
        """ヘッダー行の高度検出"""
        keywords = ['氏名', '名前', 'スタッフ', '職員', 'name', 'staff', '月', '火', '水', '木', '金', '土', '日']
        
        for i, row in enumerate(data[:10]):
            if not row:
                continue
            
            # キーワード検出
            row_text = ' '.join(str(cell).lower() for cell in row if cell)
            keyword_score = sum(1 for keyword in keywords if keyword in row_text)
            
            # 列数の妥当性チェック
            non_empty_cells = sum(1 for cell in row if cell)
            
            if keyword_score >= 2 and non_empty_cells >= 3:
                return i
        
        return 0 if data else None
    
    def _find_staff_column_advanced(self, headers: List[Any]) -> int:
        """スタッフ列の高度検出"""
        staff_keywords = ['氏名', '名前', 'スタッフ', '職員', 'name', 'staff', '社員', '従業員']
        
        for i, header in enumerate(headers):
            if not header:
                continue
            
            header_str = str(header).lower()
            for keyword in staff_keywords:
                if keyword in header_str:
                    return i
        
        # フォールバック: 最初の列
        return 0
    
    def _calculate_continuity(self, shifts: List[Dict], shift_type: str) -> float:
        """継続性計算"""
        if not shifts:
            return 0.0
        
        target_shifts = [s for s in shifts if s["shift"] == shift_type]
        if len(target_shifts) < 2:
            return 0.5
        
        # 連続性の計算
        consecutive_count = 0
        max_consecutive = 0
        
        sorted_shifts = sorted(shifts, key=lambda x: x["sequence_position"])
        current_consecutive = 0
        
        for shift in sorted_shifts:
            if shift["shift"] == shift_type:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return min(1.0, max_consecutive / len(target_shifts))
    
    def _calculate_concentration(self, shifts: List[Dict], shift_type: str) -> float:
        """集中度計算"""
        if not shifts:
            return 0.0
        
        target_shifts = [s for s in shifts if s["shift"] == shift_type]
        if not target_shifts:
            return 0.0
        
        # 時間的集中度の計算
        positions = [s["sequence_position"] for s in target_shifts]
        if len(positions) < 2:
            return 1.0
        
        # 分散の逆数として集中度を計算
        variance = statistics.variance(positions)
        max_possible_variance = (len(shifts) ** 2) / 12  # 一様分布の分散
        
        concentration = 1.0 - (variance / max_possible_variance) if max_possible_variance > 0 else 1.0
        return max(0.0, min(1.0, concentration))
    
    def _classify_specialization(self, score: float) -> str:
        """専門性分類"""
        if score >= 0.8:
            return "high_specialist"
        elif score >= 0.6:
            return "moderate_specialist"
        elif score >= 0.4:
            return "partial_specialist"
        else:
            return "generalist"
    
    def _calculate_consistency(self, shifts: List[Dict]) -> float:
        """一貫性計算"""
        if len(shifts) < 2:
            return 1.0
        
        shift_types = [s["shift"] for s in shifts]
        unique_types = len(set(shift_types))
        total_shifts = len(shift_types)
        
        # 一貫性 = 1 - (種類数 / 総シフト数)
        consistency = 1.0 - (unique_types / total_shifts)
        return max(0.0, consistency)
    
    def _analyze_daily_pattern(self, shifts: List[Dict]) -> Optional[Dict[str, Any]]:
        """日次パターン分析"""
        if len(shifts) < 7:  # 最低1週間のデータが必要
            return None
        
        # 曜日パターンの抽出
        daily_distribution = defaultdict(list)
        for shift in shifts:
            # 日付から曜日を推定（簡易版）
            col_index = shift["col_index"]
            day_of_week = col_index % 7
            daily_distribution[day_of_week].append(shift["shift"])
        
        # パターンの評価
        pattern_strength = 0.0
        dominant_patterns = {}
        
        for day, day_shifts in daily_distribution.items():
            if day_shifts:
                most_common = Counter(day_shifts).most_common(1)[0]
                ratio = most_common[1] / len(day_shifts)
                if ratio > 0.6:  # 60%以上で支配的パターン
                    dominant_patterns[day] = {
                        "shift": most_common[0],
                        "ratio": ratio
                    }
                    pattern_strength += ratio
        
        if dominant_patterns:
            return {
                "dominant_patterns": dominant_patterns,
                "pattern_strength": pattern_strength / 7,
                "regularity_index": len(dominant_patterns) / 7
            }
        
        return None
    
    def _analyze_weekly_pattern(self, shifts: List[Dict]) -> Optional[Dict[str, Any]]:
        """週次パターン分析"""
        if len(shifts) < 14:  # 最低2週間のデータが必要
            return None
        
        # 週単位でのパターン分析
        weekly_patterns = []
        week_size = 7
        
        for i in range(0, len(shifts) - week_size + 1, week_size):
            week_shifts = shifts[i:i + week_size]
            week_pattern = [s["shift"] for s in week_shifts]
            weekly_patterns.append(week_pattern)
        
        # パターンの類似性分析
        if len(weekly_patterns) >= 2:
            similarity_scores = []
            for i in range(len(weekly_patterns) - 1):
                similarity = self._calculate_pattern_similarity(
                    weekly_patterns[i], weekly_patterns[i + 1]
                )
                similarity_scores.append(similarity)
            
            avg_similarity = statistics.mean(similarity_scores)
            
            return {
                "weekly_consistency": avg_similarity,
                "pattern_variations": len(set(tuple(p) for p in weekly_patterns)),
                "dominant_weekly_pattern": self._find_dominant_weekly_pattern(weekly_patterns)
            }
        
        return None
    
    def _analyze_rhythm_pattern(self, shifts: List[Dict]) -> Optional[Dict[str, Any]]:
        """リズムパターン分析"""
        if len(shifts) < 5:
            return None
        
        # シフト変化のリズム分析
        change_intervals = []
        last_shift = shifts[0]["shift"]
        
        for i, shift in enumerate(shifts[1:], 1):
            if shift["shift"] != last_shift:
                change_intervals.append(i)
                last_shift = shift["shift"]
        
        if len(change_intervals) >= 3:
            # 変化間隔の規則性チェック
            intervals = [change_intervals[i] - change_intervals[i-1] 
                        for i in range(1, len(change_intervals))]
            
            if intervals:
                avg_interval = statistics.mean(intervals)
                interval_variance = statistics.variance(intervals) if len(intervals) > 1 else 0
                
                return {
                    "change_frequency": len(change_intervals) / len(shifts),
                    "average_interval": avg_interval,
                    "rhythm_regularity": 1.0 / (1.0 + interval_variance),
                    "rhythm_type": self._classify_rhythm(avg_interval, interval_variance)
                }
        
        return None
    
    def _classify_workload(self, load_ratio: float) -> str:
        """負荷分類"""
        if load_ratio >= 1.5:
            return "heavy_load"
        elif load_ratio >= 1.2:
            return "high_load"
        elif load_ratio >= 0.8:
            return "normal_load"
        elif load_ratio >= 0.5:
            return "light_load"
        else:
            return "minimal_load"
    
    def _calculate_load_consistency(self, shifts: List[Dict]) -> float:
        """負荷一貫性計算"""
        if len(shifts) < 7:
            return 1.0
        
        # 週単位での負荷分析
        weekly_loads = []
        week_size = 7
        
        for i in range(0, len(shifts), week_size):
            week_shifts = shifts[i:i + week_size]
            weekly_loads.append(len(week_shifts))
        
        if len(weekly_loads) > 1:
            variance = statistics.variance(weekly_loads)
            mean_load = statistics.mean(weekly_loads)
            cv = variance / mean_load if mean_load > 0 else 0
            return 1.0 / (1.0 + cv)
        
        return 1.0
    
    def _identify_peak_periods(self, shifts: List[Dict]) -> List[Dict[str, Any]]:
        """ピーク期間特定"""
        if len(shifts) < 14:
            return []
        
        # 移動平均による負荷分析
        window_size = 7
        peak_periods = []
        
        for i in range(len(shifts) - window_size + 1):
            window_shifts = shifts[i:i + window_size]
            window_load = len(window_shifts)
            
            # ピーク判定（平均の1.5倍以上）
            overall_avg = len(shifts) / (len(shifts) // window_size)
            if window_load >= overall_avg * 1.5:
                peak_periods.append({
                    "start_position": i,
                    "duration": window_size,
                    "intensity": window_load / overall_avg,
                    "period_type": "high_intensity"
                })
        
        return peak_periods
    
    def _detect_sudden_change(self, shifts: List[Dict]) -> bool:
        """急激な変化検知"""
        if len(shifts) < 6:
            return False
        
        # 前半と後半のパターン比較
        mid_point = len(shifts) // 2
        first_half = shifts[:mid_point]
        second_half = shifts[mid_point:]
        
        first_pattern = Counter(s["shift"] for s in first_half)
        second_pattern = Counter(s["shift"] for s in second_half)
        
        # パターンの類似度計算
        similarity = self._calculate_counter_similarity(first_pattern, second_pattern)
        
        return similarity < 0.3  # 30%未満で急激な変化と判定
    
    def _detect_unusual_concentration(self, shifts: List[Dict]) -> bool:
        """異常な集中検知"""
        if len(shifts) < 5:
            return False
        
        shift_counts = Counter(s["shift"] for s in shifts)
        max_count = max(shift_counts.values())
        
        # 90%以上の集中は異常
        return max_count / len(shifts) > 0.9
    
    def _detect_irregularity(self, shifts: List[Dict]) -> bool:
        """不規則性検知"""
        if len(shifts) < 10:
            return False
        
        # シフト変化の頻度分析
        changes = 0
        for i in range(1, len(shifts)):
            if shifts[i]["shift"] != shifts[i-1]["shift"]:
                changes += 1
        
        change_rate = changes / (len(shifts) - 1)
        
        # 変化率が70%以上で不規則と判定
        return change_rate > 0.7
    
    def _calculate_pattern_similarity(self, pattern1: List[str], pattern2: List[str]) -> float:
        """パターン類似度計算"""
        if len(pattern1) != len(pattern2):
            return 0.0
        
        matches = sum(1 for a, b in zip(pattern1, pattern2) if a == b)
        return matches / len(pattern1)
    
    def _find_dominant_weekly_pattern(self, weekly_patterns: List[List[str]]) -> Optional[List[str]]:
        """支配的週次パターン発見"""
        if not weekly_patterns:
            return None
        
        pattern_counts = Counter(tuple(p) for p in weekly_patterns)
        most_common = pattern_counts.most_common(1)[0]
        
        if most_common[1] >= len(weekly_patterns) * 0.5:  # 50%以上で支配的
            return list(most_common[0])
        
        return None
    
    def _classify_rhythm(self, avg_interval: float, variance: float) -> str:
        """リズム分類"""
        if variance < 0.5:
            if avg_interval <= 2:
                return "high_frequency_regular"
            elif avg_interval <= 5:
                return "medium_frequency_regular"
            else:
                return "low_frequency_regular"
        else:
            return "irregular"
    
    def _calculate_counter_similarity(self, counter1: Counter, counter2: Counter) -> float:
        """Counter類似度計算"""
        all_keys = set(counter1.keys()) | set(counter2.keys())
        if not all_keys:
            return 1.0
        
        total_diff = 0
        total_count = 0
        
        for key in all_keys:
            count1 = counter1.get(key, 0)
            count2 = counter2.get(key, 0)
            total_diff += abs(count1 - count2)
            total_count += max(count1, count2)
        
        return 1.0 - (total_diff / total_count) if total_count > 0 else 1.0
    
    def _analyze_relationship_patterns(self, staff_shifts: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """関係性パターン分析"""
        relationship_patterns = {
            "shift_correlations": {},
            "staff_interactions": {},
            "coverage_patterns": {}
        }
        
        # シフト間の相関分析
        all_shifts = []
        for shifts in staff_shifts.values():
            all_shifts.extend(s["shift"] for s in shifts)
        
        shift_types = list(set(all_shifts))
        
        # 簡易相関分析
        for i, shift1 in enumerate(shift_types):
            for shift2 in shift_types[i+1:]:
                correlation = self._calculate_shift_correlation(staff_shifts, shift1, shift2)
                if abs(correlation) > 0.3:  # 30%以上の相関
                    relationship_patterns["shift_correlations"][f"{shift1}-{shift2}"] = correlation
        
        return relationship_patterns
    
    def _analyze_sequence_patterns(self, staff_shifts: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """連続性パターン分析"""
        sequence_patterns = {}
        
        for staff_name, shifts in staff_shifts.items():
            if len(shifts) < 3:
                continue
            
            # 連続パターンの抽出
            sequences = []
            for i in range(len(shifts) - 2):
                seq = [shifts[i]["shift"], shifts[i+1]["shift"], shifts[i+2]["shift"]]
                sequences.append(tuple(seq))
            
            if sequences:
                seq_counts = Counter(sequences)
                dominant_sequences = {seq: count for seq, count in seq_counts.items() if count >= 2}
                
                if dominant_sequences:
                    sequence_patterns[staff_name] = {
                        "dominant_sequences": dominant_sequences,
                        "sequence_diversity": len(seq_counts),
                        "repetition_rate": sum(dominant_sequences.values()) / len(sequences)
                    }
        
        return sequence_patterns
    
    def _analyze_frequency_patterns(self, staff_shifts: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """頻度パターン分析"""
        frequency_patterns = {
            "shift_frequencies": {},
            "staff_frequencies": {},
            "temporal_frequencies": {}
        }
        
        # 全体的なシフト頻度
        all_shifts = []
        for shifts in staff_shifts.values():
            all_shifts.extend(s["shift"] for s in shifts)
        
        shift_counts = Counter(all_shifts)
        total_shifts = len(all_shifts)
        
        for shift_type, count in shift_counts.items():
            frequency = count / total_shifts
            frequency_patterns["shift_frequencies"][shift_type] = {
                "count": count,
                "frequency": frequency,
                "rarity_level": self._classify_frequency(frequency)
            }
        
        return frequency_patterns
    
    def _calculate_shift_correlation(self, staff_shifts: Dict[str, List[Dict]], shift1: str, shift2: str) -> float:
        """シフト間相関計算"""
        correlations = []
        
        for shifts in staff_shifts.values():
            if len(shifts) < 2:
                continue
            
            shift_sequence = [s["shift"] for s in shifts]
            
            # shift1の後にshift2が来る頻度
            transitions = 0
            shift1_occurrences = 0
            
            for i in range(len(shift_sequence) - 1):
                if shift_sequence[i] == shift1:
                    shift1_occurrences += 1
                    if shift_sequence[i + 1] == shift2:
                        transitions += 1
            
            if shift1_occurrences > 0:
                correlation = transitions / shift1_occurrences
                correlations.append(correlation)
        
        return statistics.mean(correlations) if correlations else 0.0
    
    def _classify_frequency(self, frequency: float) -> str:
        """頻度分類"""
        if frequency >= 0.3:
            return "very_common"
        elif frequency >= 0.1:
            return "common"
        elif frequency >= 0.05:
            return "moderate"
        elif frequency >= 0.01:
            return "rare"
        else:
            return "very_rare"

class ConstraintElevationEngine:
    """制約昇華エンジン - 意図を制約に変換"""
    
    def __init__(self):
        self.engine_name = "制約昇華エンジン"
        self.version = "2.0.0"
        
    def elevate_to_constraints(self, deep_patterns: Dict[str, Any]) -> List[ConstraintRule]:
        """深層パターンを制約ルールに昇華"""
        print(f"\n=== 制約昇華処理開始 ===")
        
        constraint_rules = []
        
        # 1. スタッフ専門性制約の生成
        staff_constraints = self._generate_staff_constraints(
            deep_patterns.get("staff_specialization", {})
        )
        constraint_rules.extend(staff_constraints)
        
        # 2. 時間的制約の生成
        temporal_constraints = self._generate_temporal_constraints(
            deep_patterns.get("temporal_patterns", {})
        )
        constraint_rules.extend(temporal_constraints)
        
        # 3. 負荷分散制約の生成
        workload_constraints = self._generate_workload_constraints(
            deep_patterns.get("workload_distribution", {})
        )
        constraint_rules.extend(workload_constraints)
        
        # 4. 異常回避制約の生成
        anomaly_constraints = self._generate_anomaly_constraints(
            deep_patterns.get("anomaly_patterns", {})
        )
        constraint_rules.extend(anomaly_constraints)
        
        print(f"制約昇華完了: {len(constraint_rules)}個の制約ルール生成")
        return constraint_rules
    
    def _generate_staff_constraints(self, specializations: Dict[str, Any]) -> List[ConstraintRule]:
        """スタッフ制約生成"""
        constraints = []
        
        for staff_name, spec_data in specializations.items():
            for shift_type, spec_info in spec_data.get("primary_specializations", {}).items():
                
                # 専門性レベルに応じた制約タイプ決定
                spec_score = spec_info["specialization_score"]
                classification = spec_info["classification"]
                
                if classification == "high_specialist":
                    constraint_type = ConstraintType.STATIC_HARD
                    violation_penalty = "ERROR: 高度専門性違反"
                elif classification == "moderate_specialist":
                    constraint_type = ConstraintType.STATIC_SOFT
                    violation_penalty = "WARNING: 専門性逸脱"
                else:
                    constraint_type = ConstraintType.DYNAMIC_SOFT
                    violation_penalty = "INFO: 推奨配置と異なる"
                
                # 制約ルール生成
                rule = ConstraintRule(
                    rule_id=f"STAFF_SPEC_{staff_name}_{shift_type}",
                    constraint_type=constraint_type,
                    axis=ConstraintAxis.STAFF_AXIS,
                    condition=f"スタッフ == '{staff_name}'",
                    action=f"シフト == '{shift_type}' (優先度: {spec_score:.0%})",
                    confidence=spec_info["ratio"],
                    evidence={
                        "specialization_score": spec_score,
                        "evidence_count": spec_info["evidence_count"],
                        "continuity": spec_info["continuity"],
                        "concentration": spec_info["concentration"]
                    },
                    measurement=spec_score * 100,  # 0-100の定規値
                    violation_penalty=violation_penalty
                )
                
                constraints.append(rule)
        
        return constraints
    
    def _generate_temporal_constraints(self, temporal_patterns: Dict[str, Any]) -> List[ConstraintRule]:
        """時間的制約生成"""
        constraints = []
        
        # 日次パターン制約
        for staff_name, pattern_data in temporal_patterns.get("daily_patterns", {}).items():
            for day, day_pattern in pattern_data.get("dominant_patterns", {}).items():
                
                rule = ConstraintRule(
                    rule_id=f"TEMPORAL_DAILY_{staff_name}_{day}",
                    constraint_type=ConstraintType.DYNAMIC_SOFT,
                    axis=ConstraintAxis.TIME_AXIS,
                    condition=f"スタッフ == '{staff_name}' AND 曜日 == {day}",
                    action=f"推奨シフト == '{day_pattern['shift']}'",
                    confidence=day_pattern["ratio"],
                    evidence={
                        "pattern_ratio": day_pattern["ratio"],
                        "pattern_strength": pattern_data["pattern_strength"]
                    },
                    measurement=day_pattern["ratio"] * 100,
                    violation_penalty="INFO: 時間パターン逸脱"
                )
                
                constraints.append(rule)
        
        # 週次パターン制約
        for staff_name, weekly_data in temporal_patterns.get("weekly_patterns", {}).items():
            consistency = weekly_data["weekly_consistency"]
            
            if consistency > 0.7:  # 70%以上の一貫性
                rule = ConstraintRule(
                    rule_id=f"TEMPORAL_WEEKLY_{staff_name}",
                    constraint_type=ConstraintType.DYNAMIC_SOFT,
                    axis=ConstraintAxis.TIME_AXIS,
                    condition=f"スタッフ == '{staff_name}' AND 期間 == '週次'",
                    action=f"週次パターン維持 (一貫性: {consistency:.0%})",
                    confidence=consistency,
                    evidence={
                        "weekly_consistency": consistency,
                        "pattern_variations": weekly_data["pattern_variations"]
                    },
                    measurement=consistency * 100,
                    violation_penalty="WARNING: 週次パターン破綻"
                )
                
                constraints.append(rule)
        
        return constraints
    
    def _generate_workload_constraints(self, workload_patterns: Dict[str, Any]) -> List[ConstraintRule]:
        """負荷分散制約生成"""
        constraints = []
        
        for staff_name, load_data in workload_patterns.items():
            load_ratio = load_data["relative_load"]
            classification = load_data["load_classification"]
            
            # 負荷レベルに応じた制約生成
            if classification == "heavy_load":
                constraint_type = ConstraintType.STATIC_HARD
                violation_penalty = "ERROR: 過重負荷違反"
                action = f"負荷削減必須 (現在: {load_ratio:.1f}倍)"
            elif classification == "minimal_load":
                constraint_type = ConstraintType.DYNAMIC_SOFT
                violation_penalty = "INFO: 負荷不足"
                action = f"負荷増加推奨 (現在: {load_ratio:.1f}倍)"
            else:
                continue  # 正常負荷はスキップ
            
            rule = ConstraintRule(
                rule_id=f"WORKLOAD_{staff_name}",
                constraint_type=constraint_type,
                axis=ConstraintAxis.STAFF_AXIS,
                condition=f"スタッフ == '{staff_name}'",
                action=action,
                confidence=abs(1.0 - load_ratio),  # 正常値からの乖離
                evidence={
                    "absolute_load": load_data["absolute_load"],
                    "relative_load": load_ratio,
                    "load_classification": classification
                },
                measurement=abs(load_ratio - 1.0) * 100,  # 正常値からの偏差
                violation_penalty=violation_penalty
            )
            
            constraints.append(rule)
        
        return constraints
    
    def _generate_anomaly_constraints(self, anomaly_patterns: Dict[str, Any]) -> List[ConstraintRule]:
        """異常回避制約生成"""
        constraints = []
        
        for staff_name, anomalies in anomaly_patterns.get("staff_anomalies", {}).items():
            for anomaly_type in anomalies:
                
                if anomaly_type == "sudden_pattern_change":
                    rule = ConstraintRule(
                        rule_id=f"ANOMALY_SUDDEN_{staff_name}",
                        constraint_type=ConstraintType.DYNAMIC_HARD,
                        axis=ConstraintAxis.STAFF_AXIS,
                        condition=f"スタッフ == '{staff_name}' AND パターン変化検出",
                        action="急激なパターン変化を回避",
                        confidence=0.8,
                        evidence={"anomaly_type": anomaly_type},
                        measurement=80.0,
                        violation_penalty="WARNING: パターン急変リスク"
                    )
                elif anomaly_type == "unusual_concentration":
                    rule = ConstraintRule(
                        rule_id=f"ANOMALY_CONC_{staff_name}",
                        constraint_type=ConstraintType.STATIC_SOFT,
                        axis=ConstraintAxis.STAFF_AXIS,
                        condition=f"スタッフ == '{staff_name}'",
                        action="シフト多様性確保",
                        confidence=0.7,
                        evidence={"anomaly_type": anomaly_type},
                        measurement=70.0,
                        violation_penalty="INFO: 過度な集中"
                    )
                elif anomaly_type == "high_irregularity":
                    rule = ConstraintRule(
                        rule_id=f"ANOMALY_IRREG_{staff_name}",
                        constraint_type=ConstraintType.DYNAMIC_SOFT,
                        axis=ConstraintAxis.TIME_AXIS,
                        condition=f"スタッフ == '{staff_name}'",
                        action="パターン規則性向上",
                        confidence=0.6,
                        evidence={"anomaly_type": anomaly_type},
                        measurement=60.0,
                        violation_penalty="INFO: 不規則性高"
                    )
                
                constraints.append(rule)
        
        return constraints

def main():
    """メイン実行関数"""
    print("=" * 80)
    print("高度制約発見システム - 意図発見→制約昇華")
    print("=" * 80)
    
    # システム初期化
    intention_engine = AdvancedIntentionDiscovery()
    constraint_engine = ConstraintElevationEngine()
    
    # Excelファイル検索
    excel_files = list(Path('.').glob('*.xlsx'))
    if not excel_files:
        print("Excelファイルが見つかりません")
        return 1
    
    print(f"発見されたExcelファイル: {len(excel_files)}個")
    
    # デイ関連ファイルを優先
    target_file = None
    for f in excel_files:
        if 'デイ' in f.name and 'テスト' in f.name:
            target_file = f
            break
    
    if not target_file:
        target_file = excel_files[0]
    
    print(f"分析対象: {target_file}")
    
    # Excel読み込み（direct_excel_readerを使用）
    try:
        from direct_excel_reader import DirectExcelReader
        reader = DirectExcelReader()
        data = reader.read_xlsx_as_zip(str(target_file))
        
        if not data:
            print("データ読み込み失敗")
            return 1
            
    except ImportError:
        print("direct_excel_readerが利用できません")
        return 1
    
    # Phase 1: 高度意図発見
    print(f"\n{'='*60}")
    print("Phase 1: 高度意図発見")
    print(f"{'='*60}")
    
    deep_patterns = intention_engine.discover_deep_patterns(data)
    
    # Phase 2: 制約昇華
    print(f"\n{'='*60}")
    print("Phase 2: 制約昇華")
    print(f"{'='*60}")
    
    constraint_rules = constraint_engine.elevate_to_constraints(deep_patterns)
    
    # 結果表示
    print(f"\n{'='*80}")
    print("【制約発見システム結果】")
    print(f"{'='*80}")
    
    print(f"\n◆ 生成された制約ルール: {len(constraint_rules)}個")
    
    # 制約タイプ別集計
    type_counts = Counter(rule.constraint_type.value for rule in constraint_rules)
    print(f"\n◆ 制約タイプ分布:")
    for constraint_type, count in type_counts.items():
        print(f"  - {constraint_type}: {count}個")
    
    # 軸別集計  
    axis_counts = Counter(rule.axis.value for rule in constraint_rules)
    print(f"\n◆ 制約軸分布:")
    for axis, count in axis_counts.items():
        print(f"  - {axis}: {count}個")
    
    # 上位制約表示
    sorted_rules = sorted(constraint_rules, key=lambda r: r.confidence, reverse=True)
    print(f"\n◆ 最高確信度の制約ルール（上位5件）:")
    
    for i, rule in enumerate(sorted_rules[:5], 1):
        print(f"\n{i}. {rule.rule_id}")
        print(f"   タイプ: {rule.constraint_type.value}")
        print(f"   軸: {rule.axis.value}")
        print(f"   条件: {rule.condition}")
        print(f"   行動: {rule.action}")
        print(f"   確信度: {rule.confidence:.0%}")
        print(f"   定規値: {rule.measurement:.1f}/100")
        print(f"   違反時: {rule.violation_penalty}")
    
    # レポート保存
    report = {
        "analysis_metadata": {
            "timestamp": datetime.now().isoformat(),
            "file": str(target_file),
            "method": "advanced_constraint_discovery"
        },
        "discovery_summary": {
            "total_constraints": len(constraint_rules),
            "constraint_types": dict(type_counts),
            "constraint_axes": dict(axis_counts)
        },
        "constraint_rules": [
            {
                "rule_id": rule.rule_id,
                "constraint_type": rule.constraint_type.value,
                "axis": rule.axis.value,
                "condition": rule.condition,
                "action": rule.action,
                "confidence": rule.confidence,
                "measurement": rule.measurement,
                "violation_penalty": rule.violation_penalty,
                "evidence": rule.evidence
            }
            for rule in sorted_rules
        ],
        "deep_patterns": deep_patterns
    }
    
    try:
        with open("advanced_constraint_discovery_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] 高度制約発見レポート保存: advanced_constraint_discovery_report.json")
    except Exception as e:
        print(f"[WARNING] レポート保存エラー: {e}")
    
    print(f"\n[COMPLETE] 高度制約発見システム完了")
    print(f"🎯 意図発見→制約昇華により{len(constraint_rules)}個の強制制約を生成")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())