#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ファイル整理分析 - 必須・一時・不要ファイルの分類
"""

import os
from pathlib import Path
import json
from datetime import datetime

def analyze_files():
    """ファイルを分析して分類"""
    
    base_dir = Path(".")
    all_files = []
    
    # 全ファイルを収集
    for file_path in base_dir.rglob("*"):
        if file_path.is_file():
            stat = file_path.stat()
            all_files.append({
                'path': str(file_path),
                'name': file_path.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                'extension': file_path.suffix.lower()
            })
    
    # 分類定義
    classification = {
        'essential': {
            'description': '必須ファイル（プロジェクトの核心）',
            'files': [],
            'patterns': [
                'app.py',
                'dash_app.py', 
                'streamlit_shift_analysis.py',
                'shift_suite/',
                'extracted_results/',
                'requirements.txt',
                'README.md',
                '.gitignore'
            ]
        },
        'data_files': {
            'description': 'データファイル（実際のデータ）',
            'files': [],
            'patterns': [
                '.xlsx',
                '.csv', 
                '.parquet',
                'テスト用データ',
                'extracted_results'
            ]
        },
        'backup_files': {
            'description': 'バックアップファイル（重要だが複数ある）',
            'files': [],
            'patterns': [
                '.backup',
                '_backup_',
                'BACKUP_',
                '.bak',
                'backup_'
            ]
        },
        'temporary_debug': {
            'description': '一時的なデバッグファイル（削除可能）',
            'files': [],
            'patterns': [
                'debug_',
                'test_',
                'fix_',
                'emergency_',
                'temp_',
                'simple_',
                'check_',
                'verify_'
            ]
        },
        'documentation': {
            'description': 'ドキュメント・レポート',
            'files': [],
            'patterns': [
                '.md',
                'REPORT',
                'SUMMARY',
                'ANALYSIS',
                'GUIDE',
                '.txt'
            ]
        },
        'logs': {
            'description': 'ログファイル（削除可能）',
            'files': [],
            'patterns': [
                '.log',
                'log_',
                '_log'
            ]
        },
        'config': {
            'description': '設定ファイル',
            'files': [],
            'patterns': [
                'config',
                '.json',
                '.toml',
                '.bat',
                '.sh'
            ]
        },
        'assets': {
            'description': 'アセット・スタイル',
            'files': [],
            'patterns': [
                'assets/',
                '.css',
                '.js',
                '.html'
            ]
        }
    }
    
    # ファイルを分類
    for file_info in all_files:
        file_path = file_info['path']
        file_name = file_info['name']
        
        classified = False
        
        # 各カテゴリのパターンをチェック
        for category, cat_info in classification.items():
            for pattern in cat_info['patterns']:
                if pattern in file_path or pattern in file_name:
                    cat_info['files'].append(file_info)
                    classified = True
                    break
            if classified:
                break
        
        # 分類されなかったファイルは 'other' に
        if not classified:
            if 'other' not in classification:
                classification['other'] = {
                    'description': 'その他・未分類',
                    'files': []
                }
            classification['other']['files'].append(file_info)
    
    return classification

def generate_cleanup_plan(classification):
    """クリーンアップ計画を生成"""
    
    cleanup_plan = {
        'safe_to_delete': [],
        'candidates_for_deletion': [],
        'keep_essential': [],
        'archive_candidates': []
    }
    
    # 安全に削除可能
    safe_delete_categories = ['temporary_debug', 'logs']
    for category in safe_delete_categories:
        if category in classification:
            for file_info in classification[category]['files']:
                cleanup_plan['safe_to_delete'].append(file_info['path'])
    
    # 削除候補（確認要）
    candidate_categories = ['backup_files']
    for category in candidate_categories:
        if category in classification:
            for file_info in classification[category]['files']:
                cleanup_plan['candidates_for_deletion'].append(file_info['path'])
    
    # 保持必須
    essential_categories = ['essential', 'data_files']
    for category in essential_categories:
        if category in classification:
            for file_info in classification[category]['files']:
                cleanup_plan['keep_essential'].append(file_info['path'])
    
    # アーカイブ候補
    archive_categories = ['documentation']
    for category in archive_categories:
        if category in classification:
            # サイズが大きいファイルのみアーカイブ候補
            for file_info in classification[category]['files']:
                if file_info['size'] > 10000:  # 10KB以上
                    cleanup_plan['archive_candidates'].append(file_info['path'])
    
    return cleanup_plan

def main():
    print("=== ファイル整理分析 ===")
    
    # ファイル分析
    classification = analyze_files()
    
    # 結果表示
    total_files = 0
    total_size = 0
    
    for category, info in classification.items():
        file_count = len(info['files'])
        category_size = sum(f['size'] for f in info['files'])
        total_files += file_count
        total_size += category_size
        
        print(f"\n【{category.upper()}】{info['description']}")
        print(f"  ファイル数: {file_count}")
        print(f"  合計サイズ: {category_size/1024/1024:.1f}MB")
        
        # 代表的なファイルを表示
        if file_count > 0:
            print("  主要ファイル:")
            for file_info in sorted(info['files'], key=lambda x: x['size'], reverse=True)[:5]:
                size_mb = file_info['size'] / 1024 / 1024
                print(f"    - {file_info['name']} ({size_mb:.1f}MB)")
    
    print(f"\n=== 全体統計 ===")
    print(f"総ファイル数: {total_files}")
    print(f"総サイズ: {total_size/1024/1024:.1f}MB")
    
    # クリーンアップ計画
    cleanup_plan = generate_cleanup_plan(classification)
    
    print(f"\n=== クリーンアップ提案 ===")
    print(f"安全に削除可能: {len(cleanup_plan['safe_to_delete'])}ファイル")
    print(f"削除候補（要確認）: {len(cleanup_plan['candidates_for_deletion'])}ファイル")
    print(f"必須保持: {len(cleanup_plan['keep_essential'])}ファイル")
    print(f"アーカイブ候補: {len(cleanup_plan['archive_candidates'])}ファイル")
    
    # 詳細レポートをJSONで保存
    report = {
        'analysis_date': datetime.now().isoformat(),
        'classification': classification,
        'cleanup_plan': cleanup_plan,
        'statistics': {
            'total_files': total_files,
            'total_size_mb': total_size / 1024 / 1024
        }
    }
    
    with open('file_organization_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n詳細レポート: file_organization_report.json に保存")
    
    return classification, cleanup_plan

if __name__ == '__main__':
    main()