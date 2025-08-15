#!/usr/bin/env python3
"""
Phase1 A1: パフォーマンス測定
現在の統一システムの実際のパフォーマンスをベースラインとして測定
"""

import time
import psutil
import threading
import gc
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import sys
import traceback

class PerformanceMeasurement:
    """パフォーマンス測定器"""
    
    def __init__(self):
        self.measurements = {}
        self.baseline_established = False
        
    def measure_current_unified_system(self):
        """現在の統一システムのパフォーマンス測定"""
        print("=== A1: 現在システム パフォーマンス測定 ===")
        
        measurement_results = {
            'system_info': self._get_system_info(),
            'unified_system_performance': {},
            'traditional_system_performance': {},
            'comparison_analysis': {}
        }
        
        print("システム情報:")
        for key, value in measurement_results['system_info'].items():
            print(f"  {key}: {value}")
        
        # 1. 統一システムのパフォーマンス測定
        print("\n【統一システム測定開始】")
        unified_perf = self._measure_unified_system_initialization()
        measurement_results['unified_system_performance'] = unified_perf
        
        # 2. 従来システムのパフォーマンス測定（比較用）
        print("\n【従来システム測定開始】")
        traditional_perf = self._measure_traditional_system()
        measurement_results['traditional_system_performance'] = traditional_perf
        
        # 3. 比較分析
        print("\n【比較分析】")
        comparison = self._analyze_performance_comparison(unified_perf, traditional_perf)
        measurement_results['comparison_analysis'] = comparison
        
        self.measurements = measurement_results
        return measurement_results
    
    def _get_system_info(self):
        """システム情報取得"""
        try:
            system_info = {
                'platform': sys.platform,
                'python_version': sys.version.split()[0],
                'cpu_count': psutil.cpu_count(),
                'cpu_count_logical': psutil.cpu_count(logical=True),
                'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'disk_type': self._detect_disk_type(),
                'current_directory': str(Path.cwd()),
                'measurement_time': datetime.now().isoformat()
            }
            return system_info
        except Exception as e:
            return {'error': str(e)}
    
    def _detect_disk_type(self):
        """ディスクタイプ検出（簡易版）"""
        try:
            # Windows環境での簡易SSD検出
            if sys.platform == 'win32':
                import subprocess
                result = subprocess.run(['powershell', '-Command', 
                                       'Get-PhysicalDisk | Select-Object MediaType'], 
                                       capture_output=True, text=True, timeout=5)
                if 'SSD' in result.stdout:
                    return 'SSD'
                else:
                    return 'HDD_or_Unknown'
            else:
                return 'Unknown'
        except:
            return 'Detection_Failed'
    
    def _measure_unified_system_initialization(self):
        """統一システム初期化の測定"""
        print("統一システム初期化測定中...")
        
        performance_data = {
            'initialization_attempts': [],
            'average_metrics': {},
            'resource_usage': {},
            'error_count': 0
        }
        
        # 複数回測定して平均を取る
        num_attempts = 3
        successful_attempts = []
        
        for attempt in range(num_attempts):
            print(f"  試行 {attempt + 1}/{num_attempts}")
            
            try:
                # メモリとCPU使用量の測定開始
                initial_memory = psutil.virtual_memory().used
                initial_cpu_percent = psutil.cpu_percent(interval=None)
                
                # 統一システムの初期化時間測定
                start_time = time.time()
                start_perf_time = time.perf_counter()
                
                # 統一システムのインポートと初期化
                sys.path.insert(0, '.')
                
                # 既存モジュールをクリア（新鮮な測定のため）
                modules_to_clear = [m for m in sys.modules.keys() 
                                  if 'unified_data_pipeline' in m]
                for module in modules_to_clear:
                    if module in sys.modules:
                        del sys.modules[module]
                
                # 統一システムのインポート
                try:
                    from unified_data_pipeline_architecture import (
                        get_unified_registry, UnifiedDataRegistry, DataType
                    )
                    import_success = True
                except ImportError as e:
                    print(f"    ⚠️ インポートエラー: {e}")
                    import_success = False
                    performance_data['error_count'] += 1
                    continue
                
                if import_success:
                    # 統一レジストリの初期化
                    try:
                        registry = get_unified_registry()
                        initialization_success = True
                    except Exception as e:
                        print(f"    ⚠️ 初期化エラー: {e}")
                        initialization_success = False
                        performance_data['error_count'] += 1
                        continue
                    
                    # データスキャンの実行
                    if initialization_success:
                        try:
                            # 実際にデータ取得を試行
                            test_data = registry.get_data(DataType.PROPORTIONAL_ABOLITION_ROLE)
                            data_retrieval_success = test_data is not None
                        except Exception as e:
                            print(f"    ⚠️ データ取得エラー: {e}")
                            data_retrieval_success = False
                            performance_data['error_count'] += 1
                
                # 測定終了
                end_time = time.time()
                end_perf_time = time.perf_counter()
                
                # リソース使用量測定
                final_memory = psutil.virtual_memory().used
                final_cpu_percent = psutil.cpu_percent(interval=0.1)
                
                # 結果記録
                attempt_result = {
                    'attempt_number': attempt + 1,
                    'total_time_seconds': end_time - start_time,
                    'precise_time_seconds': end_perf_time - start_perf_time,
                    'memory_used_mb': (final_memory - initial_memory) / (1024 * 1024),
                    'cpu_usage_percent': final_cpu_percent - initial_cpu_percent,
                    'import_success': import_success,
                    'initialization_success': initialization_success if import_success else False,
                    'data_retrieval_success': data_retrieval_success if import_success and initialization_success else False,
                    'timestamp': datetime.now().isoformat()
                }
                
                performance_data['initialization_attempts'].append(attempt_result)
                
                if import_success and initialization_success:
                    successful_attempts.append(attempt_result)
                    print(f"    OK 成功: {attempt_result['precise_time_seconds']:.3f}秒")
                else:
                    print(f"    ❌ 失敗")
                
                # メモリクリーンアップ
                gc.collect()
                time.sleep(0.5)  # システム安定化待機
                
            except Exception as e:
                print(f"    ERROR 予期しないエラー: {e}")
                performance_data['error_count'] += 1
                performance_data['initialization_attempts'].append({
                    'attempt_number': attempt + 1,
                    'error': str(e),
                    'traceback': traceback.format_exc(),
                    'timestamp': datetime.now().isoformat()
                })
        
        # 平均値計算
        if successful_attempts:
            avg_time = sum(a['precise_time_seconds'] for a in successful_attempts) / len(successful_attempts)
            avg_memory = sum(a['memory_used_mb'] for a in successful_attempts) / len(successful_attempts)
            avg_cpu = sum(a['cpu_usage_percent'] for a in successful_attempts) / len(successful_attempts)
            
            performance_data['average_metrics'] = {
                'avg_initialization_time_seconds': avg_time,
                'avg_memory_usage_mb': avg_memory,
                'avg_cpu_usage_percent': avg_cpu,
                'success_rate': len(successful_attempts) / num_attempts,
                'successful_attempts': len(successful_attempts),
                'total_attempts': num_attempts
            }
            
            print(f"\n統一システム平均パフォーマンス:")
            print(f"  初期化時間: {avg_time:.3f}秒")
            print(f"  メモリ使用: {avg_memory:.1f}MB")
            print(f"  CPU使用率: {avg_cpu:.1f}%")
            print(f"  成功率: {len(successful_attempts)}/{num_attempts} ({len(successful_attempts)/num_attempts*100:.1f}%)")
        else:
            print("❌ 全ての初期化試行が失敗しました")
            performance_data['average_metrics'] = {
                'avg_initialization_time_seconds': 0,
                'avg_memory_usage_mb': 0,
                'avg_cpu_usage_percent': 0,
                'success_rate': 0,
                'successful_attempts': 0,
                'total_attempts': num_attempts
            }
        
        return performance_data
    
    def _measure_traditional_system(self):
        """従来システム（直接ファイルアクセス）の測定"""
        print("従来システム測定中...")
        
        performance_data = {
            'direct_access_attempts': [],
            'average_metrics': {},
            'file_operations': {},
            'error_count': 0
        }
        
        # 按分廃止ファイルの直接アクセス測定
        target_files = [
            'proportional_abolition_role_summary.parquet',
            'proportional_abolition_organization_summary.parquet'
        ]
        
        num_attempts = 3
        successful_attempts = []
        
        for attempt in range(num_attempts):
            print(f"  試行 {attempt + 1}/{num_attempts}")
            
            try:
                initial_memory = psutil.virtual_memory().used
                start_time = time.perf_counter()
                
                # 直接ファイルアクセス
                accessed_files = []
                total_file_size = 0
                
                for file_name in target_files:
                    file_path = Path('.') / file_name
                    
                    if file_path.exists():
                        try:
                            # ファイル統計情報取得
                            file_stat = file_path.stat()
                            total_file_size += file_stat.st_size
                            
                            # Parquetファイル読み込み（実際のデータアクセス）
                            import pandas as pd
                            df = pd.read_parquet(file_path)
                            
                            accessed_files.append({
                                'file_name': file_name,
                                'file_size_bytes': file_stat.st_size,
                                'rows': len(df),
                                'columns': len(df.columns),
                                'success': True
                            })
                            
                        except Exception as e:
                            accessed_files.append({
                                'file_name': file_name,
                                'error': str(e),
                                'success': False
                            })
                            performance_data['error_count'] += 1
                    else:
                        accessed_files.append({
                            'file_name': file_name,
                            'error': 'File not found',
                            'success': False
                        })
                        performance_data['error_count'] += 1
                
                end_time = time.perf_counter()
                final_memory = psutil.virtual_memory().used
                
                # 結果記録
                successful_files = [f for f in accessed_files if f['success']]
                attempt_result = {
                    'attempt_number': attempt + 1,
                    'total_time_seconds': end_time - start_time,
                    'memory_used_mb': (final_memory - initial_memory) / (1024 * 1024),
                    'files_accessed': len(successful_files),
                    'total_files': len(target_files),
                    'total_file_size_mb': total_file_size / (1024 * 1024),
                    'files_details': accessed_files,
                    'success_rate': len(successful_files) / len(target_files),
                    'timestamp': datetime.now().isoformat()
                }
                
                performance_data['direct_access_attempts'].append(attempt_result)
                
                if len(successful_files) > 0:
                    successful_attempts.append(attempt_result)
                    print(f"    OK 成功: {attempt_result['total_time_seconds']:.3f}秒, {len(successful_files)}ファイル")
                else:
                    print(f"    ❌ 失敗: ファイルアクセス不可")
                
                gc.collect()
                time.sleep(0.5)
                
            except Exception as e:
                print(f"    ERROR 予期しないエラー: {e}")
                performance_data['error_count'] += 1
        
        # 平均値計算
        if successful_attempts:
            avg_time = sum(a['total_time_seconds'] for a in successful_attempts) / len(successful_attempts)
            avg_memory = sum(a['memory_used_mb'] for a in successful_attempts) / len(successful_attempts)
            avg_files = sum(a['files_accessed'] for a in successful_attempts) / len(successful_attempts)
            
            performance_data['average_metrics'] = {
                'avg_access_time_seconds': avg_time,
                'avg_memory_usage_mb': avg_memory,
                'avg_files_accessed': avg_files,
                'success_rate': len(successful_attempts) / num_attempts,
                'successful_attempts': len(successful_attempts),
                'total_attempts': num_attempts
            }
            
            print(f"\n従来システム平均パフォーマンス:")
            print(f"  アクセス時間: {avg_time:.3f}秒")
            print(f"  メモリ使用: {avg_memory:.1f}MB")
            print(f"  アクセスファイル数: {avg_files:.1f}")
            print(f"  成功率: {len(successful_attempts)}/{num_attempts} ({len(successful_attempts)/num_attempts*100:.1f}%)")
        else:
            print("❌ 全ての従来システムアクセスが失敗しました")
            performance_data['average_metrics'] = {
                'avg_access_time_seconds': 0,
                'avg_memory_usage_mb': 0,
                'avg_files_accessed': 0,
                'success_rate': 0,
                'successful_attempts': 0,
                'total_attempts': num_attempts
            }
        
        return performance_data
    
    def _analyze_performance_comparison(self, unified_perf, traditional_perf):
        """パフォーマンス比較分析"""
        print("パフォーマンス比較分析中...")
        
        comparison = {
            'baseline_established': False,
            'performance_ratio': {},
            'bottleneck_analysis': {},
            'recommendations': []
        }
        
        # 成功した測定データがあるかチェック
        unified_success = unified_perf['average_metrics']['success_rate'] > 0
        traditional_success = traditional_perf['average_metrics']['success_rate'] > 0
        
        if unified_success and traditional_success:
            # パフォーマンス比較
            unified_time = unified_perf['average_metrics']['avg_initialization_time_seconds']
            traditional_time = traditional_perf['average_metrics']['avg_access_time_seconds']
            
            unified_memory = unified_perf['average_metrics']['avg_memory_usage_mb']
            traditional_memory = traditional_perf['average_metrics']['avg_memory_usage_mb']
            
            comparison['performance_ratio'] = {
                'time_ratio': unified_time / traditional_time if traditional_time > 0 else 0,
                'memory_ratio': unified_memory / traditional_memory if traditional_memory > 0 else 0,
                'unified_slower_by_factor': unified_time / traditional_time if traditional_time > 0 else 0,
                'unified_uses_more_memory_by_factor': unified_memory / traditional_memory if traditional_memory > 0 else 0
            }
            
            # ベースライン確立
            comparison['baseline_established'] = True
            self.baseline_established = True
            
            print(f"パフォーマンス比較結果:")
            print(f"  統一システム: {unified_time:.3f}秒, {unified_memory:.1f}MB")
            print(f"  従来システム: {traditional_time:.3f}秒, {traditional_memory:.1f}MB")
            print(f"  時間比: 統一システムは{unified_time/traditional_time:.1f}倍遅い")
            print(f"  メモリ比: 統一システムは{unified_memory/traditional_memory:.1f}倍多い")
            
            # ボトルネック分析
            if unified_time > traditional_time * 2:  # 2倍以上遅い場合
                comparison['bottleneck_analysis']['time_bottleneck'] = {
                    'severity': 'high',
                    'factor': unified_time / traditional_time,
                    'description': '統一システムの初期化時間が従来システムの2倍以上'
                }
                comparison['recommendations'].append('初期化プロセスの最適化が必要')
            
            if unified_memory > traditional_memory * 5:  # 5倍以上メモリを使用
                comparison['bottleneck_analysis']['memory_bottleneck'] = {
                    'severity': 'high', 
                    'factor': unified_memory / traditional_memory,
                    'description': '統一システムのメモリ使用量が従来システムの5倍以上'
                }
                comparison['recommendations'].append('メモリ使用量の最適化が必要')
            
        else:
            comparison['baseline_established'] = False
            self.baseline_established = False
            print("❌ ベースライン確立失敗: 一方または両方のシステムでエラー")
            
            if not unified_success:
                comparison['recommendations'].append('統一システムの基本動作修復が必要')
            if not traditional_success:
                comparison['recommendations'].append('按分廃止ファイルの存在確認が必要')
        
        return comparison
    
    def generate_baseline_report(self):
        """ベースラインレポート生成"""
        print("\n=== A1 ベースラインレポート生成 ===")
        
        report = {
            'metadata': {
                'measurement_type': 'A1_performance_baseline',
                'timestamp': datetime.now().isoformat(),
                'baseline_established': self.baseline_established
            },
            'measurements': self.measurements,
            'conclusions': self._generate_conclusions(),
            'next_phase_readiness': self._assess_next_phase_readiness()
        }
        
        # レポートファイル保存
        report_path = Path(f'phase1_a1_performance_baseline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"ベースラインレポート保存: {report_path}")
        
        # サマリー表示
        print(f"\nA1パフォーマンス測定結果:")
        print(f"  ベースライン確立: {'✅ 成功' if self.baseline_established else '❌ 失敗'}")
        
        if self.baseline_established:
            unified_time = self.measurements['unified_system_performance']['average_metrics']['avg_initialization_time_seconds']
            traditional_time = self.measurements['traditional_system_performance']['average_metrics']['avg_access_time_seconds']
            
            print(f"  統一システム初期化: {unified_time:.3f}秒")
            print(f"  従来システムアクセス: {traditional_time:.3f}秒")
            print(f"  性能差: {unified_time/traditional_time:.1f}倍")
            
            # 990ファイルスキャン問題の実証
            if unified_time > traditional_time * 10:  # 10倍以上遅い場合
                print(f"  🚨 重要発見: 統一システムは{unified_time/traditional_time:.1f}倍遅く、最適化が必要")
            elif unified_time > traditional_time * 2:  # 2倍以上遅い場合
                print(f"  ⚠️ 改善余地: 統一システムは{unified_time/traditional_time:.1f}倍遅く、最適化推奨")
            else:
                print(f"  ✅ 良好: 統一システムのオーバーヘッドは許容範囲")
        
        return report
    
    def _generate_conclusions(self):
        """結論生成"""
        conclusions = []
        
        if self.baseline_established:
            comparison = self.measurements['comparison_analysis']
            
            # 990ファイルスキャン問題の実証結果
            time_ratio = comparison['performance_ratio']['time_ratio']
            
            if time_ratio > 10:
                conclusions.append({
                    'type': 'critical_finding',
                    'conclusion': '990ファイルスキャン問題が実証された',
                    'evidence': f'統一システムは従来システムの{time_ratio:.1f}倍の時間を要する',
                    'implication': '最適化による大幅な性能改善が期待できる'
                })
            elif time_ratio > 2:
                conclusions.append({
                    'type': 'moderate_finding',
                    'conclusion': '統一システムに性能オーバーヘッドが存在',
                    'evidence': f'統一システムは従来システムの{time_ratio:.1f}倍の時間を要する',
                    'implication': '最適化による性能改善が可能'
                })
            else:
                conclusions.append({
                    'type': 'minimal_impact',
                    'conclusion': '統一システムの性能オーバーヘッドは軽微',
                    'evidence': f'統一システムは従来システムの{time_ratio:.1f}倍の時間',
                    'implication': '最適化の優先度は低い'
                })
            
            conclusions.append({
                'type': 'baseline_success',
                'conclusion': 'パフォーマンスベースライン確立成功',
                'evidence': '統一・従来両システムの測定完了',
                'implication': 'Phase2以降の詳細検証が可能'
            })
        else:
            conclusions.append({
                'type': 'baseline_failure',
                'conclusion': 'パフォーマンスベースライン確立失敗',
                'evidence': '統一システムまたは従来システムの測定失敗',
                'implication': 'システム修復またはPhase1の再実行が必要'
            })
        
        return conclusions
    
    def _assess_next_phase_readiness(self):
        """次フェーズ準備状況評価"""
        if self.baseline_established:
            return {
                'ready_for_phase2': True,
                'confidence_level': 'high',
                'prerequisites_met': [
                    'ベースライン性能データ取得完了',
                    '統一・従来システム比較データ利用可能',
                    'ボトルネック特定済み'
                ],
                'recommended_next_steps': [
                    'A2: 機能動作確認の実行',
                    'B1: 実装可能性検証の開始'
                ]
            }
        else:
            return {
                'ready_for_phase2': False,
                'confidence_level': 'low',
                'blocking_issues': [
                    'ベースライン確立失敗',
                    'システム基本動作に問題'
                ],
                'required_actions': [
                    'システム修復',
                    'A1の再実行',
                    '基本動作確認'
                ]
            }

def main():
    print("=" * 70)
    print("*** Phase1 A1: パフォーマンス測定開始 ***")
    print("目的: 現在システムのベースライン確立")
    print("=" * 70)
    
    measurer = PerformanceMeasurement()
    
    try:
        # パフォーマンス測定実行
        results = measurer.measure_current_unified_system()
        
        # ベースラインレポート生成
        report = measurer.generate_baseline_report()
        
        print("\n" + "=" * 70)
        print("*** A1: パフォーマンス測定完了 ***")
        if measurer.baseline_established:
            print("OK ベースライン確立成功 - Phase2検証可能")
        else:
            print("❌ ベースライン確立失敗 - システム修復必要")
        print("=" * 70)
        
        return report
        
    except Exception as e:
        print(f"\nERROR A1測定中に予期しないエラー: {e}")
        print("トレースバック:")
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    main()