#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3 完了時点での完全バックアップ作成スクリプト
安全な次段階移行のための復元可能バックアップ
"""

import os
import sys
import shutil
import zipfile
import json
from pathlib import Path
from datetime import datetime
import hashlib

def create_backup_metadata():
    """バックアップメタデータの作成"""
    timestamp = datetime.now()
    
    metadata = {
        "backup_info": {
            "creation_time": timestamp.isoformat(),
            "backup_name": f"PHASE3_COMPLETE_BACKUP_{timestamp.strftime('%Y%m%d_%H%M%S')}",
            "description": "Phase 3 ブループリント分析システム完了時点でのバックアップ",
            "phase_status": "Phase 3.2 完了 - 統合ファクトブック機能実装完了",
            "next_phase": "既存システムとの段階的統合実施"
        },
        "implementation_status": {
            "phase_1": "完了 - データ構造調査",
            "phase_2": "完了 - 基本事実抽出（FactExtractor）",
            "phase_3_1": "完了 - 軽量異常検知機能",
            "phase_3_2": "完了 - ファクトブック可視化機能"
        },
        "critical_files": [],
        "file_checksums": {},
        "backup_verification": {
            "total_files": 0,
            "total_size_mb": 0.0,
            "backup_integrity": "pending"
        }
    }
    
    return metadata

def calculate_file_checksum(file_path):
    """ファイルのチェックサム計算"""
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        print(f"⚠️ チェックサム計算エラー {file_path}: {e}")
        return None

def backup_critical_files():
    """重要ファイルのバックアップ"""
    
    print("=" * 80)
    print("📦 Phase 3 重要ファイル バックアップ開始")
    print("=" * 80)
    
    # バックアップ対象ファイルの定義
    critical_files = [
        # Phase 2 実装ファイル
        "shift_suite/tasks/fact_extractor_prototype.py",
        
        # Phase 3.1 実装ファイル
        "shift_suite/tasks/lightweight_anomaly_detector.py",
        
        # Phase 3.2 実装ファイル
        "shift_suite/tasks/fact_book_visualizer.py",
        "shift_suite/tasks/dash_fact_book_integration.py",
        
        # 設計書・レポート
        "PHASE3_LIGHTWEIGHT_ANOMALY_DETECTION_DESIGN.md",
        "PHASE3_2_FACT_BOOK_INTEGRATION_GUIDE.md",
        "PHASE3_1_VERIFICATION_REPORT.md",
        "PHASE3_2_VERIFICATION_REPORT.md",
        "BLUEPRINT_PHASE1_SUMMARY.md",
        "BLUEPRINT_PHASE2_INTEGRATION_REPORT.md",
        
        # 検証スクリプト
        "verify_phase3_implementation.py",
        "verify_phase3_2_implementation.py",
        "simple_data_structure_check.py",
        "blueprint_phase1_data_investigation.py",
        "phase2_integration_test.py",
        
        # 重要な設定・定数ファイル
        "shift_suite/tasks/constants.py",
        "shift_suite/__init__.py",
        
        # メインアプリケーション（参考として）
        "dash_app.py",
        "app.py",
        "requirements.txt"
    ]
    
    # バックアップメタデータ初期化
    metadata = create_backup_metadata()
    
    # バックアップディレクトリ作成
    backup_name = metadata["backup_info"]["backup_name"]
    backup_dir = Path(backup_name)
    backup_dir.mkdir(exist_ok=True)
    
    print(f"📁 バックアップディレクトリ: {backup_dir}")
    
    backed_up_files = []
    total_size = 0
    
    for file_path in critical_files:
        source_path = Path(file_path)
        
        if source_path.exists():
            # バックアップ先パス
            backup_file_path = backup_dir / file_path
            backup_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                # ファイルコピー
                shutil.copy2(source_path, backup_file_path)
                
                # チェックサム計算
                checksum = calculate_file_checksum(source_path)
                file_size = source_path.stat().st_size
                
                backed_up_files.append({
                    "path": file_path,
                    "size_bytes": file_size,
                    "checksum": checksum,
                    "backup_status": "success"
                })
                
                total_size += file_size
                print(f"  ✅ {file_path} ({file_size:,} bytes)")
                
            except Exception as e:
                print(f"  ❌ {file_path} - エラー: {e}")
                backed_up_files.append({
                    "path": file_path,
                    "size_bytes": 0,
                    "checksum": None,
                    "backup_status": f"error: {e}"
                })
        else:
            print(f"  ⚠️ {file_path} - ファイル不存在")
            backed_up_files.append({
                "path": file_path,
                "size_bytes": 0,
                "checksum": None,
                "backup_status": "file_not_found"
            })
    
    # メタデータ更新
    metadata["critical_files"] = backed_up_files
    metadata["backup_verification"]["total_files"] = len([f for f in backed_up_files if f["backup_status"] == "success"])
    metadata["backup_verification"]["total_size_mb"] = total_size / (1024 * 1024)
    
    # メタデータファイル保存
    metadata_file = backup_dir / "backup_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 バックアップ統計:")
    print(f"  - 成功ファイル数: {metadata['backup_verification']['total_files']}")
    print(f"  - 総サイズ: {metadata['backup_verification']['total_size_mb']:.2f} MB")
    
    return backup_dir, metadata

def create_restoration_script(backup_dir):
    """復元スクリプトの作成"""
    
    restoration_script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3 バックアップ復元スクリプト
{backup_dir.name} からの復元用
"""

