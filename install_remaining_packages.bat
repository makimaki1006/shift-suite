@echo off
echo ===== 残りの必要パッケージをインストール =====

echo psutilとその他のユーティリティをインストール中...
pip install psutil>=5.9.0
pip install XlsxWriter>=3.2.0
pip install python-pptx>=0.6.23

echo.
echo ===== インストール完了 =====
echo 動作確認テスト...
python -c "import psutil; print(f'psutil {psutil.__version__} installed successfully!')"

echo.
echo Dashアプリ起動: python dash_app.py

pause