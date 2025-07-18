# shift_suite/tasks/dynamic_continuous_shift_detector.py
# 動的連続勤務検出システム - 完全に汎用的なデータ対応
# v2.0.0 - 設定ベース動的検出対応

from __future__ import annotations

import datetime as dt
import logging
import json
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd

from ..logger_config import configure_logging

configure_logging()
log = logging.getLogger(__name__)


@dataclass
class ShiftPattern:
    """勤務パターン定義"""
    code: str
    start_time: str  # HH:MM
    end_time: str    # HH:MM
    description: str = ""
    is_overnight: bool = False
    priority: int = 0  # 連続勤務判定での優先度
    
    @property
    def start_time_obj(self) -> dt.time:
        return dt.datetime.strptime(self.start_time, "%H:%M").time()
    
    @property
    def end_time_obj(self) -> dt.time:
        return dt.datetime.strptime(self.end_time, "%H:%M").time()
    
    def is_in_timerange(self, check_time: dt.time) -> bool:
        """指定時刻がこのシフトパターンの範囲内かチェック"""
        start = self.start_time_obj
        end = self.end_time_obj
        
        if not self.is_overnight:
            # 通常勤務: start <= time <= end
            return start <= check_time <= end
        else:
            # 日跨ぎ勤務: time >= start OR time <= end
            return check_time >= start or check_time <= end


@dataclass
class ContinuousShiftRule:
    """連続勤務ルール定義"""
    name: str
    from_patterns: List[str]  # 開始パターンコードリスト
    to_patterns: List[str]    # 終了パターンコードリスト
    max_gap_hours: float = 1.0  # 最大許容間隔（時間）
    overlap_tolerance_minutes: int = 15  # 重複許容時間（分）
    description: str = ""
    
    def matches(self, from_code: str, to_code: str) -> bool:
        """指定されたコードの組み合わせがこのルールに合致するかチェック"""
        return from_code in self.from_patterns and to_code in self.to_patterns


@dataclass 
class DynamicContinuousShift:
    """動的連続勤務情報"""
    staff: str
    start_date: str
    end_date: str
    start_pattern: ShiftPattern
    end_pattern: ShiftPattern
    rule: ContinuousShiftRule
    total_duration_hours: float
    overlap_times: List[str] = field(default_factory=list)
    
    def get_overlap_time_slots(self, slot_minutes: int = 15) -> List[str]:
        """重複する時刻スロットを動的に計算"""
        if not self.overlap_times:
            return []
        
        # 重複許容時間を考慮してスロットを計算
        overlap_slots = []
        tolerance_minutes = self.rule.overlap_tolerance_minutes
        
        for overlap_time_str in self.overlap_times:
            overlap_time = dt.datetime.strptime(overlap_time_str, "%H:%M").time()
            
            # 許容時間範囲内のスロットを生成
            base_datetime = dt.datetime.combine(dt.date.today(), overlap_time)
            
            # 前後の許容時間範囲
            start_tolerance = base_datetime - dt.timedelta(minutes=tolerance_minutes)
            end_tolerance = base_datetime + dt.timedelta(minutes=tolerance_minutes)
            
            # スロット生成
            current_time = start_tolerance
            while current_time <= end_tolerance:
                slot_str = current_time.strftime("%H:%M")
                if slot_str not in overlap_slots:
                    overlap_slots.append(slot_str)
                current_time += dt.timedelta(minutes=slot_minutes)
        
        return overlap_slots


