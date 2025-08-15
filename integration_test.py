#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統合テスト - 修正済みコンポーネントの連携動作検証
"""

import os
import sys

# UTF-8出力設定
os.environ['PYTHONIOENCODING'] = 'utf-8'

def test_integration():
    print("=== 修正済みコンポーネント統合テスト ===")
    print()

    test_results = {
        'fact_book_integration': False,
        'network_analysis': False,
        'constants_fix': False,
        'directory_safety': False
    }

    # Test 1: ファクトブック統合モジュール
    print("1. ファクトブック統合モジュールテスト")
    try:
        from shift_suite.tasks.dash_fact_book_integration import (
            create_fact_book_analysis_tab,
            register_fact_book_callbacks,
            get_fact_book_tab_definition
        )
        print("   OK: 全ての関数のインポート成功")
        test_results['fact_book_integration'] = True
    except Exception as e:
        print(f"   NG: エラー - {e}")

    print()

    # Test 2: ネットワーク分析機能
    print("2. ネットワーク分析機能テスト")
    try:
        import dash_cytoscape as cyto
        version = getattr(cyto, '__version__', 'unknown')
        print(f"   OK: dash-cytoscape利用可能 (v{version})")
        test_results['network_analysis'] = True
    except Exception as e:
        print(f"   NG: エラー - {e}")

    print()

    # Test 3: SLOT_HOURS定数修正
    print("3. SLOT_HOURS定数テスト")
    try:
        from shift_suite.tasks.constants import SLOT_HOURS, DEFAULT_SLOT_MINUTES
        print(f"   OK: SLOT_HOURS = {SLOT_HOURS} ({DEFAULT_SLOT_MINUTES}分 ÷ 60)")
        
        # 修正済みファイルでのインポート確認
        import shift_suite.tasks.ai_comprehensive_report_generator
        import shift_suite.tasks.analysis_dashboard
        print("   OK: 修正済みファイルでの定数インポート成功")
        test_results['constants_fix'] = True
    except Exception as e:
        print(f"   NG: エラー - {e}")

    print()

    # Test 4: 一時ディレクトリ安全性
    print("4. 一時ディレクトリ安全性テスト")
    try:
        import dash_app
        scenario_dir = dash_app.CURRENT_SCENARIO_DIR
        if scenario_dir:
            path_str = str(scenario_dir)
            is_temp = 'temp' in path_str.lower() or 'tmp' in path_str.lower()
            if not is_temp:
                print(f"   OK: 永続化ディレクトリ使用中 - {scenario_dir}")
                test_results['directory_safety'] = True
            else:
                print(f"   NG: 一時ディレクトリ使用中 - {scenario_dir}")
        else:
            print("   OK: シナリオディレクトリ未設定（安全なデフォルト状態）")
            test_results['directory_safety'] = True
    except Exception as e:
        print(f"   NG: エラー - {e}")

    print()
    print("=== テスト結果サマリー ===")
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    for test_name, result in test_results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    print()
    print(f"合格率: {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("STATUS: 全テスト合格 - 統合修正成功")
        return True
    else:
        print("STATUS: 一部テスト失敗 - 要追加修正")
        return False

if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)