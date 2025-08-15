@echo off
echo ===== 強制削除とクリーン再構築 =====

echo 1. プロセス終了（念のため）...
taskkill /f /im python.exe 2>nul
taskkill /f /im pip.exe 2>nul

echo 2. 管理者権限で強制削除...
rmdir /s /q venv-py311 2>nul
if exist venv-py311 (
    echo フォルダが残っています。手動削除を試行...
    rd /s /q venv-py311
)

echo 3. 少し待機...
timeout /t 2 /nobreak >nul

echo 4. 新環境作成...
python -m venv venv-py311

echo 5. アクティベート...
call venv-py311\Scripts\activate.bat

echo 6. requirements.txtからインストール...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ===== 完了 =====
echo アプリ起動: streamlit run app.py

pause