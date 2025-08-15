@echo off
echo ===== キャッシュクリアと再起動手順 =====

echo.
echo 1. 古いキャッシュファイルを削除...
if exist analysis_results* (
    echo 既存の分析結果を削除しています...
    for /d %%i in (analysis_results*) do (
        rmdir /s /q "%%i" 2>nul
    )
)

echo.
echo 2. 一時ファイルを削除...
if exist temp*.xlsx del /f temp*.xlsx
if exist __pycache__ rmdir /s /q __pycache__
if exist shift_suite\__pycache__ rmdir /s /q shift_suite\__pycache__
if exist shift_suite\tasks\__pycache__ rmdir /s /q shift_suite\tasks\__pycache__

echo.
echo ===== クリーニング完了 =====
echo.
echo 次の手順でアプリを起動してください：
echo 1. venv-py311\Scripts\activate.bat
echo 2. streamlit run app.py
echo 3. Excelファイルをアップロード
echo 4. "Run Analysis"ボタンをクリック
echo.
echo ログで [RestExclusion] メッセージを確認してください。

pause