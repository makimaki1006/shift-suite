@echo off
REM 依存関係インストールスクリプト (Windows用)
REM IA1: pandas依存関係の解決

echo 🚀 シフト分析システム依存関係インストール開始...
echo 📅 実行時刻: %date% %time%

REM Python環境確認
echo.
echo 📦 Python環境確認...
python --version

REM 必須パッケージリスト
echo.
echo 📋 インストール対象パッケージ:
echo   - pandas (データ分析基盤)
echo   - numpy (数値計算)
echo   - openpyxl (Excel読み書き)
echo   - scikit-learn (機械学習)
echo   - plotly (可視化)
echo   - dash (ダッシュボード)

REM pip更新
echo.
echo 🔧 pip更新...
python -m pip install --upgrade pip

REM 基本パッケージインストール
echo.
echo 📦 基本パッケージインストール...
python -m pip install pandas numpy openpyxl

REM 分析関連パッケージ
echo.
echo 📊 分析関連パッケージインストール...
python -m pip install scikit-learn scipy statsmodels

REM 可視化関連パッケージ
echo.
echo 📈 可視化関連パッケージインストール...
python -m pip install plotly dash dash-bootstrap-components

REM その他必要パッケージ
echo.
echo 🔧 その他必要パッケージインストール...
python -m pip install xlrd xlwt python-dateutil pytz

REM インストール確認
echo.
echo ✅ インストール確認...
python -c "import pandas; import numpy; import openpyxl; import sklearn; import plotly; import dash; print('✅ pandas version:', pandas.__version__); print('✅ numpy version:', numpy.__version__); print('✅ openpyxl version:', openpyxl.__version__); print('✅ scikit-learn version:', sklearn.__version__); print('✅ plotly version:', plotly.__version__); print('✅ dash version:', dash.__version__)"

echo.
echo 🎉 依存関係インストール完了!
echo 📅 完了時刻: %date% %time%
pause