import dash
from flask import jsonify
import os
import logging
import io
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# アプリケーションモジュール（必要なもののみ）
from app_layout import create_main_layout
from app_callbacks import register_callbacks
# 注意: 以下のモジュールは現在未使用のためコメントアウト
# import data_processing
# import visualization
# import utils  
# import config
# import state_manager

# ロガー設定 (dash_app.py から移動)
LOG_LEVEL = logging.DEBUG
log_stream = io.StringIO() 

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.StreamHandler(stream=log_stream)
    ],
    force=True
)
log = logging.getLogger(__name__)

# Dashアプリケーション初期化（レスポンシブ対応）
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        {"name": "description", "content": "Shift-Suite 高速分析ビューア - レスポンシブ対応"},
        {"charset": "utf-8"}
    ]
)
server = app.server
app.title = "Shift-Suite 高速分析ビューア"

# レスポンシブCSSをHTMLヘッダーに追加
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
        /* レスポンシブベーススタイル */
        @media (max-width: 768px) {
            .mobile-hide { display: none !important; }
            .container { padding: 10px !important; }
            .card { margin: 5px 0 !important; }
        }
        @media (min-width: 769px) and (max-width: 1024px) {
            .tablet-hide { display: none !important; }
            .container { padding: 15px !important; }
        }
        @media (min-width: 1025px) {
            .desktop-only { display: block !important; }
        }
        
        /* 共通レスポンシブスタイル */
        .responsive-container {
            max-width: 100%;
            overflow-x: auto;
        }
        .responsive-grid {
            display: grid;
            gap: 15px;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        }
        .responsive-card {
            background: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }
        .responsive-card:hover {
            transform: translateY(-2px);
            box_shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Flask error handlers (dash_app.py から移動)
@server.errorhandler(Exception)
def handle_exception(e):
    log.exception("Unhandled exception in request:")
    if os.environ.get('DASH_ENV') == 'production':
        error_info = {
            "error": "Internal server error",
            "message": "システムエラーが発生しました。しばらく時間をおいて再試行してください。"
        }
    else:
        error_info = {
            "error": str(e),
            "type": type(e).__name__,
            "message": "開発環境でのデバッグ情報です"
        }
    return jsonify(error_info), 500

@server.errorhandler(500)
def handle_500(e):
    log.error(f"500 error occurred: {str(e)}")
    return jsonify({
        "error": "Internal server error",
        "message": "サーバー内部でエラーが発生しました。"
    }), 500

# モジュールは上部でインポート済み

# アプリケーションのレイアウトを設定
app.layout = create_main_layout()

# コールバック関数を登録 (dash_app依存を完全に除去)
# 修正: dash_app_refは常にNoneを渡すように変更
register_callbacks(app, dash_app_ref=None)
log.info("Callbacks registered without dash_app reference (dependency removed)")

# アプリケーションの実行
if __name__ == '__main__':
    # Development mode: debug=True for detailed error messages
    # ポート8080を使用（8050がブロックされているため）
    print("Starting server on port 8080 (port 8050 was blocked)")
    print("Access at: http://localhost:8080")
    app.run(debug=True, port=8080, host='0.0.0.0')