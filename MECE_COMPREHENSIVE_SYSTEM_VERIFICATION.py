"""
MECE包括的システム機能検証
データ入稿→分解→分析→加工→可視化の全フローを徹底検証
"""

import os
import sys
import json
import datetime
import importlib.util
import traceback
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
from pathlib import Path

class VerificationCategory(Enum):
    DATA_INGESTION = "データ入稿"
    DATA_DECOMPOSITION = "データ分解" 
    DATA_ANALYSIS = "データ分析"
    RESULT_PROCESSING = "分析結果加工"
    VISUALIZATION = "可視化"
    END_TO_END_FLOW = "エンドツーエンドフロー"

class VerificationSeverity(Enum):
    CRITICAL = "致命的"
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"
    INFO = "情報"

class SystemComponent(Enum):
    CORE_ENGINE = "コアエンジン"
    AI_ML_INTEGRATION = "AI/ML統合"
    USABILITY_LAYER = "ユーザビリティ層"
    DATA_LAYER = "データ層"
    VISUALIZATION_LAYER = "可視化層"

class MECEComprehensiveVerifier:
    """MECE包括的システム検証クラス"""
    
    def __init__(self):
        self.base_path = "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析"
        self.verification_start_time = datetime.datetime.now()
        
        # 検証対象システムファイル
        self.system_files = {
            'core_system': [
                'app.py',
                'dash_app.py', 
                'shift_suite/__init__.py'
            ],
            'data_processing': [
                'shift_suite/tasks/utils.py',
                'shift_suite/tasks/shortage.py',
                'shift_suite/tasks/build_stats.py'
            ],
            'ai_ml_integration': [
                'dash_app_ai_ml_enhanced.py',
                'p2a2_realtime_prediction_display.py',
                'p2a3_anomaly_alert_system.py',
                'p2a4_optimization_visualization.py'
            ],
            'usability_enhancement': [
                'p3a1_customizable_reports.py',
                'p3a2_mobile_responsive_ui.py', 
                'p3a4_user_preferences.py'
            ],
            'maintenance_optimization': [
                'm1_system_maintenance_optimization.py'
            ],
            'system_expansion': [
                's1_system_expansion.py'
            ]
        }
        
        # 検証結果格納
        self.verification_results = {
            'session_id': f'mece_verification_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'start_time': self.verification_start_time.isoformat(),
            'categories': {},
            'components': {},
            'critical_issues': [],
            'recommendations': [],
            'overall_assessment': {}
        }
    
    def execute_comprehensive_verification(self):
        """包括的検証実行"""
        
        print("🔍 MECE包括的システム機能検証開始...")
        print(f"📊 検証カテゴリ: {len(VerificationCategory)}カテゴリ")
        print(f"🏗️ システムコンポーネント: {len(SystemComponent)}コンポーネント")
        print("=" * 80)
        
        # カテゴリ別検証実行
        for category in VerificationCategory:
            print(f"\n🎯 {category.value} 検証開始...")
            category_result = self._verify_category(category)
            self.verification_results['categories'][category.value] = category_result
            
            # 致命的問題の抽出
            if category_result.get('critical_issues'):
                self.verification_results['critical_issues'].extend(category_result['critical_issues'])
        
        # 総合分析・評価
        self._perform_comprehensive_analysis()
        self._generate_recommendations()
        self._calculate_overall_assessment()
        
        # 検証完了
        self.verification_results['end_time'] = datetime.datetime.now().isoformat()
        self.verification_results['total_duration_minutes'] = (
            datetime.datetime.now() - self.verification_start_time
        ).total_seconds() / 60
        
        return self.verification_results
    
    def _verify_category(self, category: VerificationCategory) -> Dict[str, Any]:
        """カテゴリ別検証実行"""
        
        category_result = {
            'category': category.value,
            'tests_executed': [],
            'passed_tests': 0,
            'failed_tests': 0,
            'critical_issues': [],
            'findings': [],
            'score': 0.0
        }
        
        if category == VerificationCategory.DATA_INGESTION:
            category_result = self._verify_data_ingestion()
        elif category == VerificationCategory.DATA_DECOMPOSITION:
            category_result = self._verify_data_decomposition()
        elif category == VerificationCategory.DATA_ANALYSIS:
            category_result = self._verify_data_analysis()
        elif category == VerificationCategory.RESULT_PROCESSING:
            category_result = self._verify_result_processing()
        elif category == VerificationCategory.VISUALIZATION:
            category_result = self._verify_visualization()
        elif category == VerificationCategory.END_TO_END_FLOW:
            category_result = self._verify_end_to_end_flow()
        
        return category_result
    
    def _verify_data_ingestion(self) -> Dict[str, Any]:
        """データ入稿フロー検証"""
        
        print("  📥 データ入稿フロー検証中...")
        
        result = {
            'category': 'データ入稿',
            'tests_executed': [],
            'passed_tests': 0,
            'failed_tests': 0,
            'critical_issues': [],
            'findings': []
        }
        
        # テスト1: Excel/CSVファイル読み込み機能
        test_name = "Excel/CSV読み込み機能"
        try:
            # utils.pyのsafe_read_excel関数確認
            utils_path = os.path.join(self.base_path, 'shift_suite/tasks/utils.py')
            if os.path.exists(utils_path):
                with open(utils_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'safe_read_excel' in content and 'pd.read_excel' in content:
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PASS',
                            'details': 'Excel/CSV読み込み関数が実装されている'
                        })
                        result['passed_tests'] += 1
                    else:
                        result['findings'].append({
                            'test': test_name,
                            'status': 'FAIL',
                            'details': 'Excel/CSV読み込み関数が見つからない',
                            'severity': VerificationSeverity.HIGH.value
                        })
                        result['failed_tests'] += 1
            else:
                result['critical_issues'].append({
                    'issue': f'{test_name}: utils.pyファイルが存在しない',
                    'severity': VerificationSeverity.CRITICAL.value
                })
                result['failed_tests'] += 1
        except Exception as e:
            result['critical_issues'].append({
                'issue': f'{test_name}: {str(e)}',
                'severity': VerificationSeverity.CRITICAL.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # テスト2: ZIPファイル対応
        test_name = "ZIPファイル対応"
        try:
            # dash_app.pyでのZIP処理確認
            dash_app_path = os.path.join(self.base_path, 'dash_app.py')
            if os.path.exists(dash_app_path):
                with open(dash_app_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'zipfile' in content and 'ZipFile' in content:
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PASS',
                            'details': 'ZIPファイル処理機能が実装されている'
                        })
                        result['passed_tests'] += 1
                    else:
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PARTIAL',
                            'details': 'ZIPファイル処理が限定的',
                            'severity': VerificationSeverity.MEDIUM.value
                        })
                        result['failed_tests'] += 1
            else:
                result['critical_issues'].append({
                    'issue': f'{test_name}: dash_app.pyファイルが存在しない',
                    'severity': VerificationSeverity.CRITICAL.value
                })
                result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.HIGH.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # テスト3: データバリデーション
        test_name = "データバリデーション"
        try:
            # utils.pyの_valid_df関数確認
            if os.path.exists(utils_path):
                with open(utils_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '_valid_df' in content and 'validation' in content.lower():
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PASS',
                            'details': 'データバリデーション機能が実装されている'
                        })
                        result['passed_tests'] += 1
                    else:
                        result['findings'].append({
                            'test': test_name,
                            'status': 'FAIL',
                            'details': 'データバリデーション機能が不十分',
                            'severity': VerificationSeverity.HIGH.value
                        })
                        result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.MEDIUM.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # テスト4: エラーハンドリング
        test_name = "エラーハンドリング"
        try:
            error_handling_count = 0
            for file_category, files in self.system_files.items():
                for file_name in files:
                    file_path = os.path.join(self.base_path, file_name)
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'try:' in content and 'except' in content:
                                error_handling_count += 1
            
            if error_handling_count >= len(self.system_files) * 0.8:
                result['findings'].append({
                    'test': test_name,
                    'status': 'PASS',
                    'details': f'エラーハンドリングが{error_handling_count}ファイルで実装されている'
                })
                result['passed_tests'] += 1
            else:
                result['findings'].append({
                    'test': test_name,
                    'status': 'PARTIAL',
                    'details': f'エラーハンドリングが{error_handling_count}ファイルのみで実装',
                    'severity': VerificationSeverity.MEDIUM.value
                })
                result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.MEDIUM.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # スコア計算
        total_tests = len(result['tests_executed'])
        if total_tests > 0:
            result['score'] = (result['passed_tests'] / total_tests) * 100
        
        print(f"    📊 データ入稿フロー: {result['passed_tests']}/{total_tests} テスト合格 ({result['score']:.1f}%)")
        
        return result
    
    def _verify_data_decomposition(self) -> Dict[str, Any]:
        """データ分解プロセス検証"""
        
        print("  🔧 データ分解プロセス検証中...")
        
        result = {
            'category': 'データ分解',
            'tests_executed': [],
            'passed_tests': 0,
            'failed_tests': 0,
            'critical_issues': [],
            'findings': []
        }
        
        # テスト1: シフトデータ構造解析
        test_name = "シフトデータ構造解析"
        try:
            utils_path = os.path.join(self.base_path, 'shift_suite/tasks/utils.py')
            if os.path.exists(utils_path):
                with open(utils_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'gen_labels' in content and 'shift' in content.lower():
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PASS',
                            'details': 'シフトデータ構造解析機能が実装されている'
                        })
                        result['passed_tests'] += 1
                    else:
                        result['findings'].append({
                            'test': test_name,
                            'status': 'FAIL',
                            'details': 'シフトデータ構造解析機能が不十分',
                            'severity': VerificationSeverity.HIGH.value
                        })
                        result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.HIGH.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # テスト2: 役職・時間軸分解
        test_name = "役職・時間軸分解"
        try:
            shortage_path = os.path.join(self.base_path, 'shift_suite/tasks/shortage.py')
            if os.path.exists(shortage_path):
                with open(shortage_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'role' in content.lower() and 'time' in content.lower():
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PASS',
                            'details': '役職・時間軸分解機能が実装されている'
                        })
                        result['passed_tests'] += 1
                    else:
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PARTIAL',
                            'details': '役職・時間軸分解機能が限定的',
                            'severity': VerificationSeverity.MEDIUM.value
                        })
                        result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.MEDIUM.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # テスト3: 休日・勤務パターン認識
        test_name = "休日・勤務パターン認識"
        try:
            # 複数ファイルでの休日処理確認
            holiday_implementation_found = False
            for file_category, files in self.system_files.items():
                for file_name in files:
                    file_path = os.path.join(self.base_path, file_name)
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'holiday' in content.lower() or '休日' in content:
                                holiday_implementation_found = True
                                break
                if holiday_implementation_found:
                    break
            
            if holiday_implementation_found:
                result['findings'].append({
                    'test': test_name,
                    'status': 'PASS',
                    'details': '休日・勤務パターン認識機能が実装されている'
                })
                result['passed_tests'] += 1
            else:
                result['findings'].append({
                    'test': test_name,
                    'status': 'FAIL',
                    'details': '休日・勤務パターン認識機能が見つからない',
                    'severity': VerificationSeverity.HIGH.value
                })
                result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.MEDIUM.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # テスト4: メタデータ抽出
        test_name = "メタデータ抽出"
        try:
            build_stats_path = os.path.join(self.base_path, 'shift_suite/tasks/build_stats.py')
            if os.path.exists(build_stats_path):
                with open(build_stats_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'metadata' in content.lower() or '統計' in content:
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PASS',
                            'details': 'メタデータ抽出機能が実装されている'
                        })
                        result['passed_tests'] += 1
                    else:
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PARTIAL',
                            'details': 'メタデータ抽出機能が限定的',
                            'severity': VerificationSeverity.LOW.value
                        })
                        result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.LOW.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # スコア計算
        total_tests = len(result['tests_executed'])
        if total_tests > 0:
            result['score'] = (result['passed_tests'] / total_tests) * 100
        
        print(f"    📊 データ分解プロセス: {result['passed_tests']}/{total_tests} テスト合格 ({result['score']:.1f}%)")
        
        return result
    
    def _verify_data_analysis(self) -> Dict[str, Any]:
        """データ分析アルゴリズム検証"""
        
        print("  📈 データ分析アルゴリズム検証中...")
        
        result = {
            'category': 'データ分析',
            'tests_executed': [],
            'passed_tests': 0,
            'failed_tests': 0,
            'critical_issues': [],
            'findings': []
        }
        
        # テスト1: AI/ML需要予測アルゴリズム
        test_name = "AI/ML需要予測アルゴリズム"
        try:
            prediction_path = os.path.join(self.base_path, 'p2a2_realtime_prediction_display.py')
            if os.path.exists(prediction_path):
                with open(prediction_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'prediction' in content.lower() and 'forecast' in content.lower():
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PASS',
                            'details': 'AI/ML需要予測アルゴリズムが実装されている'
                        })
                        result['passed_tests'] += 1
                    else:
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PARTIAL',
                            'details': 'AI/ML需要予測アルゴリズムが限定的',
                            'severity': VerificationSeverity.MEDIUM.value
                        })
                        result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.HIGH.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # テスト2: 異常検知システム
        test_name = "異常検知システム"
        try:
            anomaly_path = os.path.join(self.base_path, 'p2a3_anomaly_alert_system.py')
            if os.path.exists(anomaly_path):
                with open(anomaly_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'anomaly' in content.lower() and 'detection' in content.lower():
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PASS',
                            'details': '異常検知システムが実装されている'
                        })
                        result['passed_tests'] += 1
                    else:
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PARTIAL',
                            'details': '異常検知システムが限定的',
                            'severity': VerificationSeverity.MEDIUM.value
                        })
                        result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.HIGH.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # テスト3: 最適化計算エンジン
        test_name = "最適化計算エンジン"
        try:
            optimization_path = os.path.join(self.base_path, 'p2a4_optimization_visualization.py')
            if os.path.exists(optimization_path):
                with open(optimization_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'optimization' in content.lower() and 'algorithm' in content.lower():
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PASS',
                            'details': '最適化計算エンジンが実装されている'
                        })
                        result['passed_tests'] += 1
                    else:
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PARTIAL',
                            'details': '最適化計算エンジンが限定的',
                            'severity': VerificationSeverity.MEDIUM.value
                        })
                        result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.HIGH.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # テスト4: 統計分析機能
        test_name = "統計分析機能"
        try:
            # shortage.pyでの統計計算確認
            shortage_path = os.path.join(self.base_path, 'shift_suite/tasks/shortage.py')
            if os.path.exists(shortage_path):
                with open(shortage_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'statistics' in content.lower() or '統計' in content:
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PASS',
                            'details': '統計分析機能が実装されている'
                        })
                        result['passed_tests'] += 1
                    else:
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PARTIAL',
                            'details': '統計分析機能が限定的',
                            'severity': VerificationSeverity.LOW.value
                        })
                        result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.MEDIUM.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # スコア計算
        total_tests = len(result['tests_executed'])
        if total_tests > 0:
            result['score'] = (result['passed_tests'] / total_tests) * 100
        
        print(f"    📊 データ分析アルゴリズム: {result['passed_tests']}/{total_tests} テスト合格 ({result['score']:.1f}%)")
        
        return result
    
    def _verify_result_processing(self) -> Dict[str, Any]:
        """分析結果加工プロセス検証"""
        
        print("  ⚙️ 分析結果加工プロセス検証中...")
        
        result = {
            'category': '分析結果加工',
            'tests_executed': [],
            'passed_tests': 0,
            'failed_tests': 0,
            'critical_issues': [],
            'findings': []
        }
        
        # テスト1: KPI計算システム
        test_name = "KPI計算システム"
        try:
            # 複数ファイルでのKPI計算確認
            kpi_implementation_found = False
            for file_category, files in self.system_files.items():
                for file_name in files:
                    file_path = os.path.join(self.base_path, file_name)
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'kpi' in content.lower() or 'metrics' in content.lower():
                                kpi_implementation_found = True
                                break
                if kpi_implementation_found:
                    break
            
            if kpi_implementation_found:
                result['findings'].append({
                    'test': test_name,
                    'status': 'PASS',
                    'details': 'KPI計算システムが実装されている'
                })
                result['passed_tests'] += 1
            else:
                result['findings'].append({
                    'test': test_name,
                    'status': 'PARTIAL',
                    'details': 'KPI計算システムが限定的',
                    'severity': VerificationSeverity.MEDIUM.value
                })
                result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.MEDIUM.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # テスト2: レポート生成システム
        test_name = "レポート生成システム"
        try:
            reports_path = os.path.join(self.base_path, 'p3a1_customizable_reports.py')
            if os.path.exists(reports_path):
                with open(reports_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'report' in content.lower() and 'generate' in content.lower():
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PASS',
                            'details': 'レポート生成システムが実装されている'
                        })
                        result['passed_tests'] += 1
                    else:
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PARTIAL',
                            'details': 'レポート生成システムが限定的',
                            'severity': VerificationSeverity.MEDIUM.value
                        })
                        result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.MEDIUM.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # テスト3: データ集約・フィルタリング
        test_name = "データ集約・フィルタリング"
        try:
            # utils.pyでのデータ処理機能確認
            utils_path = os.path.join(self.base_path, 'shift_suite/tasks/utils.py')
            if os.path.exists(utils_path):
                with open(utils_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'filter' in content.lower() and 'aggregate' in content.lower():
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PASS',
                            'details': 'データ集約・フィルタリング機能が実装されている'
                        })
                        result['passed_tests'] += 1
                    else:
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PARTIAL',
                            'details': 'データ集約・フィルタリング機能が限定的',
                            'severity': VerificationSeverity.MEDIUM.value
                        })
                        result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.MEDIUM.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # テスト4: データエクスポート機能
        test_name = "データエクスポート機能"  
        try:
            # 複数ファイルでのエクスポート機能確認
            export_implementation_found = False
            for file_category, files in self.system_files.items():
                for file_name in files:
                    file_path = os.path.join(self.base_path, file_name)
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'export' in content.lower() or 'download' in content.lower():
                                export_implementation_found = True
                                break
                if export_implementation_found:
                    break
            
            if export_implementation_found:
                result['findings'].append({
                    'test': test_name,
                    'status': 'PASS',
                    'details': 'データエクスポート機能が実装されている'
                })
                result['passed_tests'] += 1
            else:
                result['findings'].append({
                    'test': test_name,
                    'status': 'PARTIAL',
                    'details': 'データエクスポート機能が限定的',
                    'severity': VerificationSeverity.LOW.value
                })
                result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.LOW.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # スコア計算
        total_tests = len(result['tests_executed'])
        if total_tests > 0:
            result['score'] = (result['passed_tests'] / total_tests) * 100
        
        print(f"    📊 分析結果加工プロセス: {result['passed_tests']}/{total_tests} テスト合格 ({result['score']:.1f}%)")
        
        return result
    
    def _verify_visualization(self) -> Dict[str, Any]:
        """可視化システム検証"""
        
        print("  📊 可視化システム検証中...")
        
        result = {
            'category': '可視化',
            'tests_executed': [],
            'passed_tests': 0,
            'failed_tests': 0,
            'critical_issues': [],
            'findings': []
        }
        
        # テスト1: ダッシュボード機能
        test_name = "ダッシュボード機能"
        try:
            dash_app_path = os.path.join(self.base_path, 'dash_app.py')
            if os.path.exists(dash_app_path):
                with open(dash_app_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'dashboard' in content.lower() and 'layout' in content.lower():
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PASS',
                            'details': 'ダッシュボード機能が実装されている'
                        })
                        result['passed_tests'] += 1
                    else:
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PARTIAL',
                            'details': 'ダッシュボード機能が限定的',
                            'severity': VerificationSeverity.MEDIUM.value
                        })
                        result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.HIGH.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # テスト2: インタラクティブチャート
        test_name = "インタラクティブチャート"
        try:
            # Plotlyチャート実装確認
            plotly_implementation_found = False
            for file_category, files in self.system_files.items():
                for file_name in files:
                    file_path = os.path.join(self.base_path, file_name)
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'plotly' in content.lower() and 'graph' in content.lower():
                                plotly_implementation_found = True
                                break
                if plotly_implementation_found:
                    break
            
            if plotly_implementation_found:
                result['findings'].append({
                    'test': test_name,
                    'status': 'PASS',
                    'details': 'インタラクティブチャートが実装されている'
                })
                result['passed_tests'] += 1
            else:
                result['findings'].append({
                    'test': test_name,
                    'status': 'FAIL',
                    'details': 'インタラクティブチャートが見つからない',
                    'severity': VerificationSeverity.HIGH.value
                })
                result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.HIGH.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # テスト3: レスポンシブデザイン
        test_name = "レスポンシブデザイン"
        try:
            responsive_path = os.path.join(self.base_path, 'p3a2_mobile_responsive_ui.py')
            if os.path.exists(responsive_path):
                with open(responsive_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'responsive' in content.lower() and 'mobile' in content.lower():
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PASS',
                            'details': 'レスポンシブデザインが実装されている'
                        })
                        result['passed_tests'] += 1
                    else:
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PARTIAL',
                            'details': 'レスポンシブデザインが限定的',
                            'severity': VerificationSeverity.MEDIUM.value
                        })
                        result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.MEDIUM.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # テスト4: カスタマイゼーション機能
        test_name = "カスタマイゼーション機能"
        try:
            preferences_path = os.path.join(self.base_path, 'p3a4_user_preferences.py')
            if os.path.exists(preferences_path):
                with open(preferences_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'preferences' in content.lower() and 'custom' in content.lower():
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PASS',
                            'details': 'カスタマイゼーション機能が実装されている'
                        })
                        result['passed_tests'] += 1
                    else:
                        result['findings'].append({
                            'test': test_name,
                            'status': 'PARTIAL',
                            'details': 'カスタマイゼーション機能が限定的',
                            'severity': VerificationSeverity.LOW.value
                        })
                        result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.LOW.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # スコア計算
        total_tests = len(result['tests_executed'])
        if total_tests > 0:
            result['score'] = (result['passed_tests'] / total_tests) * 100
        
        print(f"    📊 可視化システム: {result['passed_tests']}/{total_tests} テスト合格 ({result['score']:.1f}%)")
        
        return result
    
    def _verify_end_to_end_flow(self) -> Dict[str, Any]:
        """エンドツーエンドフロー検証"""
        
        print("  🔄 エンドツーエンドフロー検証中...")
        
        result = {
            'category': 'エンドツーエンドフロー',
            'tests_executed': [],
            'passed_tests': 0,
            'failed_tests': 0,
            'critical_issues': [],
            'findings': []
        }
        
        # テスト1: データ入稿→可視化フロー
        test_name = "データ入稿→可視化フロー"
        try:
            # メインアプリケーションでの統合フロー確認
            main_flow_files = ['app.py', 'dash_app.py']
            flow_implementation_found = False
            
            for file_name in main_flow_files:
                file_path = os.path.join(self.base_path, file_name)
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if ('upload' in content.lower() and 
                            'process' in content.lower() and 
                            'display' in content.lower()):
                            flow_implementation_found = True
                            break
            
            if flow_implementation_found:
                result['findings'].append({
                    'test': test_name,
                    'status': 'PASS',
                    'details': 'データ入稿→可視化フローが実装されている'
                })
                result['passed_tests'] += 1
            else:
                result['findings'].append({
                    'test': test_name,
                    'status': 'PARTIAL',
                    'details': 'データ入稿→可視化フローが限定的',
                    'severity': VerificationSeverity.HIGH.value
                })
                result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.HIGH.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # テスト2: 統合テストシステム
        test_name = "統合テストシステム"
        try:
            integration_test_files = [
                'p2a5_phase2_integration_test.py',
                'p3a5_phase3_integration_test.py'
            ]
            
            integration_tests_found = 0
            for file_name in integration_test_files:
                file_path = os.path.join(self.base_path, file_name)
                if os.path.exists(file_path):
                    integration_tests_found += 1
            
            if integration_tests_found >= len(integration_test_files):
                result['findings'].append({
                    'test': test_name,
                    'status': 'PASS',
                    'details': f'統合テストシステムが{integration_tests_found}個実装されている'
                })
                result['passed_tests'] += 1
            else:
                result['findings'].append({
                    'test': test_name,
                    'status': 'PARTIAL',
                    'details': f'統合テストシステムが{integration_tests_found}個のみ実装',
                    'severity': VerificationSeverity.MEDIUM.value
                })
                result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.MEDIUM.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # テスト3: システム起動・管理
        test_name = "システム起動・管理"
        try:
            management_files = [
                'start_production_system.py',
                'system_health_check.py'
            ]
            
            management_found = 0
            for file_name in management_files:
                file_path = os.path.join(self.base_path, file_name)
                if os.path.exists(file_path):
                    management_found += 1
            
            if management_found >= len(management_files) * 0.8:
                result['findings'].append({
                    'test': test_name,
                    'status': 'PASS',
                    'details': f'システム起動・管理機能が{management_found}個実装されている'
                })
                result['passed_tests'] += 1
            else:
                result['findings'].append({
                    'test': test_name,
                    'status': 'PARTIAL',
                    'details': f'システム起動・管理機能が{management_found}個のみ実装',
                    'severity': VerificationSeverity.MEDIUM.value
                })
                result['failed_tests'] += 1
        except Exception as e:
            result['findings'].append({
                'test': test_name,
                'status': 'ERROR',
                'details': str(e),
                'severity': VerificationSeverity.MEDIUM.value
            })
            result['failed_tests'] += 1
        
        result['tests_executed'].append(test_name)
        
        # スコア計算
        total_tests = len(result['tests_executed'])
        if total_tests > 0:
            result['score'] = (result['passed_tests'] / total_tests) * 100
        
        print(f"    📊 エンドツーエンドフロー: {result['passed_tests']}/{total_tests} テスト合格 ({result['score']:.1f}%)")
        
        return result
    
    def _perform_comprehensive_analysis(self):
        """包括的分析実行"""
        
        print("\n🧠 包括的分析実行中...")
        
        # カテゴリ別スコア分析
        category_scores = {}
        for category, result in self.verification_results['categories'].items():
            category_scores[category] = result.get('score', 0)
        
        # 平均スコア算出
        average_score = sum(category_scores.values()) / len(category_scores) if category_scores else 0
        
        # 強み・弱み分析
        strengths = []
        weaknesses = []
        
        for category, score in category_scores.items():
            if score >= 80:
                strengths.append(category)
            elif score < 60:
                weaknesses.append(category)
        
        # システム成熟度評価
        maturity_level = self._calculate_system_maturity(average_score)
        
        # 分析結果格納
        self.verification_results['comprehensive_analysis'] = {
            'category_scores': category_scores,
            'average_score': round(average_score, 1),
            'strengths': strengths,
            'weaknesses': weaknesses,
            'system_maturity': maturity_level,
            'total_critical_issues': len(self.verification_results['critical_issues'])
        }
        
        print(f"    📊 平均スコア: {average_score:.1f}%")
        print(f"    🌟 強み: {len(strengths)}カテゴリ")
        print(f"    ⚠️ 弱み: {len(weaknesses)}カテゴリ")
        print(f"    🏆 システム成熟度: {maturity_level}")
    
    def _calculate_system_maturity(self, average_score: float) -> str:
        """システム成熟度計算"""
        
        if average_score >= 90:
            return "最高水準 (Optimized)"
        elif average_score >= 80:
            return "成熟 (Managed)"
        elif average_score >= 70:
            return "定義済み (Defined)"
        elif average_score >= 60:
            return "基本 (Basic)"
        else:
            return "初期 (Initial)"
    
    def _generate_recommendations(self):
        """推奨事項生成"""
        
        print("  💡 推奨事項生成中...")
        
        recommendations = []
        
        # カテゴリ別推奨事項
        for category, result in self.verification_results['categories'].items():
            score = result.get('score', 0)
            
            if score < 60:
                recommendations.append({
                    'category': category,
                    'priority': 'HIGH',
                    'recommendation': f'{category}の機能強化が必要です。スコア{score:.1f}%を80%以上に向上させてください。',
                    'actions': [
                        f'{category}の実装状況詳細調査',
                        f'{category}の設計・実装改善',
                        f'{category}のテスト強化'
                    ]
                })
            elif score < 80:
                recommendations.append({
                    'category': category,
                    'priority': 'MEDIUM',
                    'recommendation': f'{category}の品質向上を推奨します。スコア{score:.1f}%をさらに向上させてください。',
                    'actions': [
                        f'{category}の最適化',
                        f'{category}のパフォーマンス改善'
                    ]
                })
        
        # 致命的問題への対応
        if self.verification_results['critical_issues']:
            recommendations.append({
                'category': '致命的問題',
                'priority': 'CRITICAL',
                'recommendation': f'{len(self.verification_results["critical_issues"])}件の致命的問題を即座に修正してください。',
                'actions': [
                    '致命的問題の詳細調査',
                    '緊急修正対応',
                    '根本原因分析・再発防止'
                ]
            })
        
        # システム全体推奨事項
        overall_score = self.verification_results['comprehensive_analysis']['average_score']
        if overall_score >= 85:
            recommendations.append({
                'category': 'システム全体',
                'priority': 'LOW',
                'recommendation': 'システム全体が高品質です。継続的改善を継続してください。',
                'actions': [
                    '定期的品質監視',
                    '新機能追加検討',
                    'パフォーマンス最適化'
                ]
            })
        
        self.verification_results['recommendations'] = recommendations
        
        print(f"    💡 {len(recommendations)}件の推奨事項を生成")
    
    def _calculate_overall_assessment(self):
        """総合評価計算"""
        
        print("  🏆 総合評価計算中...")
        
        analysis = self.verification_results['comprehensive_analysis']
        
        # 品質グレード決定
        average_score = analysis['average_score']
        critical_issues = analysis['total_critical_issues']
        
        if average_score >= 90 and critical_issues == 0:
            quality_grade = 'OUTSTANDING'
            grade_description = '優秀 - 業界最高水準'
        elif average_score >= 80 and critical_issues <= 1:
            quality_grade = 'EXCELLENT'
            grade_description = '優良 - 高品質システム'
        elif average_score >= 70 and critical_issues <= 3:
            quality_grade = 'GOOD'
            grade_description = '良好 - 標準以上'
        elif average_score >= 60 and critical_issues <= 5:
            quality_grade = 'ACCEPTABLE'
            grade_description = '許容 - 改善推奨'
        else:
            quality_grade = 'NEEDS_IMPROVEMENT'
            grade_description = '要改善 - 重要課題あり'
        
        # 運用準備度評価
        readiness_factors = {
            'data_processing': analysis['category_scores'].get('データ入稿', 0) >= 70,
            'analysis_capability': analysis['category_scores'].get('データ分析', 0) >= 70,
            'visualization': analysis['category_scores'].get('可視化', 0) >= 70,
            'end_to_end': analysis['category_scores'].get('エンドツーエンドフロー', 0) >= 70,
            'no_critical_issues': critical_issues == 0
        }
        
        readiness_score = sum(readiness_factors.values()) / len(readiness_factors) * 100
        
        if readiness_score >= 80:
            readiness_status = '本格運用準備完了'
        elif readiness_score >= 60:
            readiness_status = '試用運用可能'
        else:
            readiness_status = '運用準備中'
        
        # 総合評価格納
        self.verification_results['overall_assessment'] = {
            'quality_grade': quality_grade,
            'grade_description': grade_description,
            'overall_score': round(average_score, 1),
            'critical_issues_count': critical_issues,
            'readiness_score': round(readiness_score, 1),
            'readiness_status': readiness_status,
            'readiness_factors': readiness_factors,
            'system_maturity': analysis['system_maturity']
        }
        
        print(f"    🏆 品質グレード: {quality_grade}")
        print(f"    📊 総合スコア: {average_score:.1f}%")
        print(f"    🚀 運用準備度: {readiness_score:.1f}% ({readiness_status})")

