#!/usr/bin/env python3
"""
最小限のdash_appテスト - 問題を特定
"""

import sys
import traceback

def test_minimal_dash():
    """最小限のdash_appテスト"""
    
    print("=== Minimal Dash Test ===")
    
    try:
        # まず必要な基本importをテスト
        print("1. 基本importテスト...")
        import dash
        import pandas as pd
        print("   基本import: OK")
        
        # オプションのimportをテスト
        print("2. オプションimportテスト...")
        optional_imports = []
        
        try:
            import dash_cytoscape as cyto
            optional_imports.append("dash_cytoscape: OK")
        except ImportError:
            optional_imports.append("dash_cytoscape: MISSING")
            
        try:
            import seaborn as sns
            optional_imports.append("seaborn: OK")
        except ImportError:
            optional_imports.append("seaborn: MISSING")
            
        for status in optional_imports:
            print(f"   {status}")
        
        # dash_app.pyの構文チェック
        print("3. dash_app.py構文チェック...")
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        compile(content, 'dash_app.py', 'exec')
        print("   構文チェック: OK")
        
        # 必要なimportを一時的にコメントアウトしてimportテスト
        print("4. 条件付きimportテスト...")
        
        # dash_cytoscapeを条件付きにする修正を作成
        modified_content = content.replace(
            "import dash_cytoscape as cyto",
            "try:\n    import dash_cytoscape as cyto\n    CYTOSCAPE_AVAILABLE = True\nexcept ImportError:\n    cyto = None\n    CYTOSCAPE_AVAILABLE = False"
        )
        
        # seabornも条件付きに
        modified_content = modified_content.replace(
            "import seaborn as sns",
            "try:\n    import seaborn as sns\n    SEABORN_AVAILABLE = True\nexcept ImportError:\n    sns = None\n    SEABORN_AVAILABLE = False"
        )
        
        # テスト用のファイルを作成
        with open('dash_app_test.py', 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        # モディファイ版をimportテスト
        sys.path.insert(0, '.')
        import dash_app_test
        print("   条件付きimport: OK")
        
        print("\\n=== テスト完了 ===")
        return True
        
    except SyntaxError as e:
        print(f"構文エラー: 行{e.lineno} - {e.msg}")
        print(f"エラー位置: {e.text}")
        return False
        
    except Exception as e:
        print(f"エラー: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_minimal_dash()
    if success:
        print("成功: dash_appは修正可能です")
    else:
        print("失敗: 重要な問題があります")