@echo off
echo ===== Dash App完全依存関係インストール =====

echo 1. Dash関連パッケージをインストール...
pip install dash-cytoscape>=1.0.0

echo 2. システムユーティリティをインストール...
pip install psutil>=5.9.8

echo 3. Excel/ファイル処理関連をインストール...
pip install XlsxWriter>=3.2.0

echo 4. Flask（念のため確認）...
pip install flask

echo.
echo ===== インストール確認 =====
python -c "import dash_cytoscape; print(f'dash-cytoscape: OK')"
python -c "import psutil; print(f'psutil: OK')"
python -c "import xlsxwriter; print(f'XlsxWriter: OK')"
python -c "import flask; print(f'flask: OK')"

echo.
echo ===== 完了！=====
echo Dashアプリを起動: python dash_app.py

pause