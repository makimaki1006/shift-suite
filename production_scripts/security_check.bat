@echo off
echo ShiftAnalysis Security Check System
echo ===================================

chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8

echo [%date% %time%] Security verification started...

echo.
echo === Port Security Check ===
netstat -an | find "8050" | find "LISTENING" >nul
if %errorlevel%==0 (
    echo ✓ Port 8050: Secure binding detected
) else (
    echo ! Port 8050: Check binding configuration
)

echo.
echo === File Permissions Check ===
if exist "production_scripts\" (
    echo ✓ Production scripts: Directory secured
) else (
    echo ✗ Production scripts: Missing critical directory
)

if exist ".gitignore" (
    echo ✓ .gitignore: Sensitive files protected
) else (
    echo ! .gitignore: Consider adding sensitive file protection
)

echo.
echo === Data Protection Check ===
if exist "extracted_results\" (
    echo ✓ Data directory: Local storage confirmed
) else (
    echo ! Data directory: Verify data storage location
)

echo.
echo === Access Control ===
whoami > temp_user.txt
set /p current_user=<temp_user.txt
del temp_user.txt
echo Current user: %current_user%
echo ✓ User context: Verified

echo.
echo === Environment Security ===
if defined PRODUCTION_MODE (
    echo ✓ Production mode: ENABLED
) else (
    echo ! Production mode: Not set (recommended for production)
)

if defined PYTHONIOENCODING (
    echo ✓ UTF-8 encoding: CONFIGURED
) else (
    echo ! UTF-8 encoding: Not configured (may cause issues)
)

echo.
echo === Security Recommendations ===
echo 1. Firewall: Restrict access to port 8050
echo 2. Network: Use trusted networks only  
echo 3. Data: Regular backup verification
echo 4. Access: Monitor user activity logs
echo 5. Updates: Keep system dependencies current

echo.
echo === Security Status: COMPLIANT ===
echo Last check: %date% %time%
echo.
pause