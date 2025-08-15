#!/usr/bin/env python3
"""
Dash コールバック最適化
Phase 1: 緊急パフォーマンス修正
"""

def optimize_dash_callbacks():
    """
    dash_app.py のコールバック最適化実行
    - 不要な進捗監視無効化
    - タブコールバック統合
    - 重複処理削除
    """
    
    import re
    from pathlib import Path
    
    dash_app_path = Path("C:/ShiftAnalysis/dash_app.py")
    
    if not dash_app_path.exists():
        print(f"Error: {dash_app_path} not found")
        return False
    
    with open(dash_app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # バックアップ作成
    backup_path = dash_app_path.with_suffix('.py.backup_callback_optimization')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Backup created: {backup_path}")
    
    # 最適化実行
    optimizations = []
    
    # 1. 進捗監視間隔をさらに長く（既に2000msだが、5000msに変更）
    if 'interval=2000' in content:
        content = content.replace('interval=2000', 'interval=5000')
        optimizations.append("進捗監視間隔を2000ms→5000msに最適化")
    
    # 2. 無効化されていない監視系の無効化
    patterns_to_disable = [
        (r"dcc\.Interval\(id='log-interval', interval=1000\)", 
         "dcc.Interval(id='log-interval', interval=1000, disabled=True)"),
        (r"interval=10000, disabled=True", 
         "interval=10000, disabled=True"),  # 既に無効化済み
    ]
    
    for pattern, replacement in patterns_to_disable:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            optimizations.append(f"監視系コールバック無効化: {pattern}")
    
    # 3. キャッシュ最適化のための import 追加
    if 'from functools import lru_cache' not in content:
        # dash imports の後に lru_cache import を追加
        content = content.replace(
            'import dash_bootstrap_components as dbc',
            'import dash_bootstrap_components as dbc\nfrom functools import lru_cache'
        )
        optimizations.append("lru_cache import追加")
    
    # 4. データ読み込み関数にキャッシュ追加（注意深く）
    if '@lru_cache(maxsize=10)' not in content and 'def data_get(' in content:
        # data_get関数の直前にlru_cacheデコレータを追加
        content = re.sub(
            r'(def data_get\()',
            r'@lru_cache(maxsize=10)\n\1',
            content,
            count=1
        )
        optimizations.append("data_get関数にキャッシュ追加")
    
    # 最適化された内容を保存
    with open(dash_app_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("=== コールバック最適化完了 ===")
    for opt in optimizations:
        print(f"  [OK] {opt}")
    
    if not optimizations:
        print("  [OK] 最適化項目は既に適用済み")
    
    return True

def create_performance_test():
    """パフォーマンステスト作成"""
    from pathlib import Path
    test_content = '''#!/usr/bin/env python3
"""
Phase 1 パフォーマンステスト
"""

import time
import psutil
import sys
from pathlib import Path

def test_phase1_performance():
    """Phase 1 目標達成確認"""
    
    print("=== Phase 1 パフォーマンステスト ===")
    
    # 1. メモリ使用量測定
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"現在のメモリ使用量: {memory_mb:.1f}MB")
    
    # 2. 初期化時間測定（モック）
    start_time = time.time()
    
    # dash_app import時間測定
    try:
        import dash_app
        init_time = time.time() - start_time
        print(f"dash_app初期化時間: {init_time:.2f}秒")
        
        # 目標判定
        print("\\n=== Phase 1 目標判定 ===")
        
        # 初期化時間目標: ≤ 15秒
        if init_time <= 15:
            print(f"[OK] 初期化時間: {init_time:.2f}秒 <= 15秒 (達成)")
        else:
            print(f"[NG] 初期化時間: {init_time:.2f}秒 > 15秒 (未達成)")
        
        # メモリ使用量目標: ≤ 400MB
        if memory_mb <= 400:
            print(f"[OK] メモリ使用量: {memory_mb:.1f}MB <= 400MB (達成)")
        else:
            print(f"[NG] メモリ使用量: {memory_mb:.1f}MB > 400MB (未達成)")
        
        print("\\n=== 改善提案 ===")
        if init_time > 15:
            print("- 遅延インポート実装を検討")
            print("- 不要なライブラリの削除")
        
        if memory_mb > 400:
            print("- データ構造の最適化")
            print("- ガベージコレクション強化")
            
    except Exception as e:
        print(f"Error importing dash_app: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_phase1_performance()
'''
    
    test_path = Path("C:/ShiftAnalysis/phase1_performance_test.py")
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"パフォーマンステスト作成: {test_path}")
    return test_path

if __name__ == "__main__":
    print("Dash コールバック最適化開始...")
    
    if optimize_dash_callbacks():
        print("[OK] 最適化完了")
        
        # パフォーマンステスト作成
        test_path = create_performance_test()
        print(f"[OK] テストファイル作成: {test_path}")
        
    else:
        print("[NG] 最適化失敗")
        sys.exit(1)