#!/usr/bin/env python3
"""
時間軸ベース不足時間計算モジュール (動的データ対応版)
按分計算に代わる真の分析価値を持つ計算手法
"""

from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
import logging
from datetime import datetime, time, timedelta
from collections import defaultdict

log = logging.getLogger(__name__)

class TimeAxisShortageCalculator:
    """
    時間軸ベース不足時間計算クラス (動的データ対応)
    動的スロット間隔での真の過不足分析
    実需要データを最優先で活用する現実的な計算
    """
    
    def __init__(self, slot_hours: float = 0.5, slot_minutes: int = 30, auto_detect: bool = True, 
                 total_shortage_baseline: float = None):
        self.slot_hours = slot_hours
        self.slot_minutes = slot_minutes
        self.auto_detect = auto_detect
        self.detected_slot_info = None
        self.total_shortage_baseline = total_shortage_baseline  # 検証用途のみ
    
    def _calculate_demand_coverage(
        self, 
        supply_by_slot: Dict[str, float],
        need_data: pd.DataFrame,
        working_patterns: Dict,
        role_supply_ratio: float = 1.0
    ) -> Dict:
        """需要カバレッジ分析（動的データ対応）"""
        
        total_supply = sum(supply_by_slot.values())
        
        # 🔧 DYNAMIC FIX: 動的データに対応した真の需要計算
        #
        # 【真の解決方針】：
        # - 実需要データ(need_data)を最優先で活用
        # - 動的データに対応した需要計算
        # - total_shortage_baselineは検証用途のみに使用
        
        estimated_demand = self._calculate_realistic_demand(
            supply_by_slot, need_data, working_patterns, role_supply_ratio
        )
        
        log.info(f"[DYNAMIC_FIX] 動的需要計算: 需要={estimated_demand:.1f}h, 供給={total_supply:.1f}h, 比率={role_supply_ratio:.3f}")
        log.debug(f"[DYNAMIC_FIX] 需要データ利用可能: {not need_data.empty}, 時間帯数: {len(supply_by_slot)}")
        
        # 動的計算による不足/過剰分析
        shortage = max(0, estimated_demand - total_supply)
        excess = max(0, total_supply - estimated_demand)
        
        log.debug(f"[DYNAMIC_FIX] 動的計算結果 - 不足:{shortage:.1f}h, 過剰:{excess:.1f}h")
        efficiency_ratio = total_supply / max(estimated_demand, 1)
        
        return {
            'total_demand': estimated_demand,
            'total_supply': total_supply,
            'total_shortage': shortage,
            'total_excess': excess,
            'efficiency_ratio': efficiency_ratio,
            'coverage_ratio': min(1.0, efficiency_ratio)
        }
        
    def _calculate_realistic_demand(
        self,
        supply_by_slot: Dict[str, float],
        need_data: pd.DataFrame,
        working_patterns: Dict,
        role_supply_ratio: float = 1.0
    ) -> float:
        """動的データに対応した現実的な需要計算"""
        
        total_supply = sum(supply_by_slot.values())
        
        # 1. 実需要データが利用可能な場合は最優先で使用
        if not need_data.empty and len(need_data.columns) > 0:
            try:
                # 数値列のみを抽出
                numeric_cols = need_data.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    # 時間帯別需要の平均を計算
                    daily_average_demand = need_data[numeric_cols].mean().sum()
                    # スロット数から時間に変換
                    hourly_demand = daily_average_demand * self.slot_hours
                    
                    log.debug(f"[DYNAMIC_FIX] 実需要データから計算: {hourly_demand:.1f}h/日")
                    return hourly_demand
            except Exception as e:
                log.warning(f"[DYNAMIC_FIX] 実需要データ解析エラー: {e}")
        
        # 2. 働き方パターンに基づく需要推定
        if working_patterns and 'peak_hours' in working_patterns:
            peak_ratio = working_patterns.get('peak_ratio', 1.2)
            estimated_demand = total_supply * peak_ratio
            log.debug(f"[DYNAMIC_FIX] パターンベース推定: {estimated_demand:.1f}h (peak_ratio={peak_ratio})")
            return estimated_demand
        
        # 3. 供給比率に基づく動的推定
        if role_supply_ratio > 0:
            # 供給比率が低い場合は潜在需要が高いと推定
            demand_multiplier = min(1.5, 1.0 + (1.0 - role_supply_ratio) * 0.5)
            estimated_demand = total_supply * demand_multiplier
            log.debug(f"[DYNAMIC_FIX] 比率ベース推定: {estimated_demand:.1f}h (multiplier={demand_multiplier:.2f})")
            return estimated_demand
        
        # 4. フォールバック: 保守的推定
        fallback_demand = total_supply * 1.05  # 最小限の5%マージン
        log.debug(f"[DYNAMIC_FIX] フォールバック推定: {fallback_demand:.1f}h")
        return fallback_demand
    
    def calculate_role_based_shortage(
        self, 
        actual_data: pd.DataFrame,
        need_data: pd.DataFrame
    ) -> Dict[str, Dict]:
        """職種別の時間軸ベース不足時間計算"""
        role_analysis = {}
        
        # 勤務レコードのみ抽出
        work_records = actual_data[actual_data['parsed_slots_count'] > 0].copy()
        
        if work_records.empty:
            log.warning("[TimeAxis] 勤務レコードが見つかりません")
            return {}
        
        # 動的スロット検出
        if self.auto_detect and 'ds' in work_records.columns:
            self._detect_and_update_slot_interval(work_records['ds'])
        
        # 職種ごとに分析
        for role in work_records['role'].unique():
            if not role or role == '':
                continue
                
            role_records = work_records[work_records['role'] == role]
            
            # 職種別供給量を時間スロット別に集計
            role_supply = self._aggregate_supply_by_timeslot(role_records)
            
            # 職種別実働パターン分析
            working_patterns = self._analyze_working_patterns(role_records)
            
            # 需要との比較
            total_records = len(work_records)
            role_records_count = len(role_records)
            role_supply_ratio = role_records_count / max(total_records, 1)
            
            demand_coverage = self._calculate_demand_coverage(
                role_supply, need_data, working_patterns, role_supply_ratio
            )
            
            # 分析結果を保存
            role_analysis[role] = {
                **demand_coverage,
                'supply_by_slot': role_supply,
                'working_patterns': working_patterns,
                'record_count': role_records_count,
                'supply_ratio': role_supply_ratio
            }
            
            log.debug(f"[TimeAxis] {role}: 需要{demand_coverage['total_demand']:.1f}h, "
                     f"供給{demand_coverage['total_supply']:.1f}h, "
                     f"不足{demand_coverage['total_shortage']:.1f}h")
        
        log.info(f"[TimeAxis] 職種別分析完了: {len(role_analysis)}職種")
        return role_analysis
    
    def calculate_employment_based_shortage(
        self, 
        actual_data: pd.DataFrame,
        need_data: pd.DataFrame,
        cost_per_hour: Optional[Dict[str, float]] = None
    ) -> Dict[str, Dict]:
        """雇用形態別の時間軸ベース不足時間計算 (動的データ対応)"""
        employment_analysis = {}
        
        # 勤務レコードのみ抽出
        work_records = actual_data[actual_data['parsed_slots_count'] > 0].copy()
        
        if work_records.empty:
            log.warning("[TimeAxis] 勤務レコードが見つかりません")
            return {}
        
        # 動的スロット検出（職種ベース分析と共有）
        if self.auto_detect and 'ds' in work_records.columns:
            self._detect_and_update_slot_interval(work_records['ds'])
        
        # 雇用形態ごとに分析
        for employment in work_records['employment'].unique():
            if not employment or employment == '':
                continue
                
            emp_records = work_records[work_records['employment'] == employment]
            
            # 雇用形態別供給量を時間スロット別に集計
            emp_supply = self._aggregate_supply_by_timeslot(emp_records)
            
            # 雇用形態別実働パターン分析
            working_patterns = self._analyze_working_patterns(emp_records)
            
            # 需要との比較（動的計算）
            total_records = len(work_records)
            emp_records_count = len(emp_records)
            emp_supply_ratio = emp_records_count / max(total_records, 1)
            
            demand_coverage = self._calculate_demand_coverage(
                emp_supply, need_data, working_patterns, emp_supply_ratio
            )
            
            # コスト分析
            hourly_cost = cost_per_hour.get(employment, 0) if cost_per_hour else 0
            
            employment_analysis[employment] = {
                **demand_coverage,
                'supply_by_slot': emp_supply,
                'working_patterns': working_patterns,
                'record_count': emp_records_count,
                'supply_ratio': emp_supply_ratio,
                'hourly_cost': hourly_cost,
                'total_cost': demand_coverage['total_supply'] * hourly_cost
            }
            
            log.debug(f"[TimeAxis] {employment}: 需要{demand_coverage['total_demand']:.1f}h, "
                     f"供給{demand_coverage['total_supply']:.1f}h, "
                     f"不足{demand_coverage['total_shortage']:.1f}h")
        
        log.info(f"[TimeAxis] 雇用形態別分析完了: {len(employment_analysis)}形態")
        return employment_analysis
    
    def _aggregate_supply_by_timeslot(self, records: pd.DataFrame) -> Dict[str, float]:
        """時間スロット別供給量集計"""
        if 'ds' not in records.columns:
            return {}
        
        supply_by_slot = defaultdict(float)
        
        for _, record in records.iterrows():
            timestamp = record['ds']
            slots = record.get('parsed_slots_count', 1)
            time_key = timestamp.strftime('%H:%M')
            supply_by_slot[time_key] += slots * self.slot_hours
        
        return dict(supply_by_slot)
    
    def _analyze_working_patterns(self, records: pd.DataFrame) -> Dict:
        """実働パターン分析"""
        patterns = {}
        
        if 'ds' not in records.columns or records.empty:
            return patterns
        
        # 時間帯別集計
        hour_counts = defaultdict(int)
        for _, record in records.iterrows():
            hour = record['ds'].hour
            hour_counts[hour] += 1
        
        if hour_counts:
            peak_hour = max(hour_counts, key=hour_counts.get)
            total_records = sum(hour_counts.values())
            peak_ratio = hour_counts[peak_hour] / max(total_records, 1)
            
            patterns.update({
                'peak_hours': [peak_hour],
                'peak_ratio': min(2.0, 1.0 + peak_ratio),  # 最大2倍まで
                'hour_distribution': dict(hour_counts)
            })
        
        return patterns
    
    def _detect_and_update_slot_interval(self, timestamp_data: pd.Series) -> None:
        """タイムスタンプデータからスロット間隔を自動検出・更新"""
        
        if timestamp_data.empty:
            return
        
        # 分の値を抽出して分析
        minutes_set = set()
        for timestamp in timestamp_data.dropna():
            minutes_set.add(timestamp.minute)
        
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
        
        if best_match and best_score > 0.6:
            self.slot_minutes = best_match
            self.slot_hours = best_match / 60.0
            self.detected_slot_info = {
                'detected_minutes': best_match,
                'confidence': best_score,
                'original_patterns': minutes_list
            }
            log.info(f"[TimeAxis] 動的スロット検出: {best_match}分 (信頼度: {best_score:.2f})")

