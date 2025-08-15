#!/usr/bin/env python3
"""
dash_app.pyテスト用起動スクリプト
適切なCURRENT_SCENARIO_DIRを設定してからアプリケーションを起動
"""

import os
import sys
from pathlib import Path

# 必要なパスを設定
SHIFT_DIR = "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析"
RESULTS_DIR = "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/temp_analysis_results/out_p25_based"

def main():
    """メイン実行関数"""
    print("=== dash_app.py Test Startup ===")
    
    # ディレクトリの確認
    if not Path(SHIFT_DIR).exists():
        print(f"Error: Shift directory not found: {SHIFT_DIR}")
        return 1
    
    if not Path(RESULTS_DIR).exists():
        print(f"Error: Results directory not found: {RESULTS_DIR}")
        return 1
    
    # 作業ディレクトリを変更
    os.chdir(SHIFT_DIR)
    print(f"Changed directory to: {SHIFT_DIR}")
    
    # 分析結果ディレクトリを環境変数として設定（オプション）
    os.environ['ANALYSIS_RESULTS_DIR'] = RESULTS_DIR
    print(f"Set ANALYSIS_RESULTS_DIR: {RESULTS_DIR}")
    
    try:
        # dash_app.pyをインポート（実際の実行は行わない）
        print("Attempting to import dash_app...")
        
        # Pythonパスに現在のディレクトリを追加
        sys.path.insert(0, SHIFT_DIR)
        
        # ここで実際にインポートを試すが、今回は依存関係が不足しているため
        # シンタックスチェックのみ実行
        dash_app_path = Path(SHIFT_DIR) / "dash_app.py"
        with open(dash_app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        compile(content, str(dash_app_path), 'exec')
        print("✅ dash_app.py syntax check passed")
        
        # 実際の起動コマンドを表示
        print("\n=== To start the dashboard manually ===")
        print(f"cd '{SHIFT_DIR}'")
        print("python3 dash_app.py")
        print("Then open http://127.0.0.1:8050 in your browser")
        
        # CURRENT_SCENARIO_DIRの設定方法を表示
        print("\n=== Manual CURRENT_SCENARIO_DIR setup ===")
        print("In the dashboard interface:")
        print(f"1. Upload or select the analysis results from: {RESULTS_DIR}")
        print("2. Verify that data loads correctly")
        print("3. Check the browser console for [ROLE_DYNAMIC_NEED] log messages")
        
        return 0
        
    except Exception as e:
        print(f"Error during import test: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
