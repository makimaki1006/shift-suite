#!/usr/bin/env python3
"""
バックアップ検証スクリプト
"""

import os
import json
import hashlib
import zipfile
import datetime

def verify_backups():
    backup_path = os.path.join(os.path.dirname(__file__), "backups")
    
    verification_results = {
        'timestamp': datetime.datetime.now().isoformat(),
        'verified_backups': 0,
        'failed_verifications': 0,
        'results': []
    }
    
    # バックアップファイル検証
    for root, dirs, files in os.walk(backup_path):
        for file in files:
            if file.endswith('_info.json'):
                info_path = os.path.join(root, file)
                result = verify_single_backup(info_path)
                verification_results['results'].append(result)
                
                if result['status'] == 'success':
                    verification_results['verified_backups'] += 1
                else:
                    verification_results['failed_verifications'] += 1
    
    # 結果保存
    result_path = os.path.join(backup_path, f"verification_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(result_path, 'w') as f:
        json.dump(verification_results, f, indent=2)
    
    print(f"検証完了: {verification_results['verified_backups']}成功, {verification_results['failed_verifications']}失敗")
    return verification_results

def verify_single_backup(info_path):
    try:
        with open(info_path, 'r') as f:
            backup_info = json.load(f)
        
        backup_id = backup_info['backup_id']
        results = []
        
        for target in backup_info['targets']:
            backup_file = target['backup_file']
            expected_checksum = target['checksum']
            
            if os.path.exists(backup_file):
                # チェックサム検証
                actual_checksum = calculate_checksum(backup_file)
                if actual_checksum == expected_checksum:
                    results.append({'target': target['target_name'], 'checksum': 'ok'})
                else:
                    results.append({'target': target['target_name'], 'checksum': 'failed'})
            else:
                results.append({'target': target['target_name'], 'checksum': 'file_missing'})
        
        return {
            'backup_id': backup_id,
            'status': 'success' if all(r['checksum'] == 'ok' for r in results) else 'failed',
            'details': results
        }
        
    except Exception as e:
        return {
            'backup_id': 'unknown',
            'status': 'error',
            'error': str(e)
        }

def calculate_checksum(file_path):
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

if __name__ == "__main__":
    verify_backups()
