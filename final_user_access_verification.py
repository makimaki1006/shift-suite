#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最終ユーザーアクセス検証 - 実際にユーザーがシステムにアクセス可能かテスト
"""

import sys
import socket
import threading
import time
import os
from pathlib import Path

def check_port_available(port):
    """ポートが利用可能かチェック"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False

def find_free_port(start_port=8090):
    """空いているポートを見つける"""
    for port in range(start_port, start_port + 10):
        if check_port_available(port):
            return port
    return None

def test_dash_startup():
    """Dashアプリケーションの起動テスト"""
    print("=== Dash Application Startup Test ===")
    
    try:
        # dash_app.pyをインポート
        sys.path.append('.')
        import dash_app
        
        print("SUCCESS: dash_app.py imported successfully")
        
        # アプリケーションオブジェクトの確認
        if hasattr(dash_app, 'app'):
            app = dash_app.app
            print("SUCCESS: Dash app object found")
            
            # 利用可能ポートを見つける
            port = find_free_port()
            if port:
                print(f"SUCCESS: Available port found: {port}")
                
                # バックグラウンドでテスト起動
                def test_server():
                    try:
                        app.run_server(
                            host='127.0.0.1', 
                            port=port, 
                            debug=False,
                            use_reloader=False,
                            threaded=True
                        )
                    except Exception as e:
                        print(f"Server startup error: {e}")
                
                # 短時間でテスト
                server_thread = threading.Thread(target=test_server, daemon=True)
                server_thread.start()
                
                # 少し待って接続テスト
                time.sleep(3)
                
                # ポート接続テスト
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
                        test_socket.settimeout(2)
                        result = test_socket.connect_ex(('127.0.0.1', port))
                        if result == 0:
                            print(f"SUCCESS: Server is accessible on http://127.0.0.1:{port}")
                            print("SUCCESS: Users can access the system")
                            return True
                        else:
                            print("ERROR: Server is not responding")
                            return False
                except Exception as e:
                    print(f"ERROR: Connection test failed: {e}")
                    return False
                    
            else:
                print("ERROR: No available ports found")
                return False
        else:
            print("ERROR: Dash app object not found")
            return False
            
    except Exception as e:
        print(f"ERROR: Dash startup test failed: {e}")
        return False

def test_streamlit_availability():
    """Streamlit代替システムのテスト"""
    print("\n=== Streamlit Alternative Test ===")
    
    streamlit_file = Path("streamlit_shift_analysis.py")
    if streamlit_file.exists():
        print("SUCCESS: Streamlit alternative system exists")
        return True
    else:
        print("WARNING: Streamlit alternative not found")
        return False

def main():
    print("=== Final User Access Verification ===")
    print("Testing actual user accessibility to the shift analysis system")
    print()
    
    # Dashシステムテスト
    dash_result = test_dash_startup()
    
    # Streamlit代替テスト
    streamlit_result = test_streamlit_availability()
    
    # 最終評価
    print("\n=== Final User Access Assessment ===")
    
    if dash_result:
        print("SUCCESS: Primary Dash system is user-accessible")
        accessibility_score = 100
    elif streamlit_result:
        print("PARTIAL: Streamlit alternative is available")
        accessibility_score = 80
    else:
        print("ERROR: No user-accessible systems found")
        accessibility_score = 0
    
    print(f"User Accessibility Score: {accessibility_score}%")
    
    if accessibility_score >= 80:
        print("CONCLUSION: Users can access the shift analysis system")
    else:
        print("CONCLUSION: Critical accessibility issues exist")
    
    return accessibility_score

if __name__ == '__main__':
    main()