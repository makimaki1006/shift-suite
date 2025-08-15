#!/usr/bin/env python3
"""
不足分析専用ログシステム
分析段階（app.py）と可視化段階（dash_app.py）を分離してログを記録
"""

import logging
import os
from datetime import datetime
from pathlib import Path

# ログファイルのパス
LOG_DIR = Path(__file__).parent
SHORTAGE_ANALYSIS_LOG = LOG_DIR / "shortage_analysis.log"
SHORTAGE_DASHBOARD_LOG = LOG_DIR / "shortage_dashboard.log"

def setup_shortage_analysis_logger():
    """分析段階（app.py）用のログ設定"""
    logger = logging.getLogger('shortage_analysis')
    logger.setLevel(logging.INFO)
    
    # 既存のハンドラーをクリア
    logger.handlers.clear()
    
    # ファイルハンドラー
    file_handler = logging.FileHandler(SHORTAGE_ANALYSIS_LOG, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # フォーマッター
    formatter = logging.Formatter(
        '%(asctime)s [ANALYSIS] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # 初期メッセージ
    logger.info("="*60)
    logger.info("不足分析ログ（分析段階）開始")
    logger.info(f"ログファイル: {SHORTAGE_ANALYSIS_LOG}")
    logger.info("="*60)
    
    return logger

def setup_shortage_dashboard_logger():
    """可視化段階（dash_app.py）用のログ設定"""
    logger = logging.getLogger('shortage_dashboard')
    logger.setLevel(logging.INFO)
    
    # 既存のハンドラーをクリア
    logger.handlers.clear()
    
    # ファイルハンドラー
    file_handler = logging.FileHandler(SHORTAGE_DASHBOARD_LOG, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # フォーマッター
    formatter = logging.Formatter(
        '%(asctime)s [DASHBOARD] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # 初期メッセージ
    logger.info("="*60)
    logger.info("不足分析ログ（可視化段階）開始")
    logger.info(f"ログファイル: {SHORTAGE_DASHBOARD_LOG}")
    logger.info("="*60)
    
    return logger

def clear_shortage_logs():
    """不足分析ログファイルをクリア"""
    for log_file in [SHORTAGE_ANALYSIS_LOG, SHORTAGE_DASHBOARD_LOG]:
        if log_file.exists():
            log_file.unlink()
            print(f"ログファイルをクリアしました: {log_file}")

def show_log_files():
    """ログファイルの場所を表示"""
    print("📝 不足分析専用ログファイル:")
    print(f"  分析段階: {SHORTAGE_ANALYSIS_LOG}")
    print(f"  可視化段階: {SHORTAGE_DASHBOARD_LOG}")
    print()
    print("📖 ログ確認コマンド:")
    print(f"  tail -f '{SHORTAGE_ANALYSIS_LOG}'")
    print(f"  tail -f '{SHORTAGE_DASHBOARD_LOG}'")
    print(f"  # 両方同時に見る場合:")
    print(f"  tail -f '{SHORTAGE_ANALYSIS_LOG}' '{SHORTAGE_DASHBOARD_LOG}'")

if __name__ == "__main__":
    # テスト実行
    print("不足分析ログシステムのテスト")
    
    # ログファイルの場所を表示
    show_log_files()
    
    # テストログ
    analysis_logger = setup_shortage_analysis_logger()
    dashboard_logger = setup_shortage_dashboard_logger()
    
    analysis_logger.info("分析段階テストメッセージ")
    dashboard_logger.info("可視化段階テストメッセージ")
    
    print("\nログファイルが作成されました。")