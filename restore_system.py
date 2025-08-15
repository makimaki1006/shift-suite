#!/usr/bin/env python3
"""
システムリストアスクリプト
"""

import os
import json
import zipfile
import shutil
import datetime

class SystemRestore:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.backup_path = os.path.join(self.base_path, "backups")
    
    def list_backups(self):
        """利用可能なバックアップ一覧表示"""
        backup_files = []
        for root, dirs, files in os.walk(self.backup_path):
            for file in files:
                if file.endswith('_info.json'):
                    info_path = os.path.join(root, file)
                    try:
                        with open(info_path, 'r') as f:
                            backup_info = json.load(f)
                        backup_files.append(backup_info)
                    except:
                        continue
        
        return sorted(backup_files, key=lambda x: x['timestamp'], reverse=True)
    
    def restore_backup(self, backup_id, restore_path=None):
        """指定されたバックアップからリストア"""
        if not restore_path:
            restore_path = self.base_path
        
        print(f"リストア開始: {backup_id}")
        
        # バックアップ情報取得
        info_files = []
        for root, dirs, files in os.walk(self.backup_path):
            for file in files:
                if file.startswith(backup_id) and file.endswith('_info.json'):
                    info_files.append(os.path.join(root, file))
        
        if not info_files:
            print(f"エラー: バックアップ {backup_id} が見つかりません")
            return False
        
        info_path = info_files[0]
        with open(info_path, 'r') as f:
            backup_info = json.load(f)
        
        # 各ターゲットをリストア
        total_restored = 0
        for target in backup_info['targets']:
            backup_file = target['backup_file']
            if os.path.exists(backup_file):
                print(f"リストア中: {target['target_name']}")
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    zipf.extractall(restore_path)
                total_restored += target['file_count']
            else:
                print(f"警告: バックアップファイルが見つかりません: {backup_file}")
        
        print(f"リストア完了: {total_restored}ファイル")
        return True

if __name__ == "__main__":
    import sys
    restore = SystemRestore()
    
    if len(sys.argv) < 2:
        print("利用可能なバックアップ:")
        backups = restore.list_backups()
        for backup in backups[:10]:  # 最新10件
            print(f"  {backup['backup_id']} ({backup['timestamp']})")
    else:
        backup_id = sys.argv[1]
        restore_path = sys.argv[2] if len(sys.argv) > 2 else None
        restore.restore_backup(backup_id, restore_path)
