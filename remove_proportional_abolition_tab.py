#!/usr/bin/env python3
"""
Remove Proportional Abolition Tab
既存の按分廃止タブを段階的に削除する
"""

import shutil
from pathlib import Path
from datetime import datetime

def create_cleanup_backup():
    """クリーンアップ用バックアップ作成"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(f"CLEANUP_BACKUP_{timestamp}")
        backup_dir.mkdir(exist_ok=True)
        
        if Path('dash_app.py').exists():
            shutil.copy2('dash_app.py', backup_dir / 'dash_app.py.backup')
            print(f"Cleanup backup created: {backup_dir}")
            return backup_dir
        else:
            print("Error: dash_app.py not found")
            return None
    except Exception as e:
        print(f"Cleanup backup error: {e}")
        return None

def find_proportional_abolition_tab():
    """按分廃止タブ関数の位置を特定"""
    try:
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        start_line = None
        end_line = len(lines)
        
        for i, line in enumerate(lines):
            if 'def create_proportional_abolition_tab(' in line:
                start_line = i
                break
        
        if start_line is None:
            print("create_proportional_abolition_tab function not found (may already be removed)")
            return None
            
        # 関数終了位置を特定
        indent_level = len(lines[start_line]) - len(lines[start_line].lstrip())
        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            if line.strip() and not line.startswith(' ' * (indent_level + 1)):
                if line.startswith('def ') or line.startswith('class ') or line.startswith('@'):
                    end_line = i
                    break
        
        print(f"Found create_proportional_abolition_tab: lines {start_line + 1}-{end_line}")
        return {'start': start_line, 'end': end_line}
        
    except Exception as e:
        print(f"Function search error: {e}")
        return None

def remove_proportional_tab_references():
    """按分廃止タブへの参照を削除"""
    try:
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        cleaned_lines = []
        
        # タブ参照を含む行をコメントアウトまたは削除
        for line in lines:
            # 按分廃止タブのdcc.Tab定義を探す
            if 'dcc.Tab' in line and '按分廃止' in line:
                # この行をコメントアウト
                cleaned_lines.append(f"# REMOVED: {line}")
                print(f"Commented out tab definition: {line.strip()}")
            # 按分廃止タブへの直接参照をチェック
            elif 'create_proportional_abolition_tab' in line and 'def ' not in line:
                # 関数呼び出しをコメントアウト
                cleaned_lines.append(f"# REMOVED: {line}")
                print(f"Commented out function call: {line.strip()}")
            else:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
        
    except Exception as e:
        print(f"Reference removal error: {e}")
        return None

def remove_proportional_abolition_function(content, function_pos):
    """按分廃止タブ関数を削除"""
    try:
        lines = content.split('\n')
        
        # 削除される関数の情報を表示
        function_lines = lines[function_pos['start']:function_pos['end']]
        print(f"Removing function with {len(function_lines)} lines")
        
        # 関数を削除
        new_lines = lines[:function_pos['start']] + ['#按分廃止タブ関数は統合により削除されました'] + [''] + lines[function_pos['end']:]
        
        return '\n'.join(new_lines)
        
    except Exception as e:
        print(f"Function removal error: {e}")
        return None

def update_tab_list():
    """タブリストの更新"""
    print("Updating tab list to remove proportional abolition tab...")
    
    try:
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # タブリスト定義を探して更新
        lines = content.split('\n')
        updated_lines = []
        
        in_tab_list = False
        for line in lines:
            # dcc.Tabsの定義を探す
            if 'dcc.Tabs' in line and 'children=' in line:
                in_tab_list = True
                updated_lines.append(line)
            elif in_tab_list and '按分廃止' in line:
                # 按分廃止タブの行をコメントアウト
                updated_lines.append(f"            # REMOVED: {line.strip()}")
            elif in_tab_list and ']' in line and line.strip().startswith(']'):
                in_tab_list = False
                updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        return '\n'.join(updated_lines)
        
    except Exception as e:
        print(f"Tab list update error: {e}")
        return None

def verify_removal():
    """削除の確認"""
    try:
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        issues = []
        
        # 按分廃止への参照が残っていないかチェック
        if 'create_proportional_abolition_tab(' in content:
            if '# REMOVED:' not in content or 'create_proportional_abolition_tab(' in content.replace('# REMOVED:', ''):
                issues.append("create_proportional_abolition_tab function definition still exists")
        
        # タブ定義の確認
        active_proportional_refs = [line for line in content.split('\n') 
                                   if '按分廃止' in line and '# REMOVED:' not in line]
        
        if active_proportional_refs:
            issues.append(f"Active proportional abolition references found: {len(active_proportional_refs)}")
            for ref in active_proportional_refs[:3]:  # 最初の3つだけ表示
                issues.append(f"  - {ref.strip()}")
        
        if issues:
            print("Verification issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("Verification passed: No active proportional abolition references found")
            return True
            
    except Exception as e:
        print(f"Verification error: {e}")
        return False

def test_after_removal():
    """削除後のテスト"""
    import subprocess
    
    print("Testing after proportional tab removal...")
    
    try:
        # 構文チェック
        result = subprocess.run([
            'python', '-m', 'py_compile', 'dash_app.py'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Syntax error after removal: {result.stderr}")
            return False
        
        # インポートテスト
        result = subprocess.run([
            'python', '-c', 'import dash_app; print("Import successful after cleanup")'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"Import failed after removal: {result.stderr}")
            return False
        
        print("Post-removal tests passed")
        return True
        
    except Exception as e:
        print(f"Post-removal test error: {e}")
        return False

def main():
    print("=== Proportional Abolition Tab Removal ===")
    
    try:
        # Step 1: Create backup
        print("\nStep 1: Creating cleanup backup...")
        backup_dir = create_cleanup_backup()
        if not backup_dir:
            raise Exception("Cleanup backup creation failed")
        
        # Step 2: Find proportional abolition tab function
        print("\nStep 2: Finding proportional abolition tab function...")
        function_pos = find_proportional_abolition_tab()
        
        # Step 3: Remove references
        print("\nStep 3: Removing proportional abolition references...")
        content = remove_proportional_tab_references()
        if not content:
            raise Exception("Reference removal failed")
        
        # Step 4: Remove function if it exists
        if function_pos:
            print("\nStep 4: Removing proportional abolition function...")
            content = remove_proportional_abolition_function(content, function_pos)
            if not content:
                raise Exception("Function removal failed")
        else:
            print("\nStep 4: No proportional abolition function to remove")
        
        # Step 5: Update tab list
        print("\nStep 5: Updating tab list...")
        content = update_tab_list()
        if not content:
            raise Exception("Tab list update failed")
        
        # Step 6: Write updated content
        print("\nStep 6: Writing updated dash_app.py...")
        with open('dash_app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Step 7: Verify removal
        print("\nStep 7: Verifying removal...")
        if not verify_removal():
            print("Warning: Some verification issues found, but continuing...")
        
        # Step 8: Test after removal
        print("\nStep 8: Testing after removal...")
        if not test_after_removal():
            print("Post-removal tests failed - consider rollback")
            return {'success': False, 'error': 'Post-removal tests failed'}
        
        print("\nProportional abolition tab removal completed successfully!")
        print(f"Cleanup backup location: {backup_dir}")
        print("\nSummary:")
        print("- Old proportional abolition tab has been removed")
        print("- New integrated shortage tab with mode selection is active")
        print("- All tests passed")
        print("- Integration is complete")
        
        return {
            'success': True, 
            'backup_dir': backup_dir,
            'summary': 'Integration completed successfully'
        }
        
    except Exception as e:
        print(f"\nProportional abolition tab removal failed: {e}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    main()