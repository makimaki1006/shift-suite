#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
バックアップ構造の詳細検証
"""

import json
import zipfile
from pathlib import Path

def verify_backup_structure():
    """バックアップ構造の詳細検証"""
    
    print("=" * 80)
    print("🔍 バックアップ構造検証")
    print("=" * 80)
    
    # 1. ディレクトリ構造の検証
    backup_dir = Path("PHASE3_COMPLETE_BACKUP_20250802_100555")
    
    print("📁 ディレクトリ構造:")
    
    # 期待される構造
    expected_structure = {
        "ルートファイル": [
            "backup_metadata.json",
            "restore_phase3.py",
            "verify_backup.py",
            "README.md"
        ],
        "Phase実装": [
            "shift_suite/tasks/fact_extractor_prototype.py",
            "shift_suite/tasks/lightweight_anomaly_detector.py",
            "shift_suite/tasks/fact_book_visualizer.py",
            "shift_suite/tasks/dash_fact_book_integration.py"
        ],
        "設計書": [
            "PHASE3_LIGHTWEIGHT_ANOMALY_DETECTION_DESIGN.md",
            "PHASE3_2_FACT_BOOK_INTEGRATION_GUIDE.md"
        ]
    }
    
    for category, files in expected_structure.items():
        print(f"\n{category}:")
        for file_path in files:
            full_path = backup_dir / file_path
            exists = full_path.exists()
            status = "✅" if exists else "❌"
            print(f"  {status} {file_path}")
            
            if exists and file_path.endswith('.json'):
                # JSONファイルの妥当性検証
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                    print(f"      ✅ JSON形式妥当")
                except:
                    print(f"      ❌ JSON形式エラー")
    
    # 2. ZIPアーカイブの完全性検証
    print("\n📦 ZIPアーカイブ検証:")
    
    zip_path = Path("PHASE3_COMPLETE_BACKUP_20250802_100555.zip")
    if zip_path.exists():
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # ZIP整合性テスト
                result = zf.testzip()
                if result is None:
                    print("  ✅ ZIP整合性OK")
                else:
                    print(f"  ❌ ZIP破損: {result}")
                
                # ファイル数確認
                file_list = zf.namelist()
                print(f"  📊 ZIPファイル数: {len(file_list)}")
                
                # 重要ファイルの存在確認
                important_files = [
                    "backup_metadata.json",
                    "shift_suite/tasks/fact_extractor_prototype.py",
                    "shift_suite/tasks/lightweight_anomaly_detector.py",
                    "shift_suite/tasks/fact_book_visualizer.py"
                ]
                
                for imp_file in important_files:
                    # ZIPパス形式に変換
                    zip_file_path = f"PHASE3_COMPLETE_BACKUP_20250802_100555/{imp_file}"
                    exists_in_zip = any(zip_file_path in f for f in file_list)
                    status = "✅" if exists_in_zip else "❌"
                    print(f"    {status} {imp_file}")
                    
        except Exception as e:
            print(f"  ❌ ZIPエラー: {e}")
    else:
        print("  ❌ ZIPファイル不存在")
    
    # 3. 復元可能性の検証
    print("\n🔄 復元可能性:")
    
    # 復元スクリプトの内容確認
    restore_script = backup_dir / "restore_phase3.py"
    if restore_script.exists():
        with open(restore_script, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 必要な機能の存在確認
        required_functions = [
            ("restore_phase3_backup", "メイン復元関数"),
            ("shutil.copy2", "ファイルコピー機能"),
            ("json.load", "メタデータ読み込み"),
            ("Path", "パス操作")
        ]
        
        for func, desc in required_functions:
            exists = func in content
            status = "✅" if exists else "❌"
            print(f"  {status} {desc}")
    
    # 4. メタデータ完全性
    print("\n📋 メタデータ完全性:")
    
    metadata_path = backup_dir / "backup_metadata.json"
    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # 必須フィールド確認
        required_fields = [
            ("backup_info", "バックアップ基本情報"),
            ("implementation_status", "実装状況"),
            ("critical_files", "重要ファイル一覧"),
            ("backup_verification", "検証情報")
        ]
        
        for field, desc in required_fields:
            exists = field in metadata
            status = "✅" if exists else "❌"
            print(f"  {status} {desc}")
            
            if exists and field == "critical_files":
                # ファイル毎の必須情報確認
                file_count = len(metadata[field])
                checksum_count = len([f for f in metadata[field] if f.get("checksum")])
                print(f"      - ファイル数: {file_count}")
                print(f"      - チェックサム付与: {checksum_count}/{file_count}")
    
    print("\n✅ バックアップ構造検証完了")

if __name__ == "__main__":
    verify_backup_structure()