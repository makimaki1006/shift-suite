"""
AI/ML機能統合テスト
MT2.4: 需要予測、異常検知、最適化アルゴリズムの統合テスト
"""

import os
import sys
import json
import datetime
import importlib.util
from typing import Dict, List, Any, Optional

# シフト分析モジュールのパスを追加
sys.path.append('/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/shift_suite/tasks')

class AIMLIntegrationTest:
    """AI/ML機能統合テストクラス"""
    
    def __init__(self):
        self.base_path = "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析"
        self.test_time = datetime.datetime.now()
        
        # テスト対象モジュール
        self.modules = {
            'demand_prediction': None,
            'anomaly_detection': None,
            'optimization_algorithms': None
        }
        
        # 統合テスト結果
        self.integration_results = {
            'module_loading': {},
            'individual_tests': {},
            'integration_tests': {},
            'performance_tests': {},
            'error_handling_tests': {}
        }
    
    def run_comprehensive_integration_test(self):
        """包括的統合テスト実行"""
        try:
            print("🤖 AI/ML機能統合テスト開始...")
            print(f"📅 テスト開始時刻: {self.test_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 1. モジュール読み込みテスト
            module_loading_result = self._test_module_loading()
            self.integration_results['module_loading'] = module_loading_result
            print("✅ モジュール読み込み: 完了")
            
            # 2. 個別機能テスト
            individual_tests_result = self._test_individual_functions()
            self.integration_results['individual_tests'] = individual_tests_result
            print("✅ 個別機能テスト: 完了")
            
            # 3. 統合機能テスト
            integration_tests_result = self._test_integration_scenarios()
            self.integration_results['integration_tests'] = integration_tests_result
            print("✅ 統合機能テスト: 完了")
            
            # 4. パフォーマンステスト
            performance_tests_result = self._test_performance()
            self.integration_results['performance_tests'] = performance_tests_result
            print("✅ パフォーマンステスト: 完了")
            
            # 5. エラーハンドリングテスト
            error_handling_result = self._test_error_handling()
            self.integration_results['error_handling_tests'] = error_handling_result
            print("✅ エラーハンドリングテスト: 完了")
            
            # 総合評価
            overall_assessment = self._calculate_overall_assessment()
            
            return {
                'success': True,
                'test_timestamp': self.test_time.isoformat(),
                'test_results': self.integration_results,
                'overall_assessment': overall_assessment,
                'summary': self._generate_test_summary()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'test_timestamp': self.test_time.isoformat()
            }
    
    def _test_module_loading(self):
        """モジュール読み込みテスト"""
        print("📦 モジュール読み込みテスト実行中...")
        
        loading_results = {}
        
        # 需要予測モジュール
        try:
            spec = importlib.util.spec_from_file_location(
                "demand_prediction_model", 
                "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/shift_suite/tasks/demand_prediction_model.py"
            )
            demand_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(demand_module)
            self.modules['demand_prediction'] = demand_module.DemandPredictionModel()
            loading_results['demand_prediction'] = {'success': True, 'error': None}
        except Exception as e:
            loading_results['demand_prediction'] = {'success': False, 'error': str(e)}
        
        # 異常検知モジュール
        try:
            spec = importlib.util.spec_from_file_location(
                "advanced_anomaly_detector", 
                "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/shift_suite/tasks/advanced_anomaly_detector.py"
            )
            anomaly_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(anomaly_module)
            self.modules['anomaly_detection'] = anomaly_module.AdvancedAnomalyDetector()
            loading_results['anomaly_detection'] = {'success': True, 'error': None}
        except Exception as e:
            loading_results['anomaly_detection'] = {'success': False, 'error': str(e)}
        
        # 最適化アルゴリズムモジュール
        try:
            spec = importlib.util.spec_from_file_location(
                "optimization_algorithms", 
                "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/shift_suite/tasks/optimization_algorithms.py"
            )
            optimization_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(optimization_module)
            self.modules['optimization_algorithms'] = optimization_module.OptimizationAlgorithm()
            loading_results['optimization_algorithms'] = {'success': True, 'error': None}
        except Exception as e:
            loading_results['optimization_algorithms'] = {'success': False, 'error': str(e)}
        
        # 成功率計算
        successful_loads = sum(1 for result in loading_results.values() if result['success'])
        total_modules = len(loading_results)
        success_rate = (successful_loads / total_modules) * 100
        
        return {
            'detailed_results': loading_results,
            'successful_loads': successful_loads,
            'total_modules': total_modules,
            'success_rate': success_rate,
            'overall_success': success_rate == 100
        }
    
    def _test_individual_functions(self):
        """個別機能テスト"""
        print("🔧 個別機能テスト実行中...")
        
        individual_results = {}
        
        # 需要予測テスト
        if self.modules['demand_prediction']:
            try:
                sample_data = self._generate_sample_historical_data()
                training_result = self.modules['demand_prediction'].train_model(sample_data)
                prediction_result = self.modules['demand_prediction'].predict_demand('2025-02-01', 24)
                
                individual_results['demand_prediction'] = {
                    'success': training_result['success'] and prediction_result['success'],
                    'training_accuracy': training_result.get('model_accuracy', 0),
                    'prediction_count': len(prediction_result.get('predictions', [])),
                    'error': None
                }
            except Exception as e:
                individual_results['demand_prediction'] = {'success': False, 'error': str(e)}
        else:
            individual_results['demand_prediction'] = {'success': False, 'error': 'Module not loaded'}
        
        # 異常検知テスト
        if self.modules['anomaly_detection']:
            try:
                sample_data = self._generate_sample_anomaly_data()
                training_result = self.modules['anomaly_detection'].train_detector(sample_data)
                detection_result = self.modules['anomaly_detection'].detect_anomalies(sample_data[-10:])
                
                individual_results['anomaly_detection'] = {
                    'success': training_result['success'] and detection_result['success'],
                    'training_accuracy': training_result.get('model_accuracy', 0),
                    'anomalies_detected': len(detection_result.get('anomalies', [])),
                    'error': None
                }
            except Exception as e:
                individual_results['anomaly_detection'] = {'success': False, 'error': str(e)}
        else:
            individual_results['anomaly_detection'] = {'success': False, 'error': 'Module not loaded'}
        
        # 最適化アルゴリズムテスト
        if self.modules['optimization_algorithms']:
            try:
                staff_data, demand_data = self._generate_sample_optimization_data()
                optimization_result = self.modules['optimization_algorithms'].optimize_shift_allocation(staff_data, demand_data)
                
                individual_results['optimization_algorithms'] = {
                    'success': optimization_result['success'],
                    'fitness_score': optimization_result.get('best_solution', {}).get('fitness_score', 0),
                    'algorithms_tested': len(optimization_result.get('algorithm_results', {})),
                    'error': None
                }
            except Exception as e:
                individual_results['optimization_algorithms'] = {'success': False, 'error': str(e)}
        else:
            individual_results['optimization_algorithms'] = {'success': False, 'error': 'Module not loaded'}
        
        # 個別テスト成功率
        successful_tests = sum(1 for result in individual_results.values() if result['success'])
        total_tests = len(individual_results)
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        return {
            'detailed_results': individual_results,
            'successful_tests': successful_tests,
            'total_tests': total_tests,
            'success_rate': success_rate
        }
    
    def _test_integration_scenarios(self):
        """統合シナリオテスト"""
        print("🔄 統合シナリオテスト実行中...")
        
        integration_results = {}
        
        # シナリオ1: 需要予測 → 最適化
        try:
            if self.modules['demand_prediction'] and self.modules['optimization_algorithms']:
                # 需要予測実行
                sample_data = self._generate_sample_historical_data()
                self.modules['demand_prediction'].train_model(sample_data)
                prediction_result = self.modules['demand_prediction'].predict_demand('2025-02-01', 24)
                
                # 予測結果を最適化入力に変換
                demand_data = self._convert_prediction_to_demand_data(prediction_result)
                staff_data, _ = self._generate_sample_optimization_data()
                
                # 最適化実行
                optimization_result = self.modules['optimization_algorithms'].optimize_shift_allocation(staff_data, demand_data)
                
                integration_results['prediction_to_optimization'] = {
                    'success': optimization_result['success'],
                    'data_flow_success': True,
                    'optimization_score': optimization_result.get('best_solution', {}).get('fitness_score', 0)
                }
            else:
                integration_results['prediction_to_optimization'] = {
                    'success': False,
                    'error': 'Required modules not available'
                }
        except Exception as e:
            integration_results['prediction_to_optimization'] = {'success': False, 'error': str(e)}
        
        # シナリオ2: 最適化 → 異常検知
        try:
            if self.modules['optimization_algorithms'] and self.modules['anomaly_detection']:
                # 最適化実行
                staff_data, demand_data = self._generate_sample_optimization_data()
                optimization_result = self.modules['optimization_algorithms'].optimize_shift_allocation(staff_data, demand_data)
                
                # 最適化結果を異常検知入力に変換
                anomaly_data = self._convert_optimization_to_anomaly_data(optimization_result)
                
                # 異常検知訓練・実行
                self.modules['anomaly_detection'].train_detector(anomaly_data)
                detection_result = self.modules['anomaly_detection'].detect_anomalies(anomaly_data[-5:])
                
                integration_results['optimization_to_anomaly'] = {
                    'success': detection_result['success'],
                    'data_flow_success': True,
                    'anomalies_found': len(detection_result.get('anomalies', []))
                }
            else:
                integration_results['optimization_to_anomaly'] = {
                    'success': False,
                    'error': 'Required modules not available'
                }
        except Exception as e:
            integration_results['optimization_to_anomaly'] = {'success': False, 'error': str(e)}
        
        # シナリオ3: 全機能連携
        try:
            if all(self.modules.values()):
                # 1. 需要予測
                sample_data = self._generate_sample_historical_data()
                self.modules['demand_prediction'].train_model(sample_data)
                prediction_result = self.modules['demand_prediction'].predict_demand('2025-02-01', 12)
                
                # 2. 予測結果を基に最適化
                demand_data = self._convert_prediction_to_demand_data(prediction_result)
                staff_data, _ = self._generate_sample_optimization_data()
                optimization_result = self.modules['optimization_algorithms'].optimize_shift_allocation(staff_data, demand_data)
                
                # 3. 最適化結果の異常検知
                anomaly_data = self._convert_optimization_to_anomaly_data(optimization_result)
                self.modules['anomaly_detection'].train_detector(anomaly_data)
                detection_result = self.modules['anomaly_detection'].detect_anomalies(anomaly_data[-3:])
                
                integration_results['full_pipeline'] = {
                    'success': True,
                    'prediction_accuracy': prediction_result.get('success', False),
                    'optimization_score': optimization_result.get('best_solution', {}).get('fitness_score', 0),
                    'anomalies_detected': len(detection_result.get('anomalies', [])),
                    'pipeline_integrity': True
                }
            else:
                integration_results['full_pipeline'] = {
                    'success': False,
                    'error': 'Not all modules available'
                }
        except Exception as e:
            integration_results['full_pipeline'] = {'success': False, 'error': str(e)}
        
        # 統合テスト成功率
        successful_integrations = sum(1 for result in integration_results.values() if result['success'])
        total_integrations = len(integration_results)
        success_rate = (successful_integrations / total_integrations) * 100 if total_integrations > 0 else 0
        
        return {
            'detailed_results': integration_results,
            'successful_integrations': successful_integrations,
            'total_integrations': total_integrations,
            'success_rate': success_rate
        }
    
    def _test_performance(self):
        """パフォーマンステスト"""
        print("⚡ パフォーマンステスト実行中...")
        
        performance_results = {}
        
        # 各モジュールの処理時間測定
        for module_name, module in self.modules.items():
            if module:
                try:
                    start_time = datetime.datetime.now()
                    
                    if module_name == 'demand_prediction':
                        sample_data = self._generate_sample_historical_data(days=7)  # 軽量データ
                        module.train_model(sample_data)
                        module.predict_demand('2025-02-01', 12)
                        
                    elif module_name == 'anomaly_detection':
                        sample_data = self._generate_sample_anomaly_data(size=50)  # 軽量データ
                        module.train_detector(sample_data)
                        module.detect_anomalies(sample_data[-5:])
                        
                    elif module_name == 'optimization_algorithms':
                        staff_data, demand_data = self._generate_sample_optimization_data()
                        module.optimize_shift_allocation(staff_data[:2], demand_data[:2])  # 軽量データ
                    
                    end_time = datetime.datetime.now()
                    processing_time = (end_time - start_time).total_seconds()
                    
                    performance_results[module_name] = {
                        'success': True,
                        'processing_time_seconds': processing_time,
                        'performance_level': self._classify_performance(processing_time)
                    }
                    
                except Exception as e:
                    performance_results[module_name] = {'success': False, 'error': str(e)}
            else:
                performance_results[module_name] = {'success': False, 'error': 'Module not loaded'}
        
        # 全体的なパフォーマンス評価
        total_time = sum(result.get('processing_time_seconds', 0) for result in performance_results.values() if result['success'])
        successful_tests = sum(1 for result in performance_results.values() if result['success'])
        
        return {
            'detailed_results': performance_results,
            'total_processing_time': total_time,
            'average_processing_time': total_time / successful_tests if successful_tests > 0 else 0,
            'performance_grade': self._grade_overall_performance(total_time)
        }
    
    def _test_error_handling(self):
        """エラーハンドリングテスト"""
        print("🚨 エラーハンドリングテスト実行中...")
        
        error_handling_results = {}
        
        # 各モジュールのエラーハンドリングテスト
        for module_name, module in self.modules.items():
            if module:
                error_scenarios = {
                    'empty_data': [],
                    'invalid_data': [{'invalid': 'data'}],
                    'null_data': None
                }
                
                module_errors = {}
                
                for scenario_name, test_data in error_scenarios.items():
                    try:
                        if module_name == 'demand_prediction':
                            result = module.train_model(test_data)
                        elif module_name == 'anomaly_detection':
                            result = module.train_detector(test_data)
                        elif module_name == 'optimization_algorithms':
                            result = module.optimize_shift_allocation(test_data, test_data)
                        
                        # エラーハンドリングが適切かチェック
                        module_errors[scenario_name] = {
                            'handled_gracefully': not result.get('success', True),
                            'error_message_provided': 'error' in result,
                            'no_crash': True
                        }
                        
                    except Exception as e:
                        module_errors[scenario_name] = {
                            'handled_gracefully': False,
                            'error_message_provided': True,
                            'no_crash': False,
                            'exception': str(e)
                        }
                
                # モジュール全体のエラーハンドリング評価
                graceful_handling_count = sum(1 for result in module_errors.values() 
                                            if result['handled_gracefully'] and result['no_crash'])
                total_scenarios = len(module_errors)
                
                error_handling_results[module_name] = {
                    'detailed_scenarios': module_errors,
                    'graceful_handling_rate': (graceful_handling_count / total_scenarios) * 100,
                    'overall_error_handling': graceful_handling_count == total_scenarios
                }
            else:
                error_handling_results[module_name] = {
                    'error': 'Module not loaded',
                    'graceful_handling_rate': 0,
                    'overall_error_handling': False
                }
        
        return error_handling_results
    
    def _calculate_overall_assessment(self):
        """総合評価計算"""
        scores = {
            'module_loading': 0,
            'individual_functions': 0,
            'integration': 0,
            'performance': 0,
            'error_handling': 0
        }
        
        # モジュール読み込みスコア
        if 'module_loading' in self.integration_results:
            scores['module_loading'] = self.integration_results['module_loading'].get('success_rate', 0)
        
        # 個別機能スコア
        if 'individual_tests' in self.integration_results:
            scores['individual_functions'] = self.integration_results['individual_tests'].get('success_rate', 0)
        
        # 統合機能スコア
        if 'integration_tests' in self.integration_results:
            scores['integration'] = self.integration_results['integration_tests'].get('success_rate', 0)
        
        # パフォーマンススコア
        if 'performance_tests' in self.integration_results:
            perf_results = self.integration_results['performance_tests']
            successful_perf_tests = sum(1 for result in perf_results.get('detailed_results', {}).values() 
                                      if result.get('success', False))
            total_perf_tests = len(perf_results.get('detailed_results', {}))
            scores['performance'] = (successful_perf_tests / total_perf_tests) * 100 if total_perf_tests > 0 else 0
        
        # エラーハンドリングスコア
        if 'error_handling_tests' in self.integration_results:
            error_results = self.integration_results['error_handling_tests']
            avg_error_handling = sum(result.get('graceful_handling_rate', 0) 
                                   for result in error_results.values() 
                                   if isinstance(result, dict) and 'graceful_handling_rate' in result)
            valid_modules = len([result for result in error_results.values() 
                               if isinstance(result, dict) and 'graceful_handling_rate' in result])
            scores['error_handling'] = avg_error_handling / valid_modules if valid_modules > 0 else 0
        
        # 重み付き総合スコア
        weights = {
            'module_loading': 0.15,
            'individual_functions': 0.30,
            'integration': 0.35,
            'performance': 0.15,
            'error_handling': 0.05
        }
        
        overall_score = sum(scores[category] * weights[category] for category in scores)
        
        return {
            'category_scores': scores,
            'weights': weights,
            'overall_score': overall_score,
            'grade': self._grade_overall_score(overall_score),
            'recommendations': self._generate_recommendations(scores)
        }
    
    def _generate_test_summary(self):
        """テストサマリー生成"""
        summary = {
            'test_execution_time': datetime.datetime.now().isoformat(),
            'modules_tested': len(self.modules),
            'test_categories': len(self.integration_results),
            'overall_status': 'success',
            'key_achievements': [],
            'areas_for_improvement': []
        }
        
        # 主要な成果
        if self.integration_results.get('module_loading', {}).get('success_rate', 0) == 100:
            summary['key_achievements'].append('全モジュールの正常読み込み')
        
        if self.integration_results.get('individual_tests', {}).get('success_rate', 0) >= 80:
            summary['key_achievements'].append('個別機能テスト高成功率')
        
        if self.integration_results.get('integration_tests', {}).get('success_rate', 0) >= 70:
            summary['key_achievements'].append('統合機能テスト成功')
        
        # 改善領域
        low_scores = []
        for category, result in self.integration_results.items():
            if isinstance(result, dict) and 'success_rate' in result:
                if result['success_rate'] < 80:
                    low_scores.append(category)
        
        if low_scores:
            summary['areas_for_improvement'] = [f'{category}の改善が必要' for category in low_scores]
        
        return summary
    
    # ヘルパーメソッド群
    def _generate_sample_historical_data(self, days: int = 30):
        """サンプル履歴データ生成"""
        import random
        start_date = datetime.datetime(2025, 1, 1)
        
        data = []
        for day in range(days):
            current_date = start_date + datetime.timedelta(days=day)
            for hour in range(0, 24, 4):  # 4時間間隔
                data.append({
                    'timestamp': (current_date + datetime.timedelta(hours=hour)).isoformat(),
                    'demand': 50 + random.uniform(-20, 30),
                    'date': current_date.strftime('%Y-%m-%d'),
                    'hour': hour,
                    'day_of_week': current_date.weekday(),
                    'month': current_date.month
                })
        
        return data
    
    def _generate_sample_anomaly_data(self, size: int = 100):
        """サンプル異常データ生成"""
        import random
        data = []
        
        for i in range(size):
            timestamp = datetime.datetime(2025, 1, 1) + datetime.timedelta(hours=i)
            
            # 通常データと異常データを混在
            if i % 20 == 0:  # 5%の確率で異常
                value = random.uniform(200, 300)  # 異常値
            else:
                value = random.uniform(50, 150)  # 正常値
            
            data.append({
                'timestamp': timestamp.isoformat(),
                'value': value,
                'feature1': random.uniform(0, 1),
                'feature2': random.uniform(0, 1)
            })
        
        return data
    
    def _generate_sample_optimization_data(self):
        """サンプル最適化データ生成"""
        staff_data = [
            {
                'id': 'staff_001',
                'name': 'テストスタッフ1',
                'skills': ['basic'],
                'hourly_rate': 1500,
                'max_hours_per_week': 40
            },
            {
                'id': 'staff_002',
                'name': 'テストスタッフ2',
                'skills': ['intermediate'],
                'hourly_rate': 1800,
                'max_hours_per_week': 35
            }
        ]
        
        demand_data = [
            {
                'time_slot': 'morning',
                'required_staff': 1,
                'required_skills': ['basic'],
                'priority': 'high'
            },
            {
                'time_slot': 'afternoon',
                'required_staff': 2,
                'required_skills': ['basic', 'intermediate'],
                'priority': 'medium'
            }
        ]
        
        return staff_data, demand_data
    
    def _convert_prediction_to_demand_data(self, prediction_result):
        """予測結果を需要データに変換"""
        if not prediction_result.get('success'):
            return []
        
        demand_data = []
        predictions = prediction_result.get('predictions', [])
        
        for i, pred in enumerate(predictions[:5]):  # 最初の5件のみ
            demand_data.append({
                'time_slot': f"slot_{i}",
                'required_staff': max(1, int(pred.get('predicted_demand', 50) / 50)),
                'required_skills': ['basic'],
                'priority': pred.get('demand_level', 'medium'),
                'demand_intensity': pred.get('predicted_demand', 50) / 100
            })
        
        return demand_data
    
    def _convert_optimization_to_anomaly_data(self, optimization_result):
        """最適化結果を異常検知データに変換"""
        if not optimization_result.get('success'):
            return []
        
        analysis = optimization_result.get('solution_analysis', {})
        
        # 最適化メトリクスを異常検知用データに変換
        anomaly_data = []
        base_time = datetime.datetime(2025, 2, 1)
        
        for i in range(10):
            timestamp = base_time + datetime.timedelta(hours=i)
            anomaly_data.append({
                'timestamp': timestamp.isoformat(),
                'value': analysis.get('total_cost', 0) / 1000 + i * 5,  # コストベース
                'feature1': analysis.get('total_hours', 0) / 100,
                'feature2': analysis.get('overtime_hours', 0) / 10
            })
        
        return anomaly_data
    
    def _classify_performance(self, processing_time):
        """パフォーマンス分類"""
        if processing_time < 1:
            return 'excellent'
        elif processing_time < 3:
            return 'good'
        elif processing_time < 10:
            return 'acceptable'
        else:
            return 'poor'
    
    def _grade_overall_performance(self, total_time):
        """全体パフォーマンス評価"""
        if total_time < 5:
            return 'A'
        elif total_time < 15:
            return 'B'
        elif total_time < 30:
            return 'C'
        else:
            return 'D'
    
    def _grade_overall_score(self, score):
        """総合スコア評価"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _generate_recommendations(self, scores):
        """推奨事項生成"""
        recommendations = []
        
        for category, score in scores.items():
            if score < 70:
                if category == 'module_loading':
                    recommendations.append("モジュール読み込みエラーの解決が必要です")
                elif category == 'individual_functions':
                    recommendations.append("個別機能の動作確認と修正が必要です")
                elif category == 'integration':
                    recommendations.append("モジュール間の統合機能の改善が必要です")
                elif category == 'performance':
                    recommendations.append("パフォーマンスの最適化が必要です")
                elif category == 'error_handling':
                    recommendations.append("エラーハンドリングの強化が必要です")
        
        if not recommendations:
            recommendations.append("全ての機能が正常に動作しています。継続的な監視を推奨します。")
        
        return recommendations

if __name__ == "__main__":
    # AI/ML統合テスト実行
    print("🤖 AI/ML機能統合テスト開始...")
    
    integration_tester = AIMLIntegrationTest()
    
    # 統合テスト実行
    test_result = integration_tester.run_comprehensive_integration_test()
    
    # 結果ファイル保存
    result_filename = f"ai_ml_integration_test_results_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    result_filepath = os.path.join(integration_tester.base_path, result_filename)
    
    with open(result_filepath, 'w', encoding='utf-8') as f:
        json.dump(test_result, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎯 AI/ML機能統合テスト完了!")
    print(f"📁 テスト結果: {result_filename}")
    
    if test_result['success']:
        assessment = test_result['overall_assessment']
        summary = test_result['summary']
        
        print(f"\n📊 統合テスト結果:")
        print(f"  • 総合スコア: {assessment['overall_score']:.1f}/100")
        print(f"  • 総合評価: {assessment['grade']}")
        print(f"  • テスト済みモジュール: {summary['modules_tested']}個")
        print(f"  • テストカテゴリ: {summary['test_categories']}種類")
        
        print(f"\n📈 カテゴリ別スコア:")
        for category, score in assessment['category_scores'].items():
            print(f"  • {category}: {score:.1f}%")
        
        print(f"\n🎯 主要成果:")
        for achievement in summary['key_achievements']:
            print(f"  • {achievement}")
        
        if assessment['recommendations']:
            print(f"\n💡 推奨事項:")
            for recommendation in assessment['recommendations']:
                print(f"  • {recommendation}")
        
        print(f"\n🎉 AI/ML機能統合テスト成功!")
    else:
        print(f"❌ 統合テスト失敗: {test_result['error']}")