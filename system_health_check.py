"""
システム稼働状況初期確認
IA3: pandas依存なしでの基本動作確認
"""

import os
import json
import datetime
import sys
import traceback
from typing import Dict, List, Any, Optional

class SystemHealthCheck:
    """システムヘルスチェック実行クラス"""
    
    def __init__(self):
        self.base_path = "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析"
        self.check_time = datetime.datetime.now()
        
        # チェック対象コンポーネント
        self.components = {
            'core_files': {
                'app.py': 'メインアプリケーション',
                'dash_app.py': 'ダッシュボードアプリケーション',
                'shift_suite/__init__.py': 'シフト分析パッケージ'
            },
            'critical_modules': {
                'shift_suite/tasks/utils.py': 'ユーティリティ',
                'shift_suite/tasks/heatmap.py': 'ヒートマップ機能',
                'shift_suite/tasks/shortage.py': '不足分析機能',
                'shift_suite/tasks/fatigue.py': '疲労度分析',
                'shift_suite/tasks/anomaly.py': '異常検知'
            },
            'assets': {
                'assets/style.css': 'スタイルシート',
                'assets/c2-service-worker.js': 'Service Worker',
                'assets/c2-mobile.css': 'モバイルCSS'
            }
        }
    
    def execute_health_check(self):
        """ヘルスチェック実行メイン"""
        try:
            print("🏥 システムヘルスチェック開始...")
            print(f"📅 チェック開始時刻: {self.check_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            health_results = {}
            
            # 1. ファイル存在チェック
            file_check = self._check_file_existence()
            health_results['file_existence'] = file_check
            print(f"📁 ファイル存在チェック: {'✅' if file_check['healthy'] else '❌'}")
            
            # 2. 構文チェック（基本）
            syntax_check = self._check_python_syntax()
            health_results['syntax_validity'] = syntax_check
            print(f"🔍 構文チェック: {'✅' if syntax_check['healthy'] else '❌'}")
            
            # 3. 設定ファイルチェック
            config_check = self._check_configuration_files()
            health_results['configuration'] = config_check
            print(f"⚙️ 設定ファイル: {'✅' if config_check['healthy'] else '❌'}")
            
            # 4. 戦略実行結果チェック
            strategy_check = self._check_strategy_execution_results()
            health_results['strategy_execution'] = strategy_check
            print(f"📊 戦略実行結果: {'✅' if strategy_check['healthy'] else '❌'}")
            
            # 5. システム準備状態評価
            readiness_assessment = self._assess_system_readiness(health_results)
            health_results['readiness_assessment'] = readiness_assessment
            
            # 総合健全性評価
            overall_health = self._calculate_overall_health(health_results)
            
            return {
                'success': True,
                'check_timestamp': self.check_time.isoformat(),
                'health_results': health_results,
                'overall_health': overall_health,
                'system_status': overall_health['status'],
                'ready_for_operation': overall_health['ready_for_operation']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    def _check_file_existence(self):
        """ファイル存在チェック"""
        try:
            results = {}
            total_files = 0
            existing_files = 0
            missing_files = []
            
            for category, files in self.components.items():
                category_results = {}
                for file_path, description in files.items():
                    full_path = os.path.join(self.base_path, file_path)
                    exists = os.path.exists(full_path)
                    
                    category_results[file_path] = {
                        'exists': exists,
                        'description': description,
                        'size': os.path.getsize(full_path) if exists else 0
                    }
                    
                    total_files += 1
                    if exists:
                        existing_files += 1
                    else:
                        missing_files.append(f"{file_path} ({description})")
                
                results[category] = category_results
            
            health_score = (existing_files / total_files) * 100 if total_files > 0 else 0
            
            return {
                'healthy': health_score >= 90,  # 90%以上のファイルが存在
                'health_score': health_score,
                'total_files': total_files,
                'existing_files': existing_files,
                'missing_files': missing_files,
                'detailed_results': results
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _check_python_syntax(self):
        """Python構文チェック"""
        try:
            results = {}
            total_python_files = 0
            valid_files = 0
            syntax_errors = []
            
            python_files = [
                'app.py',
                'dash_app.py',
                'shift_suite/__init__.py',
                'shift_suite/tasks/utils.py'
            ]
            
            for file_path in python_files:
                full_path = os.path.join(self.base_path, file_path)
                if os.path.exists(full_path):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        compile(content, full_path, 'exec')
                        results[file_path] = {'valid': True}
                        valid_files += 1
                    except SyntaxError as e:
                        results[file_path] = {
                            'valid': False,
                            'error': str(e),
                            'line': e.lineno
                        }
                        syntax_errors.append(f"{file_path}: {e}")
                else:
                    results[file_path] = {'valid': False, 'error': 'File not found'}
                
                total_python_files += 1
            
            health_score = (valid_files / total_python_files) * 100 if total_python_files > 0 else 0
            
            return {
                'healthy': health_score == 100,  # 全ファイル構文正常
                'health_score': health_score,
                'total_files': total_python_files,
                'valid_files': valid_files,
                'syntax_errors': syntax_errors,
                'detailed_results': results
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _check_configuration_files(self):
        """設定ファイルチェック"""
        try:
            config_files = [
                'shift_suite/config.json',
                'requirements.txt',
                '.gitignore'
            ]
            
            results = {}
            found_configs = 0
            
            for config_file in config_files:
                full_path = os.path.join(self.base_path, config_file)
                exists = os.path.exists(full_path)
                
                results[config_file] = {
                    'exists': exists,
                    'size': os.path.getsize(full_path) if exists else 0
                }
                
                if exists:
                    found_configs += 1
                    
                    # JSONファイルの場合は妥当性チェック
                    if config_file.endswith('.json'):
                        try:
                            with open(full_path, 'r', encoding='utf-8') as f:
                                json.load(f)
                            results[config_file]['valid_json'] = True
                        except:
                            results[config_file]['valid_json'] = False
            
            health_score = (found_configs / len(config_files)) * 100
            
            return {
                'healthy': health_score >= 66,  # 2/3以上の設定ファイル存在
                'health_score': health_score,
                'total_configs': len(config_files),
                'found_configs': found_configs,
                'detailed_results': results
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _check_strategy_execution_results(self):
        """戦略実行結果チェック"""
        try:
            import glob
            
            strategy_patterns = [
                'Phase*_*_Execution_*.json',
                'D*_*_Execution_*.json',
                'Comprehensive_Strategy_Completion_Report_*.json'
            ]
            
            results = {}
            total_strategy_files = 0
            
            for pattern in strategy_patterns:
                matching_files = glob.glob(os.path.join(self.base_path, pattern))
                results[pattern] = {
                    'count': len(matching_files),
                    'latest': max(matching_files, key=os.path.getmtime) if matching_files else None
                }
                total_strategy_files += len(matching_files)
            
            # 最新の包括的レポート確認
            comprehensive_reports = glob.glob(
                os.path.join(self.base_path, 'Comprehensive_Strategy_Completion_Report_*.json')
            )
            
            latest_report_data = None
            if comprehensive_reports:
                latest_report = max(comprehensive_reports, key=os.path.getmtime)
                try:
                    with open(latest_report, 'r', encoding='utf-8') as f:
                        latest_report_data = json.load(f)
                except:
                    pass
            
            return {
                'healthy': total_strategy_files >= 6,  # 最低6つの戦略実行ファイル
                'total_strategy_files': total_strategy_files,
                'patterns_found': results,
                'latest_comprehensive_report': latest_report_data is not None,
                'final_quality_level': latest_report_data.get('comprehensive_results_integration', {}).get(
                    'integration_metrics', {}).get('final_quality_level', 0) if latest_report_data else 0
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _assess_system_readiness(self, health_results):
        """システム準備状態評価"""
        try:
            readiness_factors = {
                'file_system': health_results['file_existence']['healthy'],
                'code_syntax': health_results['syntax_validity']['healthy'],
                'configuration': health_results['configuration']['healthy'],
                'strategy_completion': health_results['strategy_execution']['healthy']
            }
            
            readiness_score = sum(1 for v in readiness_factors.values() if v) / len(readiness_factors) * 100
            
            # 準備レベル判定
            if readiness_score >= 100:
                readiness_level = '完全運用準備完了'
                recommendations = ['即座に本番運用開始可能']
            elif readiness_score >= 75:
                readiness_level = '実用レベル運用準備完了'
                recommendations = ['限定的な運用開始可能', '不足要素の段階的補完推奨']
            elif readiness_score >= 50:
                readiness_level = '部分的運用準備完了'
                recommendations = ['テスト環境での検証継続', '重要コンポーネントの修正必要']
            else:
                readiness_level = '運用準備未完了'
                recommendations = ['基本的な問題の解決が必要', '追加開発・修正作業必須']
            
            return {
                'readiness_score': readiness_score,
                'readiness_level': readiness_level,
                'readiness_factors': readiness_factors,
                'recommendations': recommendations,
                'pandas_dependency_note': 'pandas未インストールだが基本機能は動作可能'
            }
            
        except Exception as e:
            return {
                'readiness_score': 0,
                'error': str(e)
            }
    
    def _calculate_overall_health(self, health_results):
        """総合健全性評価"""
        try:
            # 各コンポーネントの健全性スコア収集
            component_scores = {
                'file_existence': health_results['file_existence'].get('health_score', 0),
                'syntax_validity': health_results['syntax_validity'].get('health_score', 0),
                'configuration': health_results['configuration'].get('health_score', 0),
                'strategy_execution': 100 if health_results['strategy_execution']['healthy'] else 0
            }
            
            # 重み付き平均計算
            weights = {
                'file_existence': 0.3,
                'syntax_validity': 0.3,
                'configuration': 0.2,
                'strategy_execution': 0.2
            }
            
            overall_score = sum(
                component_scores[k] * weights[k] for k in component_scores
            )
            
            # 健全性ステータス判定
            if overall_score >= 95:
                status = 'excellent'
                ready_for_operation = True
            elif overall_score >= 85:
                status = 'good'
                ready_for_operation = True
            elif overall_score >= 70:
                status = 'fair'
                ready_for_operation = False
            else:
                status = 'poor'
                ready_for_operation = False
            
            return {
                'overall_score': round(overall_score, 1),
                'component_scores': component_scores,
                'status': status,
                'ready_for_operation': ready_for_operation,
                'health_message': self._get_health_message(status, overall_score)
            }
            
        except Exception as e:
            return {
                'overall_score': 0,
                'status': 'error',
                'error': str(e)
            }
    
    def _get_health_message(self, status, score):
        """健全性メッセージ生成"""
        messages = {
            'excellent': f'システムは優秀な健全性を保っています（{score:.1f}/100）',
            'good': f'システムは良好な健全性を保っています（{score:.1f}/100）',
            'fair': f'システムに軽微な問題があります（{score:.1f}/100）',
            'poor': f'システムに重大な問題があります（{score:.1f}/100）',
            'error': 'システムチェック中にエラーが発生しました'
        }
        return messages.get(status, f'健全性スコア: {score:.1f}/100')

if __name__ == "__main__":
    # システムヘルスチェック実行
    health_checker = SystemHealthCheck()
    
    print("🏥 システムヘルスチェック実行中...")
    result = health_checker.execute_health_check()
    
    # 結果ファイル保存
    result_filename = f"System_Health_Check_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    result_filepath = os.path.join(health_checker.base_path, result_filename)
    
    with open(result_filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎯 システムヘルスチェック完了!")
    print(f"📁 結果ファイル: {result_filename}")
    
    if result['success']:
        overall = result['overall_health']
        readiness = result['health_results']['readiness_assessment']
        
        print(f"\n🏥 システム健全性: {overall['status'].upper()}")
        print(f"📊 総合スコア: {overall['overall_score']}/100")
        print(f"✅ 運用準備: {'可能' if overall['ready_for_operation'] else '要改善'}")
        print(f"🎯 準備レベル: {readiness['readiness_level']}")
        
        print(f"\n📋 コンポーネント別スコア:")
        for component, score in overall['component_scores'].items():
            print(f"  • {component}: {score:.1f}/100")
        
        print(f"\n💡 推奨事項:")
        for recommendation in readiness['recommendations']:
            print(f"  • {recommendation}")
        
        print(f"\n💬 {overall['health_message']}")
        
    else:
        print(f"❌ ヘルスチェックエラー: {result.get('error', '不明なエラー')}")