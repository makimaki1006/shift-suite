#!/usr/bin/env python3
"""
Simple UI Fix
包括的UI問題の修正を実行する（シンプル版）
"""

import shutil
from pathlib import Path
from datetime import datetime
import subprocess
import re

def create_backup():
    """バックアップ作成"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"UI_FIX_BACKUP_{timestamp}")
    backup_dir.mkdir(exist_ok=True)
    
    if Path('dash_app.py').exists():
        shutil.copy2('dash_app.py', backup_dir / 'dash_app.py.backup')
        print(f"Backup created: {backup_dir}")
        return backup_dir
    return None

def remove_proportional_tab():
    """按分廃止タブの削除"""
    try:
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 按分廃止タブの定義を削除
        content = re.sub(
            r"dcc\.Tab\(label='\[TARGET\] 按分廃止.*?proportional_abolition.*?\),",
            '# REMOVED: 按分廃止タブ（統合により削除）',
            content,
            flags=re.DOTALL
        )
        
        with open('dash_app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("Proportional abolition tab removed from UI")
        return True
        
    except Exception as e:
        print(f"Error removing proportional tab: {e}")
        return False

def improve_tab_labels():
    """タブラベルの改善"""
    try:
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # タブラベルの改善
        replacements = [
            (r"label='\[WARNING\] 不足分析'", "label='不足分析'"),
            (r"label='\[CHART\] 概要'", "label='概要'"),
            (r"label='\[GRAPH\] 需要予測'", "label='需要予測'"),
            (r"label='\[BOARD\] 基準乖離分析'", "label='基準乖離分析'"),
        ]
        
        changes = 0
        for pattern, replacement in replacements:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                content = new_content
                changes += 1
        
        if changes > 0:
            with open('dash_app.py', 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Tab labels improved: {changes} changes")
        
        return True
        
    except Exception as e:
        print(f"Error improving tab labels: {e}")
        return False

def test_syntax():
    """構文テスト"""
    try:
        result = subprocess.run([
            'python', '-m', 'py_compile', 'dash_app.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Syntax check passed")
            return True
        else:
            print(f"Syntax error: {result.stderr}")
            return False
    except Exception as e:
        print(f"Syntax test error: {e}")
        return False

def test_import():
    """インポートテスト"""
    try:
        result = subprocess.run([
            'python', '-c', 'import dash_app; print("Import successful")'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("Import test passed")
            return True
        else:
            print(f"Import failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"Import test error: {e}")
        return False

def main():
    print("=== Simple UI Fix Execution ===")
    
    try:
        # Step 1: Backup
        print("\nStep 1: Creating backup...")
        backup_dir = create_backup()
        if not backup_dir:
            raise Exception("Backup creation failed")
        
        # Step 2: Remove proportional tab
        print("\nStep 2: Removing proportional abolition tab...")
        if not remove_proportional_tab():
            raise Exception("Proportional tab removal failed")
        
        # Step 3: Improve tab labels
        print("\nStep 3: Improving tab labels...")
        if not improve_tab_labels():
            raise Exception("Tab label improvement failed")
        
        # Step 4: Syntax check
        print("\nStep 4: Syntax check...")
        if not test_syntax():
            print("Syntax error detected - consider rollback")
            raise Exception("Syntax errors found")
        
        # Step 5: Import test
        print("\nStep 5: Import test...")
        if not test_import():
            print("Import failed - consider rollback")
            raise Exception("Import test failed")
        
        print("\nSimple UI fix completed successfully!")
        print(f"Backup location: {backup_dir}")
        print("\nChanges made:")
        print("- Removed proportional abolition tab from UI")
        print("- Cleaned up tab labels")
        print("- Verified syntax and imports")
        print("\nNext steps:")
        print("1. Test the dashboard UI")
        print("2. Verify shortage analysis tab works in both modes")
        print("3. Confirm no errors in browser console")
        
        return {'success': True, 'backup_dir': backup_dir}
        
    except Exception as e:
        print(f"\nSimple UI fix failed: {e}")
        if backup_dir:
            print(f"Restore from backup: {backup_dir}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    main()