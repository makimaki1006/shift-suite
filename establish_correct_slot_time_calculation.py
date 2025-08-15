#!/usr/bin/env python3
"""
正確なスロット時間計算の確立
Step 2: 24時間48スロット構造に基づく時間計算システム
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import time, datetime
import json

def establish_correct_slot_time_calculation():
    """正確なスロット時間計算システムの確立"""
    
    print('=' * 80)
    print('Step 2: 正確なスロット時間計算の確立')
    print('目的: 24時間48スロット構造に基づく統一的時間計算システム')
    print('=' * 80)
    
    scenario_dir = Path('extracted_results/out_p25_based')
    
    try:
        # 1. 補完後データの読み込みと検証
        print('\n【Phase 1: 補完後データの読み込み】')
        data = pd.read_parquet(scenario_dir / 'intermediate_data.parquet')
        data_verification = verify_24_slot_structure(data)
        print_data_verification(data_verification)
        
        if not data_verification['valid']:
            print('[ERROR] 24スロット構造が確立されていません')
            return {'success': False}
        
        # 2. 標準スロット時間の計算
        print('\n【Phase 2: 標準スロット時間の計算】')
        standard_slot_calculation = calculate_standard_slot_time()
        print_standard_calculation(standard_slot_calculation)
        
        # 3. 実データでの時間計算検証
        print('\n【Phase 3: 実データでの時間計算検証】')
        actual_calculation = verify_with_actual_data(data, standard_slot_calculation)
        print_actual_calculation_verification(actual_calculation)
        
        # 4. 営業時間 vs 全時間の区別
        print('\n【Phase 4: 営業時間と全時間の区別】')
        time_classification = classify_operating_vs_full_time(data)
        print_time_classification(time_classification)
        
        # 5. 統一時間計算システムの構築
        print('\n【Phase 5: 統一時間計算システム構築】')
        unified_system = build_unified_time_calculation_system(
            standard_slot_calculation, 
            actual_calculation, 
            time_classification
        )
        print_unified_system(unified_system)
        
        # 6. 時間計算関数の定義と保存
        print('\n【Phase 6: 時間計算関数の定義】')
        save_time_calculation_functions(unified_system)
        
        # 7. 計算システム検証
        print('\n【Phase 7: システム検証】')
        system_verification = verify_calculation_system(data, unified_system)
        print_system_verification(system_verification)
        
        return {
            'success': True,
            'standard_calculation': standard_slot_calculation,
            'actual_verification': actual_calculation,
            'time_classification': time_classification,
            'unified_system': unified_system,
            'verification': system_verification
        }
        
    except Exception as e:
        print(f'[ERROR] 時間計算システム確立に失敗: {e}')
        return {'success': False, 'error': str(e)}

def verify_24_slot_structure(data):
    """24スロット構造の検証"""
    
    unique_times = data['ds'].dt.time.unique()
    unique_count = len(unique_times)
    
    # 24時間完全スロットの期待値
    expected_slots = []
    for hour in range(24):
        for minute in [0, 30]:
            expected_slots.append(time(hour, minute))
    
    expected_set = set(expected_slots)
    actual_set = set(unique_times)
    
    return {
        'valid': unique_count == 48 and expected_set == actual_set,
        'actual_slot_count': unique_count,
        'expected_slot_count': 48,
        'missing_slots': list(expected_set - actual_set),
        'extra_slots': list(actual_set - expected_set)
    }

def print_data_verification(verification):
    """データ検証結果の表示"""
    
    status = "[OK] 合格" if verification['valid'] else "[ERROR] 不合格"
    print(f'24スロット構造検証: {status}')
    print(f'  実際のスロット数: {verification["actual_slot_count"]}個')
    print(f'  期待スロット数: {verification["expected_slot_count"]}個')
    
    if verification['missing_slots']:
        print(f'  欠落スロット: {len(verification["missing_slots"])}個')
    
    if verification['extra_slots']:
        print(f'  余分なスロット: {len(verification["extra_slots"])}個')

def calculate_standard_slot_time():
    """標準スロット時間の計算"""
    
    # 24時間48スロット標準計算
    total_hours_per_day = 24.0
    total_slots_per_day = 48
    standard_slot_hours = total_hours_per_day / total_slots_per_day
    standard_slot_minutes = standard_slot_hours * 60
    
    return {
        'standard_slot_hours': standard_slot_hours,
        'standard_slot_minutes': standard_slot_minutes,
        'total_slots_per_day': total_slots_per_day,
        'total_hours_per_day': total_hours_per_day,
        'calculation_basis': '24時間÷48スロット=0.5時間/スロット'
    }

def print_standard_calculation(calculation):
    """標準計算の表示"""
    
    print(f'標準スロット時間: {calculation["standard_slot_hours"]:.3f}時間/スロット')
    print(f'標準スロット時間: {calculation["standard_slot_minutes"]:.0f}分/スロット')
    print(f'1日スロット数: {calculation["total_slots_per_day"]}個')
    print(f'計算根拠: {calculation["calculation_basis"]}')

def verify_with_actual_data(data, standard_calculation):
    """実データでの検証"""
    
    # 営業時間スロット（NIGHT_SLOTでない）の特定
    operating_data = data[data['role'] != 'NIGHT_SLOT']
    night_data = data[data['role'] == 'NIGHT_SLOT']
    
    # 実際の営業スロット時間
    operating_times = set(operating_data['ds'].dt.time.unique())
    operating_slot_count = len(operating_times)
    
    # 営業時間の範囲計算
    if operating_times:
        min_time = min(operating_times)
        max_time = max(operating_times)
        
        # 営業時間計算（分単位）
        min_minutes = min_time.hour * 60 + min_time.minute
        max_minutes = max_time.hour * 60 + max_time.minute
        operating_minutes = max_minutes - min_minutes + 30  # 最後のスロット30分含む
        operating_hours = operating_minutes / 60
        
        actual_slot_hours = operating_hours / operating_slot_count if operating_slot_count > 0 else 0
    else:
        operating_hours = 0
        actual_slot_hours = 0
    
    return {
        'operating_slot_count': operating_slot_count,
        'night_slot_count': len(set(night_data['ds'].dt.time.unique())) if len(night_data) > 0 else 0,
        'operating_hours_per_day': operating_hours,
        'actual_operating_slot_hours': actual_slot_hours,
        'standard_slot_hours': standard_calculation['standard_slot_hours'],
        'time_calculation_method': 'operating' if operating_slot_count != 48 else 'standard'
    }

def print_actual_calculation_verification(verification):
    """実データ検証結果の表示"""
    
    print(f'営業スロット数: {verification["operating_slot_count"]}個')
    print(f'夜間スロット数: {verification["night_slot_count"]}個')
    print(f'営業時間: {verification["operating_hours_per_day"]:.1f}時間/日')
    print(f'営業ベーススロット時間: {verification["actual_operating_slot_hours"]:.3f}時間/スロット')
    print(f'標準スロット時間: {verification["standard_slot_hours"]:.3f}時間/スロット')
    print(f'推奨計算方法: {verification["time_calculation_method"]}')

def classify_operating_vs_full_time(data):
    """営業時間と全時間の分類"""
    
    # 営業時間の特定（NIGHT_SLOTでない）
    operating_data = data[data['role'] != 'NIGHT_SLOT']
    night_data = data[data['role'] == 'NIGHT_SLOT']
    
    total_records = len(data)
    operating_records = len(operating_data)
    night_records = len(night_data)
    
    # 分類結果
    classification = {
        'total_records': total_records,
        'operating_records': operating_records,
        'night_records': night_records,
        'operating_ratio': operating_records / total_records if total_records > 0 else 0,
        'night_ratio': night_records / total_records if total_records > 0 else 0,
        'has_night_operations': night_records > 0 and any(
            data[data['role'] != 'NIGHT_SLOT']['role'].notna()  # 実際の夜勤があるか
        ),
        'pure_day_operation': night_records > 0 and all(
            data[data['role'] == 'NIGHT_SLOT']['staff'] == 'NIGHT_SLOT_PLACEHOLDER'
        )
    }
    
    return classification

def print_time_classification(classification):
    """時間分類結果の表示"""
    
    print(f'全レコード数: {classification["total_records"]}')
    print(f'営業時間レコード数: {classification["operating_records"]} ({classification["operating_ratio"]:.1%})')
    print(f'夜間時間レコード数: {classification["night_records"]} ({classification["night_ratio"]:.1%})')
    print(f'夜間営業: {"あり" if classification["has_night_operations"] else "なし"}')
    print(f'日勤のみ運営: {"はい" if classification["pure_day_operation"] else "いいえ"}')

def build_unified_time_calculation_system(standard_calc, actual_calc, time_class):
    """統一時間計算システムの構築"""
    
    # 計算方針の決定
    if time_class['pure_day_operation']:
        # 日勤のみの場合は標準24時間ベースを使用
        recommended_slot_hours = standard_calc['standard_slot_hours']
        calculation_approach = 'STANDARD_24H'
        rationale = '夜間営業なしのため標準24時間48スロット計算を採用'
    else:
        # 夜間営業がある場合は実営業時間ベース
        recommended_slot_hours = actual_calc['actual_operating_slot_hours']
        calculation_approach = 'ACTUAL_OPERATING'
        rationale = '夜間営業ありのため実営業時間ベース計算を採用'
    
    # 統一システム定義
    unified_system = {
        'slot_hours': recommended_slot_hours,
        'slot_minutes': recommended_slot_hours * 60,
        'calculation_approach': calculation_approach,
        'rationale': rationale,
        'parameters': {
            'total_slots_per_day': 48,
            'operating_slots_per_day': actual_calc['operating_slot_count'],
            'night_slots_per_day': actual_calc['night_slot_count']
        },
        'formulas': {
            'record_to_hours': f'{recommended_slot_hours:.6f} * record_count',
            'daily_hours': f'total_hours / period_days',
            'monthly_hours': f'daily_hours * 30'
        }
    }
    
    return unified_system

def print_unified_system(system):
    """統一システムの表示"""
    
    print(f'採用スロット時間: {system["slot_hours"]:.6f}時間/スロット ({system["slot_minutes"]:.1f}分)')
    print(f'計算アプローチ: {system["calculation_approach"]}')
    print(f'採用理由: {system["rationale"]}')
    
    print('\n時間計算式:')
    for formula_name, formula in system['formulas'].items():
        print(f'  {formula_name}: {formula}')

def save_time_calculation_functions(system):
    """時間計算関数の保存"""
    
    function_code = f'''# 統一時間計算システム
# 自動生成: {datetime.now().isoformat()}

# システム定数
UNIFIED_SLOT_HOURS = {system['slot_hours']:.6f}
CALCULATION_APPROACH = '{system['calculation_approach']}'

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
SYSTEM_INFO = {system}
'''
    
    with open('unified_time_calculation_system.py', 'w', encoding='utf-8') as f:
        f.write(function_code)
    
    print('統一時間計算関数を保存: unified_time_calculation_system.py')

def verify_calculation_system(data, system):
    """計算システムの検証"""
    
    # テストデータでの検証
    test_records = len(data[data['role'] != 'NIGHT_SLOT'])  # 営業時間のレコード
    period_days = data['ds'].dt.date.nunique()
    
    # 新システムでの計算
    total_hours = test_records * system['slot_hours']
    daily_hours = total_hours / period_days
    monthly_hours = daily_hours * 30
    
    # 従来システムでの計算（比較用）
    old_total_hours = test_records * 0.52  # 従来の固定値
    old_daily_hours = old_total_hours / period_days
    
    verification = {
        'test_records': test_records,
        'period_days': period_days,
        'new_system': {
            'total_hours': total_hours,
            'daily_hours': daily_hours,
            'monthly_hours': monthly_hours
        },
        'old_system': {
            'total_hours': old_total_hours,
            'daily_hours': old_daily_hours
        },
        'improvement': {
            'ratio': total_hours / old_total_hours if old_total_hours > 0 else 1,
            'daily_difference': daily_hours - old_daily_hours
        },
        'reasonableness_check': {
            'daily_hours_reasonable': 50 <= daily_hours <= 200,  # 1日50-200時間は合理的範囲
            'monthly_hours_reasonable': 1500 <= monthly_hours <= 6000  # 月1500-6000時間は合理的範囲
        }
    }
    
    return verification

def print_system_verification(verification):
    """システム検証結果の表示"""
    
    print(f'検証対象レコード: {verification["test_records"]}件 ({verification["period_days"]}日間)')
    
    print('\n新システム計算結果:')
    new = verification['new_system']
    print(f'  総時間: {new["total_hours"]:.1f}時間')
    print(f'  日平均: {new["daily_hours"]:.1f}時間/日')
    print(f'  月間換算: {new["monthly_hours"]:.1f}時間/月')
    
    print('\n従来システム比較:')
    old = verification['old_system']
    imp = verification['improvement']
    print(f'  従来計算: {old["total_hours"]:.1f}時間 → {old["daily_hours"]:.1f}時間/日')
    print(f'  改善比率: {imp["ratio"]:.2f}倍')
    print(f'  日次差分: {imp["daily_difference"]:+.1f}時間/日')
    
    print('\n合理性チェック:')
    reasonable = verification['reasonableness_check']
    print(f'  日次時間: {"[OK] 合理的" if reasonable["daily_hours_reasonable"] else "[WARNING] 要確認"}')
    print(f'  月次時間: {"[OK] 合理的" if reasonable["monthly_hours_reasonable"] else "[WARNING] 要確認"}')

if __name__ == "__main__":
    result = establish_correct_slot_time_calculation()
    
    if result and result.get('success', False):
        print('\n' + '=' * 80)
        print('Step 2完了: 正確なスロット時間計算システム確立')
        print('Step 3: Needファイルとの整合性確認に進行可能')
        print('=' * 80)
    else:
        print('\nStep 2失敗: 問題を修正してから再実行してください')