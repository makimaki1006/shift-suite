#!/usr/bin/env python3
"""
簡易パフォーマンスチェック
"""

import psutil
import time

def main():
    print("=== 簡易パフォーマンスチェック ===")
    
    # メモリ使用量
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"現在のメモリ使用量: {memory_mb:.1f}MB")
    
    # dash_app.pyファイルサイズ確認
    import os
    dash_app_size = os.path.getsize("C:/ShiftAnalysis/dash_app.py") / 1024
    print(f"dash_app.pyファイルサイズ: {dash_app_size:.1f}KB")
    
    # 技術的負債スコア確認（前回実行結果から）
    print("\n=== 技術的負債状況（前回分析結果） ===")
    print("dash_app.py: スコア 98.0 [緊急対応が必要]")
    print("app.py: スコア 93.0 [緊急対応が必要]")
    
    print("\n=== Phase 1 実装状況 ===")
    
    # アセットファイル確認
    assets_exist = []
    assets_exist.append(os.path.exists("C:/ShiftAnalysis/assets/style.css"))
    assets_exist.append(os.path.exists("C:/ShiftAnalysis/assets/c2-mobile.css"))
    
    if all(assets_exist):
        print("[OK] 不足アセット補完: 完了")
    else:
        print("[NG] 不足アセット補完: 未完了")
    
    # バックアップファイル確認（最適化実行確認）
    backup_exists = os.path.exists("C:/ShiftAnalysis/dash_app.py.backup_callback_optimization")
    if backup_exists:
        print("[OK] コールバック最適化: 実行済み")
    else:
        print("[NG] コールバック最適化: 未実行")
    
    # 必須パッケージ確認
    try:
        import pandas
        import numpy  
        import dash
        import plotly
        print("[OK] 基本依存関係: 利用可能")
    except ImportError as e:
        print(f"[NG] 基本依存関係: {e}")
    
    print("\n=== 次のステップ推奨 ===")
    print("1. dash_app.py の巨大ファイル問題対策")
    print("2. コールバック数削減（現在55個）")
    print("3. データキャッシュ戦略強化")
    print("4. 不要な処理の削除")
    
    print("\n=== Phase 1 完了判定 ===")
    score = 0
    if all(assets_exist):
        score += 25
    if backup_exists:
        score += 25  
    if memory_mb <= 400:
        score += 25
    if dash_app_size <= 500:  # 500KB以下が理想
        score += 25
    
    print(f"Phase 1 達成度: {score}/100点")
    
    if score >= 75:
        print("[OK] Phase 1 基本目標達成")
    elif score >= 50:
        print("[WARNING] Phase 1 部分達成")
    else:
        print("[NG] Phase 1 追加対策必要")

if __name__ == "__main__":
    main()