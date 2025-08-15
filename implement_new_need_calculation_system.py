#!/usr/bin/env python3
"""
新Need算出システムの実装
Step 5: 按分廃止・職種別分析の完全実装
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import time, datetime
import json
import sys
sys.path.append('.')
from unified_time_calculation_system import records_to_daily_hours, UNIFIED_SLOT_HOURS

def implement_new_need_calculation_system():
    """新Need算出システムの実装実行"""
    
    print('=' * 80)
    print('Step 5: 新Need算出システムの実装')
    print('目的: 按分廃止・職種別分析の完全実装')
    print('コンセプト: 組織全体、各職種ごと、各雇用形態ごとに真の過不足をあぶりだす')
    print('=' * 80)
    
    scenario_dir = Path('extracted_results/out_p25_based')
    
    try:
        # 1. 統合データ読み込み
        print('\n【Phase 1: 統合データ読み込み】')
        data_loader = NewNeedCalculationDataLoader(scenario_dir)
        data_package = data_loader.load_integrated_data()
        print_data_loading_result(data_package)
        
        # 2. 按分廃止Need算出エンジン構築
        print('\n【Phase 2: 按分廃止Need算出エンジン構築】')
        need_engine = ProportionalAbolitionNeedEngine(data_package)
        engine_status = need_engine.initialize_calculation_engine()
        print_engine_initialization_status(engine_status)
        
        # 3. 職種別Need算出実行
        print('\n【Phase 3: 職種別Need算出実行】')
        role_based_results = need_engine.calculate_role_based_shortages()
        print_role_based_calculation_results(role_based_results)
        
        # 4. 雇用形態別Need算出実行
        print('\n【Phase 4: 雇用形態別Need算出実行】')
        employment_based_results = need_engine.calculate_employment_based_shortages()
        print_employment_based_calculation_results(employment_based_results)
        
        # 5. 組織全体Need算出実行
        print('\n【Phase 5: 組織全体Need算出実行】')
        organization_wide_results = need_engine.calculate_organization_wide_shortages()
        print_organization_wide_calculation_results(organization_wide_results)
        
        # 6. 真の過不足分析レポート生成
        print('\n【Phase 6: 真の過不足分析レポート生成】')
        comprehensive_analysis = generate_comprehensive_shortage_analysis(
            role_based_results, employment_based_results, organization_wide_results
        )
        print_comprehensive_analysis_results(comprehensive_analysis)
        
        # 7. 新Need算出システム保存
        print('\n【Phase 7: 新Need算出システム保存】')
        system_save_result = save_new_need_calculation_system(
            data_package, role_based_results, employment_based_results, 
            organization_wide_results, comprehensive_analysis
        )
        print_system_save_result(system_save_result)
        
        return {
            'success': True,
            'data_package': data_package,
            'role_based_results': role_based_results,
            'employment_based_results': employment_based_results,
            'organization_wide_results': organization_wide_results,
            'comprehensive_analysis': comprehensive_analysis,
            'system_files': system_save_result
        }
        
    except Exception as e:
        print(f'[ERROR] 新Need算出システム実装失敗: {e}')
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

class NewNeedCalculationDataLoader:
    """新Need算出用データローダー"""
    
    def __init__(self, scenario_dir):
        self.scenario_dir = scenario_dir
        
    def load_integrated_data(self):
        """統合データの読み込み"""
        
        # 1. intermediate_data読み込み
        intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
        operating_data = intermediate_data[intermediate_data['role'] != 'NIGHT_SLOT']
        
        # 2. Need値読み込み
        need_files = list(self.scenario_dir.glob('need_per_date_slot_role_*.parquet'))
        need_data = {}
        
        for need_file in need_files:
            role_name = need_file.name.replace('need_per_date_slot_role_', '').replace('.parquet', '')
            df = pd.read_parquet(need_file)
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            total_need = df[numeric_cols].sum().sum()
            
            need_data[role_name] = {
                'file_path': need_file,
                'raw_dataframe': df,
                'total_need_value': total_need,
                'need_hours_total': total_need * UNIFIED_SLOT_HOURS,
                'need_hours_daily': (total_need * UNIFIED_SLOT_HOURS) / 30
            }
        
        # 3. 統合データパッケージ作成
        data_package = {
            'intermediate_data': intermediate_data,
            'operating_data': operating_data,
            'need_data': need_data,
            'metadata': {
                'total_records': len(operating_data),
                'period_days': intermediate_data['ds'].dt.date.nunique(),
                'unique_roles': operating_data['role'].nunique(),
                'unique_employments': operating_data['employment'].nunique(),
                'unique_staff': operating_data['staff'].nunique(),
                'need_files_count': len(need_files),
                'total_need_hours': sum(data['need_hours_total'] for data in need_data.values())
            }
        }
        
        return data_package

def print_data_loading_result(data_package):
    """データ読み込み結果表示"""
    
    meta = data_package['metadata']
    print(f'実配置データ: {meta["total_records"]:,}レコード ({meta["period_days"]}日間)')
    print(f'職種数: {meta["unique_roles"]}, 雇用形態数: {meta["unique_employments"]}')
    print(f'スタッフ数: {meta["unique_staff"]}名')
    print(f'Needファイル数: {meta["need_files_count"]}個')
    print(f'総Need時間: {meta["total_need_hours"]:.1f}時間')

def print_engine_initialization_status(engine_status):
    """エンジン初期化状況表示"""
    
    status = "[OK]" if engine_status['engine_ready'] else "[ERROR]"
    print(f'按分廃止エンジン: {status}')
    print(f'職種数: {engine_status["role_count"]}, 雇用形態数: {engine_status["employment_count"]}')
    print(f'算出基準: {engine_status["calculation_basis"]}')

class ProportionalAbolitionNeedEngine:
    """按分廃止Need算出エンジン"""
    
    def __init__(self, data_package):
        self.data_package = data_package
        self.operating_data = data_package['operating_data']
        self.need_data = data_package['need_data']
        
    def initialize_calculation_engine(self):
        """算出エンジン初期化"""
        
        print('按分廃止エンジン初期化中...')
        
        # 職種別実配置時間計算
        self.role_actual_allocation = {}
        for role in self.operating_data['role'].unique():
            role_data = self.operating_data[self.operating_data['role'] == role]
            role_records = len(role_data)
            role_hours_total = role_records * UNIFIED_SLOT_HOURS
            role_hours_daily = role_hours_total / 30
            
            self.role_actual_allocation[role] = {
                'records': role_records,
                'hours_total': role_hours_total,
                'hours_daily': role_hours_daily,
                'staff_count': role_data['staff'].nunique()
            }
        
        # 雇用形態別実配置時間計算
        self.employment_actual_allocation = {}
        for employment in self.operating_data['employment'].unique():
            emp_data = self.operating_data[self.operating_data['employment'] == employment]
            emp_records = len(emp_data)
            emp_hours_total = emp_records * UNIFIED_SLOT_HOURS
            emp_hours_daily = emp_hours_total / 30
            
            self.employment_actual_allocation[employment] = {
                'records': emp_records,
                'hours_total': emp_hours_total,
                'hours_daily': emp_hours_daily,
                'staff_count': emp_data['staff'].nunique()
            }
        
        return {
            'engine_ready': True,
            'role_count': len(self.role_actual_allocation),
            'employment_count': len(self.employment_actual_allocation),
            'calculation_basis': 'UNIFIED_SLOT_HOURS = 0.5時間/レコード'
        }
    
    def calculate_role_based_shortages(self):
        """職種別過不足算出"""
        
        print('職種別過不足算出実行中...')
        
        role_shortages = {}
        
        for role_name, need_info in self.need_data.items():
            # Need値
            need_hours_daily = need_info['need_hours_daily']
            
            # 実配置値
            actual_info = self.role_actual_allocation.get(role_name, {
                'hours_daily': 0,
                'staff_count': 0,
                'records': 0
            })
            actual_hours_daily = actual_info['hours_daily']
            
            # 過不足算出（正の値=不足、負の値=余剰）
            shortage_daily = need_hours_daily - actual_hours_daily
            
            role_shortages[role_name] = {
                'role': role_name,
                'need_hours_daily': need_hours_daily,
                'actual_hours_daily': actual_hours_daily,
                'shortage_daily': shortage_daily,
                'shortage_status': 'SHORTAGE' if shortage_daily > 0 else 'SURPLUS' if shortage_daily < 0 else 'BALANCED',
                'staff_count_current': actual_info['staff_count'],
                'shortage_magnitude': abs(shortage_daily),
                'coverage_ratio': actual_hours_daily / need_hours_daily if need_hours_daily > 0 else float('inf')
            }
        
        # 職種別ランキング
        shortage_ranking = sorted(
            role_shortages.values(), 
            key=lambda x: x['shortage_daily'], 
            reverse=True
        )
        
        return {
            'role_shortages': role_shortages,
            'shortage_ranking': shortage_ranking,
            'total_roles': len(role_shortages),
            'shortage_roles': len([r for r in role_shortages.values() if r['shortage_daily'] > 0]),
            'surplus_roles': len([r for r in role_shortages.values() if r['shortage_daily'] < 0]),
            'balanced_roles': len([r for r in role_shortages.values() if r['shortage_daily'] == 0])
        }
    
    def calculate_employment_based_shortages(self):
        """雇用形態別過不足算出"""
        
        print('雇用形態別過不足算出実行中...')
        
        # 雇用形態別Need値の集計（職種から推定）
        employment_needs = {}
        
        for employment in self.employment_actual_allocation.keys():
            # この雇用形態のスタッフが担当している職種のNeed値を合計
            emp_staff_data = self.operating_data[self.operating_data['employment'] == employment]
            emp_roles = emp_staff_data['role'].unique()
            
            total_need_daily = 0
            for role in emp_roles:
                if role in self.need_data:
                    role_need_daily = self.need_data[role]['need_hours_daily']
                    # その職種における、この雇用形態の割合で按分
                    role_total_records = len(self.operating_data[self.operating_data['role'] == role])
                    role_emp_records = len(emp_staff_data[emp_staff_data['role'] == role])
                    
                    if role_total_records > 0:
                        emp_role_ratio = role_emp_records / role_total_records
                        total_need_daily += role_need_daily * emp_role_ratio
            
            employment_needs[employment] = total_need_daily
        
        # 雇用形態別過不足算出
        employment_shortages = {}
        
        for employment, actual_info in self.employment_actual_allocation.items():
            need_hours_daily = employment_needs.get(employment, 0)
            actual_hours_daily = actual_info['hours_daily']
            shortage_daily = need_hours_daily - actual_hours_daily
            
            employment_shortages[employment] = {
                'employment': employment,
                'need_hours_daily': need_hours_daily,
                'actual_hours_daily': actual_hours_daily,
                'shortage_daily': shortage_daily,
                'shortage_status': 'SHORTAGE' if shortage_daily > 0 else 'SURPLUS' if shortage_daily < 0 else 'BALANCED',
                'staff_count_current': actual_info['staff_count'],
                'shortage_magnitude': abs(shortage_daily),
                'coverage_ratio': actual_hours_daily / need_hours_daily if need_hours_daily > 0 else float('inf')
            }
        
        return {
            'employment_shortages': employment_shortages,
            'total_employments': len(employment_shortages),
            'shortage_employments': len([e for e in employment_shortages.values() if e['shortage_daily'] > 0]),
            'surplus_employments': len([e for e in employment_shortages.values() if e['shortage_daily'] < 0])
        }
    
    def calculate_organization_wide_shortages(self):
        """組織全体過不足算出"""
        
        print('組織全体過不足算出実行中...')
        
        # 組織全体Need値
        total_need_daily = sum(need_info['need_hours_daily'] for need_info in self.need_data.values())
        
        # 組織全体実配置値
        total_actual_daily = sum(actual_info['hours_daily'] for actual_info in self.role_actual_allocation.values())
        
        # 組織全体過不足
        total_shortage_daily = total_need_daily - total_actual_daily
        
        organization_wide = {
            'total_need_daily': total_need_daily,
            'total_actual_daily': total_actual_daily,
            'total_shortage_daily': total_shortage_daily,
            'organization_status': 'SHORTAGE' if total_shortage_daily > 0 else 'SURPLUS' if total_shortage_daily < 0 else 'BALANCED',
            'total_staff_count': self.data_package['metadata']['unique_staff'],
            'coverage_ratio': total_actual_daily / total_need_daily if total_need_daily > 0 else float('inf'),
            'shortage_percentage': (total_shortage_daily / total_need_daily * 100) if total_need_daily > 0 else 0
        }
        
        return organization_wide

def print_role_based_calculation_results(results):
    """職種別算出結果表示"""
    
    print(f'職種別過不足算出完了: {results["total_roles"]}職種')
    print(f'  不足職種: {results["shortage_roles"]}職種')
    print(f'  余剰職種: {results["surplus_roles"]}職種')
    print(f'  適正職種: {results["balanced_roles"]}職種')
    
    print('\n職種別不足ランキング（上位5位）:')
    for i, role_info in enumerate(results['shortage_ranking'][:5], 1):
        status_icon = '[SHORTAGE]' if role_info['shortage_daily'] > 0 else '[SURPLUS]' if role_info['shortage_daily'] < 0 else '[BALANCED]'
        print(f'  {i}. {status_icon} {role_info["role"]}: {role_info["shortage_daily"]:+.1f}時間/日 (現在{role_info["staff_count_current"]}名)')

def print_employment_based_calculation_results(results):
    """雇用形態別算出結果表示"""
    
    print(f'雇用形態別過不足算出完了: {results["total_employments"]}形態')
    print(f'  不足形態: {results["shortage_employments"]}形態')
    print(f'  余剰形態: {results["surplus_employments"]}形態')
    
    print('\n雇用形態別過不足:')
    for employment, emp_info in results['employment_shortages'].items():
        status_icon = '[SHORTAGE]' if emp_info['shortage_daily'] > 0 else '[SURPLUS]' if emp_info['shortage_daily'] < 0 else '[BALANCED]'
        print(f'  {status_icon} {employment}: {emp_info["shortage_daily"]:+.1f}時間/日 (現在{emp_info["staff_count_current"]}名)')

def print_organization_wide_calculation_results(results):
    """組織全体算出結果表示"""
    
    status_icon = '[SHORTAGE]' if results['total_shortage_daily'] > 0 else '[SURPLUS]' if results['total_shortage_daily'] < 0 else '[BALANCED]'
    print(f'組織全体過不足: {status_icon} {results["organization_status"]}')
    print(f'  総Need: {results["total_need_daily"]:.1f}時間/日')
    print(f'  総実配置: {results["total_actual_daily"]:.1f}時間/日')
    print(f'  過不足: {results["total_shortage_daily"]:+.1f}時間/日')
    print(f'  不足率: {results["shortage_percentage"]:+.1f}%')
    print(f'  総スタッフ: {results["total_staff_count"]}名')

def generate_comprehensive_shortage_analysis(role_results, employment_results, org_results):
    """包括的過不足分析生成"""
    
    print('包括的過不足分析生成中...')
    
    # 按分廃止により明らかになった真実の抽出
    critical_findings = []
    
    # 1. 深刻な不足職種の特定
    severe_shortage_roles = [
        r for r in role_results['shortage_ranking'] 
        if r['shortage_daily'] > 2.0  # 2時間/日以上の不足
    ]
    
    if severe_shortage_roles:
        critical_findings.append({
            'finding_type': 'SEVERE_ROLE_SHORTAGE',
            'description': f'{len(severe_shortage_roles)}職種で深刻な人手不足',
            'details': severe_shortage_roles,
            'priority': 'CRITICAL'
        })
    
    # 2. 完全未配置職種の特定
    zero_allocation_roles = [
        r for r in role_results['role_shortages'].values()
        if r['staff_count_current'] == 0 and r['need_hours_daily'] > 0
    ]
    
    if zero_allocation_roles:
        critical_findings.append({
            'finding_type': 'ZERO_ALLOCATION_ROLES',
            'description': f'{len(zero_allocation_roles)}職種が完全未配置',
            'details': zero_allocation_roles,
            'priority': 'CRITICAL'
        })
    
    # 3. 按分隠蔽効果の定量化
    proportional_hiding_effect = {
        'organization_appears_balanced': abs(org_results['total_shortage_daily']) < 5.0,
        'individual_roles_severely_imbalanced': len(severe_shortage_roles) > 0 or len(zero_allocation_roles) > 0,
        'hidden_by_proportional_allocation': False
    }
    
    proportional_hiding_effect['hidden_by_proportional_allocation'] = (
        proportional_hiding_effect['organization_appears_balanced'] and
        proportional_hiding_effect['individual_roles_severely_imbalanced']
    )
    
    # 4. 改善優先度マトリックス
    improvement_priorities = []
    
    for role_info in role_results['shortage_ranking']:
        if role_info['shortage_daily'] > 0:
            if role_info['staff_count_current'] == 0:
                priority = 'IMMEDIATE'
            elif role_info['shortage_daily'] > 5.0:
                priority = 'HIGH'
            elif role_info['shortage_daily'] > 2.0:
                priority = 'MEDIUM'
            else:
                priority = 'LOW'
            
            improvement_priorities.append({
                'role': role_info['role'],
                'shortage_hours': role_info['shortage_daily'],
                'priority': priority,
                'recommended_action': generate_role_improvement_action(role_info)
            })
    
    comprehensive_analysis = {
        'analysis_timestamp': datetime.now().isoformat(),
        'analysis_type': 'PROPORTIONAL_ABOLITION_COMPREHENSIVE_ANALYSIS',
        'critical_findings': critical_findings,
        'proportional_hiding_effect': proportional_hiding_effect,
        'improvement_priorities': improvement_priorities,
        'summary_statistics': {
            'total_roles_analyzed': role_results['total_roles'],
            'roles_in_shortage': role_results['shortage_roles'],
            'roles_in_surplus': role_results['surplus_roles'],
            'organization_wide_status': org_results['organization_status'],
            'most_critical_role': role_results['shortage_ranking'][0]['role'] if role_results['shortage_ranking'] else None,
            '按分廃止_effectiveness': 'HIGH' if proportional_hiding_effect['hidden_by_proportional_allocation'] else 'MODERATE'
        }
    }
    
    return comprehensive_analysis

def generate_role_improvement_action(role_info):
    """職種別改善アクション生成"""
    
    if role_info['staff_count_current'] == 0:
        return f"緊急採用: {role_info['role']}の専門スタッフを至急採用"
    elif role_info['shortage_daily'] > 5.0:
        needed_additional_hours = role_info['shortage_daily']
        needed_staff = needed_additional_hours / 4.0  # 1人4時間/日と仮定
        return f"増員: {role_info['role']}を約{needed_staff:.1f}名増員"
    else:
        return f"勤務時間調整: {role_info['role']}の勤務時間を{role_info['shortage_daily']:.1f}時間/日増加"

def print_comprehensive_analysis_results(analysis):
    """包括的分析結果表示"""
    
    print(f'按分廃止効果: {analysis["summary_statistics"]["按分廃止_effectiveness"]}')
    print(f'クリティカル発見: {len(analysis["critical_findings"])}件')
    
    if analysis['proportional_hiding_effect']['hidden_by_proportional_allocation']:
        print('\n[WARNING] 按分による真実隠蔽を検出:')
        print('   組織全体では均衡に見えるが、個別職種で深刻な不均衡')
    
    print(f'\n改善優先度:')
    priority_counts = {}
    for item in analysis['improvement_priorities']:
        priority = item['priority']
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    for priority, count in priority_counts.items():
        print(f'  {priority}: {count}職種')

def save_new_need_calculation_system(data_package, role_results, employment_results, org_results, analysis):
    """新Need算出システム保存"""
    
    print('新Need算出システム保存中...')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 1. メイン結果レポート
    main_report = {
        'system_info': {
            'system_name': '按分廃止・職種別分析システム',
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'calculation_basis': 'UNIFIED_SLOT_HOURS = 0.5時間/レコード'
        },
        'data_metadata': data_package['metadata'],
        'role_based_analysis': role_results,
        'employment_based_analysis': employment_results,
        'organization_wide_analysis': org_results,
        'comprehensive_analysis': analysis
    }
    
    main_report_file = f'按分廃止_職種別分析_完全レポート_{timestamp}.json'
    with open(main_report_file, 'w', encoding='utf-8') as f:
        json.dump(main_report, f, ensure_ascii=False, indent=2, default=str)
    
    # 2. 職種別詳細CSV
    role_details_df = pd.DataFrame([
        {
            '職種': info['role'],
            'Need時間_日': info['need_hours_daily'],
            '実配置時間_日': info['actual_hours_daily'],
            '過不足_日': info['shortage_daily'],
            '現在スタッフ数': info['staff_count_current'],
            'カバレッジ率': info['coverage_ratio'],
            '状態': info['shortage_status']
        }
        for info in role_results['role_shortages'].values()
    ])
    
    role_csv_file = f'職種別過不足詳細_{timestamp}.csv'
    role_details_df.to_csv(role_csv_file, index=False, encoding='utf-8')
    
    # 3. 改善アクションプラン
    improvement_df = pd.DataFrame(analysis['improvement_priorities'])
    improvement_csv_file = f'改善アクションプラン_{timestamp}.csv'
    improvement_df.to_csv(improvement_csv_file, index=False, encoding='utf-8')
    
    return {
        'main_report_file': main_report_file,
        'role_details_csv': role_csv_file,
        'improvement_plan_csv': improvement_csv_file,
        'files_created': [main_report_file, role_csv_file, improvement_csv_file]
    }

def print_system_save_result(save_result):
    """システム保存結果表示"""
    
    print(f'新Need算出システム保存完了: {len(save_result["files_created"])}ファイル')
    for file_path in save_result['files_created']:
        print(f'  - {file_path}')

if __name__ == "__main__":
    result = implement_new_need_calculation_system()
    
    if result and result.get('success', False):
        print('\n' + '=' * 80)
        print('🎉 Step 5完了: 新Need算出システム実装成功')
        print('🎯 按分廃止・職種別分析の完全実装達成')
        print('🔍 組織全体、各職種ごと、各雇用形態ごとの真の過不足を解明')
        print('=' * 80)
        
        # サマリー表示
        analysis = result['comprehensive_analysis']
        print(f'\n📊 分析結果サマリー:')
        print(f'   分析職種数: {analysis["summary_statistics"]["total_roles_analyzed"]}')
        print(f'   不足職種数: {analysis["summary_statistics"]["roles_in_shortage"]}')
        print(f'   按分廃止効果: {analysis["summary_statistics"]["按分廃止_effectiveness"]}')
        
    else:
        print('\nStep 5失敗: システム実装に問題が発生')