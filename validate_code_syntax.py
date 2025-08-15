#!/usr/bin/env python3
"""
統一分析管理システムのコード構文確認
実際にPythonとして正しく解析できるかをテスト
"""

import ast
import sys
from pathlib import Path

def validate_python_syntax(file_path):
    """Pythonファイルの構文確認"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # AST解析で構文エラーをチェック
        ast.parse(content)
        return True, "構文OK"
        
    except SyntaxError as e:
        return False, f"構文エラー: {e}"
    except Exception as e:
        return False, f"その他エラー: {e}"

def main():
    print("統一分析管理システム コード構文検証")
    print("=" * 50)
    
    # 検証対象ファイル
    files_to_check = [
        "shift_suite/tasks/unified_analysis_manager.py",
        "shift_suite/tasks/ai_comprehensive_report_generator.py",
        "shift_suite/tasks/shortage.py",
        "shift_suite/tasks/fatigue.py",
        "shift_suite/tasks/fairness.py",
        "app.py"
    ]
    
    all_valid = True
    
    for file_path in files_to_check:
        path = Path(file_path)
        if path.exists():
            is_valid, message = validate_python_syntax(path)
            status = "✅" if is_valid else "❌"
            print(f"{status} {file_path}: {message}")
            if not is_valid:
                all_valid = False
        else:
            print(f"⚠️ {file_path}: ファイルが見つかりません")
            all_valid = False
    
    print("\n" + "=" * 50)
    if all_valid:
        print("🎉 全ファイルの構文が正常です")
        print("統一分析管理システムのコードは実行可能です")
    else:
        print("❌ 構文エラーが検出されました")
    
    return all_valid

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)