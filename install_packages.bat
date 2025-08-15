@echo off
echo ===== Python 3.13対応パッケージインストール =====

echo 1. pipとsetuptoolsをアップグレード...
python -m pip install --upgrade pip setuptools wheel

echo 2. プリビルド版numpyを強制インストール...
pip install --only-binary=:all: numpy

echo 3. プリビルド版pandasをインストール...
pip install --only-binary=:all: pandas

echo 4. 基本パッケージをインストール...
pip install openpyxl pyarrow

echo 5. Webフレームワークをインストール...
pip install streamlit==1.44.0
pip install plotly==5.20.0
pip install dash==2.16.1
pip install dash-bootstrap-components==1.7.0
pip install matplotlib

echo.
echo ===== 完了 =====
echo テスト: python -c "import numpy, pandas, streamlit, plotly; print('All packages imported successfully!')"

pause