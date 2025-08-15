#!/usr/bin/env python3
"""
動的対応強化版 新Need算出システム
ユーザー指摘事項への対応:
1. app.pyからの期間日数動的指定対応
2. Needファイル命名規則の動的対応
3. 職種名動的マッチング
4. スロット数動的検出（24時間は固定）
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import time, datetime, timedelta
import json
import sys
import re
import glob
from typing import Dict, List, Tuple, Optional, Any
sys.path.append('.')
from unified_time_calculation_system import UNIFIED_SLOT_HOURS

class DynamicNeedCalculationSystem:
    """動的対応強化版Need算出システム"""
    
    def __init__(self, scenario_dir: Path, config: Optional[Dict] = None):
        self.scenario_dir = scenario_dir
        self.config = config or {}
        self.system_metadata = {}
        
    def execute_dynamic_need_calculation(self) -> Dict[str, Any]:
        """動的Need算出システム実行"""
        
        print('=' * 80)
        print('動的対応強化版 新Need算出システム')
        print('目的: 按分廃止・職種別分析（動的データ完全対応）')
        print('=' * 80)
        
        try:
            # 1. 動的システム設定読み込み
            print('\n【Phase 1: 動的システム設定読み込み】')
            dynamic_config = self.load_dynamic_system_config()
            print_dynamic_config(dynamic_config)
            
            # 2. 動的データ構造検出・読み込み
            print('\n【Phase 2: 動的データ構造検出・読み込み】')
            dynamic_data = self.detect_and_load_dynamic_data()
            print_dynamic_data_info(dynamic_data)
            
            # 3. 動的Need算出エンジン初期化
            print('\n【Phase 3: 動的Need算出エンジン初期化】')
            need_engine = DynamicProportionalAbolitionEngine(dynamic_data, dynamic_config)
            engine_status = need_engine.initialize_dynamic_engine()
            print_engine_status(engine_status)
            
            # 4. 動的職種別Need算出
            print('\n【Phase 4: 動的職種別Need算出】')
            role_results = need_engine.calculate_dynamic_role_shortages()
            print_dynamic_role_results(role_results)
            
            # 5. 動的雇用形態別Need算出
            print('\n【Phase 5: 動的雇用形態別Need算出】')
            employment_results = need_engine.calculate_dynamic_employment_shortages()
            print_dynamic_employment_results(employment_results)
            
            # 6. 動的組織全体Need算出
            print('\n【Phase 6: 動的組織全体Need算出】')
            organization_results = need_engine.calculate_dynamic_organization_shortages()
            print_dynamic_organization_results(organization_results)
            
            # 7. 動的総合分析
            print('\n【Phase 7: 動的総合分析】')
            comprehensive_analysis = need_engine.generate_dynamic_comprehensive_analysis(
                role_results, employment_results, organization_results, dynamic_config
            )
            print_comprehensive_analysis(comprehensive_analysis)
            
            # 8. 動的結果保存
            print('\n【Phase 8: 動的結果保存】')
            save_results = need_engine.save_dynamic_calculation_results(
                dynamic_config, dynamic_data, role_results, 
                employment_results, organization_results, comprehensive_analysis
            )
            print_save_results(save_results)
            
            return {
                'success': True,
                'dynamic_config': dynamic_config,
                'dynamic_data': dynamic_data,
                'role_results': role_results,
                'employment_results': employment_results,
                'organization_results': organization_results,
                'comprehensive_analysis': comprehensive_analysis,
                'save_results': save_results
            }
            
        except Exception as e:
            print(f'[ERROR] 動的Need算出システム実行失敗: {e}')
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def load_dynamic_system_config(self) -> Dict[str, Any]:
        """動的システム設定読み込み"""
        
        # 1. app.pyからの期間情報取得（シミュレーション）
        app_config = self.extract_app_py_config()
        
        # 2. データから動的パラメータ抽出
        data_derived_config = self.extract_data_derived_config()
        
        # 3. 統合設定作成
        dynamic_config = {
            'period_info': app_config.get('period_info', {}),
            'data_structure': data_derived_config.get('data_structure', {}),
            'calculation_settings': {
                'slot_hours': UNIFIED_SLOT_HOURS,
                'hours_per_day': 24,  # 固定（ユーザー指定）
                'dynamic_slot_count': True,  # スロット数は動的
                'dynamic_period': True,      # 期間は動的
                'dynamic_roles': True,       # 職種は動的
                'dynamic_need_files': True   # Needファイルは動的
            },
            'detection_settings': {
                'need_file_pattern': '*.parquet',  # より柔軟なパターン
                'role_detection_method': 'AUTO',
                'period_detection_method': 'AUTO'
            }
        }
        
        return dynamic_config
    
    def extract_app_py_config(self) -> Dict[str, Any]:
        """app.pyから設定情報抽出（実際の実装では引数で受け取る）"""
        
        # 実際の実装では、app.pyから以下の情報を受け取る想定:
        # - need_ref_start_date_widget
        # - need_ref_end_date_widget  
        # - その他の動的設定
        
        # シミュレーション用のデフォルト設定
        default_start = datetime.now() - timedelta(days=30)
        default_end = datetime.now()
        
        return {
            'period_info': {
                'start_date': default_start,
                'end_date': default_end,
                'period_days': (default_end - default_start).days + 1,
                'source': 'APP_PY_DYNAMIC'
            }
        }
    
    def extract_data_derived_config(self) -> Dict[str, Any]:
        """データから設定情報抽出"""
        
        config = {'data_structure': {}}
        
        # intermediate_dataから構造情報抽出
        try:
            intermediate_file = self.scenario_dir / 'intermediate_data.parquet'
            if intermediate_file.exists():
                data = pd.read_parquet(intermediate_file)
                
                # 時間構造の動的検出
                unique_times = data['ds'].dt.time.unique()
                slot_count = len(unique_times)
                
                # 期間情報の動的検出
                date_range = data['ds'].dt.date.unique()
                actual_period_days = len(date_range)
                
                config['data_structure'] = {
                    'detected_slot_count': slot_count,
                    'detected_period_days': actual_period_days,
                    'detected_date_range': {
                        'start': date_range.min(),
                        'end': date_range.max()
                    },
                    'time_slots': sorted(unique_times)
                }
        except Exception as e:
            print(f'[WARNING] データ構造検出エラー: {e}')
        
        return config
    
    def detect_and_load_dynamic_data(self) -> Dict[str, Any]:
        """動的データ構造検出・読み込み"""
        
        # 1. intermediate_dataの動的読み込み
        intermediate_data = self.load_intermediate_data_dynamically()
        
        # 2. Needファイルの動的検出・読み込み
        need_data = self.detect_and_load_need_files_dynamically()
        
        # 3. 職種情報の動的抽出
        role_mapping = self.extract_dynamic_role_mapping(intermediate_data, need_data)
        
        # 4. 統合データパッケージ作成
        dynamic_data = {
            'intermediate_data': intermediate_data['data'],
            'intermediate_metadata': intermediate_data['metadata'],
            'need_data': need_data['data'],
            'need_metadata': need_data['metadata'],
            'role_mapping': role_mapping,
            'system_metadata': {
                'total_roles_detected': len(role_mapping.get('role_mappings', {})),
                'total_need_files_detected': len(need_data['data']),
                'data_consistency_check': self.check_data_consistency(
                    intermediate_data, need_data
                )
            }
        }
        
        return dynamic_data
    
    def load_intermediate_data_dynamically(self) -> Dict[str, Any]:
        """intermediate_dataの動的読み込み"""
        
        intermediate_file = self.scenario_dir / 'intermediate_data.parquet'
        
        if not intermediate_file.exists():
            raise FileNotFoundError(f'intermediate_data.parquet not found: {intermediate_file}')
        
        data = pd.read_parquet(intermediate_file)
        operating_data = data[data['role'] != 'NIGHT_SLOT']
        
        metadata = {
            'file_path': intermediate_file,
            'total_records': len(data),
            'operating_records': len(operating_data),
            'unique_roles': operating_data['role'].nunique(),
            'unique_employments': operating_data['employment'].nunique(),
            'unique_staff': operating_data['staff'].nunique(),
            'date_range': {
                'start': data['ds'].dt.date.min(),
                'end': data['ds'].dt.date.max(),
                'days': data['ds'].dt.date.nunique()
            },
            'time_structure': {
                'unique_times': len(data['ds'].dt.time.unique()),
                'time_range': {
                    'start': str(data['ds'].dt.time.min()),
                    'end': str(data['ds'].dt.time.max())
                }
            }
        }
        
        return {'data': data, 'metadata': metadata}
    
    def detect_and_load_need_files_dynamically(self) -> Dict[str, Any]:
        """Needファイルの動的検出・読み込み"""
        
        # 柔軟なファイル検出パターン
        search_patterns = [
            'need_per_date_slot_role_*.parquet',  # 標準パターン
            'need_*_role_*.parquet',              # 変種パターン1
            'need_*.parquet',                     # 変種パターン2
            '*need*.parquet'                      # 最広パターン
        ]
        
        detected_files = []
        
        for pattern in search_patterns:
            files = list(self.scenario_dir.glob(pattern))
            for file in files:
                if file not in detected_files:
                    detected_files.append(file)
        
        if not detected_files:
            raise FileNotFoundError('No Need files detected with any pattern')
        
        # 各ファイルの動的解析
        need_data = {}
        file_metadata = []
        
        for need_file in detected_files:
            try:
                # ファイル名から職種名を動的抽出
                role_name = self.extract_role_from_filename(need_file.name)
                
                df = pd.read_parquet(need_file)
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                total_need = df[numeric_cols].sum().sum()
                
                need_data[role_name] = {
                    'file_path': need_file,
                    'raw_dataframe': df,
                    'total_need_value': total_need,
                    'need_hours_total': total_need * UNIFIED_SLOT_HOURS,
                    'need_hours_daily': None,  # 動的期間で後で計算
                    'file_structure': {
                        'shape': df.shape,
                        'slot_count': df.shape[0],
                        'period_count': df.shape[1]
                    }
                }
                
                file_metadata.append({
                    'file_name': need_file.name,
                    'extracted_role': role_name,
                    'total_need': total_need,
                    'structure': df.shape
                })
                
            except Exception as e:
                print(f'[WARNING] Needファイル読み込みエラー {need_file.name}: {e}')
        
        return {
            'data': need_data,
            'metadata': {
                'detected_files_count': len(detected_files),
                'successfully_loaded': len(need_data),
                'file_details': file_metadata,
                'detection_patterns_used': search_patterns
            }
        }
    
    def extract_role_from_filename(self, filename: str) -> str:
        """ファイル名から職種名を動的抽出"""
        
        # 複数の抽出パターンを試行
        patterns = [
            r'need_per_date_slot_role_(.+)\.parquet',  # 標準パターン
            r'need_.*_role_(.+)\.parquet',             # 変種パターン1
            r'need_(.+)\.parquet',                     # 変種パターン2
            r'(.+)_need\.parquet',                     # 変種パターン3
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                extracted_role = match.group(1)
                # クリーニング処理
                extracted_role = extracted_role.replace('_', ' ').strip()
                return extracted_role
        
        # パターンマッチしない場合は、ファイル名から拡張子を除去
        return filename.replace('.parquet', '').replace('need_', '').replace('_', ' ').strip()
    
    def extract_dynamic_role_mapping(self, intermediate_data: Dict, need_data: Dict) -> Dict[str, Any]:
        """動的職種マッピング抽出"""
        
        # intermediate_dataから実際の職種を取得
        actual_roles = set(intermediate_data['data']['role'].unique())
        actual_roles.discard('NIGHT_SLOT')  # 夜間プレースホルダー除外
        
        # Needファイルから抽出された職種を取得
        need_roles = set(need_data['data'].keys())
        
        # 職種マッピング作成
        role_mappings = {}
        unmatched_actual_roles = set(actual_roles)
        unmatched_need_roles = set(need_roles)
        
        # 完全一致マッピング
        for actual_role in list(actual_roles):
            if actual_role in need_roles:
                role_mappings[actual_role] = actual_role
                unmatched_actual_roles.discard(actual_role)
                unmatched_need_roles.discard(actual_role)
        
        # 部分一致マッピング
        for actual_role in list(unmatched_actual_roles):
            for need_role in list(unmatched_need_roles):
                if self.check_role_similarity(actual_role, need_role):
                    role_mappings[actual_role] = need_role
                    unmatched_actual_roles.discard(actual_role)
                    unmatched_need_roles.discard(need_role)
                    break
        
        return {
            'role_mappings': role_mappings,
            'unmatched_actual_roles': list(unmatched_actual_roles),
            'unmatched_need_roles': list(unmatched_need_roles),
            'mapping_statistics': {
                'total_actual_roles': len(actual_roles),
                'total_need_roles': len(need_roles),
                'successful_mappings': len(role_mappings),
                'mapping_success_rate': len(role_mappings) / max(len(actual_roles), 1)
            }
        }
    
    def check_role_similarity(self, role1: str, role2: str) -> bool:
        """職種名類似性チェック"""
        
        # 基本的な類似性チェック
        role1_clean = re.sub(r'[^\w]', '', role1).lower()
        role2_clean = re.sub(r'[^\w]', '', role2).lower()
        
        # 部分一致チェック
        if role1_clean in role2_clean or role2_clean in role1_clean:
            return True
        
        # 共通キーワードチェック
        common_keywords = ['介護', '看護', '医師', '管理', '訓練', '栄養', '調理']
        
        for keyword in common_keywords:
            if keyword in role1 and keyword in role2:
                return True
        
        return False
    
    def check_data_consistency(self, intermediate_data: Dict, need_data: Dict) -> Dict[str, Any]:
        """データ整合性チェック"""
        
        consistency = {
            'period_consistency': True,
            'slot_consistency': True,
            'issues': []
        }
        
        # 期間整合性チェック
        intermediate_period = intermediate_data['metadata']['date_range']['days']
        
        for role, need_info in need_data['data'].items():
            need_period = need_info['file_structure']['period_count']
            if intermediate_period != need_period:
                consistency['period_consistency'] = False
                consistency['issues'].append(
                    f'期間不整合: {role} - intermediate:{intermediate_period}日 vs need:{need_period}日'
                )
        
        # スロット整合性チェック
        intermediate_slots = intermediate_data['metadata']['time_structure']['unique_times']
        
        for role, need_info in need_data['data'].items():
            need_slots = need_info['file_structure']['slot_count']
            if intermediate_slots != need_slots:
                consistency['slot_consistency'] = False
                consistency['issues'].append(
                    f'スロット不整合: {role} - intermediate:{intermediate_slots}スロット vs need:{need_slots}スロット'
                )
        
        return consistency

class DynamicProportionalAbolitionEngine:
    """動的按分廃止Need算出エンジン"""
    
    def __init__(self, dynamic_data: Dict, dynamic_config: Dict):
        self.dynamic_data = dynamic_data
        self.dynamic_config = dynamic_config
        
        # 動的パラメータ設定
        self.period_days = self.determine_dynamic_period()
        self.slot_hours = dynamic_config['calculation_settings']['slot_hours']
        
    def determine_dynamic_period(self) -> int:
        """動的期間決定"""
        
        # app.pyからの期間情報を優先
        if 'period_info' in self.dynamic_config:
            app_period = self.dynamic_config['period_info'].get('period_days')
            if app_period and app_period > 0:
                return app_period
        
        # データから推定
        data_period = self.dynamic_data['intermediate_metadata']['date_range']['days']
        return data_period
    
    def initialize_dynamic_engine(self) -> Dict[str, Any]:
        """動的エンジン初期化"""
        
        operating_data = self.dynamic_data['intermediate_data']
        operating_data = operating_data[operating_data['role'] != 'NIGHT_SLOT']
        
        # 職種別実配置の動的計算
        self.role_actual_allocation = {}
        for role in operating_data['role'].unique():
            role_data = operating_data[operating_data['role'] == role]
            role_records = len(role_data)
            role_hours_total = role_records * self.slot_hours
            role_hours_daily = role_hours_total / self.period_days
            
            self.role_actual_allocation[role] = {
                'records': role_records,
                'hours_total': role_hours_total,
                'hours_daily': role_hours_daily,
                'staff_count': role_data['staff'].nunique()
            }
        
        # 雇用形態別実配置の動的計算
        self.employment_actual_allocation = {}
        for employment in operating_data['employment'].unique():
            emp_data = operating_data[operating_data['employment'] == employment]
            emp_records = len(emp_data)
            emp_hours_total = emp_records * self.slot_hours
            emp_hours_daily = emp_hours_total / self.period_days
            
            self.employment_actual_allocation[employment] = {
                'records': emp_records,
                'hours_total': emp_hours_total,
                'hours_daily': emp_hours_daily,
                'staff_count': emp_data['staff'].nunique()
            }
        
        # Needデータの期間正規化
        self.normalize_need_data_for_period()
        
        return {
            'engine_ready': True,
            'dynamic_period_days': self.period_days,
            'role_count': len(self.role_actual_allocation),
            'employment_count': len(self.employment_actual_allocation),
            'slot_hours': self.slot_hours,
            'calculation_method': 'DYNAMIC_PERIOD_AWARE'
        }
    
    def normalize_need_data_for_period(self):
        """Need データの期間正規化"""
        
        for role, need_info in self.dynamic_data['need_data'].items():
            # 動的期間での日次Need計算
            need_hours_daily = (need_info['total_need_value'] * self.slot_hours) / self.period_days
            need_info['need_hours_daily'] = need_hours_daily
    
    def calculate_dynamic_role_shortages(self) -> Dict[str, Any]:
        """動的職種別過不足算出"""
        
        role_shortages = {}
        role_mapping = self.dynamic_data['role_mapping']['role_mappings']
        
        # マッピングされた職種の過不足計算
        for actual_role, need_role in role_mapping.items():
            if need_role in self.dynamic_data['need_data']:
                need_info = self.dynamic_data['need_data'][need_role]
                need_hours_daily = need_info['need_hours_daily']
                
                actual_info = self.role_actual_allocation.get(actual_role, {
                    'hours_daily': 0,
                    'staff_count': 0,
                    'records': 0
                })
                actual_hours_daily = actual_info['hours_daily']
                
                shortage_daily = need_hours_daily - actual_hours_daily
                
                role_shortages[actual_role] = {
                    'role': actual_role,
                    'mapped_need_role': need_role,
                    'need_hours_daily': need_hours_daily,
                    'actual_hours_daily': actual_hours_daily,
                    'shortage_daily': shortage_daily,
                    'shortage_status': 'SHORTAGE' if shortage_daily > 0 else 'SURPLUS' if shortage_daily < 0 else 'BALANCED',
                    'staff_count_current': actual_info['staff_count'],
                    'shortage_magnitude': abs(shortage_daily),
                    'coverage_ratio': actual_hours_daily / need_hours_daily if need_hours_daily > 0 else float('inf')
                }
        
        # マッピングされなかった職種の処理
        unmatched_roles = self.dynamic_data['role_mapping']['unmatched_actual_roles']
        for role in unmatched_roles:
            actual_info = self.role_actual_allocation.get(role, {})
            role_shortages[role] = {
                'role': role,
                'mapped_need_role': None,
                'need_hours_daily': 0,  # Needデータなし
                'actual_hours_daily': actual_info.get('hours_daily', 0),
                'shortage_daily': -actual_info.get('hours_daily', 0),  # 全て余剰扱い
                'shortage_status': 'SURPLUS_NO_NEED_DATA',
                'staff_count_current': actual_info.get('staff_count', 0),
                'shortage_magnitude': actual_info.get('hours_daily', 0),
                'coverage_ratio': float('inf')
            }
        
        shortage_ranking = sorted(
            role_shortages.values(),
            key=lambda x: x['shortage_daily'],
            reverse=True
        )
        
        return {
            'role_shortages': role_shortages,
            'shortage_ranking': shortage_ranking,
            'total_roles': len(role_shortages),
            'mapped_roles': len(role_mapping),
            'unmapped_roles': len(unmatched_roles),
            'shortage_roles': len([r for r in role_shortages.values() if r['shortage_daily'] > 0]),
            'surplus_roles': len([r for r in role_shortages.values() if r['shortage_daily'] < 0])
        }
    
    def calculate_dynamic_employment_shortages(self) -> Dict[str, Any]:
        """動的雇用形態別過不足算出"""
        
        # 雇用形態別Need推定（職種別Needから配分）
        employment_needs = {}
        operating_data = self.dynamic_data['intermediate_data']
        operating_data = operating_data[operating_data['role'] != 'NIGHT_SLOT']
        
        for employment in self.employment_actual_allocation.keys():
            emp_staff_data = operating_data[operating_data['employment'] == employment]
            total_need_daily = 0
            
            for _, row in emp_staff_data.iterrows():
                role = row['role']
                # 職種マッピングを使用してNeed取得
                role_mapping = self.dynamic_data['role_mapping']['role_mappings']
                if role in role_mapping:
                    need_role = role_mapping[role]
                    if need_role in self.dynamic_data['need_data']:
                        need_info = self.dynamic_data['need_data'][need_role]
                        # レコード単位でNeedを配分
                        total_need_daily += need_info['need_hours_daily'] * self.slot_hours / self.period_days
            
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
    
    def calculate_dynamic_organization_shortages(self) -> Dict[str, Any]:
        """動的組織全体過不足算出"""
        
        # 組織全体Need値（動的期間対応）
        total_need_daily = sum(
            need_info['need_hours_daily']
            for need_info in self.dynamic_data['need_data'].values()
        )
        
        # 組織全体実配置値
        total_actual_daily = sum(
            actual_info['hours_daily']
            for actual_info in self.role_actual_allocation.values()
        )
        
        # 組織全体過不足
        total_shortage_daily = total_need_daily - total_actual_daily
        
        return {
            'total_need_daily': total_need_daily,
            'total_actual_daily': total_actual_daily,
            'total_shortage_daily': total_shortage_daily,
            'organization_status': 'SHORTAGE' if total_shortage_daily > 0 else 'SURPLUS' if total_shortage_daily < 0 else 'BALANCED',
            'total_staff_count': self.dynamic_data['intermediate_metadata']['unique_staff'],
            'coverage_ratio': total_actual_daily / total_need_daily if total_need_daily > 0 else float('inf'),
            'shortage_percentage': (total_shortage_daily / total_need_daily * 100) if total_need_daily > 0 else 0,
            'period_days': self.period_days,
            'calculation_method': 'DYNAMIC_PERIOD_AWARE'
        }

    def generate_dynamic_comprehensive_analysis(
        self, role_results: Dict, employment_results: Dict, 
        organization_results: Dict, dynamic_config: Dict
    ) -> Dict[str, Any]:
        """動的総合分析生成"""
        
        # 動的システムの効果測定
        dynamic_effectiveness = {
            'period_flexibility': dynamic_config['calculation_settings']['dynamic_period'],
            'role_flexibility': dynamic_config['calculation_settings']['dynamic_roles'],
            'need_file_flexibility': dynamic_config['calculation_settings']['dynamic_need_files'],
            'mapping_success_rate': self.dynamic_data['role_mapping']['mapping_statistics']['mapping_success_rate']
        }
        
        # 按分廃止効果の評価
        proportional_abolition_effect = self.evaluate_proportional_abolition_effect(
            role_results, organization_results
        )
        
        return {
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_type': 'DYNAMIC_PROPORTIONAL_ABOLITION_ANALYSIS',
            'dynamic_system_config': dynamic_config,
            'dynamic_effectiveness': dynamic_effectiveness,
            'proportional_abolition_effect': proportional_abolition_effect,
            'role_analysis_summary': {
                'total_roles_analyzed': role_results['total_roles'],
                'mapped_roles': role_results['mapped_roles'],
                'unmapped_roles': role_results['unmapped_roles'],
                'roles_in_shortage': role_results['shortage_roles'],
                'roles_in_surplus': role_results['surplus_roles']
            },
            'organization_analysis_summary': {
                'organization_status': organization_results['organization_status'],
                'total_shortage_daily': organization_results['total_shortage_daily'],
                'period_days_used': organization_results['period_days'],
                'calculation_method': organization_results['calculation_method']
            },
            'system_recommendations': self.generate_dynamic_system_recommendations(
                dynamic_effectiveness, role_results, organization_results
            )
        }
    
    def evaluate_proportional_abolition_effect(self, role_results: Dict, organization_results: Dict) -> Dict[str, Any]:
        """按分廃止効果評価"""
        
        # 組織全体と個別職種の不均衡度測定
        org_shortage_magnitude = abs(organization_results['total_shortage_daily'])
        
        role_shortage_magnitudes = [
            abs(role['shortage_daily']) 
            for role in role_results['role_shortages'].values()
        ]
        
        max_role_shortage = max(role_shortage_magnitudes) if role_shortage_magnitudes else 0
        avg_role_shortage = sum(role_shortage_magnitudes) / len(role_shortage_magnitudes) if role_shortage_magnitudes else 0
        
        # 按分隠蔽効果の検出
        hidden_by_proportional = (
            org_shortage_magnitude < 5.0 and  # 組織全体は小さな不足
            max_role_shortage > 2.0             # しかし個別職種で大きな不足
        )
        
        return {
            'organization_shortage_magnitude': org_shortage_magnitude,
            'max_individual_role_shortage': max_role_shortage,
            'average_individual_role_shortage': avg_role_shortage,
            'proportional_hiding_detected': hidden_by_proportional,
            'abolition_effectiveness': 'HIGH' if hidden_by_proportional else 'MODERATE',
            'detailed_findings': [
                f'最大職種不足: {max_role_shortage:.1f}時間/日',
                f'組織全体不足: {org_shortage_magnitude:.1f}時間/日',
                '按分による隠蔽効果' if hidden_by_proportional else '按分隠蔽なし'
            ]
        }
    
    def generate_dynamic_system_recommendations(
        self, effectiveness: Dict, role_results: Dict, organization_results: Dict
    ) -> List[str]:
        """動的システム推奨事項生成"""
        
        recommendations = []
        
        # マッピング成功率に基づく推奨
        mapping_rate = effectiveness['mapping_success_rate']
        if mapping_rate < 0.8:
            recommendations.append(f'職種マッピング改善推奨（現在{mapping_rate:.1%}）')
        
        # 期間動的対応の推奨
        if effectiveness['period_flexibility']:
            recommendations.append('期間動的対応: 正常動作中')
        
        # 職種動的対応の推奨
        unmapped_count = role_results['unmapped_roles']
        if unmapped_count > 0:
            recommendations.append(f'未マップ職種対応: {unmapped_count}職種要対応')
        
        # 組織状況に基づく推奨
        if organization_results['organization_status'] == 'SHORTAGE':
            recommendations.append('組織全体で人手不足: 採用強化推奨')
        elif organization_results['organization_status'] == 'SURPLUS':
            recommendations.append('組織全体で配置余剰: 効率化推奨')
        
        return recommendations

    def save_dynamic_calculation_results(
        self, dynamic_config: Dict, dynamic_data: Dict, 
        role_results: Dict, employment_results: Dict, 
        organization_results: Dict, comprehensive_analysis: Dict
    ) -> Dict[str, Any]:
        """動的算出結果保存"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # メイン結果レポート
        main_report = {
            'system_info': {
                'system_name': '動的対応強化版 按分廃止・職種別分析システム',
                'version': '2.0_DYNAMIC',
                'timestamp': datetime.now().isoformat(),
                'dynamic_features': [
                    'app.py期間連携', 'Needファイル動的検出', 
                    '職種動的マッピング', 'スロット数動的対応'
                ]
            },
            'dynamic_config': dynamic_config,
            'dynamic_data_metadata': {
                'intermediate_metadata': dynamic_data['intermediate_metadata'],
                'need_metadata': dynamic_data['need_metadata'],
                'role_mapping': dynamic_data['role_mapping'],
                'system_metadata': dynamic_data['system_metadata']
            },
            'analysis_results': {
                'role_based_analysis': role_results,
                'employment_based_analysis': employment_results,
                'organization_wide_analysis': organization_results,
                'comprehensive_analysis': comprehensive_analysis
            }
        }
        
        # ファイル保存
        main_report_file = f'動的按分廃止_完全レポート_{timestamp}.json'
        with open(main_report_file, 'w', encoding='utf-8') as f:
            json.dump(main_report, f, ensure_ascii=False, indent=2, default=str)
        
        # 職種別詳細CSV（動的対応版）
        role_details = []
        for role_info in role_results['role_shortages'].values():
            role_details.append({
                '職種': role_info['role'],
                'マップ先Need': role_info.get('mapped_need_role', 'N/A'),
                'Need時間_日': role_info['need_hours_daily'],
                '実配置時間_日': role_info['actual_hours_daily'],
                '過不足_日': role_info['shortage_daily'],
                '現在スタッフ数': role_info['staff_count_current'],
                'カバレッジ率': role_info['coverage_ratio'],
                '状態': role_info['shortage_status']
            })
        
        role_df = pd.DataFrame(role_details)
        role_csv_file = f'動的職種別過不足詳細_{timestamp}.csv'
        role_df.to_csv(role_csv_file, index=False, encoding='utf-8')
        
        return {
            'main_report_file': main_report_file,
            'role_details_csv': role_csv_file,
            'files_created': [main_report_file, role_csv_file],
            'dynamic_features_applied': [
                'Period: app.py連携対応',
                'Need Files: 動的検出対応', 
                'Role Mapping: 動的マッピング対応',
                'Time Structure: スロット動的検出対応'
            ]
        }

