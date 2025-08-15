#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ダッシュボード起動スクリプト
修正されたdash_app.pyを使用してダッシュボードを起動
"""

import sys
import os
from pathlib import Path

def check_requirements():
    """必要なパッケージの確認"""
    
    required_packages = ['dash', 'plotly', 'pandas', 'numpy']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"OK {package}: インストール済み")
        except ImportError:
            missing_packages.append(package)
            print(f"NG {package}: 未インストール")
    
    return missing_packages

def install_packages(packages):
    """必要なパッケージのインストール"""
    
    if not packages:
        return True
        
    print(f"\n📦 以下のパッケージをインストールします: {', '.join(packages)}")
    
    import subprocess
    
    try:
        # pipを使用してパッケージをインストール
        cmd = [sys.executable, '-m', 'pip', 'install'] + packages
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ パッケージのインストールが完了しました")
            return True
        else:
            print(f"❌ インストールエラー: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ インストール中にエラーが発生: {e}")
        return False

def start_dashboard():
    """ダッシュボードの起動"""
    
    print("🚀 修正されたダッシュボードを起動しています...\n")
    
    # 現在のディレクトリをPythonパスに追加
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    try:
        # dash_app.pyをインポート
        print("📄 dash_app.py を読み込み中...")
        import dash_app
        
        print("✅ dash_app.py の読み込み完了")
        print("\n🎯 期待される修正効果:")
        print("  - 不足時間: 26245h → 正常値")
        print("  - 職種別ヒートマップ: 正確な表示")
        print("  - エラーなし動作")
        
        print("\n🌐 ダッシュボードを起動しています...")
        print("   アドレス: http://localhost:8050")
        print("   ブラウザで上記URLにアクセスしてください")
        
        # Dashアプリケーションの起動
        if hasattr(dash_app, 'app'):
            # デバッグモードで起動
            dash_app.app.run_server(
                debug=False,  # 本番用はFalse
                host='127.0.0.1',
                port=8050,
                dev_tools_hot_reload=False
            )
        else:
            print("❌ dash_app.py内にappオブジェクトが見つかりません")
            
    except ImportError as e:
        print(f"❌ dash_app.pyのインポートエラー: {e}")
        print("\n原因:")
        print("  - 必要なパッケージが不足している可能性")
        print("  - dash_app.py内でエラーが発生している可能性")
        
    except Exception as e:
        print(f"❌ ダッシュボード起動エラー: {e}")
        print("\n🔧 トラブルシューティング:")
        print("  1. ポート8050が他のアプリケーションで使用されていないか確認")
        print("  2. ファイアウォール設定を確認")
        print("  3. 管理者権限で実行を試す")

def main():
    """メイン処理"""
    
    print("修正済みシフト分析ダッシュボード起動ツール")
    print("="*50)
    
    # 1. 必要パッケージの確認
    print("\n必要パッケージの確認中...")
    missing = check_requirements()
    
    # 2. 不足パッケージのインストール
    if missing:
        print(f"\n⚠️  {len(missing)}個のパッケージが不足しています")
        
        # ユーザーに確認（自動でYesとする）
        print("📦 自動インストールを実行します...")
        
        if install_packages(missing):
            print("✅ すべてのパッケージがインストールされました")
        else:
            print("❌ パッケージインストールに失敗しました")
            print("\n手動インストール方法:")
            print(f"  pip install {' '.join(missing)}")
            return
    
    # 3. ダッシュボードの起動
    print("\n" + "="*50)
    start_dashboard()

if __name__ == "__main__":
    main()