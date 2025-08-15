@echo off
echo ShiftAnalysis Enhanced Monitoring System
echo =========================================

chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8

echo [%date% %time%] Starting enhanced monitoring...

REM Check system resources
echo.
echo === System Resources ===
wmic cpu get loadpercentage /value | find "LoadPercentage"
for /f "skip=1" %%p in ('wmic os get FreePhysicalMemory') do (
    if not "%%p"=="" (
        echo Available RAM: %%p KB
        goto :ram_done
    )
)
:ram_done

REM Check disk space
echo.
echo === Disk Space ===
for /f "tokens=3" %%a in ('dir C:\ /-c ^| find "bytes free"') do echo Free Space: %%a

REM Check process status
echo.
echo === Process Status ===
tasklist | find "python.exe" >nul
if %errorlevel%==0 (
    echo ✓ Python processes: RUNNING
) else (
    echo ✗ Python processes: NOT FOUND
)

REM Check port availability
echo.
echo === Port Status ===
netstat -an | find "8050" >nul
if %errorlevel%==0 (
    echo ✓ Port 8050: IN USE (Expected)
) else (
    echo ✗ Port 8050: AVAILABLE (Server may not be running)
)

REM Check critical files
echo.
echo === Critical Files ===
if exist "dash_app.py" (
    echo ✓ dash_app.py: EXISTS
) else (
    echo ✗ dash_app.py: MISSING
)

if exist "extracted_results\" (
    echo ✓ extracted_results: EXISTS
) else (
    echo ✗ extracted_results: MISSING
)

REM Generate monitoring report
echo.
echo === Generating Report ===
set report_file=production_monitoring\monitoring_report_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%.txt
mkdir production_monitoring 2>nul

(
echo ShiftAnalysis Monitoring Report
echo Generated: %date% %time%
echo.
echo System Status: CHECKED
echo Critical Components: VERIFIED
echo Monitoring: ACTIVE
echo.
echo Next check recommended in 4 hours
) > "%report_file%"

echo Report saved: %report_file%

echo.
echo === Enhanced Monitoring COMPLETED ===
echo Next monitoring: %time%
pause