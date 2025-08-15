# 統一時間計算システム
# 自動生成: 2025-08-07T15:25:08.941144

# システム定数
UNIFIED_SLOT_HOURS = 0.500000
CALCULATION_APPROACH = 'STANDARD_24H'

def records_to_hours(record_count):
    """レコード数から時間への変換"""
    return record_count * UNIFIED_SLOT_HOURS

def records_to_daily_hours(record_count, period_days):
    """レコード数から日平均時間への変換"""
    total_hours = records_to_hours(record_count)
    return total_hours / period_days

def records_to_monthly_hours(record_count, period_days):
    """レコード数から月間時間への変換（30日基準）"""
    daily_hours = records_to_daily_hours(record_count, period_days)
    return daily_hours * 30

# システム情報
SYSTEM_INFO = {'slot_hours': 0.5, 'slot_minutes': 30.0, 'calculation_approach': 'STANDARD_24H', 'rationale': '夜間営業なしのため標準24時間48スロット計算を採用', 'parameters': {'total_slots_per_day': 48, 'operating_slots_per_day': 21, 'night_slots_per_day': 27}, 'formulas': {'record_to_hours': '0.500000 * record_count', 'daily_hours': 'total_hours / period_days', 'monthly_hours': 'daily_hours * 30'}}
