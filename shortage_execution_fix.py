# -*- coding: utf-8 -*-
"""
shortage.py実行プロセス修復スクリプト
Critical問題: shortage_time.parquet未生成の根本原因修復
"""

import sys
sys.path.append('.')

from pathlib import Path
import pandas as pd
from shift_suite.tasks import shortage
from shift_suite.tasks.constants import DEFAULT_SLOT_MINUTES

def diagnose_shortage_execution():
    """shortage実行プロセスの診断"""
    
    print('=== shortage.py実行プロセス診断 ===')
    
    scenarios = ['out_p25_based', 'out_mean_based', 'out_median_based']
    results = {}
    
    for scenario in scenarios:
        print(f'\n【{scenario}】')
        scenario_path = Path(f'extracted_results/{scenario}')
        
        if not scenario_path.exists():
            print(f'NG: シナリオディレクトリ未存在')
            results[scenario] = {'status': 'missing_directory'}
            continue
        
        # 必要ファイルの存在確認
        required_files = [
            'heat_ALL.parquet',
            'need_per_date_slot.parquet',
            'heatmap.meta.json'
        ]
        
        missing_files = []
        for required_file in required_files:
            if not (scenario_path / required_file).exists():
                missing_files.append(required_file)
        
        if missing_files:
            print(f'NG: 必要ファイル未存在: {missing_files}')
            results[scenario] = {
                'status': 'missing_prerequisites',
                'missing_files': missing_files
            }
            continue
        
        print('OK: 前提ファイル確認完了')
        
        # shortage_time.parquetの存在確認
        shortage_time_path = scenario_path / 'shortage_time.parquet'
        if shortage_time_path.exists():
            print(f'OK: shortage_time.parquet存在（{shortage_time_path.stat().st_size} bytes）')
            results[scenario] = {'status': 'completed'}
        else:
            print('NG: shortage_time.parquet未生成')
            results[scenario] = {
                'status': 'execution_needed',
                'ready_for_execution': True
            }
    
    return results

def execute_shortage_analysis(scenario_path: Path):
    """shortage分析を実行"""
    
    print(f'\n=== shortage分析実行: {scenario_path.name} ===')
    
    try:
        # shortage_and_brief関数を呼び出し
        result_paths = shortage.shortage_and_brief(
            out_dir=scenario_path,
            slot=DEFAULT_SLOT_MINUTES,  # 30分スロット
            include_zero_days=True,
            auto_detect_slot=True
        )
        
        if result_paths:
            shortage_time_path, shortage_role_path = result_paths
            print(f'SUCCESS: shortage_time.parquet生成完了')
            print(f'  - {shortage_time_path}')
            print(f'  - {shortage_role_path}')
            
            # 生成ファイルの検証
            if shortage_time_path and shortage_time_path.exists():
                df = pd.read_parquet(shortage_time_path)
                print(f'  検証: {df.shape[0]}時間帯 × {df.shape[1]}日付')
                total_shortage_slots = df.sum().sum()
                total_shortage_hours = total_shortage_slots * 0.5
                print(f'  総不足: {total_shortage_hours:.1f}時間')
                return True
            
        else:
            print('ERROR: shortage_and_brief実行失敗')
            return False
            
    except Exception as e:
        print(f'ERROR: shortage実行エラー: {e}')
        import traceback
        print('詳細エラー:')
        print(traceback.format_exc())
        return False

def fix_shortage_execution_process():
    """shortage実行プロセスの完全修復"""
    
    print('=== shortage実行プロセス完全修復 ===')
    
    # 1. 診断実行
    diagnosis = diagnose_shortage_execution()
    
    # 2. 修復対象の特定
    scenarios_to_fix = [
        scenario for scenario, result in diagnosis.items() 
        if result.get('status') == 'execution_needed'
    ]
    
    if not scenarios_to_fix:
        print('\n全シナリオでshortage_time.parquet生成済み - 修復不要')
        return diagnosis
    
    print(f'\n修復対象: {len(scenarios_to_fix)}シナリオ')
    
    # 3. 各シナリオでshortage分析実行
    fixed_scenarios = []
    failed_scenarios = []
    
    for scenario in scenarios_to_fix:
        scenario_path = Path(f'extracted_results/{scenario}')
        
        print(f'\n--- {scenario} 修復開始 ---')
        
        if execute_shortage_analysis(scenario_path):
            fixed_scenarios.append(scenario)
        else:
            failed_scenarios.append(scenario)
    
    # 4. 修復結果の確認
    print(f'\n=== 修復結果サマリー ===')
    print(f'修復成功: {len(fixed_scenarios)}件')
    for scenario in fixed_scenarios:
        print(f'  ✓ {scenario}')
    
    if failed_scenarios:
        print(f'修復失敗: {len(failed_scenarios)}件')
        for scenario in failed_scenarios:
            print(f'  ✗ {scenario}')
    
    # 5. 最終検証
    print(f'\n=== 最終検証 ===')
    final_diagnosis = diagnose_shortage_execution()
    
    completed_count = sum(1 for result in final_diagnosis.values() if result.get('status') == 'completed')
    total_count = len(final_diagnosis)
    
    print(f'shortage_time.parquet生成: {completed_count}/{total_count}シナリオ')
    
    if completed_count == total_count:
        print('SUCCESS: 全シナリオでshortage実行プロセス修復完了')
    else:
        print('PARTIAL: 一部シナリオで修復未完了')
    
    return final_diagnosis

if __name__ == '__main__':
    result = fix_shortage_execution_process()
    
    success_count = sum(1 for r in result.values() if r.get('status') == 'completed')
    total_count = len(result)
    
    print(f'\n修復完了: {success_count}/{total_count}シナリオ')
    
    if success_count == total_count:
        print('✓ Critical問題「shortage.py実行プロセス修復」完了')
    else:
        print('△ 一部シナリオで継続対応が必要')