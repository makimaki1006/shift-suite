#!/usr/bin/env python3
"""
Phase1 A2: 機能動作確認
現在の990ファイルスキャン（実際334ファイル）の詳細動作分析
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import traceback

class FunctionalVerification:
    """機能動作確認器"""
    
    def __init__(self):
        self.verification_results = {}
        self.scan_details = {}
        
    def verify_unified_system_behavior(self):
        """統一システムの動作検証"""
        print("=== A2: 統一システム機能動作確認 ===")
        
        verification_results = {
            'scan_behavior_analysis': {},
            'file_detection_analysis': {},
            'metadata_generation_analysis': {},
            'proportional_abolition_access': {},
            'system_functionality_summary': {}
        }
        
        # 1. スキャン動作の詳細分析
        print("\n【スキャン動作分析】")
        scan_analysis = self._analyze_scan_behavior()
        verification_results['scan_behavior_analysis'] = scan_analysis
        
        # 2. ファイル検出の詳細分析
        print("\n【ファイル検出分析】")
        detection_analysis = self._analyze_file_detection()
        verification_results['file_detection_analysis'] = detection_analysis
        
        # 3. メタデータ生成の分析
        print("\n【メタデータ生成分析】")
        metadata_analysis = self._analyze_metadata_generation()
        verification_results['metadata_generation_analysis'] = metadata_analysis
        
        # 4. 按分廃止データアクセスの分析
        print("\n【按分廃止アクセス分析】")
        proportional_access = self._analyze_proportional_abolition_access()
        verification_results['proportional_abolition_access'] = proportional_access
        
        # 5. システム機能性サマリー
        print("\n【システム機能性評価】")
        functionality_summary = self._evaluate_system_functionality(verification_results)
        verification_results['system_functionality_summary'] = functionality_summary
        
        self.verification_results = verification_results
        return verification_results
    
    def _analyze_scan_behavior(self):
        """スキャン動作の詳細分析"""
        print("統一システムのスキャン動作を分析中...")
        
        scan_analysis = {
            'scan_trigger_points': [],
            'scan_scope_analysis': {},
            'scan_efficiency_analysis': {},
            'scan_pattern_analysis': {}
        }
        
        try:
            # 統一システムをインポートしてスキャン動作を観察
            sys.path.insert(0, '.')
            from unified_data_pipeline_architecture import (
                get_unified_registry, UnifiedDataRegistry, DataType
            )
            
            print("  統一システムインポート成功")
            
            # レジストリ初期化時のスキャン観察
            print("  レジストリ初期化によるスキャン観察...")
            registry = get_unified_registry()
            
            # スキャン結果の詳細分析
            if hasattr(registry, 'metadata_store'):
                total_files = len(registry.metadata_store)
                print(f"    登録ファイル数: {total_files}")
                
                scan_analysis['scan_scope_analysis'] = {
                    'total_scanned_files': total_files,
                    'expected_files_for_proportional': 2,
                    'overhead_files': max(0, total_files - 2),
                    'efficiency_ratio': 2 / total_files if total_files > 0 else 0,
                    'waste_ratio': max(0, total_files - 2) / total_files if total_files > 0 else 0
                }
                
                print(f"    オーバーヘッド: {max(0, total_files - 2)}ファイル")
                print(f"    効率性: {2 / total_files * 100 if total_files > 0 else 0:.1f}%")
                print(f"    無駄度: {max(0, total_files - 2) / total_files * 100 if total_files > 0 else 0:.1f}%")
                
                # ファイルタイプ別分析
                file_types = {}
                data_types = {}
                
                for file_path, metadata in registry.metadata_store.items():
                    # 拡張子別
                    ext = Path(file_path).suffix
                    file_types[ext] = file_types.get(ext, 0) + 1
                    
                    # データタイプ別
                    if hasattr(metadata, 'data_type'):
                        dtype = str(metadata.data_type)
                        data_types[dtype] = data_types.get(dtype, 0) + 1
                
                scan_analysis['scan_pattern_analysis'] = {
                    'file_types_scanned': file_types,
                    'data_types_detected': data_types,
                    'proportional_abolition_files': [
                        f for f in registry.metadata_store.keys() 
                        if 'proportional_abolition' in f.lower()
                    ]
                }
                
                print(f"    ファイルタイプ別: {file_types}")
                print(f"    按分廃止ファイル: {len(scan_analysis['scan_pattern_analysis']['proportional_abolition_files'])}件")
                
            scan_analysis['scan_trigger_points'].append({
                'trigger': 'registry_initialization',
                'timestamp': datetime.now().isoformat(),
                'files_scanned': total_files,
                'success': True
            })
            
        except Exception as e:
            print(f"  ERROR スキャン動作分析失敗: {e}")
            scan_analysis['scan_trigger_points'].append({
                'trigger': 'registry_initialization',
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'success': False
            })
        
        return scan_analysis
    
    def _analyze_file_detection(self):
        """ファイル検出の詳細分析"""
        print("ファイル検出ロジックを分析中...")
        
        detection_analysis = {
            'detection_accuracy': {},
            'false_positives': [],
            'false_negatives': [],
            'detection_logic_evaluation': {}
        }
        
        try:
            # 実際のファイルシステムと比較
            current_dir = Path('.')
            
            # 実際の按分廃止ファイル
            actual_proportional_files = list(current_dir.glob('*proportional*'))
            actual_proportional_files = [f for f in actual_proportional_files if f.is_file()]
            
            print(f"  実際の按分関連ファイル: {len(actual_proportional_files)}件")
            for f in actual_proportional_files:
                print(f"    {f.name}")
            
            # 統一システムが検出したファイル
            from unified_data_pipeline_architecture import get_unified_registry, DataType
            registry = get_unified_registry()
            
            detected_proportional = []
            if hasattr(registry, 'metadata_store'):
                for file_path, metadata in registry.metadata_store.items():
                    if 'proportional' in file_path.lower():
                        detected_proportional.append(file_path)
            
            print(f"  統一システム検出: {len(detected_proportional)}件")
            
            # 検出精度分析
            actual_names = set(f.name for f in actual_proportional_files)
            detected_names = set(Path(f).name for f in detected_proportional)
            
            true_positives = actual_names.intersection(detected_names)
            false_positives = detected_names - actual_names  
            false_negatives = actual_names - detected_names
            
            detection_analysis['detection_accuracy'] = {
                'true_positives': list(true_positives),
                'false_positives': list(false_positives),
                'false_negatives': list(false_negatives),
                'precision': len(true_positives) / len(detected_names) if detected_names else 0,
                'recall': len(true_positives) / len(actual_names) if actual_names else 0
            }
            
            print(f"  検出精度:")
            print(f"    正検出: {len(true_positives)}件")
            print(f"    誤検出: {len(false_positives)}件") 
            print(f"    未検出: {len(false_negatives)}件")
            print(f"    精度: {len(true_positives) / len(detected_names) * 100 if detected_names else 0:.1f}%")
            print(f"    再現率: {len(true_positives) / len(actual_names) * 100 if actual_names else 0:.1f}%")
            
        except Exception as e:
            print(f"  ERROR ファイル検出分析失敗: {e}")
            detection_analysis['detection_logic_evaluation']['error'] = str(e)
        
        return detection_analysis
    
    def _analyze_metadata_generation(self):
        """メタデータ生成の分析"""
        print("メタデータ生成プロセスを分析中...")
        
        metadata_analysis = {
            'metadata_completeness': {},
            'metadata_accuracy': {},
            'metadata_overhead': {},
            'metadata_utility': {}
        }
        
        try:
            from unified_data_pipeline_architecture import get_unified_registry
            registry = get_unified_registry()
            
            if hasattr(registry, 'metadata_store'):
                total_metadata = len(registry.metadata_store)
                
                # メタデータの完全性チェック
                complete_metadata = 0
                incomplete_metadata = 0
                metadata_fields_analysis = {}
                
                for file_path, metadata in registry.metadata_store.items():
                    fields_present = []
                    
                    if hasattr(metadata, 'data_type'):
                        fields_present.append('data_type')
                    if hasattr(metadata, 'stage'):
                        fields_present.append('stage')
                    if hasattr(metadata, 'priority'):
                        fields_present.append('priority')
                    if hasattr(metadata, 'hash_value'):
                        fields_present.append('hash_value')
                    if hasattr(metadata, 'size_bytes'):
                        fields_present.append('size_bytes')
                    
                    if len(fields_present) >= 3:  # 基本的なフィールドが揃っている
                        complete_metadata += 1
                    else:
                        incomplete_metadata += 1
                    
                    for field in fields_present:
                        metadata_fields_analysis[field] = metadata_fields_analysis.get(field, 0) + 1
                
                metadata_analysis['metadata_completeness'] = {
                    'total_metadata_entries': total_metadata,
                    'complete_entries': complete_metadata,
                    'incomplete_entries': incomplete_metadata,
                    'completeness_rate': complete_metadata / total_metadata if total_metadata > 0 else 0,
                    'field_coverage': metadata_fields_analysis
                }
                
                print(f"  メタデータエントリ: {total_metadata}件")
                print(f"  完全なエントリ: {complete_metadata}件")
                print(f"  完全性率: {complete_metadata / total_metadata * 100 if total_metadata > 0 else 0:.1f}%")
                
                # 按分廃止に対するメタデータの有用性評価
                proportional_metadata_count = 0
                for file_path, metadata in registry.metadata_store.items():
                    if 'proportional' in file_path.lower():
                        proportional_metadata_count += 1
                
                metadata_analysis['metadata_utility'] = {
                    'proportional_abolition_metadata': proportional_metadata_count,
                    'total_metadata': total_metadata,
                    'utility_ratio': proportional_metadata_count / total_metadata if total_metadata > 0 else 0,
                    'overhead_metadata': total_metadata - proportional_metadata_count
                }
                
                print(f"  按分廃止用メタデータ: {proportional_metadata_count}件")
                print(f"  メタデータ有用率: {proportional_metadata_count / total_metadata * 100 if total_metadata > 0 else 0:.1f}%")
                print(f"  オーバーヘッドメタデータ: {total_metadata - proportional_metadata_count}件")
            
        except Exception as e:
            print(f"  ERROR メタデータ分析失敗: {e}")
            metadata_analysis['error'] = str(e)
        
        return metadata_analysis
    
    def _analyze_proportional_abolition_access(self):
        """按分廃止データアクセスの分析"""
        print("按分廃止データアクセスを分析中...")
        
        access_analysis = {
            'access_success_rate': {},
            'access_performance': {},
            'data_quality': {},
            'access_path_analysis': {}
        }
        
        try:
            from unified_data_pipeline_architecture import get_unified_registry, DataType
            import time
            
            registry = get_unified_registry()
            
            # 按分廃止データへのアクセステスト
            access_attempts = [
                {
                    'data_type': DataType.PROPORTIONAL_ABOLITION_ROLE,
                    'description': '按分廃止職種データ'
                },
                {
                    'data_type': DataType.PROPORTIONAL_ABOLITION_ORG,  
                    'description': '按分廃止組織データ'
                }
            ]
            
            access_results = []
            
            for attempt in access_attempts:
                try:
                    start_time = time.perf_counter()
                    data = registry.get_data(attempt['data_type'])
                    end_time = time.perf_counter()
                    
                    access_time = end_time - start_time
                    
                    result = {
                        'data_type': str(attempt['data_type']),
                        'description': attempt['description'],
                        'access_time_seconds': access_time,
                        'success': data is not None,
                        'data_shape': None,
                        'data_size_mb': 0
                    }
                    
                    if data is not None:
                        try:
                            if hasattr(data, 'shape'):
                                result['data_shape'] = data.shape
                            if hasattr(data, 'memory_usage'):
                                result['data_size_mb'] = data.memory_usage(deep=True).sum() / (1024 * 1024)
                        except:
                            pass
                    
                    access_results.append(result)
                    
                    if result['success']:
                        print(f"    {result['description']}: OK ({access_time:.3f}秒)")
                        if result['data_shape']:
                            print(f"      形状: {result['data_shape']}")
                    else:
                        print(f"    {result['description']}: NG")
                    
                except Exception as e:
                    access_results.append({
                        'data_type': str(attempt['data_type']),
                        'description': attempt['description'],
                        'success': False,
                        'error': str(e)
                    })
                    print(f"    {attempt['description']}: ERROR - {e}")
            
            # アクセス成功率計算
            successful_accesses = [r for r in access_results if r['success']]
            access_analysis['access_success_rate'] = {
                'successful_accesses': len(successful_accesses),
                'total_attempts': len(access_results),
                'success_rate': len(successful_accesses) / len(access_results) if access_results else 0
            }
            
            if successful_accesses:
                avg_access_time = sum(r['access_time_seconds'] for r in successful_accesses if 'access_time_seconds' in r) / len(successful_accesses)
                access_analysis['access_performance'] = {
                    'average_access_time_seconds': avg_access_time,
                    'access_results': access_results
                }
                print(f"  平均アクセス時間: {avg_access_time:.3f}秒")
            
            print(f"  アクセス成功率: {len(successful_accesses)}/{len(access_results)} ({len(successful_accesses)/len(access_results)*100:.1f}%)")
            
        except Exception as e:
            print(f"  ERROR 按分廃止アクセス分析失敗: {e}")
            access_analysis['error'] = str(e)
        
        return access_analysis
    
    def _evaluate_system_functionality(self, verification_results):
        """システム機能性の総合評価"""
        print("システム機能性を総合評価中...")
        
        functionality_summary = {
            'overall_functionality_score': 0,
            'functional_areas_assessment': {},
            'critical_issues': [],
            'optimization_opportunities': [],
            'next_phase_recommendations': []
        }
        
        try:
            # スキャン機能の評価
            scan_analysis = verification_results.get('scan_behavior_analysis', {})
            scan_scope = scan_analysis.get('scan_scope_analysis', {})
            
            if scan_scope:
                efficiency_ratio = scan_scope.get('efficiency_ratio', 0)
                if efficiency_ratio < 0.1:  # 10%未満の効率
                    functionality_summary['critical_issues'].append({
                        'area': 'scan_efficiency',
                        'issue': f'スキャン効率が{efficiency_ratio*100:.1f}%と極めて低い',
                        'impact': 'high',
                        'recommendation': 'スキャン対象の最適化が急務'
                    })
                
                functionality_summary['functional_areas_assessment']['scan_functionality'] = {
                    'score': min(efficiency_ratio * 10, 10),  # 効率性ベースのスコア
                    'efficiency_ratio': efficiency_ratio,
                    'assessment': 'poor' if efficiency_ratio < 0.1 else 'fair' if efficiency_ratio < 0.5 else 'good'
                }
            
            # 検出機能の評価  
            detection_analysis = verification_results.get('file_detection_analysis', {})
            detection_accuracy = detection_analysis.get('detection_accuracy', {})
            
            if detection_accuracy:
                precision = detection_accuracy.get('precision', 0)
                recall = detection_accuracy.get('recall', 0)
                
                functionality_summary['functional_areas_assessment']['detection_functionality'] = {
                    'score': (precision + recall) * 5,  # 精度と再現率の平均×5
                    'precision': precision,
                    'recall': recall,
                    'assessment': 'excellent' if (precision + recall) > 1.8 else 'good' if (precision + recall) > 1.2 else 'fair'
                }
            
            # アクセス機能の評価
            access_analysis = verification_results.get('proportional_abolition_access', {})
            access_success = access_analysis.get('access_success_rate', {})
            
            if access_success:
                success_rate = access_success.get('success_rate', 0)
                
                functionality_summary['functional_areas_assessment']['access_functionality'] = {
                    'score': success_rate * 10,  # 成功率×10
                    'success_rate': success_rate,
                    'assessment': 'excellent' if success_rate > 0.9 else 'good' if success_rate > 0.7 else 'poor'
                }
                
                if success_rate < 0.8:
                    functionality_summary['critical_issues'].append({
                        'area': 'data_access',
                        'issue': f'按分廃止データアクセス成功率が{success_rate*100:.1f}%',
                        'impact': 'high',
                        'recommendation': 'データアクセス機構の改善が必要'
                    })
            
            # 総合スコア計算
            area_scores = [
                area['score'] for area in functionality_summary['functional_areas_assessment'].values()
                if 'score' in area
            ]
            
            if area_scores:
                functionality_summary['overall_functionality_score'] = sum(area_scores) / len(area_scores)
            
            # 最適化機会の特定
            if scan_scope and scan_scope.get('waste_ratio', 0) > 0.9:  # 90%以上が無駄
                functionality_summary['optimization_opportunities'].append({
                    'area': 'scan_optimization',
                    'opportunity': f"スキャン対象の{scan_scope.get('waste_ratio', 0)*100:.1f}%が按分廃止に不要",
                    'potential_improvement': '大幅な性能向上が期待',
                    'implementation_complexity': 'medium'
                })
            
            # 次フェーズ推奨事項
            if len(functionality_summary['critical_issues']) == 0:
                functionality_summary['next_phase_recommendations'].append('B1: 実装可能性検証への移行推奨')
            else:
                functionality_summary['next_phase_recommendations'].append('システム修復後にB1検証実施')
            
            # 総合評価出力
            overall_score = functionality_summary['overall_functionality_score']
            print(f"  総合機能性スコア: {overall_score:.1f}/10")
            print(f"  重要問題: {len(functionality_summary['critical_issues'])}件")
            print(f"  最適化機会: {len(functionality_summary['optimization_opportunities'])}件")
            
        except Exception as e:
            print(f"  ERROR 機能性評価失敗: {e}")
            functionality_summary['evaluation_error'] = str(e)
        
        return functionality_summary
    
    def generate_functional_verification_report(self):
        """機能検証レポート生成"""
        print("\n=== A2 機能検証レポート生成 ===")
        
        report = {
            'metadata': {
                'verification_type': 'A2_functional_verification',
                'timestamp': datetime.now().isoformat(),
                'verification_completed': True
            },
            'verification_results': self.verification_results,
            'key_findings': self._generate_key_findings(),
            'phase1_completion_status': self._assess_phase1_completion()
        }
        
        # レポートファイル保存
        report_path = Path(f'phase1_a2_functional_verification_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"機能検証レポート保存: {report_path}")
        
        # サマリー表示
        print(f"\nA2機能動作確認結果:")
        
        if self.verification_results:
            summary = self.verification_results.get('system_functionality_summary', {})
            overall_score = summary.get('overall_functionality_score', 0)
            critical_issues = len(summary.get('critical_issues', []))
            
            print(f"  機能性スコア: {overall_score:.1f}/10")
            print(f"  重要問題: {critical_issues}件")
            
            # スキャン効率の表示
            scan_analysis = self.verification_results.get('scan_behavior_analysis', {})
            scan_scope = scan_analysis.get('scan_scope_analysis', {})
            if scan_scope:
                efficiency = scan_scope.get('efficiency_ratio', 0) * 100
                waste = scan_scope.get('waste_ratio', 0) * 100
                print(f"  スキャン効率性: {efficiency:.1f}%")
                print(f"  スキャン無駄度: {waste:.1f}%")
            
            # アクセス成功率の表示
            access_analysis = self.verification_results.get('proportional_abolition_access', {})
            access_success = access_analysis.get('access_success_rate', {})
            if access_success:
                success_rate = access_success.get('success_rate', 0) * 100
                print(f"  按分廃止アクセス: {success_rate:.1f}%成功")
        
        return report
    
    def _generate_key_findings(self):
        """主要発見事項の生成"""
        key_findings = []
        
        if self.verification_results:
            # スキャン効率の発見
            scan_analysis = self.verification_results.get('scan_behavior_analysis', {})
            scan_scope = scan_analysis.get('scan_scope_analysis', {})
            
            if scan_scope:
                total_files = scan_scope.get('total_scanned_files', 0)
                efficiency = scan_scope.get('efficiency_ratio', 0)
                
                key_findings.append({
                    'finding': 'scan_efficiency_extremely_low',
                    'description': f'{total_files}ファイルをスキャンして按分廃止2ファイルにアクセス',
                    'efficiency_percentage': efficiency * 100,
                    'severity': 'critical' if efficiency < 0.1 else 'high',
                    'evidence': f'効率性{efficiency*100:.1f}%, 無駄度{scan_scope.get("waste_ratio", 0)*100:.1f}%'
                })
            
            # 検出精度の発見
            detection_analysis = self.verification_results.get('file_detection_analysis', {})
            detection_accuracy = detection_analysis.get('detection_accuracy', {})
            
            if detection_accuracy:
                precision = detection_accuracy.get('precision', 0)
                recall = detection_accuracy.get('recall', 0)
                
                if precision > 0.8 and recall > 0.8:
                    key_findings.append({
                        'finding': 'detection_accuracy_good',
                        'description': '按分廃止ファイルの検出精度は良好',
                        'precision': precision,
                        'recall': recall,
                        'severity': 'positive'
                    })
            
            # アクセス機能の発見
            access_analysis = self.verification_results.get('proportional_abolition_access', {})
            access_success = access_analysis.get('access_success_rate', {})
            
            if access_success:
                success_rate = access_success.get('success_rate', 0)
                
                key_findings.append({
                    'finding': 'data_access_functionality',
                    'description': '按分廃止データアクセス機能の評価',
                    'success_rate': success_rate,
                    'severity': 'positive' if success_rate > 0.8 else 'medium',
                    'assessment': '良好' if success_rate > 0.8 else '改善余地あり'
                })
        
        return key_findings
    
    def _assess_phase1_completion(self):
        """Phase1完了状況評価"""
        completion_status = {
            'a1_performance_completed': True,  # A1は完了済み
            'a2_functional_completed': True,   # A2は現在完了
            'ready_for_b1_implementation': False,
            'phase1_overall_success': False,
            'blocking_issues': [],
            'next_steps': []
        }
        
        # A2の結果に基づく評価
        if self.verification_results:
            summary = self.verification_results.get('system_functionality_summary', {})
            critical_issues = summary.get('critical_issues', [])
            overall_score = summary.get('overall_functionality_score', 0)
            
            if len(critical_issues) == 0 and overall_score > 6:
                completion_status['ready_for_b1_implementation'] = True
                completion_status['phase1_overall_success'] = True
                completion_status['next_steps'].append('B1: 実装可能性検証の開始')
            else:
                completion_status['blocking_issues'] = [issue['issue'] for issue in critical_issues]
                if overall_score <= 6:
                    completion_status['blocking_issues'].append(f'機能性スコア低下({overall_score:.1f}/10)')
                completion_status['next_steps'].append('システム改善後にB1検証実施')
        
        return completion_status

def main():
    print("=" * 70)
    print("*** Phase1 A2: 機能動作確認開始 ***")
    print("目的: 統一システムの詳細動作分析")  
    print("=" * 70)
    
    verifier = FunctionalVerification()
    
    try:
        # 機能動作検証実行
        results = verifier.verify_unified_system_behavior()
        
        # 機能検証レポート生成
        report = verifier.generate_functional_verification_report()
        
        print("\n" + "=" * 70)
        print("*** A2: 機能動作確認完了 ***")
        
        if report and report['phase1_completion_status']['ready_for_b1_implementation']:
            print("OK Phase1 基礎検証完了 - B1実装可能性検証へ移行可能")
        else:
            print("WARN システム改善推奨 - 課題解決後にB1検証実施")
        
        print("=" * 70)
        
        return report
        
    except Exception as e:
        print(f"\nERROR A2検証中に予期しないエラー: {e}")
        print("トレースバック:")
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    main()