def calculate_time_axis_shortage(
    working_data: pd.DataFrame, 
    need_data: Optional[pd.DataFrame] = None,
    total_shortage_baseline: float = None
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    按分計算の代替として時間軸ベース計算を実行（動的データ対応）
    
    Args:
        working_data: 勤務データ
        need_data: 需要データ（オプション、優先的に使用）
        total_shortage_baseline: 按分計算の総不足時間（検証用途）
        
    Returns:
        (職種別不足時間辞書, 雇用形態別不足時間辞書)
    """
    calculator = TimeAxisShortageCalculator(
        auto_detect=True, 
        total_shortage_baseline=total_shortage_baseline  # 検証用途のみ
    )
    
    # 安全なneed_data処理
    safe_need_data = need_data if need_data is not None and not need_data.empty else pd.DataFrame()
    
    # 職種別分析
    role_analysis = calculator.calculate_role_based_shortage(
        working_data, safe_need_data
    )
    
    # 雇用形態別分析
    employment_analysis = calculator.calculate_employment_based_shortage(
        working_data, safe_need_data
    )
    
    # 結果を辞書形式で返す（既存インターフェース互換）
    role_shortages = {
        role: analysis['total_shortage'] 
        for role, analysis in role_analysis.items()
    }
    
    employment_shortages = {
        employment: analysis['total_shortage'] 
        for employment, analysis in employment_analysis.items()
    }
    
    # スロット情報を安全に取得
    confidence = 'N/A'
    if calculator.detected_slot_info and isinstance(calculator.detected_slot_info, dict):
        confidence = calculator.detected_slot_info.get('confidence', 'N/A')
    
    log.info(f"[TimeAxis] 検出スロット: {calculator.slot_minutes}分 (信頼度: {confidence})")
    log.info(f"[TimeAxis] 時間軸ベース計算完了: 職種{len(role_shortages)}個, 雇用形態{len(employment_shortages)}個")
    
    return role_shortages, employment_shortages