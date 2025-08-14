@echo off
echo ShiftAnalysis Backup
echo ===================

set BACKUP_DATE=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%
set BACKUP_DATE=%BACKUP_DATE: =0%
set BACKUP_DIR=production_backups\backup_%BACKUP_DATE%

mkdir "%BACKUP_DIR%" 2>nul

echo Backing up files...
xcopy /E /I /Y shift_suite "%BACKUP_DIR%\shift_suite\" >nul
copy *.py "%BACKUP_DIR%\" >nul
copy requirements.txt "%BACKUP_DIR%\" >nul

echo Backup completed: %BACKUP_DIR%
pause
