#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
バックアップ完全性の詳細分析
"""

import json
from pathlib import Path

def analyze_backup_completeness():
    """バックアップ完全性の詳細分析"""
    
    print("=" * 80)
    print("🔍 バックアップ完全性の詳細分析")
    print("=" * 80)
    
    # メタデータ読み込み
    metadata_path = Path("PHASE3_COMPLETE_BACKUP_20250802_100555/backup_metadata.json")
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # 1. カテゴリ別分析
    categories = {
        "Phase 2実装": [],
        "Phase 3.1実装": [],
        "Phase 3.2実装": [],
        "設計書・ドキュメント": [],
        "検証スクリプト": [],
        "システム基盤": [],
        "メインアプリケーション": []
    }
    
    for file_info in metadata["critical_files"]:
        path = file_info["path"]
        
        if "fact_extractor_prototype" in path:
            categories["Phase 2実装"].append(file_info)
        elif "lightweight_anomaly_detector" in path:
            categories["Phase 3.1実装"].append(file_info)
        elif "fact_book_visualizer" in path or "dash_fact_book_integration" in path:
            categories["Phase 3.2実装"].append(file_info)
        elif ".md" in path and "PHASE" in path:
            categories["設計書・ドキュメント"].append(file_info)
        elif "verify" in path or "check" in path or "test" in path:
            categories["検証スクリプト"].append(file_info)
        elif "constants.py" in path or "__init__.py" in path or "requirements.txt" in path:
            categories["システム基盤"].append(file_info)
        elif "app.py" in path or "dash_app.py" in path:
            categories["メインアプリケーション"].append(file_info)
    
    # 2. カテゴリ別サマリー
    print("\n📊 カテゴリ別バックアップ状況:")
    total_size = 0
    
    for category, files in categories.items():
        if files:
            category_size = sum(f["size_bytes"] for f in files)
            total_size += category_size
            print(f"\n{category}: {len(files)}ファイル ({category_size/1024:.1f} KB)")
            for f in files:
                status = "✅" if f["backup_status"] == "success" else "❌"
                print(f"  {status} {Path(f['path']).name} ({f['size_bytes']:,} bytes)")
    
    # 3. 完全性検証
    print(f"\n🔒 完全性保証:")
    
    # チェックサム検証
    all_have_checksum = all(f.get("checksum") for f in metadata["critical_files"])
    print(f"  {'✅' if all_have_checksum else '❌'} 全ファイルにチェックサム付与")
    
    # 成功率
    success_count = len([f for f in metadata["critical_files"] if f["backup_status"] == "success"])
    total_count = len(metadata["critical_files"])
    success_rate = (success_count / total_count) * 100
    print(f"  {'✅' if success_rate == 100 else '❌'} バックアップ成功率: {success_rate:.1f}%")
    
    # 4. 復元可能性検証
    print(f"\n🔄 復元可能性:")
    
    # 復元スクリプトの存在
    restore_script = Path("PHASE3_COMPLETE_BACKUP_20250802_100555/restore_phase3.py")
    print(f"  {'✅' if restore_script.exists() else '❌'} 復元スクリプト存在")
    
    # 検証スクリプトの存在
    verify_script = Path("PHASE3_COMPLETE_BACKUP_20250802_100555/verify_backup.py")
    print(f"  {'✅' if verify_script.exists() else '❌'} 検証スクリプト存在")
    
    # ZIPアーカイブの存在
    zip_file = Path("PHASE3_COMPLETE_BACKUP_20250802_100555.zip")
    if zip_file.exists():
        zip_size_mb = zip_file.stat().st_size / (1024 * 1024)
        print(f"  ✅ ZIPアーカイブ存在 ({zip_size_mb:.2f} MB)")
    else:
        print(f"  ❌ ZIPアーカイブ不在")
    
    # 5. Phase完全性マトリクス
    print(f"\n📋 Phase完全性マトリクス:")
    
    phase_matrix = {
        "Phase 1": ["設計書", "調査スクリプト"],
        "Phase 2": ["実装コード", "統合レポート", "テストスクリプト"],
        "Phase 3.1": ["実装コード", "設計書", "検証レポート"],
        "Phase 3.2": ["実装コード", "統合ガイド", "検証レポート"]
    }
    
    for phase, components in phase_matrix.items():
        print(f"\n  {phase}:")
        for component in components:
            # 簡易的な存在確認
            exists = any(component.lower() in str(f["path"]).lower() for f in metadata["critical_files"])
            status = "✅" if exists else "⚠️"
            print(f"    {status} {component}")
    
    # 6. 統計サマリー
    print(f"\n📊 バックアップ統計:")
    print(f"  総ファイル数: {total_count}")
    print(f"  総サイズ: {total_size / (1024*1024):.2f} MB")
    print(f"  平均ファイルサイズ: {(total_size / total_count) / 1024:.1f} KB")
    print(f"  最大ファイル: {max(metadata['critical_files'], key=lambda x: x['size_bytes'])['path']}")
    print(f"  最小ファイル: {min(metadata['critical_files'], key=lambda x: x['size_bytes'])['path']}")
    
    # 最終判定
    is_complete = (
        success_rate == 100 and
        all_have_checksum and
        restore_script.exists() and
        verify_script.exists() and
        zip_file.exists()
    )
    
    print(f"\n{'🎯' if is_complete else '⚠️'} バックアップ完全性判定: {'完全' if is_complete else '不完全'}")
    
    return is_complete

if __name__ == "__main__":
    analyze_backup_completeness()