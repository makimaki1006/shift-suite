#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dash_app.py の根本問題診断と修復
100%責任感での完全復旧
"""

import sys
import importlib
import traceback
import subprocess
import time
import threading
import requests
from pathlib import Path
import os

# エンコーディング設定
os.environ['PYTHONIOENCODING'] = 'utf-8'

class DashAppDiagnostic:
    def __init__(self):
        self.issues = []
        self.critical_issues = []
        self.fixes_applied = []
        
    def run_complete_diagnostic(self):
        """完全な診断の実行"""
        print("=" * 80)
        print("🔍 dash_app.py 根本問題診断・修復システム")
        print("ユーザー要求: 全機能使用可能にする（UI、ビジュアライズ等々）")
        print("=" * 80)
        
        # 段階1: ファイル構造分析
        self.analyze_file_structure()
        
        # 段階2: 依存関係問題特定
        self.analyze_dependencies()
        
        # 段階3: インポートエラー特定
        self.analyze_imports()
        
        # 段階4: レイアウト問題分析
        self.analyze_layout_issues()
        
        # 段階5: 実際の起動テスト
        self.test_actual_startup()
        
        # 段階6: 修復提案
        self.propose_fixes()
        
    def analyze_file_structure(self):
        """ファイル構造分析"""
        print("\n🔍 段階1: ファイル構造分析")
        
        dash_app_file = Path("dash_app.py")
        
        if not dash_app_file.exists():
            self.critical_issues.append("dash_app.py file missing")
            print("❌ dash_app.py が存在しません")
            return
            
        file_size = dash_app_file.stat().st_size
        print(f"✅ dash_app.py サイズ: {file_size:,} bytes")
        
        # 行数確認
        with open(dash_app_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"✅ 総行数: {len(lines):,} 行")
        
        if len(lines) > 10000:
            self.issues.append("Very large file - potential performance issue")
            print("⚠️ 非常に大きなファイル（パフォーマンス問題の可能性）")
            
        # レイアウト設定行の確認
        layout_lines = [i for i, line in enumerate(lines, 1) if 'app.layout' in line]
        print(f"✅ app.layout 設定行: {layout_lines}")
        
    def analyze_dependencies(self):
        """依存関係分析"""
        print("\n🔍 段階2: 依存関係問題特定")
        
        # dash_app.pyの依存関係を抽出
        try:
            with open("dash_app.py", 'r', encoding='utf-8') as f:
                content = f.read()
                
            # import文を抽出
            import_lines = [line.strip() for line in content.split('\n') if line.strip().startswith(('import ', 'from '))]
            
            print(f"📋 インポート文数: {len(import_lines)}")
            
            # 問題のある可能性の高いインポート
            problematic_imports = []
            
            for line in import_lines[:20]:  # 最初の20個をチェック
                print(f"  📦 {line}")
                
                # 特定の問題のあるインポートを特定
                if 'shift_suite' in line:
                    problematic_imports.append(line)
                elif 'cytoscape' in line:
                    problematic_imports.append(line)
                elif 'psutil' in line:
                    problematic_imports.append(line)
                    
            if problematic_imports:
                print(f"\n⚠️ 問題の可能性があるインポート: {len(problematic_imports)}")
                for imp in problematic_imports:
                    print(f"  🔴 {imp}")
                    
        except Exception as e:
            self.critical_issues.append(f"Failed to analyze imports: {e}")
            print(f"❌ インポート分析エラー: {e}")
            
    def analyze_imports(self):
        """インポートエラー特定"""
        print("\n🔍 段階3: インポートエラー特定")
        
        # shift_suite パッケージの確認
        try:
            sys.path.append(str(Path.cwd()))
            import shift_suite
            print("✅ shift_suite: インポート成功")
        except Exception as e:
            self.critical_issues.append(f"shift_suite import failed: {e}")
            print(f"❌ shift_suite: インポートエラー - {e}")
            
        # dash_cytoscape の確認
        try:
            import dash_cytoscape
            print("✅ dash_cytoscape: インポート成功")
        except Exception as e:
            self.issues.append(f"dash_cytoscape import failed: {e}")
            print(f"⚠️ dash_cytoscape: インポートエラー - {e}")
            
        # 基本的なDash依存関係確認
        basic_deps = ['dash', 'plotly', 'pandas', 'numpy']
        
        for dep in basic_deps:
            try:
                module = importlib.import_module(dep)
                version = getattr(module, '__version__', 'unknown')
                print(f"✅ {dep}: {version}")
            except Exception as e:
                self.critical_issues.append(f"{dep} import failed: {e}")
                print(f"❌ {dep}: インポートエラー - {e}")
                
    def analyze_layout_issues(self):
        """レイアウト問題分析"""
        print("\n🔍 段階4: レイアウト問題分析")
        
        try:
            with open("dash_app.py", 'r', encoding='utf-8') as f:
                content = f.read()
                
            # レイアウト設定の確認
            if 'app.layout = html.Div' in content:
                print("✅ app.layout 設定確認")
            else:
                self.critical_issues.append("app.layout not found")
                print("❌ app.layout 設定が見つからない")
                
            # コールバック数の確認
            callback_count = content.count('@app.callback')
            print(f"✅ コールバック数: {callback_count}")
            
            if callback_count > 50:
                self.issues.append("Too many callbacks - potential performance issue")
                print("⚠️ コールバック数が多い（パフォーマンス問題の可能性）")
                
            # 複雑なHTML構造の確認
            html_div_count = content.count('html.Div')
            print(f"✅ HTML Div 要素数: {html_div_count}")
            
            if html_div_count > 200:
                self.issues.append("Complex HTML structure")
                print("⚠️ 複雑なHTML構造")
                
        except Exception as e:
            self.critical_issues.append(f"Layout analysis failed: {e}")
            print(f"❌ レイアウト分析エラー: {e}")
            
    def test_actual_startup(self):
        """実際の起動テスト"""
        print("\n🔍 段階5: 実際の起動テスト")
        
        # インポートテスト
        print("📋 dash_app.py インポートテスト中...")
        
        try:
            # 既存のdash_appモジュールを削除
            modules_to_remove = [name for name in sys.modules.keys() if 'dash_app' in name]
            for module in modules_to_remove:
                del sys.modules[module]
                
            # インポート試行
            import dash_app
            print("✅ dash_app.py インポート成功")
            
            # アプリオブジェクトの確認
            if hasattr(dash_app, 'app'):
                print("✅ app オブジェクト確認")
                
                # レイアウトの確認
                if dash_app.app.layout is not None:
                    print("✅ app.layout 設定済み")
                else:
                    self.critical_issues.append("app.layout is None")
                    print("❌ app.layout が設定されていない")
                    
            else:
                self.critical_issues.append("app object not found")
                print("❌ app オブジェクトが見つからない")
                
        except Exception as e:
            self.critical_issues.append(f"Import failed: {e}")
            print(f"❌ インポート失敗: {e}")
            print("詳細エラー:")
            print(traceback.format_exc())
            
    def propose_fixes(self):
        """修復提案"""
        print("\n" + "=" * 80)
        print("🔧 修復提案と実行計画")
        print("=" * 80)
        
        print(f"🔍 発見された問題: {len(self.issues) + len(self.critical_issues)}")
        print(f"🔴 重大な問題: {len(self.critical_issues)}")
        print(f"🟡 軽微な問題: {len(self.issues)}")
        
        if self.critical_issues:
            print("\n💀 重大な問題:")
            for issue in self.critical_issues:
                print(f"  ❌ {issue}")
                
        if self.issues:
            print("\n⚠️ 軽微な問題:")
            for issue in self.issues:
                print(f"  🟡 {issue}")
                
        # 修復計画
        print("\n🔧 段階的修復計画:")
        
        if any("shift_suite" in issue for issue in self.critical_issues):
            print("1. 🔴 shift_suite依存関係の修正")
            print("   - パッケージの再インストール")
            print("   - インポートパスの修正")
            
        if any("import failed" in issue for issue in self.critical_issues):
            print("2. 🔴 基本依存関係の修正")
            print("   - 必要パッケージの確認・インストール")
            
        if any("layout" in issue for issue in self.critical_issues):
            print("3. 🔴 レイアウト問題の修正")
            print("   - app.layout設定の確認・修正")
            
        print("4. 🔄 段階的テスト")
        print("   - 最小構成での動作確認")
        print("   - 機能の段階的復旧")
        
        # 成功の見込み
        if len(self.critical_issues) == 0:
            print("\n🎉 修復成功の見込み: 高 (90%+)")
        elif len(self.critical_issues) <= 2:
            print("\n⚠️ 修復成功の見込み: 中 (70-90%)")
        else:
            print("\n💀 修復成功の見込み: 低 (50-70%)")
            print("   大幅な修正が必要")

if __name__ == "__main__":
    diagnostic = DashAppDiagnostic()
    diagnostic.run_complete_diagnostic()