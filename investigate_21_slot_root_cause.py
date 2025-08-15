#!/usr/bin/env python3
"""
21スロット問題の根本原因調査
なぜ24スロットではなく21スロットなのかを徹底解明
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import time, datetime, timedelta

def investigate_21_slot_mystery():
    """21スロット問題の根本原因調査"""
    
    print('=' * 80)
    print('21スロット問題 根本原因調査')
    print('ユーザー指摘: 24スロット（夜間=0）であるべきが21スロット')
    print('=' * 80)
    
    scenario_dir = Path('extracted_results/out_p25_based')
    
    # 1. intermediate_dataの時間構造詳細調査
    print('\n【調査1: intermediate_dataの時間構造】')
    
    try:
        data = pd.read_parquet(scenario_dir / 'intermediate_data.parquet')
        
        # 時刻の詳細分析
        time_analysis = analyze_time_structure(data)
        print_time_analysis(time_analysis)
        
        # 2. Needファイルの時間構造調査
        print('\n【調査2: Needファイルの時間構造】')
        need_analysis = analyze_need_file_structure(scenario_dir)
        print_need_analysis(need_analysis)
        
        # 3. 構造不整合の検証
        print('\n【調査3: 構造不整合の検証】')
        inconsistency_analysis = verify_structure_inconsistency(time_analysis, need_analysis)
        print_inconsistency_analysis(inconsistency_analysis)
        
        # 4. 実配置時間の正確な再計算
        print('\n【調査4: 実配置時間の正確な再計算】')
        correct_time_calculation = recalculate_actual_time_correctly(data, time_analysis)
        print_correct_time_calculation(correct_time_calculation)
        
        # 5. 根本原因の特定と対策
        print('\n【調査5: 根本原因特定と対策】')
        root_cause_analysis = identify_root_cause_and_solution(
            time_analysis, need_analysis, inconsistency_analysis, correct_time_calculation
        )
        print_root_cause_analysis(root_cause_analysis)
        
        return {
            'time_analysis': time_analysis,
            'need_analysis': need_analysis,
            'inconsistency_analysis': inconsistency_analysis,
            'correct_time_calculation': correct_time_calculation,
            'root_cause_analysis': root_cause_analysis
        }
        
    except Exception as e:
        print(f'[ERROR] 調査失敗: {e}')
        return None

def analyze_time_structure(data):
    """intermediate_dataの時間構造分析"""
    
    unique_times = sorted(data['ds'].dt.time.unique())
    
    # 時間スロットの詳細
    time_slots = []
    for t in unique_times:
        time_slots.append({
            'time': t,
            'hour': t.hour,
            'minute': t.minute,
            'total_minutes': t.hour * 60 + t.minute
        })
    
    # 欠落時間帯の特定
    all_possible_30min_slots = []
    for hour in range(24):
        for minute in [0, 30]:
            all_possible_30min_slots.append(time(hour, minute))
    
    existing_times_set = set(unique_times)
    missing_times = [t for t in all_possible_30min_slots if t not in existing_times_set]
    
    # 夜間時間帯の分析
    night_times = [t for t in unique_times if t.hour >= 18 or t.hour < 6]
    missing_night_times = [t for t in missing_times if t.hour >= 18 or t.hour < 6]
    
    return {
        'total_slots': len(unique_times),
        'unique_times': unique_times,
        'time_slots': time_slots,
        'missing_times': missing_times,
        'missing_count': len(missing_times),
        'night_slots_existing': len(night_times),
        'night_slots_missing': len(missing_night_times),
        'coverage_ratio': len(unique_times) / 48,  # 48 = 24時間 × 2スロット/時間
        'first_time': min(unique_times),
        'last_time': max(unique_times)
    }

def print_time_analysis(analysis):
    """時間分析結果の表示"""
    print(f'実際のスロット数: {analysis["total_slots"]}個')
    print(f'期待されるスロット数: 48個（24時間×30分間隔）')
    print(f'欠落スロット数: {analysis["missing_count"]}個')
    print(f'時間カバレッジ: {analysis["coverage_ratio"]:.1%}')
    print(f'時間範囲: {analysis["first_time"]} - {analysis["last_time"]}')
    print(f'夜間スロット: 既存{analysis["night_slots_existing"]}個, 欠落{analysis["night_slots_missing"]}個')
    
    # 欠落時間帯の詳細表示
    if analysis["missing_times"]:
        print(f'\n欠落時間帯（最初の10個）:')
        for t in analysis["missing_times"][:10]:
            print(f'  {t}')
        if len(analysis["missing_times"]) > 10:
            print(f'  ... 他{len(analysis["missing_times"]) - 10}個')

def analyze_need_file_structure(scenario_dir):
    """Needファイルの構造分析"""
    
    need_files = list(scenario_dir.glob('need_per_date_slot_role_*.parquet'))
    
    if not need_files:
        return {'error': 'Needファイルが見つかりません'}
    
    # サンプルファイルで構造確認
    sample_file = need_files[0]
    sample_df = pd.read_parquet(sample_file)
    
    return {
        'need_file_count': len(need_files),
        'sample_file': sample_file.name,
        'sample_shape': sample_df.shape,
        'rows_slots': sample_df.shape[0],  # 行数 = スロット数
        'cols_days': sample_df.shape[1],   # 列数 = 日数
        'expected_slots': 48,
        'slot_mismatch': sample_df.shape[0] != 48
    }

def print_need_analysis(analysis):
    """Need分析結果の表示"""
    if 'error' in analysis:
        print(f'[ERROR] {analysis["error"]}')
        return
    
    print(f'Needファイル数: {analysis["need_file_count"]}個')
    print(f'サンプルファイル: {analysis["sample_file"]}')
    print(f'Needファイル形状: {analysis["sample_shape"]} (行=スロット, 列=日数)')
    print(f'Needファイルのスロット数: {analysis["rows_slots"]}個')
    print(f'期待スロット数: {analysis["expected_slots"]}個')
    print(f'スロット数不一致: {"[WARNING] あり" if analysis["slot_mismatch"] else "[OK] なし"}')

def verify_structure_inconsistency(time_analysis, need_analysis):
    """構造不整合の検証"""
    
    if 'error' in need_analysis:
        return {'error': 'Need分析エラーのため不整合検証不可'}
    
    # intermediate_data vs Needファイルの構造比較
    actual_slots = time_analysis['total_slots']  # 21
    need_slots = need_analysis['rows_slots']     # 48
    
    inconsistency = {
        'structure_mismatch': actual_slots != need_slots,
        'actual_slots': actual_slots,
        'need_slots': need_slots,
        'slot_gap': need_slots - actual_slots,
        'severity': 'CRITICAL' if actual_slots != need_slots else 'OK'
    }
    
    # 時間範囲の整合性チェック
    if not time_analysis['missing_times']:
        time_coverage_issue = False
    else:
        # 夜間時間帯が欠落しているかチェック
        night_missing = any(t.hour >= 18 or t.hour < 6 for t in time_analysis['missing_times'])
        time_coverage_issue = night_missing
    
    inconsistency.update({
        'time_coverage_issue': time_coverage_issue,
        'missing_night_slots': time_analysis['night_slots_missing']
    })
    
    return inconsistency

def print_inconsistency_analysis(analysis):
    """不整合分析の表示"""
    if 'error' in analysis:
        print(f'[ERROR] {analysis["error"]}')
        return
    
    print(f'構造不整合: {"[CRITICAL] 検出" if analysis["structure_mismatch"] else "[OK] なし"}')
    print(f'  実配置データスロット数: {analysis["actual_slots"]}個')
    print(f'  Needファイルスロット数: {analysis["need_slots"]}個')
    print(f'  スロット差分: {analysis["slot_gap"]}個')
    print(f'時間カバレッジ問題: {"[WARNING] あり" if analysis["time_coverage_issue"] else "[OK] なし"}')
    print(f'  欠落夜間スロット: {analysis["missing_night_slots"]}個')

def recalculate_actual_time_correctly(data, time_analysis):
    """実配置時間の正確な再計算"""
    
    total_records = len(data)
    actual_slots = time_analysis['total_slots']
    period_days = data['ds'].dt.date.nunique()
    
    # 正確なスロット時間計算
    # 実際の営業時間を基準とする
    first_time = time_analysis['first_time']
    last_time = time_analysis['last_time']
    
    # 営業時間の計算（分単位）
    first_minutes = first_time.hour * 60 + first_time.minute
    last_minutes = last_time.hour * 60 + last_time.minute
    operating_minutes = last_minutes - first_minutes + 30  # 最後のスロットの30分含む
    operating_hours = operating_minutes / 60
    
    # スロット当たりの時間
    slot_duration_hours = operating_hours / actual_slots
    
    # 再計算
    recalculated = {
        'operating_hours_per_day': operating_hours,
        'slot_duration_hours': slot_duration_hours,
        'total_allocated_hours_period': total_records * slot_duration_hours,
        'daily_allocated_hours': (total_records * slot_duration_hours) / period_days,
        'comparison_with_previous': {
            'previous_calculation': total_records * 0.52,  # 以前の計算
            'new_calculation': total_records * slot_duration_hours,
            'difference_ratio': (total_records * slot_duration_hours) / (total_records * 0.52) if total_records * 0.52 > 0 else 0
        }
    }
    
    return recalculated

def print_correct_time_calculation(calc):
    """正しい時間計算の表示"""
    print(f'営業時間: {calc["operating_hours_per_day"]:.1f}時間/日')
    print(f'スロット時間: {calc["slot_duration_hours"]:.3f}時間/スロット')
    print(f'期間総配置時間: {calc["total_allocated_hours_period"]:.1f}時間')
    print(f'日平均配置時間: {calc["daily_allocated_hours"]:.1f}時間/日')
    
    print(f'\n計算方法比較:')
    comp = calc['comparison_with_previous']
    print(f'  従来計算: {comp["previous_calculation"]:.1f}時間/月')
    print(f'  修正計算: {comp["new_calculation"]:.1f}時間/月')
    print(f'  比率: {comp["difference_ratio"]:.2f}倍')

def identify_root_cause_and_solution(time_analysis, need_analysis, inconsistency, time_calc):
    """根本原因特定と対策"""
    
    root_causes = []
    solutions = []
    
    # 根本原因1: 構造不整合
    if inconsistency.get('structure_mismatch', False):
        root_causes.append({
            'cause': 'intermediate_dataとNeedファイルのスロット数不整合',
            'details': f'実配置{inconsistency["actual_slots"]}個 vs Need{inconsistency["need_slots"]}個',
            'impact': 'Need算出の基盤が根本的に不整合'
        })
        
        solutions.append({
            'solution': '24スロット構造への統一',
            'approach': '夜間スロットをNeed=0、実配置=0として追加',
            'implementation': 'intermediate_dataに夜間スロットを0レコードで補完'
        })
    
    # 根本原因2: 時間計算の誤り
    if time_calc['comparison_with_previous']['difference_ratio'] != 1.0:
        root_causes.append({
            'cause': 'スロット時間計算の誤用',
            'details': f'0.52時間固定 vs 実際の{time_calc["slot_duration_hours"]:.3f}時間',
            'impact': '実配置時間の過大/過小評価'
        })
        
        solutions.append({
            'solution': '動的スロット時間計算の採用',
            'approach': f'実営業時間({time_calc["operating_hours_per_day"]:.1f}h) ÷ スロット数',
            'implementation': '営業時間ベースの動的計算'
        })
    
    # 根本原因3: 夜間除外の取り扱い
    if time_analysis['night_slots_missing'] > 0:
        root_causes.append({
            'cause': '夜間時間帯の不適切な除外',
            'details': f'{time_analysis["night_slots_missing"]}個の夜間スロットが欠落',
            'impact': 'ヒートマップ・分析の視覚的不整合'
        })
        
        solutions.append({
            'solution': '24時間完全対応の実装',
            'approach': '夜間=0で24スロット構造を維持',
            'implementation': 'データ補完とビューアの24時間対応'
        })
    
    return {
        'root_causes': root_causes,
        'solutions': solutions,
        'priority': 'CRITICAL - アルゴリズム設計前に解決必須',
        'impact_assessment': 'Need積算の根本的信頼性に関わる構造問題'
    }

def print_root_cause_analysis(analysis):
    """根本原因分析の表示"""
    print(f'優先度: {analysis["priority"]}')
    print(f'影響評価: {analysis["impact_assessment"]}')
    
    print(f'\n【根本原因 {len(analysis["root_causes"])}件】')
    for i, cause in enumerate(analysis['root_causes'], 1):
        print(f'{i}. {cause["cause"]}')
        print(f'   詳細: {cause["details"]}')
        print(f'   影響: {cause["impact"]}')
    
    print(f'\n【対策案 {len(analysis["solutions"])}件】')
    for i, solution in enumerate(analysis['solutions'], 1):
        print(f'{i}. {solution["solution"]}')
        print(f'   アプローチ: {solution["approach"]}')
        print(f'   実装方法: {solution["implementation"]}')

if __name__ == "__main__":
    result = investigate_21_slot_mystery()
    if result:
        print('\n' + '=' * 80)
        print('結論: 21スロット問題の根本原因特定完了')
        print('アルゴリズム設計前にこれらの構造問題の解決が必須')
        print('=' * 80)
    else:
        print('調査に失敗しました')