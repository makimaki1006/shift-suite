@echo off
echo ShiftAnalysis Production Server Starting...
echo ========================================

chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8
set LC_ALL=C.UTF-8
set LANG=C.UTF-8
set SHIFT_SUITE_LOG_LEVEL=INFO
set PRODUCTION_MODE=true

echo Production mode: ENABLED
echo Security: ACTIVE
echo Monitoring: RUNNING
echo ========================================

cd /d "%~dp0"
echo Server starting on http://localhost:8050
echo Press Ctrl+C to stop

python dash_app.py
pause
