"""
依存関係インストール・検証統合スクリプト
"""

import subprocess
import sys
import os
import datetime
import json
from typing import Dict, List, Any

class DependencyInstaller:
    """依存関係インストーラークラス"""
    
    def __init__(self):
        self.required_packages = {
            'core_packages': {
                'dash': '2.14.1',
                'plotly': '5.17.0', 
                'pandas': '2.1.1',
                'numpy': '1.24.3'
            },
            'analysis_packages': {
                'scipy': '1.11.3',
                'scikit-learn': '1.3.0',
                'openpyxl': '3.1.2',
                'xlsxwriter': '3.1.9'
            },
            'ui_packages': {
                'dash-bootstrap-components': '1.5.0',
                'kaleido': '0.2.1'
            },
            'development_packages': {
                'pytest': '7.4.2',
                'flask': '2.3.3'
            }
        }
    
    def install_package(self, package_name, version=None):
        """個別パッケージインストール"""
        
        try:
            if version:
                package_spec = f"{package_name}=={version}"
            else:
                package_spec = package_name
            
            print(f"📦 インストール中: {package_spec}")
            
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', package_spec
            ], capture_output=True, text=True, check=True)
            
            print(f"  ✅ {package_name} インストール成功")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"  ❌ {package_name} インストール失敗: {e}")
            return False
        except Exception as e:
            print(f"  ⚠️ {package_name} 予期しないエラー: {e}")
            return False
    
    def install_all_packages(self):
        """全パッケージインストール"""
        
        print("🚀 依存関係インストール開始...")
        print(f"🐍 Python バージョン: {sys.version}")
        
        # pipアップグレード
        print("\n📦 pip アップグレード...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                         capture_output=True, check=True)
            print("  ✅ pip アップグレード成功")
        except:
            print("  ⚠️ pip アップグレード失敗（続行）")
        
        installation_results = {}
        total_packages = 0
        successful_packages = 0
        
        for category, packages in self.required_packages.items():
            print(f"\n📊 {category} インストール中...")
            category_results = {}
            
            for package_name, version in packages.items():
                total_packages += 1
                success = self.install_package(package_name, version)
                category_results[package_name] = success
                
                if success:
                    successful_packages += 1
            
            installation_results[category] = category_results
        
        # インストール結果サマリー
        success_rate = (successful_packages / total_packages) * 100
        print(f"\n📊 インストール結果: {successful_packages}/{total_packages} パッケージ ({success_rate:.1f}%)")
        
        return installation_results, success_rate >= 80
    
    def verify_installation(self):
        """インストール検証"""
        
        print("\n🔍 インストール検証中...")
        
        verification_results = {}
        
        # 重要パッケージの検証
        critical_packages = {
            'dash': 'Dashフレームワーク',
            'plotly': 'Plotly可視化',
            'pandas': 'データ処理',
            'numpy': '数値計算'
        }
        
        for package, description in critical_packages.items():
            try:
                if package == 'sklearn':
                    import sklearn
                    module = sklearn
                else:
                    module = __import__(package)
                
                version = getattr(module, '__version__', 'unknown')
                verification_results[package] = {
                    'installed': True,
                    'version': version,
                    'description': description
                }
                print(f"  ✅ {description}: {version}")
                
            except ImportError:
                verification_results[package] = {
                    'installed': False,
                    'description': description
                }
                print(f"  ❌ {description}: インストールされていません")
        
        return verification_results
    
    def create_simple_test(self):
        """簡単な動作テスト"""
        
        print("\n🧪 簡単な動作テスト実行中...")
        
        test_results = {}
        
        # Dashアプリ作成テスト
        try:
            import dash
            from dash import html
            
            app = dash.Dash(__name__)
            app.layout = html.Div("テストアプリ")
            
            test_results['dash_test'] = True
            print("  ✅ Dashアプリ作成: OK")
            
        except Exception as e:
            test_results['dash_test'] = False
            print(f"  ❌ Dashアプリ作成: {e}")
        
        # データ処理テスト
        try:
            import pandas as pd
            import numpy as np
            
            df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
            result = df.sum()
            
            test_results['data_processing_test'] = True
            print("  ✅ データ処理: OK")
            
        except Exception as e:
            test_results['data_processing_test'] = False
            print(f"  ❌ データ処理: {e}")
        
        # 可視化テスト
        try:
            import plotly.graph_objects as go
            
            fig = go.Figure(data=go.Bar(x=[1, 2, 3], y=[1, 3, 2]))
            
            test_results['visualization_test'] = True
            print("  ✅ 可視化: OK")
            
        except Exception as e:
            test_results['visualization_test'] = False
            print(f"  ❌ 可視化: {e}")
        
        return test_results
    
    def generate_report(self, installation_results, verification_results, test_results):
        """レポート生成"""
        
        report = {
            'timestamp': datetime.datetime.now().isoformat(),
            'python_version': sys.version,
            'installation_results': installation_results,
            'verification_results': verification_results,
            'test_results': test_results,
            'summary': {
                'installation_success': all(
                    all(results.values()) for results in installation_results.values()
                ),
                'verification_success': all(
                    result.get('installed', False) for result in verification_results.values()
                ),
                'test_success': all(test_results.values())
            }
        }
        
        report_filename = f"dependency_installation_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📋 レポート保存: {report_filename}")
        
        return report

def main():
    """メイン実行"""
    
    print("🚀 シフト分析システム 依存関係セットアップ開始...")
    print("=" * 60)
    
    installer = DependencyInstaller()
    
    try:
        # Step 1: パッケージインストール
        installation_results, install_success = installer.install_all_packages()
        
        # Step 2: インストール検証
        verification_results = installer.verify_installation()
        
        # Step 3: 動作テスト
        test_results = installer.create_simple_test()
        
        # Step 4: レポート生成
        report = installer.generate_report(installation_results, verification_results, test_results)
        
        # 結果表示
        print("\n" + "=" * 60)
        print("🎯 セットアップ完了!")
        
        if report['summary']['installation_success']:
            print("✅ パッケージインストール: 成功")
        else:
            print("❌ パッケージインストール: 一部失敗")
        
        if report['summary']['verification_success']:
            print("✅ インストール検証: 成功")
        else:
            print("❌ インストール検証: 一部失敗")
        
        if report['summary']['test_success']:
            print("✅ 動作テスト: 成功")
        else:
            print("❌ 動作テスト: 一部失敗")
        
        # 次のステップ案内
        if all(report['summary'].values()):
            print("\n🌟 すべてのセットアップが完了しました!")
            print("🚀 次のコマンドでシステムを起動してください:")
            print("  python start_production_system.py")
        else:
            print("\n🔧 一部のセットアップに問題があります")
            print("💡 以下を確認してください:")
            print("  1. Python環境の確認")
            print("  2. ネットワーク接続の確認")
            print("  3. 管理者権限での実行")
        
        return all(report['summary'].values())
        
    except Exception as e:
        print(f"\n❌ セットアップエラー: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)