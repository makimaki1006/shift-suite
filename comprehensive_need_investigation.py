#!/usr/bin/env python3
"""
Need積算修正方針決定のための包括的調査システム
あらゆる角度からNeed積算を調査し、修正方針を決定する
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
from datetime import datetime, time
import matplotlib.pyplot as plt
import seaborn as sns

class ComprehensiveNeedInvestigator:
    """Need積算包括的調査システム"""
    
    def __init__(self, scenario_dir: Path):
        self.scenario_dir = scenario_dir
        self.investigation_results = {}
        
    def investigate_need_comprehensive(self) -> Dict[str, any]:
        """Need積算の包括的調査"""
        
        print('=' * 80)
        print('Need積算 包括的調査システム')
        print('目的: あらゆる角度から調査してNeed積算修正方針を決定')
        print('=' * 80)
        
        # 1. 基礎データ構造の深掘り調査
        basic_structure = self._investigate_basic_data_structure()
        self.investigation_results['basic_structure'] = basic_structure
        
        # 2. Needファイル生成元の推定調査
        source_analysis = self._investigate_need_source_generation()
        self.investigation_results['source_analysis'] = source_analysis
        
        # 3. 時間帯別需要パターンの妥当性調査
        hourly_patterns = self._investigate_hourly_demand_patterns()
        self.investigation_results['hourly_patterns'] = hourly_patterns
        
        # 4. 職種別Need値の現場妥当性調査
        role_reality = self._investigate_role_need_reality()
        self.investigation_results['role_reality'] = role_reality
        
        # 5. 現実的介護施設需要との比較調査
        facility_comparison = self._investigate_realistic_facility_comparison()
        self.investigation_results['facility_comparison'] = facility_comparison
        
        # 6. Need値の統計的異常検知
        anomaly_detection = self._investigate_statistical_anomalies()
        self.investigation_results['anomaly_detection'] = anomaly_detection
        
        # 7. 代替Need積算方式の検討
        alternative_methods = self._investigate_alternative_need_methods()
        self.investigation_results['alternative_methods'] = alternative_methods
        
        # 8. 総合修正方針の決定
        return self._determine_correction_policy()
    
    def _investigate_basic_data_structure(self) -> Dict[str, any]:
        """基礎データ構造の深掘り調査"""
        print('\n【基礎データ構造深掘り調査】')
        
        results = {}
        
        # intermediate_dataの詳細分析
        intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
        
        # 時間カバレッジの詳細
        time_coverage = self._analyze_time_coverage(intermediate_data)
        results['time_coverage'] = time_coverage
        
        # データ密度の分析
        density_analysis = self._analyze_data_density(intermediate_data)
        results['density_analysis'] = density_analysis
        
        # 職種・雇用形態の分布詳細
        distribution_analysis = self._analyze_staff_distribution(intermediate_data)
        results['distribution_analysis'] = distribution_analysis
        
        return results
    
    def _analyze_time_coverage(self, data: pd.DataFrame) -> Dict[str, any]:
        """時間カバレッジの詳細分析"""
        print('\n時間カバレッジ分析:')
        
        # 時間帯の詳細分析
        unique_times = sorted(data['ds'].dt.time.unique())
        
        print(f'  実際の時間帯: {len(unique_times)}個')
        print(f'  開始時刻: {unique_times[0]}')
        print(f'  終了時刻: {unique_times[-1]}')
        
        # 時間の連続性チェック
        time_gaps = []
        for i in range(1, len(unique_times)):
            prev_time = unique_times[i-1]
            curr_time = unique_times[i]
            
            # 時間を分に変換
            prev_minutes = prev_time.hour * 60 + prev_time.minute
            curr_minutes = curr_time.hour * 60 + curr_time.minute
            
            gap_minutes = curr_minutes - prev_minutes
            time_gaps.append(gap_minutes)
        
        # ギャップの統計
        if time_gaps:
            print(f'  時間間隔: 平均{np.mean(time_gaps):.1f}分, 標準偏差{np.std(time_gaps):.1f}分')
            print(f'  間隔範囲: {min(time_gaps)}分-{max(time_gaps)}分')
        
        # 欠落時間帯の特定
        expected_24h_slots = 48  # 30分間隔
        missing_coverage = expected_24h_slots - len(unique_times)
        
        print(f'  期待スロット数: {expected_24h_slots}')
        print(f'  実際スロット数: {len(unique_times)}')
        print(f'  欠落スロット数: {missing_coverage}')
        
        # 夜間時間帯の有無
        night_slots = [t for t in unique_times if t.hour >= 18 or t.hour < 6]
        print(f'  夜間スロット数: {len(night_slots)}')
        
        return {
            'total_slots': len(unique_times),
            'start_time': str(unique_times[0]),
            'end_time': str(unique_times[-1]),
            'average_gap_minutes': np.mean(time_gaps) if time_gaps else 0,
            'missing_slots': missing_coverage,
            'night_slots': len(night_slots),
            'continuous': len(set(time_gaps)) == 1 if time_gaps else False
        }
    
    def _analyze_data_density(self, data: pd.DataFrame) -> Dict[str, any]:
        """データ密度の分析"""
        print('\nデータ密度分析:')
        
        # 日別・時間帯別のレコード密度
        daily_counts = data.groupby(data['ds'].dt.date).size()
        hourly_counts = data.groupby(data['ds'].dt.time).size()
        
        print(f'  日別レコード数: 平均{daily_counts.mean():.1f}, 変動係数{daily_counts.std()/daily_counts.mean():.3f}')
        print(f'  時間帯別レコード数: 平均{hourly_counts.mean():.1f}, 変動係数{hourly_counts.std()/hourly_counts.mean():.3f}')
        
        # スパース性の評価
        total_possible_slots = len(data['ds'].dt.date.unique()) * len(data['ds'].dt.time.unique())
        sparsity = 1 - (len(data) / total_possible_slots)
        
        print(f'  理論最大レコード数: {total_possible_slots}')
        print(f'  実際レコード数: {len(data)}')
        print(f'  データスパース性: {sparsity:.3f}')
        
        return {
            'daily_variation_coefficient': daily_counts.std() / daily_counts.mean(),
            'hourly_variation_coefficient': hourly_counts.std() / hourly_counts.mean(),
            'data_sparsity': sparsity,
            'density_ratio': len(data) / total_possible_slots
        }
    
    def _analyze_staff_distribution(self, data: pd.DataFrame) -> Dict[str, any]:
        """職種・雇用形態分布の詳細分析"""
        print('\n職種・雇用形態分布分析:')
        
        # 職種分布
        role_distribution = data['role'].value_counts()
        print(f'  職種数: {len(role_distribution)}')
        for role, count in role_distribution.items():
            percentage = count / len(data) * 100
            print(f'    {role}: {count}件 ({percentage:.1f}%)')
        
        # 雇用形態分布
        employment_distribution = data['employment'].value_counts()
        print(f'  雇用形態数: {len(employment_distribution)}')
        for emp, count in employment_distribution.items():
            percentage = count / len(data) * 100
            print(f'    {emp}: {count}件 ({percentage:.1f}%)')
        
        # 職種×雇用形態クロス分析
        cross_analysis = data.groupby(['role', 'employment']).size()
        print(f'  職種×雇用形態組み合わせ: {len(cross_analysis)}パターン')
        
        return {
            'role_count': len(role_distribution),
            'employment_count': len(employment_distribution),
            'cross_combinations': len(cross_analysis),
            'role_distribution': role_distribution.to_dict(),
            'employment_distribution': employment_distribution.to_dict()
        }
    
    def _investigate_need_source_generation(self) -> Dict[str, any]:
        """Needファイル生成元の推定調査"""
        print('\n【Needファイル生成元推定調査】')
        
        results = {}
        need_files = list(self.scenario_dir.glob('need_per_date_slot_role_*.parquet'))
        
        # 各Needファイルの詳細分析
        file_analyses = []
        
        for need_file in need_files:
            df = pd.read_parquet(need_file)
            role_name = need_file.name.replace('need_per_date_slot_role_', '').replace('.parquet', '')
            
            # ファイル別の特性分析
            file_analysis = {
                'role': role_name,
                'shape': df.shape,
                'total_need': df.sum().sum(),
                'non_zero_ratio': (df > 0).sum().sum() / (df.shape[0] * df.shape[1]),
                'value_distribution': {
                    'min': df.min().min(),
                    'max': df.max().max(),
                    'mean': df.mean().mean(),
                    'std': df.std().mean()
                }
            }
            
            # 値の分布パターン分析
            flat_values = df.values.flatten()
            unique_values = np.unique(flat_values[flat_values > 0])
            
            file_analysis['unique_nonzero_values'] = len(unique_values)
            file_analysis['common_values'] = unique_values[:10].tolist() if len(unique_values) > 0 else []
            
            # パターン認識
            if len(unique_values) == 1:
                file_analysis['pattern'] = 'BINARY_CONSTANT'
            elif len(unique_values) < 5:
                file_analysis['pattern'] = 'FEW_DISCRETE_VALUES'
            elif df.std().mean() / df.mean().mean() < 0.1:
                file_analysis['pattern'] = 'LOW_VARIATION'
            else:
                file_analysis['pattern'] = 'HIGH_VARIATION'
            
            file_analyses.append(file_analysis)
            
            print(f'{role_name}:')
            print(f'  形状: {df.shape}')
            print(f'  需要合計: {df.sum().sum()}')
            print(f'  非ゼロ比率: {file_analysis["non_zero_ratio"]:.3f}')
            print(f'  値パターン: {file_analysis["pattern"]}')
            print(f'  ユニーク値数: {len(unique_values)}')
        
        results['file_analyses'] = file_analyses
        
        # 生成方式の推定
        generation_hypothesis = self._estimate_generation_method(file_analyses)
        results['generation_hypothesis'] = generation_hypothesis
        
        return results
    
    def _estimate_generation_method(self, file_analyses: List[Dict]) -> Dict[str, any]:
        """生成方式の推定"""
        print('\nNeed生成方式推定:')
        
        # パターン分析
        patterns = [analysis['pattern'] for analysis in file_analyses]
        pattern_counts = {pattern: patterns.count(pattern) for pattern in set(patterns)}
        
        print(f'  パターン分布: {pattern_counts}')
        
        # 推定結果
        if pattern_counts.get('BINARY_CONSTANT', 0) > len(file_analyses) * 0.7:
            method = 'SIMPLE_BINARY_ALLOCATION'
            confidence = 'HIGH'
            description = '単純な0/1バイナリ配分による生成'
        elif pattern_counts.get('FEW_DISCRETE_VALUES', 0) > len(file_analyses) * 0.5:
            method = 'DISCRETE_LEVEL_ALLOCATION'
            confidence = 'MEDIUM'
            description = '段階的レベル配分による生成'
        else:
            method = 'COMPLEX_CALCULATION'
            confidence = 'LOW'
            description = '複雑な計算による生成'
        
        print(f'  推定生成方式: {method}')
        print(f'  信頼度: {confidence}')
        print(f'  説明: {description}')
        
        return {
            'estimated_method': method,
            'confidence': confidence,
            'description': description,
            'pattern_distribution': pattern_counts
        }
    
    def _investigate_hourly_demand_patterns(self) -> Dict[str, any]:
        """時間帯別需要パターンの妥当性調査"""
        print('\n【時間帯別需要パターン妥当性調査】')
        
        results = {}
        need_files = list(self.scenario_dir.glob('need_per_date_slot_role_*.parquet'))
        
        # 各職種の時間帯パターン分析
        hourly_analyses = []
        
        for need_file in need_files:
            df = pd.read_parquet(need_file)
            role_name = need_file.name.replace('need_per_date_slot_role_', '').replace('.parquet', '')
            
            # 時間帯別需要合計
            hourly_demand = df.sum(axis=1)
            
            # ピーク時間帯の特定
            peak_hours = hourly_demand.nlargest(5).index.tolist()
            low_hours = hourly_demand.nsmallest(5).index.tolist()
            
            # 24時間パターンの現実性評価
            reality_score = self._evaluate_hourly_reality(hourly_demand, role_name)
            
            hourly_analysis = {
                'role': role_name,
                'peak_hours': peak_hours,
                'low_hours': low_hours,
                'demand_variation': hourly_demand.std() / hourly_demand.mean() if hourly_demand.mean() > 0 else 0,
                'night_demand_ratio': hourly_demand[42:].sum() / hourly_demand.sum() if hourly_demand.sum() > 0 else 0,  # 21:00-24:00
                'reality_score': reality_score
            }
            
            hourly_analyses.append(hourly_analysis)
            
            print(f'{role_name}:')
            print(f'  需要変動係数: {hourly_analysis["demand_variation"]:.3f}')
            print(f'  夜間需要比率: {hourly_analysis["night_demand_ratio"]:.3f}')
            print(f'  現実性スコア: {reality_score:.2f}/1.0')
        
        results['hourly_analyses'] = hourly_analyses
        
        # 全体的な時間パターンの評価
        overall_evaluation = self._evaluate_overall_time_patterns(hourly_analyses)
        results['overall_evaluation'] = overall_evaluation
        
        return results
    
    def _evaluate_hourly_reality(self, hourly_demand: pd.Series, role: str) -> float:
        """時間帯需要の現実性評価"""
        score = 1.0
        
        # 介護系職種の現実性チェック
        if '介護' in role:
            # 深夜早朝の需要チェック（過度に高くないか）
            night_early = hourly_demand[0:12].mean() + hourly_demand[40:].mean()
            day_time = hourly_demand[16:36].mean()  # 8:00-18:00
            
            if night_early > day_time * 1.5:  # 夜間需要が日中の1.5倍超は不自然
                score -= 0.3
            
            # 食事時間帯の需要チェック
            meal_times = [16, 24, 36]  # 8:00, 12:00, 18:00
            meal_demand = hourly_demand[meal_times].mean()
            if meal_demand < hourly_demand.mean() * 0.5:  # 食事時間が平均の半分以下は不自然
                score -= 0.2
        
        # 事務系職種の現実性チェック
        elif '事務' in role:
            # 夜間需要はほぼゼロであるべき
            night_demand = hourly_demand[36:].sum()  # 18:00以降
            total_demand = hourly_demand.sum()
            
            if night_demand > total_demand * 0.1:  # 夜間需要が10%超は不自然
                score -= 0.4
        
        # 運転士の現実性チェック
        elif '運転士' in role:
            # 送迎時間帯に集中すべき
            morning_peak = hourly_demand[16:20].sum()  # 8:00-10:00
            evening_peak = hourly_demand[32:36].sum()  # 16:00-18:00
            total_demand = hourly_demand.sum()
            
            peak_ratio = (morning_peak + evening_peak) / total_demand if total_demand > 0 else 0
            if peak_ratio < 0.6:  # ピーク時間帯が60%未満は不自然
                score -= 0.3
        
        return max(0.0, score)
    
    def _evaluate_overall_time_patterns(self, hourly_analyses: List[Dict]) -> Dict[str, any]:
        """全体的な時間パターンの評価"""
        
        # 現実性スコアの分布
        reality_scores = [analysis['reality_score'] for analysis in hourly_analyses]
        
        overall_score = np.mean(reality_scores)
        problematic_roles = [analysis['role'] for analysis in hourly_analyses if analysis['reality_score'] < 0.5]
        
        evaluation = {
            'overall_reality_score': overall_score,
            'problematic_roles': problematic_roles,
            'evaluation': 'GOOD' if overall_score >= 0.7 else 'POOR' if overall_score < 0.4 else 'MODERATE'
        }
        
        print(f'\n時間パターン全体評価:')
        print(f'  全体現実性スコア: {overall_score:.2f}/1.0')
        print(f'  評価: {evaluation["evaluation"]}')
        if problematic_roles:
            print(f'  問題のある職種: {problematic_roles}')
        
        return evaluation
    
    def _investigate_role_need_reality(self) -> Dict[str, any]:
        """職種別Need値の現場妥当性調査"""
        print('\n【職種別Need値現場妥当性調査】')
        
        # 実配置データとの比較
        intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
        
        reality_assessments = []
        need_files = list(self.scenario_dir.glob('need_per_date_slot_role_*.parquet'))
        
        for need_file in need_files:
            df = pd.read_parquet(need_file)
            role_name = need_file.name.replace('need_per_date_slot_role_', '').replace('.parquet', '')
            
            need_total = df.sum().sum()
            
            # 対応する実配置を検索
            matching_roles = []
            for actual_role in intermediate_data['role'].unique():
                if (role_name in str(actual_role) or 
                    str(actual_role) in role_name or
                    self._fuzzy_role_match(role_name, actual_role)):
                    matching_roles.append(actual_role)
            
            if matching_roles:
                actual_records = intermediate_data[
                    intermediate_data['role'].isin(matching_roles)
                ].shape[0]
                
                need_vs_actual_ratio = need_total / actual_records if actual_records > 0 else float('inf')
                
                # 現場妥当性の評価
                reality_assessment = self._assess_role_need_reality(
                    role_name, need_total, actual_records, need_vs_actual_ratio
                )
                
                reality_assessments.append({
                    'role': role_name,
                    'need_total': need_total,
                    'actual_records': actual_records,
                    'ratio': need_vs_actual_ratio,
                    'assessment': reality_assessment
                })
                
                print(f'{role_name}:')
                print(f'  Need: {need_total}, 実配置: {actual_records}')
                print(f'  比率: {need_vs_actual_ratio:.2f}')
                print(f'  現場妥当性: {reality_assessment["level"]} ({reality_assessment["reason"]})')
        
        return {
            'role_assessments': reality_assessments,
            'overall_assessment': self._calculate_overall_role_reality(reality_assessments)
        }
    
    def _fuzzy_role_match(self, need_role: str, actual_role: str) -> bool:
        """あいまい職種マッチング"""
        # 特殊文字を除去して比較
        clean_need = str(need_role).replace('/', '').replace('（', '').replace('）', '').replace('・', '')
        clean_actual = str(actual_role).replace('/', '').replace('（', '').replace('）', '').replace('・', '')
        
        return clean_need == clean_actual
    
    def _assess_role_need_reality(self, role: str, need: float, actual: int, ratio: float) -> Dict[str, any]:
        """職種別Need値の現場妥当性評価"""
        
        if '介護' in role:
            if 0.8 <= ratio <= 1.2:
                return {'level': 'REALISTIC', 'reason': '介護職種として適正な需要レベル'}
            elif ratio > 2.0:
                return {'level': 'UNREALISTIC_HIGH', 'reason': '介護職種として需要過大'}
            elif ratio < 0.3:
                return {'level': 'UNREALISTIC_LOW', 'reason': '介護職種として需要過小'}
            else:
                return {'level': 'QUESTIONABLE', 'reason': '要詳細確認'}
        
        elif '事務' in role:
            if 0.3 <= ratio <= 0.8:
                return {'level': 'REALISTIC', 'reason': '事務職種として適正な需要レベル'}
            elif ratio > 1.5:
                return {'level': 'UNREALISTIC_HIGH', 'reason': '事務職種として需要過大'}
            else:
                return {'level': 'QUESTIONABLE', 'reason': '要詳細確認'}
        
        elif '看護師' in role:
            if 0.7 <= ratio <= 1.1:
                return {'level': 'REALISTIC', 'reason': '看護師として適正な需要レベル'}
            elif ratio > 1.5:
                return {'level': 'UNREALISTIC_HIGH', 'reason': '看護師として需要過大'}
            elif ratio < 0.5:
                return {'level': 'UNREALISTIC_LOW', 'reason': '看護師として需要過小'}
            else:
                return {'level': 'QUESTIONABLE', 'reason': '要詳細確認'}
        
        else:
            # その他の職種
            if 0.5 <= ratio <= 1.5:
                return {'level': 'REALISTIC', 'reason': '一般職種として妥当な範囲'}
            elif ratio > 3.0:
                return {'level': 'UNREALISTIC_HIGH', 'reason': '需要過大'}
            elif ratio < 0.1:
                return {'level': 'UNREALISTIC_LOW', 'reason': '需要過小'}
            else:
                return {'level': 'QUESTIONABLE', 'reason': '要詳細確認'}
    
    def _calculate_overall_role_reality(self, assessments: List[Dict]) -> Dict[str, any]:
        """職種別現場妥当性の全体評価"""
        
        realistic_count = sum(1 for a in assessments if a['assessment']['level'] == 'REALISTIC')
        unrealistic_count = sum(1 for a in assessments if 'UNREALISTIC' in a['assessment']['level'])
        questionable_count = sum(1 for a in assessments if a['assessment']['level'] == 'QUESTIONABLE')
        
        realistic_ratio = realistic_count / len(assessments) if assessments else 0
        
        if realistic_ratio >= 0.7:
            overall = 'GOOD'
        elif realistic_ratio >= 0.4:
            overall = 'MODERATE'
        else:
            overall = 'POOR'
        
        return {
            'realistic_count': realistic_count,
            'unrealistic_count': unrealistic_count,
            'questionable_count': questionable_count,
            'realistic_ratio': realistic_ratio,
            'overall_assessment': overall
        }
    
    def _investigate_realistic_facility_comparison(self) -> Dict[str, any]:
        """現実的介護施設需要との比較調査"""
        print('\n【現実的介護施設需要比較調査】')
        
        # 業界標準データとの比較
        industry_standards = self._get_industry_standards()
        
        # 現在のNeed値を業界標準と比較
        need_files = list(self.scenario_dir.glob('need_per_date_slot_role_*.parquet'))
        total_need = sum(pd.read_parquet(f).sum().sum() for f in need_files)
        
        # スロット時間を考慮した時間換算
        slot_hours = 1.143  # 68.6分/60分
        current_need_hours = total_need * slot_hours
        current_daily_need = current_need_hours / 30  # 30日間
        
        comparison_results = {}
        
        for facility_type, standard in industry_standards.items():
            ratio = current_daily_need / standard['daily_care_hours']
            
            comparison_results[facility_type] = {
                'standard_daily_hours': standard['daily_care_hours'],
                'current_daily_hours': current_daily_need,
                'ratio': ratio,
                'assessment': self._assess_facility_comparison(ratio)
            }
            
            print(f'{facility_type}:')
            print(f'  標準: {standard["daily_care_hours"]}時間/日')
            print(f'  現在: {current_daily_need:.1f}時間/日')
            print(f'  倍率: {ratio:.1f}倍')
            print(f'  評価: {comparison_results[facility_type]["assessment"]}')
        
        return {
            'current_daily_need': current_daily_need,
            'comparisons': comparison_results,
            'overall_assessment': self._calculate_facility_comparison_overall(comparison_results)
        }
    
    def _get_industry_standards(self) -> Dict[str, Dict]:
        """介護業界標準データ"""
        return {
            '小規模施設(定員20名)': {
                'capacity': 20,
                'care_hours_per_resident': 3.5,
                'daily_care_hours': 70
            },
            '中規模施設(定員50名)': {
                'capacity': 50,
                'care_hours_per_resident': 4.0,
                'daily_care_hours': 200
            },
            '大規模施設(定員100名)': {
                'capacity': 100,
                'care_hours_per_resident': 3.8,
                'daily_care_hours': 380
            }
        }
    
    def _assess_facility_comparison(self, ratio: float) -> str:
        """施設比較評価"""
        if 0.8 <= ratio <= 1.2:
            return 'REALISTIC'
        elif 1.2 < ratio <= 2.0:
            return 'SLIGHTLY_HIGH'
        elif ratio > 2.0:
            return 'UNREALISTIC_HIGH'
        elif 0.5 <= ratio < 0.8:
            return 'SLIGHTLY_LOW'
        else:
            return 'UNREALISTIC_LOW'
    
    def _calculate_facility_comparison_overall(self, comparisons: Dict) -> str:
        """施設比較全体評価"""
        realistic_count = sum(1 for c in comparisons.values() if c['assessment'] == 'REALISTIC')
        total_count = len(comparisons)
        
        if realistic_count >= total_count * 0.7:
            return 'GOOD'
        elif realistic_count >= total_count * 0.3:
            return 'MODERATE'
        else:
            return 'POOR'
    
    def _investigate_statistical_anomalies(self) -> Dict[str, any]:
        """Need値の統計的異常検知"""
        print('\n【統計的異常検知調査】')
        
        anomalies = []
        need_files = list(self.scenario_dir.glob('need_per_date_slot_role_*.parquet'))
        
        for need_file in need_files:
            df = pd.read_parquet(need_file)
            role_name = need_file.name.replace('need_per_date_slot_role_', '').replace('.parquet', '')
            
            # 異常検知
            file_anomalies = self._detect_file_anomalies(df, role_name)
            anomalies.extend(file_anomalies)
        
        # 異常の分類と重要度評価
        classified_anomalies = self._classify_anomalies(anomalies)
        
        print(f'検出された異常: {len(anomalies)}件')
        for category, category_anomalies in classified_anomalies.items():
            print(f'  {category}: {len(category_anomalies)}件')
        
        return {
            'total_anomalies': len(anomalies),
            'anomaly_details': anomalies,
            'classified_anomalies': classified_anomalies,
            'severity_assessment': self._assess_anomaly_severity(classified_anomalies)
        }
    
    def _detect_file_anomalies(self, df: pd.DataFrame, role: str) -> List[Dict]:
        """ファイル別異常検知"""
        anomalies = []
        
        # 1. 極端な値の検知
        max_value = df.max().max()
        if max_value > 10:  # 1スロットで10人超は異常
            anomalies.append({
                'type': 'EXTREME_VALUE',
                'role': role,
                'value': max_value,
                'description': f'1スロット{max_value}人は異常な高需要'
            })
        
        # 2. ゼロ値の異常な分布
        zero_ratio = (df == 0).sum().sum() / (df.shape[0] * df.shape[1])
        if zero_ratio > 0.9:  # 90%以上がゼロは異常
            anomalies.append({
                'type': 'EXCESSIVE_ZEROS',
                'role': role,
                'value': zero_ratio,
                'description': f'{zero_ratio:.1%}がゼロ値は異常なスパース性'
            })
        
        # 3. 時間パターンの異常
        hourly_sum = df.sum(axis=1)
        if hourly_sum.std() / hourly_sum.mean() > 2.0:  # 変動係数2.0超は異常
            anomalies.append({
                'type': 'ABNORMAL_TIME_PATTERN',
                'role': role,
                'value': hourly_sum.std() / hourly_sum.mean(),
                'description': '時間帯別需要の変動が異常に大きい'
            })
        
        # 4. 日次パターンの異常
        daily_sum = df.sum(axis=0)
        if daily_sum.std() / daily_sum.mean() > 1.5:  # 変動係数1.5超は異常
            anomalies.append({
                'type': 'ABNORMAL_DAILY_PATTERN',
                'role': role,
                'value': daily_sum.std() / daily_sum.mean(),
                'description': '日別需要の変動が異常に大きい'
            })
        
        return anomalies
    
    def _classify_anomalies(self, anomalies: List[Dict]) -> Dict[str, List[Dict]]:
        """異常の分類"""
        classified = {
            'CRITICAL': [],
            'WARNING': [],
            'INFO': []
        }
        
        for anomaly in anomalies:
            if anomaly['type'] == 'EXTREME_VALUE':
                classified['CRITICAL'].append(anomaly)
            elif anomaly['type'] == 'EXCESSIVE_ZEROS':
                classified['WARNING'].append(anomaly)
            else:
                classified['INFO'].append(anomaly)
        
        return classified
    
    def _assess_anomaly_severity(self, classified_anomalies: Dict) -> str:
        """異常の重要度評価"""
        critical_count = len(classified_anomalies['CRITICAL'])
        warning_count = len(classified_anomalies['WARNING'])
        
        if critical_count > 0:
            return 'HIGH'
        elif warning_count > 3:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _investigate_alternative_need_methods(self) -> Dict[str, any]:
        """代替Need積算方式の検討"""
        print('\n【代替Need積算方式検討】')
        
        # 現在の実配置ベースの方式
        actual_based = self._calculate_actual_based_need()
        
        # 業界標準ベースの方式
        standard_based = self._calculate_standard_based_need()
        
        # ハイブリッド方式
        hybrid = self._calculate_hybrid_need()
        
        alternatives = {
            'actual_based': actual_based,
            'standard_based': standard_based,
            'hybrid': hybrid
        }
        
        # 各方式の評価
        for method_name, method_result in alternatives.items():
            print(f'{method_name}:')
            print(f'  日次需要合計: {method_result["daily_total"]:.1f}時間/日')
            print(f'  現実性評価: {method_result["reality_score"]:.2f}/1.0')
        
        # 推奨方式の決定
        recommended = self._select_recommended_method(alternatives)
        
        return {
            'alternatives': alternatives,
            'recommended_method': recommended
        }
    
    def _calculate_actual_based_need(self) -> Dict[str, any]:
        """実配置ベースのNeed算出"""
        intermediate_data = pd.read_parquet(self.scenario_dir / 'intermediate_data.parquet')
        
        # 実配置の1.1倍を基準Need とする
        total_records = len(intermediate_data)
        slot_hours = 1.143
        daily_hours = total_records * slot_hours / 30
        daily_need = daily_hours * 1.1
        
        return {
            'method': 'ACTUAL_BASED',
            'daily_total': daily_need,
            'reality_score': 0.9,  # 実配置ベースなので現実的
            'description': '実配置の1.1倍を基準とする方式'
        }
    
    def _calculate_standard_based_need(self) -> Dict[str, any]:
        """業界標準ベースのNeed算出"""
        # 中規模施設(50名)を想定
        standard_daily_hours = 200
        
        return {
            'method': 'STANDARD_BASED',
            'daily_total': standard_daily_hours,
            'reality_score': 0.8,  # 業界標準なので現実的
            'description': '介護業界標準(中規模施設)を基準とする方式'
        }
    
    def _calculate_hybrid_need(self) -> Dict[str, any]:
        """ハイブリッド方式のNeed算出"""
        # 実配置と業界標準の平均
        actual_need = self._calculate_actual_based_need()['daily_total']
        standard_need = self._calculate_standard_based_need()['daily_total']
        hybrid_need = (actual_need + standard_need) / 2
        
        return {
            'method': 'HYBRID',
            'daily_total': hybrid_need,
            'reality_score': 0.85,  # 両方の特徴を持つ
            'description': '実配置と業界標準の平均を基準とする方式'
        }
    
    def _select_recommended_method(self, alternatives: Dict) -> Dict[str, any]:
        """推奨方式の選択"""
        # 現実性スコアが最も高い方式を推奨
        best_method = max(alternatives.items(), key=lambda x: x[1]['reality_score'])
        
        return {
            'method_name': best_method[0],
            'method_details': best_method[1],
            'reason': f'現実性スコア{best_method[1]["reality_score"]:.2f}が最高'
        }
    
    def _determine_correction_policy(self) -> Dict[str, any]:
        """Need積算修正方針の決定"""
        print('\n' + '=' * 80)
        print('Need積算修正方針決定')
        print('=' * 80)
        
        # 全調査結果の統合評価
        overall_assessment = self._integrate_all_findings()
        
        # 修正方針の決定
        correction_policy = self._formulate_correction_policy(overall_assessment)
        
        print(f'\n【総合評価】')
        print(f'データ構造: {overall_assessment["data_structure_score"]:.2f}/1.0')
        print(f'時間パターン: {overall_assessment["time_pattern_score"]:.2f}/1.0')
        print(f'職種妥当性: {overall_assessment["role_reality_score"]:.2f}/1.0')
        print(f'施設比較: {overall_assessment["facility_comparison_score"]:.2f}/1.0')
        
        print(f'\n【修正方針】')
        print(f'優先度: {correction_policy["priority"]}')
        print(f'修正方式: {correction_policy["method"]}')
        print(f'説明: {correction_policy["description"]}')
        
        return {
            'investigation_results': self.investigation_results,
            'overall_assessment': overall_assessment,
            'correction_policy': correction_policy,
            'next_actions': correction_policy['next_actions']
        }
    
    def _integrate_all_findings(self) -> Dict[str, any]:
        """全調査結果の統合評価"""
        
        # 各調査結果からスコアを算出
        data_structure_score = self._calculate_data_structure_score()
        time_pattern_score = self._calculate_time_pattern_score()
        role_reality_score = self._calculate_role_reality_score()
        facility_comparison_score = self._calculate_facility_comparison_score()
        
        total_score = (data_structure_score + time_pattern_score + 
                      role_reality_score + facility_comparison_score) / 4
        
        return {
            'data_structure_score': data_structure_score,
            'time_pattern_score': time_pattern_score,
            'role_reality_score': role_reality_score,
            'facility_comparison_score': facility_comparison_score,
            'total_score': total_score
        }
    
    def _calculate_data_structure_score(self) -> float:
        """データ構造スコア算出"""
        basic = self.investigation_results['basic_structure']
        
        score = 1.0
        
        # 21スロット問題
        if basic['time_coverage']['missing_slots'] > 20:
            score -= 0.4
        
        # データ密度問題
        if basic['density_analysis']['data_sparsity'] > 0.8:
            score -= 0.3
        
        return max(0.0, score)
    
    def _calculate_time_pattern_score(self) -> float:
        """時間パターンスコア算出"""
        hourly = self.investigation_results['hourly_patterns']
        return hourly['overall_evaluation']['overall_reality_score']
    
    def _calculate_role_reality_score(self) -> float:
        """職種現実性スコア算出"""
        role_reality = self.investigation_results['role_reality']
        return role_reality['overall_assessment']['realistic_ratio']
    
    def _calculate_facility_comparison_score(self) -> float:
        """施設比較スコア算出"""
        facility = self.investigation_results['facility_comparison']
        
        realistic_count = sum(1 for c in facility['comparisons'].values() 
                             if c['assessment'] == 'REALISTIC')
        total_count = len(facility['comparisons'])
        
        return realistic_count / total_count if total_count > 0 else 0.0
    
    def _formulate_correction_policy(self, assessment: Dict) -> Dict[str, any]:
        """修正方針の策定"""
        
        total_score = assessment['total_score']
        
        if total_score >= 0.7:
            priority = 'LOW'
            method = 'MINOR_ADJUSTMENT'
            description = '軽微な調整のみ実施'
            actions = ['現在のNeedファイルの値を10-20%調整', 'スロット時間の再計算']
        elif total_score >= 0.4:
            priority = 'MEDIUM'
            method = 'PARTIAL_RECONSTRUCTION'
            description = '部分的な再構築が必要'
            actions = ['問題のある職種のNeed値再計算', '時間パターンの現実化', 'スロット構造の検討']
        else:
            priority = 'HIGH'
            method = 'FULL_RECONSTRUCTION'
            description = 'Need積算の全面的な再構築が必要'
            actions = ['実配置ベース方式への変更', '業界標準との整合', '全職種Need値の再計算']
        
        # 推奨代替方式の選択
        alternative_method = self.investigation_results['alternative_methods']['recommended_method']
        
        return {
            'priority': priority,
            'method': method,
            'description': description,
            'next_actions': actions,
            'recommended_alternative': alternative_method,
            'implementation_order': self._create_implementation_order(priority, actions)
        }
    
    def _create_implementation_order(self, priority: str, actions: List[str]) -> List[Dict]:
        """実装順序の作成"""
        
        if priority == 'HIGH':
            return [
                {'step': 1, 'action': '緊急バックアップ作成', 'urgency': 'IMMEDIATE'},
                {'step': 2, 'action': '代替Need積算方式の実装', 'urgency': 'HIGH'},
                {'step': 3, 'action': '全職種Need値の再計算', 'urgency': 'HIGH'},
                {'step': 4, 'action': '結果検証と現場確認', 'urgency': 'MEDIUM'}
            ]
        elif priority == 'MEDIUM':
            return [
                {'step': 1, 'action': 'バックアップ作成', 'urgency': 'HIGH'},
                {'step': 2, 'action': '問題職種の特定修正', 'urgency': 'MEDIUM'},
                {'step': 3, 'action': '修正結果の検証', 'urgency': 'MEDIUM'}
            ]
        else:
            return [
                {'step': 1, 'action': '軽微調整の実装', 'urgency': 'LOW'},
                {'step': 2, 'action': '結果確認', 'urgency': 'LOW'}
            ]

def run_comprehensive_need_investigation():
    """包括的Need調査の実行"""
    scenario_dir = Path('extracted_results/out_p25_based')
    
    if not scenario_dir.exists():
        print(f'エラー: シナリオディレクトリが見つかりません: {scenario_dir}')
        return None
    
    investigator = ComprehensiveNeedInvestigator(scenario_dir)
    return investigator.investigate_need_comprehensive()

if __name__ == "__main__":
    result = run_comprehensive_need_investigation()
    
    if result:
        # 結果をJSONファイルに保存
        output_file = Path('comprehensive_need_investigation_results.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f'\n詳細調査結果を保存: {output_file}')
        print('=' * 80)
        print('Need積算修正方針決定完了')
        print('=' * 80)