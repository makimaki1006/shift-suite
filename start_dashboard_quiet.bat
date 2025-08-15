@echo off
echo Starting ShiftAnalysis Dashboard (Quiet Mode)...
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=0
set SHIFT_SUITE_LOG_LEVEL=WARNING
set ANALYSIS_LOG_LEVEL=ERROR
python dash_app.py 2>nul
pause
