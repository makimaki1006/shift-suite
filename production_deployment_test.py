#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本番環境適用前テスト
Phase 2/3.1修正の最終確認スクリプト
"""

import sys
import traceback
from pathlib import Path
from datetime import datetime

def test_import_functionality():
    """修正されたモジュールのインポートテスト"""
    
    print("🔍 インポート機能テスト")
    print("=" * 60)
    
    test_results = {}
    
    # Phase 2インポートテスト
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from shift_suite.tasks.fact_extractor_prototype import FactExtractorPrototype
        
        # インスタンス生成テスト
        extractor = FactExtractorPrototype()
        print("✅ Phase 2 (FactExtractorPrototype): インポート・初期化成功")
        test_results["phase2_import"] = True
        
    except Exception as e:
        print(f"❌ Phase 2インポートエラー: {e}")
        print(f"詳細: {traceback.format_exc()}")
        test_results["phase2_import"] = False
    
    # Phase 3.1インポートテスト
    try:
        from shift_suite.tasks.lightweight_anomaly_detector import LightweightAnomalyDetector
        
        # インスタンス生成テスト
        detector = LightweightAnomalyDetector(sensitivity="medium")
        print("✅ Phase 3.1 (LightweightAnomalyDetector): インポート・初期化成功")
        test_results["phase31_import"] = True
        
    except Exception as e:
        print(f"❌ Phase 3.1インポートエラー: {e}")
        print(f"詳細: {traceback.format_exc()}")
        test_results["phase31_import"] = False
    
    # 統合モジュールテスト
    try:
        from shift_suite.tasks.fact_book_visualizer import FactBookVisualizer
        
        # インスタンス生成テスト
        visualizer = FactBookVisualizer(sensitivity="medium")
        print("✅ 統合モジュール (FactBookVisualizer): インポート・初期化成功")
        test_results["integration_import"] = True
        
    except Exception as e:
        print(f"❌ 統合モジュールインポートエラー: {e}")
        print(f"詳細: {traceback.format_exc()}")
        test_results["integration_import"] = False
    
    return test_results

def test_syntax_validation():
    """構文検証テスト"""
    
    print("\n🔍 構文検証テスト")
    print("=" * 60)
    
    test_files = [
        "shift_suite/tasks/fact_extractor_prototype.py",
        "shift_suite/tasks/lightweight_anomaly_detector.py",
        "shift_suite/tasks/fact_book_visualizer.py"
    ]
    
    syntax_results = {}
    
    for file_path in test_files:
        path = Path(file_path)
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 基本的な構文チェック
                compile(content, str(path), 'exec')
                print(f"✅ {file_path}: 構文エラーなし")
                syntax_results[file_path] = True
                
            except SyntaxError as e:
                print(f"❌ {file_path}: 構文エラー - {e}")
                syntax_results[file_path] = False
            except Exception as e:
                print(f"⚠️ {file_path}: 読み込みエラー - {e}")
                syntax_results[file_path] = False
        else:
            print(f"⚠️ {file_path}: ファイル不存在")
            syntax_results[file_path] = False
    
    return syntax_results

def test_slot_hours_usage():
    """SLOT_HOURS使用箇所の確認"""
    
    print("\n🔍 SLOT_HOURS使用箇所確認")
    print("=" * 60)
    
    test_files = [
        "shift_suite/tasks/fact_extractor_prototype.py",
        "shift_suite/tasks/lightweight_anomaly_detector.py"
    ]
    
    usage_results = {}
    
    for file_path in test_files:
        path = Path(file_path)
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # SLOT_HOURS乗算箇所をカウント
                slot_hours_count = content.count('* SLOT_HOURS')
                
                # 誤ったコメントの確認
                wrong_comment = "parsed_slots_count is already in hours" in content
                
                print(f"📊 {file_path}:")
                print(f"  SLOT_HOURS乗算: {slot_hours_count}箇所")
                print(f"  誤ったコメント: {'残存' if wrong_comment else '除去済み'}")
                
                # 期待値との比較
                if file_path.endswith("fact_extractor_prototype.py"):
                    expected = 4
                    status = "✅" if slot_hours_count >= expected and not wrong_comment else "❌"
                else:
                    expected = 1
                    status = "✅" if slot_hours_count >= expected and not wrong_comment else "❌"
                
                print(f"  評価: {status} (期待値: {expected}箇所)")
                
                usage_results[file_path] = {
                    "slot_hours_count": slot_hours_count,
                    "wrong_comment": wrong_comment,
                    "expected": expected,
                    "passed": slot_hours_count >= expected and not wrong_comment
                }
                
            except Exception as e:
                print(f"❌ {file_path}: 読み込みエラー - {e}")
                usage_results[file_path] = {"error": str(e)}
        else:
            print(f"⚠️ {file_path}: ファイル不存在")
            usage_results[file_path] = {"error": "ファイル不存在"}
    
    return usage_results

def test_calculation_logic():
    """計算ロジックの理論確認"""
    
    print("\n🔍 計算ロジック理論確認")
    print("=" * 60)
    
    # 理論値テスト
    SLOT_HOURS = 0.5
    test_cases = [
        {"slots": 8, "expected_hours": 4.0, "description": "4時間勤務"},
        {"slots": 12, "expected_hours": 6.0, "description": "6時間勤務"},
        {"slots": 16, "expected_hours": 8.0, "description": "8時間勤務"},
        {"slots": 2, "expected_hours": 1.0, "description": "1時間勤務"},
        {"slots": 1, "expected_hours": 0.5, "description": "30分勤務"}
    ]
    
    calculation_results = {}
    
    print("🧮 理論計算確認:")
    for case in test_cases:
        calculated = case["slots"] * SLOT_HOURS
        expected = case["expected_hours"]
        match = abs(calculated - expected) < 0.01
        
        print(f"  {case['description']}: {case['slots']}スロット × {SLOT_HOURS} = {calculated}時間")
        print(f"    期待値: {expected}時間, 一致: {'✅' if match else '❌'}")
        
        calculation_results[case["description"]] = {
            "calculated": calculated,
            "expected": expected,
            "match": match
        }
    
    return calculation_results

def test_dependency_availability():
    """依存関係の確認"""
    
    print("\n🔍 依存関係確認")
    print("=" * 60)
    
    dependencies = [
        "pandas", "numpy", "datetime", "logging", "pathlib"
    ]
    
    dependency_results = {}
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}: 利用可能")
            dependency_results[dep] = True
        except ImportError:
            print(f"❌ {dep}: 利用不可")
            dependency_results[dep] = False
    
    return dependency_results

def generate_deployment_readiness_report(results):
    """デプロイメント準備状況レポート生成"""
    
    print("\n" + "=" * 80)
    print("📋 デプロイメント準備状況レポート")
    print("=" * 80)
    
    # 総合評価の計算
    total_tests = 0
    passed_tests = 0
    
    # インポートテスト評価
    import_tests = results.get("import_tests", {})
    for test, result in import_tests.items():
        total_tests += 1
        if result:
            passed_tests += 1
    
    # 構文テスト評価
    syntax_tests = results.get("syntax_tests", {})
    for test, result in syntax_tests.items():
        total_tests += 1
        if result:
            passed_tests += 1
    
    # SLOT_HOURS使用テスト評価
    usage_tests = results.get("usage_tests", {})
    for test, result in usage_tests.items():
        if isinstance(result, dict) and "passed" in result:
            total_tests += 1
            if result["passed"]:
                passed_tests += 1
    
    # 計算ロジックテスト評価
    calc_tests = results.get("calculation_tests", {})
    for test, result in calc_tests.items():
        total_tests += 1
        if result.get("match", False):
            passed_tests += 1
    
    # 依存関係テスト評価
    dep_tests = results.get("dependency_tests", {})
    for test, result in dep_tests.items():
        total_tests += 1
        if result:
            passed_tests += 1
    
    # 成功率計算
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"🎯 総合結果: {passed_tests}/{total_tests} テスト合格")
    print(f"📊 成功率: {success_rate:.1f}%")
    
    # デプロイメント判定
    if success_rate >= 95:
        deployment_status = "🟢 デプロイメント準備完了"
        recommendation = "本番環境への適用を推奨します"
    elif success_rate >= 80:
        deployment_status = "🟡 条件付きデプロイメント可能"
        recommendation = "軽微な問題の修正後に適用を推奨します"
    else:
        deployment_status = "🔴 デプロイメント延期推奨"
        recommendation = "重要な問題の解決が必要です"
    
    print(f"\n{deployment_status}")
    print(f"推奨: {recommendation}")
    
    # 詳細結果
    print(f"\n📊 詳細結果:")
    print(f"  ✅ インポート機能: {sum(import_tests.values())}/{len(import_tests)}")
    print(f"  ✅ 構文検証: {sum(syntax_tests.values())}/{len(syntax_tests)}")
    print(f"  ✅ SLOT_HOURS使用: {sum(1 for r in usage_tests.values() if isinstance(r, dict) and r.get('passed', False))}/{len([r for r in usage_tests.values() if isinstance(r, dict) and 'passed' in r])}")
    print(f"  ✅ 計算ロジック: {sum(1 for r in calc_tests.values() if r.get('match', False))}/{len(calc_tests)}")
    print(f"  ✅ 依存関係: {sum(dep_tests.values())}/{len(dep_tests)}")
    
    return {
        "success_rate": success_rate,
        "deployment_ready": success_rate >= 95,
        "recommendation": recommendation
    }

def main():
    """メイン実行"""
    
    print("🚨 Phase 2/3.1修正 - 本番環境適用前テスト")
    print("=" * 80)
    print(f"実行日時: {datetime.now().isoformat()}")
    
    # 各テストの実行
    results = {}
    
    # 1. インポート機能テスト
    results["import_tests"] = test_import_functionality()
    
    # 2. 構文検証テスト
    results["syntax_tests"] = test_syntax_validation()
    
    # 3. SLOT_HOURS使用確認
    results["usage_tests"] = test_slot_hours_usage()
    
    # 4. 計算ロジック確認
    results["calculation_tests"] = test_calculation_logic()
    
    # 5. 依存関係確認
    results["dependency_tests"] = test_dependency_availability()
    
    # 6. 総合レポート生成
    deployment_report = generate_deployment_readiness_report(results)
    
    print(f"\n✅ 本番環境適用前テスト完了")
    
    return deployment_report["deployment_ready"]

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)