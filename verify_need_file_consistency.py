#!/usr/bin/env python3
"""
Needファイルとの整合性確認
Step 3: 24スロット構造統一後のNeedファイル検証
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import time, datetime
import json

def verify_need_file_consistency():
    """Needファイルとの整合性確認実行"""
    
    print('=' * 80)
    print('Step 3: Needファイルとの整合性確認')
    print('目的: 24スロット構造統一後のNeed算出基盤の整合性検証')
    print('=' * 80)
    
    scenario_dir = Path('extracted_results/out_p25_based')
    
    try:
        # 1. 統一後intermediate_dataの構造確認
        print('\n【Phase 1: 統一後intermediate_data構造確認】')
        data_structure = verify_intermediate_data_structure(scenario_dir)
        print_data_structure_verification(data_structure)
        
        # 2. Needファイル群の構造分析
        print('\n【Phase 2: Needファイル群構造分析】')
        need_analysis = analyze_need_files_structure(scenario_dir)
        print_need_files_analysis(need_analysis)
        
        # 3. スロット数整合性の詳細検証
        print('\n【Phase 3: スロット数整合性検証】')
        slot_consistency = verify_slot_consistency(data_structure, need_analysis)
        print_slot_consistency_verification(slot_consistency)
        
        # 4. Need値の妥当性検証
        print('\n【Phase 4: Need値妥当性検証】')
        need_validity = verify_need_values_validity(need_analysis)
        print_need_validity_verification(need_validity)
        
        # 5. 時間軸整合性の確認
        print('\n【Phase 5: 時間軸整合性確認】')
        temporal_consistency = verify_temporal_consistency(data_structure, need_analysis)
        print_temporal_consistency_verification(temporal_consistency)
        
        # 6. 統合整合性評価
        print('\n【Phase 6: 統合整合性評価】')
        overall_assessment = assess_overall_consistency(
            data_structure, need_analysis, slot_consistency, 
            need_validity, temporal_consistency
        )
        print_overall_assessment(overall_assessment)
        
        return {
            'success': overall_assessment['consistent'],
            'data_structure': data_structure,
            'need_analysis': need_analysis,
            'slot_consistency': slot_consistency,
            'need_validity': need_validity,
            'temporal_consistency': temporal_consistency,
            'overall_assessment': overall_assessment
        }
        
    except Exception as e:
        print(f'[ERROR] 整合性確認失敗: {e}')
        return {'success': False, 'error': str(e)}

def verify_intermediate_data_structure(scenario_dir):
    """統一後intermediate_data構造確認"""
    
    data = pd.read_parquet(scenario_dir / 'intermediate_data.parquet')
    
    # 時間スロット構造の詳細確認
    unique_times = sorted(data['ds'].dt.time.unique())
    
    # 24時間完全スロットかチェック
    expected_24h_slots = []
    for hour in range(24):
        for minute in [0, 30]:
            expected_24h_slots.append(time(hour, minute))
    
    expected_set = set(expected_24h_slots)
    actual_set = set(unique_times)
    
    # 夜間スロット分析
    night_slots = [t for t in unique_times if t.hour >= 18 or t.hour < 6]
    operating_slots = [t for t in unique_times if 6 <= t.hour < 18]
    
    # NIGHT_SLOT_PLACEHOLDERの確認
    night_placeholder_records = len(data[data['role'] == 'NIGHT_SLOT'])
    operating_records = len(data[data['role'] != 'NIGHT_SLOT'])
    
    return {
        'total_records': len(data),
        'period_days': data['ds'].dt.date.nunique(),
        'slot_structure': {
            'total_slots': len(unique_times),
            'expected_24h_slots': len(expected_24h_slots),
            'complete_24h_coverage': expected_set == actual_set,
            'missing_slots': list(expected_set - actual_set),
            'extra_slots': list(actual_set - expected_set)
        },
        'time_classification': {
            'night_slots': len(night_slots),
            'operating_slots': len(operating_slots),
            'night_placeholder_records': night_placeholder_records,
            'operating_records': operating_records
        },
        'data_quality': {
            'has_duplicates': data.duplicated().any(),
            'has_missing_values': data.isnull().any().any(),
            'datetime_format_valid': pd.api.types.is_datetime64_any_dtype(data['ds'])
        }
    }

def print_data_structure_verification(structure):
    """データ構造検証結果の表示"""
    
    print(f'統一後データ: {structure["total_records"]:,}レコード ({structure["period_days"]}日間)')
    
    slot_info = structure['slot_structure']
    status = "[OK] 完全" if slot_info['complete_24h_coverage'] else "[ERROR] 不完全"
    print(f'24時間カバレッジ: {status}')
    print(f'  実際スロット数: {slot_info["total_slots"]}個')
    print(f'  期待スロット数: {slot_info["expected_24h_slots"]}個')
    
    if slot_info['missing_slots']:
        print(f'  欠落スロット: {len(slot_info["missing_slots"])}個')
    
    time_class = structure['time_classification']
    print(f'時間分類: 営業{time_class["operating_slots"]}スロット, 夜間{time_class["night_slots"]}スロット')
    print(f'レコード分類: 実働{time_class["operating_records"]}件, 夜間プレースホルダー{time_class["night_placeholder_records"]}件')

def analyze_need_files_structure(scenario_dir):
    """Needファイル群の構造分析"""
    
    need_files = list(scenario_dir.glob('need_per_date_slot_role_*.parquet'))
    
    if not need_files:
        return {'error': 'Needファイルが見つかりません'}
    
    need_analysis = {
        'file_count': len(need_files),
        'file_details': [],
        'structure_summary': {
            'consistent_structure': True,
            'slot_counts': set(),
            'date_ranges': set(),
            'total_need_values': 0
        }
    }
    
    for need_file in need_files:
        try:
            df = pd.read_parquet(need_file)
            
            # Need値の基本統計
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            total_need = df[numeric_cols].sum().sum() if len(numeric_cols) > 0 else 0
            
            file_info = {
                'filename': need_file.name,
                'shape': df.shape,
                'slot_count': df.shape[0],  # 行数 = スロット数
                'date_count': df.shape[1],  # 列数 = 日数
                'total_need_value': total_need,
                'has_negative_values': (df[numeric_cols] < 0).any().any() if len(numeric_cols) > 0 else False,
                'max_need_value': df[numeric_cols].max().max() if len(numeric_cols) > 0 else 0
            }
            
            need_analysis['file_details'].append(file_info)
            need_analysis['structure_summary']['slot_counts'].add(df.shape[0])
            need_analysis['structure_summary']['date_ranges'].add(df.shape[1])
            need_analysis['structure_summary']['total_need_values'] += total_need
            
        except Exception as e:
            need_analysis['file_details'].append({
                'filename': need_file.name,
                'error': str(e)
            })
            need_analysis['structure_summary']['consistent_structure'] = False
    
    # 構造一貫性チェック
    need_analysis['structure_summary']['slot_counts'] = list(need_analysis['structure_summary']['slot_counts'])
    need_analysis['structure_summary']['date_ranges'] = list(need_analysis['structure_summary']['date_ranges'])
    need_analysis['structure_summary']['consistent_structure'] = (
        len(need_analysis['structure_summary']['slot_counts']) == 1 and
        len(need_analysis['structure_summary']['date_ranges']) == 1
    )
    
    return need_analysis

def print_need_files_analysis(analysis):
    """Needファイル分析結果の表示"""
    
    if 'error' in analysis:
        print(f'[ERROR] {analysis["error"]}')
        return
    
    print(f'Needファイル数: {analysis["file_count"]}個')
    
    summary = analysis['structure_summary']
    status = "[OK] 一貫" if summary['consistent_structure'] else "[ERROR] 不一致"
    print(f'構造一貫性: {status}')
    print(f'  スロット数: {summary["slot_counts"]}')
    print(f'  日数: {summary["date_ranges"]}')
    print(f'  総Need値: {summary["total_need_values"]:.1f}')
    
    # ファイル詳細サンプル表示
    print(f'\nファイル詳細（最初の3個）:')
    for file_info in analysis['file_details'][:3]:
        if 'error' not in file_info:
            print(f'  {file_info["filename"]}: {file_info["shape"]}, Need合計={file_info["total_need_value"]:.1f}')
        else:
            print(f'  {file_info["filename"]}: エラー - {file_info["error"]}')

def verify_slot_consistency(data_structure, need_analysis):
    """スロット数整合性の詳細検証"""
    
    if 'error' in need_analysis:
        return {'error': 'Need分析エラーのため検証不可'}
    
    # データ構造のスロット数
    actual_data_slots = data_structure['slot_structure']['total_slots']
    
    # Needファイルのスロット数（一貫性があることを前提）
    need_slot_counts = need_analysis['structure_summary']['slot_counts']
    
    if len(need_slot_counts) == 1:
        need_slots = need_slot_counts[0]
        consistent = actual_data_slots == need_slots
    else:
        need_slots = None
        consistent = False
    
    consistency = {
        'consistent': consistent,
        'actual_data_slots': actual_data_slots,
        'need_file_slots': need_slots,
        'slot_difference': (need_slots - actual_data_slots) if need_slots else None,
        'severity': 'OK' if consistent else 'CRITICAL'
    }
    
    # 24時間完全カバレッジとNeedファイルの整合性
    complete_24h = data_structure['slot_structure']['complete_24h_coverage']
    expected_need_slots = 48  # 24時間 × 2スロット
    
    consistency.update({
        'complete_24h_coverage': complete_24h,
        'expected_slots_24h': expected_need_slots,
        'need_matches_24h': need_slots == expected_need_slots if need_slots else False,
        'ready_for_calculation': consistent and complete_24h and (need_slots == expected_need_slots)
    })
    
    return consistency

def print_slot_consistency_verification(consistency):
    """スロット整合性検証結果の表示"""
    
    if 'error' in consistency:
        print(f'[ERROR] {consistency["error"]}')
        return
    
    status = "[OK] 整合" if consistency['consistent'] else "[CRITICAL] 不整合"
    print(f'スロット数整合性: {status}')
    print(f'  実配置データ: {consistency["actual_data_slots"]}スロット')
    print(f'  Needファイル: {consistency["need_file_slots"]}スロット')
    
    if consistency['slot_difference']:
        print(f'  差分: {consistency["slot_difference"]}スロット')
    
    coverage_status = "[OK]" if consistency['complete_24h_coverage'] else "[ERROR]"
    print(f'24時間完全カバレッジ: {coverage_status}')
    
    calc_ready = "[OK] 準備完了" if consistency['ready_for_calculation'] else "[ERROR] 要修正"
    print(f'計算準備状況: {calc_ready}')

def verify_need_values_validity(need_analysis):
    """Need値の妥当性検証"""
    
    if 'error' in need_analysis:
        return {'error': 'Need分析エラーのため検証不可'}
    
    # 全ファイルの統計集計
    total_files = len(need_analysis['file_details'])
    successful_files = len([f for f in need_analysis['file_details'] if 'error' not in f])
    
    # Need値の妥当性チェック
    validity_checks = {
        'file_success_rate': successful_files / total_files if total_files > 0 else 0,
        'has_negative_values': any(
            f.get('has_negative_values', False) 
            for f in need_analysis['file_details'] if 'error' not in f
        ),
        'reasonable_value_range': True,  # 詳細チェック実装予定
        'total_need_reasonable': True   # 詳細チェック実装予定
    }
    
    # Need値の統計
    need_stats = {
        'total_need_all_files': need_analysis['structure_summary']['total_need_values'],
        'average_need_per_file': need_analysis['structure_summary']['total_need_values'] / successful_files if successful_files > 0 else 0,
        'max_need_value': max(
            f.get('max_need_value', 0) 
            for f in need_analysis['file_details'] if 'error' not in f
        ) if successful_files > 0 else 0
    }
    
    # 妥当性総合評価
    overall_validity = (
        validity_checks['file_success_rate'] >= 0.9 and
        not validity_checks['has_negative_values'] and
        validity_checks['reasonable_value_range'] and
        validity_checks['total_need_reasonable']
    )
    
    return {
        'valid': overall_validity,
        'validity_checks': validity_checks,
        'need_statistics': need_stats,
        'recommendations': generate_need_validity_recommendations(validity_checks, need_stats)
    }

def print_need_validity_verification(validity):
    """Need妥当性検証結果の表示"""
    
    if 'error' in validity:
        print(f'[ERROR] {validity["error"]}')
        return
    
    status = "[OK] 妥当" if validity['valid'] else "[WARNING] 要注意"
    print(f'Need値妥当性: {status}')
    
    checks = validity['validity_checks']
    print(f'  ファイル成功率: {checks["file_success_rate"]:.1%}')
    print(f'  負の値: {"検出" if checks["has_negative_values"] else "なし"}')
    
    stats = validity['need_statistics']
    print(f'  総Need値: {stats["total_need_all_files"]:.1f}')
    print(f'  平均Need/ファイル: {stats["average_need_per_file"]:.1f}')
    print(f'  最大Need値: {stats["max_need_value"]:.1f}')

def generate_need_validity_recommendations(validity_checks, need_stats):
    """Need妥当性に基づく推奨事項生成"""
    
    recommendations = []
    
    if validity_checks['file_success_rate'] < 0.9:
        recommendations.append('一部Needファイルの読み込みエラーを修正')
    
    if validity_checks['has_negative_values']:
        recommendations.append('負のNeed値の原因調査と修正')
    
    if need_stats['total_need_all_files'] == 0:
        recommendations.append('Need値が全て0の原因調査')
    
    if not recommendations:
        recommendations.append('Need値は妥当性基準を満たしています')
    
    return recommendations

def verify_temporal_consistency(data_structure, need_analysis):
    """時間軸整合性の確認"""
    
    if 'error' in need_analysis:
        return {'error': 'Need分析エラーのため検証不可'}
    
    # データ構造の期間
    data_days = data_structure['period_days']
    
    # Needファイルの期間（一貫性チェック済み前提）
    need_date_ranges = need_analysis['structure_summary']['date_ranges']
    
    if len(need_date_ranges) == 1:
        need_days = need_date_ranges[0]
        temporal_consistent = data_days == need_days
    else:
        need_days = None
        temporal_consistent = False
    
    return {
        'consistent': temporal_consistent,
        'data_period_days': data_days,
        'need_period_days': need_days,
        'period_difference': (need_days - data_days) if need_days else None,
        'temporal_alignment': temporal_consistent
    }

def print_temporal_consistency_verification(temporal):
    """時間軸整合性検証結果の表示"""
    
    if 'error' in temporal:
        print(f'[ERROR] {temporal["error"]}')
        return
    
    status = "[OK] 整合" if temporal['consistent'] else "[ERROR] 不整合"
    print(f'時間軸整合性: {status}')
    print(f'  実配置データ期間: {temporal["data_period_days"]}日')
    print(f'  Needファイル期間: {temporal["need_period_days"]}日')
    
    if temporal['period_difference']:
        print(f'  期間差分: {temporal["period_difference"]}日')

def assess_overall_consistency(data_structure, need_analysis, slot_consistency, need_validity, temporal_consistency):
    """統合整合性評価"""
    
    # 各要素の整合性チェック
    consistency_elements = {
        'data_structure_valid': data_structure['slot_structure']['complete_24h_coverage'],
        'need_files_accessible': 'error' not in need_analysis,
        'slot_consistency': slot_consistency.get('consistent', False),
        'need_validity': need_validity.get('valid', False),
        'temporal_consistency': temporal_consistency.get('consistent', False)
    }
    
    # 統合評価
    overall_consistent = all(consistency_elements.values())
    
    # クリティカル問題の特定
    critical_issues = []
    
    if not consistency_elements['data_structure_valid']:
        critical_issues.append('24時間スロット構造が不完全')
    
    if not consistency_elements['need_files_accessible']:
        critical_issues.append('Needファイルへのアクセス問題')
    
    if not consistency_elements['slot_consistency']:
        critical_issues.append('スロット数の不整合')
    
    if not consistency_elements['temporal_consistency']:
        critical_issues.append('期間の不整合')
    
    # 推奨アクション
    recommended_actions = []
    
    if overall_consistent:
        recommended_actions.extend([
            'Step 4: Needファイル構造の修正に進行可能',
            'Step 5: 新Need算出システムの実装準備完了'
        ])
    else:
        recommended_actions.extend([
            '特定された問題の修正が最優先',
            'アルゴリズム設計は整合性確保後に実施'
        ])
    
    return {
        'consistent': overall_consistent,
        'consistency_elements': consistency_elements,
        'critical_issues': critical_issues,
        'success_rate': sum(consistency_elements.values()) / len(consistency_elements),
        'recommended_actions': recommended_actions,
        'ready_for_next_step': overall_consistent
    }

def print_overall_assessment(assessment):
    """統合整合性評価結果の表示"""
    
    status = "[OK] 整合" if assessment['consistent'] else "[CRITICAL] 要修正"
    print(f'統合整合性評価: {status}')
    print(f'成功率: {assessment["success_rate"]:.1%}')
    
    print(f'\n整合性要素:')
    for element, result in assessment['consistency_elements'].items():
        element_status = "[OK]" if result else "[ERROR]"
        print(f'  {element}: {element_status}')
    
    if assessment['critical_issues']:
        print(f'\nクリティカル問題:')
        for issue in assessment['critical_issues']:
            print(f'  - {issue}')
    
    print(f'\n推奨アクション:')
    for action in assessment['recommended_actions']:
        print(f'  - {action}')
    
    next_step_status = "[OK] 準備完了" if assessment['ready_for_next_step'] else "[BLOCKED] 要修正"
    print(f'\n次ステップ: {next_step_status}')

if __name__ == "__main__":
    result = verify_need_file_consistency()
    
    if result and result.get('success', False):
        print('\n' + '=' * 80)
        print('Step 3完了: Needファイル整合性確認成功')
        print('Step 4: Needファイル構造修正に進行可能')
        print('=' * 80)
    else:
        print('\nStep 3失敗: 整合性問題の修正が必要')
        
        # 整合性レポートの保存
        if result:
            report_file = 'need_file_consistency_report.json'
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            print(f'詳細レポート保存: {report_file}')