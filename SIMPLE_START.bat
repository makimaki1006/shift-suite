@echo off
chcp 65001 > nul
echo Starting Shift Analysis System...
echo ================================

cd /d "C:\Users\fuji1\OneDrive\デスクトップ\シフト分析"

echo Current directory: %CD%

echo Activating Python virtual environment...
call "venv-py311\Scripts\activate.bat"

echo Installing all packages from requirements.txt...
pip install -r requirements.txt

echo.
echo Choose application:
echo [1] Streamlit (Recommended)
echo [2] Dash
echo.

set /p choice="Select option (1 or 2): "

if "%choice%"=="1" (
    echo Starting Streamlit app...
    streamlit run app.py
) else if "%choice%"=="2" (
    echo Starting Dash app...
    python dash_app.py
) else (
    echo Invalid choice. Starting Streamlit by default...
    streamlit run app.py
)

pause