import shutil
import json
from pathlib import Path

def restore_phase3_backup():
    """Phase 3 バックアップの復元"""
    
    print("🔄 Phase 3 バックアップ復元開始")
    print("=" * 60)
    
    backup_dir = Path("{backup_dir.name}")
    
    if not backup_dir.exists():
        print("❌ バックアップディレクトリが見つかりません")
        return False
    
    # メタデータ読み込み
    metadata_file = backup_dir / "backup_metadata.json"
    if not metadata_file.exists():
        print("❌ バックアップメタデータが見つかりません")
        return False
    
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    print(f"📋 復元対象: {{metadata['backup_info']['backup_name']}}")
    print(f"📅 作成日時: {{metadata['backup_info']['creation_time']}}")
    print()
    
    # ファイル復元
    success_count = 0
    for file_info in metadata["critical_files"]:
        if file_info["backup_status"] == "success":
            source_path = backup_dir / file_info["path"]
            target_path = Path(file_info["path"])
            
            try:
                # ディレクトリ作成
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # ファイル復元
                shutil.copy2(source_path, target_path)
                print(f"✅ {{file_info['path']}}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ {{file_info['path']}} - エラー: {{e}}")
        else:
            print(f"⚠️ {{file_info['path']}} - スキップ ({{file_info['backup_status']}})")
    
    print(f"\\n🎉 復元完了: {{success_count}}ファイル")
    print("⚠️ 復元後は動作確認を実施してください")
    
    return True

if __name__ == "__main__":
    restore_phase3_backup()
'''
    
    restore_script_path = backup_dir / "restore_phase3.py"
    with open(restore_script_path, 'w', encoding='utf-8') as f:
        f.write(restoration_script)
    
    # 実行権限付与（Linux/Mac）
    try:
        os.chmod(restore_script_path, 0o755)
    except:
        pass  # Windowsでは無視
    
    print(f"📝 復元スクリプト作成: {restore_script_path}")

def create_verification_script(backup_dir):
    """バックアップ検証スクリプトの作成"""
    
    verification_script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3 バックアップ検証スクリプト
{backup_dir.name} の整合性確認用
"""

import json
import hashlib
from pathlib import Path

def calculate_checksum(file_path):
    """ファイルチェックサム計算"""
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception:
        return None

def verify_backup():
    """バックアップの整合性検証"""
    
    print("🔍 Phase 3 バックアップ検証開始")
    print("=" * 60)
    
    backup_dir = Path("{backup_dir.name}")
    metadata_file = backup_dir / "backup_metadata.json"
    
    if not metadata_file.exists():
        print("❌ メタデータファイルが見つかりません")
        return False
    
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    print(f"📋 検証対象: {{metadata['backup_info']['backup_name']}}")
    print()
    
    success_count = 0
    error_count = 0
    
    for file_info in metadata["critical_files"]:
        if file_info["backup_status"] == "success":
            backup_file = backup_dir / file_info["path"]
            
            if backup_file.exists():
                current_checksum = calculate_checksum(backup_file)
                original_checksum = file_info["checksum"]
                
                if current_checksum == original_checksum:
                    print(f"✅ {{file_info['path']}} - 整合性OK")
                    success_count += 1
                else:
                    print(f"❌ {{file_info['path']}} - チェックサム不一致")
                    error_count += 1
            else:
                print(f"❌ {{file_info['path']}} - ファイル不存在")
                error_count += 1
        else:
            print(f"⚠️ {{file_info['path']}} - 元々バックアップ失敗")
    
    print(f"\\n📊 検証結果:")
    print(f"  - 成功: {{success_count}}ファイル")
    print(f"  - エラー: {{error_count}}ファイル")
    
    if error_count == 0:
        print("🎉 バックアップ整合性確認完了")
        return True
    else:
        print("⚠️ バックアップに問題があります")
        return False

if __name__ == "__main__":
    verify_backup()
'''
    
    verify_script_path = backup_dir / "verify_backup.py"
    with open(verify_script_path, 'w', encoding='utf-8') as f:
        f.write(verification_script)
    
    try:
        os.chmod(verify_script_path, 0o755)
    except:
        pass
    
    print(f"🔍 検証スクリプト作成: {verify_script_path}")

