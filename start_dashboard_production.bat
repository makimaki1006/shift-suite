@echo off
echo ShiftAnalysis Dashboard - Production Mode
echo ========================================
echo * UTF-8 encoding enabled
echo * Quiet logging mode
echo * Production-ready configuration
echo ========================================
echo.

chcp 65001 > nul 2>&1
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=0
set SHIFT_SUITE_LOG_LEVEL=CRITICAL
set ANALYSIS_LOG_LEVEL=CRITICAL
set PYTHONWARNINGS=ignore

echo Starting dashboard...
python dash_app.py 2>nul

echo.
echo Dashboard stopped.
pause