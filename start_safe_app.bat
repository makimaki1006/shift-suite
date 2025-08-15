@echo off
REM セーフモードアプリ起動スクリプト
echo Starting Safe Mode Shift Analysis App...

REM 仮想環境をアクティベート
call venv-py311\Scripts\activate.bat

REM Unicode環境設定
chcp 65001
set PYTHONIOENCODING=utf-8

REM セーフモードアプリを起動
echo Starting Streamlit app in safe mode...
streamlit run app_safe.py --server.port 8501

pause