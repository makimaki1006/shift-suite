@echo off
echo ===== StreamlitとPlotlyの依存関係問題修正 =====

echo 現在の仮想環境をアクティベート中...
call venv-py311\Scripts\activate.bat

echo.
echo 問題のあるパッケージをアンインストール...
pip uninstall -y narwhals plotly dash streamlit

echo.
echo 安定版パッケージを再インストール...
pip install plotly==5.20.0
pip install streamlit==1.44.0
pip install dash==2.16.1

echo.
echo 修正完了。アプリケーションを起動してください。
echo   streamlit run app.py
echo   または
echo   python dash_app.py

pause