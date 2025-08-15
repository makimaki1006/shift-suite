#!/usr/bin/env python3
"""
疲労度分析の基本的な構文とインポートテスト
"""
import sys
from pathlib import Path

def test_imports():
    """インポートテストのみ実行"""
    print("🔬 疲労度分析モジュールのインポートテスト")
    print("=" * 50)
    
    try:
        # 基本的なインポートテスト
        from shift_suite.tasks.fatigue import train_fatigue
        print("✅ train_fatigue関数のインポート成功")
        
        from shift_suite.tasks.fatigue import _features
        print("✅ _features関数のインポート成功")
        
        from shift_suite.tasks.fatigue import _get_time_category
        print("✅ _get_time_category関数のインポート成功")
        
        from shift_suite.tasks.fatigue import _analyze_consecutive_days
        print("✅ _analyze_consecutive_days関数のインポート成功")
        
        # 関数の署名確認
        import inspect
        sig = inspect.signature(train_fatigue)
        print(f"✅ train_fatigue署名: {sig}")
        
        return True
        
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ その他のエラー: {e}")
        return False

def test_constants():
    """定数のインポートテスト"""
    print("\n📊 定数モジュールのテスト")
    print("-" * 30)
    
    try:
        from shift_suite.tasks.constants import FATIGUE_PARAMETERS
        print("✅ FATIGUE_PARAMETERS定数のインポート成功")
        print(f"パラメータ: {FATIGUE_PARAMETERS}")
        return True
    except ImportError as e:
        print(f"❌ 定数インポートエラー: {e}")
        print("⚠️ constants.pyが不足している可能性があります")
        return False

def test_rest_analyzer():
    """RestTimeAnalyzerのインポートテスト"""
    print("\n⏰ RestTimeAnalyzerのテスト")
    print("-" * 30)
    
    try:
        from shift_suite.tasks.analyzers.rest_time import RestTimeAnalyzer
        print("✅ RestTimeAnalyzerのインポート成功")
        
        # インスタンス生成テスト
        analyzer = RestTimeAnalyzer()
        print("✅ RestTimeAnalyzerインスタンス生成成功")
        return True
    except ImportError as e:
        print(f"❌ RestTimeAnalyzerインポートエラー: {e}")
        print("⚠️ rest_time.pyが不足している可能性があります")
        return False

def test_utils():
    """ユーティリティ関数のテスト"""
    print("\n🛠️ ユーティリティ関数のテスト")
    print("-" * 30)
    
    try:
        from shift_suite.tasks.utils import save_df_xlsx, save_df_parquet, log
        print("✅ ユーティリティ関数のインポート成功")
        return True
    except ImportError as e:
        print(f"❌ ユーティリティインポートエラー: {e}")
        return False

def main():
    """メインテスト"""
    print("🔍 復元された疲労度分析機能の基本テスト")
    print("=" * 60)
    
    tests = [
        ("基本インポート", test_imports),
        ("定数モジュール", test_constants),
        ("RestTimeAnalyzer", test_rest_analyzer),
        ("ユーティリティ", test_utils)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}でエラー: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📋 テスト結果")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 結果: {passed_tests}/{total_tests} テストが成功")
    
    if passed_tests == total_tests:
        print("🎉 基本テストが成功！疲労度分析機能は正しく復元されています。")
        print("\n📝 次のステップ:")
        print("1. app.pyで疲労分析オプションを有効にして実行")
        print("2. 生成されたfatigue_score.parquetファイルを確認")
        print("3. dash_app.pyで疲労度タブの表示を確認")
    else:
        print("⚠️ 一部の依存関係が不足しています。")
        failed_tests = [name for name, result in results if not result]
        print(f"失敗したテスト: {failed_tests}")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()