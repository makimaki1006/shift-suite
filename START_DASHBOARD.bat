@echo off
echo 🔧 修正済みシフト分析ダッシュボード起動
echo ==========================================

cd /d "C:\Users\fuji1\OneDrive\デスクトップ\シフト分析"

echo 📂 作業ディレクトリ: %CD%

echo 🐍 Python仮想環境を有効化しています...
call "venv-py311\Scripts\activate.bat"

echo 📦 必要パッケージをインストール中...
pip install dash plotly pandas numpy openpyxl

echo 🚀 ダッシュボードを起動しています...
echo ✅ 修正内容: 不足時間正常化、職種別ヒートマップ修正
echo 🌐 ブラウザでアクセス: http://localhost:8050

python start_dashboard.py

pause