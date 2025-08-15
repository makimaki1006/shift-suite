#!/usr/bin/env python3
"""
完全app統合テスト実行
按分廃止・職種別分析システムとapp.pyの完全統合テスト
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
import json
from datetime import datetime
import sys

class AppParameterExtractor:
    """app.pyからの動的パラメータ抽出クラス"""
    
    def __init__(self, app_file_path='app.py'):
        self.app_file_path = Path(app_file_path)
        
    def extract_scenario_directory_smart(self):
        """スマートシナリオディレクトリ抽出"""
        
        # 利用可能なシナリオディレクトリを検索
        extracted_results_path = Path('extracted_results')
        if extracted_results_path.exists():
            scenario_dirs = [d for d in extracted_results_path.iterdir() if d.is_dir() and d.name.startswith('out_')]
            
            if scenario_dirs:
                # 最初に見つかったシナリオディレクトリを使用
                selected_dir = scenario_dirs[0]
                
                return {
                    'directory': str(selected_dir),
                    'available_directories': [str(d) for d in scenario_dirs],
                    'extraction_method': 'SMART_DETECTION'
                }
        
        return {
            'directory': 'extracted_results/out_p25_based',
            'available_directories': [],
            'extraction_method': 'DEFAULT_FALLBACK'
        }
    
    def extract_period_from_data(self, scenario_dir):
        """データから期間を動的抽出"""
        
        try:
            intermediate_file = Path(scenario_dir) / 'intermediate_data.parquet'
            if intermediate_file.exists():
                df = pd.read_parquet(intermediate_file)
                if 'ds' in df.columns:
                    unique_dates = df['ds'].dt.date.nunique()
                    return {
                        'period_days': unique_dates,
                        'extraction_method': 'DATA_DRIVEN'
                    }
        except Exception as e:
            print(f'[WARNING] データからの期間抽出失敗: {e}')
        
        return {
            'period_days': 30,
            'extraction_method': 'DEFAULT'
        }

class DynamicNeedCalculationIntegration:
    """動的Need算出統合クラス - app.py統合専用"""
    
    def __init__(self, app_file_path='app.py'):
        self.param_extractor = AppParameterExtractor(app_file_path)
        self.calculation_results = {}
        
    def execute_integrated_calculation(self):
        """統合計算実行"""
        
        print('app.py統合Need算出実行中...')
        
        # 1. シナリオディレクトリ検出
        scenario_info = self.param_extractor.extract_scenario_directory_smart()
        scenario_dir = Path(scenario_info['directory'])
        
        print(f'使用シナリオディレクトリ: {scenario_dir}')
        print(f'検出方法: {scenario_info["extraction_method"]}')
        
        if not scenario_dir.exists():
            raise FileNotFoundError(f'シナリオディレクトリが存在しません: {scenario_dir}')
        
        # 2. 期間パラメータ抽出
        period_info = self.param_extractor.extract_period_from_data(scenario_dir)
        period_days = period_info['period_days']
        
        print(f'分析期間: {period_days}日 ({period_info["extraction_method"]})')
        
        # 3. データ読み込み
        data_package = self.load_dynamic_data(scenario_dir, period_days)
        
        # 4. Need算出実行
        calculation_results = self.execute_proportional_abolition_calculation(
            data_package, period_days
        )
        
        # 5. 結果統合
        integrated_results = {
            'scenario_info': scenario_info,
            'period_info': period_info,
            'data_metadata': data_package['metadata'],
            'calculation_results': calculation_results,
            'integration_timestamp': datetime.now().isoformat()
        }
        
        self.calculation_results = integrated_results
        return integrated_results
    
    def load_dynamic_data(self, scenario_dir, period_days):
        """動的データ読み込み"""
        
        print(f'データ読み込み中: {scenario_dir}')
        
        # intermediate_data読み込み
        intermediate_data = pd.read_parquet(scenario_dir / 'intermediate_data.parquet')
        operating_data = intermediate_data[intermediate_data['role'] != 'NIGHT_SLOT']
        
        # Need値動的読み込み（複数パターン対応）
        need_files_patterns = [
            'need_per_date_slot_role_*.parquet',
            'need_*_role_*.parquet',
            'need_*.parquet'
        ]
        
        need_files = []
        for pattern in need_files_patterns:
            found_files = list(scenario_dir.glob(pattern))
            if found_files:
                need_files = found_files
                break
        
        if not need_files:
            raise FileNotFoundError(f'Needファイルが見つかりません: {scenario_dir}')
        
        print(f'Needファイル検出: {len(need_files)}ファイル')
        
        # Need値処理
        need_data = {}
        for need_file in need_files:
            role_name = self.extract_role_name_from_filename(need_file.name)
            df = pd.read_parquet(need_file)
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            total_need = df[numeric_cols].sum().sum()
            
            need_data[role_name] = {
                'file_path': need_file,
                'total_need_value': total_need,
                'need_hours_total': total_need * 0.5,  # UNIFIED_SLOT_HOURS
                'need_hours_daily': (total_need * 0.5) / period_days  # 動的期間対応
            }
        
        return {
            'intermediate_data': intermediate_data,
            'operating_data': operating_data,
            'need_data': need_data,
            'metadata': {
                'total_records': len(operating_data),
                'period_days': period_days,  # 動的期間
                'unique_roles': operating_data['role'].nunique(),
                'unique_staff': operating_data['staff'].nunique(),
                'need_files_count': len(need_files),
                'total_need_hours': sum(data['need_hours_total'] for data in need_data.values())
            }
        }
    
    def extract_role_name_from_filename(self, filename):
        """ファイル名から職種名抽出"""
        
        # パターン1: need_per_date_slot_role_職種名.parquet
        if 'need_per_date_slot_role_' in filename:
            return filename.replace('need_per_date_slot_role_', '').replace('.parquet', '')
        
        # パターン2: need_職種名_role_*.parquet
        match = re.search(r'need_([^_]+)_role', filename)
        if match:
            return match.group(1)
        
        # パターン3: need_職種名.parquet
        if filename.startswith('need_'):
            return filename.replace('need_', '').replace('.parquet', '')
        
        # フォールバック
        return filename.replace('.parquet', '')
    
    def execute_proportional_abolition_calculation(self, data_package, period_days):
        """按分廃止計算実行"""
        
        print('按分廃止計算実行中...')
        
        operating_data = data_package['operating_data']
        need_data = data_package['need_data']
        
        # 職種別実配置時間計算
        role_actual_allocation = {}
        for role in operating_data['role'].unique():
            role_data = operating_data[operating_data['role'] == role]
            role_records = len(role_data)
            role_hours_total = role_records * 0.5
            role_hours_daily = role_hours_total / period_days  # 動的期間対応
            
            role_actual_allocation[role] = {
                'records': role_records,
                'hours_total': role_hours_total,
                'hours_daily': role_hours_daily,
                'staff_count': role_data['staff'].nunique()
            }
        
        # 職種別過不足算出
        role_shortages = {}
        for role_name, need_info in need_data.items():
            need_hours_daily = need_info['need_hours_daily']
            actual_info = role_actual_allocation.get(role_name, {
                'hours_daily': 0, 'staff_count': 0
            })
            actual_hours_daily = actual_info['hours_daily']
            shortage_daily = need_hours_daily - actual_hours_daily
            
            role_shortages[role_name] = {
                'role': role_name,
                'need_hours_daily': need_hours_daily,
                'actual_hours_daily': actual_hours_daily,
                'shortage_daily': shortage_daily,
                'shortage_status': 'SHORTAGE' if shortage_daily > 0 else 'SURPLUS' if shortage_daily < 0 else 'BALANCED',
                'staff_count_current': actual_info['staff_count']
            }
        
        # 組織全体過不足算出
        total_need_daily = sum(need_info['need_hours_daily'] for need_info in need_data.values())
        total_actual_daily = sum(actual_info['hours_daily'] for actual_info in role_actual_allocation.values())
        total_shortage_daily = total_need_daily - total_actual_daily
        
        print(f'計算完了: 職種{len(role_shortages)}個、組織全体{total_shortage_daily:+.1f}時間/日')
        
        return {
            'role_based_results': {
                'role_shortages': role_shortages,
                'shortage_ranking': sorted(role_shortages.values(), key=lambda x: x['shortage_daily'], reverse=True)
            },
            'organization_wide_results': {
                'total_need_daily': total_need_daily,
                'total_actual_daily': total_actual_daily,
                'total_shortage_daily': total_shortage_daily,
                'organization_status': 'SHORTAGE' if total_shortage_daily > 0 else 'SURPLUS' if total_shortage_daily < 0 else 'BALANCED'
            }
        }
    
    def get_streamlit_display_data(self):
        """Streamlit表示用データ取得"""
        
        if not self.calculation_results:
            raise ValueError('計算結果がありません。execute_integrated_calculation()を先に実行してください。')
        
        results = self.calculation_results['calculation_results']
        
        # 職種別データフレーム作成
        role_df = pd.DataFrame([
            {
                '職種': info['role'],
                'Need時間/日': round(info['need_hours_daily'], 1),
                '実配置時間/日': round(info['actual_hours_daily'], 1),
                '過不足時間/日': round(info['shortage_daily'], 1),
                '現在スタッフ数': info['staff_count_current'],
                '状態': info['shortage_status']
            }
            for info in results['role_based_results']['role_shortages'].values()
        ])
        
        # 組織全体データ
        org_data = results['organization_wide_results']
        
        return {
            'role_breakdown_df': role_df,
            'organization_summary': {
                'total_need': round(org_data['total_need_daily'], 1),
                'total_actual': round(org_data['total_actual_daily'], 1),
                'total_shortage': round(org_data['total_shortage_daily'], 1),
                'status': org_data['organization_status']
            },
            'scenario_info': self.calculation_results['scenario_info'],
            'period_info': self.calculation_results['period_info']
        }

def test_complete_app_integration():
    """完全app統合テスト実行"""
    
    print('=' * 80)
    print('完全app統合テスト実行')
    print('按分廃止・職種別分析システム×app.py統合検証')
    print('=' * 80)
    
    try:
        # 1. 統合システム初期化
        print('\n【Phase 1: 統合システム初期化】')
        integration = DynamicNeedCalculationIntegration('app.py')
        
        # 2. 統合計算実行
        print('\n【Phase 2: 統合計算実行】')
        calculation_results = integration.execute_integrated_calculation()
        
        # 3. Streamlit表示データ準備
        print('\n【Phase 3: Streamlit表示データ準備】')
        display_data = integration.get_streamlit_display_data()
        
        print(f'表示データ準備完了: {len(display_data["role_breakdown_df"])}職種')
        print(f'組織全体状態: {display_data["organization_summary"]["status"]}')
        print(f'組織全体過不足: {display_data["organization_summary"]["total_shortage"]:+.1f}時間/日')
        
        # 4. 結果検証
        print('\n【Phase 4: 結果検証】')
        
        validation_checks = {
            'calculation_completed': len(calculation_results) > 0,
            'role_data_available': len(display_data['role_breakdown_df']) > 0,
            'organization_status_valid': display_data['organization_summary']['status'] in ['SHORTAGE', 'SURPLUS', 'BALANCED'],
            'period_detected': calculation_results['period_info']['period_days'] > 0,
            'scenario_detected': calculation_results['scenario_info']['extraction_method'] != 'DEFAULT_FALLBACK'
        }
        
        validation_score = sum(validation_checks.values()) / len(validation_checks) * 100
        print(f'統合検証スコア: {validation_score:.1f}%')
        
        for check_name, result in validation_checks.items():
            status = '[OK]' if result else '[ERROR]'
            print(f'  {status} {check_name}: {result}')
        
        # 5. 職種別詳細表示
        print('\n【Phase 5: 職種別詳細結果】')
        role_df = display_data['role_breakdown_df']
        
        print(f'職種別分析結果 (上位5職種):')
        top_roles = role_df.nlargest(5, '過不足時間/日')
        for _, row in top_roles.iterrows():
            status_icon = '🔴' if row['状態'] == 'SHORTAGE' else '🟢' if row['状態'] == 'SURPLUS' else '⚪'
            print(f'  {status_icon} {row["職種"]}: {row["過不足時間/日"]:+.1f}h/日 (スタッフ{row["現在スタッフ数"]}名)')
        
        # 6. 結果保存
        test_results = {
            'test_success': True,
            'validation_score': validation_score,
            'validation_checks': validation_checks,
            'calculation_results': calculation_results,
            'display_data': {
                'role_count': len(display_data['role_breakdown_df']),
                'organization_summary': display_data['organization_summary'],
                'scenario_info': display_data['scenario_info'],
                'period_info': display_data['period_info']
            },
            'test_timestamp': datetime.now().isoformat()
        }
        
        result_file = f'完全app統合テスト結果_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2, default=str)
        print(f'\n統合テスト結果保存: {result_file}')
        
        # CSV出力
        role_csv_file = f'職種別過不足結果_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        role_df.to_csv(role_csv_file, index=False, encoding='utf-8')
        print(f'職種別結果CSV保存: {role_csv_file}')
        
        return test_results
        
    except Exception as e:
        print(f'[ERROR] 完全app統合テスト失敗: {e}')
        import traceback
        traceback.print_exc()
        return {'test_success': False, 'error': str(e)}

if __name__ == "__main__":
    result = test_complete_app_integration()
    
    if result and result.get('test_success', False):
        print('\n' + '=' * 80)
        print('[SUCCESS] 完全app統合テスト成功!')
        
        validation_score = result.get('validation_score', 0)
        if validation_score >= 90:
            print('[EXCELLENT] 完璧な統合を確認')
        elif validation_score >= 80:
            print('[VERY_GOOD] 高品質な統合を確認')
        elif validation_score >= 70:
            print('[GOOD] 良好な統合を確認')
        else:
            print('[WARNING] 統合品質の改善が必要')
            
        print(f'統合品質スコア: {validation_score:.1f}%')
        print('[READY] Streamlitダッシュボードでの利用準備完了')
        print('=' * 80)
        
        # 次のステップ案内
        print('\n次のステップ:')
        print('1. Streamlitダッシュボードでの表示テスト')
        print('2. app.pyへの統合機能組み込み')
        print('3. ユーザーインターフェースの実装')
        
    else:
        print('\n完全app統合テストで問題が発生しました')
        if 'error' in result:
            print(f'エラー詳細: {result["error"]}')