#!/usr/bin/env python3
"""
動的パラメータ抽出テスト
app.pyからの期間パラメータとシナリオディレクトリの動的抽出テスト
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
import json
from datetime import datetime

class AppParameterExtractor:
    """app.pyからの動的パラメータ抽出クラス"""
    
    def __init__(self, app_file_path='app.py'):
        self.app_file_path = Path(app_file_path)
        
    def extract_period_parameters(self):
        """期間パラメータ抽出"""
        
        try:
            with open(self.app_file_path, 'r', encoding='utf-8') as f:
                app_content = f.read()
            
            # need_ref_start_date_widget と need_ref_end_date_widget の検索
            period_params = {}
            
            # 開始日パターン検索
            start_date_patterns = [
                r'need_ref_start_date_widget.*?=.*?([\'"][^\'"\n]*[\'"])',
                r'need_ref_start_date.*?=.*?([\'"][^\'"\n]*[\'"])',
                r'start.*?date.*?=.*?([\'"][^\'"\n]*[\'"])',
            ]
            
            # 終了日パターン検索
            end_date_patterns = [
                r'need_ref_end_date_widget.*?=.*?([\'"][^\'"\n]*[\'"])',
                r'need_ref_end_date.*?=.*?([\'"][^\'"\n]*[\'"])',
                r'end.*?date.*?=.*?([\'"][^\'"\n]*[\'"])',
            ]
            
            # デフォルト値設定
            period_params = {
                'start_date': None,
                'end_date': None,
                'period_days': 30,  # デフォルト
                'extraction_method': 'DEFAULT'
            }
            
            # パターンマッチング実行
            for pattern in start_date_patterns:
                match = re.search(pattern, app_content, re.IGNORECASE | re.DOTALL)
                if match:
                    period_params['start_date'] = match.group(1).strip('\'"')
                    period_params['extraction_method'] = 'REGEX_EXTRACTED'
                    break
            
            for pattern in end_date_patterns:
                match = re.search(pattern, app_content, re.IGNORECASE | re.DOTALL)
                if match:
                    period_params['end_date'] = match.group(1).strip('\'"')
                    period_params['extraction_method'] = 'REGEX_EXTRACTED'
                    break
            
            # 期間日数計算
            if period_params['start_date'] and period_params['end_date']:
                try:
                    start_dt = pd.to_datetime(period_params['start_date'])
                    end_dt = pd.to_datetime(period_params['end_date'])
                    period_params['period_days'] = (end_dt - start_dt).days + 1
                except Exception as e:
                    print(f'[WARNING] 日付解析失敗: {e}')
                    period_params['period_days'] = 30
            
            return period_params
            
        except Exception as e:
            print(f'[WARNING] app.pyパラメータ抽出失敗: {e}')
            return {
                'start_date': None,
                'end_date': None,
                'period_days': 30,
                'extraction_method': 'ERROR_FALLBACK'
            }
    
    def extract_scenario_directory(self):
        """シナリオディレクトリ抽出"""
        
        try:
            with open(self.app_file_path, 'r', encoding='utf-8') as f:
                app_content = f.read()
            
            # シナリオディレクトリパターン検索
            directory_patterns = [
                r'extracted_results[/\\\\]([^/\\\\\'\"\\s]+)',
                r'scenario.*?dir.*?=.*?[\'"]([^\'\"]+)[\'"]',
                r'out_[a-zA-Z0-9_]+',
            ]
            
            scenario_info = {
                'directory': 'extracted_results/out_p25_based',  # デフォルト
                'extraction_method': 'DEFAULT'
            }
            
            for pattern in directory_patterns:
                matches = re.findall(pattern, app_content, re.IGNORECASE)
                if matches:
                    scenario_info['directory'] = f'extracted_results/{matches[-1]}'
                    scenario_info['extraction_method'] = 'REGEX_EXTRACTED'
                    break
            
            return scenario_info
            
        except Exception as e:
            print(f'[WARNING] シナリオディレクトリ抽出失敗: {e}')
            return {
                'directory': 'extracted_results/out_p25_based',
                'extraction_method': 'ERROR_FALLBACK'
            }
    
    def extract_all_parameters(self):
        """全パラメータ統合抽出"""
        
        period_params = self.extract_period_parameters()
        scenario_info = self.extract_scenario_directory()
        
        return {
            'period': period_params,
            'scenario': scenario_info,
            'extraction_timestamp': datetime.now().isoformat(),
            'app_file_path': str(self.app_file_path)
        }

def test_dynamic_parameter_extraction():
    """動的パラメータ抽出テスト実行"""
    
    print('=' * 80)
    print('動的パラメータ抽出テスト')
    print('app.pyからの期間・シナリオパラメータ抽出検証')
    print('=' * 80)
    
    try:
        # 1. app.pyファイル存在確認
        app_file_path = Path('app.py')
        if not app_file_path.exists():
            print(f'[ERROR] app.pyファイルが見つかりません: {app_file_path}')
            return {'success': False, 'error': 'app.py not found'}
        
        print(f'[INFO] app.pyファイル確認: {app_file_path} (サイズ: {app_file_path.stat().st_size} bytes)')
        
        # 2. パラメータ抽出実行
        print('\n【Phase 1: パラメータ抽出実行】')
        extractor = AppParameterExtractor('app.py')
        
        # 期間パラメータテスト
        period_params = extractor.extract_period_parameters()
        print(f'期間パラメータ抽出: {period_params["extraction_method"]}')
        print(f'  開始日: {period_params["start_date"]}')
        print(f'  終了日: {period_params["end_date"]}')
        print(f'  期間日数: {period_params["period_days"]}日')
        
        # シナリオディレクトリテスト
        scenario_info = extractor.extract_scenario_directory()
        print(f'\nシナリオディレクトリ抽出: {scenario_info["extraction_method"]}')
        print(f'  ディレクトリ: {scenario_info["directory"]}')
        
        # 統合パラメータテスト
        all_params = extractor.extract_all_parameters()
        print(f'\n統合パラメータ抽出成功: {len(all_params)}項目')
        
        # 3. 抽出結果検証
        print('\n【Phase 2: 抽出結果検証】')
        
        # シナリオディレクトリ存在確認
        scenario_path = Path(scenario_info['directory'])
        scenario_exists = scenario_path.exists()
        print(f'シナリオディレクトリ存在: {scenario_exists} ({scenario_path})')
        
        if scenario_exists:
            # intermediate_data.parquet存在確認
            intermediate_file = scenario_path / 'intermediate_data.parquet'
            intermediate_exists = intermediate_file.exists()
            print(f'intermediate_data.parquet存在: {intermediate_exists}')
            
            # Needファイル確認
            need_files = list(scenario_path.glob('need_per_date_slot_role_*.parquet'))
            print(f'Needファイル数: {len(need_files)}個')
            
            if need_files:
                print('  Needファイル一覧:')
                for need_file in need_files[:5]:  # 最初の5個を表示
                    print(f'    - {need_file.name}')
                if len(need_files) > 5:
                    print(f'    - ... 他{len(need_files) - 5}ファイル')
        
        # 4. 動的対応性評価
        print('\n【Phase 3: 動的対応性評価】')
        
        dynamic_compatibility = {
            'parameter_extraction': period_params['extraction_method'] != 'ERROR_FALLBACK',
            'scenario_detection': scenario_info['extraction_method'] != 'ERROR_FALLBACK',
            'data_file_accessibility': scenario_exists and intermediate_exists,
            'need_files_available': len(need_files) > 0 if scenario_exists else False
        }
        
        compatibility_score = sum(dynamic_compatibility.values()) / len(dynamic_compatibility) * 100
        print(f'動的対応度: {compatibility_score:.1f}%')
        
        for test_name, result in dynamic_compatibility.items():
            status = '[OK]' if result else '[ERROR]'
            print(f'  {status} {test_name}: {result}')
        
        # 5. 結果保存
        test_results = {
            'test_success': True,
            'extraction_results': all_params,
            'validation_results': {
                'scenario_exists': scenario_exists,
                'intermediate_exists': intermediate_exists if scenario_exists else False,
                'need_files_count': len(need_files) if scenario_exists else 0
            },
            'dynamic_compatibility': dynamic_compatibility,
            'compatibility_score': compatibility_score,
            'test_timestamp': datetime.now().isoformat()
        }
        
        result_file = f'動的パラメータ抽出テスト結果_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2, default=str)
        print(f'\nテスト結果保存: {result_file}')
        
        return test_results
        
    except Exception as e:
        print(f'[ERROR] 動的パラメータ抽出テスト失敗: {e}')
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    result = test_dynamic_parameter_extraction()
    
    if result and result.get('test_success', False):
        print('\n' + '=' * 80)
        print('[SUCCESS] 動的パラメータ抽出テスト完了')
        compatibility_score = result.get('compatibility_score', 0)
        if compatibility_score >= 80:
            print('[EXCELLENT] 高い動的対応性を確認')
        elif compatibility_score >= 60:
            print('[GOOD] 十分な動的対応性を確認')
        else:
            print('[WARNING] 動的対応性の改善が必要')
        print(f'総合動的対応度: {compatibility_score:.1f}%')
        print('=' * 80)
    else:
        print('\n動的パラメータ抽出テストで問題が発生しました')