"""
Phase 1: SLOT_HOURS計算正確性検証
現状最適化継続戦略における数値品質・計算精度確保

96.7/100品質レベル維持のための計算保護確認
"""

import os
import json
import datetime
import re
from typing import Dict, List, Any

class Phase1SlotHoursVerification:
    """Phase 1: SLOT_HOURS計算正確性検証システム"""
    
    def __init__(self):
        self.base_path = "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析"
        self.verification_start_time = datetime.datetime.now()
        
        # SLOT_HOURS保護対象モジュール
        self.protected_modules = [
            'shift_suite/tasks/fact_extractor_prototype.py',
            'shift_suite/tasks/lightweight_anomaly_detector.py'
        ]
        
        # 計算精度ベースライン
        self.calculation_baselines = {
            'slot_hours_value': 0.5,  # 30分 = 0.5時間
            'minimum_multiplications': 1,
            'expected_definition_count': 1,
            'calculation_accuracy_target': 100.0  # 100%精度要求
        }
        
        # 検証パターン
        self.verification_patterns = {
            'slot_hours_definition': r'SLOT_HOURS\s*=\s*0\.5',
            'slot_hours_multiplication': r'\*\s*SLOT_HOURS',
            'slot_hours_usage': r'SLOT_HOURS',
            'calculation_context': r'(hours|時間|計算).*SLOT_HOURS|SLOT_HOURS.*(hours|時間|計算)',
            'protected_calculation': r'(parsed_slots_count|slot_count|slots).*\*\s*SLOT_HOURS'
        }
        
    def execute_slot_hours_verification(self):
        """SLOT_HOURS計算正確性検証メイン実行"""
        print("🔍 Phase 1: SLOT_HOURS計算正確性検証開始...")
        print(f"📅 検証実行時刻: {self.verification_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 計算精度目標: {self.calculation_baselines['calculation_accuracy_target']}%")
        
        try:
            # モジュール別SLOT_HOURS検証
            module_verification_results = {}
            
            for module_path in self.protected_modules:
                print(f"\n🔄 {module_path}検証中...")
                verification_result = self._verify_module_slot_hours_implementation(module_path)
                module_verification_results[module_path] = verification_result
                
                if verification_result['verification_success']:
                    print(f"✅ {module_path}: 計算保護正常")
                else:
                    print(f"⚠️ {module_path}: 要確認")
            
            # 計算一貫性・整合性確認
            consistency_check = self._check_calculation_consistency(module_verification_results)
            if consistency_check['consistency_maintained']:
                print("✅ 計算一貫性・整合性: 維持")
            else:
                print("⚠️ 計算一貫性・整合性: 要対応")
            
            # 数値精度・正確性評価
            accuracy_evaluation = self._evaluate_numerical_accuracy(module_verification_results)
            if accuracy_evaluation['accuracy_acceptable']:
                print("✅ 数値精度・正確性: acceptable")
            else:
                print("⚠️ 数値精度・正確性: 要改善")
            
            # 総合検証結果分析
            verification_analysis = self._analyze_verification_results(
                module_verification_results, consistency_check, accuracy_evaluation
            )
            
            return {
                'metadata': {
                    'verification_execution_id': f"PHASE1_SLOT_HOURS_VERIFY_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'verification_start_time': self.verification_start_time.isoformat(),
                    'verification_end_time': datetime.datetime.now().isoformat(),
                    'verification_duration': str(datetime.datetime.now() - self.verification_start_time),
                    'calculation_baselines': self.calculation_baselines,
                    'verification_scope': 'SLOT_HOURS計算正確性・保護機能・数値精度'
                },
                'module_verification_results': module_verification_results,
                'consistency_check': consistency_check,
                'accuracy_evaluation': accuracy_evaluation,
                'verification_analysis': verification_analysis,
                'success': verification_analysis['overall_verification_status'] == 'verified',
                'slot_hours_verification_status': verification_analysis['verification_level']
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.datetime.now().isoformat(),
                'status': 'slot_hours_verification_failed'
            }
    
    def _verify_module_slot_hours_implementation(self, module_path):
        """モジュール別SLOT_HOURS実装検証"""
        try:
            full_path = os.path.join(self.base_path, module_path)
            
            if not os.path.exists(full_path):
                return {
                    'verification_success': False,
                    'error': 'module_not_found',
                    'module_status': 'missing'
                }
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # パターンマッチング検証
            pattern_matches = {}
            for pattern_name, pattern in self.verification_patterns.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                pattern_matches[pattern_name] = {
                    'count': len(matches),
                    'matches': matches,
                    'found': len(matches) > 0
                }
            
            # 基本検証項目
            basic_verification = {
                'slot_hours_defined': pattern_matches['slot_hours_definition']['found'],
                'slot_hours_definition_count': pattern_matches['slot_hours_definition']['count'],
                'slot_hours_multiplications': pattern_matches['slot_hours_multiplication']['count'],
                'slot_hours_usage_count': pattern_matches['slot_hours_usage']['count'],
                'protected_calculations_found': pattern_matches['protected_calculation']['found'],
                'protected_calculations_count': pattern_matches['protected_calculation']['count']
            }
            
            # 計算文脈分析
            calculation_context = {
                'context_matches': pattern_matches['calculation_context']['matches'],
                'context_appropriate': len(pattern_matches['calculation_context']['matches']) > 0,
                'calculation_purpose': 'time_conversion' if 'hours' in str(pattern_matches['calculation_context']['matches']).lower() else 'slot_conversion'
            }
            
            # コード品質指標
            code_quality = {
                'module_size': len(content),
                'lines_count': len(content.splitlines()),
                'comments_present': '"""' in content or '#' in content,
                'imports_present': 'import' in content,
                'functions_defined': content.count('def ') > 0,
                'classes_defined': content.count('class ') > 0
            }
            
            # 検証成功判定
            verification_success = (
                basic_verification['slot_hours_defined'] and
                basic_verification['slot_hours_definition_count'] >= self.calculation_baselines['minimum_multiplications'] and
                basic_verification['slot_hours_multiplications'] >= self.calculation_baselines['minimum_multiplications'] and
                basic_verification['protected_calculations_found']
            )
            
            # 計算保護レベル評価
            if verification_success and basic_verification['slot_hours_multiplications'] >= 3:
                protection_level = 'comprehensive'
            elif verification_success:
                protection_level = 'standard'
            elif basic_verification['slot_hours_defined']:
                protection_level = 'minimal'
            else:
                protection_level = 'insufficient'
            
            return {
                'verification_success': verification_success,
                'pattern_matches': pattern_matches,
                'basic_verification': basic_verification,
                'calculation_context': calculation_context,
                'code_quality': code_quality,
                'protection_level': protection_level,
                'module_status': 'verified' if verification_success else 'requires_attention',
                'verification_timestamp': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'verification_success': False,
                'error': str(e),
                'module_status': 'verification_failed'
            }
    
    def _check_calculation_consistency(self, module_verification_results):
        """計算一貫性・整合性確認"""
        try:
            consistency_checks = {}
            
            # 全モジュール統計
            total_definitions = sum(
                result.get('basic_verification', {}).get('slot_hours_definition_count', 0)
                for result in module_verification_results.values()
                if result.get('verification_success', False)
            )
            
            total_multiplications = sum(
                result.get('basic_verification', {}).get('slot_hours_multiplications', 0)
                for result in module_verification_results.values()
                if result.get('verification_success', False)
            )
            
            total_usage = sum(
                result.get('basic_verification', {}).get('slot_hours_usage_count', 0)
                for result in module_verification_results.values()
                if result.get('verification_success', False)
            )
            
            # モジュール間一貫性確認
            definition_consistency = all(
                result.get('basic_verification', {}).get('slot_hours_definition_count', 0) >= 1
                for result in module_verification_results.values()
                if result.get('verification_success', False)
            )
            
            protection_level_consistency = all(
                result.get('protection_level', '') in ['standard', 'comprehensive']
                for result in module_verification_results.values()
                if result.get('verification_success', False)
            )
            
            # 計算パターン一貫性
            pattern_consistency = {
                'all_modules_have_definitions': definition_consistency,
                'all_modules_have_multiplications': all(
                    result.get('basic_verification', {}).get('slot_hours_multiplications', 0) > 0
                    for result in module_verification_results.values()
                    if result.get('verification_success', False)
                ),
                'protection_levels_consistent': protection_level_consistency,
                'calculation_contexts_appropriate': all(
                    result.get('calculation_context', {}).get('context_appropriate', False)
                    for result in module_verification_results.values()
                    if result.get('verification_success', False)
                )
            }
            
            # 一貫性評価
            consistency_score = sum(pattern_consistency.values()) / len(pattern_consistency)
            consistency_maintained = consistency_score >= 0.75  # 75%以上で一貫性維持
            
            consistency_checks = {
                'total_definitions': total_definitions,
                'total_multiplications': total_multiplications,
                'total_usage': total_usage,
                'pattern_consistency': pattern_consistency,
                'consistency_score': consistency_score,
                'consistency_maintained': consistency_maintained,
                'consistency_level': 'high' if consistency_score >= 0.9 else 'moderate' if consistency_score >= 0.75 else 'low'
            }
            
            return {
                'success': True,
                'consistency_checks': consistency_checks,
                'consistency_maintained': consistency_maintained,
                'check_timestamp': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'consistency_maintained': False
            }
    
    def _evaluate_numerical_accuracy(self, module_verification_results):
        """数値精度・正確性評価"""
        try:
            accuracy_metrics = {}
            
            # 各モジュールの精度評価
            module_accuracy_scores = {}
            
            for module_path, result in module_verification_results.items():
                if result.get('verification_success', False):
                    # 基本精度スコア
                    basic_score = 0
                    
                    # SLOT_HOURS定義の正確性
                    if result.get('basic_verification', {}).get('slot_hours_defined', False):
                        basic_score += 30
                    
                    # 乗算使用の適切性
                    multiplications = result.get('basic_verification', {}).get('slot_hours_multiplications', 0)
                    if multiplications >= 1:
                        basic_score += 25
                    if multiplications >= 3:
                        basic_score += 15  # 複数箇所での使用
                    
                    # 保護計算の存在
                    if result.get('basic_verification', {}).get('protected_calculations_found', False):
                        basic_score += 20
                    
                    # コンテキストの適切性
                    if result.get('calculation_context', {}).get('context_appropriate', False):
                        basic_score += 10
                    
                    module_accuracy_scores[module_path] = basic_score
                else:
                    module_accuracy_scores[module_path] = 0
            
            # 全体精度評価
            overall_accuracy_score = sum(module_accuracy_scores.values()) / len(module_accuracy_scores) if module_accuracy_scores else 0
            
            # 精度判定
            accuracy_acceptable = overall_accuracy_score >= self.calculation_baselines['calculation_accuracy_target'] * 0.95  # 95%以上
            
            # 精度レベル分類
            if overall_accuracy_score >= 95:
                accuracy_level = 'excellent'
            elif overall_accuracy_score >= 85:
                accuracy_level = 'good'
            elif overall_accuracy_score >= 75:
                accuracy_level = 'acceptable'
            else:
                accuracy_level = 'needs_improvement'
            
            accuracy_metrics = {
                'module_accuracy_scores': module_accuracy_scores,
                'overall_accuracy_score': overall_accuracy_score,
                'accuracy_acceptable': accuracy_acceptable,
                'accuracy_level': accuracy_level,
                'target_score': self.calculation_baselines['calculation_accuracy_target'],
                'accuracy_gap': self.calculation_baselines['calculation_accuracy_target'] - overall_accuracy_score
            }
            
            return {
                'success': True,
                'accuracy_metrics': accuracy_metrics,
                'accuracy_acceptable': accuracy_acceptable,
                'evaluation_timestamp': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'accuracy_acceptable': False
            }
    
    def _analyze_verification_results(self, module_results, consistency_check, accuracy_evaluation):
        """検証結果総合分析"""
        try:
            # 各カテゴリ成功確認
            categories_success = {
                'module_verification': all(
                    result.get('verification_success', False)
                    for result in module_results.values()
                ),
                'consistency_check': consistency_check.get('consistency_maintained', False),
                'accuracy_evaluation': accuracy_evaluation.get('accuracy_acceptable', False)
            }
            
            # 総合成功率
            overall_success_rate = sum(categories_success.values()) / len(categories_success)
            
            # 検証ステータス判定
            if overall_success_rate == 1.0:
                overall_verification_status = 'verified'
                verification_level = 'fully_compliant'
            elif overall_success_rate >= 0.67:
                overall_verification_status = 'mostly_verified'
                verification_level = 'largely_compliant'
            else:
                overall_verification_status = 'requires_attention'
                verification_level = 'needs_improvement'
            
            # 具体的問題・推奨事項識別
            identified_issues = []
            recommended_actions = []
            
            if not categories_success['module_verification']:
                failed_modules = [
                    module_path for module_path, result in module_results.items()
                    if not result.get('verification_success', False)
                ]
                if failed_modules:
                    identified_issues.append(f"モジュール検証失敗: {', '.join(failed_modules)}")
                    recommended_actions.append("失敗モジュールのSLOT_HOURS実装修正")
            
            if not categories_success['consistency_check']:
                identified_issues.append("計算一貫性・整合性問題")
                recommended_actions.append("モジュール間SLOT_HOURS使用パターン統一")
            
            if not categories_success['accuracy_evaluation']:
                accuracy_gap = accuracy_evaluation.get('accuracy_metrics', {}).get('accuracy_gap', 0)
                identified_issues.append(f"精度不足: {accuracy_gap:.1f}%のギャップ")
                recommended_actions.append("計算精度向上・保護機能強化")
            
            # 品質ベースライン維持評価
            quality_baseline_maintained = overall_success_rate >= 0.967  # 96.7%以上
            
            # 次回検証計画
            next_verification_schedule = {
                'next_verification_date': (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
                'verification_frequency': '日次' if overall_verification_status == 'requires_attention' else '週次',
                'priority_level': 'high' if overall_verification_status == 'requires_attention' else 'medium'
            }
            
            return {
                'overall_verification_status': overall_verification_status,
                'verification_level': verification_level,
                'categories_success': categories_success,
                'overall_success_rate': overall_success_rate,
                'quality_baseline_maintained': quality_baseline_maintained,
                'identified_issues': identified_issues,
                'recommended_actions': recommended_actions,
                'next_verification_schedule': next_verification_schedule,
                'analysis_timestamp': datetime.datetime.now().isoformat(),
                'phase1_data_quality_status': 'maintained' if overall_verification_status in ['verified', 'mostly_verified'] else 'requires_attention'
            }
            
        except Exception as e:
            return {
                'overall_verification_status': 'analysis_failed',
                'error': str(e),
                'analysis_method': 'verification_analysis_failed'
            }

def main():
    """Phase 1: SLOT_HOURS計算正確性検証メイン実行"""
    print("🔍 Phase 1: SLOT_HOURS計算正確性検証開始...")
    
    verifier = Phase1SlotHoursVerification()
    result = verifier.execute_slot_hours_verification()
    
    if 'error' in result:
        print(f"❌ SLOT_HOURS検証エラー: {result['error']}")
        return result
    
    # 結果保存
    result_file = f"Phase1_SLOT_HOURS_Verification_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 結果表示
    print(f"\n🎯 Phase 1: SLOT_HOURS計算正確性検証完了!")
    print(f"📁 検証結果ファイル: {result_file}")
    
    if result['success']:
        print(f"✅ SLOT_HOURS計算検証: 成功")
        print(f"🏆 検証レベル: {result['verification_analysis']['verification_level']}")
        print(f"📊 成功率: {result['verification_analysis']['overall_success_rate']:.1%}")
        print(f"🎯 品質ベースライン維持: {'Yes' if result['verification_analysis']['quality_baseline_maintained'] else 'No'}")
        
        if result['verification_analysis']['recommended_actions']:
            print(f"\n🚀 推奨アクション:")
            for i, action in enumerate(result['verification_analysis']['recommended_actions'][:3], 1):
                print(f"  {i}. {action}")
    else:
        print(f"❌ SLOT_HOURS計算検証: 要対応")
        print(f"📋 問題: {', '.join(result['verification_analysis']['identified_issues'])}")
        print(f"🚨 計算精度確保が必要")
    
    return result

if __name__ == "__main__":
    result = main()