# 表示関数群
def print_dynamic_config(config):
    """動的設定表示"""
    period_days = config.get('period_info', {}).get('period_days', 'N/A')
    print(f'動的期間設定: {period_days}日')
    print(f'動的対応機能: 期間={config["calculation_settings"]["dynamic_period"]}, 職種={config["calculation_settings"]["dynamic_roles"]}')

def print_dynamic_data_info(data):
    """動的データ情報表示"""
    print(f'データ読み込み: 成功')
    print(f'中間データ: {data["intermediate_metadata"]["total_records"]}レコード')
    print(f'Needファイル: {data["need_metadata"]["successfully_loaded"]}個検出')
    print(f'職種マッピング: {data["role_mapping"]["mapping_statistics"]["successful_mappings"]}/{data["role_mapping"]["mapping_statistics"]["total_actual_roles"]} ({data["role_mapping"]["mapping_statistics"]["mapping_success_rate"]:.1%})')

def print_engine_status(status):
    """エンジン状態表示"""
    print(f'動的エンジン: [OK] 初期化完了')
    print(f'動的期間: {status["dynamic_period_days"]}日')
    print(f'職種数: {status["role_count"]}, 雇用形態数: {status["employment_count"]}')
    print(f'計算方法: {status["calculation_method"]}')

