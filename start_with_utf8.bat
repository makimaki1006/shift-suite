@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=0
python %*
