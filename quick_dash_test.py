#!/usr/bin/env python3
"""
dash_app.pyの問題を素早くテスト
"""

import sys
from pathlib import Path

# シフト分析モジュールのパスを追加
sys.path.append(str(Path(__file__).parent))

def test_import():
    """モジュールインポートテスト"""
    try:
        import dash_app
        print("OK: dash_app.py インポート成功")
        return True
    except Exception as e:
        print(f"NG: dash_app.py インポートエラー: {e}")
        return False

def test_function_existence():
    """関数存在テスト"""
    try:
        import dash_app
        
        # 重要な関数が存在するか確認
        functions_to_check = [
            'create_shortage_tab',
            'create_leave_analysis_tab',
            'initialize_shortage_content',
            'initialize_leave_content'
        ]
        
        missing_functions = []
        for func_name in functions_to_check:
            if not hasattr(dash_app, func_name):
                missing_functions.append(func_name)
        
        if missing_functions:
            print(f"NG: 不足している関数: {missing_functions}")
            return False
        else:
            print("OK: 全ての重要関数が存在")
            return True
            
    except Exception as e:
        print(f"NG: 関数存在テストエラー: {e}")
        return False

def test_data_cache():
    """DATA_CACHEテスト"""
    try:
        import dash_app
        
        if hasattr(dash_app, 'DATA_CACHE'):
            print("OK: DATA_CACHEが存在")
            
            # data_get関数のテスト
            if hasattr(dash_app, 'data_get'):
                result = dash_app.data_get('test_key', 'default_value')
                if result == 'default_value':
                    print("OK: data_get関数が正常動作")
                    return True
                else:
                    print("NG: data_get関数の動作が異常")
                    return False
            else:
                print("NG: data_get関数が存在しない")
                return False
        else:
            print("NG: DATA_CACHEが存在しない")
            return False
            
    except Exception as e:
        print(f"NG: DATA_CACHEテストエラー: {e}")
        return False

def run_quick_tests():
    """クイックテスト実行"""
    print("=== dash_app.py クイックテスト ===")
    
    tests = [
        ("インポートテスト", test_import),
        ("関数存在テスト", test_function_existence),
        ("DATA_CACHEテスト", test_data_cache),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        results.append(test_func())
    
    print(f"\n=== 結果 ===")
    print(f"成功: {sum(results)}/{len(results)}")
    
    if all(results):
        print("全テスト成功: dash_app.pyの基本構造は正常")
        print("問題は実行時の条件やデータに関連している可能性があります")
    else:
        print("一部テスト失敗: dash_app.pyに構造的問題があります")

if __name__ == "__main__":
    run_quick_tests()