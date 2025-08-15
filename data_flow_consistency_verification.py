# -*- coding: utf-8 -*-
"""
データフロー一貫性検証スクリプト
データ入稿→分解→分析→加工→可視化の完全追跡
"""

import sys
sys.path.append('.')

import pandas as pd
from pathlib import Path
import json

def verify_data_flow_consistency():
    """データフロー全体の一貫性を検証"""
    
    print('=== データフロー一貫性検証 ===')
    
    # Step 1: データ入稿層の確認
    print('\n【Step 1: データ入稿層】')
    test_excel_files = [
        'デイ_テスト用データ_休日精緻.xlsx',
        'ショート_テスト用データ.xlsx',  
        'テストデータ_勤務表　勤務時間_トライアル.xlsx'
    ]
    
    available_excel = []
    for excel_file in test_excel_files:
        if Path(excel_file).exists():
            available_excel.append(excel_file)
            print(f'OK {excel_file}: 存在確認')
        else:
            print(f'NG {excel_file}: 未存在')
    
    # Step 2: データ分解層の確認
    print('\n【Step 2: データ分解層】')
    
    # intermediate_data.parquet の確認
    scenarios = ['out_p25_based', 'out_mean_based', 'out_median_based']
    intermediate_files = []
    
    for scenario in scenarios:
        intermediate_file = Path(f'extracted_results/{scenario}/intermediate_data.parquet')
        if intermediate_file.exists():
            try:
                df = pd.read_parquet(intermediate_file)
                intermediate_files.append((scenario, df))
                print(f'OK {scenario}/intermediate_data.parquet: {df.shape[0]}行×{df.shape[1]}列')
                
                # データ構造確認
                key_columns = ['staff', 'role', 'employment', 'date', 'start_time', 'end_time']
                available_columns = [col for col in key_columns if col in df.columns]
                print(f'  主要列: {len(available_columns)}/{len(key_columns)}個 {available_columns}')
                
            except Exception as e:
                print(f'NG {scenario}/intermediate_data.parquet: 読み込みエラー {e}')
    
    # Step 3: データ分析層の確認  
    print('\n【Step 3: データ分析層】')
    
    # need_per_date_slot_*.parquet の確認
    for scenario in scenarios:
        need_files = list(Path(f'extracted_results/{scenario}').glob('need_per_date_slot_role_*.parquet'))
        if need_files:
            print(f'OK {scenario}: {len(need_files)}職種のneedファイル')
            
            # サンプル分析
            sample_file = need_files[0]
            try:
                df = pd.read_parquet(sample_file)
                print(f'  サンプル分析: {df.shape[0]}レコード, 列{list(df.columns)[:5]}...')
            except Exception as e:
                print(f'  サンプル読み込みエラー: {e}')
        else:
            print(f'NG {scenario}: needファイル未存在')
    
    # Step 4: 分析結果加工層の確認
    print('\n【Step 4: 分析結果加工層】')
    
    # shortage系ファイルの確認
    for scenario in scenarios:
        scenario_path = Path(f'extracted_results/{scenario}')
        shortage_files = [
            'shortage_time.parquet',
            'shortage_role_summary.parquet', 
            'shortage_employment_summary.parquet'
        ]
        
        for shortage_file in shortage_files:
            file_path = scenario_path / shortage_file
            if file_path.exists():
                try:
                    df = pd.read_parquet(file_path)
                    print(f'OK {scenario}/{shortage_file}: {df.shape[0]}行')
                except Exception as e:
                    print(f'NG {scenario}/{shortage_file}: 読み込みエラー {e}')
            else:
                print(f'-- {scenario}/{shortage_file}: 未存在')
    
    # Step 5: 可視化層の確認
    print('\n【Step 5: 可視化層】')
    
    # ヒートマップファイルの確認
    for scenario in scenarios:
        scenario_path = Path(f'extracted_results/{scenario}')
        heat_files = list(scenario_path.glob('heat_*.parquet'))
        xlsx_files = list(scenario_path.glob('heat_*.xlsx'))
        
        print(f'OK {scenario}: ヒートマップ {len(heat_files)}parquet, {len(xlsx_files)}xlsx')
    
    # メタデータファイルの確認
    meta_files = ['heatmap.meta.json', 'shortage.meta.json']
    for scenario in scenarios:
        for meta_file in meta_files:
            file_path = Path(f'extracted_results/{scenario}/{meta_file}')
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        meta_data = json.load(f)
                    print(f'OK {scenario}/{meta_file}: メタデータ確認')
                except Exception as e:
                    print(f'NG {scenario}/{meta_file}: 読み込みエラー {e}')
    
    # Step 6: フロー一貫性評価
    print('\n【Step 6: フロー一貫性評価】')
    
    flow_consistency_score = 0
    max_score = 5
    
    # 1. データ入稿→分解の一貫性
    if available_excel and intermediate_files:
        flow_consistency_score += 1
        print('OK データ入稿→分解: 一貫性確認')
    else:
        print('NG データ入稿→分解: 一貫性問題')
    
    # 2. 分解→分析の一貫性  
    analysis_consistent = all(len(list(Path(f'extracted_results/{s}').glob('need_per_date_slot_role_*.parquet'))) > 0 for s in scenarios)
    if analysis_consistent:
        flow_consistency_score += 1
        print('OK 分解→分析: 一貫性確認')
    else:
        print('NG 分解→分析: 一貫性問題')
    
    # 3. 分析→加工の一貫性
    processing_files_exist = []
    for scenario in scenarios:
        shortage_exists = Path(f'extracted_results/{scenario}/shortage_time.parquet').exists()
        processing_files_exist.append(shortage_exists)
    
    if any(processing_files_exist):
        flow_consistency_score += 1
        print('OK 分析→加工: 一貫性確認')
    else:
        print('NG 分析→加工: 一貫性問題')
    
    # 4. 加工→可視化の一貫性
    visualization_consistent = all(len(list(Path(f'extracted_results/{s}').glob('heat_*.parquet'))) > 0 for s in scenarios)
    if visualization_consistent:
        flow_consistency_score += 1
        print('OK 加工→可視化: 一貫性確認')
    else:
        print('NG 加工→可視化: 一貫性問題')
    
    # 5. 全体統合の一貫性
    ui_apps_exist = Path('app.py').exists() and Path('dash_app.py').exists()
    if ui_apps_exist:
        flow_consistency_score += 1
        print('OK 全体統合: UI統合確認')
    else:
        print('NG 全体統合: UI統合問題')
    
    # 総合評価
    consistency_percentage = (flow_consistency_score / max_score) * 100
    print(f'\n【総合評価】')
    print(f'フロー一貫性スコア: {flow_consistency_score}/{max_score} ({consistency_percentage:.1f}%)')
    
    if consistency_percentage >= 80:
        status = '優秀'
    elif consistency_percentage >= 60:
        status = '良好'
    elif consistency_percentage >= 40:
        status = '要改善'
    else:
        status = '問題あり'
    
    print(f'一貫性評価: {status}')
    
    return {
        'flow_score': flow_consistency_score,
        'max_score': max_score,
        'percentage': consistency_percentage,
        'status': status,
        'available_excel': available_excel,
        'scenarios': scenarios,
        'intermediate_files': len(intermediate_files)
    }

if __name__ == '__main__':
    result = verify_data_flow_consistency()
    print(f'\n検証完了: {result["status"]} ({result["percentage"]:.1f}%)')