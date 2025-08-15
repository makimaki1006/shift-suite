"""
本格運用システム起動スクリプト
フル機能版シフト分析システムの統合起動
"""

import sys
import os
import datetime
import subprocess
import threading
import time
from typing import Dict, List, Any

class ProductionSystemManager:
    """本格運用システム管理クラス"""
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.startup_time = datetime.datetime.now()
        
        # システム構成
        self.system_components = {
            'main_dashboard': {
                'file': 'dash_app.py',
                'port': 8050,
                'description': 'メインダッシュボード',
                'priority': 1
            },
            'ai_ml_dashboard': {
                'file': 'dash_app_ai_ml_enhanced.py',
                'port': 8051,
                'description': 'AI/ML統合ダッシュボード',
                'priority': 2
            },
            'api_server': {
                'file': 'app.py',
                'port': 5000,
                'description': 'APIサーバー',
                'priority': 3
            }
        }
        
        # 運用設定
        self.production_config = {
            'host': '0.0.0.0',  # 全インターフェースでリッスン
            'debug': False,     # 本格運用ではFalse
            'threaded': True,   # マルチスレッド対応
            'auto_reload': False,  # 本格運用では無効
            'log_level': 'INFO'
        }
        
        self.running_processes = {}
        self.system_status = {}
    
    def check_system_readiness(self):
        """システム運用準備確認"""
        
        print("🔍 システム運用準備確認中...")
        
        readiness_checks = {
            'dependency_check': self._check_dependencies(),
            'file_integrity_check': self._check_file_integrity(),
            'port_availability_check': self._check_port_availability(),
            'configuration_check': self._check_configuration()
        }
        
        all_ready = all(readiness_checks.values())
        
        print("\n📊 運用準備チェック結果:")
        for check_name, status in readiness_checks.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {check_name}: {'OK' if status else 'NG'}")
        
        if all_ready:
            print("\n🌟 システム運用準備完了!")
            return True
        else:
            print("\n🔧 運用準備に課題があります")
            return False
    
    def _check_dependencies(self):
        """依存関係確認"""
        
        required_packages = ['dash', 'plotly', 'pandas', 'numpy']
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                print(f"  ⚠️ 必須パッケージ不足: {package}")
                return False
        
        return True
    
    def _check_file_integrity(self):
        """ファイル整合性確認"""
        
        for component_name, component_info in self.system_components.items():
            file_path = os.path.join(self.base_path, component_info['file'])
            if not os.path.exists(file_path):
                print(f"  ⚠️ 必須ファイル不足: {component_info['file']}")
                return False
        
        return True
    
    def _check_port_availability(self):
        """ポート利用可能性確認"""
        
        import socket
        
        for component_name, component_info in self.system_components.items():
            port = component_info['port']
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                result = s.connect_ex(('localhost', port))
                if result == 0:
                    print(f"  ⚠️ ポート{port}が既に使用中")
                    return False
        
        return True
    
    def _check_configuration(self):
        """設定確認"""
        
        # 環境変数確認
        env_vars = ['FLASK_ENV', 'DASH_ENV']
        for env_var in env_vars:
            if env_var in os.environ:
                if os.environ[env_var] == 'development':
                    print(f"  ⚠️ {env_var}が開発モードです")
        
        return True
    
    def start_system_components(self):
        """システムコンポーネント起動"""
        
        print("\n🚀 システムコンポーネント起動中...")
        
        # 優先順位順に起動
        sorted_components = sorted(
            self.system_components.items(),
            key=lambda x: x[1]['priority']
        )
        
        for component_name, component_info in sorted_components:
            success = self._start_component(component_name, component_info)
            self.system_status[component_name] = success
            
            if success:
                print(f"  ✅ {component_info['description']}: 起動成功 (Port {component_info['port']})")
            else:
                print(f"  ❌ {component_info['description']}: 起動失敗")
            
            # 起動間隔
            time.sleep(2)
        
        return all(self.system_status.values())
    
    def _start_component(self, component_name, component_info):
        """個別コンポーネント起動"""
        
        try:
            file_path = os.path.join(self.base_path, component_info['file'])
            
            if not os.path.exists(file_path):
                return False
            
            # Pythonプロセスとして起動
            process = subprocess.Popen([
                sys.executable, file_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.running_processes[component_name] = process
            
            # 起動確認（簡易）
            time.sleep(3)
            if process.poll() is None:  # プロセスが生きている
                return True
            else:
                return False
                
        except Exception as e:
            print(f"    エラー: {e}")
            return False
    
    def monitor_system_health(self):
        """システムヘルス監視"""
        
        print("\n💓 システムヘルス監視開始...")
        
        def health_check_loop():
            while True:
                try:
                    health_status = {}
                    
                    for component_name, process in self.running_processes.items():
                        if process and process.poll() is None:
                            health_status[component_name] = 'RUNNING'
                        else:
                            health_status[component_name] = 'STOPPED'
                    
                    # ヘルス状況表示（5分間隔）
                    current_time = datetime.datetime.now().strftime('%H:%M:%S')
                    running_count = sum(1 for status in health_status.values() if status == 'RUNNING')
                    total_count = len(health_status)
                    
                    print(f"[{current_time}] システム状況: {running_count}/{total_count} コンポーネント稼働中")
                    
                    # 異常検知
                    if running_count < total_count:
                        print("⚠️ 一部コンポーネントが停止しています")
                        for comp_name, status in health_status.items():
                            if status == 'STOPPED':
                                print(f"  - {comp_name}: 停止")
                    
                    time.sleep(300)  # 5分間隔
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"監視エラー: {e}")
                    time.sleep(60)
        
        # 監視スレッド開始
        health_thread = threading.Thread(target=health_check_loop, daemon=True)
        health_thread.start()
    
    def display_access_information(self):
        """アクセス情報表示"""
        
        print("\n🌐 システムアクセス情報:")
        print("=" * 50)
        
        for component_name, component_info in self.system_components.items():
            if self.system_status.get(component_name, False):
                port = component_info['port']
                description = component_info['description']
                
                print(f"📊 {description}")
                print(f"   URL: http://localhost:{port}")
                print(f"   外部アクセス: http://[サーバーIP]:{port}")
                print()
        
        print("💡 使用方法:")
        print("  1. ブラウザで上記URLにアクセス")
        print("  2. メインダッシュボードから機能選択")
        print("  3. AI/ML機能は専用ダッシュボードで利用")
        print()
        print("🛠️ 管理:")
        print("  - システム停止: Ctrl+C")
        print("  - ログ確認: 各コンポーネントのログ出力を確認")
        print("  - トラブルシューティング: README.md参照")
    
    def graceful_shutdown(self):
        """グレースフルシャットダウン"""
        
        print("\n🛑 システムシャットダウン中...")
        
        for component_name, process in self.running_processes.items():
            if process and process.poll() is None:
                print(f"  停止中: {component_name}")
                process.terminate()
                
                # 5秒待って強制終了
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    print(f"  強制終了: {component_name}")
        
        print("✅ システムシャットダウン完了")
    
    def generate_startup_report(self):
        """起動レポート生成"""
        
        report = {
            'startup_time': self.startup_time.isoformat(),
            'system_components': self.system_components,
            'component_status': self.system_status,
            'production_config': self.production_config,
            'total_components': len(self.system_components),
            'running_components': sum(self.system_status.values()),
            'success_rate': sum(self.system_status.values()) / len(self.system_status) * 100
        }
        
        report_filename = f"production_startup_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        import json
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📋 起動レポート保存: {report_filename}")
        
        return report

def main():
    """メイン起動プロセス"""
    
    print("🚀 シフト分析システム 本格運用開始...")
    print("=" * 60)
    
    manager = ProductionSystemManager()
    
    try:
        # Step 1: システム運用準備確認
        if not manager.check_system_readiness():
            print("\n❌ システム運用準備が完了していません")
            print("💡 先に install_full_dependencies.bat と verify_installation.py を実行してください")
            return False
        
        # Step 2: システムコンポーネント起動
        if not manager.start_system_components():
            print("\n❌ システムコンポーネント起動に失敗しました")
            return False
        
        # Step 3: アクセス情報表示
        manager.display_access_information()
        
        # Step 4: 起動レポート生成
        manager.generate_startup_report()
        
        # Step 5: システムヘルス監視開始
        manager.monitor_system_health()
        
        print("\n🌟 システム本格運用開始!")
        print("📱 ブラウザでダッシュボードにアクセスしてください")
        print("⌨️ 停止する場合は Ctrl+C を押してください")
        
        # メインループ
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            manager.graceful_shutdown()
        
        return True
        
    except Exception as e:
        print(f"\n❌ システム起動エラー: {e}")
        manager.graceful_shutdown()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)