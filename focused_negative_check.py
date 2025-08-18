#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
集中的ネガティブ検証：本当に解決しているか？
"""

import sys
import requests
import threading
import time

def focused_negative_check():
    """集中的にネガティブ検証"""
    print("=== 集中的ネガティブ検証 ===")
    
    critical_issues = []
    
    try:
        sys.path.append('.')
        import dash_app
        
        # 1. 実際のHTTPサーバー検証
        def start_test_server():
            try:
                dash_app.app.run_server(debug=False, host='127.0.0.1', port=8052, use_reloader=False)
            except:
                pass
        
        server_thread = threading.Thread(target=start_test_server, daemon=True)
        server_thread.start()
        time.sleep(5)
        
        # HTTPアクセステスト
        try:
            response = requests.get('http://127.0.0.1:8052', timeout=10)
            html = response.text
            
            # 具体的な問題チェック
            if '_dash-loading' in html:
                loading_positions = []
                start = 0
                while True:
                    pos = html.find('_dash-loading', start)
                    if pos == -1:
                        break
                    loading_positions.append(pos)
                    start = pos + 1
                
                if loading_positions:
                    critical_issues.append(f"Loading状態検出: {len(loading_positions)}箇所 at positions {loading_positions[:3]}")
            
            # エラーメッセージの詳細検索
            error_indicators = ['unhashable type', 'DataFrame', 'TypeError', 'サプタブ作成エラー']
            for indicator in error_indicators:
                if indicator in html:
                    critical_issues.append(f"エラー痕跡検出: '{indicator}' found in HTML")
            
        except Exception as e:
            critical_issues.append(f"HTTP接続失敗: {e}")
        
        # 2. 実際のコールバック関数での問題検証
        print("コールバック実行テスト中...")
        try:
            # 問題が報告されたinitialize_shortage_contentを直接テスト
            style = {'display': 'block'}
            result = dash_app.initialize_shortage_content(style, 'test_scenario', True)
            
            if result is None:
                critical_issues.append("initialize_shortage_content returned None")
            elif hasattr(result, 'children') and not result.children:
                critical_issues.append("initialize_shortage_content returned empty content")
                
        except Exception as e:
            critical_issues.append(f"initialize_shortage_content FAILED: {e}")
            if 'unhashable' in str(e).lower():
                critical_issues.append("CRITICAL: DataFrame unhashable error STILL EXISTS")
        
        # 3. create_shortage_tab関数の詳細検証
        try:
            result = dash_app.create_shortage_tab('test_scenario')
            if not result:
                critical_issues.append("create_shortage_tab returned falsy value")
        except Exception as e:
            critical_issues.append(f"create_shortage_tab FAILED: {e}")
            if 'unhashable' in str(e).lower():
                critical_issues.append("CRITICAL: DataFrame unhashable in create_shortage_tab")
        
        # 4. データアクセスの問題検証  
        data_keys_to_test = ['shortage_role_summary', 'long_df', 'intermediate_data']
        for key in data_keys_to_test:
            try:
                data = dash_app.data_get(key)
                if data is None:
                    critical_issues.append(f"Data key '{key}' returns None")
                elif hasattr(data, 'empty') and data.empty:
                    critical_issues.append(f"Data key '{key}' returns empty DataFrame")
            except Exception as e:
                critical_issues.append(f"Data access '{key}' FAILED: {e}")
        
    except Exception as e:
        critical_issues.append(f"Import or setup FAILED: {e}")
    
    # 結果判定
    print(f"\n=== ネガティブ検証結果 ===")
    if critical_issues:
        print(f"FAILED: {len(critical_issues)}個の深刻な問題発見")
        for i, issue in enumerate(critical_issues, 1):
            print(f"  {i}. {issue}")
        print("\n結論: 問題は解決していない")
        return False
    else:
        print("PASSED: 深刻な問題は検出されず")
        print("結論: ネガティブ検証でも問題なし") 
        return True

if __name__ == "__main__":
    result = focused_negative_check()
    print(f"\n最終判定: {'SUCCESS' if result else 'FAILURE'}")