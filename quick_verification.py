#!/usr/bin/env python3
"""
統一分析管理システム クイック検証スクリプト
実データを使用せずに、システムの基本動作を検証
"""

import sys
import os
from pathlib import Path
from datetime import datetime

def print_section(title):
    """セクション表示"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def verify_file_modifications():
    """ファイル修正状況の確認"""
    print_section("1. ファイル修正状況の確認")
    
    critical_files = {
        "app.py": ["unified_analysis_manager", "UNIFIED_ANALYSIS_AVAILABLE"],
        "shift_suite/tasks/shortage.py": ["slot_hours", "slot / 60"],
        "shift_suite/tasks/fatigue.py": ["slot_minutes"],
        "shift_suite/tasks/unified_analysis_manager.py": ["SafeDataConverter", "DynamicKeyManager"]
    }
    
    for file_path, keywords in critical_files.items():
        if Path(file_path).exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n📄 {file_path}")
            for keyword in keywords:
                if keyword in content:
                    print(f"   ✅ '{keyword}' 実装確認")
                else:
                    print(f"   ❌ '{keyword}' 見つかりません")
        else:
            print(f"\n❌ {file_path} が存在しません")

def verify_calculation_fixes():
    """計算ロジック修正の確認"""
    print_section("2. 計算ロジック修正の確認")
    
    # 問題のあったパターンを検索
    problematic_patterns = [
        ("SLOT_HOURS定数", "SLOT_HOURS = "),
        ("固定スロット時間", ".sum() * SLOT_HOURS"),
        ("全体合計の誤り", ".sum().sum() * SLOT_HOURS")
    ]
    
    files_to_check = [
        "shift_suite/tasks/shortage.py",
        "shift_suite/tasks/build_stats.py",
        "shift_suite/tasks/fatigue.py"
    ]
    
    for file_path in files_to_check:
        if Path(file_path).exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n📄 {file_path}")
            problems_found = False
            for pattern_name, pattern in problematic_patterns:
                if pattern in content:
                    print(f"   ⚠️ {pattern_name} が残存しています")
                    problems_found = True
            
            if not problems_found:
                print(f"   ✅ 問題パターンは修正済み")
                # 正しい実装の確認
                if "slot_hours = slot / 60" in content or "slot_minutes" in content:
                    print(f"   ✅ 動的スロット計算実装確認")

def verify_json_output_fix():
    """JSON出力問題の修正確認"""
    print_section("3. JSON出力修正の確認")
    
    # app.pyでの統一システム利用確認
    app_path = Path("app.py")
    if app_path.exists():
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        integration_points = [
            ("統一システムimport", "from shift_suite.tasks.unified_analysis_manager import"),
            ("統一システム初期化", "UnifiedAnalysisManager()"),
            ("AI互換データ取得", "get_ai_compatible_results"),
            ("データ整合性チェック", "data_integrity")
        ]
        
        for check_name, pattern in integration_points:
            if pattern in content:
                print(f"✅ {check_name}: 実装確認")
            else:
                print(f"❌ {check_name}: 見つかりません")

def verify_error_handling():
    """エラー処理実装の確認"""
    print_section("4. エラー処理とフォールバック機能")
    
    unified_path = Path("shift_suite/tasks/unified_analysis_manager.py")
    if unified_path.exists():
        with open(unified_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # エラー処理関連のカウント
        try_count = content.count("try:")
        except_count = content.count("except")
        log_error_count = content.count("log.error")
        log_warning_count = content.count("log.warning")
        fallback_count = content.count("fallback")
        
        print(f"エラー処理実装統計:")
        print(f"  try-except: {try_count}/{except_count} ブロック")
        print(f"  エラーログ: {log_error_count} 箇所")
        print(f"  警告ログ: {log_warning_count} 箇所") 
        print(f"  フォールバック: {fallback_count} 箇所")
        
        if try_count > 5 and except_count > 5:
            print(f"  ✅ 包括的なエラー処理実装")
        else:
            print(f"  ⚠️ エラー処理が不足している可能性")

def generate_test_commands():
    """テスト実行用コマンドの生成"""
    print_section("5. 推奨テストコマンド")
    
    print("\n基本的な動作確認:")
    print("  streamlit run app.py")
    
    print("\n計算結果の確認:")
    print("  # 最新の結果ディレクトリを確認")
    print("  ls -la out/*/scenario_*/")
    
    print("\nJSON出力の確認:")
    print("  # AI包括レポートの内容確認")
    print("  find out -name '*comprehensive*.json' -exec cat {} \\; | python -m json.tool | less")
    
    print("\nログの確認:")
    print("  # エラーや警告の確認")
    print("  grep -E 'ERROR|WARNING' shift_suite.log | tail -20")
    
    print("\n動的スロット設定の確認:")
    print("  # スロット関連のログ")
    print("  grep -i 'slot' shift_suite.log | tail -10")

def main():
    """メイン検証処理"""
    print("🔍 統一分析管理システム クイック検証")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 各種検証の実行
    verify_file_modifications()
    verify_calculation_fixes()
    verify_json_output_fix()
    verify_error_handling()
    generate_test_commands()
    
    # 総合評価
    print_section("検証結果サマリー")
    print("""
このクイック検証で確認できること:
✅ ファイル構造と基本的な実装
✅ 計算ロジックの修正状況
✅ 統一システムの統合状況
✅ エラー処理の実装度

次のステップ:
1. 上記のテストコマンドを実行
2. 実際のデータでapp.pyを起動して動作確認
3. VERIFICATION_GUIDE.mdに従って詳細検証
""")

if __name__ == "__main__":
    main()