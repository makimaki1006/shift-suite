@echo off
echo ===== 不足ライブラリの一括インストール =====

echo 機械学習・統計パッケージをインストール中...
pip install scikit-learn>=1.4.0
pip install lightgbm>=4.0.0
pip install scipy>=1.11.0
pip install statsmodels>=0.14.0
pip install networkx>=3.0

echo.
echo ===== インストール完了 =====
echo 動作確認テスト...
python -c "import sklearn, lightgbm, scipy, statsmodels, networkx; print('All ML packages imported successfully!')"

echo.
echo アプリ起動: streamlit run app.py

pause