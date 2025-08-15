#!/usr/bin/env python3
"""
最小限のdash_app.pyテスト - エラーの正確な場所を特定
"""

def test_function_exists():
    """関数の存在とコードの確認"""
    print("=== 関数存在チェック ===")
    
    # ファイルから直接読み込み
    with open('dash_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # create_shortage_tab関数の存在確認
    if "def create_shortage_tab(" in content:
        print("✅ create_shortage_tab関数が存在")
        
        # 変数初期化の確認
        if "df_shortage_role_filtered = {}" in content:
            print("✅ df_shortage_role_filtered初期化が存在")
            
            # tryブロック内にあるか確認
            lines = content.split('\n')
            function_started = False
            try_started = False
            init_found = False
            
            for i, line in enumerate(lines):
                if "def create_shortage_tab(" in line:
                    function_started = True
                    print(f"  関数開始: 行 {i+1}")
                elif function_started and "try:" in line.strip():
                    try_started = True
                    print(f"  try開始: 行 {i+1}")
                elif function_started and try_started and "df_shortage_role_filtered = {}" in line:
                    init_found = True
                    spaces = len(line) - len(line.lstrip())
                    print(f"  変数初期化: 行 {i+1}, インデント: {spaces}スペース")
                    if spaces >= 8:  # tryブロック内（最低8スペース）
                        print("  ✅ tryブロック内に正しく配置")
                    else:
                        print("  ❌ tryブロック外に配置されている")
                    break
            
            if not init_found:
                print("  ❌ tryブロック内に初期化が見つからない")
                
        else:
            print("❌ df_shortage_role_filtered初期化が見つからない")
    else:
        print("❌ create_shortage_tab関数が見つからない")

def check_syntax():
    """構文チェック"""
    print("\n=== 構文チェック ===")
    try:
        import ast
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        print("✅ 構文は正常")
        return True
    except SyntaxError as e:
        print(f"❌ 構文エラー: {e}")
        print(f"   行 {e.lineno}: {e.text}")
        return False
    except Exception as e:
        print(f"❌ その他のエラー: {e}")
        return False

if __name__ == "__main__":
    test_function_exists()
    check_syntax()
    print("\n" + "="*50)
    print("エラーが続く場合、以下を確認してください:")
    print("1. dash_app.pyが実際に最新版を使用しているか")
    print("2. Pythonプロセスを完全に再起動したか")
    print("3. 他にdash_app.pyファイルが存在しないか")
    print("4. インポートキャッシュがクリアされているか")