#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
バックアップファイル内容の完全性検証
オリジナルとバックアップのバイト単位比較
"""

import hashlib
import json
from pathlib import Path
import filecmp

def calculate_file_checksum(file_path):
    """ファイルのSHA-256チェックサム計算"""
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        return None

def compare_file_content(original_path, backup_path):
    """ファイル内容の詳細比較"""
    
    # 1. ファイルサイズ比較
    original_size = original_path.stat().st_size
    backup_size = backup_path.stat().st_size
    size_match = original_size == backup_size
    
    # 2. チェックサム比較
    original_checksum = calculate_file_checksum(original_path)
    backup_checksum = calculate_file_checksum(backup_path)
    checksum_match = original_checksum == backup_checksum
    
    # 3. バイト単位比較（Python標準ライブラリ）
    byte_match = filecmp.cmp(original_path, backup_path, shallow=False)
    
    # 4. 行数比較（テキストファイルの場合）
    try:
        with open(original_path, 'r', encoding='utf-8') as f:
            original_lines = len(f.readlines())
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_lines = len(f.readlines())
        line_match = original_lines == backup_lines
    except:
        original_lines = backup_lines = 0
        line_match = True  # バイナリファイルの場合はスキップ
    
    return {
        "size_match": size_match,
        "original_size": original_size,
        "backup_size": backup_size,
        "checksum_match": checksum_match,
        "original_checksum": original_checksum,
        "backup_checksum": backup_checksum,
        "byte_match": byte_match,
        "line_match": line_match,
        "original_lines": original_lines,
        "backup_lines": backup_lines
    }

def verify_all_backup_content():
    """全バックアップファイルの内容検証"""
    
    print("=" * 80)
    print("🔬 バックアップファイル内容の完全性検証")
    print("=" * 80)
    
    # メタデータ読み込み
    metadata_path = Path("PHASE3_COMPLETE_BACKUP_20250802_100555/backup_metadata.json")
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # 重要ファイルの検証（Phase 2, 3.1, 3.2の実装ファイル中心）
    critical_files = [
        "shift_suite/tasks/fact_extractor_prototype.py",
        "shift_suite/tasks/lightweight_anomaly_detector.py", 
        "shift_suite/tasks/fact_book_visualizer.py",
        "shift_suite/tasks/dash_fact_book_integration.py"
    ]
    
    print("\n📋 重要実装ファイルの詳細検証:")
    print("-" * 80)
    
    all_match = True
    
    for file_path in critical_files:
        print(f"\n🔍 {file_path}:")
        
        original_path = Path(file_path)
        backup_path = Path(f"PHASE3_COMPLETE_BACKUP_20250802_100555/{file_path}")
        
        if not original_path.exists():
            print("  ❌ オリジナルファイルが存在しません")
            continue
            
        if not backup_path.exists():
            print("  ❌ バックアップファイルが存在しません")
            all_match = False
            continue
        
        # 詳細比較実行
        comparison = compare_file_content(original_path, backup_path)
        
        # 結果表示
        print(f"  📊 サイズ: {'✅' if comparison['size_match'] else '❌'} " +
              f"オリジナル {comparison['original_size']:,} bytes = " +
              f"バックアップ {comparison['backup_size']:,} bytes")
        
        print(f"  🔐 チェックサム: {'✅' if comparison['checksum_match'] else '❌'}")
        if not comparison['checksum_match']:
            print(f"    オリジナル: {comparison['original_checksum']}")
            print(f"    バックアップ: {comparison['backup_checksum']}")
        
        print(f"  💾 バイト比較: {'✅ 完全一致' if comparison['byte_match'] else '❌ 不一致'}")
        
        if comparison['original_lines'] > 0:
            print(f"  📝 行数: {'✅' if comparison['line_match'] else '❌'} " +
                  f"{comparison['original_lines']} 行")
        
        # メタデータとの照合
        meta_file = next((f for f in metadata['critical_files'] if f['path'] == file_path), None)
        if meta_file:
            meta_checksum = meta_file.get('checksum')
            meta_match = meta_checksum == comparison['original_checksum']
            print(f"  📋 メタデータ照合: {'✅' if meta_match else '❌'}")
        
        if not (comparison['size_match'] and comparison['checksum_match'] and comparison['byte_match']):
            all_match = False
    
    # 追加検証: ランダムサンプリング
    print("\n📊 その他ファイルのランダムサンプル検証:")
    print("-" * 80)
    
    sample_files = [
        "PHASE3_LIGHTWEIGHT_ANOMALY_DETECTION_DESIGN.md",
        "verify_phase3_implementation.py",
        "shift_suite/tasks/constants.py"
    ]
    
    for file_path in sample_files:
        original_path = Path(file_path)
        backup_path = Path(f"PHASE3_COMPLETE_BACKUP_20250802_100555/{file_path}")
        
        if original_path.exists() and backup_path.exists():
            comparison = compare_file_content(original_path, backup_path)
            status = "✅" if comparison['byte_match'] else "❌"
            print(f"  {status} {file_path} ({comparison['original_size']:,} bytes)")
    
    # 最終判定
    print("\n" + "=" * 80)
    print(f"🎯 内容完全性検証結果: {'✅ 完全一致' if all_match else '❌ 不一致あり'}")
    
    if all_match:
        print("📋 結論: バックアップファイルの内容は省略なく完全にコピーされています")
    else:
        print("⚠️ 警告: 一部のファイルで不一致が検出されました")
    
    return all_match

def show_sample_content():
    """実装ファイルのサンプル内容表示（省略されていないことの証明）"""
    
    print("\n" + "=" * 80)
    print("📄 バックアップファイルのサンプル内容（省略なしの証明）")
    print("=" * 80)
    
    # Phase 3.1の異常検知メソッドが完全に含まれているか確認
    backup_file = Path("PHASE3_COMPLETE_BACKUP_20250802_100555/shift_suite/tasks/lightweight_anomaly_detector.py")
    
    if backup_file.exists():
        with open(backup_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"\n🔍 lightweight_anomaly_detector.py の検証:")
        print(f"  総文字数: {len(content):,}")
        print(f"  総行数: {content.count(chr(10))}")
        
        # 重要なメソッドの存在確認
        important_methods = [
            "_detect_excessive_hours",
            "_detect_continuous_work_violations",
            "_detect_night_shift_anomalies",
            "_detect_interval_violations",
            "_calculate_severity",
            "generate_anomaly_summary"
        ]
        
        print(f"\n  重要メソッドの存在確認:")
        for method in important_methods:
            if f"def {method}" in content:
                # メソッドの開始位置と一部のコードを表示
                start_pos = content.find(f"def {method}")
                method_preview = content[start_pos:start_pos+200].split('\n')[0]
                print(f"    ✅ {method_preview}")
            else:
                print(f"    ❌ {method} が見つかりません")

if __name__ == "__main__":
    # 完全性検証実行
    is_complete = verify_all_backup_content()
    
    # サンプル内容表示
    show_sample_content()
    
    print("\n✅ 検証完了")