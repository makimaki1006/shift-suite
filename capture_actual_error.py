#!/usr/bin/env python3
"""
実際のdf_shortage_role_filteredエラーをキャプチャ
"""

import sys
import traceback
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def capture_error():
    """実際のエラーをキャプチャ"""
    print("=== df_shortage_role_filteredエラー追跡 ===")
    
    try:
        # dash_app.pyを直接インポートしてcreate_shortage_tab呼び出し
        import dash_app
        print("✅ dash_app.py import successful")
        
        # DATA_CACHEをクリア（新しい状態をシミュレート）
        if hasattr(dash_app, 'DATA_CACHE'):
            dash_app.DATA_CACHE.clear()
        
        # create_shortage_tab関数を直接実行
        print("🔍 create_shortage_tab関数を実行...")
        result = dash_app.create_shortage_tab("test_scenario")
        print(f"✅ 成功: {type(result)}")
        
    except NameError as e:
        if "df_shortage_role_filtered" in str(e):
            print(f"❌ df_shortage_role_filteredエラー発生: {e}")
            print("\n=== 詳細トレースバック ===")
            print(traceback.format_exc())
            
            # エラーが発生した行番号を特定
            tb = traceback.extract_tb(e.__traceback__)
            for frame in tb:
                if "df_shortage_role_filtered" in frame.line:
                    print(f"🎯 エラー発生箇所: {frame.filename}:{frame.lineno}")
                    print(f"   問題の行: {frame.line}")
            
        else:
            print(f"✅ 別のNameError: {e}")
    except Exception as e:
        print(f"✅ その他のエラー: {type(e).__name__}: {e}")

def check_function_definition():
    """関数定義を再確認"""
    print("\n=== 関数定義確認 ===")
    
    dash_app_path = Path("dash_app.py")
    if not dash_app_path.exists():
        print("❌ dash_app.py not found")
        return
    
    with open(dash_app_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # create_shortage_tab関数の範囲を特定
    function_start = None
    function_end = None
    
    for i, line in enumerate(lines):
        if "def create_shortage_tab(" in line:
            function_start = i + 1
            break
    
    if function_start is None:
        print("❌ create_shortage_tab function not found")
        return
    
    # 関数の終わりを探す
    for i in range(function_start, len(lines)):
        line = lines[i]
        if line.strip().startswith("def ") and not line.startswith("    "):
            function_end = i
            break
    
    if function_end is None:
        function_end = len(lines)
    
    print(f"関数範囲: 行 {function_start} - {function_end}")
    
    # df_shortage_role_filteredの使用箇所をチェック
    df_usage_lines = []
    for i in range(function_start - 1, function_end):
        line = lines[i]
        if "df_shortage_role_filtered" in line:
            df_usage_lines.append((i + 1, line.strip()))
    
    print(f"\ndf_shortage_role_filteredの使用箇所 ({len(df_usage_lines)}箇所):")
    for line_num, line_content in df_usage_lines:
        print(f"  {line_num:4d}: {line_content}")
    
    # 初期化箇所を確認
    init_lines = [item for item in df_usage_lines if "= {" in item[1]]
    if init_lines:
        print(f"\n初期化箇所: 行 {init_lines[0][0]}")
    else:
        print("\n❌ 初期化箇所が見つからない")

if __name__ == "__main__":
    capture_error()
    check_function_definition()