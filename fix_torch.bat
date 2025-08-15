@echo off
echo Fixing PyTorch circular import error...
echo =====================================

cd /d "C:\Users\fuji1\OneDrive\デスクトップ\シフト分析"

echo Activating virtual environment...
call "venv-py311\Scripts\activate.bat"

echo Uninstalling torch...
pip uninstall -y torch torchvision torchaudio

echo Clearing pip cache...
pip cache purge

echo Reinstalling torch...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

echo Testing torch import...
python -c "import torch; print('Torch version:', torch.__version__)"

echo.
echo Fix completed! Try running streamlit again:
echo streamlit run app.py
echo.
pause