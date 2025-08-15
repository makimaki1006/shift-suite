#!/usr/bin/env python3
"""
実配置データの慎重な分析と特性把握
Step2-T1: データを深く理解してからアルゴリズム設計に進む
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class CarefulActualDataAnalyzer:
    """実配置データの慎重な分析システム"""
    
    def __init__(self, scenario_dir: Path):
        self.scenario_dir = scenario_dir
        self.analysis_results = {}
        
    def analyze_actual_data_carefully(self) -> Dict[str, any]:
        """実配置データの慎重な分析実行"""
        
        print('=' * 80)
        print('Step2-T1: 実配置データ慎重分析システム')
        print('目的: 現在データの深い理解 → 安全な設計基盤の構築')
        print('=' * 80)
        
        # 1. データ読み込みと基本検証
        self._load_and_validate_data()
        
        # 2. 職種別配置パターンの詳細分析
        self._analyze_role_allocation_patterns()
        
        # 3. 雇用形態別勤務パターンの分析
        self._analyze_employment_patterns()
        
        # 4. 時間軸特性の詳細把握
        self._analyze_temporal_characteristics()
        
        # 5. データ品質と信頼性の評価
        self._assess_data_quality_reliability()
        
        # 6. Need算出設計のための推奨事項
        self._generate_design_recommendations()
        
        return self._create_comprehensive_analysis_report()
    
    def _load_and_validate_data(self):
        """データ読み込みと基本検証"""
        print('\n【Phase 1: データ読み込みと基本検証】')
        
        try:
            self.intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
            print('[OK] intermediate_data読み込み成功')
            print(f'   総レコード数: {len(self.intermediate_data):,}')
            print(f'   カラム数: {len(self.intermediate_data.columns)}')
            print(f'   メモリ使用量: {self.intermediate_data.memory_usage(deep=True).sum() / 1024**2:.1f}MB')
            
            # 基本統計
            basic_stats = {
                'total_records': len(self.intermediate_data),
                'date_range': {
                    'start': self.intermediate_data['ds'].min(),
                    'end': self.intermediate_data['ds'].max(),
                    'days': self.intermediate_data['ds'].dt.date.nunique()
                },
                'time_slots': {
                    'unique_times': len(self.intermediate_data['ds'].dt.time.unique()),
                    'time_range': {
                        'start': str(self.intermediate_data['ds'].dt.time.min()),
                        'end': str(self.intermediate_data['ds'].dt.time.max())
                    }
                },
                'staff_diversity': {
                    'unique_staff': self.intermediate_data['staff'].nunique(),
                    'unique_roles': self.intermediate_data['role'].nunique(),
                    'unique_employments': self.intermediate_data['employment'].nunique()
                }
            }
            
            self.analysis_results['basic_stats'] = basic_stats
            
            print(f'   期間: {basic_stats["date_range"]["days"]}日間')
            print(f'   時間スロット: {basic_stats["time_slots"]["unique_times"]}個')
            print(f'   スタッフ数: {basic_stats["staff_diversity"]["unique_staff"]}名')
            
        except Exception as e:
            print(f'[ERROR] データ読み込み失敗 - {e}')
            raise
    
    def _analyze_role_allocation_patterns(self):
        """職種別配置パターンの詳細分析"""
        print('\n【Phase 2: 職種別配置パターン詳細分析】')
        
        # 職種別基本統計
        role_stats = {}
        role_distribution = self.intermediate_data['role'].value_counts()
        
        print(f'検出職種数: {len(role_distribution)}職種')
        print('\n職種別配置状況:')
        
        for role, count in role_distribution.items():
            percentage = count / len(self.intermediate_data) * 100
            print(f'  {role}: {count:,}レコード ({percentage:.1f}%)')
            
            # 職種別詳細分析
            role_data = self.intermediate_data[self.intermediate_data['role'] == role]
            
            role_analysis = {
                'record_count': count,
                'percentage': percentage,
                'unique_staff': role_data['staff'].nunique(),
                'avg_records_per_staff': count / role_data['staff'].nunique(),
                'time_distribution': self._analyze_role_time_pattern(role_data),
                'employment_mix': role_data['employment'].value_counts().to_dict(),
                'workload_intensity': self._calculate_workload_intensity(role_data)
            }
            
            role_stats[role] = role_analysis
        
        self.analysis_results['role_patterns'] = role_stats
        
        # 職種間の相関・依存関係分析
        self._analyze_role_interdependencies()
    
    def _analyze_role_time_pattern(self, role_data: pd.DataFrame) -> Dict:
        """職種別時間パターン分析"""
        
        # 時間帯別分布
        hourly_dist = role_data['ds'].dt.hour.value_counts().sort_index()
        
        # ピーク時間の特定
        peak_hours = hourly_dist.nlargest(3).index.tolist()
        low_hours = hourly_dist.nsmallest(3).index.tolist()
        
        # 時間集中度の計算
        time_concentration = hourly_dist.std() / hourly_dist.mean() if hourly_dist.mean() > 0 else 0
        
        return {
            'hourly_distribution': hourly_dist.to_dict(),
            'peak_hours': peak_hours,
            'low_hours': low_hours,
            'time_concentration': time_concentration,
            'evening_ratio': len(role_data[role_data['ds'].dt.hour >= 17]) / len(role_data)
        }
    
    def _calculate_workload_intensity(self, role_data: pd.DataFrame) -> Dict:
        """職種別ワークロード強度計算"""
        
        # スタッフあたりの勤務密度
        staff_workload = role_data.groupby('staff').size()
        
        return {
            'avg_records_per_staff': staff_workload.mean(),
            'workload_std': staff_workload.std(),
            'workload_variation': staff_workload.std() / staff_workload.mean() if staff_workload.mean() > 0 else 0,
            'max_workload_staff': staff_workload.max(),
            'min_workload_staff': staff_workload.min()
        }
    
    def _analyze_role_interdependencies(self):
        """職種間相関・依存関係分析"""
        print('\n職種間相関分析:')
        
        # 時間帯別の職種共存パターン
        hourly_role_matrix = self.intermediate_data.pivot_table(
            index=self.intermediate_data['ds'].dt.hour,
            columns='role',
            values='staff',
            aggfunc='count',
            fill_value=0
        )
        
        # 職種間相関係数
        role_correlations = hourly_role_matrix.corr()
        
        # 高い相関（>0.7）を持つ職種ペアの特定
        high_correlations = []
        for i, role1 in enumerate(role_correlations.columns):
            for j, role2 in enumerate(role_correlations.columns):
                if i < j and abs(role_correlations.loc[role1, role2]) > 0.7:
                    high_correlations.append({
                        'role1': role1,
                        'role2': role2,
                        'correlation': role_correlations.loc[role1, role2]
                    })
        
        print(f'  高相関職種ペア数: {len(high_correlations)}')
        for corr in high_correlations[:3]:  # 上位3つ表示
            print(f'    {corr["role1"]} ↔ {corr["role2"]}: {corr["correlation"]:.3f}')
        
        self.analysis_results['role_correlations'] = {
            'correlation_matrix': role_correlations.to_dict(),
            'high_correlations': high_correlations
        }
    
    def _analyze_employment_patterns(self):
        """雇用形態別勤務パターン分析"""
        print('\n【Phase 3: 雇用形態別勤務パターン分析】')
        
        emp_stats = {}
        emp_distribution = self.intermediate_data['employment'].value_counts()
        
        for employment, count in emp_distribution.items():
            emp_data = self.intermediate_data[self.intermediate_data['employment'] == employment]
            
            emp_analysis = {
                'record_count': count,
                'unique_staff': emp_data['staff'].nunique(),
                'role_diversity': emp_data['role'].nunique(),
                'avg_hours_per_staff': count / emp_data['staff'].nunique() * 0.5,  # 30分スロット
                'time_pattern': self._analyze_employment_time_pattern(emp_data),
                'role_distribution': emp_data['role'].value_counts().to_dict()
            }
            
            emp_stats[employment] = emp_analysis
            
            print(f'{employment}:')
            print(f'  レコード数: {count:,} ({count/len(self.intermediate_data)*100:.1f}%)')
            print(f'  スタッフ数: {emp_analysis["unique_staff"]}名')
            print(f'  平均勤務時間: {emp_analysis["avg_hours_per_staff"]:.1f}時間/月')
        
        self.analysis_results['employment_patterns'] = emp_stats
    
    def _analyze_employment_time_pattern(self, emp_data: pd.DataFrame) -> Dict:
        """雇用形態別時間パターン分析"""
        
        # 時間帯分布
        hour_dist = emp_data['ds'].dt.hour.value_counts().sort_index()
        
        # 勤務時間帯の特性
        morning_ratio = len(emp_data[emp_data['ds'].dt.hour < 12]) / len(emp_data)
        afternoon_ratio = len(emp_data[(emp_data['ds'].dt.hour >= 12) & (emp_data['ds'].dt.hour < 18)]) / len(emp_data)
        evening_ratio = len(emp_data[emp_data['ds'].dt.hour >= 18]) / len(emp_data)
        
        return {
            'morning_ratio': morning_ratio,
            'afternoon_ratio': afternoon_ratio,
            'evening_ratio': evening_ratio,
            'peak_hour': hour_dist.idxmax(),
            'time_spread': hour_dist.std()
        }
    
    def _analyze_temporal_characteristics(self):
        """時間軸特性の詳細把握"""
        print('\n【Phase 4: 時間軸特性詳細把握】')
        
        # 日別変動パターン
        daily_counts = self.intermediate_data.groupby(self.intermediate_data['ds'].dt.date).size()
        
        # 曜日パターン
        weekday_pattern = self.intermediate_data.groupby(self.intermediate_data['ds'].dt.dayofweek).size()
        
        # 時間スロット詳細
        time_slots = self.intermediate_data['ds'].dt.time.unique()
        sorted_times = sorted(time_slots)
        
        # スロット間隔の計算
        time_intervals = []
        for i in range(1, len(sorted_times)):
            prev_minutes = sorted_times[i-1].hour * 60 + sorted_times[i-1].minute
            curr_minutes = sorted_times[i].hour * 60 + sorted_times[i].minute
            interval = curr_minutes - prev_minutes
            time_intervals.append(interval)
        
        temporal_analysis = {
            'daily_variation': {
                'mean': daily_counts.mean(),
                'std': daily_counts.std(),
                'coefficient_variation': daily_counts.std() / daily_counts.mean(),
                'min_day': daily_counts.min(),
                'max_day': daily_counts.max()
            },
            'weekday_pattern': weekday_pattern.to_dict(),
            'time_structure': {
                'total_slots': len(time_slots),
                'start_time': str(sorted_times[0]),
                'end_time': str(sorted_times[-1]),
                'typical_interval': np.mean(time_intervals) if time_intervals else 0,
                'interval_consistency': np.std(time_intervals) if time_intervals else 0
            }
        }
        
        self.analysis_results['temporal_characteristics'] = temporal_analysis
        
        print(f'日別変動係数: {temporal_analysis["daily_variation"]["coefficient_variation"]:.3f}')
        print(f'時間スロット数: {temporal_analysis["time_structure"]["total_slots"]}個')
        print(f'典型的間隔: {temporal_analysis["time_structure"]["typical_interval"]:.1f}分')
    
    def _assess_data_quality_reliability(self):
        """データ品質と信頼性評価"""
        print('\n【Phase 5: データ品質・信頼性評価】')
        
        quality_assessment = {
            'completeness': {
                'missing_values': self.intermediate_data.isnull().sum().to_dict(),
                'data_coverage': len(self.intermediate_data) / (
                    self.analysis_results['basic_stats']['date_range']['days'] * 
                    self.analysis_results['basic_stats']['time_slots']['unique_times']
                )
            },
            'consistency': {
                'duplicate_records': self.intermediate_data.duplicated().sum(),
                'data_types_consistent': self._check_data_type_consistency(),
                'value_ranges_valid': self._check_value_ranges()
            },
            'reliability_indicators': {
                'staff_id_consistency': self._check_staff_consistency(),
                'temporal_continuity': self._check_temporal_continuity(),
                'logical_constraints': self._check_logical_constraints()
            }
        }
        
        self.analysis_results['data_quality'] = quality_assessment
        
        print(f'データカバレッジ: {quality_assessment["completeness"]["data_coverage"]:.3f}')
        print(f'重複レコード: {quality_assessment["consistency"]["duplicate_records"]}件')
        
        # 品質スコア算出
        quality_score = self._calculate_quality_score(quality_assessment)
        self.analysis_results['overall_quality_score'] = quality_score
        
        print(f'総合品質スコア: {quality_score:.2f}/1.0')
    
    def _check_data_type_consistency(self) -> bool:
        """データ型整合性チェック"""
        expected_types = {
            'ds': 'datetime64[ns]',
            'staff': 'object',
            'role': 'object',
            'employment': 'object'
        }
        
        for col, expected_type in expected_types.items():
            if col in self.intermediate_data.columns:
                if not str(self.intermediate_data[col].dtype).startswith(expected_type.split('[')[0]):
                    return False
        return True
    
    def _check_value_ranges(self) -> Dict:
        """値の妥当性チェック"""
        checks = {}
        
        # 日時の妥当性
        checks['date_range_valid'] = (
            self.intermediate_data['ds'].min().year >= 2020 and
            self.intermediate_data['ds'].max().year <= 2030
        )
        
        # スタッフIDの妥当性
        checks['staff_ids_valid'] = self.intermediate_data['staff'].str.len().between(1, 50).all()
        
        return checks
    
    def _check_staff_consistency(self) -> float:
        """スタッフ情報の整合性確認"""
        # 同じスタッフが複数の雇用形態を持たないかチェック
        staff_employment = self.intermediate_data.groupby('staff')['employment'].nunique()
        consistent_staff_ratio = (staff_employment == 1).mean()
        
        return consistent_staff_ratio
    
    def _check_temporal_continuity(self) -> Dict:
        """時間的連続性チェック"""
        # 日付の連続性
        date_range = pd.date_range(
            start=self.intermediate_data['ds'].dt.date.min(),
            end=self.intermediate_data['ds'].dt.date.max(),
            freq='D'
        )
        actual_dates = set(self.intermediate_data['ds'].dt.date)
        expected_dates = set(date_range.date)
        
        return {
            'missing_dates': len(expected_dates - actual_dates),
            'continuity_ratio': len(actual_dates) / len(expected_dates)
        }
    
    def _check_logical_constraints(self) -> Dict:
        """論理制約チェック"""
        constraints = {}
        
        # 同一スタッフが同時刻に複数の場所にいないかチェック
        duplicate_assignments = self.intermediate_data.groupby(['ds', 'staff']).size()
        constraints['no_double_booking'] = (duplicate_assignments <= 1).all()
        
        # 職種と雇用形態の組み合わせ妥当性
        role_emp_combinations = self.intermediate_data.groupby(['role', 'employment']).size()
        constraints['valid_role_employment_combinations'] = len(role_emp_combinations)
        
        return constraints
    
    def _calculate_quality_score(self, quality_assessment: Dict) -> float:
        """総合品質スコア算出"""
        score = 1.0
        
        # 完全性スコア
        if quality_assessment['completeness']['data_coverage'] < 0.8:
            score -= 0.2
        
        # 整合性スコア  
        if quality_assessment['consistency']['duplicate_records'] > 0:
            score -= 0.1
        
        # 信頼性スコア
        if quality_assessment['reliability_indicators']['staff_id_consistency'] < 0.95:
            score -= 0.2
        
        return max(0.0, score)
    
    def _generate_design_recommendations(self):
        """Need算出設計のための推奨事項生成"""
        print('\n【Phase 6: 設計推奨事項生成】')
        
        recommendations = {
            'algorithm_approach': self._recommend_algorithm_approach(),
            'data_handling': self._recommend_data_handling(),
            'validation_strategy': self._recommend_validation_strategy(),
            'risk_mitigation': self._recommend_risk_mitigation()
        }
        
        self.analysis_results['design_recommendations'] = recommendations
        
        print('設計推奨事項:')
        for category, items in recommendations.items():
            print(f'  {category}: {len(items)}項目')
    
    def _recommend_algorithm_approach(self) -> List[str]:
        """アルゴリズムアプローチの推奨"""
        recommendations = []
        
        # データ品質に基づく推奨
        if self.analysis_results['overall_quality_score'] >= 0.8:
            recommendations.append('高品質データのため、精密な実配置ベース算出が適用可能')
        else:
            recommendations.append('データ品質に注意して、保守的な係数適用を推奨')
        
        # 職種特性に基づく推奨
        role_count = len(self.analysis_results['role_patterns'])
        if role_count >= 10:
            recommendations.append('多職種環境のため、職種別個別調整係数の適用を推奨')
        
        # 時間構造に基づく推奨
        slot_count = self.analysis_results['temporal_characteristics']['time_structure']['total_slots']
        if slot_count < 48:
            recommendations.append('部分時間カバレッジのため、時間補正係数の適用を検討')
        
        return recommendations
    
    def _recommend_data_handling(self) -> List[str]:
        """データ処理の推奨」"""
        recommendations = []
        
        # 欠損値処理
        missing_ratio = sum(self.analysis_results['data_quality']['completeness']['missing_values'].values())
        if missing_ratio > 0:
            recommendations.append('欠損値の適切な補間または除外処理が必要')
        
        # 異常値処理
        daily_variation = self.analysis_results['temporal_characteristics']['daily_variation']['coefficient_variation']
        if daily_variation > 0.3:
            recommendations.append('日別変動が大きいため、外れ値の検出・処理を実施')
        
        return recommendations
    
    def _recommend_validation_strategy(self) -> List[str]:
        """検証戦略の推奨"""
        return [
            '職種別Need/実配置比率の段階的確認',
            '業界標準との整合性チェック',
            '現場フィードバックとの照合',
            '時系列一貫性の確認'
        ]
    
    def _recommend_risk_mitigation(self) -> List[str]:
        """リスク軽減策の推奨"""
        return [
            'バックアップシステムの活用（既に実装済み）',
            '段階的調整による影響最小化',
            '継続監視システムの構築',
            '現場との密な連携'
        ]
    
    def _create_comprehensive_analysis_report(self) -> Dict[str, any]:
        """包括的分析レポート作成"""
        print('\n' + '=' * 80)
        print('実配置データ慎重分析 完了')
        print('=' * 80)
        
        report = {
            'analysis_metadata': {
                'analysis_date': datetime.now().isoformat(),
                'analysis_type': 'Careful Actual Data Analysis',
                'data_source': str(self.scenario_dir / 'intermediate_data.parquet'),
                'analysis_phase': 'Step2-T1'
            },
            'executive_summary': {
                'total_records': self.analysis_results['basic_stats']['total_records'],
                'analysis_period': f"{self.analysis_results['basic_stats']['date_range']['days']}日間",
                'role_count': len(self.analysis_results['role_patterns']),
                'employment_count': len(self.analysis_results['employment_patterns']),
                'data_quality_score': self.analysis_results['overall_quality_score'],
                'readiness_for_algorithm_design': self.analysis_results['overall_quality_score'] >= 0.7
            },
            'detailed_findings': self.analysis_results,
            'next_steps': [
                'S2-T2: 実配置ベースNeed算出アルゴリズム設計への進行',
                '職種別調整係数の精密設計',
                '業界標準整合性チェック機構の実装'
            ]
        }
        
        # サマリー表示
        summary = report['executive_summary']
        print(f'\n【分析完了サマリー】')
        print(f'分析対象: {summary["total_records"]:,}レコード ({summary["analysis_period"]})')
        print(f'職種数: {summary["role_count"]}, 雇用形態数: {summary["employment_count"]}')
        print(f'データ品質スコア: {summary["data_quality_score"]:.2f}/1.0')
        print(f'アルゴリズム設計準備: {"[OK] 準備完了" if summary["readiness_for_algorithm_design"] else "[WARNING] 要注意"}')
        
        return report

def run_careful_actual_data_analysis():
    """慎重な実配置データ分析の実行"""
    scenario_dir = Path('extracted_results/out_p25_based')
    
    if not scenario_dir.exists():
        print(f'エラー: シナリオディレクトリが見つかりません: {scenario_dir}')
        return None
    
    analyzer = CarefulActualDataAnalyzer(scenario_dir)
    return analyzer.analyze_actual_data_carefully()

if __name__ == "__main__":
    result = run_careful_actual_data_analysis()
    
    if result:
        # 分析結果をJSONファイルに保存
        output_file = Path('careful_actual_data_analysis_report.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        print(f'\n詳細分析レポートを保存: {output_file}')
        print('=' * 80)
        print('S2-T1完了: Step2-T2アルゴリズム設計への準備完了')
        print('=' * 80)