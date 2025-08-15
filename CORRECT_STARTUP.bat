@echo off
echo 🔧 修正済みシフト分析システム起動 (完全版)
echo ================================================

cd /d "C:\Users\fuji1\OneDrive\デスクトップ\シフト分析"

echo 📂 作業ディレクトリ: %CD%

echo 🐍 Python仮想環境を有効化中...
call "venv-py311\Scripts\activate.bat"

echo 📦 requirements.txtから必要パッケージをインストール中...
echo (すでにインストール済みの場合はスキップされます)
pip install -r requirements.txt

echo.
echo 🎯 修正内容確認:
echo   ✅ 不足時間問題: 26245h → 正常値に修正済み
echo   ✅ 職種別ヒートマップ: 正確なneed値表示
echo   ✅ 古いコピーファイル削除済み
echo.

echo 🚀 アプリケーション選択:
echo   [1] Streamlitアプリ (推奨)
echo   [2] Dashアプリ
echo.

set /p choice="起動方法を選択してください (1 または 2): "

if "%choice%"=="1" (
    echo 🌟 Streamlitアプリを起動しています...
    echo 🌐 ブラウザで自動的に開かれます
    streamlit run app.py
) else if "%choice%"=="2" (
    echo 📊 Dashアプリを起動しています...
    echo 🌐 ブラウザでアクセス: http://localhost:8050
    python dash_app.py
) else (
    echo ❌ 無効な選択です。デフォルトでStreamlitを起動します...
    streamlit run app.py
)

echo.
echo ✨ アプリケーションが起動しました！
echo 🔍 修正効果を確認してください:
echo   - 概要タブの不足時間が正常値になっているか
echo   - 職種別ヒートマップが正しく表示されているか
echo.

pause