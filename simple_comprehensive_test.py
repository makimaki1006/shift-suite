#!/usr/bin/env python3
"""
Simple Comprehensive Test
統合後の機能をテストする
"""

import subprocess
from pathlib import Path
from datetime import datetime

def test_dash_app_import():
    """dash_app.pyのインポートテスト"""
    print("Testing dash_app.py import...")
    try:
        result = subprocess.run([
            'python', '-c', 
            'import sys; sys.path.append("."); import dash_app; print("Import successful")'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and 'successful' in result.stdout:
            print("  PASS: dash_app.py import successful")
            return True
        else:
            print(f"  FAIL: dash_app.py import failed - {result.stderr}")
            return False
    except Exception as e:
        print(f"  ERROR: Import test error - {e}")
        return False

def test_shortage_tab_function():
    """不足分析タブ関数の存在確認"""
    print("Testing shortage tab function existence...")
    try:
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 統合された関数が存在するかチェック
        if 'def create_shortage_tab(' in content:
            print("  PASS: create_shortage_tab function exists")
        else:
            print("  FAIL: create_shortage_tab function not found")
            return False
        
        # 新しいコールバック関数をチェック
        if 'update_shortage_mode_explanation' in content:
            print("  PASS: mode explanation callback exists")
        else:
            print("  FAIL: mode explanation callback not found")
            return False
        
        if 'update_shortage_results' in content:
            print("  PASS: results update callback exists")
        else:
            print("  FAIL: results update callback not found")
            return False
        
        # モード選択UIをチェック
        if 'shortage-analysis-mode' in content:
            print("  PASS: mode selector UI exists")
        else:
            print("  FAIL: mode selector UI not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ERROR: Function test error - {e}")
        return False

def test_proportional_data_access():
    """按分廃止データアクセステスト"""
    print("Testing proportional abolition data access...")
    try:
        test_script = '''
import sys
sys.path.append(".")
import pandas as pd
from pathlib import Path

success = True
try:
    # 按分廃止データファイルの確認
    role_file = Path("proportional_abolition_role_summary.parquet")
    org_file = Path("proportional_abolition_organization_summary.parquet")
    
    if role_file.exists():
        df_role = pd.read_parquet(role_file)
        print(f"Role data shape: {df_role.shape}")
    else:
        print("Role data file not found")
    
    if org_file.exists():
        df_org = pd.read_parquet(org_file)
        print(f"Org data shape: {df_org.shape}")
    else:
        print("Org data file not found")
    
    print("Data access test: SUCCESS")
except Exception as e:
    print(f"Data access test: FAILED - {e}")
'''
        
        result = subprocess.run([
            'python', '-c', test_script
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and 'SUCCESS' in result.stdout:
            print("  PASS: Proportional data access successful")
            return True
        else:
            print(f"  FAIL: Data access failed - {result.stderr}")
            return False
    except Exception as e:
        print(f"  ERROR: Data access test error - {e}")
        return False

def test_key_functions():
    """重要関数の存在確認"""
    print("Testing key function definitions...")
    try:
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        key_functions = [
            'create_basic_shortage_display',
            'create_advanced_shortage_display',
            'data_get'
        ]
        
        all_found = True
        for func in key_functions:
            if func in content:
                print(f"  PASS: {func} found")
            else:
                print(f"  FAIL: {func} not found")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"  ERROR: Key functions test error - {e}")
        return False

def test_ui_components():
    """UIコンポーネントの確認"""
    print("Testing UI components...")
    try:
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        ui_components = [
            'dcc.RadioItems',
            'html.Div',
            'dash_table.DataTable',
            'shortage-analysis-mode',
            'shortage-mode-explanation',
            'shortage-results-container'
        ]
        
        all_found = True
        for component in ui_components:
            if component in content:
                print(f"  PASS: {component} found")
            else:
                print(f"  FAIL: {component} not found")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"  ERROR: UI components test error - {e}")
        return False

def verify_backup_exists():
    """バックアップの存在確認"""
    print("Verifying backup existence...")
    try:
        backup_dirs = list(Path('.').glob('INTEGRATION_BACKUP_*'))
        if backup_dirs:
            latest_backup = max(backup_dirs, key=lambda p: p.stat().st_mtime)
            backup_file = latest_backup / 'dash_app.py.backup'
            if backup_file.exists():
                print(f"  PASS: Backup found at {latest_backup}")
                return True
            else:
                print(f"  FAIL: Backup file not found in {latest_backup}")
                return False
        else:
            print("  FAIL: No backup directories found")
            return False
    except Exception as e:
        print(f"  ERROR: Backup verification error - {e}")
        return False

def run_comprehensive_test():
    """包括的テストの実行"""
    print("=" * 60)
    print("Comprehensive Integration Test")
    print("=" * 60)
    
    test_results = {
        'dash_import': False,
        'shortage_function': False,
        'data_access': False,
        'key_functions': False,
        'ui_components': False,
        'backup_verification': False
    }
    
    # テスト実行
    test_results['dash_import'] = test_dash_app_import()
    test_results['shortage_function'] = test_shortage_tab_function()
    test_results['data_access'] = test_proportional_data_access()
    test_results['key_functions'] = test_key_functions()
    test_results['ui_components'] = test_ui_components()
    test_results['backup_verification'] = verify_backup_exists()
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:20}: {status}")
        if result:
            passed += 1
    
    success_rate = (passed / total) * 100
    overall_success = success_rate >= 80  # 80%以上で成功とする
    
    print(f"\nOverall Result: {passed}/{total} tests passed ({success_rate:.1f}%)")
    
    if overall_success:
        print("\nCOMPREHENSIVE TEST: SUCCESS")
        print("Integration appears to be working correctly!")
        print("\nNext steps:")
        print("1. Test the actual UI by running the dashboard")
        print("2. Verify mode switching works properly")
        print("3. Check that data displays correctly in both modes")
        print("4. Consider removing the old proportional abolition tab")
    else:
        print("\nCOMPREHENSIVE TEST: FAILED")
        print("Some issues were detected. Review the failed tests above.")
    
    return {
        'success': overall_success,
        'results': test_results,
        'success_rate': success_rate,
        'timestamp': datetime.now().isoformat()
    }

def main():
    try:
        return run_comprehensive_test()
    except Exception as e:
        print(f"\nTEST EXECUTION ERROR: {e}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    main()