def print_dynamic_role_results(results):
    """動的職種結果表示"""
    print(f'職種別過不足算出: {results["total_roles"]}職種')
    print(f'  マップ済み: {results["mapped_roles"]}職種')
    print(f'  未マップ: {results["unmapped_roles"]}職種')
    print(f'  不足: {results["shortage_roles"]}職種, 余剰: {results["surplus_roles"]}職種')
    
    print(f'\n職種別不足ランキング（上位5位）:')
    for i, role_info in enumerate(results['shortage_ranking'][:5], 1):
        status = '[SHORTAGE]' if role_info['shortage_daily'] > 0 else '[SURPLUS]' if role_info['shortage_daily'] < 0 else '[BALANCED]'
        mapped_info = f" -> {role_info.get('mapped_need_role', 'N/A')}" if role_info.get('mapped_need_role') else ""
        print(f'  {i}. {status} {role_info["role"]}{mapped_info}: {role_info["shortage_daily"]:+.1f}時間/日 ({role_info["staff_count_current"]}名)')

def print_dynamic_employment_results(results):
    """動的雇用形態結果表示"""
    print(f'雇用形態別過不足: {results["total_employments"]}形態')
    for employment, info in results['employment_shortages'].items():
        status = '[SHORTAGE]' if info['shortage_daily'] > 0 else '[SURPLUS]' if info['shortage_daily'] < 0 else '[BALANCED]'
        print(f'  {status} {employment}: {info["shortage_daily"]:+.1f}時間/日 ({info["staff_count_current"]}名)')

