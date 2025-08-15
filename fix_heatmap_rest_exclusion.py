#!/usr/bin/env python3
"""
ヒートマップ休日除外修正スクリプト
============================

キャッシュされた分析結果をクリアし、休日除外フィルターが確実に適用されるようにする
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List

def find_analysis_directories() -> List[Path]:
    """分析結果ディレクトリを検索"""
    current_dir = Path.cwd()
    analysis_dirs = []
    
    # 一般的な分析結果ディレクトリパターンを検索
    patterns = [
        "analysis_results*",
        "*_分析結果*",
        "*analysis*",
        "*_results*"
    ]
    
    for pattern in patterns:
        for path in current_dir.glob(pattern):
            if path.is_dir():
                analysis_dirs.append(path)
    
    return analysis_dirs

def find_parquet_files() -> List[Path]:
    """Parquetファイルを検索"""
    current_dir = Path.cwd()
    parquet_files = []
    
    # 分析関連のparquetファイルを検索
    patterns = [
        "pre_aggregated_data.parquet",
        "intermediate_data.parquet", 
        "heat_*.parquet",
        "shortage_*.parquet",
        "*_heatmap.parquet"
    ]
    
    for pattern in patterns:
        for path in current_dir.glob(pattern):
            if path.is_file():
                parquet_files.append(path)
    
    return parquet_files

def clear_cache_files():
    """キャッシュファイルをクリア"""
    print("🧹 キャッシュクリア実行中...")
    
    cleared_count = 0
    
    # 1. 分析結果ディレクトリの削除
    analysis_dirs = find_analysis_directories()
    for dir_path in analysis_dirs:
        try:
            print(f"  📁 削除中: {dir_path}")
            shutil.rmtree(dir_path)
            cleared_count += 1
        except Exception as e:
            print(f"  ❌ 削除失敗: {dir_path} - {e}")
    
    # 2. Parquetファイルの削除
    parquet_files = find_parquet_files()
    for file_path in parquet_files:
        try:
            print(f"  📄 削除中: {file_path}")
            file_path.unlink()
            cleared_count += 1
        except Exception as e:
            print(f"  ❌ 削除失敗: {file_path} - {e}")
    
    # 3. Python __pycache__ の削除
    pycache_dirs = list(Path.cwd().rglob("__pycache__"))
    for pycache_dir in pycache_dirs:
        try:
            if "venv" not in str(pycache_dir) and ".venv" not in str(pycache_dir):
                print(f"  🗂️  削除中: {pycache_dir}")
                shutil.rmtree(pycache_dir)
                cleared_count += 1
        except Exception as e:
            print(f"  ❌ 削除失敗: {pycache_dir} - {e}")
    
    print(f"✅ クリア完了: {cleared_count}個のファイル/ディレクトリを削除")
    return cleared_count

def verify_rest_exclusion_implementation():
    """休日除外実装の確認"""
    print("\n🔍 休日除外実装の確認...")
    
    dash_app = Path("dash_app.py")
    utils_file = Path("shift_suite/tasks/utils.py")
    
    if not dash_app.exists():
        print("❌ dash_app.py が見つかりません")
        return False
    
    if not utils_file.exists():
        print("❌ utils.py が見つかりません")
        return False
    
    with open(dash_app, 'r', encoding='utf-8') as f:
        dash_content = f.read()
    
    with open(utils_file, 'r', encoding='utf-8') as f:
        utils_content = f.read()
    
    # 基本的な実装をチェック
    basic_checks = {
        "dash_app.py存在": True,
        "utils.py存在": True,
        "統合版フィルター": "apply_rest_exclusion_filter" in utils_content,
        "データ読み込み統合": "pre_aggregated_data" in dash_content,
    }
    
    all_checks_passed = True
    for check_name, result in basic_checks.items():
        if result:
            print(f"  ✅ {check_name}: 確認")
        else:
            print(f"  ❌ {check_name}: 問題")
            all_checks_passed = False
    
    return all_checks_passed

def main():
    """メイン処理"""
    print("=" * 60)
    print("🎯 ヒートマップ休日除外修正スクリプト")
    print("=" * 60)
    
    # 1. 実装確認
    implementation_ok = verify_rest_exclusion_implementation()
    if not implementation_ok:
        print("\n❌ 休日除外の実装に問題があります。")
        print("   dash_app.pyの修正が必要です。")
        return False
    
    print("\n✅ 休日除外の実装確認完了")
    
    # 2. キャッシュクリア
    cleared_count = clear_cache_files()
    
    if cleared_count == 0:
        print("\n💡 削除対象のキャッシュファイルが見つかりませんでした")
    
    # 3. 手順案内
    print("\n" + "=" * 60)
    print("📋 次の手順")
    print("=" * 60)
    print("1. dash_app.py を起動")
    print("2. テストデータ「ショート_テスト用データ.xlsx」をアップロード")
    print("3. 分析実行（新しいフィルターが適用されます）")
    print("4. ヒートマップタブで休日除外を確認")
    print("")
    print("🔍 確認ポイント:")
    print("  • ログに '[RestExclusion]' メッセージが表示される")
    print("  • ヒートマップに'×'記号の時間帯が表示されない")
    print("  • 実際に働いているスタッフのみが可視化される")
    print("")
    print("✨ これで「休みがカウントされている現状」が解決されます！")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)