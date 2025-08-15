#!/usr/bin/env python3
"""
時間軸ベース分析ロジックの設計
按分計算に代わる真の分析手法
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, time, timedelta
from collections import defaultdict

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class TimeAxisAnalyzer:
    """
    時間軸ベース分析クラス
    30分スロット単位での真の過不足分析
    """
    
    def __init__(self, slot_minutes: int = 30):
        self.slot_minutes = slot_minutes
        self.slots_per_day = 24 * 60 // slot_minutes  # 48スロット/日
        
    def generate_time_slots(self) -> List[str]:
        """24時間の30分スロットを生成"""
        slots = []
        current_time = time(0, 0)
        
        for i in range(self.slots_per_day):
            slots.append(current_time.strftime("%H:%M"))
            # 30分追加
            minutes = current_time.minute + self.slot_minutes
            hours = current_time.hour
            if minutes >= 60:
                minutes -= 60
                hours += 1
                if hours >= 24:
                    hours = 0
            current_time = time(hours, minutes)
        
        return slots
    
    def analyze_role_working_patterns(self, shift_records: pd.DataFrame) -> Dict:
        """
        職種別の実勤務パターン分析
        
        Args:
            shift_records: ingest_excelで生成されたレコード
            
        Returns:
            職種別勤務パターン分析結果
        """
        
        # 勤務レコードのみ抽出（休暇を除外）
        work_records = shift_records[shift_records['parsed_slots_count'] > 0].copy()
        
        analysis_result = {
            'role_patterns': {},
            'time_slot_analysis': {},
            'peak_hours': {},
            'coverage_gaps': {}
        }
        
        # 時間スロット生成
        time_slots = self.generate_time_slots()
        
        # 職種別分析
        for role in work_records['role'].unique():
            if not role or role == '':
                continue
                
            role_data = work_records[work_records['role'] == role]
            
            # 職種別時間帯分析
            role_time_distribution = defaultdict(int)
            
            for _, record in role_data.iterrows():
                # datetime から時刻スロットを抽出
                record_time = record['ds'].strftime("%H:%M")
                role_time_distribution[record_time] += 1
            
            # ピーク時間帯の特定
            sorted_times = sorted(role_time_distribution.items(), 
                                key=lambda x: x[1], reverse=True)
            
            peak_times = sorted_times[:5] if len(sorted_times) >= 5 else sorted_times
            
            analysis_result['role_patterns'][role] = {
                'total_work_slots': len(role_data),
                'unique_staff': role_data['staff'].nunique(),
                'time_distribution': dict(role_time_distribution),
                'peak_times': peak_times,
                'coverage_span': f"{min(role_time_distribution.keys())} - {max(role_time_distribution.keys())}" if role_time_distribution else "No data"
            }
        
        # 全体的な時間帯分析
        overall_time_distribution = defaultdict(int)
        for _, record in work_records.iterrows():
            record_time = record['ds'].strftime("%H:%M")
            overall_time_distribution[record_time] += 1
        
        analysis_result['time_slot_analysis'] = {
            'total_slots_covered': len(overall_time_distribution),
            'total_work_records': len(work_records),
            'busiest_slots': sorted(overall_time_distribution.items(), 
                                  key=lambda x: x[1], reverse=True)[:10],
            'quietest_slots': sorted([item for item in overall_time_distribution.items() if item[1] > 0], 
                                   key=lambda x: x[1])[:5]
        }
        
        # カバレッジギャップ特定
        all_possible_slots = set(time_slots)
        covered_slots = set(overall_time_distribution.keys())
        uncovered_slots = all_possible_slots - covered_slots
        
        analysis_result['coverage_gaps'] = {
            'total_possible_slots': len(all_possible_slots),
            'covered_slots': len(covered_slots),
            'uncovered_slots': len(uncovered_slots),
            'gap_times': sorted(list(uncovered_slots)),
            'coverage_ratio': len(covered_slots) / len(all_possible_slots)
        }
        
        return analysis_result
    
    def calculate_true_shortage_by_timeslot(
        self, 
        need_data: Dict[str, Dict[str, float]], 
        supply_data: Dict[str, Dict[str, float]]
    ) -> Dict:
        """
        時間スロット別の真の過不足計算
        
        Args:
            need_data: {date: {timeslot: need_hours}}
            supply_data: {date: {timeslot: supply_hours}}
            
        Returns:
            時間スロット別過不足分析結果
        """
        
        timeslot_analysis = {
            'daily_analysis': {},
            'slot_patterns': defaultdict(list),
            'shortage_summary': {},
            'critical_periods': []
        }
        
        total_shortage_hours = 0
        total_excess_hours = 0
        
        # 日別分析
        all_dates = set(need_data.keys()) | set(supply_data.keys())
        
        for date in all_dates:
            date_need = need_data.get(date, {})
            date_supply = supply_data.get(date, {})
            
            date_analysis = {
                'total_need': sum(date_need.values()),
                'total_supply': sum(date_supply.values()),
                'slot_details': {},
                'shortage_hours': 0,
                'excess_hours': 0
            }
            
            # スロット別詳細分析
            all_slots = set(date_need.keys()) | set(date_supply.keys())
            
            for slot in all_slots:
                need_hours = date_need.get(slot, 0)
                supply_hours = date_supply.get(slot, 0)
                difference = supply_hours - need_hours
                
                slot_detail = {
                    'need': need_hours,
                    'supply': supply_hours,
                    'difference': difference,
                    'status': 'shortage' if difference < 0 else 'excess' if difference > 0 else 'balanced'
                }
                
                date_analysis['slot_details'][slot] = slot_detail
                
                # パターン蓄積（時間帯別分析用）
                timeslot_analysis['slot_patterns'][slot].append({
                    'date': date,
                    'difference': difference,
                    'shortage_hours': abs(difference) if difference < 0 else 0,
                    'excess_hours': difference if difference > 0 else 0
                })
                
                # 累計計算
                if difference < 0:
                    date_analysis['shortage_hours'] += abs(difference)
                    total_shortage_hours += abs(difference)
                elif difference > 0:
                    date_analysis['excess_hours'] += difference
                    total_excess_hours += difference
            
            timeslot_analysis['daily_analysis'][date] = date_analysis
        
        # 時間スロット別パターン分析
        slot_summary = {}
        for slot, records in timeslot_analysis['slot_patterns'].items():
            total_shortage = sum(r['shortage_hours'] for r in records)
            total_excess = sum(r['excess_hours'] for r in records)
            avg_difference = np.mean([r['difference'] for r in records])
            
            slot_summary[slot] = {
                'total_shortage_hours': total_shortage,
                'total_excess_hours': total_excess,
                'net_difference': total_excess - total_shortage,
                'average_difference': avg_difference,
                'critical_level': self._assess_criticality(total_shortage, len(records))
            }
        
        # 重要な不足時間帯特定
        critical_slots = sorted(
            [(slot, data['total_shortage_hours']) for slot, data in slot_summary.items()],
            key=lambda x: x[1], reverse=True
        )[:10]
        
        timeslot_analysis['shortage_summary'] = {
            'total_shortage_hours': total_shortage_hours,
            'total_excess_hours': total_excess_hours,
            'net_shortage': total_shortage_hours - total_excess_hours,
            'most_critical_slots': critical_slots,
            'slot_summary': slot_summary
        }
        
        timeslot_analysis['critical_periods'] = [
            slot for slot, shortage in critical_slots if shortage > 0
        ]
        
        return timeslot_analysis
    
    def _assess_criticality(self, shortage_hours: float, num_days: int) -> str:
        """不足時間の重要度評価"""
        if num_days == 0:
            return "no_data"
        
        avg_shortage_per_day = shortage_hours / num_days
        
        if avg_shortage_per_day >= 4:  # 1日平均4時間以上不足
            return "critical"
        elif avg_shortage_per_day >= 2:  # 1日平均2時間以上不足
            return "high"
        elif avg_shortage_per_day >= 0.5:  # 1日平均30分以上不足
            return "medium"
        else:
            return "low"

def demonstrate_time_axis_analysis():
    """時間軸ベース分析のデモンストレーション"""
    
    print("=== 時間軸ベース分析デモンストレーション ===")
    
    try:
        # ingest_excelでレコード生成
        from shift_suite.tasks.io_excel import ingest_excel
        
        test_file = project_root / "デイ_テスト用データ_休日精緻.xlsx"
        long_df, wt_df, unknown_codes = ingest_excel(
            excel_path=test_file,
            shift_sheets=["R7.2"],
            header_row=0,
            slot_minutes=30
        )
        
        print(f"生成されたレコード数: {len(long_df)}")
        
        # 時間軸分析器初期化
        analyzer = TimeAxisAnalyzer()
        
        # 職種別勤務パターン分析
        pattern_analysis = analyzer.analyze_role_working_patterns(long_df)
        
        print(f"\n=== 職種別勤務パターン分析結果 ===")
        print(f"分析対象職種数: {len(pattern_analysis['role_patterns'])}")
        
        for role, data in list(pattern_analysis['role_patterns'].items())[:3]:
            print(f"\n職種: {role}")
            print(f"  総勤務スロット数: {data['total_work_slots']}")
            print(f"  職員数: {data['unique_staff']}")
            print(f"  カバー時間帯: {data['coverage_span']}")
            print(f"  ピーク時間帯:")
            for time_slot, count in data['peak_times'][:3]:
                print(f"    {time_slot}: {count}件")
        
        print(f"\n=== 全体時間帯分析 ===")
        time_analysis = pattern_analysis['time_slot_analysis']
        print(f"カバー済みスロット数: {time_analysis['total_slots_covered']}/48")
        print(f"最も忙しい時間帯:")
        for time_slot, count in time_analysis['busiest_slots'][:5]:
            print(f"  {time_slot}: {count}件")
        
        print(f"\n=== カバレッジギャップ ===")
        gap_analysis = pattern_analysis['coverage_gaps']
        print(f"カバー率: {gap_analysis['coverage_ratio']:.1%}")
        print(f"未カバー時間帯数: {gap_analysis['uncovered_slots']}")
        if gap_analysis['gap_times']:
            print(f"未カバー時間帯例: {gap_analysis['gap_times'][:5]}")
        
        return pattern_analysis
        
    except Exception as e:
        print(f"分析エラー: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = demonstrate_time_axis_analysis()