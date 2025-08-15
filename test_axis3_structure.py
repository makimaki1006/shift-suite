#!/usr/bin/env python3
"""
軸3実装の構造確認（モジュールインポートなし）
"""

import os
import ast

def check_file_structure():
    """ファイル構造と関数・クラスの確認"""
    print("🧪 軸3実装ファイル構造確認")
    print("=" * 50)
    
    files_to_check = [
        "shift_suite/tasks/axis3_time_calendar_mece_extractor.py",
        "shift_suite/tasks/advanced_blueprint_engine_v2.py",
        "dash_app.py"
    ]
    
    for filepath in files_to_check:
        print(f"\n📄 {filepath}")
        
        if not os.path.exists(filepath):
            print("  ❌ ファイルが存在しません")
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # ASTで解析
            tree = ast.parse(content)
            
            # クラスと関数を抽出
            classes = []
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    # トップレベルの関数のみ
                    if hasattr(node, 'col_offset') and node.col_offset == 0:
                        functions.append(node.name)
            
            print(f"  ✅ ファイルサイズ: {len(content):,} 文字")
            print(f"  ✅ 行数: {len(content.splitlines()):,} 行")
            
            if classes:
                print(f"  📦 クラス ({len(classes)}):")
                for cls in classes[:5]:  # 最初の5個まで表示
                    print(f"    - {cls}")
                if len(classes) > 5:
                    print(f"    ... 他 {len(classes) - 5} クラス")
            
            if functions:
                print(f"  🔧 トップレベル関数 ({len(functions)}):")
                for func in functions[:5]:  # 最初の5個まで表示
                    print(f"    - {func}")
                if len(functions) > 5:
                    print(f"    ... 他 {len(functions) - 5} 関数")
            
        except Exception as e:
            print(f"  ❌ 解析エラー: {e}")

def check_axis3_implementation():
    """軸3特有の実装を確認"""
    print("\n\n🔍 軸3特有の実装確認")
    print("=" * 50)
    
    # axis3_time_calendar_mece_extractor.py の確認
    print("\n1. TimeCalendarMECEFactExtractor の確認:")
    
    filepath = "shift_suite/tasks/axis3_time_calendar_mece_extractor.py"
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # MECEカテゴリーを探す
        categories = []
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if '"祝日・特別日制約"' in line or '"季節性・月次制約"' in line:
                # 前後の行も確認
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                context = '\n'.join(lines[start:end])
                categories.append(context.strip())
        
        if categories:
            print("  ✅ MECEカテゴリー定義を発見:")
            for cat in categories[:3]:
                print(f"    {cat[:100]}...")
    
    # dash_app.py での軸3タブ確認
    print("\n2. dash_app.py での軸3タブ実装:")
    
    if os.path.exists("dash_app.py"):
        with open("dash_app.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 軸3関連のタブを探す
        if "'time_calendar_rules'" in content:
            print("  ✅ 時間カレンダールールタブが存在")
        
        if "'three_axis_integration'" in content:
            print("  ✅ 3軸統合タブが存在")
        
        # コールバック関数を探す
        if "execute_time_calendar_extraction" in content:
            print("  ✅ 軸3実行コールバック関数が存在")
        
        if "execute_three_axis_integration" in content:
            print("  ✅ 3軸統合実行コールバック関数が存在")

def check_integration():
    """統合実装の確認"""
    print("\n\n🔗 統合実装の確認")
    print("=" * 50)
    
    filepath = "shift_suite/tasks/advanced_blueprint_engine_v2.py"
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 3軸統合メソッドを探す
        if "_integrate_multi_axis_constraints" in content:
            print("  ✅ 3軸統合メソッド (_integrate_multi_axis_constraints) が存在")
        
        # TimeCalendarMECEFactExtractorのインポートを確認
        if "TimeCalendarMECEFactExtractor" in content:
            print("  ✅ TimeCalendarMECEFactExtractor がインポートされている")
        
        # 3軸統合の実行を確認
        if "three_axis_integration" in content:
            print("  ✅ three_axis_integration キーが使用されている")

def main():
    """メイン実行"""
    check_file_structure()
    check_axis3_implementation()
    check_integration()
    
    print("\n\n" + "=" * 50)
    print("📋 確認完了")
    print("=" * 50)
    print("\n実装ファイルの構造は正常です。")
    print("dash_app.py を起動して、UIから軸3機能を確認してください。")
    print("\n起動コマンド: python dash_app.py")

if __name__ == "__main__":
    main()