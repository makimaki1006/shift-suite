#!/usr/bin/env python3
"""
app.py側への按分廃止機能追加
按分廃止分析結果をZIP出力用に保存する機能を実装
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import sys
import re

# 既存の統合モジュールからインポート
sys.path.append('.')

class AppProportionalAbolitionIntegrator:
    """app.py用按分廃止統合クラス"""
    
    def __init__(self):
        self.integration_results = {}
        
    def execute_proportional_abolition_analysis(self, scenario_dir=None):
        """按分廃止分析実行"""
        
        print('=' * 80)
        print('app.py統合: 按分廃止分析実行')
        print('目的: ZIP出力用の按分廃止分析結果生成')
        print('=' * 80)
        
        try:
            # 1. シナリオディレクトリ検出
            if not scenario_dir:
                scenario_dir = self.detect_scenario_directory()
            
            scenario_path = Path(scenario_dir)
            if not scenario_path.exists():
                raise FileNotFoundError(f'シナリオディレクトリが存在しません: {scenario_path}')
                
            print(f'使用シナリオディレクトリ: {scenario_path}')
            
            # 2. データ読み込み
            print('\n【Phase 1: データ読み込み】')
            data_package = self.load_scenario_data(scenario_path)
            
            # 3. 按分廃止計算実行
            print('\n【Phase 2: 按分廃止計算実行】')
            calculation_results = self.calculate_proportional_abolition(data_package)
            
            # 4. ZIP出力用ファイル生成
            print('\n【Phase 3: ZIP出力用ファイル生成】')
            output_files = self.generate_zip_output_files(calculation_results, data_package)
            
            self.integration_results = {
                'scenario_directory': str(scenario_path),
                'calculation_results': calculation_results,
                'output_files': output_files,
                'execution_timestamp': datetime.now().isoformat()
            }
            
            return self.integration_results
            
        except Exception as e:
            print(f'[ERROR] 按分廃止分析実行失敗: {e}')
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def detect_scenario_directory(self):
        """シナリオディレクトリ自動検出"""
        
        extracted_results_path = Path('extracted_results')
        if extracted_results_path.exists():
            scenario_dirs = [d for d in extracted_results_path.iterdir() 
                           if d.is_dir() and d.name.startswith('out_')]
            
            if scenario_dirs:
                selected_dir = scenario_dirs[0]  # 最初に見つかったディレクトリを使用
                print(f'シナリオディレクトリ自動検出: {selected_dir}')
                return str(selected_dir)
        
        # デフォルトフォールバック
        return 'extracted_results/out_p25_based'
    
    def load_scenario_data(self, scenario_path):
        """シナリオデータ読み込み"""
        
        # intermediate_data読み込み
        intermediate_file = scenario_path / 'intermediate_data.parquet'
        if not intermediate_file.exists():
            raise FileNotFoundError(f'intermediate_data.parquet が見つかりません: {intermediate_file}')
            
        intermediate_data = pd.read_parquet(intermediate_file)
        operating_data = intermediate_data[intermediate_data['role'] != 'NIGHT_SLOT']
        
        print(f'intermediate_data読み込み: {len(intermediate_data):,}レコード')
        print(f'稼働データ抽出: {len(operating_data):,}レコード')
        
        # 期間計算
        if 'ds' in intermediate_data.columns:
            period_days = intermediate_data['ds'].dt.date.nunique()
        else:
            period_days = 30  # デフォルト
            
        print(f'分析期間: {period_days}日')
        
        # Needファイル読み込み
        need_files = list(scenario_path.glob('need_per_date_slot_role_*.parquet'))
        if not need_files:
            raise FileNotFoundError(f'Needファイルが見つかりません: {scenario_path}')
            
        print(f'Needファイル検出: {len(need_files)}ファイル')
        
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
                'need_hours_daily': (total_need * 0.5) / period_days
            }
            
            print(f'  {role_name}: {total_need:,.0f} → {need_data[role_name]["need_hours_daily"]:.1f}h/日')
        
        return {
            'intermediate_data': intermediate_data,
            'operating_data': operating_data,
            'need_data': need_data,
            'metadata': {
                'total_records': len(operating_data),
                'period_days': period_days,
                'unique_roles': operating_data['role'].nunique(),
                'unique_staff': operating_data['staff'].nunique(),
                'need_files_count': len(need_files),
                'scenario_path': str(scenario_path)
            }
        }
    
    def extract_role_name_from_filename(self, filename):
        """ファイル名から職種名抽出"""
        
        if 'need_per_date_slot_role_' in filename:
            return filename.replace('need_per_date_slot_role_', '').replace('.parquet', '')
        
        match = re.search(r'need_([^_]+)_role', filename)
        if match:
            return match.group(1)
        
        if filename.startswith('need_'):
            return filename.replace('need_', '').replace('.parquet', '')
        
        return filename.replace('.parquet', '')
    
    def calculate_proportional_abolition(self, data_package):
        """按分廃止計算実行"""
        
        operating_data = data_package['operating_data']
        need_data = data_package['need_data']
        period_days = data_package['metadata']['period_days']
        
        print(f'職種別配置時間計算: {operating_data["role"].nunique()}職種')
        
        # 職種別実配置時間計算
        role_actual_allocation = {}
        for role in operating_data['role'].unique():
            role_data = operating_data[operating_data['role'] == role]
            role_records = len(role_data)
            role_hours_total = role_records * 0.5  # UNIFIED_SLOT_HOURS
            role_hours_daily = role_hours_total / period_days
            
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
                'hours_daily': 0, 'staff_count': 0, 'records': 0
            })
            actual_hours_daily = actual_info['hours_daily']
            shortage_daily = need_hours_daily - actual_hours_daily
            
            role_shortages[role_name] = {
                'role': role_name,
                'need_hours_daily': need_hours_daily,
                'actual_hours_daily': actual_hours_daily,
                'shortage_daily': shortage_daily,
                'shortage_status': self.get_shortage_status(shortage_daily),
                'staff_count_current': actual_info['staff_count'],
                'shortage_magnitude': abs(shortage_daily)
            }
            
            print(f'  {role_name}: Need {need_hours_daily:.1f}h/日, 実配置 {actual_hours_daily:.1f}h/日, 過不足 {shortage_daily:+.1f}h/日')
        
        # 組織全体過不足算出
        total_need_daily = sum(need_info['need_hours_daily'] for need_info in need_data.values())
        total_actual_daily = sum(actual_info['hours_daily'] for actual_info in role_actual_allocation.values())
        total_shortage_daily = total_need_daily - total_actual_daily
        
        print(f'\n組織全体: Need {total_need_daily:.1f}h/日, 実配置 {total_actual_daily:.1f}h/日, 過不足 {total_shortage_daily:+.1f}h/日')
        
        return {
            'role_based_results': {
                'role_shortages': role_shortages,
                'shortage_ranking': sorted(role_shortages.values(), key=lambda x: x['shortage_daily'], reverse=True)
            },
            'organization_wide_results': {
                'total_need_daily': total_need_daily,
                'total_actual_daily': total_actual_daily,
                'total_shortage_daily': total_shortage_daily,
                'organization_status': self.get_shortage_status(total_shortage_daily),
                'total_staff_count': data_package['metadata']['unique_staff']
            }
        }
    
    def get_shortage_status(self, shortage_value):
        """不足状況判定"""
        if shortage_value > 0.1:
            return 'SHORTAGE'
        elif shortage_value < -0.1:
            return 'SURPLUS'
        else:
            return 'BALANCED'
    
    def generate_zip_output_files(self, calculation_results, data_package):
        """ZIP出力用ファイル生成"""
        
        print('ZIP出力用ファイル生成中...')
        
        output_files = []
        
        # 1. 職種別按分廃止結果
        role_data = []
        for role_name, role_info in calculation_results['role_based_results']['role_shortages'].items():
            role_data.append({
                '職種': role_info['role'],
                'Need時間/日': round(role_info['need_hours_daily'], 1),
                '実配置時間/日': round(role_info['actual_hours_daily'], 1),
                '過不足時間/日': round(role_info['shortage_daily'], 1),
                '現在スタッフ数': role_info['staff_count_current'],
                '状態': role_info['shortage_status']
            })
        
        role_df = pd.DataFrame(role_data)
        role_file = 'proportional_abolition_role_summary.parquet'
        role_df.to_parquet(role_file, index=False)
        output_files.append(role_file)
        print(f'  職種別結果保存: {role_file} ({len(role_df)}職種)')
        
        # 2. 組織全体按分廃止結果
        org_data = calculation_results['organization_wide_results']
        org_df = pd.DataFrame([{
            'total_need': round(org_data['total_need_daily'], 1),
            'total_actual': round(org_data['total_actual_daily'], 1),
            'total_shortage': round(org_data['total_shortage_daily'], 1),
            'status': org_data['organization_status'],
            'total_staff_count': org_data['total_staff_count']
        }])
        
        org_file = 'proportional_abolition_organization_summary.parquet'
        org_df.to_parquet(org_file, index=False)
        output_files.append(org_file)
        print(f'  組織全体結果保存: {org_file}')
        
        # 3. 按分廃止メタデータ
        metadata = {
            'analysis_type': '按分廃止・職種別分析',
            'analysis_description': '従来の按分方式を廃止し、各職種の真の過不足を分析',
            'timestamp': datetime.now().isoformat(),
            'period_days': data_package['metadata']['period_days'],
            'scenario_directory': data_package['metadata']['scenario_path'],
            'total_roles_analyzed': len(calculation_results['role_based_results']['role_shortages']),
            'organization_status': org_data['organization_status'],
            'proportional_abolition_effectiveness': self.calculate_effectiveness(calculation_results)
        }
        
        metadata_file = 'proportional_abolition_metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        output_files.append(metadata_file)
        print(f'  メタデータ保存: {metadata_file}')
        
        print(f'ZIP出力ファイル生成完了: {len(output_files)}ファイル')
        
        return {
            'files_created': output_files,
            'role_summary_file': role_file,
            'organization_summary_file': org_file,
            'metadata_file': metadata_file
        }
    
    def calculate_effectiveness(self, calculation_results):
        """按分廃止効果計算"""
        
        role_shortages = calculation_results['role_based_results']['role_shortages']
        org_results = calculation_results['organization_wide_results']
        
        # 深刻な不足職種数
        severe_shortage_roles = len([r for r in role_shortages.values() if r['shortage_daily'] > 2.0])
        
        # 完全未配置職種数
        zero_allocation_roles = len([r for r in role_shortages.values() 
                                   if r['staff_count_current'] == 0 and r['need_hours_daily'] > 0])
        
        # 組織全体では均衡に見えるが個別職種で深刻な不均衡
        organization_appears_balanced = abs(org_results['total_shortage_daily']) < 5.0
        individual_roles_severely_imbalanced = (severe_shortage_roles > 0 or zero_allocation_roles > 0)
        
        if organization_appears_balanced and individual_roles_severely_imbalanced:
            return 'HIGH'  # 按分による隠蔽効果が顕著
        elif individual_roles_severely_imbalanced:
            return 'MEDIUM'  # 職種別不均衡が存在
        else:
            return 'LOW'  # 比較的均衡している

def integrate_proportional_abolition_to_app():
    """app.pyへの按分廃止機能統合実行"""
    
    print('=' * 80)
    print('app.py按分廃止機能統合')
    print('按分廃止分析結果のZIP出力機能追加')
    print('=' * 80)
    
    try:
        # 1. 按分廃止分析実行
        integrator = AppProportionalAbolitionIntegrator()
        results = integrator.execute_proportional_abolition_analysis()
        
        if results.get('success', True):  # successキーがない場合は成功とみなす
            print('\n' + '=' * 80)
            print('[SUCCESS] app.py按分廃止機能統合完了!')
            print('🎯 按分廃止分析結果がZIP出力用ファイルとして準備完了')
            print('=' * 80)
            
            # 結果サマリー表示
            calc_results = results['calculation_results']
            org_results = calc_results['organization_wide_results']
            role_count = len(calc_results['role_based_results']['role_shortages'])
            
            print(f'\n📊 按分廃止分析結果サマリー:')
            print(f'   分析職種数: {role_count}職種')
            print(f'   組織全体状態: {org_results["organization_status"]}')
            print(f'   組織全体過不足: {org_results["total_shortage_daily"]:+.1f}時間/日')
            print(f'   総スタッフ数: {org_results["total_staff_count"]}名')
            
            print(f'\n📁 出力ファイル:')
            for file_path in results['output_files']['files_created']:
                print(f'   ✅ {file_path}')
            
            print(f'\n🎯 次のステップ:')
            print('1. これらのファイルを既存のZIP出力処理に含める')
            print('2. app.pyの分析実行時に按分廃止分析を自動実行')
            print('3. dash_app.pyで按分廃止タブを追加して結果表示')
            
            return results
        else:
            print(f'\n[ERROR] 按分廃止機能統合失敗: {results.get("error", "Unknown error")}')
            return results
            
    except Exception as e:
        print(f'[ERROR] 按分廃止機能統合実行失敗: {e}')
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    result = integrate_proportional_abolition_to_app()
    
    if result and result.get('success', True):
        print('\n🚀 app.py統合準備完了 - Step 2のdash_app.py修正に進むことができます')
    else:
        print('\napp.py統合でエラーが発生しました。問題を解決してから次のステップに進んでください。')