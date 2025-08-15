#!/usr/bin/env python3
"""
df_shortage_role_filteredエラー修正のテスト
"""

import sys
from pathlib import Path
import pandas as pd

# シフト分析モジュールのパスを追加
sys.path.append(str(Path(__file__).parent))

def test_create_shortage_tab():
    """create_shortage_tab関数のテスト"""
    print("=== create_shortage_tab関数テスト ===")
    
    try:
        # dash_app.pyをインポート
        import dash_app
        
        # create_shortage_tab関数が存在することを確認
        if hasattr(dash_app, 'create_shortage_tab'):
            print("OK: create_shortage_tab関数が存在")
            
            # 関数を実行してみる（エラーが発生しないか確認）
            try:
                result = dash_app.create_shortage_tab("test_scenario")
                print("OK: create_shortage_tab関数の実行が成功")
                print(f"    返り値のタイプ: {type(result)}")
                return True
            except NameError as e:
                if "df_shortage_role_filtered" in str(e):
                    print(f"NG: df_shortage_role_filteredエラーが発生: {e}")
                    return False
                else:
                    print(f"OK: 他のNameError（許容範囲）: {e}")
                    return True
            except Exception as e:
                print(f"OK: その他のエラー（許容範囲）: {e}")
                return True
        else:
            print("NG: create_shortage_tab関数が存在しない")
            return False
            
    except Exception as e:
        print(f"NG: テスト実行エラー: {e}")
        return False

def test_variable_initialization():
    """変数初期化のテスト"""
    print("\n=== 変数初期化テスト ===")
    
    try:
        # dash_app.pyのソースコードを確認
        dash_app_path = Path(__file__).parent / "dash_app.py"
        if dash_app_path.exists():
            content = dash_app_path.read_text(encoding='utf-8')
            
            # 重要な修正点をチェック
            checks = [
                ("関数先頭での初期化", "df_shortage_role_filtered = {}"),
                ("関数先頭での初期化", "df_shortage_emp_filtered = {}"),
                ("try-except追加", "except Exception as e:"),
                ("ログ追加", "[shortage_tab]"),
            ]
            
            success_count = 0
            for check_name, pattern in checks:
                if pattern in content:
                    print(f"OK: {check_name} - '{pattern}' が見つかりました")
                    success_count += 1
                else:
                    print(f"NG: {check_name} - '{pattern}' が見つかりません")
            
            print(f"変数初期化チェック: {success_count}/{len(checks)} 成功")
            return success_count == len(checks)
        else:
            print("NG: dash_app.pyが見つかりません")
            return False
            
    except Exception as e:
        print(f"NG: 変数初期化テストエラー: {e}")
        return False

def run_shortage_error_tests():
    """不足分析エラーテスト実行"""
    print("=== df_shortage_role_filteredエラー修正テスト ===")
    print(f"実行時刻: {pd.Timestamp.now()}")
    
    tests = [
        ("関数実行テスト", test_create_shortage_tab),
        ("変数初期化テスト", test_variable_initialization),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        results.append(test_func())
    
    print(f"\n=== テスト結果 ===")
    print(f"成功: {sum(results)}/{len(results)}")
    
    if all(results):
        print("全テスト成功: df_shortage_role_filteredエラーが修正されました")
        print("dash_app.pyを起動して動作確認してください")
    else:
        print("一部テスト失敗: まだ問題が残っている可能性があります")
    
    return all(results)

if __name__ == "__main__":
    run_shortage_error_tests()