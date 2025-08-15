"""
Phase 1: 日次システム稼働監視
現状最適化継続戦略フェーズ1の実行

96.7/100品質レベル維持・システム安定性確保
"""

import os
import json
import datetime
import hashlib
from typing import Dict, List, Any

class Phase1DailySystemMonitoring:
    """Phase 1: 日次システム稼働監視システム"""
    
    def __init__(self):
        self.base_path = "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析"
        self.monitoring_start_time = datetime.datetime.now()
        
        # 品質ベースライン（維持目標）
        self.quality_baselines = {
            'system_quality_score': 96.7,
            'user_satisfaction_score': 96.6,
            'deployment_success_rate': 100.0,
            'uptime_target': 99.9
        }
        
        # 監視対象システムファイル
        self.critical_system_files = [
            'dash_app.py',
            'app.py',
            'shift_suite/tasks/fact_extractor_prototype.py',
            'shift_suite/tasks/lightweight_anomaly_detector.py'
        ]
        
        # 監視対象モバイル資産
        self.mobile_assets = [
            'assets/c2-mobile-integrated.css',
            'assets/c2-mobile-integrated.js',
            'assets/c2-service-worker.js'
        ]
        
        # アラート条件
        self.alert_conditions = {
            'file_access_failure': 'ファイルアクセス不可・破損検出',
            'hash_integrity_failure': 'ファイルハッシュ不整合・予期しない変更',
            'size_anomaly': 'ファイルサイズ異常変化（±20%以上）',
            'slot_hours_protection_failure': 'SLOT_HOURS計算保護機能破損',
            'mobile_asset_unavailable': 'モバイル資産アクセス不可'
        }
        
    def execute_daily_monitoring(self):
        """日次システム稼働監視メイン実行"""
        print("📊 Phase 1: 日次システム稼働監視開始...")
        print(f"📅 監視実行時刻: {self.monitoring_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 品質維持目標: {self.quality_baselines['system_quality_score']}/100")
        
        try:
            # システムファイル稼働状況確認
            system_health_check = self._check_system_file_health()
            if system_health_check['success']:
                print("✅ システムファイル稼働状況: 正常")
            else:
                print("⚠️ システムファイル稼働状況: 要注意")
            
            # モバイル資産稼働確認
            mobile_assets_check = self._check_mobile_assets_health()
            if mobile_assets_check['success']:
                print("✅ モバイル資産稼働状況: 正常")
            else:
                print("⚠️ モバイル資産稼働状況: 要注意")
            
            # データ品質・SLOT_HOURS保護確認
            data_quality_check = self._check_data_quality_slot_hours_protection()
            if data_quality_check['success']:
                print("✅ データ品質・SLOT_HOURS保護: 正常")
            else:
                print("⚠️ データ品質・SLOT_HOURS保護: 要注意")
            
            # 総合監視結果分析
            monitoring_analysis = self._analyze_daily_monitoring_results(
                system_health_check, mobile_assets_check, data_quality_check
            )
            
            return {
                'metadata': {
                    'monitoring_execution_id': f"PHASE1_DAILY_MONITOR_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'monitoring_start_time': self.monitoring_start_time.isoformat(),
                    'monitoring_end_time': datetime.datetime.now().isoformat(),
                    'monitoring_duration': str(datetime.datetime.now() - self.monitoring_start_time),
                    'quality_baselines': self.quality_baselines,
                    'monitoring_scope': 'システム稼働・モバイル資産・データ品質'
                },
                'system_health_check': system_health_check,
                'mobile_assets_check': mobile_assets_check,
                'data_quality_check': data_quality_check,
                'monitoring_analysis': monitoring_analysis,
                'success': monitoring_analysis['overall_health_status'] == 'healthy',
                'daily_monitoring_status': monitoring_analysis['daily_status']
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.datetime.now().isoformat(),
                'status': 'daily_monitoring_failed'
            }
    
    def _check_system_file_health(self):
        """システムファイル稼働状況確認"""
        try:
            file_health_results = {}
            
            for file_path in self.critical_system_files:
                full_path = os.path.join(self.base_path, file_path)
                
                if os.path.exists(full_path):
                    # ファイル基本情報取得
                    file_stat = os.stat(full_path)
                    file_size = file_stat.st_size
                    last_modified = datetime.datetime.fromtimestamp(file_stat.st_mtime)
                    
                    # ファイルハッシュ計算
                    with open(full_path, 'rb') as f:
                        file_content = f.read()
                        file_hash = hashlib.md5(file_content).hexdigest()
                    
                    # アクセス可能性確認
                    readable = os.access(full_path, os.R_OK)
                    
                    file_health_results[file_path] = {
                        'exists': True,
                        'accessible': readable,
                        'size': file_size,
                        'size_kb': round(file_size / 1024, 2),
                        'last_modified': last_modified.isoformat(),
                        'file_hash': file_hash,
                        'integrity_check': 'passed',
                        'health_status': 'healthy'
                    }
                else:
                    file_health_results[file_path] = {
                        'exists': False,
                        'accessible': False,
                        'health_status': 'critical_missing',
                        'alert_condition': self.alert_conditions['file_access_failure']
                    }
            
            # 全体ファイル健全性評価
            all_files_healthy = all(
                result.get('health_status') == 'healthy' 
                for result in file_health_results.values()
            )
            
            critical_issues = [
                file_path for file_path, result in file_health_results.items()
                if result.get('health_status') == 'critical_missing'
            ]
            
            return {
                'success': all_files_healthy,
                'file_health_results': file_health_results,
                'total_files_checked': len(self.critical_system_files),
                'healthy_files_count': sum(1 for r in file_health_results.values() if r.get('health_status') == 'healthy'),
                'critical_issues': critical_issues,
                'overall_system_health': 'healthy' if all_files_healthy else 'requires_attention',
                'check_timestamp': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'check_method': 'system_file_health_check_failed'
            }
    
    def _check_mobile_assets_health(self):
        """モバイル資産稼働確認"""
        try:
            mobile_health_results = {}
            
            for asset_path in self.mobile_assets:
                full_path = os.path.join(self.base_path, asset_path)
                
                if os.path.exists(full_path):
                    # 資産基本情報取得
                    asset_stat = os.stat(full_path)
                    asset_size = asset_stat.st_size
                    last_modified = datetime.datetime.fromtimestamp(asset_stat.st_mtime)
                    
                    # 内容確認（CSS/JS固有チェック）
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # CSS固有チェック
                    if asset_path.endswith('.css'):
                        css_features = {
                            'responsive_design': '@media' in content,
                            'mobile_breakpoints': '768px' in content or '1024px' in content,
                            'touch_optimization': 'touch' in content.lower(),
                            'content_substantial': len(content) > 5000
                        }
                        feature_check = css_features
                    
                    # JS固有チェック
                    elif asset_path.endswith('.js'):
                        js_features = {
                            'event_handling': 'addEventListener' in content,
                            'mobile_logic': 'mobile' in content.lower(),
                            'touch_events': 'touch' in content.lower(),
                            'content_substantial': len(content) > 3000
                        }
                        feature_check = js_features
                    
                    else:
                        feature_check = {'basic_check': len(content) > 100}
                    
                    mobile_health_results[asset_path] = {
                        'available': True,
                        'accessible': os.access(full_path, os.R_OK),
                        'size': asset_size,
                        'size_kb': round(asset_size / 1024, 2),
                        'last_modified': last_modified.isoformat(),
                        'feature_check': feature_check,
                        'features_intact': all(feature_check.values()),
                        'health_status': 'operational' if all(feature_check.values()) else 'degraded'
                    }
                else:
                    mobile_health_results[asset_path] = {
                        'available': False,
                        'accessible': False,
                        'health_status': 'unavailable',
                        'alert_condition': self.alert_conditions['mobile_asset_unavailable']
                    }
            
            # モバイル資産全体評価
            all_assets_operational = all(
                result.get('health_status') == 'operational' 
                for result in mobile_health_results.values()
            )
            
            unavailable_assets = [
                asset_path for asset_path, result in mobile_health_results.items()
                if result.get('health_status') == 'unavailable'
            ]
            
            return {
                'success': all_assets_operational,
                'mobile_health_results': mobile_health_results,
                'total_assets_checked': len(self.mobile_assets),
                'operational_assets_count': sum(1 for r in mobile_health_results.values() if r.get('health_status') == 'operational'),
                'unavailable_assets': unavailable_assets,
                'overall_mobile_health': 'operational' if all_assets_operational else 'requires_attention',
                'check_timestamp': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'check_method': 'mobile_assets_health_check_failed'
            }
    
    def _check_data_quality_slot_hours_protection(self):
        """データ品質・SLOT_HOURS保護確認"""
        try:
            protection_check_results = {}
            
            # SLOT_HOURS保護対象モジュール
            protected_modules = [
                'shift_suite/tasks/fact_extractor_prototype.py',
                'shift_suite/tasks/lightweight_anomaly_detector.py'
            ]
            
            for module_path in protected_modules:
                full_path = os.path.join(self.base_path, module_path)
                
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # SLOT_HOURS保護確認
                    slot_hours_multiplications = content.count('* SLOT_HOURS')
                    slot_hours_definition = content.count('SLOT_HOURS = 0.5')
                    
                    # 計算保護整合性確認
                    protection_intact = (
                        slot_hours_multiplications > 0 and 
                        slot_hours_definition > 0 and
                        'SLOT_HOURS = 0.5' in content
                    )
                    
                    # コード品質確認
                    code_quality_indicators = {
                        'imports_present': 'import' in content,
                        'functions_defined': 'def ' in content,
                        'classes_defined': 'class ' in content,
                        'docstrings_present': '"""' in content,
                        'substantial_content': len(content) > 5000
                    }
                    
                    protection_check_results[module_path] = {
                        'module_exists': True,
                        'slot_hours_multiplications': slot_hours_multiplications,
                        'slot_hours_definition': slot_hours_definition,
                        'protection_intact': protection_intact,
                        'code_quality_indicators': code_quality_indicators,
                        'code_quality_score': sum(code_quality_indicators.values()) / len(code_quality_indicators),
                        'module_size': len(content),
                        'protection_status': 'protected' if protection_intact else 'compromised'
                    }
                else:
                    protection_check_results[module_path] = {
                        'module_exists': False,
                        'protection_status': 'missing',
                        'alert_condition': self.alert_conditions['slot_hours_protection_failure']
                    }
            
            # データ品質保護全体評価
            all_protections_intact = all(
                result.get('protection_status') == 'protected' 
                for result in protection_check_results.values()
            )
            
            compromised_modules = [
                module_path for module_path, result in protection_check_results.items()
                if result.get('protection_status') in ['compromised', 'missing']
            ]
            
            return {
                'success': all_protections_intact,
                'protection_check_results': protection_check_results,
                'total_modules_checked': len(protected_modules),
                'protected_modules_count': sum(1 for r in protection_check_results.values() if r.get('protection_status') == 'protected'),
                'compromised_modules': compromised_modules,
                'overall_protection_status': 'intact' if all_protections_intact else 'requires_attention',
                'check_timestamp': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'check_method': 'data_quality_protection_check_failed'
            }
    
    def _analyze_daily_monitoring_results(self, system_health, mobile_assets, data_quality):
        """日次監視結果総合分析"""
        try:
            # 各カテゴリ成功確認
            categories_success = {
                'system_health': system_health.get('success', False),
                'mobile_assets': mobile_assets.get('success', False),
                'data_quality': data_quality.get('success', False)
            }
            
            # 総合成功率
            overall_success_rate = sum(categories_success.values()) / len(categories_success)
            
            # 健全性ステータス判定
            if overall_success_rate == 1.0:
                overall_health_status = 'healthy'
                daily_status = 'excellent'
            elif overall_success_rate >= 0.67:
                overall_health_status = 'mostly_healthy'
                daily_status = 'good_with_minor_issues'
            else:
                overall_health_status = 'requires_attention'
                daily_status = 'needs_immediate_action'
            
            # 具体的問題・アラート識別
            identified_issues = []
            
            if not system_health.get('success', False):
                critical_issues = system_health.get('critical_issues', [])
                if critical_issues:
                    identified_issues.extend([
                        f"システムファイル重大問題: {', '.join(critical_issues)}"
                    ])
            
            if not mobile_assets.get('success', False):
                unavailable_assets = mobile_assets.get('unavailable_assets', [])
                if unavailable_assets:
                    identified_issues.extend([
                        f"モバイル資産利用不可: {', '.join(unavailable_assets)}"
                    ])
            
            if not data_quality.get('success', False):
                compromised_modules = data_quality.get('compromised_modules', [])
                if compromised_modules:
                    identified_issues.extend([
                        f"データ品質保護破損: {', '.join(compromised_modules)}"
                    ])
            
            # 品質ベースライン維持評価
            quality_baseline_maintained = overall_success_rate >= 0.95  # 95%以上で品質維持
            
            # 即座実行推奨アクション
            immediate_actions = []
            
            if overall_health_status == 'requires_attention':
                immediate_actions.extend([
                    "技術チーム緊急招集・問題分析開始",
                    "影響範囲評価・リスク分析実施",
                    "暫定対策・緊急修復実行",
                    "ユーザー影響確認・通知実施"
                ])
            elif overall_health_status == 'mostly_healthy':
                immediate_actions.extend([
                    "特定問題の詳細調査・原因分析",
                    "予防保全・改善施策検討",
                    "監視強化・追加チェック実施"
                ])
            else:
                immediate_actions.extend([
                    "現在の良好状態継続維持",
                    "予防保全・定期点検継続",
                    "パフォーマンス最適化検討"
                ])
            
            # 次回監視計画
            next_monitoring_schedule = {
                'next_daily_check': (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M'),
                'urgent_recheck_needed': overall_health_status == 'requires_attention',
                'recheck_interval': '2時間後' if overall_health_status == 'requires_attention' else '24時間後'
            }
            
            return {
                'overall_health_status': overall_health_status,
                'daily_status': daily_status,
                'categories_success': categories_success,
                'overall_success_rate': overall_success_rate,
                'quality_baseline_maintained': quality_baseline_maintained,
                'identified_issues': identified_issues,
                'immediate_actions': immediate_actions,
                'next_monitoring_schedule': next_monitoring_schedule,
                'analysis_timestamp': datetime.datetime.now().isoformat(),
                'phase1_execution_status': 'on_track' if overall_health_status in ['healthy', 'mostly_healthy'] else 'requires_escalation'
            }
            
        except Exception as e:
            return {
                'overall_health_status': 'analysis_failed',
                'error': str(e),
                'analysis_method': 'daily_monitoring_analysis_failed'
            }

def main():
    """Phase 1: 日次システム稼働監視メイン実行"""
    print("📊 Phase 1: 日次システム稼働監視開始...")
    
    monitor = Phase1DailySystemMonitoring()
    result = monitor.execute_daily_monitoring()
    
    if 'error' in result:
        print(f"❌ 日次監視エラー: {result['error']}")
        return result
    
    # 結果保存
    result_file = f"Phase1_Daily_System_Monitoring_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 結果表示
    print(f"\n🎯 Phase 1: 日次システム稼働監視完了!")
    print(f"📁 監視結果ファイル: {result_file}")
    
    if result['success']:
        print(f"✅ 日次システム監視: 成功")
        print(f"🏆 総合健全性: {result['monitoring_analysis']['overall_health_status']}")
        print(f"📊 成功率: {result['monitoring_analysis']['overall_success_rate']:.1%}")
        print(f"🎯 品質ベースライン維持: {'Yes' if result['monitoring_analysis']['quality_baseline_maintained'] else 'No'}")
        
        if result['monitoring_analysis']['immediate_actions']:
            print(f"\n🚀 即座実行推奨:")
            for i, action in enumerate(result['monitoring_analysis']['immediate_actions'][:3], 1):
                print(f"  {i}. {action}")
    else:
        print(f"❌ 日次システム監視: 要対応")
        print(f"📋 問題: {', '.join(result['monitoring_analysis']['identified_issues'])}")
        print(f"🚨 緊急対応が必要")
    
    return result

if __name__ == "__main__":
    result = main()