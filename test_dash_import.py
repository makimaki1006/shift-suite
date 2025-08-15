#!/usr/bin/env python3
"""
dash_app.pyのインポートをテストして問題を特定
"""

def test_dash_import():
    """dash_app.pyのインポートテスト"""
    print("=== dash_app.py インポートテスト ===")
    
    try:
        print("dash_app.pyをインポート中...")
        import dash_app
        print("✅ インポート成功")
        
        # shortage_dash_logの存在確認
        if hasattr(dash_app, 'shortage_dash_log'):
            print("✅ shortage_dash_log が存在")
            # テストログを出力
            dash_app.shortage_dash_log.info("=== インポートテスト成功 ===")
            print("✅ ログ出力成功")
        else:
            print("❌ shortage_dash_log が見つからない")
        
        # create_shortage_tab関数の確認
        if hasattr(dash_app, 'create_shortage_tab'):
            print("✅ create_shortage_tab関数が存在")
            
            # 関数のソースコード確認（最初の数行）
            import inspect
            source_lines = inspect.getsource(dash_app.create_shortage_tab).split('\n')[:10]
            print("関数の最初の数行:")
            for i, line in enumerate(source_lines[:5], 1):
                print(f"  {i}: {line}")
            
            # shortage_dash_log使用確認
            source = inspect.getsource(dash_app.create_shortage_tab)
            if "shortage_dash_log" in source:
                print("✅ 関数内でshortage_dash_logを使用")
            else:
                print("❌ 関数内でshortage_dash_logを使用していない")
                
        else:
            print("❌ create_shortage_tab関数が見つからない")
            
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ その他のエラー: {e}")
        import traceback
        print("詳細:")
        print(traceback.format_exc())
        return False
    
    return True

def test_create_shortage_tab():
    """create_shortage_tab関数の直接実行テスト"""
    print("\n=== create_shortage_tab関数実行テスト ===")
    
    try:
        import dash_app
        
        # DATA_CACHEをクリア
        if hasattr(dash_app, 'DATA_CACHE'):
            dash_app.DATA_CACHE.clear()
        
        print("create_shortage_tab関数を実行中...")
        result = dash_app.create_shortage_tab("test_scenario")
        print(f"✅ 実行成功: {type(result)}")
        
        # shortage_dashboard.logを確認
        import os
        log_file = "shortage_dashboard.log"
        if os.path.exists(log_file):
            print(f"✅ ログファイルが存在: {log_file}")
            
            # 最新のログエントリを確認
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    print("最新のログエントリ:")
                    for line in lines[-5:]:  # 最後の5行
                        print(f"  {line.strip()}")
                else:
                    print("❌ ログファイルが空")
        else:
            print(f"❌ ログファイルが存在しない: {log_file}")
            
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        import traceback
        print("詳細:")
        print(traceback.format_exc())
        return False
    
    return True

if __name__ == "__main__":
    print("dash_app.py 問題診断開始")
    
    success1 = test_dash_import()
    success2 = test_create_shortage_tab()
    
    print(f"\n=== 診断結果 ===")
    print(f"インポートテスト: {'✅ 成功' if success1 else '❌ 失敗'}")
    print(f"関数実行テスト: {'✅ 成功' if success2 else '❌ 失敗'}")
    
    if success1 and success2:
        print("🎉 dash_app.pyは正常に動作しています")
        print("問題は実際のWebアプリケーション実行時にあります")
    else:
        print("❌ dash_app.pyに問題があります")