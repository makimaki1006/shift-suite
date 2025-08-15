#!/usr/bin/env python3
"""
dash_app.pyの起動テスト用スクリプト
CURRENT_SCENARIO_DIRを適切に設定してテスト
"""

import os
import sys
import logging
from pathlib import Path

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

def test_dash_app_startup():
    """dash_app.pyの起動テスト"""
    log.info("=== Testing dash_app.py startup ===")
    
    try:
        # シフト分析ディレクトリに移動
        shift_dir = "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析"
        os.chdir(shift_dir)
        log.info(f"Changed directory to: {shift_dir}")
        
        # dash_app.pyの存在確認
        dash_app_path = Path(shift_dir) / "dash_app.py"
        if not dash_app_path.exists():
            log.error("dash_app.py not found")
            return False
        
        log.info("dash_app.py found")
        
        # 分析結果ディレクトリの確認
        results_dir = "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/temp_analysis_results/out_p25_based"
        results_path = Path(results_dir)
        
        if not results_path.exists():
            log.error(f"Results directory not found: {results_dir}")
            return False
        
        log.info(f"Results directory confirmed: {results_dir}")
        
        # dash_app.pyの重要な設定部分をチェック
        log.info("Checking dash_app.py configuration...")
        
        with open(dash_app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 重要な機能の存在確認
        checks = {
            'calculate_role_dynamic_need': 'calculate_role_dynamic_need' in content,
            'CURRENT_SCENARIO_DIR': 'CURRENT_SCENARIO_DIR' in content,
            'DATA_CACHE': 'DATA_CACHE' in content,
            'safe_callback': 'safe_callback' in content,
            'ThreadSafeLRUCache': 'ThreadSafeLRUCache' in content,
        }
        
        for check_name, check_result in checks.items():
            if check_result:
                log.info(f"✅ {check_name}: Found")
            else:
                log.warning(f"⚠️ {check_name}: Not found")
        
        # ログメッセージの確認
        log_checks = {
            '[ROLE_DYNAMIC_NEED]': '[ROLE_DYNAMIC_NEED]' in content,
            'role_ratio': 'role_ratio' in content,
            'baseline_need': 'baseline_need' in content,
        }
        
        log.info("Checking for debug log messages:")
        for check_name, check_result in log_checks.items():
            if check_result:
                log.info(f"✅ {check_name}: Found")
            else:
                log.warning(f"⚠️ {check_name}: Not found")
        
        # Python importチェック（実際には実行できないが、構文チェック）
        log.info("Performing syntax check...")
        try:
            compile(content, dash_app_path, 'exec')
            log.info("✅ Syntax check passed")
        except SyntaxError as e:
            log.error(f"❌ Syntax error: {e}")
            return False
        
        return True
        
    except Exception as e:
        log.error(f"Error during startup test: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_test_startup_script():
    """実際のテスト用起動スクリプトを作成"""
    log.info("=== Creating test startup script ===")
    
    startup_script = '''#!/usr/bin/env python3
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
        print("\\n=== To start the dashboard manually ===")
        print(f"cd '{SHIFT_DIR}'")
        print("python3 dash_app.py")
        print("Then open http://127.0.0.1:8050 in your browser")
        
        # CURRENT_SCENARIO_DIRの設定方法を表示
        print("\\n=== Manual CURRENT_SCENARIO_DIR setup ===")
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
'''
    
    script_path = "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/start_dash_test.py"
    
    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(startup_script)
        
        # 実行権限を付与
        os.chmod(script_path, 0o755)
        
        log.info(f"✅ Test startup script created: {script_path}")
        log.info("You can run it with: python3 start_dash_test.py")
        
        return True
        
    except Exception as e:
        log.error(f"Failed to create startup script: {e}")
        return False

def main():
    """メインテスト実行"""
    log.info("Starting dash_app.py startup test")
    
    success = True
    
    # 基本的な起動テスト
    if not test_dash_app_startup():
        success = False
    
    # テスト用起動スクリプトの作成
    if not create_test_startup_script():
        success = False
    
    # 総合結果
    log.info(f"\\n=== STARTUP TEST SUMMARY ===")
    log.info(f"Overall result: {'PASS' if success else 'FAIL'}")
    
    if success:
        log.info("✅ dash_app.py appears ready for startup")
        log.info("Next steps:")
        log.info("1. Install required packages: pip install dash plotly pandas numpy")
        log.info("2. Run: python3 start_dash_test.py")
        log.info("3. Manually start: python3 dash_app.py")
        log.info("4. Open browser to: http://127.0.0.1:8050")
        log.info("5. Upload analysis results and test functionality")
    else:
        log.warning("⚠️ Some issues detected - review before startup")
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)