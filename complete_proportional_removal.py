#!/usr/bin/env python3
"""
Complete Proportional Abolition Tab Removal
按分廃止タブの完全削除を実行
"""
import shutil
from pathlib import Path
from datetime import datetime
import re

def create_backup():
    """バックアップ作成"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"COMPLETE_REMOVAL_BACKUP_{timestamp}")
    backup_dir.mkdir(exist_ok=True)
    
    if Path('dash_app.py').exists():
        shutil.copy2('dash_app.py', backup_dir / 'dash_app.py.backup')
        print(f"Backup created: {backup_dir}")
        return backup_dir
    return None

def remove_proportional_tab_from_list():
    """タブリストから按分廃止タブを削除"""
    print("Removing proportional_abolition from tab list...")
    
    try:
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find and replace the tab list
        old_pattern = r"'overview', 'heatmap', 'shortage', 'proportional_abolition', 'optimization', 'leave',"
        new_pattern = "'overview', 'heatmap', 'shortage', 'optimization', 'leave',"
        
        new_content = content.replace(old_pattern, new_pattern)
        
        if new_content != content:
            with open('dash_app.py', 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("SUCCESS: Removed proportional_abolition from tab list")
            return True
        else:
            print("WARNING: Tab list pattern not found")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to remove from tab list - {e}")
        return False

def remove_proportional_tab_function():
    """create_proportional_abolition_tab関数を削除"""
    print("Removing create_proportional_abolition_tab function...")
    
    try:
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the function definition and remove it
        # Pattern to match the entire function
        pattern = r"def create_proportional_abolition_tab\(.*?\) -> html\.Div:.*?(?=\ndef [a-zA-Z_]|\nclass [a-zA-Z_]|\n@|\Z)"
        
        new_content = re.sub(pattern, 
                           "# REMOVED: create_proportional_abolition_tab function (integrated into shortage tab)\n", 
                           content, flags=re.DOTALL)
        
        if new_content != content:
            with open('dash_app.py', 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("SUCCESS: Removed create_proportional_abolition_tab function")
            return True
        else:
            print("WARNING: Function pattern not found")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to remove function - {e}")
        return False

def remove_proportional_callback():
    """initialize_proportional_abolition_content コールバックを削除"""
    print("Removing initialize_proportional_abolition_content callback...")
    
    try:
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find and remove the callback function
        pattern = r"def initialize_proportional_abolition_content\(.*?\):.*?(?=\ndef [a-zA-Z_]|\nclass [a-zA-Z_]|\n@|\Z)"
        
        new_content = re.sub(pattern, 
                           "# REMOVED: initialize_proportional_abolition_content callback (integrated into shortage tab)\n", 
                           content, flags=re.DOTALL)
        
        if new_content != content:
            with open('dash_app.py', 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("SUCCESS: Removed initialize_proportional_abolition_content callback")
            return True
        else:
            print("WARNING: Callback pattern not found")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to remove callback - {e}")
        return False

def verify_removal():
    """削除が完全かどうか確認"""
    print("Verifying complete removal...")
    
    try:
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for remaining references (excluding data access which is intentional)
        problematic_patterns = [
            r"create_proportional_abolition_tab",
            r"initialize_proportional_abolition_content", 
            r"'proportional_abolition'",  # in tab lists
        ]
        
        # Allowed patterns (these are OK for data access in integrated tab)
        allowed_patterns = [
            r"proportional_abolition_role_summary",
            r"proportional_abolition_organization_summary"
        ]
        
        issues = []
        for pattern in problematic_patterns:
            matches = re.findall(pattern, content)
            if matches:
                # Filter out allowed patterns
                filtered_matches = []
                for match in matches:
                    is_allowed = False
                    for allowed in allowed_patterns:
                        if allowed in match:
                            is_allowed = True
                            break
                    if not is_allowed:
                        filtered_matches.append(match)
                
                if filtered_matches:
                    issues.append(f"Pattern '{pattern}': {len(filtered_matches)} occurrences")
        
        if issues:
            print("WARNING: Found remaining issues:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("SUCCESS: Complete removal verified")
            return True
            
    except Exception as e:
        print(f"ERROR: Verification failed - {e}")
        return False

def test_syntax():
    """構文テスト"""
    try:
        import subprocess
        result = subprocess.run([
            'python', '-m', 'py_compile', 'dash_app.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("SUCCESS: Syntax check passed")
            return True
        else:
            print(f"ERROR: Syntax error - {result.stderr}")
            return False
    except Exception as e:
        print(f"ERROR: Syntax test failed - {e}")
        return False

def main():
    print("=== Complete Proportional Abolition Tab Removal ===")
    
    try:
        # Step 1: Create backup
        print("\nStep 1: Creating backup...")
        backup_dir = create_backup()
        if not backup_dir:
            raise Exception("Backup creation failed")
        
        # Step 2: Remove from tab list
        print("\nStep 2: Removing from tab list...")
        tab_removed = remove_proportional_tab_from_list()
        
        # Step 3: Remove function
        print("\nStep 3: Removing function...")
        function_removed = remove_proportional_tab_function()
        
        # Step 4: Remove callback
        print("\nStep 4: Removing callback...")
        callback_removed = remove_proportional_callback()
        
        # Step 5: Verify removal
        print("\nStep 5: Verifying complete removal...")
        removal_verified = verify_removal()
        
        # Step 6: Syntax check
        print("\nStep 6: Syntax check...")
        syntax_ok = test_syntax()
        
        # Summary
        changes_made = sum([tab_removed, function_removed, callback_removed])
        print(f"\n=== SUMMARY ===")
        print(f"Changes made: {changes_made}/3")
        print(f"Removal verified: {removal_verified}")
        print(f"Syntax check: {syntax_ok}")
        
        if changes_made >= 2 and removal_verified and syntax_ok:
            print("\nSUCCESS: Complete proportional abolition tab removal completed!")
            print(f"Backup location: {backup_dir}")
            print("\nWhat was removed:")
            print("- Proportional abolition tab from UI tab list")
            print("- create_proportional_abolition_tab function")
            print("- initialize_proportional_abolition_content callback")
            print("\nWhat was preserved:")
            print("- Data access to proportional_abolition_* files (for integrated tab)")
            print("- Core data processing logic")
            
            return True
        else:
            print(f"\nPARTIAL SUCCESS: Some issues remain")
            print(f"Consider rollback from: {backup_dir}")
            return False
        
    except Exception as e:
        print(f"\nERROR: Complete removal failed - {e}")
        if backup_dir:
            print(f"Rollback available: {backup_dir}")
        return False

if __name__ == "__main__":
    main()