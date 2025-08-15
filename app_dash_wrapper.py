#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
シンプルなアプリケーション起動スクリプト
修正されたdash_app.pyを起動します
"""

import sys
import os
from pathlib import Path

# 現在のディレクトリをPythonパスに追加
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """ダッシュボードアプリケーションを起動"""
    
    print("📊 シフト分析ダッシュボードを起動しています...")
    print("🔧 修正されたコードで実行されます\n")
    
    try:
        # dash_app.pyをインポートして実行
        import dash_app
        
        print("✅ dash_app.py を正常に読み込みました")
        print("🌐 ブラウザでダッシュボードにアクセスしてください")
        print("📝 アドレス: http://localhost:8050")
        print("\n🎯 修正内容:")
        print("  - 不足時間の正常化（26245h → 適正値）")
        print("  - 職種別ヒートマップの正確な表示") 
        print("  - エラーのないスムーズな動作")
        
        # アプリケーションを起動
        if hasattr(dash_app, 'app'):
            dash_app.app.run_server(debug=True, host='0.0.0.0', port=8050)
        else:
            print("❌ dash_app.pyにappオブジェクトが見つかりません")
            
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        print("\n🔧 対応方法:")
        print("  1. 必要なパッケージをインストール:")
        print("     pip install dash plotly pandas numpy")
        print("  2. 仮想環境を有効化していることを確認")
        print("  3. dash_app.pyが存在することを確認")
        
    except Exception as e:
        print(f"❌ 起動エラー: {e}")
        print("\n🔧 対応方法:")
        print("  1. ログファイルを確認")
        print("  2. 必要なデータファイルが存在することを確認")
        print("  3. ポート8050が使用可能であることを確認")

if __name__ == "__main__":
    main()