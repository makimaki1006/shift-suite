#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dash_app.py 永続的起動スクリプト
ユーザーが実際に使用できる状態を作成
"""

import os
import sys
import subprocess

def run_dash_system():
    """dash_app.pyを永続的に起動"""
    print("=" * 60)
    print("DASH SHIFT ANALYSIS SYSTEM")
    print("dash_app.py 起動中...")
    print("=" * 60)
    
    # 環境設定
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    try:
        # dash_app.pyを直接実行
        cmd = [
            sys.executable, "-c",
            """
import dash_app
print('Dash アプリケーション起動中...')
print('ブラウザで http://localhost:8080 にアクセスしてください')
print('終了するには Ctrl+C を押してください')
dash_app.app.run_server(
    debug=False,
    host='0.0.0.0',
    port=8080,
    use_reloader=False,
    dev_tools_hot_reload=False
)
"""
        ]
        
        print("起動コマンド実行中...")
        print("URL: http://localhost:8080")
        print("終了: Ctrl+C")
        print("-" * 60)
        
        # 実行
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\nシステムを終了しました")
    except Exception as e:
        print(f"エラー: {e}")
        print("\nトラブルシューティング:")
        print("1. pip install dash")
        print("2. python -c \"import dash_app\"")

if __name__ == "__main__":
    run_dash_system()