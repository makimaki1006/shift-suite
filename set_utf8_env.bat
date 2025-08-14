@echo off
echo Setting UTF-8 environment for ShiftAnalysis...

chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8
set LC_ALL=C.UTF-8
set LANG=C.UTF-8

echo UTF-8 environment configured successfully.
echo PYTHONIOENCODING=%PYTHONIOENCODING%
echo PYTHONLEGACYWINDOWSSTDIO=%PYTHONLEGACYWINDOWSSTDIO%
echo.
echo Ready for production use.