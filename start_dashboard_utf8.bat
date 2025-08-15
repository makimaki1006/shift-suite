@echo off
echo Starting ShiftAnalysis Dashboard with UTF-8 encoding...
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=0
python dash_app.py
pause
