@echo off
REM scikit-learn DLL依存関係問題の修正スクリプト
echo Fixing scikit-learn DLL dependencies...

REM 仮想環境をアクティベート
call venv-py311\Scripts\activate.bat

REM scikit-learnを再インストール（軽量版）
echo Reinstalling scikit-learn...
pip uninstall scikit-learn -y
pip install scikit-learn==1.4.2

REM lightgbmを再インストール（軽量版）
echo Reinstalling lightgbm...
pip uninstall lightgbm -y
pip install lightgbm==4.1.0

REM Visual C++ Redistributableの確認
echo Checking Visual C++ Redistributable...
echo If still having issues, please install Visual C++ Redistributable 2019-2022

echo DLL fix completed!
pause