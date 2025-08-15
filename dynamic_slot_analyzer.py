#!/usr/bin/env python3
"""
動的スロット間隔対応の時間軸分析器
15分、30分、60分などの異なるスロット間隔に自動対応
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime, time, timedelta
from collections import defaultdict, Counter
import logging

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

log = logging.getLogger(__name__)

class DynamicSlotAnalyzer:
    """
    動的スロット間隔対応の時間軸分析器
    データから自動的にスロット間隔を検出し、適応的に分析
    """
    
    def __init__(self, auto_detect_slot: bool = True):
        self.auto_detect_slot = auto_detect_slot
        self.detected_slot_minutes = None
        self.detected_slot_hours = None
        self.slot_pattern = None
        
    def detect_slot_interval(self, timestamp_data: pd.Series) -> Dict[str, any]:
        """
        実際のタイムスタンプデータからスロット間隔を自動検出
        
        Args:
            timestamp_data: datetime型のタイムスタンプ系列
            
        Returns:
            検出結果辞書
        """
        if timestamp_data.empty:
            return {'slot_minutes': 30, 'slot_hours': 0.5, 'confidence': 0.0}
        
        # タイムスタンプを時刻のみに変換
        time_only = timestamp_data.dt.time
        
        # 分の値を抽出して分析
        minutes_set = set()
        for t in time_only.dropna():
            minutes_set.add(t.minute)
        
        # 分の値から間隔を推定
        minutes_list = sorted(list(minutes_set))
        
        # 一般的なスロット間隔パターンを確認
        slot_patterns = {
            15: [0, 15, 30, 45],
            30: [0, 30],
            60: [0],
            20: [0, 20, 40],
            10: [0, 10, 20, 30, 40, 50]
        }
        
        best_match = None
        best_score = 0.0
        
        for slot_min, pattern in slot_patterns.items():
            # パターンとの一致度を計算
            matches = len(set(minutes_list) & set(pattern))
            total = len(set(minutes_list) | set(pattern))
            score = matches / total if total > 0 else 0.0
            
            if score > best_score:
                best_score = score
                best_match = slot_min
        
        # デフォルトは30分
        if best_match is None or best_score < 0.5:
            best_match = 30
            best_score = 0.5
        
        self.detected_slot_minutes = best_match
        self.detected_slot_hours = best_match / 60.0
        self.slot_pattern = slot_patterns.get(best_match, [0, 30])
        
        log.info(f"[DynamicSlot] 検出されたスロット間隔: {best_match}分 (信頼度: {best_score:.2f})")
        log.info(f"[DynamicSlot] 検出された分パターン: {minutes_list}")
        
        return {
            'slot_minutes': best_match,
            'slot_hours': best_match / 60.0,
            'confidence': best_score,
            'detected_pattern': self.slot_pattern,
            'actual_minutes': minutes_list
        }
    
    def generate_dynamic_time_slots(self, slot_minutes: int = None) -> List[str]:
        """指定されたスロット間隔で24時間の時間スロットを生成"""
        if slot_minutes is None:
            slot_minutes = self.detected_slot_minutes or 30
        
        slots = []
        current_time = time(0, 0)
        slots_per_day = 24 * 60 // slot_minutes
        
        for i in range(slots_per_day):
            slots.append(current_time.strftime("%H:%M"))
            # スロット間隔を追加
            minutes = current_time.minute + slot_minutes
            hours = current_time.hour
            while minutes >= 60:
                minutes -= 60
                hours += 1
            if hours >= 24:
                break  # 24時間を超える場合は終了
            current_time = time(hours, minutes)
        
        return slots
    
    def analyze_with_dynamic_slots(
        self, 
        actual_data: pd.DataFrame,
        need_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, any]:
        """
        動的スロット検出による包括的分析
        
        Args:
            actual_data: 実績データ (ds列を含む)
            need_data: 需要データ（オプション）
            
        Returns:
            包括的分析結果
        """
        analysis_result = {
            'slot_detection': {},
            'role_analysis': {},
            'employment_analysis': {},
            'time_pattern_analysis': {},
            'recommendations': []
        }
        
        if actual_data.empty or 'ds' not in actual_data.columns:
            log.warning("[DynamicSlot] 有効なデータが見つかりません")
            return analysis_result
        
        # 1. スロット間隔の自動検出
        if self.auto_detect_slot:
            slot_detection = self.detect_slot_interval(actual_data['ds'])
            analysis_result['slot_detection'] = slot_detection
        else:
            # デフォルト値使用
            analysis_result['slot_detection'] = {
                'slot_minutes': 30, 'slot_hours': 0.5, 
                'confidence': 1.0, 'detected_pattern': [0, 30]
            }
        
        slot_hours = analysis_result['slot_detection']['slot_hours']
        slot_minutes = analysis_result['slot_detection']['slot_minutes']
        
        # 2. 勤務レコードのみ抽出
        work_records = actual_data[actual_data['parsed_slots_count'] > 0].copy() if 'parsed_slots_count' in actual_data.columns else actual_data.copy()
        
        if work_records.empty:
            log.warning("[DynamicSlot] 勤務レコードが見つかりません")
            return analysis_result
        
        # 3. 職種別分析（動的スロット対応）
        if 'role' in work_records.columns:
            role_analysis = self._analyze_by_category(
                work_records, 'role', slot_hours, slot_minutes
            )
            analysis_result['role_analysis'] = role_analysis
        
        # 4. 雇用形態別分析（動的スロット対応）
        if 'employment' in work_records.columns:
            employment_analysis = self._analyze_by_category(
                work_records, 'employment', slot_hours, slot_minutes
            )
            analysis_result['employment_analysis'] = employment_analysis
        
        # 5. 時間パターン分析
        time_analysis = self._analyze_time_patterns(
            work_records, slot_minutes
        )
        analysis_result['time_pattern_analysis'] = time_analysis
        
        # 6. 推奨事項生成
        recommendations = self._generate_recommendations(analysis_result)
        analysis_result['recommendations'] = recommendations
        
        log.info(f"[DynamicSlot] 動的分析完了: {slot_minutes}分間隔, 職種{len(analysis_result['role_analysis'])}個, 雇用形態{len(analysis_result['employment_analysis'])}個")
        
        return analysis_result
    
    def _analyze_by_category(
        self, 
        data: pd.DataFrame, 
        category_col: str, 
        slot_hours: float,
        slot_minutes: int
    ) -> Dict[str, Dict]:
        """カテゴリ別（職種・雇用形態）の動的分析"""
        
        category_analysis = {}
        
        for category in data[category_col].unique():
            if not category or category == '':
                continue
                
            category_data = data[data[category_col] == category]
            
            # 時間分布分析（動的スロット対応）
            time_distribution = self._calculate_time_distribution(
                category_data, slot_minutes
            )
            
            # 供給量計算（動的スロット対応）
            supply_by_slot = self._calculate_supply_by_slot(
                category_data, slot_hours
            )
            
            # カバレッジ分析
            coverage_analysis = self._calculate_coverage(
                supply_by_slot, slot_minutes
            )
            
            # 効率性指標
            efficiency_metrics = self._calculate_efficiency_metrics(
                category_data, slot_hours
            )
            
            category_analysis[category] = {
                'total_records': len(category_data),
                'total_hours': len(category_data) * slot_hours,
                'unique_staff': category_data['staff'].nunique() if 'staff' in category_data.columns else 0,
                'time_distribution': time_distribution,
                'supply_by_slot': supply_by_slot,
                'coverage_analysis': coverage_analysis,
                'efficiency_metrics': efficiency_metrics,
                'slot_utilization': len(supply_by_slot) / (24 * 60 // slot_minutes) if slot_minutes > 0 else 0
            }
        
        return category_analysis
    
    def _calculate_time_distribution(self, data: pd.DataFrame, slot_minutes: int) -> Dict:
        """時間分布の計算（動的スロット対応）"""
        
        # スロット別分布
        slot_distribution = defaultdict(int)
        hour_distribution = defaultdict(int)
        
        for _, record in data.iterrows():
            timestamp = record['ds']
            
            # スロット単位での分布
            slot_key = self._timestamp_to_slot_key(timestamp, slot_minutes)
            slot_distribution[slot_key] += 1
            
            # 時間単位での分布
            hour_distribution[timestamp.hour] += 1
        
        # ピーク時間の特定
        peak_slots = sorted(slot_distribution.items(), key=lambda x: x[1], reverse=True)[:5]
        peak_hours = sorted(hour_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'slot_distribution': dict(slot_distribution),
            'hour_distribution': dict(hour_distribution),
            'peak_slots': peak_slots,
            'peak_hours': peak_hours,
            'total_unique_slots': len(slot_distribution),
            'busiest_slot': peak_slots[0] if peak_slots else None,
            'quietest_periods': self._identify_quiet_periods(slot_distribution, slot_minutes)
        }
    
    def _timestamp_to_slot_key(self, timestamp: datetime, slot_minutes: int) -> str:
        """タイムスタンプをスロットキーに変換（動的間隔対応）"""
        
        # 分を最寄りのスロット境界に丸める
        minutes = timestamp.minute
        slot_minute = (minutes // slot_minutes) * slot_minutes
        
        return f"{timestamp.hour:02d}:{slot_minute:02d}"
    
    def _calculate_supply_by_slot(self, data: pd.DataFrame, slot_hours: float) -> Dict[str, float]:
        """スロット別供給量計算"""
        
        supply_by_slot = defaultdict(float)
        
        for _, record in data.iterrows():
            time_slot = record['ds'].strftime("%H:%M")
            supply_by_slot[time_slot] += slot_hours
            
        return dict(supply_by_slot)
    
    def _calculate_coverage(self, supply_by_slot: Dict[str, float], slot_minutes: int) -> Dict:
        """カバレッジ分析"""
        
        total_possible_slots = 24 * 60 // slot_minutes
        covered_slots = len(supply_by_slot)
        
        return {
            'total_possible_slots': total_possible_slots,
            'covered_slots': covered_slots,
            'coverage_ratio': covered_slots / total_possible_slots,
            'uncovered_slots': total_possible_slots - covered_slots,
            'average_supply_per_slot': np.mean(list(supply_by_slot.values())) if supply_by_slot else 0
        }
    
    def _calculate_efficiency_metrics(self, data: pd.DataFrame, slot_hours: float) -> Dict:
        """効率性指標の計算"""
        
        total_hours = len(data) * slot_hours
        unique_staff = data['staff'].nunique() if 'staff' in data.columns else 1
        
        return {
            'total_hours': total_hours,
            'hours_per_staff': total_hours / max(unique_staff, 1),
            'utilization_score': min(1.0, total_hours / max(unique_staff * 8, 1)),  # 8時間を基準とした利用率
            'distribution_evenness': self._calculate_distribution_evenness(data)
        }
    
    def _calculate_distribution_evenness(self, data: pd.DataFrame) -> float:
        """分布の均等性を計算（Jain指数）"""
        
        if 'staff' not in data.columns:
            return 1.0
        
        staff_counts = data['staff'].value_counts().values
        if len(staff_counts) <= 1:
            return 1.0
        
        # Jain指数
        sum_counts = np.sum(staff_counts)
        sum_squares = np.sum(staff_counts ** 2)
        n = len(staff_counts)
        
        jain_index = (sum_counts ** 2) / (n * sum_squares)
        return jain_index
    
    def _identify_quiet_periods(self, slot_distribution: Dict, slot_minutes: int) -> List[str]:
        """静かな時間帯の特定"""
        
        if not slot_distribution:
            return []
        
        min_activity = min(slot_distribution.values())
        quiet_slots = [slot for slot, count in slot_distribution.items() if count == min_activity]
        
        return quiet_slots[:5]  # 最大5個まで
    
    def _analyze_time_patterns(self, data: pd.DataFrame, slot_minutes: int) -> Dict:
        """全体的な時間パターン分析"""
        
        # 曜日別分析
        weekday_distribution = defaultdict(int)
        for _, record in data.iterrows():
            weekday = record['ds'].strftime('%A')
            weekday_distribution[weekday] += 1
        
        # 時間帯別密度
        hourly_density = defaultdict(list)
        for _, record in data.iterrows():
            hour = record['ds'].hour
            hourly_density[hour].append(record['ds'])
        
        # 密度統計
        density_stats = {}
        for hour, timestamps in hourly_density.items():
            density_stats[hour] = {
                'count': len(timestamps),
                'density': len(timestamps) / max(60 // slot_minutes, 1)  # 1時間あたりの理論最大スロット数で正規化
            }
        
        return {
            'weekday_distribution': dict(weekday_distribution),
            'hourly_density': density_stats,
            'busiest_weekday': max(weekday_distribution.items(), key=lambda x: x[1]) if weekday_distribution else None,
            'peak_density_hour': max(density_stats.items(), key=lambda x: x[1]['density']) if density_stats else None
        }
    
    def _generate_recommendations(self, analysis_result: Dict) -> List[str]:
        """分析結果に基づく推奨事項"""
        
        recommendations = []
        
        # スロット間隔に関する推奨
        confidence = analysis_result['slot_detection']['confidence']
        slot_minutes = analysis_result['slot_detection']['slot_minutes']
        
        if confidence < 0.7:
            recommendations.append(f"スロット間隔の信頼度が低い({confidence:.2f})。データの一貫性を確認してください。")
        
        if slot_minutes < 30:
            recommendations.append(f"{slot_minutes}分間隔は細かい分析に適しています。詳細な需給マッチング分析を推奨します。")
        elif slot_minutes > 30:
            recommendations.append(f"{slot_minutes}分間隔は大局的な傾向把握に適しています。より細かい分析が必要な場合は間隔の見直しを検討してください。")
        
        # カバレッジに関する推奨
        role_analysis = analysis_result.get('role_analysis', {})
        for role, data in role_analysis.items():
            coverage = data['coverage_analysis']['coverage_ratio']
            if coverage < 0.3:
                recommendations.append(f"職種'{role}'の時間カバレッジが低い({coverage:.1%})。勤務時間の拡充を検討してください。")
        
        return recommendations

def test_dynamic_slot_analyzer():
    """動的スロット分析器のテスト"""
    
    print("=== 動的スロット間隔対応テスト ===")
    
    try:
        # テスト用のサンプルデータ生成（異なるスロット間隔）
        sample_data_15min = pd.DataFrame({
            'staff': ['田中', '佐藤', '鈴木'] * 8,
            'role': ['看護師', '介護士', '事務'] * 8,
            'employment': ['常勤', 'パート', 'スポット'] * 8,
            'ds': pd.date_range('2025-01-01 08:00', periods=24, freq='15min'),
            'parsed_slots_count': [1] * 24
        })
        
        sample_data_60min = pd.DataFrame({
            'staff': ['田中', '佐藤', '鈴木'] * 4,
            'role': ['看護師', '介護士', '事務'] * 4,
            'employment': ['常勤', 'パート', 'スポット'] * 4,
            'ds': pd.date_range('2025-01-01 08:00', periods=12, freq='60min'),
            'parsed_slots_count': [1] * 12
        })
        
        analyzer = DynamicSlotAnalyzer(auto_detect_slot=True)
        
        # 15分間隔データのテスト
        print("\n=== 15分間隔データ分析 ===")
        result_15min = analyzer.analyze_with_dynamic_slots(sample_data_15min)
        
        detection_15 = result_15min['slot_detection']
        print(f"検出間隔: {detection_15['slot_minutes']}分 (信頼度: {detection_15['confidence']:.2f})")
        print(f"職種別分析数: {len(result_15min['role_analysis'])}")
        
        # 60分間隔データのテスト
        print("\n=== 60分間隔データ分析 ===")
        result_60min = analyzer.analyze_with_dynamic_slots(sample_data_60min)
        
        detection_60 = result_60min['slot_detection']
        print(f"検出間隔: {detection_60['slot_minutes']}分 (信頼度: {detection_60['confidence']:.2f})")
        print(f"雇用形態別分析数: {len(result_60min['employment_analysis'])}")
        
        # 推奨事項表示
        print(f"\n=== 推奨事項 ===")
        for rec in result_15min['recommendations']:
            print(f"- {rec}")
        
        return True
        
    except Exception as e:
        print(f"テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dynamic_slot_analyzer()
    print(f"\n動的スロット対応テスト: {'成功' if success else '失敗'}")