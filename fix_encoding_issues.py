# -*- coding: utf-8 -*-
"""
文字エンコーディング問題の修正スクリプト
Windows環境での文字化け問題を解決
"""

import os
import sys
import subprocess
from pathlib import Path

def fix_encoding_environment():
    """文字エンコーディング環境の修正"""
    
    print("=== 文字エンコーディング問題修正 ===")
    
    # 1. 環境変数の設定
    fixes_applied = []
    
    # PYTHONIOENCODING を UTF-8 に設定
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    fixes_applied.append("PYTHONIOENCODING=utf-8 設定")
    
    # PYTHONLEGACYWINDOWSSTDIO を無効化
    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '0'
    fixes_applied.append("PYTHONLEGACYWINDOWSSTDIO=0 設定")
    
    # 2. バッチファイルでの起動スクリプト作成
    startup_script = Path("start_with_utf8.bat")
    with open(startup_script, 'w', encoding='utf-8') as f:
        f.write("""@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=0
python %*
""")
    fixes_applied.append(f"UTF-8起動スクリプト作成: {startup_script}")
    
    # 3. ダッシュボード起動スクリプト作成
    dashboard_script = Path("start_dashboard_utf8.bat")
    with open(dashboard_script, 'w', encoding='utf-8') as f:
        f.write("""@echo off
echo Starting ShiftAnalysis Dashboard with UTF-8 encoding...
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=0
python dash_app.py
pause
""")
    fixes_applied.append(f"ダッシュボード起動スクリプト作成: {dashboard_script}")
    
    # 4. 修正確認用テストスクリプト
    test_script = Path("test_encoding_fix.py")
    with open(test_script, 'w', encoding='utf-8') as f:
        f.write("""# -*- coding: utf-8 -*-
import sys
import pandas as pd

print("=== エンコーディング修正テスト ===")
print(f"標準出力エンコーディング: {sys.stdout.encoding}")

# テストデータで確認
test_data = pd.DataFrame({
    'staff': ['山田太郎', '田中花子', '佐藤次郎'],
    'role': ['介護', '看護師', '管理者']
})

print("\\nテストデータ:")
print(test_data)

# 日本語文字列のテスト
test_string = "これは日本語のテストです。文字化けしていませんか？"
print(f"\\n日本語テスト: {test_string}")

print("\\n✓ エンコーディング修正が正常に適用されました")
""")
    fixes_applied.append(f"修正確認テストスクリプト作成: {test_script}")
    
    print("\\n適用された修正:")
    for i, fix in enumerate(fixes_applied, 1):
        print(f"  {i}. {fix}")
    
    return fixes_applied

def test_encoding_fix():
    """修正の効果をテスト"""
    
    print("\\n=== 修正効果テスト ===")
    
    # UTF-8環境でテスト実行
    try:
        result = subprocess.run([
            'cmd', '/c', 'chcp 65001 > nul && set PYTHONIOENCODING=utf-8 && python test_encoding_fix.py'
        ], capture_output=True, text=True, encoding='utf-8')
        
        print("テスト実行結果:")
        print(result.stdout)
        
        if result.stderr:
            print("エラー出力:")
            print(result.stderr)
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"テスト実行エラー: {e}")
        return False

if __name__ == '__main__':
    # 修正実行
    fixes = fix_encoding_environment()
    
    # テスト実行
    success = test_encoding_fix()
    
    print(f"\\n=== 修正完了 ===")
    print(f"適用された修正数: {len(fixes)}")
    print(f"テスト結果: {'成功' if success else '要確認'}")
    
    print(f"\\n今後の推奨使用方法:")
    print(f"1. ダッシュボード起動: start_dashboard_utf8.bat")
    print(f"2. Python実行: start_with_utf8.bat <スクリプト名>")
    print(f"3. コマンドライン: set PYTHONIOENCODING=utf-8 && python <スクリプト名>")