def create_zip_archive(backup_dir):
    """ZIPアーカイブの作成"""
    
    zip_path = Path(f"{backup_dir.name}.zip")
    
    print(f"\n📦 ZIPアーカイブ作成開始: {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in backup_dir.rglob('*'):
            if file_path.is_file():
                arc_name = file_path.relative_to(backup_dir.parent)
                zipf.write(file_path, arc_name)
                print(f"  📄 {arc_name}")
    
    zip_size = zip_path.stat().st_size / (1024 * 1024)
    print(f"✅ ZIPアーカイブ作成完了: {zip_size:.2f} MB")
    
    return zip_path

def main():
    """メインバックアップ処理"""
    
    print("🚀 Phase 3 完了時点 完全バックアップ作成開始")
    print(f"📅 実行日時: {datetime.now().strftime('%Y年%m月%d日 %H時%M分%S秒')}")
    
    try:
        # 1. 重要ファイルバックアップ
        backup_dir, metadata = backup_critical_files()
        
        # 2. 復元スクリプト作成
        create_restoration_script(backup_dir)
        
        # 3. 検証スクリプト作成
        create_verification_script(backup_dir)
        
        # 4. README作成
        readme_content = f"""# Phase 3 完了バックアップ

**作成日時**: {metadata['backup_info']['creation_time']}
**バックアップ名**: {metadata['backup_info']['backup_name']}

## 📋 バックアップ内容
- Phase 2: FactExtractor プロトタイプ
- Phase 3.1: 軽量異常検知機能  
- Phase 3.2: ファクトブック可視化機能
- 設計書・検証レポート
- 復元・検証スクリプト

## 🔄 復元方法
```bash
python restore_phase3.py
```

## 🔍 検証方法
```bash
python verify_backup.py
```

## ⚠️ 注意事項
- 復元前に現在のファイルをバックアップしてください
- 復元後は必ず動作確認を実施してください
- 問題がある場合は即座にこのバックアップから復元してください
"""
        
        readme_path = backup_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # 5. ZIPアーカイブ作成
        zip_path = create_zip_archive(backup_dir)
        
        # 完了サマリー
        print("\n" + "=" * 80)
        print("🎉 Phase 3 完全バックアップ作成完了")
        print("=" * 80)
        print(f"📁 バックアップディレクトリ: {backup_dir}")
        print(f"📦 ZIPアーカイブ: {zip_path}")
        print(f"📊 総ファイル数: {metadata['backup_verification']['total_files']}")
        print(f"📏 総サイズ: {metadata['backup_verification']['total_size_mb']:.2f} MB")
        print()
        print("🔄 復元コマンド:")
        print(f"   cd {backup_dir} && python restore_phase3.py")
        print()
        print("🔍 検証コマンド:")
        print(f"   cd {backup_dir} && python verify_backup.py")
        print()
        print("✅ 安全な次段階移行の準備完了")
        
        return True
        
    except Exception as e:
        print(f"❌ バックアップ作成中にエラー: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)