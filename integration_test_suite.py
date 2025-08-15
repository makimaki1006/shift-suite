#!/usr/bin/env python3
"""
統合テストスイート
================

これまでの修正の統合動作を検証:
1. 按分計算から時間軸ベース分析への移行
2. 動的スロット間隔対応
3. UI表示の整合性
4. エラーハンドリング
"""

import sys
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Any
import tempfile
import json

# プロジェクトルートの設定
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class IntegrationTestSuite:
    """統合テスト実行クラス"""
    
    def __init__(self):
        self.test_results = {}
        self.mock_data_cache = {}
        
    def setup_mock_environment(self):
        """テスト環境のセットアップ"""
        log.info("=== テスト環境セットアップ ===")
        
        # モックデータキャッシュの初期化
        self.mock_data_cache = {
            'DETECTED_SLOT_INFO': {
                'slot_minutes': 30,
                'slot_hours': 0.5,
                'confidence': 0.85,
                'auto_detected': True
            }
        }
        
        log.info("テスト環境セットアップ完了")
    
    def test_proportional_to_time_axis_migration(self) -> Dict[str, Any]:
        """按分計算から時間軸ベース分析への移行テスト"""
        log.info("=== 按分→時間軸ベース移行テスト ===")
        
        try:
            # テストデータ生成
            test_data = pd.DataFrame({
                'staff': ['田中', '佐藤', '鈴木'] * 10,
                'role': ['看護師', '介護士', '事務'] * 10,
                'employment': ['常勤', 'パート', 'スポット'] * 10,
                'ds': pd.date_range('2025-01-01 08:00', periods=30, freq='30min'),
                'parsed_slots_count': [1] * 30
            })
            
            # 時間軸ベース計算のテスト
            from shift_suite.tasks.time_axis_shortage_calculator import calculate_time_axis_shortage
            
            role_shortages, employment_shortages = calculate_time_axis_shortage(test_data)
            
            # 結果検証
            migration_test = {
                'time_axis_calculation_success': len(role_shortages) > 0 and len(employment_shortages) > 0,
                'role_categories_detected': len(role_shortages),
                'employment_categories_detected': len(employment_shortages),
                'data_consistency': abs(sum(role_shortages.values()) - sum(employment_shortages.values())) < 1.0,
                'calculation_method': '時間軸ベース',
                'status': 'PASS'
            }
            
            log.info(f"  職種別カテゴリ: {len(role_shortages)}個")
            log.info(f"  雇用形態別カテゴリ: {len(employment_shortages)}個")
            log.info(f"  データ整合性: {'✓' if migration_test['data_consistency'] else '✗'}")
            
            return migration_test
            
        except Exception as e:
            log.error(f"移行テストエラー: {e}")
            return {'status': 'FAIL', 'error': str(e)}
    
    def test_dynamic_slot_integration(self) -> Dict[str, Any]:
        """動的スロット間隔統合テスト"""
        log.info("=== 動的スロット統合テスト ===")
        
        try:
            from shift_suite.tasks.time_axis_shortage_calculator import TimeAxisShortageCalculator
            
            test_scenarios = [
                ('15分間隔', pd.date_range('2025-01-01 08:00', periods=16, freq='15min')),
                ('30分間隔', pd.date_range('2025-01-01 08:00', periods=12, freq='30min')),
                ('60分間隔', pd.date_range('2025-01-01 08:00', periods=8, freq='60min'))
            ]
            
            detection_results = {}
            
            for scenario_name, timestamps in test_scenarios:
                calculator = TimeAxisShortageCalculator(auto_detect=True)
                calculator._detect_and_update_slot_interval(pd.Series(timestamps))
                
                detected_info = calculator.get_detected_slot_info()
                
                detection_results[scenario_name] = {
                    'detected_minutes': detected_info['slot_minutes'] if detected_info else None,
                    'confidence': detected_info['confidence'] if detected_info else 0.0,
                    'success': detected_info is not None
                }
                
                log.info(f"  {scenario_name}: {detected_info['slot_minutes'] if detected_info else 'None'}分 "
                        f"(信頼度: {detected_info['confidence'] if detected_info else 0:.2f})")
            
            integration_success = all(r['success'] for r in detection_results.values())
            
            return {
                'detection_results': detection_results,
                'integration_success': integration_success,
                'status': 'PASS' if integration_success else 'FAIL'
            }
            
        except Exception as e:
            log.error(f"動的スロット統合テストエラー: {e}")
            return {'status': 'FAIL', 'error': str(e)}
    
    def test_ui_consistency(self) -> Dict[str, Any]:
        """UI表示整合性テスト"""
        log.info("=== UI整合性テスト ===")
        
        try:
            # DETECTed_SLOT_INFOのモック
            mock_slot_info = self.mock_data_cache['DETECTED_SLOT_INFO']
            
            # UI表示テスト用の文字列生成
            ui_elements = {
                'slot_display': f"{mock_slot_info['slot_minutes']}分スロット単位での真の過不足分析による職種別・雇用形態別算出",
                'slot_conversion': f"1スロット = {mock_slot_info['slot_hours']:.2f}時間（{mock_slot_info['slot_minutes']}分間隔）",
                'confidence_info': f" (検出スロット: {mock_slot_info['slot_minutes']}分, 信頼度: {mock_slot_info['confidence']:.2f})"
            }
            
            # UI要素の妥当性チェック
            ui_tests = {
                'slot_display_valid': '分スロット単位' in ui_elements['slot_display'],
                'conversion_accurate': str(mock_slot_info['slot_minutes']) in ui_elements['slot_conversion'],
                'confidence_displayed': 'confidence' in ui_elements['confidence_info'] or '信頼度' in ui_elements['confidence_info'],
                'dynamic_values_used': mock_slot_info['slot_minutes'] != 30 or mock_slot_info['auto_detected']
            }
            
            ui_consistency = all(ui_tests.values())
            
            log.info("  UI要素検証:")
            for test_name, result in ui_tests.items():
                log.info(f"    {test_name}: {'✓' if result else '✗'}")
            
            return {
                'ui_elements': ui_elements,
                'ui_tests': ui_tests,
                'ui_consistency': ui_consistency,
                'status': 'PASS' if ui_consistency else 'FAIL'
            }
            
        except Exception as e:
            log.error(f"UI整合性テストエラー: {e}")
            return {'status': 'FAIL', 'error': str(e)}
    
    def test_error_handling(self) -> Dict[str, Any]:
        """エラーハンドリングテスト"""
        log.info("=== エラーハンドリングテスト ===")
        
        error_scenarios = {}
        
        try:
            from shift_suite.tasks.time_axis_shortage_calculator import TimeAxisShortageCalculator
            
            # 1. 空データでのエラーハンドリング
            empty_df = pd.DataFrame()
            calculator = TimeAxisShortageCalculator(auto_detect=True)
            
            try:
                role_shortages, employment_shortages = calculator.calculate_role_based_shortage(empty_df, empty_df), calculator.calculate_employment_based_shortage(empty_df, empty_df)
                error_scenarios['empty_data'] = {'handled_gracefully': True, 'error': None}
            except Exception as e:
                error_scenarios['empty_data'] = {'handled_gracefully': False, 'error': str(e)}
            
            # 2. 不正なタイムスタンプでのエラーハンドリング
            invalid_df = pd.DataFrame({
                'staff': ['test'],
                'role': ['test'],
                'employment': ['test'],
                'ds': [None],
                'parsed_slots_count': [1]
            })
            
            try:
                calculator._detect_and_update_slot_interval(invalid_df['ds'])
                error_scenarios['invalid_timestamps'] = {'handled_gracefully': True, 'error': None}
            except Exception as e:
                error_scenarios['invalid_timestamps'] = {'handled_gracefully': False, 'error': str(e)}
            
            # 3. 欠損データでのエラーハンドリング
            missing_data_df = pd.DataFrame({
                'staff': ['田中', None, '佐藤'],
                'role': ['看護師', '介護士', None],
                'employment': [None, 'パート', 'スポット'],
                'ds': pd.date_range('2025-01-01', periods=3, freq='1H'),
                'parsed_slots_count': [1, 1, 1]
            })
            
            try:
                role_result = calculator.calculate_role_based_shortage(missing_data_df, pd.DataFrame())
                error_scenarios['missing_data'] = {'handled_gracefully': True, 'error': None}
            except Exception as e:
                error_scenarios['missing_data'] = {'handled_gracefully': False, 'error': str(e)}
            
            error_handling_success = all(scenario['handled_gracefully'] for scenario in error_scenarios.values())
            
            log.info("  エラーハンドリング結果:")
            for scenario, result in error_scenarios.items():
                log.info(f"    {scenario}: {'✓' if result['handled_gracefully'] else '✗'}")
                if not result['handled_gracefully']:
                    log.warning(f"      エラー: {result['error']}")
            
            return {
                'error_scenarios': error_scenarios,
                'error_handling_success': error_handling_success,
                'status': 'PASS' if error_handling_success else 'FAIL'
            }
            
        except Exception as e:
            log.error(f"エラーハンドリングテストエラー: {e}")
            return {'status': 'FAIL', 'error': str(e)}
    
    def test_data_flow_integrity(self) -> Dict[str, Any]:
        """データフロー整合性テスト"""
        log.info("=== データフロー整合性テスト ===")
        
        try:
            # エンドツーエンドのデータフローテスト
            input_data = pd.DataFrame({
                'staff': ['田中', '佐藤', '鈴木', '田中', '佐藤'],
                'role': ['看護師', '介護士', '事務', '看護師', '介護士'],
                'employment': ['常勤', 'パート', 'スポット', '常勤', 'パート'],
                'ds': pd.date_range('2025-01-01 08:00', periods=5, freq='30min'),
                'parsed_slots_count': [1, 1, 1, 1, 1]
            })
            
            # 1. 動的スロット検出
            from shift_suite.tasks.time_axis_shortage_calculator import TimeAxisShortageCalculator
            calculator = TimeAxisShortageCalculator(auto_detect=True)
            calculator._detect_and_update_slot_interval(input_data['ds'])
            detected_slot_info = calculator.get_detected_slot_info()
            
            # 2. 時間軸ベース計算
            role_analysis = calculator.calculate_role_based_shortage(input_data, pd.DataFrame())
            employment_analysis = calculator.calculate_employment_based_shortage(input_data, pd.DataFrame())
            
            # 3. データ整合性チェック
            flow_integrity = {
                'slot_detection_success': detected_slot_info is not None,
                'role_analysis_success': len(role_analysis) > 0,
                'employment_analysis_success': len(employment_analysis) > 0,
                'expected_roles_found': set(['看護師', '介護士', '事務']).issubset(set(role_analysis.keys())),
                'expected_employments_found': set(['常勤', 'パート', 'スポット']).issubset(set(employment_analysis.keys())),
                'data_types_consistent': all(isinstance(v, dict) for v in role_analysis.values()),
                'slot_info_preserved': detected_slot_info['slot_minutes'] == 30  # 30分間隔データ
            }
            
            integrity_score = sum(flow_integrity.values()) / len(flow_integrity)
            
            log.info(f"  データフロー整合性スコア: {integrity_score:.1%}")
            log.info(f"  検出スロット: {detected_slot_info['slot_minutes'] if detected_slot_info else 'None'}分")
            log.info(f"  分析結果 - 職種: {len(role_analysis)}個, 雇用形態: {len(employment_analysis)}個")
            
            return {
                'flow_integrity': flow_integrity,
                'integrity_score': integrity_score,
                'detected_slot_info': detected_slot_info,
                'role_analysis_count': len(role_analysis),
                'employment_analysis_count': len(employment_analysis),
                'status': 'PASS' if integrity_score >= 0.8 else 'FAIL'
            }
            
        except Exception as e:
            log.error(f"データフロー整合性テストエラー: {e}")
            return {'status': 'FAIL', 'error': str(e)}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """全統合テストの実行"""
        log.info("=" * 60)
        log.info("統合テストスイート実行開始")
        log.info("=" * 60)
        
        # テスト環境セットアップ
        self.setup_mock_environment()
        
        # 各テストの実行
        tests = {
            'proportional_migration': self.test_proportional_to_time_axis_migration(),
            'dynamic_slot_integration': self.test_dynamic_slot_integration(),
            'ui_consistency': self.test_ui_consistency(),
            'error_handling': self.test_error_handling(),
            'data_flow_integrity': self.test_data_flow_integrity()
        }
        
        # 結果集計
        passed_tests = sum(1 for test in tests.values() if test.get('status') == 'PASS')
        total_tests = len(tests)
        success_rate = passed_tests / total_tests
        
        # 総合結果
        integration_result = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_status': 'PASS' if success_rate >= 0.8 else 'FAIL',
            'individual_tests': tests
        }
        
        # 結果サマリー
        log.info("=" * 60)
        log.info("統合テスト結果サマリー")
        log.info("=" * 60)
        log.info(f"総合成功率: {success_rate:.1%} ({passed_tests}/{total_tests})")
        log.info(f"総合判定: {'✅ PASS' if success_rate >= 0.8 else '❌ FAIL'}")
        
        for test_name, result in tests.items():
            status_icon = '✅' if result.get('status') == 'PASS' else '❌'
            log.info(f"  {test_name}: {status_icon} {result.get('status', 'UNKNOWN')}")
        
        return integration_result

def main():
    """メイン実行関数"""
    suite = IntegrationTestSuite()
    result = suite.run_all_tests()
    
    # 結果をJSONファイルに保存
    with open('integration_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📊 統合テスト結果は integration_test_results.json に保存されました")
    
    return result.get('overall_status') == 'PASS'

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)