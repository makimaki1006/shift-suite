@echo off
echo ShiftAnalysis Health Check
echo =========================

chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8

echo [1/3] Python environment...
python --version

echo [2/3] Dependencies...
python -c "import pandas, dash, streamlit; print('Dependencies: OK')"

echo [3/3] Configuration...
if exist production_config\config.json (
    echo Configuration: OK
) else (
    echo Configuration: MISSING
)

echo Health check completed
pause
