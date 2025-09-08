#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dashアプリケーション起動スクリプト
"""

import sys
import webbrowser
import time
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("🚀 ShiftAnalysis Dashboard 起動")
print("=" * 60)

print("\n📦 アプリケーションを起動中...")

# dash_app.pyを直接実行
try:
    import dash_app
    
    print("✅ アプリケーションが起動しました！")
    print("\n" + "=" * 60)
    print("📌 アクセス方法:")
    print("=" * 60)
    print("🌐 ブラウザで以下のURLを開いてください:")
    print("   http://localhost:8050")
    print("\n📂 ZIPファイルアップロード方法:")
    print("   1. ブラウザでアプリを開く")
    print("   2. 「データをアップロード」エリアにZIPファイルをドラッグ＆ドロップ")
    print("   3. 自動的にデータが読み込まれ、タブが表示されます")
    print("\n⌨️ 終了方法: Ctrl+C")
    print("=" * 60)
    
    # ブラウザを自動で開く（オプション）
    time.sleep(2)
    webbrowser.open('http://localhost:8050')
    
    # アプリを実行
    dash_app.app.run_server(debug=False, port=8050, host='0.0.0.0')
    
except KeyboardInterrupt:
    print("\n\n🛑 アプリケーションを終了しています...")
    print("✅ 正常に終了しました")
except Exception as e:
    print(f"❌ エラーが発生しました: {e}")
    import traceback
    traceback.print_exc()