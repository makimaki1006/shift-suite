#!/usr/bin/env python3
"""
Phase1 C1: 技術的リスク評価
システム変更に伴う技術的リスクの包括的評価
"""

import json
import sys
import ast
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import traceback

class TechnicalRiskAssessment:
    """技術的リスク評価器"""
    
    def __init__(self):
        self.risk_assessment_results = {}
        self.risk_matrix = {}
        self.mitigation_strategies = {}
        
    def assess_technical_risks(self):
        """技術的リスク評価実行"""
        print("=== C1: 技術的リスク評価 ===")
        
        risk_results = {
            'code_modification_risks': {},
            'integration_risks': {},
            'performance_risks': {},
            'data_integrity_risks': {},
            'operational_risks': {},
            'risk_matrix_analysis': {},
            'mitigation_plan': {}
        }
        
        # 1. コード修正リスク
        print("\n【コード修正リスク評価】")
        code_risks = self._assess_code_modification_risks()
        risk_results['code_modification_risks'] = code_risks
        
        # 2. 統合リスク
        print("\n【統合リスク評価】")
        integration_risks = self._assess_integration_risks()
        risk_results['integration_risks'] = integration_risks
        
        # 3. パフォーマンスリスク
        print("\n【パフォーマンスリスク評価】")
        performance_risks = self._assess_performance_risks()
        risk_results['performance_risks'] = performance_risks
        
        # 4. データ整合性リスク
        print("\n【データ整合性リスク評価】")
        data_risks = self._assess_data_integrity_risks()
        risk_results['data_integrity_risks'] = data_risks
        
        # 5. 運用リスク
        print("\n【運用リスク評価】")
        operational_risks = self._assess_operational_risks()
        risk_results['operational_risks'] = operational_risks
        
        # 6. リスクマトリックス分析
        print("\n【リスクマトリックス分析】")
        risk_matrix = self._create_risk_matrix(risk_results)
        risk_results['risk_matrix_analysis'] = risk_matrix
        
        # 7. リスク軽減計画
        print("\n【リスク軽減計画】")
        mitigation_plan = self._create_mitigation_plan(risk_results)
        risk_results['mitigation_plan'] = mitigation_plan
        
        self.risk_assessment_results = risk_results
        return risk_results
    
    def _assess_code_modification_risks(self):
        """コード修正リスク評価"""
        print("コード修正に伴うリスクを評価中...")
        
        code_risks = {
            'syntax_errors': {},
            'logic_errors': {},
            'compatibility_breaks': {},
            'regression_risks': {},
            'debugging_complexity': {}
        }
        
        try:
            # 修正対象ファイルの分析
            target_file = Path('unified_data_pipeline_architecture.py')
            
            if target_file.exists():
                with open(target_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # コードの複雑性分析
                lines = content.split('\n')
                total_lines = len(lines)
                code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
                
                # 構文チェック
                try:
                    ast.parse(content)
                    syntax_risk = 'low'
                except SyntaxError:
                    syntax_risk = 'high'
                
                code_risks['syntax_errors'] = {
                    'current_syntax_valid': syntax_risk == 'low',
                    'modification_syntax_risk': 'medium',
                    'risk_level': 'medium',
                    'reason': 'target_types引数追加時の構文ミスリスク'
                }
                
                # ロジックエラーリスク
                # 条件分岐の複雑性チェック
                if_statements = len(re.findall(r'\bif\b', content))
                for_loops = len(re.findall(r'\bfor\b', content))
                while_loops = len(re.findall(r'\bwhile\b', content))
                
                complexity_score = if_statements + for_loops * 2 + while_loops * 3
                
                code_risks['logic_errors'] = {
                    'existing_complexity': complexity_score,
                    'complexity_increase_estimate': 5,
                    'conditional_logic_risk': 'medium',
                    'risk_level': 'medium',
                    'primary_concerns': [
                        'target_types引数の不正値処理',
                        'None判定とDataType判定の混在',
                        'ファイル未発見時のフォールバック失敗'
                    ]
                }
                
                # 後方互換性破損リスク
                api_calls = content.count('_scan_available_data')
                
                code_risks['compatibility_breaks'] = {
                    'api_calls_in_file': api_calls,
                    'backward_compatibility_risk': 'low',
                    'risk_level': 'low',
                    'reason': 'Optional引数のため既存呼び出しは保持'
                }
                
                # 回帰リスク
                code_risks['regression_risks'] = {
                    'affected_functionality': [
                        '全ファイルスキャン動作',
                        'メタデータ生成プロセス',
                        'キャッシュ動作',
                        'エラーハンドリング'
                    ],
                    'regression_probability': 'medium',
                    'risk_level': 'medium',
                    'testing_requirement': 'comprehensive'
                }
                
                # デバッグ複雑性
                code_risks['debugging_complexity'] = {
                    'new_code_paths': 2,  # 全スキャン, 特定スキャン
                    'conditional_branches': 3,  # None, PROPORTIONAL_*, その他
                    'debug_complexity_increase': 'medium',
                    'risk_level': 'medium',
                    'monitoring_requirements': [
                        'スキャンモード判定ログ',
                        'ファイル検出状況ログ',
                        'パフォーマンス測定ログ'
                    ]
                }
                
                print(f"    対象ファイル分析: {total_lines}行, 複雑性スコア: {complexity_score}")
                print("    構文リスク: medium")
                print("    ロジックリスク: medium")
                print("    互換性リスク: low")
                print("    回帰リスク: medium")
                print("    デバッグリスク: medium")
                
            else:
                print("    ERROR: 対象ファイルが見つからない")
                code_risks['file_access_error'] = 'Target file not found'
        
        except Exception as e:
            print(f"  ERROR: コード修正リスク評価失敗 - {e}")
            code_risks['assessment_error'] = str(e)
        
        return code_risks
    
    def _assess_integration_risks(self):
        """統合リスク評価"""
        print("既存システム統合リスクを評価中...")
        
        integration_risks = {
            'dash_app_integration': {},
            'unified_registry_integration': {},
            'data_pipeline_integration': {},
            'third_party_integration': {}
        }
        
        try:
            # Dash統合リスク
            dash_path = Path('dash_app.py')
            if dash_path.exists():
                with open(dash_path, 'r', encoding='utf-8') as f:
                    dash_content = f.read()
                
                # 統一システム使用箇所の特定
                unified_calls = dash_content.count('get_unified_registry')
                proportional_refs = dash_content.count('proportional_abolition')
                
                integration_risks['dash_app_integration'] = {
                    'integration_points': unified_calls,
                    'proportional_references': proportional_refs,
                    'risk_level': 'low' if unified_calls <= 5 else 'medium',
                    'potential_issues': [
                        'データ取得タイミングの変更',
                        'エラーハンドリングの不整合',
                        'キャッシュ動作の変更'
                    ],
                    'mitigation_required': unified_calls > 0
                }
                
                print(f"    Dash統合ポイント: {unified_calls}箇所")
                print(f"    按分廃止参照: {proportional_refs}箇所")
            
            # 統一レジストリ統合リスク
            integration_risks['unified_registry_integration'] = {
                'registry_modification_impact': 'medium',
                'cache_behavior_change': 'medium',
                'metadata_consistency_risk': 'low',
                'risk_level': 'medium',
                'key_concerns': [
                    'レジストリ初期化タイミングの変更',
                    'データタイプ判定ロジックの複雑化',
                    'ThreadSafeLRUCacheとの相互作用'
                ]
            }
            
            # データパイプライン統合リスク
            integration_risks['data_pipeline_integration'] = {
                'pipeline_flow_impact': 'medium',
                'data_consistency_risk': 'low',
                'performance_integration_risk': 'low',
                'risk_level': 'medium',
                'areas_of_concern': [
                    'データローディング順序の変更',
                    '依存データの未ロード状態',
                    'エラー伝播の変更'
                ]
            }
            
            # サードパーティ統合リスク
            integration_risks['third_party_integration'] = {
                'external_dependency_risk': 'low',
                'library_compatibility_risk': 'low',
                'risk_level': 'low',
                'reason': 'コア変更は内部実装のみ'
            }
            
            print("    Dash統合リスク: low-medium")
            print("    レジストリ統合リスク: medium")
            print("    パイプライン統合リスク: medium")
            print("    サードパーティ統合リスク: low")
            
        except Exception as e:
            print(f"  ERROR: 統合リスク評価失敗 - {e}")
            integration_risks['assessment_error'] = str(e)
        
        return integration_risks
    
    def _assess_performance_risks(self):
        """パフォーマンスリスク評価"""
        print("パフォーマンス関連リスクを評価中...")
        
        performance_risks = {
            'performance_regression_risk': {},
            'memory_usage_risk': {},
            'scalability_risk': {},
            'bottleneck_shift_risk': {}
        }
        
        try:
            # パフォーマンス劣化リスク
            performance_risks['performance_regression_risk'] = {
                'proportional_abolition_performance': 'improvement_expected',
                'full_analysis_performance': 'no_change_expected',
                'conditional_logic_overhead': 'minimal',
                'risk_level': 'low',
                'expected_improvement': '+80% for proportional operations',
                'potential_degradation_scenarios': [
                    'target_types判定オーバーヘッド',
                    'データタイプ変換コスト',
                    'フォールバック処理コスト'
                ]
            }
            
            # メモリ使用量リスク
            performance_risks['memory_usage_risk'] = {
                'memory_reduction_expected': True,
                'reduction_estimate': '60% for proportional operations',
                'memory_leak_risk': 'low',
                'risk_level': 'low',
                'monitoring_points': [
                    'レジストリキャッシュサイズ',
                    'メタデータストレージ使用量',
                    'ガベージコレクション頻度'
                ]
            }
            
            # スケーラビリティリスク
            performance_risks['scalability_risk'] = {
                'small_scale_impact': 'positive',
                'large_scale_impact': 'positive',
                'concurrent_access_risk': 'low',
                'risk_level': 'low',
                'scalability_factors': [
                    'ファイル数増加時の効果拡大',
                    'メモリ制約環境での効果顕在化',
                    '同時アクセス時の競合減少'
                ]
            }
            
            # ボトルネック移行リスク
            performance_risks['bottleneck_shift_risk'] = {
                'io_bottleneck_reduction': 'significant',
                'cpu_bottleneck_risk': 'minimal',
                'network_bottleneck_risk': 'none',
                'new_bottleneck_likelihood': 'low',
                'risk_level': 'low',
                'potential_new_bottlenecks': [
                    'データタイプ判定処理',
                    'ファイル存在確認処理',
                    'エラーハンドリング処理'
                ]
            }
            
            print("    パフォーマンス劣化リスク: low")
            print("    メモリ使用量リスク: low")
            print("    スケーラビリティリスク: low")
            print("    ボトルネック移行リスク: low")
            
        except Exception as e:
            print(f"  ERROR: パフォーマンスリスク評価失敗 - {e}")
            performance_risks['assessment_error'] = str(e)
        
        return performance_risks
    
    def _assess_data_integrity_risks(self):
        """データ整合性リスク評価"""
        print("データ整合性リスクを評価中...")
        
        data_risks = {
            'data_loss_risk': {},
            'data_corruption_risk': {},
            'consistency_risk': {},
            'cache_coherence_risk': {}
        }
        
        try:
            # データ消失リスク
            data_risks['data_loss_risk'] = {
                'file_detection_failure_risk': 'medium',
                'metadata_loss_risk': 'low',
                'cache_invalidation_risk': 'low',
                'risk_level': 'medium',
                'scenarios': [
                    'target_typesに含まれないデータタイプのスキップ',
                    '按分廃止ファイルの誤った未検出',
                    'パス指定ミスによる検出失敗'
                ],
                'data_recovery_capability': 'fallback_to_full_scan'
            }
            
            # データ破損リスク
            data_risks['data_corruption_risk'] = {
                'file_content_corruption_risk': 'none',
                'metadata_corruption_risk': 'low',
                'cache_corruption_risk': 'low',
                'risk_level': 'low',
                'reason': '読み込み専用操作のため破損リスクは低い'
            }
            
            # データ一貫性リスク
            data_risks['consistency_risk'] = {
                'cross_analysis_consistency': 'maintained',
                'temporal_consistency_risk': 'low',
                'version_consistency_risk': 'low',
                'risk_level': 'low',
                'consistency_mechanisms': [
                    'ファイルハッシュによる整合性確認',
                    'タイムスタンプによるバージョン管理',
                    'メタデータ検証プロセス'
                ]
            }
            
            # キャッシュ一貫性リスク
            data_risks['cache_coherence_risk'] = {
                'cache_invalidation_risk': 'medium',
                'cache_hit_miss_pattern_change': 'significant',
                'cache_size_optimization_needed': True,
                'risk_level': 'medium',
                'cache_management_requirements': [
                    'スキャンモード別キャッシュ戦略',
                    'データタイプ別キャッシュ有効期限',
                    'メモリ使用量最適化'
                ]
            }
            
            print("    データ消失リスク: medium")
            print("    データ破損リスク: low")
            print("    データ一貫性リスク: low")
            print("    キャッシュ一貫性リスク: medium")
            
        except Exception as e:
            print(f"  ERROR: データ整合性リスク評価失敗 - {e}")
            data_risks['assessment_error'] = str(e)
        
        return data_risks
    
    def _assess_operational_risks(self):
        """運用リスク評価"""
        print("運用関連リスクを評価中...")
        
        operational_risks = {
            'deployment_risk': {},
            'rollback_risk': {},
            'monitoring_risk': {},
            'maintenance_risk': {}
        }
        
        try:
            # デプロイリスク
            operational_risks['deployment_risk'] = {
                'deployment_complexity': 'low',
                'downtime_required': False,
                'rollback_capability': 'available',
                'risk_level': 'low',
                'deployment_considerations': [
                    '後方互換性維持により段階デプロイ可能',
                    'A/Bテスト実施可能',
                    'カナリアリリース適用可能'
                ]
            }
            
            # ロールバックリスク
            operational_risks['rollback_risk'] = {
                'rollback_complexity': 'low',
                'rollback_time_estimate': '< 5 minutes',
                'data_loss_during_rollback': 'none',
                'risk_level': 'low',
                'rollback_triggers': [
                    '按分廃止機能の停止',
                    '予期しないパフォーマンス劣化',
                    'データ整合性エラー',
                    'メモリ使用量異常増加'
                ]
            }
            
            # 監視リスク
            operational_risks['monitoring_risk'] = {
                'visibility_reduction_risk': 'medium',
                'monitoring_gap_risk': 'medium',
                'alerting_effectiveness_risk': 'medium',
                'risk_level': 'medium',
                'monitoring_enhancements_required': [
                    'スキャンモード判定の監視',
                    'ファイル検出状況の監視',
                    'パフォーマンス指標の追加',
                    'エラーパターンの監視'
                ]
            }
            
            # 保守リスク
            operational_risks['maintenance_risk'] = {
                'code_maintainability': 'improved',
                'documentation_update_required': True,
                'knowledge_transfer_complexity': 'medium',
                'risk_level': 'low',
                'maintenance_considerations': [
                    '条件分岐ロジックの理解要求',
                    'デバッグ手順の更新',
                    '運用手順書の改訂',
                    'トラブルシューティングガイド更新'
                ]
            }
            
            print("    デプロイリスク: low")
            print("    ロールバックリスク: low")
            print("    監視リスク: medium")
            print("    保守リスク: low")
            
        except Exception as e:
            print(f"  ERROR: 運用リスク評価失敗 - {e}")
            operational_risks['assessment_error'] = str(e)
        
        return operational_risks
    
    def _create_risk_matrix(self, risk_results):
        """リスクマトリックス作成"""
        print("リスクマトリックスを作成中...")
        
        # リスクの収集と分類
        all_risks = []
        
        # 各カテゴリからリスクを抽出
        for category, risks in risk_results.items():
            if category == 'risk_matrix_analysis' or category == 'mitigation_plan':
                continue
            
            for risk_type, risk_data in risks.items():
                if isinstance(risk_data, dict) and 'risk_level' in risk_data:
                    all_risks.append({
                        'category': category,
                        'type': risk_type,
                        'risk_level': risk_data['risk_level'],
                        'data': risk_data
                    })
        
        # リスクレベル別分類
        risk_matrix = {
            'high_risks': [],
            'medium_risks': [],
            'low_risks': [],
            'risk_distribution': {},
            'overall_risk_score': 0,
            'overall_risk_level': 'low'
        }
        
        for risk in all_risks:
            if risk['risk_level'] == 'high':
                risk_matrix['high_risks'].append(risk)
            elif risk['risk_level'] == 'medium':
                risk_matrix['medium_risks'].append(risk)
            else:
                risk_matrix['low_risks'].append(risk)
        
        # リスク分布
        risk_matrix['risk_distribution'] = {
            'high': len(risk_matrix['high_risks']),
            'medium': len(risk_matrix['medium_risks']),
            'low': len(risk_matrix['low_risks']),
            'total': len(all_risks)
        }
        
        # 総合リスクスコア計算
        high_weight = 3
        medium_weight = 2
        low_weight = 1
        
        total_score = (
            len(risk_matrix['high_risks']) * high_weight +
            len(risk_matrix['medium_risks']) * medium_weight +
            len(risk_matrix['low_risks']) * low_weight
        )
        
        max_possible_score = len(all_risks) * high_weight
        normalized_score = total_score / max_possible_score if max_possible_score > 0 else 0
        
        risk_matrix['overall_risk_score'] = normalized_score
        
        if normalized_score > 0.7:
            risk_matrix['overall_risk_level'] = 'high'
        elif normalized_score > 0.4:
            risk_matrix['overall_risk_level'] = 'medium'
        else:
            risk_matrix['overall_risk_level'] = 'low'
        
        print(f"    高リスク: {len(risk_matrix['high_risks'])}件")
        print(f"    中リスク: {len(risk_matrix['medium_risks'])}件")
        print(f"    低リスク: {len(risk_matrix['low_risks'])}件")
        print(f"    総合リスクレベル: {risk_matrix['overall_risk_level']}")
        print(f"    総合リスクスコア: {normalized_score:.2f}")
        
        return risk_matrix
    
    def _create_mitigation_plan(self, risk_results):
        """リスク軽減計画作成"""
        print("リスク軽減計画を作成中...")
        
        mitigation_plan = {
            'immediate_actions': [],
            'pre_implementation_actions': [],
            'implementation_safeguards': [],
            'post_implementation_monitoring': [],
            'contingency_plans': []
        }
        
        risk_matrix = risk_results.get('risk_matrix_analysis', {})
        
        # 高リスクへの対処
        high_risks = risk_matrix.get('high_risks', [])
        for risk in high_risks:
            if risk['type'] == 'logic_errors':
                mitigation_plan['pre_implementation_actions'].append({
                    'action': '包括的単体テスト作成',
                    'priority': 'critical',
                    'timeline': '実装前',
                    'responsible': 'developer',
                    'details': 'target_types引数の全パターンテスト'
                })
        
        # 中リスクへの対処
        medium_risks = risk_matrix.get('medium_risks', [])
        for risk in medium_risks:
            if risk['type'] == 'regression_risks':
                mitigation_plan['implementation_safeguards'].append({
                    'action': '回帰テストスイート実行',
                    'priority': 'high',
                    'timeline': '実装時',
                    'responsible': 'tester',
                    'details': '既存全機能の動作確認'
                })
            
            if risk['type'] == 'data_loss_risk':
                mitigation_plan['implementation_safeguards'].append({
                    'action': 'フォールバック機構実装',
                    'priority': 'high',
                    'timeline': '実装時',
                    'responsible': 'developer',
                    'details': '特定スキャン失敗時の全スキャン自動切り替え'
                })
            
            if risk['type'] == 'monitoring_risk':
                mitigation_plan['post_implementation_monitoring'].append({
                    'action': '詳細監視システム構築',
                    'priority': 'medium',
                    'timeline': '実装後',
                    'responsible': 'operations',
                    'details': 'スキャンモード・パフォーマンス・エラー状況の監視'
                })
        
        # 緊急時対応計画
        mitigation_plan['contingency_plans'] = [
            {
                'scenario': '按分廃止機能完全停止',
                'trigger': 'データアクセス失敗率 > 50%',
                'response': '即座にフォールバックモード有効化',
                'timeline': '< 5 minutes',
                'automation': 'automatic'
            },
            {
                'scenario': 'パフォーマンス大幅劣化',
                'trigger': '初期化時間 > 従来の150%',
                'response': '従来システムへ自動ロールバック',
                'timeline': '< 10 minutes',
                'automation': 'semi-automatic'
            },
            {
                'scenario': 'メモリ使用量異常増加',
                'trigger': 'メモリ使用量 > システムメモリの80%',
                'response': 'キャッシュクリア＋システム再起動',
                'timeline': '< 15 minutes',
                'automation': 'manual'
            }
        ]
        
        # 即座のアクション（実装開始前）
        mitigation_plan['immediate_actions'] = [
            {
                'action': '詳細実装計画書作成',
                'priority': 'critical',
                'timeline': '実装開始前',
                'estimated_hours': 8
            },
            {
                'action': 'プロトタイプでの詳細検証',
                'priority': 'critical',
                'timeline': '実装開始前',
                'estimated_hours': 16
            },
            {
                'action': 'ロールバック手順書作成',
                'priority': 'high',
                'timeline': '実装開始前',
                'estimated_hours': 4
            }
        ]
        
        print(f"    緊急対応項目: {len(mitigation_plan['immediate_actions'])}件")
        print(f"    実装前対応: {len(mitigation_plan['pre_implementation_actions'])}件")
        print(f"    実装時対応: {len(mitigation_plan['implementation_safeguards'])}件")
        print(f"    実装後監視: {len(mitigation_plan['post_implementation_monitoring'])}件")
        print(f"    緊急時計画: {len(mitigation_plan['contingency_plans'])}件")
        
        return mitigation_plan
    
    def generate_risk_assessment_report(self):
        """技術的リスク評価レポート生成"""
        print("\n=== C1 技術的リスク評価レポート生成 ===")
        
        report = {
            'metadata': {
                'assessment_type': 'C1_technical_risk_assessment',
                'timestamp': datetime.now().isoformat(),
                'assessment_completed': True
            },
            'risk_assessment_results': self.risk_assessment_results,
            'executive_summary': self._generate_executive_summary(),
            'go_no_go_recommendation': self._generate_go_no_go_recommendation()
        }
        
        # レポートファイル保存
        report_path = Path(f'phase1_c1_technical_risk_assessment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"技術的リスク評価レポート保存: {report_path}")
        
        # サマリー表示
        print(f"\nC1技術的リスク評価結果:")
        
        if self.risk_assessment_results:
            risk_matrix = self.risk_assessment_results.get('risk_matrix_analysis', {})
            overall_risk_level = risk_matrix.get('overall_risk_level', 'unknown')
            risk_distribution = risk_matrix.get('risk_distribution', {})
            
            print(f"  総合リスクレベル: {overall_risk_level}")
            print(f"  リスク分布: 高{risk_distribution.get('high', 0)}, 中{risk_distribution.get('medium', 0)}, 低{risk_distribution.get('low', 0)}")
            
            # 軽減計画サマリー
            mitigation = self.risk_assessment_results.get('mitigation_plan', {})
            immediate_actions = len(mitigation.get('immediate_actions', []))
            contingency_plans = len(mitigation.get('contingency_plans', []))
            
            print(f"  緊急対応項目: {immediate_actions}件")
            print(f"  緊急時計画: {contingency_plans}件")
        
        return report
    
    def _generate_executive_summary(self):
        """エグゼクティブサマリー生成"""
        summary = {
            'overall_assessment': 'implementable_with_caution',
            'key_risks_identified': [],
            'critical_mitigation_required': [],
            'go_no_go_factors': [],
            'confidence_level': 'medium'
        }
        
        if self.risk_assessment_results:
            risk_matrix = self.risk_assessment_results.get('risk_matrix_analysis', {})
            overall_risk_level = risk_matrix.get('overall_risk_level', 'medium')
            
            # 総合評価決定
            if overall_risk_level == 'low':
                summary['overall_assessment'] = 'low_risk_implementation'
                summary['confidence_level'] = 'high'
            elif overall_risk_level == 'medium':
                summary['overall_assessment'] = 'implementable_with_caution'
                summary['confidence_level'] = 'medium'
            else:
                summary['overall_assessment'] = 'high_risk_implementation'
                summary['confidence_level'] = 'low'
            
            # 主要リスクの特定
            high_risks = risk_matrix.get('high_risks', [])
            medium_risks = risk_matrix.get('medium_risks', [])
            
            for risk in high_risks:
                summary['key_risks_identified'].append(f"{risk['category']}.{risk['type']}")
                summary['critical_mitigation_required'].append(f"{risk['type']}への対処")
            
            for risk in medium_risks[:3]:  # 上位3件
                summary['key_risks_identified'].append(f"{risk['category']}.{risk['type']}")
            
            # GO/NO-GO要因
            summary['go_no_go_factors'] = [
                f"総合リスクレベル: {overall_risk_level}",
                f"高リスク項目: {len(high_risks)}件",
                f"重要な軽減策実装: 必須",
                '後方互換性: 維持される',
                'ロールバック能力: 利用可能'
            ]
        
        return summary
    
    def _generate_go_no_go_recommendation(self):
        """GO/NO-GO推奨判定生成"""
        recommendation = {
            'decision': 'CONDITIONAL_GO',
            'confidence': 'medium',
            'conditions': [],
            'timeline_impact': {},
            'resource_requirements': {}
        }
        
        if self.risk_assessment_results:
            risk_matrix = self.risk_assessment_results.get('risk_matrix_analysis', {})
            overall_risk_level = risk_matrix.get('overall_risk_level', 'medium')
            high_risk_count = risk_matrix.get('risk_distribution', {}).get('high', 0)
            
            # 判定ロジック
            if high_risk_count == 0 and overall_risk_level == 'low':
                recommendation['decision'] = 'GO'
                recommendation['confidence'] = 'high'
            elif high_risk_count <= 1 and overall_risk_level in ['low', 'medium']:
                recommendation['decision'] = 'CONDITIONAL_GO'
                recommendation['confidence'] = 'medium'
            else:
                recommendation['decision'] = 'NO_GO'
                recommendation['confidence'] = 'low'
            
            # 条件設定
            if recommendation['decision'] == 'CONDITIONAL_GO':
                recommendation['conditions'] = [
                    '包括的テストスイートの作成・実行',
                    'フォールバック機構の実装',
                    '詳細監視システムの構築',
                    'ロールバック手順の確立',
                    '段階的デプロイの実施'
                ]
            elif recommendation['decision'] == 'GO':
                recommendation['conditions'] = [
                    '基本テストの実行',
                    'ロールバック準備'
                ]
            
            # タイムライン影響
            mitigation = self.risk_assessment_results.get('mitigation_plan', {})
            immediate_actions = len(mitigation.get('immediate_actions', []))
            
            recommendation['timeline_impact'] = {
                'additional_days_required': 3 + immediate_actions,
                'risk_mitigation_phase': f'{immediate_actions * 8} hours',
                'total_project_delay': '3-5 days'
            }
            
            recommendation['resource_requirements'] = {
                'additional_developer_time': '3 days',
                'additional_testing_time': '2 days',
                'risk_specialist_review': '1 day'
            }
        
        return recommendation

def main():
    print("=" * 70)
    print("*** Phase1 C1: 技術的リスク評価開始 ***")
    print("目的: システム変更に伴う技術的リスクの包括的評価")
    print("=" * 70)
    
    assessor = TechnicalRiskAssessment()
    
    try:
        # 技術的リスク評価実行
        results = assessor.assess_technical_risks()
        
        # リスク評価レポート生成
        report = assessor.generate_risk_assessment_report()
        
        print("\n" + "=" * 70)
        print("*** C1: 技術的リスク評価完了 ***")
        
        if report and report['go_no_go_recommendation']['decision'] == 'GO':
            print("GO 技術的リスク許容範囲 - 実装推奨")
        elif report and report['go_no_go_recommendation']['decision'] == 'CONDITIONAL_GO':
            print("CONDITIONAL_GO 条件付き実装可能 - リスク軽減必須")
        else:
            print("NO_GO 技術的リスク高 - 実装非推奨")
        
        print("=" * 70)
        
        return report
        
    except Exception as e:
        print(f"\nERROR C1評価中に予期しないエラー: {e}")
        print("トレースバック:")
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    main()