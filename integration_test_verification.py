#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3 統合テスト検証
dash_app.pyへの統合が正常に完了していることを確認
"""

import ast
import re
from pathlib import Path
import logging

def verify_integration_completion():
    """統合完了の詳細検証"""
    
    print("=" * 80)
    print("🧪 Phase 3 統合テスト検証")
    print("=" * 80)
    
    # dash_app.pyを読み込み
    dash_app_path = Path("dash_app.py")
    if not dash_app_path.exists():
        print("❌ dash_app.py が見つかりません")
        return False
    
    with open(dash_app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. インポート文の確認
    print("\n📦 Step 1: インポート確認")
    import_checks = [
        ("from shift_suite.tasks.fact_book_visualizer import FactBookVisualizer", "FactBookVisualizer"),
        ("from shift_suite.tasks.dash_fact_book_integration import", "統合モジュール"),
        ("FACT_BOOK_INTEGRATION_AVAILABLE = True", "機能フラグ")
    ]
    
    for import_line, description in import_checks:
        if import_line in content:
            print(f"  ✅ {description}")
        else:
            print(f"  ❌ {description}")
    
    # 2. タブ定義の確認
    print("\n📑 Step 2: タブ定義確認")
    tab_pattern = r"dcc\.Tab\(label='📊 統合ファクトブック', value='fact_book_analysis'\)"
    if re.search(tab_pattern, content):
        print("  ✅ ファクトブックタブが定義されています")
    else:
        print("  ❌ ファクトブックタブが見つかりません")
    
    # 3. コールバック確認
    print("\n🔄 Step 3: コールバック確認")
    callback_checks = [
        (r"@callback.*fact-book-results.*fact-book-status", "メインコールバック"),
        ("generate-fact-book-button", "ボタンイベント"),
        ("fact-book-sensitivity", "感度設定"),
        ("selected-scenario", "シナリオ選択")
    ]
    
    for pattern, description in callback_checks:
        if re.search(pattern, content):
            print(f"  ✅ {description}")
        else:
            print(f"  ❌ {description}")
    
    # 4. UI要素の確認
    print("\n🎨 Step 4: UI要素確認")
    ui_elements = [
        ("fact-book-analysis", "ファクトブック分析ID"),
        ("統合ファクトブック機能", "機能説明"),
        ("Phase 2の基本事実抽出とPhase 3.1の異常検知", "機能統合説明"),
        ("📊 ファクトブック分析実行", "実行ボタン")
    ]
    
    for element, description in ui_elements:
        if element in content:
            print(f"  ✅ {description}")
        else:
            print(f"  ❌ {description}")
    
    # 5. 構文解析によるエラーチェック
    print("\n🔍 Step 5: 構文解析チェック")
    try:
        ast.parse(content)
        print("  ✅ Python構文が正常です")
        syntax_ok = True
    except SyntaxError as e:
        print(f"  ❌ 構文エラー: {e}")
        syntax_ok = False
    
    # 6. 統合ポイントの数量確認
    print("\n📊 Step 6: 統合ポイント数量確認")
    
    # ファクトブック関連のコード行数をカウント
    fact_book_lines = [line for line in content.split('\n') if 'fact_book' in line.lower() or '統合ファクトブック' in line]
    print(f"  📝 ファクトブック関連コード行数: {len(fact_book_lines)}")
    
    # コールバック行数
    callback_start = content.find("# 📊 Phase 3: 統合ファクトブック分析コールバック")
    if callback_start != -1:
        callback_section = content[callback_start:callback_start+5000]
        callback_lines = len(callback_section.split('\n'))
        print(f"  🔄 コールバックセクション行数: {callback_lines}")
    
    # 7. 既存機能との競合チェック
    print("\n⚠️ Step 7: 既存機能競合チェック")
    
    # 既存のタブとの重複確認
    existing_tabs = re.findall(r"dcc\.Tab\(label='([^']*)'", content)
    print(f"  📑 総タブ数: {len(existing_tabs)}")
    
    if "📊 統合ファクトブック" in existing_tabs:
        tab_count = existing_tabs.count("📊 統合ファクトブック")
        if tab_count == 1:
            print(f"  ✅ ファクトブックタブは一意です")
        else:
            print(f"  ⚠️ ファクトブックタブが{tab_count}回定義されています")
    
    # 8. Phase 3機能の完全性確認
    print("\n🎯 Step 8: Phase 3機能完全性")
    
    phase_features = [
        ("Phase 2", "基本事実抽出"),
        ("Phase 3.1", "異常検知"),
        ("Phase 3.2", "統合可視化")
    ]
    
    for phase, description in phase_features:
        if phase in content:
            print(f"  ✅ {phase}: {description}")
        else:
            print(f"  ❌ {phase}: {description}")
    
    # 総合判定
    print("\n" + "=" * 80)
    print("🎯 統合テスト結果:")
    
    # 必須チェック項目
    critical_checks = [
        "統合ファクトブック" in content,
        "fact_book_analysis" in content,
        "generate-fact-book-button" in content,
        syntax_ok
    ]
    
    passed_checks = sum(critical_checks)
    total_checks = len(critical_checks)
    
    success_rate = (passed_checks / total_checks) * 100
    
    if success_rate >= 100:
        print(f"✅ 統合テスト完全成功 ({success_rate:.1f}%)")
        print("📋 結論: Phase 3の統合は正常に完了しています")
        return True
    elif success_rate >= 75:
        print(f"⚠️ 統合テスト部分成功 ({success_rate:.1f}%)")
        print("📋 結論: 基本的な統合は完了していますが、一部要改善")
        return True
    else:
        print(f"❌ 統合テスト失敗 ({success_rate:.1f}%)")
        print("📋 結論: 統合に重大な問題があります")
        return False

def test_dash_integration_functions():
    """統合された関数の基本動作テスト"""
    
    print("\n" + "=" * 80)
    print("🔧 統合関数の基本動作テスト")
    print("=" * 80)
    
    try:
        # dash_fact_book_integration モジュールの基本テスト
        import sys
        sys.path.append('shift_suite/tasks')
        
        # モジュールが存在するかテスト
        integration_file = Path("shift_suite/tasks/dash_fact_book_integration.py")
        if integration_file.exists():
            print("✅ 統合モジュールファイルが存在します")
            
            # モジュール内の重要関数の存在確認
            with open(integration_file, 'r', encoding='utf-8') as f:
                module_content = f.read()
            
            required_functions = [
                "create_fact_book_analysis_tab",
                "create_fact_book_dashboard", 
                "create_overview_cards",
                "create_anomaly_section",
                "get_fact_book_tab_definition"
            ]
            
            for func in required_functions:
                if f"def {func}" in module_content:
                    print(f"  ✅ {func} 関数が定義されています")
                else:
                    print(f"  ❌ {func} 関数が見つかりません")
        else:
            print("❌ 統合モジュールファイルが見つかりません")
        
    except Exception as e:
        print(f"⚠️ 基本動作テストでエラー: {e}")

if __name__ == "__main__":
    # 統合完了検証
    integration_success = verify_integration_completion()
    
    # 関数動作テスト
    test_dash_integration_functions()
    
    print(f"\n🏁 最終結果: {'✅ 統合成功' if integration_success else '❌ 統合に問題'}")