#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ネガティブ検証：実際の問題を徹底的に確認
"""

import sys
import time
import requests
import threading
import traceback
from pathlib import Path

def negative_verification():
    """ネガティブな観点で問題を徹底検証"""
    print("=== ネガティブ検証開始：本当に全て解決しているか？ ===")
    
    issues_found = []
    
    # 1. 実際のサーバー起動とアクセスの詳細検証
    print("\n1. 実サーバー検証")
    try:
        sys.path.append('.')
        import dash_app
        
        def start_server():
            try:
                dash_app.app.run_server(debug=False, host='127.0.0.1', port=8051, use_reloader=False)
            except Exception as e:
                print(f"サーバー起動エラー: {e}")
        
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        time.sleep(5)  # 十分な起動時間
        
        # HTTP詳細チェック
        response = requests.get('http://127.0.0.1:8051', timeout=10)
        html_content = response.text
        
        # Loading状態の詳細確認
        if '_dash-loading' in html_content:
            loading_count = html_content.count('_dash-loading')
            issues_found.append(f"Loading状態で停止: {loading_count}箇所検出")
            
        # エラーメッセージの詳細確認
        error_patterns = ['error', 'エラー', 'failed', 'exception', 'unhashable']
        for pattern in error_patterns:
            if pattern in html_content.lower():
                count = html_content.lower().count(pattern)
                if count > 0:
                    issues_found.append(f"エラーパターン '{pattern}': {count}回検出")
        
        # 必須要素の厳格チェック
        required_elements = [
            ('main-content', 'main-content'),
            ('プルダウンセレクタ', 'function-selector-dropdown'),
            ('ナビゲーション', 'navbar'),
            ('コンテンツエリア', 'main-content')
        ]
        
        for name, element_id in required_elements:
            if element_id not in html_content:
                issues_found.append(f"必須要素欠如: {name} ({element_id})")
                
    except Exception as e:
        issues_found.append(f"サーバー検証失敗: {e}")
        traceback.print_exc()
    
    # 2. 機能別詳細検証
    print("\n2. 機能別詳細検証")
    try:
        # 各タブ生成の検証
        tab_functions = [
            'create_shortage_tab',
            'create_overview_tab', 
            'create_heatmap_tab',
            'create_leave_analysis_tab'
        ]
        
        for func_name in tab_functions:
            try:
                func = getattr(dash_app, func_name, None)
                if func:
                    result = func('test_scenario')
                    if not result or not hasattr(result, 'children'):
                        issues_found.append(f"タブ生成異常: {func_name} - 無効な戻り値")
                else:
                    issues_found.append(f"関数不存在: {func_name}")
            except Exception as e:
                issues_found.append(f"タブ生成エラー: {func_name} - {e}")
                
    except Exception as e:
        issues_found.append(f"機能検証失敗: {e}")
    
    # 3. データ整合性の厳格チェック
    print("\n3. データ整合性検証")
    try:
        # 重要データの検証
        critical_data_keys = [
            'shortage_role_summary',
            'shortage_employment_summary', 
            'long_df',
            'intermediate_data'
        ]
        
        for key in critical_data_keys:
            try:
                data = dash_app.data_get(key)
                if data is None:
                    issues_found.append(f"データ欠如: {key} - None")
                elif hasattr(data, 'empty') and data.empty:
                    issues_found.append(f"データ空: {key} - 空のDataFrame")
                elif hasattr(data, 'shape') and data.shape[0] == 0:
                    issues_found.append(f"データ無し: {key} - 0行")
            except Exception as e:
                issues_found.append(f"データ取得エラー: {key} - {e}")
                
    except Exception as e:
        issues_found.append(f"データ検証失敗: {e}")
    
    # 4. コールバック関数の厳格検証
    print("\n4. コールバック関数検証")
    try:
        # 主要コールバックの検証
        callback_tests = [
            ('update_shortage_results', ['advanced', 'test_scenario']),
            ('initialize_shortage_content', [{'display': 'block'}, 'test_scenario', True]),
            ('update_content_from_dropdown', ['overview'])
        ]
        
        for func_name, args in callback_tests:
            try:
                func = getattr(dash_app, func_name, None)
                if func:
                    result = func(*args)
                    if result is None:
                        issues_found.append(f"コールバック戻り値None: {func_name}")
                else:
                    issues_found.append(f"コールバック関数不存在: {func_name}")
            except Exception as e:
                issues_found.append(f"コールバックエラー: {func_name} - {e}")
                if 'unhashable' in str(e).lower():
                    issues_found.append(f"CRITICAL: DataFrame unhashable in {func_name}")
                    
    except Exception as e:
        issues_found.append(f"コールバック検証失敗: {e}")
    
    # 5. メモリとパフォーマンスの検証
    print("\n5. パフォーマンス検証")
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_percent = process.memory_percent()
        
        if memory_percent > 50:  # 50%以上のメモリ使用
            issues_found.append(f"高メモリ使用: {memory_percent:.1f}%")
            
        # キャッシュサイズの確認
        if hasattr(dash_app, 'DATA_CACHE'):
            cache_size = len(dash_app.DATA_CACHE._cache) if hasattr(dash_app.DATA_CACHE, '_cache') else 0
            if cache_size > 100:  # 異常に多いキャッシュ
                issues_found.append(f"過大キャッシュ: {cache_size}エントリ")
                
    except Exception as e:
        issues_found.append(f"パフォーマンス検証失敗: {e}")
    
    # 結果レポート
    print(f"\n=== ネガティブ検証結果 ===")
    if issues_found:
        print(f"❌ {len(issues_found)}個の問題を発見:")
        for i, issue in enumerate(issues_found, 1):
            print(f"  {i}. {issue}")
        print("\n結論: 完了していません - 問題が残存")
        return False
    else:
        print("✓ 問題は検出されませんでした")
        print("結論: 厳格検証でも問題なし")
        return True

if __name__ == "__main__":
    result = negative_verification()
    sys.exit(0 if result else 1)