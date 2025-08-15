@echo off
echo ===== 仮想環境再作成スクリプト =====

echo 既存の仮想環境を削除中...
if exist venv-py311 (
    rmdir /s /q venv-py311
    echo 既存環境削除完了
) else (
    echo 既存環境は見つかりませんでした
)

echo.
echo 新しい仮想環境を作成中...
python -m venv venv-py311

echo.
echo 仮想環境をアクティベート中...
call venv-py311\Scripts\activate.bat

echo.
echo pipをアップグレード中...
python -m pip install --upgrade pip

echo.
echo 基本パッケージをインストール中...
pip install pandas==2.2.3
pip install numpy==1.26.4
pip install openpyxl==3.1.5

echo.
echo Webフレームワークをインストール中（安定版）...
pip install plotly==5.20.0
pip install streamlit==1.44.0
pip install dash==2.16.1
pip install dash-bootstrap-components==1.7.0

echo.
echo その他必要パッケージをインストール中...
pip install matplotlib==3.8.4
pip install pyarrow==17.0.0
pip install scikit-learn==1.4.2

echo.
echo ===== 仮想環境再作成完了 =====
echo 以下のコマンドでアプリを起動してください：
echo   venv-py311\Scripts\activate.bat
echo   streamlit run app.py

pause