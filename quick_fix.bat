@echo off
echo ===== 仮想環境クイック再構築 =====

echo 1. 古い環境削除...
if exist venv-py311 rmdir /s /q venv-py311

echo 2. 新環境作成...
python -m venv venv-py311

echo 3. アクティベート...
call venv-py311\Scripts\activate.bat

echo 4. requirements.txtから一括インストール...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ===== 完了 =====
echo 以下でアプリ起動:
echo   streamlit run app.py
echo   または
echo   python dash_app.py

pause