class DynamicContinuousShiftDetector:
    """完全に動的な連続勤務検出システム"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.shift_patterns: Dict[str, ShiftPattern] = {}
        self.continuous_shift_rules: List[ContinuousShiftRule] = []
        self.detected_shifts: List[DynamicContinuousShift] = []
        
        # 設定の読み込み
        if config_path and config_path.exists():
            self.load_config(config_path)
        else:
            # デフォルト設定を生成
            self._generate_default_config()
    
    def load_config(self, config_path: Path):
        """設定ファイルから動的に設定を読み込み"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # シフトパターンの読み込み
            for pattern_data in config.get('shift_patterns', []):
                pattern = ShiftPattern(**pattern_data)
                self.shift_patterns[pattern.code] = pattern
            
            # 連続勤務ルールの読み込み
            for rule_data in config.get('continuous_shift_rules', []):
                rule = ContinuousShiftRule(**rule_data)
                self.continuous_shift_rules.append(rule)
            
            log.info(f"設定読み込み完了: {len(self.shift_patterns)}パターン, {len(self.continuous_shift_rules)}ルール")
            
        except Exception as e:
            log.warning(f"設定ファイル読み込みエラー: {e}, デフォルト設定を使用")
            self._generate_default_config()
    
    def _generate_default_config(self):
        """デフォルト設定の生成（後方互換性のため）"""
        # 基本的な日本の医療・介護現場パターン
        default_patterns = [
            ShiftPattern("日", "09:00", "17:00", "日勤", False, 1),
            ShiftPattern("遅", "13:00", "21:00", "遅番", False, 2),
            ShiftPattern("夜", "16:45", "00:00", "夜勤前半", True, 3),
            ShiftPattern("明", "00:00", "10:00", "明け番", True, 4),
            ShiftPattern("早", "07:00", "15:00", "早番", False, 1),
        ]
        
        for pattern in default_patterns:
            self.shift_patterns[pattern.code] = pattern
        
        # デフォルト連続勤務ルール
        default_rules = [
            ContinuousShiftRule(
                name="夜勤→明け番",
                from_patterns=["夜"], 
                to_patterns=["明"],
                max_gap_hours=0.5,
                overlap_tolerance_minutes=30,
                description="典型的な夜勤→明け番パターン"
            ),
        ]
        
        self.continuous_shift_rules = default_rules
        log.info("デフォルト設定を生成しました")
    
    def auto_detect_patterns_from_data(self, long_df: pd.DataFrame, wt_df: pd.DataFrame = None):
        """データから動的にシフトパターンを検出・学習"""
        if long_df.empty:
            return
        
        log.info("データからシフトパターンを自動検出開始")
        
        # 既存パターンと競合しない新しいパターンを検出
        detected_patterns = {}
        
        # wt_dfがある場合は勤務区分定義を優先使用
        if wt_df is not None and not wt_df.empty:
            for _, row in wt_df.iterrows():
                code = row.get('code', '')
                start = row.get('start_parsed', '')
                end = row.get('end_parsed', '')
                remarks = row.get('remarks', '')
                
                if code and start and end:
                    # 日跨ぎ判定
                    try:
                        start_time = dt.datetime.strptime(start, "%H:%M").time()
                        end_time = dt.datetime.strptime(end, "%H:%M").time()
                        is_overnight = end_time <= start_time or end == "00:00"
                        
                        pattern = ShiftPattern(
                            code=code,
                            start_time=start,
                            end_time=end,
                            description=remarks,
                            is_overnight=is_overnight,
                            priority=self._calculate_priority(start_time, end_time, is_overnight)
                        )
                        
                        detected_patterns[code] = pattern
                        log.debug(f"勤務区分から検出: {code} ({start}-{end})")
                        
                    except Exception as e:
                        log.warning(f"勤務区分解析エラー {code}: {e}")
        
        # long_dfから実際の使用パターンを検出
        code_time_pairs = []
        for _, row in long_df.iterrows():
            code = row.get('code', '')
            ds = row.get('ds')
            if code and ds:
                time_obj = pd.to_datetime(ds).time()
                code_time_pairs.append((code, time_obj))
        
        # コードごとの時間範囲を分析
        code_time_ranges = {}
        for code, time_obj in code_time_pairs:
            if code not in code_time_ranges:
                code_time_ranges[code] = {'times': [], 'min_time': None, 'max_time': None}
            
            code_time_ranges[code]['times'].append(time_obj)
        
        # 各コードの時間範囲を計算
        for code, data in code_time_ranges.items():
            if code in detected_patterns:
                continue  # 既に勤務区分で定義済み
            
            times = sorted(data['times'])
            if len(times) < 2:
                continue
            
            min_time = min(times)
            max_time = max(times)
            
            # 日跨ぎ判定（深夜帯と夕方帯が混在する場合）
            morning_times = [t for t in times if t.hour < 12]
            evening_times = [t for t in times if t.hour >= 16]
            is_overnight = len(morning_times) > 0 and len(evening_times) > 0
            
            if is_overnight:
                # 夜勤パターンの場合
                start_time = min(evening_times).strftime("%H:%M")
                end_time = max(morning_times).strftime("%H:%M")
            else:
                start_time = min_time.strftime("%H:%M")
                end_time = max_time.strftime("%H:%M")
            
            pattern = ShiftPattern(
                code=code,
                start_time=start_time,
                end_time=end_time,
                description=f"自動検出パターン ({len(times)}回出現)",
                is_overnight=is_overnight,
                priority=self._calculate_priority(min_time, max_time, is_overnight)
            )
            
            detected_patterns[code] = pattern
            log.info(f"データから自動検出: {code} ({start_time}-{end_time}) {'[日跨ぎ]' if is_overnight else ''}")
        
        # 検出したパターンをマージ
        self.shift_patterns.update(detected_patterns)
        
        # 連続勤務ルールの自動生成
        self._auto_generate_continuous_rules(long_df)
    
    def _calculate_priority(self, start_time: dt.time, end_time: dt.time, is_overnight: bool) -> int:
        """時間帯に基づいて優先度を計算"""
        if is_overnight:
            return 10  # 日跨ぎは高優先度
        elif start_time.hour < 6:
            return 8   # 早朝
        elif start_time.hour >= 22:
            return 7   # 深夜
        elif start_time.hour >= 17:
            return 5   # 夕方
        else:
            return 3   # 日中
    
    def _auto_generate_continuous_rules(self, long_df: pd.DataFrame):
        """実データから連続勤務ルールを自動生成"""
        # 職員ごとの連続するコードパターンを分析
        continuous_patterns = {}
        
        for staff in long_df['staff'].unique():
            staff_data = long_df[long_df['staff'] == staff].copy()
            staff_data['date'] = pd.to_datetime(staff_data['ds']).dt.date
            staff_data = staff_data.sort_values('ds')
            
            # 連続する日付のコード変遷を追跡
            prev_date = None
            prev_codes = set()
            
            for date, group in staff_data.groupby('date'):
                current_codes = set(group['code'].unique())
                
                if prev_date and (date - prev_date).days == 1:
                    # 連続する日付での組み合わせを記録
                    for prev_code in prev_codes:
                        for current_code in current_codes:
                            pattern_key = f"{prev_code}→{current_code}"
                            if pattern_key not in continuous_patterns:
                                continuous_patterns[pattern_key] = 0
                            continuous_patterns[pattern_key] += 1
                
                prev_date = date
                prev_codes = current_codes
        
        # 頻度の高いパターンから連続勤務ルールを生成
        threshold = 2  # 最低2回以上出現したパターンのみ
        for pattern, count in continuous_patterns.items():
            if count >= threshold:
                from_code, to_code = pattern.split('→')
                
                # 既存ルールと重複チェック
                exists = any(
                    rule for rule in self.continuous_shift_rules
                    if from_code in rule.from_patterns and to_code in rule.to_patterns
                )
                
                if not exists:
                    rule = ContinuousShiftRule(
                        name=f"自動検出: {pattern}",
                        from_patterns=[from_code],
                        to_patterns=[to_code],
                        max_gap_hours=2.0,  # 動的に調整可能
                        overlap_tolerance_minutes=30,
                        description=f"データから検出 (出現回数: {count})"
                    )
                    self.continuous_shift_rules.append(rule)
                    log.info(f"連続勤務ルール自動生成: {pattern} (出現{count}回)")
    
    def detect_continuous_shifts(self, long_df: pd.DataFrame, wt_df: pd.DataFrame = None) -> List[DynamicContinuousShift]:
        """動的な連続勤務検出"""
        if long_df.empty:
            return []
        
        # パターンの自動学習
        self.auto_detect_patterns_from_data(long_df, wt_df)
        
        log.info(f"動的連続勤務検出開始: {len(self.shift_patterns)}パターン, {len(self.continuous_shift_rules)}ルール")
        
        continuous_shifts = []
        
        # 職員ごとに処理
        for staff in long_df['staff'].unique():
            staff_data = long_df[long_df['staff'] == staff].copy()
            staff_data['date'] = pd.to_datetime(staff_data['ds']).dt.date
            staff_data['time'] = pd.to_datetime(staff_data['ds']).dt.time
            staff_data = staff_data.sort_values('ds')
            
            # 日別パターン分析
            daily_shifts = self._analyze_daily_shifts(staff_data)
            
            # 連続勤務検出
            staff_continuous = self._detect_staff_continuous_shifts(daily_shifts, staff)
            continuous_shifts.extend(staff_continuous)
        
        self.detected_shifts = continuous_shifts
        log.info(f"動的連続勤務検出完了: {len(continuous_shifts)}件")
        
        return continuous_shifts
    
    def _analyze_daily_shifts(self, staff_data: pd.DataFrame) -> Dict[str, Dict]:
        """職員の日別勤務を分析"""
        daily_shifts = {}
        
        for date, group in staff_data.groupby('date'):
            date_str = date.strftime('%Y-%m-%d')
            codes = group['code'].unique()
            times = [t for t in group['time']]
            
            # この日の勤務パターンを特定
            detected_patterns = []
            for code in codes:
                if code in self.shift_patterns:
                    pattern = self.shift_patterns[code]
                    
                    # 実際の時間がパターンと合致するかチェック
                    matching_times = [
                        t for t in times 
                        if pattern.is_in_timerange(t)
                    ]
                    
                    if matching_times:
                        detected_patterns.append({
                            'pattern': pattern,
                            'matching_times': matching_times,
                            'start_time': min(matching_times),
                            'end_time': max(matching_times)
                        })
            
            # 優先度でソート
            detected_patterns.sort(key=lambda x: x['pattern'].priority, reverse=True)
            
            daily_shifts[date_str] = {
                'date': date,
                'codes': list(codes),
                'times': times,
                'patterns': detected_patterns,
                'primary_pattern': detected_patterns[0] if detected_patterns else None
            }
        
        return daily_shifts
    
    def _detect_staff_continuous_shifts(self, daily_shifts: Dict, staff: str) -> List[DynamicContinuousShift]:
        """職員の連続勤務を検出"""
        continuous_shifts = []
        dates = sorted(daily_shifts.keys())
        
        for i in range(len(dates) - 1):
            current_date = dates[i]
            next_date = dates[i + 1]
            
            current_shift = daily_shifts[current_date]
            next_shift = daily_shifts[next_date]
            
            # 連続する日付かチェック
            if not self._is_consecutive_dates(current_date, next_date):
                continue
            
            # 各ルールとの照合
            for rule in self.continuous_shift_rules:
                continuous_shift = self._check_rule_match(
                    current_shift, next_shift, rule, staff
                )
                if continuous_shift:
                    continuous_shifts.append(continuous_shift)
                    log.debug(f"連続勤務検出: {staff} {current_date}→{next_date} ({rule.name})")
        
        return continuous_shifts
    
    def _check_rule_match(self, current_shift: Dict, next_shift: Dict, 
                         rule: ContinuousShiftRule, staff: str) -> Optional[DynamicContinuousShift]:
        """連続勤務ルールとの照合"""
        current_pattern = current_shift.get('primary_pattern')
        next_pattern = next_shift.get('primary_pattern')
        
        if not current_pattern or not next_pattern:
            return None
        
        current_code = current_pattern['pattern'].code
        next_code = next_pattern['pattern'].code
        
        if not rule.matches(current_code, next_code):
            return None
        
        # 時間的な連続性をチェック
        current_end = current_pattern['end_time']
        next_start = next_pattern['start_time']
        
        # 日跨ぎを考慮した時間差計算
        if current_pattern['pattern'].is_overnight and next_pattern['pattern'].is_overnight:
            # 両方日跨ぎの場合は特別処理
            gap_hours = self._calculate_overnight_gap(current_end, next_start)
        else:
            # 通常の時間差計算
            gap_hours = self._calculate_time_gap(current_end, next_start)
        
        if gap_hours > rule.max_gap_hours:
            return None
        
        # 重複時間の計算
        overlap_times = self._calculate_overlap_times(
            current_pattern['pattern'], next_pattern['pattern'], rule
        )
        
        # 総勤務時間の計算
        total_duration = self._calculate_total_duration(
            current_shift['date'], current_pattern,
            next_shift['date'], next_pattern
        )
        
        return DynamicContinuousShift(
            staff=staff,
            start_date=current_shift['date'].strftime('%Y-%m-%d'),
            end_date=next_shift['date'].strftime('%Y-%m-%d'),
            start_pattern=current_pattern['pattern'],
            end_pattern=next_pattern['pattern'],
            rule=rule,
            total_duration_hours=total_duration,
            overlap_times=overlap_times
        )
    
    def _calculate_overlap_times(self, pattern1: ShiftPattern, pattern2: ShiftPattern,
                               rule: ContinuousShiftRule) -> List[str]:
        """重複時間を動的に計算"""
        overlap_times = []
        
        if pattern1.is_overnight and pattern2.is_overnight:
            # 両方が日跨ぎの場合
            end1 = pattern1.end_time_obj
            start2 = pattern2.start_time_obj
            
            # 重複する可能性のある時間範囲を特定
            if end1 == start2:
                overlap_times.append(pattern1.end_time)
            elif abs((dt.datetime.combine(dt.date.today(), end1) - 
                     dt.datetime.combine(dt.date.today(), start2)).total_seconds()) <= rule.overlap_tolerance_minutes * 60:
                # 許容範囲内の場合は両方の時刻を重複対象とする
                overlap_times.extend([pattern1.end_time, pattern2.start_time])
        
        return overlap_times
    
    def _calculate_overnight_gap(self, end_time: dt.time, start_time: dt.time) -> float:
        """日跨ぎを考慮した時間差計算"""
        end_dt = dt.datetime.combine(dt.date.today(), end_time)
        start_dt = dt.datetime.combine(dt.date.today() + dt.timedelta(days=1), start_time)
        gap = start_dt - end_dt
        return abs(gap.total_seconds()) / 3600
    
    def _calculate_time_gap(self, end_time: dt.time, start_time: dt.time) -> float:
        """通常の時間差計算"""
        end_dt = dt.datetime.combine(dt.date.today(), end_time)
        start_dt = dt.datetime.combine(dt.date.today(), start_time)
        if start_dt < end_dt:
            start_dt += dt.timedelta(days=1)
        gap = start_dt - end_dt
        return gap.total_seconds() / 3600
    
    def _calculate_total_duration(self, start_date: dt.date, start_pattern: Dict,
                                end_date: dt.date, end_pattern: Dict) -> float:
        """総勤務時間の計算"""
        start_dt = dt.datetime.combine(start_date, start_pattern['start_time'])
        end_dt = dt.datetime.combine(end_date, end_pattern['end_time'])
        
        if end_dt < start_dt:
            end_dt += dt.timedelta(days=1)
        
        duration = end_dt - start_dt
        return duration.total_seconds() / 3600
    
    def _is_consecutive_dates(self, date1: str, date2: str) -> bool:
        """連続する日付かチェック"""
        try:
            d1 = dt.datetime.strptime(date1, '%Y-%m-%d').date()
            d2 = dt.datetime.strptime(date2, '%Y-%m-%d').date()
            return (d2 - d1).days == 1
        except:
            return False
    
    def get_dynamic_duplicate_time_slots(self, target_date: str, slot_minutes: int = 15) -> Set[Tuple[str, str]]:
        """動的重複時刻スロットの取得"""
        duplicates = set()
        
        for shift in self.detected_shifts:
            if shift.end_date == target_date:
                overlap_slots = shift.get_overlap_time_slots(slot_minutes)
                for time_slot in overlap_slots:
                    duplicates.add((shift.staff, time_slot))
        
        return duplicates
    
    def should_adjust_need_dynamic(self, time_slot: str, date: str) -> Tuple[bool, int, str]:
        """動的Need値調整判定"""
        continuing_staff = set()
        applicable_rules = []
        
        for shift in self.detected_shifts:
            if shift.end_date == date:
                overlap_slots = shift.get_overlap_time_slots()
                if time_slot in overlap_slots:
                    continuing_staff.add(shift.staff)
                    applicable_rules.append(shift.rule.name)
        
        rule_summary = ", ".join(set(applicable_rules)) if applicable_rules else "なし"
        
        return len(continuing_staff) > 0, len(continuing_staff), rule_summary
    
    def export_config(self, config_path: Path):
        """現在の設定をファイルに出力"""
        config = {
            "shift_patterns": [
                {
                    "code": pattern.code,
                    "start_time": pattern.start_time,
                    "end_time": pattern.end_time,
                    "description": pattern.description,
                    "is_overnight": pattern.is_overnight,
                    "priority": pattern.priority
                }
                for pattern in self.shift_patterns.values()
            ],
            "continuous_shift_rules": [
                {
                    "name": rule.name,
                    "from_patterns": rule.from_patterns,
                    "to_patterns": rule.to_patterns,
                    "max_gap_hours": rule.max_gap_hours,
                    "overlap_tolerance_minutes": rule.overlap_tolerance_minutes,
                    "description": rule.description
                }
                for rule in self.continuous_shift_rules
            ]
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        log.info(f"設定ファイル出力: {config_path}")
    
    def get_detection_summary(self) -> Dict[str, Any]:
        """検出結果のサマリー"""
        if not self.detected_shifts:
            return {"total_count": 0}
        
        total_count = len(self.detected_shifts)
        avg_duration = sum(s.total_duration_hours for s in self.detected_shifts) / total_count
        
        # ルール別統計
        rule_stats = {}
        for shift in self.detected_shifts:
            rule_name = shift.rule.name
            if rule_name not in rule_stats:
                rule_stats[rule_name] = 0
            rule_stats[rule_name] += 1
        
        # パターン別統計
        pattern_stats = {}
        for shift in self.detected_shifts:
            pattern_key = f"{shift.start_pattern.code}→{shift.end_pattern.code}"
            if pattern_key not in pattern_stats:
                pattern_stats[pattern_key] = 0
            pattern_stats[pattern_key] += 1
        
        return {
            "total_count": total_count,
            "average_duration_hours": round(avg_duration, 2),
            "detected_patterns": len(self.shift_patterns),
            "active_rules": len(self.continuous_shift_rules),
            "rule_statistics": rule_stats,
            "pattern_statistics": pattern_stats,
            "max_duration_hours": round(max(s.total_duration_hours for s in self.detected_shifts), 2)
        }