#!/usr/bin/env python3
"""
24スロット構造への統一
Step1: intermediate_dataに欠落スロットを補完
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import time, datetime, timedelta
import json

def fix_24_slot_structure():
    """24スロット構造への統一実行"""
    
    print('=' * 80)
    print('Step 1: 24スロット構造への統一')
    print('目的: intermediate_dataを48スロット（24時間×30分）構造に補完')
    print('=' * 80)
    
    scenario_dir = Path('extracted_results/out_p25_based')
    
    try:
        # 1. 現在のデータ読み込み
        print('\n【Phase 1: 現在データの読み込み】')
        original_data = pd.read_parquet(scenario_dir / 'intermediate_data.parquet')
        
        print(f'元データ: {len(original_data)}レコード')
        print(f'期間: {original_data["ds"].dt.date.nunique()}日間')
        print(f'現在スロット数: {original_data["ds"].dt.time.nunique()}個')
        
        # 2. 完全な24時間スロット構造の定義
        print('\n【Phase 2: 24時間完全スロット構造の定義】')
        complete_slots = define_complete_24hour_slots()
        print(f'完全スロット数: {len(complete_slots)}個')
        
        # 3. 欠落スロットの特定
        print('\n【Phase 3: 欠落スロットの特定】')
        existing_times = set(original_data['ds'].dt.time.unique())
        missing_slots = identify_missing_slots(complete_slots, existing_times)
        print(f'欠落スロット数: {len(missing_slots)}個')
        
        # 4. 補完データの生成
        print('\n【Phase 4: 補完データの生成】')
        complemented_data = create_complemented_data(original_data, missing_slots)
        print(f'補完後データ: {len(complemented_data)}レコード')
        print(f'補完後スロット数: {complemented_data["ds"].dt.time.nunique()}個')
        
        # 5. データ整合性の検証
        print('\n【Phase 5: データ整合性検証】')
        validation_result = validate_complemented_data(complemented_data, complete_slots)
        print_validation_result(validation_result)
        
        # 6. 補完データの保存
        if validation_result['valid']:
            print('\n【Phase 6: 補完データの保存】')
            save_complemented_data(complemented_data, scenario_dir)
            
            # 7. 補完レポートの生成
            generate_complement_report(original_data, complemented_data, missing_slots, validation_result)
            
            return {
                'success': True,
                'original_records': len(original_data),
                'complemented_records': len(complemented_data),
                'missing_slots_filled': len(missing_slots),
                'validation_result': validation_result
            }
        else:
            print('\n[ERROR] データ検証に失敗しました')
            return {'success': False, 'validation_result': validation_result}
        
    except Exception as e:
        print(f'[ERROR] 24スロット構造統一に失敗: {e}')
        return {'success': False, 'error': str(e)}

def define_complete_24hour_slots():
    """完全な24時間スロット構造の定義"""
    
    complete_slots = []
    
    # 24時間 × 30分間隔 = 48スロット
    for hour in range(24):
        for minute in [0, 30]:
            complete_slots.append(time(hour, minute))
    
    return sorted(complete_slots)

def identify_missing_slots(complete_slots, existing_times):
    """欠落スロットの特定"""
    
    missing_slots = []
    
    for slot_time in complete_slots:
        if slot_time not in existing_times:
            missing_slots.append(slot_time)
    
    print(f'欠落時間帯の詳細（最初の10個）:')
    for i, slot in enumerate(missing_slots[:10]):
        print(f'  {slot}')
    if len(missing_slots) > 10:
        print(f'  ... 他{len(missing_slots) - 10}個')
    
    return missing_slots

def create_complemented_data(original_data, missing_slots):
    """補完データの生成"""
    
    # 期間の特定
    date_range = pd.date_range(
        start=original_data['ds'].dt.date.min(),
        end=original_data['ds'].dt.date.max(),
        freq='D'
    )
    
    print(f'補完対象期間: {len(date_range)}日間')
    print(f'欠落スロット: {len(missing_slots)}個/日')
    print(f'生成する補完レコード数: {len(date_range) * len(missing_slots)}個')
    
    # 補完レコードの生成
    complement_records = []
    
    for date in date_range:
        for slot_time in missing_slots:
            # 夜間スロットのダミーレコード作成
            # Need=0、実配置=0を表現するため、空のレコードは作らない
            # 代わりに、夜間であることを示すマーカーレコードを作成
            complement_record = {
                'ds': pd.Timestamp.combine(date.date(), slot_time),
                'staff': 'NIGHT_SLOT_PLACEHOLDER',  # 夜間スロットのプレースホルダー
                'role': 'NIGHT_SLOT',
                'employment': 'NIGHT_SLOT', 
                'code': 'NIGHT',
                'holiday_type': 'NORMAL',
                'parsed_slots_count': 0  # 夜間スロットは0
            }
            complement_records.append(complement_record)
    
    # 補完データフレーム作成
    complement_df = pd.DataFrame(complement_records)
    
    # 元データと統合
    complemented_data = pd.concat([original_data, complement_df], ignore_index=True)
    
    # 時系列でソート
    complemented_data = complemented_data.sort_values('ds').reset_index(drop=True)
    
    return complemented_data

def validate_complemented_data(data, complete_slots):
    """補完データの整合性検証"""
    
    validation = {
        'valid': True,
        'checks': {},
        'issues': []
    }
    
    # チェック1: 24時間完全カバー
    actual_times = set(data['ds'].dt.time.unique())
    expected_times = set(complete_slots)
    
    missing_after_complement = expected_times - actual_times
    extra_times = actual_times - expected_times
    
    validation['checks']['complete_coverage'] = len(missing_after_complement) == 0
    if missing_after_complement:
        validation['issues'].append(f'まだ欠落している時間帯: {len(missing_after_complement)}個')
        validation['valid'] = False
    
    if extra_times:
        validation['issues'].append(f'予期しない時間帯: {len(extra_times)}個')
    
    # チェック2: 48スロット確認
    validation['checks']['slot_count'] = len(actual_times) == 48
    if len(actual_times) != 48:
        validation['issues'].append(f'スロット数が48でない: {len(actual_times)}個')
        validation['valid'] = False
    
    # チェック3: 日付の連続性
    dates = data['ds'].dt.date.unique()
    validation['checks']['date_continuity'] = len(dates) > 0
    
    # チェック4: 夜間スロットの確認
    night_slots = [t for t in actual_times if t.hour >= 18 or t.hour < 6]
    validation['checks']['night_slots_present'] = len(night_slots) > 0
    
    return validation

def print_validation_result(validation):
    """検証結果の表示"""
    
    print(f'データ検証結果: {"[OK] 合格" if validation["valid"] else "[ERROR] 不合格"}')
    
    print('\n検証項目:')
    for check_name, result in validation['checks'].items():
        status = "[OK]" if result else "[ERROR]"
        print(f'  {check_name}: {status}')
    
    if validation['issues']:
        print('\n検出された問題:')
        for issue in validation['issues']:
            print(f'  - {issue}')

def save_complemented_data(data, scenario_dir):
    """補完データの保存"""
    
    # 元ファイルのバックアップ
    original_file = scenario_dir / 'intermediate_data.parquet'
    backup_file = scenario_dir / 'intermediate_data_21slot_backup.parquet'
    
    if original_file.exists():
        import shutil
        shutil.copy2(original_file, backup_file)
        print(f'元ファイルをバックアップ: {backup_file.name}')
    
    # 補完データの保存
    data.to_parquet(original_file, index=False)
    print(f'24スロット補完データを保存: {original_file.name}')
    
    # 検証用のサンプル出力
    sample_file = scenario_dir / 'intermediate_data_24slot_sample.csv'
    sample_data = data.head(100)
    sample_data.to_csv(sample_file, index=False, encoding='utf-8')
    print(f'サンプルデータ出力: {sample_file.name}')

def generate_complement_report(original_data, complemented_data, missing_slots, validation):
    """補完レポートの生成"""
    
    report = {
        'complement_timestamp': datetime.now().isoformat(),
        'operation': '24スロット構造への統一',
        'original_data_stats': {
            'records': len(original_data),
            'unique_slots': original_data['ds'].dt.time.nunique(),
            'date_range_days': original_data['ds'].dt.date.nunique()
        },
        'complemented_data_stats': {
            'records': len(complemented_data),
            'unique_slots': complemented_data['ds'].dt.time.nunique(),
            'date_range_days': complemented_data['ds'].dt.date.nunique()
        },
        'complement_operation': {
            'missing_slots_identified': len(missing_slots),
            'missing_slots_details': [str(t) for t in missing_slots],
            'complement_records_added': len(complemented_data) - len(original_data)
        },
        'validation_result': validation,
        'next_steps': [
            'Step 2: 正確なスロット時間計算の確立',
            'Step 3: Needファイルとの整合性確認'
        ]
    }
    
    # レポート保存
    with open('24_slot_complement_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f'\n補完レポート保存: 24_slot_complement_report.json')
    
    # サマリー表示
    print('\n' + '=' * 60)
    print('24スロット構造統一完了サマリー')
    print('=' * 60)
    print(f'元データ: {report["original_data_stats"]["records"]}レコード, {report["original_data_stats"]["unique_slots"]}スロット')
    print(f'補完後: {report["complemented_data_stats"]["records"]}レコード, {report["complemented_data_stats"]["unique_slots"]}スロット')
    print(f'追加レコード: {report["complement_operation"]["complement_records_added"]}個')
    print(f'検証結果: {"[OK] 成功" if validation["valid"] else "[ERROR] 失敗"}')

if __name__ == "__main__":
    result = fix_24_slot_structure()
    
    if result and result.get('success', False):
        print('\n' + '=' * 80)
        print('Step 1完了: 24スロット構造への統一成功')
        print('Step 2: 正確なスロット時間計算に進行可能')
        print('=' * 80)
    else:
        print('\nStep 1失敗: 問題を修正してから再実行してください')