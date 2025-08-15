@echo off
REM 実用制約発見システム起動スクリプト
echo Starting Practical Constraint Discovery System...

echo.
echo ====================================
echo   実用制約発見システム起動中...
echo ====================================
echo.

REM 現在のディレクトリを表示
echo Current Directory: %CD%
echo.

REM 仮想環境をアクティベート（存在する場合）
if exist "venv-py311\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv-py311\Scripts\activate.bat
) else (
    echo No virtual environment found, using system Python...
)

REM Unicode環境設定
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

REM 利用可能なExcelファイルをスキャン
echo Scanning for Excel files...
dir *.xlsx *.xls /b 2>nul
if errorlevel 1 (
    echo Warning: No Excel files found in current directory
    echo Please place Excel files in this directory for analysis
    echo.
)

REM Streamlitアプリを起動
echo.
echo Starting Streamlit application...
echo Access URL: http://localhost:8501
echo.
echo ====================================
echo   システム起動完了！ブラウザでアクセスしてください
echo ====================================
echo.

REM Streamlit実行
streamlit run practical_system_implementation.py --server.port 8501 --server.headless true

echo.
echo Application terminated.
pause