@echo off
REM Unicode環境の修正
echo Fixing Unicode environment...

REM コンソールコードページをUTF-8に設定
chcp 65001

REM Python環境変数の設定
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSFSENCODING=1

REM 仮想環境をアクティベート
call venv-py311\Scripts\activate.bat

echo Unicode environment fixed!
echo You can now run: python dash_app.py

pause