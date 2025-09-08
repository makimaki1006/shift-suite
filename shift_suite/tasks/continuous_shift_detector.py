# shift_suite/tasks/continuous_shift_detector.py
# 連続勤務検出・管理ユーティリティ
# v1.0.0 - 夜勤→明け番連続勤務対応

from __future__ import annotations

import datetime as dt
import logging
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
import pandas as pd

from ..logger_config import configure_logging

configure_logging()
log = logging.getLogger(__name__)


@dataclass
class ContinuousShift:
    """連続勤務情報を保持するデータクラス"""
    staff: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    start_time: str  # HH:MM
    end_time: str    # HH:MM
    start_code: str  # 夜、など
    end_code: str    # 明、など
    total_duration_hours: float
    is_overnight: bool = True
    
    def get_overlap_times(self) -> List[str]:
        """0:00を含む重複時刻のリストを返す"""
        if self.is_overnight:
            return ["00:00"]
        return []


class ContinuousShiftDetector:
    """連続勤務パターンを検出・管理するクラス"""
    
    def __init__(self):
        self.continuous_shifts: List[ContinuousShift] = []
        self.overnight_codes = {'夜', '明', 'アケ', 'ake', '明け', 'AKE', '夜勤', 'NIGHT'}
        self.night_shift_codes = {'夜', '夜勤', 'NIGHT'}
        self.morning_shift_codes = {'明', 'アケ', 'ake', '明け', 'AKE'}
    
    def detect_continuous_shifts(self, long_df: pd.DataFrame) -> List[ContinuousShift]:
        """
        long_dfから連続勤務パターンを検出
        
        Args:
            long_df: 長時間フォーマットのシフトデータ
            
        Returns:
            検出された連続勤務のリスト
        """
        if long_df.empty:
            return []
        
        log.info("連続勤務検出を開始します")
        continuous_shifts = []
        
        # 職員ごとに処理
        for staff in long_df['staff'].unique():
            staff_data = long_df[long_df['staff'] == staff].copy()
            staff_data['date'] = pd.to_datetime(staff_data['ds']).dt.date
            staff_data['time'] = pd.to_datetime(staff_data['ds']).dt.time
            staff_data = staff_data.sort_values('ds')
            
            # 日付ごとの勤務パターンを分析
            daily_patterns = self._analyze_daily_patterns(staff_data)
            
            # 連続勤務を検出
            continuous_patterns = self._detect_overnight_patterns(daily_patterns, staff)
            continuous_shifts.extend(continuous_patterns)
        
        self.continuous_shifts = continuous_shifts
        log.info(f"連続勤務検出完了: {len(continuous_shifts)}件")
        
        return continuous_shifts
    
    def _analyze_daily_patterns(self, staff_data: pd.DataFrame) -> Dict[str, Dict]:
        """職員の日別勤務パターンを分析"""
        daily_patterns = {}
        
        for date, group in staff_data.groupby('date'):
            date_str = date.strftime('%Y-%m-%d')
            times = [t.strftime('%H:%M') for t in group['time']]
            # 'code'カラムがない場合は'task'カラムを使用
            if 'code' in group.columns:
                codes = group['code'].unique()
            elif 'task' in group.columns:
                codes = group['task'].unique()
            else:
                codes = []
            
            # 夜勤パターンの検出（16:00以降にシフトが開始）
            has_night_shift = any(
                t >= dt.time(16, 0) for t in group['time']
            ) and any(code in self.night_shift_codes for code in codes)
            
            # 明け番パターンの検出（6:00以前にシフトが終了）
            has_morning_shift = any(
                t <= dt.time(10, 0) for t in group['time']
            ) and any(code in self.morning_shift_codes for code in codes)
            
            daily_patterns[date_str] = {
                'times': sorted(times),
                'codes': list(codes),
                'has_night_shift': has_night_shift,
                'has_morning_shift': has_morning_shift,
                'data': group
            }
        
        return daily_patterns
    
    def _detect_overnight_patterns(self, daily_patterns: Dict, staff: str) -> List[ContinuousShift]:
        """日跨ぎ連続勤務パターンを検出"""
        continuous_shifts = []
        dates = sorted(daily_patterns.keys())
        
        for i in range(len(dates) - 1):
            current_date = dates[i]
            next_date = dates[i + 1]
            
            current_pattern = daily_patterns[current_date]
            next_pattern = daily_patterns[next_date]
            
            # 夜勤→明け番パターンの検出
            if (current_pattern['has_night_shift'] and 
                next_pattern['has_morning_shift'] and
                self._is_consecutive_dates(current_date, next_date)):
                
                # 連続勤務の詳細分析
                continuous_shift = self._create_continuous_shift(
                    staff, current_date, next_date, 
                    current_pattern, next_pattern
                )
                
                if continuous_shift:
                    continuous_shifts.append(continuous_shift)
                    log.debug(f"連続勤務検出: {staff} {current_date}→{next_date}")
        
        return continuous_shifts
    
    def _is_consecutive_dates(self, date1: str, date2: str) -> bool:
        """2つの日付が連続しているかチェック"""
        try:
            d1 = dt.datetime.strptime(date1, '%Y-%m-%d').date()
            d2 = dt.datetime.strptime(date2, '%Y-%m-%d').date()
            return (d2 - d1).days == 1
        except:
            return False
    
    def _create_continuous_shift(self, staff: str, start_date: str, end_date: str,
                               start_pattern: Dict, end_pattern: Dict) -> Optional[ContinuousShift]:
        """連続勤務オブジェクトを作成"""
        try:
            # 開始時刻と終了時刻を特定
            start_times = start_pattern['times']
            end_times = end_pattern['times']
            
            if not start_times or not end_times:
                return None
            
            # 夜勤の開始時刻（最も早い時刻）
            start_time = min(start_times)
            
            # 明け番の終了時刻（最も遅い時刻）
            end_time = max(end_times)
            
            # 勤務コードを特定
            start_codes = [c for c in start_pattern['codes'] if c in self.night_shift_codes]
            end_codes = [c for c in end_pattern['codes'] if c in self.morning_shift_codes]
            
            start_code = start_codes[0] if start_codes else start_pattern['codes'][0]
            end_code = end_codes[0] if end_codes else end_pattern['codes'][0]
            
            # 総勤務時間を計算
            total_duration = self._calculate_total_duration(
                start_date, start_time, end_date, end_time
            )
            
            return ContinuousShift(
                staff=staff,
                start_date=start_date,
                end_date=end_date,
                start_time=start_time,
                end_time=end_time,
                start_code=start_code,
                end_code=end_code,
                total_duration_hours=total_duration,
                is_overnight=True
            )
            
        except Exception as e:
            log.warning(f"連続勤務作成エラー: {staff} {start_date}→{end_date}: {e}")
            return None
    
    def _calculate_total_duration(self, start_date: str, start_time: str, 
                                end_date: str, end_time: str) -> float:
        """総勤務時間を計算（時間単位）"""
        try:
            start_dt = dt.datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
            end_dt = dt.datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")
            
            duration = end_dt - start_dt
            return duration.total_seconds() / 3600
        except:
            return 0.0
    
    def get_duplicate_time_slots(self, target_date: str) -> Set[Tuple[str, str]]:
        """
        指定日付で重複する可能性のある時刻スロットを取得
        
        Returns:
            Set of (staff, time) tuples that should be deduplicated
        """
        duplicates = set()
        
        for shift in self.continuous_shifts:
            if shift.end_date == target_date:
                # 翌日0:00は前日夜勤の継続として重複カウント対象
                for overlap_time in shift.get_overlap_times():
                    duplicates.add((shift.staff, overlap_time))
        
        return duplicates
    
    def should_adjust_need(self, time_slot: str, date: str) -> Tuple[bool, int]:
        """
        指定時刻・日付でNeed値の調整が必要かチェック
        
        Returns:
            (adjustment_needed, continuing_staff_count)
        """
        if not time_slot.startswith('00:'):
            return False, 0
        
        # 当日0:00時点で前日からの継続勤務者数を計算
        continuing_staff = set()
        for shift in self.continuous_shifts:
            if shift.end_date == date and "00:00" in shift.get_overlap_times():
                continuing_staff.add(shift.staff)
        
        return len(continuing_staff) > 0, len(continuing_staff)
    
    def get_continuous_shift_summary(self) -> Dict:
        """連続勤務の統計サマリーを取得"""
        if not self.continuous_shifts:
            return {"total_count": 0}
        
        total_count = len(self.continuous_shifts)
        avg_duration = sum(s.total_duration_hours for s in self.continuous_shifts) / total_count
        max_duration = max(s.total_duration_hours for s in self.continuous_shifts)
        
        staff_counts = {}
        for shift in self.continuous_shifts:
            staff_counts[shift.staff] = staff_counts.get(shift.staff, 0) + 1
        
        return {
            "total_count": total_count,
            "average_duration_hours": round(avg_duration, 2),
            "max_duration_hours": round(max_duration, 2),
            "unique_staff_count": len(staff_counts),
            "most_frequent_staff": max(staff_counts.items(), key=lambda x: x[1]) if staff_counts else None
        }