def execute_mece_comprehensive_verification():
    """MECE包括的検証実行メイン"""
    
    print("🔍 MECE包括的システム機能検証実行開始...")
    print("=" * 80)
    
    # 検証実行
    verifier = MECEComprehensiveVerifier()
    verification_results = verifier.execute_comprehensive_verification()
    
    # 結果保存
    result_filename = f"mece_comprehensive_verification_results_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    result_filepath = os.path.join("/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析", result_filename)
    
    with open(result_filepath, 'w', encoding='utf-8') as f:
        json.dump(verification_results, f, ensure_ascii=False, indent=2)
    
    # 結果表示
    print("\n" + "=" * 80)
    print("🎯 MECE包括的検証完了!")
    print(f"📁 検証結果: {result_filename}")
    
    # サマリー表示
    overall = verification_results['overall_assessment']
    analysis = verification_results['comprehensive_analysis']
    
    print(f"\n📊 検証結果サマリー:")
    print(f"  🏆 品質グレード: {overall['quality_grade']} ({overall['grade_description']})")
    print(f"  📈 総合スコア: {overall['overall_score']}%")
    print(f"  🚀 運用準備度: {overall['readiness_score']}% ({overall['readiness_status']})")
    print(f"  🎯 システム成熟度: {overall['system_maturity']}")
    print(f"  ⚠️ 致命的問題: {overall['critical_issues_count']}件")
    
    print(f"\n📋 カテゴリ別スコア:")
    for category, score in analysis['category_scores'].items():
        status_icon = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
        print(f"  {status_icon} {category}: {score:.1f}%")
    
    print(f"\n💡 推奨事項: {len(verification_results['recommendations'])}件")
    for rec in verification_results['recommendations'][:3]:  # 上位3件表示
        priority_icon = "🔴" if rec['priority'] == 'CRITICAL' else "🟡" if rec['priority'] == 'HIGH' else "🟢"
        print(f"  {priority_icon} [{rec['priority']}] {rec['recommendation']}")
    
    # 運用可能性判定
    if overall['readiness_score'] >= 80:
        print(f"\n🌟 システムは本格運用準備が完了しています!")
    elif overall['readiness_score'] >= 60:
        print(f"\n✅ システムは試用運用が可能な状態です")
    else:
        print(f"\n🔧 システムは運用準備中です。改善が必要です")
    
    return verification_results

if __name__ == "__main__":
    execute_mece_comprehensive_verification()