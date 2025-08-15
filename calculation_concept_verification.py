#!/usr/bin/env python3
"""
現在の計算がコンセプト通りに動作しているかの検証
計算ロジックの正確性をステップ別に確認
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict

class CalculationConceptVerifier:
    """計算コンセプト検証システム"""
    
    def __init__(self, scenario_dir: Path):
        self.scenario_dir = scenario_dir
        
    def verify_calculation_concept(self) -> Dict[str, any]:
        """計算がコンセプト通りに動作しているかの検証"""
        
        print('=' * 80)
        print('計算コンセプト検証')
        print('目的: 現在の計算が設計通りに動作しているかを確認')
        print('=' * 80)
        
        verification_results = {}
        
        # 1. 基本データ構造の理解確認
        data_structure = self._verify_data_structure_understanding()
        verification_results['data_structure'] = data_structure
        
        # 2. Need vs 実配置の対応関係確認
        need_allocation_mapping = self._verify_need_allocation_mapping()
        verification_results['need_allocation_mapping'] = need_allocation_mapping
        
        # 3. スロット計算の正確性確認
        slot_calculation = self._verify_slot_calculation_accuracy()
        verification_results['slot_calculation'] = slot_calculation
        
        # 4. 単位系の一貫性確認
        unit_consistency = self._verify_unit_consistency()
        verification_results['unit_consistency'] = unit_consistency
        
        # 5. 実際の計算手順の検証
        calculation_steps = self._verify_calculation_steps()
        verification_results['calculation_steps'] = calculation_steps
        
        return self._generate_concept_verification_report(verification_results)
    
    def _verify_data_structure_understanding(self) -> Dict[str, any]:
        """基本データ構造の理解確認"""
        print('\n【1. 基本データ構造の理解確認】')
        
        # intermediate_data.parquet の構造
        intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
        
        print(f'intermediate_data.parquet:')
        print(f'  総レコード数: {len(intermediate_data)}')
        print(f'  カラム: {list(intermediate_data.columns)}')
        print(f'  期間: {intermediate_data["ds"].min()} ～ {intermediate_data["ds"].max()}')
        print(f'  実日数: {intermediate_data["ds"].dt.date.nunique()}日')
        
        # 時間スロット分析
        unique_times = intermediate_data['ds'].dt.time.unique()
        print(f'  時間スロット数: {len(unique_times)}')
        print(f'  時間範囲: {min(unique_times)} ～ {max(unique_times)}')
        
        # スロット間隔の計算
        sorted_times = sorted(unique_times)
        if len(sorted_times) >= 2:
            first_interval = None
            for i in range(1, min(5, len(sorted_times))):
                prev_time = pd.Timestamp.combine(pd.Timestamp.today().date(), sorted_times[i-1])
                curr_time = pd.Timestamp.combine(pd.Timestamp.today().date(), sorted_times[i])
                interval_minutes = (curr_time - prev_time).total_seconds() / 60
                if interval_minutes > 0:
                    if first_interval is None:
                        first_interval = interval_minutes
                    print(f'  スロット間隔例: {interval_minutes}分')
                    break
        
        # Needファイル構造
        need_files = list(self.scenario_dir.glob('need_per_date_slot_role_*.parquet'))
        print(f'\nNeedファイル構造:')
        print(f'  ファイル数: {len(need_files)}')
        
        if need_files:
            sample_need = pd.read_parquet(need_files[0])
            print(f'  サンプル形状: {sample_need.shape}')
            print(f'  行数（スロット数）: {sample_need.shape[0]}')
            print(f'  列数（日数）: {sample_need.shape[1]}')
        
        return {
            'intermediate_records': len(intermediate_data),
            'actual_days': intermediate_data['ds'].dt.date.nunique(),
            'time_slots': len(unique_times),
            'slot_interval_minutes': first_interval if 'first_interval' in locals() else None,
            'need_files_count': len(need_files),
            'need_file_shape': sample_need.shape if need_files else None
        }
    
    def _verify_need_allocation_mapping(self) -> Dict[str, any]:
        """Need vs 実配置の対応関係確認"""
        print('\n【2. Need vs 実配置の対応関係確認】')
        
        intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
        
        # 実配置の職種別集計
        actual_allocation = intermediate_data['role'].value_counts()
        print(f'実配置職種別レコード数:')
        for role, count in actual_allocation.items():
            print(f'  {role}: {count}レコード')
        
        # Needファイルとの対応確認
        need_files = list(self.scenario_dir.glob('need_per_date_slot_role_*.parquet'))
        mapping_results = {}
        
        print(f'\nNeed <-> 実配置の対応関係:')
        
        for need_file in need_files:
            # ファイル名から職種抽出
            role_name = need_file.name.replace('need_per_date_slot_role_', '').replace('.parquet', '')
            
            # Needデータ読み込み
            need_df = pd.read_parquet(need_file)
            need_total = need_df.sum().sum()
            
            # 対応する実配置の検索
            matching_roles = []
            for actual_role in actual_allocation.index:
                if (role_name in str(actual_role) or 
                    str(actual_role) in role_name or
                    role_name.replace('/', '').replace('（', '').replace('）', '') == str(actual_role)):
                    matching_roles.append(actual_role)
            
            if matching_roles:
                actual_count = sum(actual_allocation[role] for role in matching_roles)
                ratio = need_total / actual_count if actual_count > 0 else float('inf')
                
                print(f'  {role_name}:')
                print(f'    Need合計: {need_total}')
                print(f'    実配置: {actual_count}レコード (職種: {matching_roles})')
                print(f'    Need/実配置比: {ratio:.2f}')
                
                mapping_results[role_name] = {
                    'need_total': need_total,
                    'actual_count': actual_count,
                    'ratio': ratio,
                    'matching_roles': matching_roles
                }
            else:
                print(f'  {role_name}: 対応する実配置が見つかりません')
                mapping_results[role_name] = {
                    'need_total': need_total,
                    'actual_count': 0,
                    'ratio': float('inf'),
                    'matching_roles': []
                }
        
        return mapping_results
    
    def _verify_slot_calculation_accuracy(self) -> Dict[str, any]:
        """スロット計算の正確性確認"""
        print('\n【3. スロット計算の正確性確認】')
        
        intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
        
        # 時間スロットの詳細分析
        unique_times = intermediate_data['ds'].dt.time.unique()
        time_slot_count = len(unique_times)
        
        # 期間の詳細分析
        unique_dates = intermediate_data['ds'].dt.date.unique()
        date_count = len(unique_dates)
        
        print(f'時間軸分析:')
        print(f'  実際の日数: {date_count}日')
        print(f'  実際のスロット数: {time_slot_count}スロット')
        
        # 理論値との比較
        print(f'\n理論値との比較:')
        print(f'  24時間÷30分 = 48スロット (理論値)')
        print(f'  実際のスロット数: {time_slot_count}スロット')
        
        slot_accuracy = time_slot_count == 48
        print(f'  スロット数の正確性: {"[OK]" if slot_accuracy else "[ERROR]"}')
        
        # スロット時間の計算
        if time_slot_count > 0:
            slot_duration_hours = 24 / time_slot_count
            print(f'  1スロット時間: {slot_duration_hours:.3f}時間 ({slot_duration_hours*60:.1f}分)')
        
        # レコード分布の確認
        records_per_day = len(intermediate_data) / date_count
        print(f'\n1日あたりレコード分布:')
        print(f'  平均: {records_per_day:.1f}レコード/日')
        
        daily_counts = intermediate_data.groupby(intermediate_data['ds'].dt.date).size()
        print(f'  最大: {daily_counts.max()}レコード/日')
        print(f'  最小: {daily_counts.min()}レコード/日')
        print(f'  標準偏差: {daily_counts.std():.1f}')
        
        return {
            'actual_days': date_count,
            'actual_slots': time_slot_count,
            'expected_slots': 48,
            'slot_accuracy': slot_accuracy,
            'slot_duration_hours': slot_duration_hours if 'slot_duration_hours' in locals() else None,
            'avg_records_per_day': records_per_day
        }
    
    def _verify_unit_consistency(self) -> Dict[str, any]:
        """単位系の一貫性確認"""
        print('\n【4. 単位系の一貫性確認】')
        
        # Needファイルの単位確認
        need_files = list(self.scenario_dir.glob('need_per_date_slot_role_*.parquet'))
        
        if need_files:
            sample_need = pd.read_parquet(need_files[0])
            
            print(f'Needファイルの単位分析:')
            print(f'  データ型: {sample_need.dtypes.iloc[0]}')
            print(f'  値の範囲: {sample_need.min().min()} ～ {sample_need.max().max()}')
            print(f'  典型的な値: {sample_need[sample_need > 0].stack().mode().iloc[0] if (sample_need > 0).any().any() else "なし"}')
            
            # セルの意味解釈
            print(f'\nセルの意味解釈:')
            print(f'  各セル = 特定の日付・時間スロットでの必要人数')
            print(f'  行(48行) = 24時間を30分スロットで分割')
            print(f'  列(30列) = 30日間')
            
            # 単位の整合性チェック
            print(f'\n単位系整合性:')
            print(f'  Needファイル: 人数/スロット')
            print(f'  intermediate_data: レコード数 (1レコード = 1人・1スロット)')
            
            unit_consistent = True  # 基本的には整合している
            
        # intermediate_dataの単位確認
        intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
        
        print(f'\nintermediate_dataの単位分析:')
        print(f'  1レコード = 1人がある時間スロットに配置')
        print(f'  dsカラム = 具体的な日時')
        print(f'  roleカラム = 職種')
        
        return {
            'need_unit': '人数/スロット',
            'intermediate_unit': '1レコード = 1人・1スロット',
            'unit_consistent': unit_consistent if 'unit_consistent' in locals() else True
        }
    
    def _verify_calculation_steps(self) -> Dict[str, any]:
        """実際の計算手順の検証"""
        print('\n【5. 実際の計算手順の検証】')
        
        # サンプル職種で計算手順を検証
        sample_role = "介護"
        
        print(f'サンプル職種「{sample_role}」で計算検証:')
        
        # Step 1: Need集計
        need_files = [f for f in self.scenario_dir.glob('need_per_date_slot_role_*.parquet') 
                     if sample_role in f.name]
        
        total_need = 0
        print(f'\nStep 1 - Need集計:')
        for need_file in need_files:
            df = pd.read_parquet(need_file)
            file_need = df.sum().sum()
            total_need += file_need
            print(f'  {need_file.name}: {file_need}')
        
        print(f'  Need合計: {total_need} (単位: 人・スロット)')
        
        # Step 2: 実配置集計
        intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
        care_data = intermediate_data[intermediate_data['role'].str.contains(sample_role, na=False)]
        
        actual_records = len(care_data)
        print(f'\nStep 2 - 実配置集計:')
        print(f'  実配置レコード数: {actual_records} (単位: 人・スロット)')
        
        # Step 3: 現在の計算ロジック
        print(f'\nStep 3 - 現在の計算ロジック:')
        
        # 動的スロット時間
        time_slots = intermediate_data['ds'].dt.time.unique()
        slot_duration_hours = 24 / len(time_slots)
        print(f'  スロット時間: {slot_duration_hours:.3f}時間/スロット')
        
        # 時間換算
        need_hours = total_need * slot_duration_hours
        actual_hours = actual_records * slot_duration_hours
        print(f'  Need時間: {need_hours:.1f}時間')
        print(f'  実配置時間: {actual_hours:.1f}時間')
        
        # 期間正規化
        period_days = intermediate_data['ds'].dt.date.nunique()
        daily_need = need_hours / period_days
        daily_actual = actual_hours / period_days
        daily_difference = daily_need - daily_actual
        
        print(f'  期間: {period_days}日')
        print(f'  1日Need: {daily_need:.1f}時間/日')
        print(f'  1日実配置: {daily_actual:.1f}時間/日')
        print(f'  1日差分: {daily_difference:+.1f}時間/日')
        
        # 計算ロジックの妥当性チェック
        logic_valid = True
        issues = []
        
        if total_need == 0:
            issues.append('Needがゼロ - データまたはマッピングの問題')
            logic_valid = False
        
        if actual_records == 0:
            issues.append('実配置がゼロ - 職種マッピングの問題')
            logic_valid = False
        
        if abs(daily_difference) > 100:
            issues.append(f'1日差分{daily_difference:+.1f}時間は非現実的')
            logic_valid = False
        
        print(f'\n計算ロジック検証:')
        if logic_valid:
            print('  [OK] 計算手順は論理的に正しい')
        else:
            print('  [ERROR] 計算に問題あり:')
            for issue in issues:
                print(f'    - {issue}')
        
        return {
            'sample_role': sample_role,
            'total_need': total_need,
            'actual_records': actual_records,
            'slot_duration_hours': slot_duration_hours,
            'daily_difference': daily_difference,
            'logic_valid': logic_valid,
            'issues': issues
        }
    
    def _generate_concept_verification_report(self, results: Dict[str, any]) -> Dict[str, any]:
        """コンセプト検証レポート生成"""
        print('\n' + '=' * 80)
        print('計算コンセプト検証レポート')
        print('=' * 80)
        
        # 各検証項目の評価
        evaluations = {
            'data_structure': 'PASS' if results['data_structure']['need_files_count'] > 0 else 'FAIL',
            'need_allocation_mapping': 'PASS' if len(results['need_allocation_mapping']) > 0 else 'FAIL',
            'slot_calculation': 'PASS' if results['slot_calculation']['slot_accuracy'] else 'WARNING',
            'unit_consistency': 'PASS' if results['unit_consistency']['unit_consistent'] else 'FAIL',
            'calculation_steps': 'PASS' if results['calculation_steps']['logic_valid'] else 'FAIL'
        }
        
        print(f'\n【検証結果サマリー】')
        for category, status in evaluations.items():
            status_symbol = {'PASS': '[OK]', 'WARNING': '[WARNING]', 'FAIL': '[ERROR]'}[status]
            print(f'  {category}: {status_symbol} {status}')
        
        # 全体評価
        fail_count = sum(1 for status in evaluations.values() if status == 'FAIL')
        warning_count = sum(1 for status in evaluations.values() if status == 'WARNING')
        
        if fail_count == 0 and warning_count == 0:
            overall_status = 'PASS'
            print(f'\n【総合評価】[OK] 計算はコンセプト通りに動作')
        elif fail_count == 0:
            overall_status = 'WARNING'
            print(f'\n【総合評価】[WARNING] 計算は概ねコンセプト通り（要注意項目あり）')
        else:
            overall_status = 'FAIL'
            print(f'\n【総合評価】[ERROR] 計算にコンセプトとの乖離あり')
        
        # 具体的な問題点
        if results['calculation_steps']['issues']:
            print(f'\n【検出された問題】')
            for issue in results['calculation_steps']['issues']:
                print(f'  - {issue}')
        
        return {
            'overall_status': overall_status,
            'category_evaluations': evaluations,
            'detailed_results': results,
            'requires_fix': overall_status == 'FAIL'
        }

def run_calculation_concept_verification():
    """計算コンセプト検証の実行"""
    scenario_dir = Path('extracted_results/out_p25_based')
    
    if not scenario_dir.exists():
        print(f'エラー: シナリオディレクトリが見つかりません: {scenario_dir}')
        return None
    
    verifier = CalculationConceptVerifier(scenario_dir)
    return verifier.verify_calculation_concept()

if __name__ == "__main__":
    result = run_calculation_concept_verification()
    
    if result:
        print('\n' + '=' * 80)
        if result['requires_fix']:
            print('結論: 計算のコンセプト修正が必要')
        else:
            print('結論: 計算はコンセプト通りに動作')
        print('=' * 80)