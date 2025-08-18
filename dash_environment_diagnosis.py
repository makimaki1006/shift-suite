#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dash環境の根本的問題診断
"""

import sys
import os
import traceback

def diagnose_dash_environment():
    """Dash環境の詳細診断"""
    print("=== Dash環境根本診断 ===")
    
    # Python環境確認
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Dashインポートテスト
    try:
        import dash
        print(f"Dash version: {dash.__version__}")
        print("Dash import: SUCCESS")
    except Exception as e:
        print(f"Dash import: FAILED - {e}")
        return False
    
    # 基本コンポーネントテスト
    try:
        from dash import html, dcc
        print("Basic components import: SUCCESS")
    except Exception as e:
        print(f"Basic components import: FAILED - {e}")
        return False
    
    # アプリケーション作成テスト
    try:
        app = dash.Dash(__name__)
        print("App creation: SUCCESS")
        
        # 基本レイアウト作成
        app.layout = html.Div([
            html.H1("Test App"),
            html.P("Basic test content")
        ])
        print("Layout assignment: SUCCESS")
        
        # Flask app確認
        print(f"Flask app type: {type(app.server)}")
        print(f"Flask app name: {app.server.name}")
        
        # 設定確認
        print("\nDash設定:")
        for key, value in app.config.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"App creation/layout: FAILED - {e}")
        print(traceback.format_exc())
        return False
    
    # 依存関係確認
    print("\n=== 依存関係確認 ===")
    dependencies = ['flask', 'werkzeug', 'plotly', 'dash_bootstrap_components']
    
    for dep in dependencies:
        try:
            module = __import__(dep)
            version = getattr(module, '__version__', 'Unknown')
            print(f"{dep}: {version}")
        except ImportError:
            print(f"{dep}: NOT INSTALLED")
        except Exception as e:
            print(f"{dep}: ERROR - {e}")
    
    # JavaScript/CSS assets確認
    print("\n=== Assets確認 ===")
    try:
        print(f"Assets folder: {getattr(app, '_assets_folder', 'Default')}")
        print(f"Serve locally: {app.scripts.config.serve_locally}")
        print(f"External scripts: {len(app.scripts.config.external_scripts)}")
        print(f"External stylesheets: {len(app.css.config.external_stylesheets)}")
    except Exception as e:
        print(f"Assets configuration check: FAILED - {e}")
    
    print("\n=== 診断完了 ===")
    return True

if __name__ == "__main__":
    success = diagnose_dash_environment()
    print(f"\n最終結果: {'SUCCESS' if success else 'FAILURE'}")