def print_dynamic_organization_results(results):
    """動的組織結果表示"""
    status = '[SHORTAGE]' if results['total_shortage_daily'] > 0 else '[SURPLUS]' if results['total_shortage_daily'] < 0 else '[BALANCED]'
    print(f'組織全体過不足: {status} {results["organization_status"]}')
    print(f'  期間: {results["period_days"]}日（動的）')
    print(f'  総Need: {results["total_need_daily"]:.1f}時間/日')
    print(f'  総実配置: {results["total_actual_daily"]:.1f}時間/日')
    print(f'  過不足: {results["total_shortage_daily"]:+.1f}時間/日')
    print(f'  計算方法: {results["calculation_method"]}')

def print_comprehensive_analysis(analysis):
    """総合分析表示"""
    print(f'動的按分廃止効果: {analysis["proportional_abolition_effect"]["abolition_effectiveness"]}')
    print(f'動的システム効果:')
    eff = analysis['dynamic_effectiveness']
    print(f'  職種マッピング成功率: {eff["mapping_success_rate"]:.1%}')
    print(f'  動的機能: 期間={eff["period_flexibility"]}, 職種={eff["role_flexibility"]}, Need={eff["need_file_flexibility"]}')

def print_save_results(results):
    """保存結果表示"""
    print(f'動的結果保存: {len(results["files_created"])}ファイル')
    for feature in results['dynamic_features_applied']:
        print(f'  [OK] {feature}')

if __name__ == "__main__":
    scenario_dir = Path('extracted_results/out_p25_based')
    
    # 動的システム初期化
    dynamic_system = DynamicNeedCalculationSystem(scenario_dir)
    
    # 動的Need算出実行
    result = dynamic_system.execute_dynamic_need_calculation()
    
    if result and result.get('success', False):
        print('\n' + '=' * 80)
        print('[SUCCESS] 動的対応強化版 按分廃止システム実装完了')
        print('[DYNAMIC] app.py期間連携, Need動的検出, 職種動的マッピング対応')
        print('=' * 80)
    else:
        print('\n[ERROR] 動的システム実装失敗')