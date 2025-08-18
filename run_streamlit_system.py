#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Streamlitシフト分析システム起動スクリプト
"""

import subprocess
import sys
import os
from pathlib import Path

def run_streamlit_system():
    """Streamlitシフト分析システムを起動"""
    print("🚀 Streamlitシフト分析システムを起動中...")
    
    # 環境設定
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Streamlitアプリのパス
    app_path = Path(__file__).parent / "streamlit_shift_analysis.py"
    
    if not app_path.exists():
        print(f"❌ エラー: {app_path} が見つかりません")
        return False
    
    try:
        # Streamlit起動コマンド
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            str(app_path),
            "--server.headless", "true",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ]
        
        print(f"📋 起動コマンド: {' '.join(cmd)}")
        print("🌐 ブラウザで http://localhost:8501 にアクセスしてください")
        print("⚠️  終了するには Ctrl+C を押してください")
        print("=" * 60)
        
        # Streamlit実行
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n👋 システムを終了しました")
        return True
    except Exception as e:
        print(f"❌ 起動エラー: {e}")
        return False

if __name__ == "__main__":
    run_streamlit_system()