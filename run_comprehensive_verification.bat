@echo off
echo ========================================
echo 包括的アウトプット品質検証スクリプト実行
echo ========================================

cd /d "C:\ShiftAnalysis"

echo.
echo [1] Python環境確認...
python --version
if errorlevel 1 (
    echo Python が見つかりません。
    echo Python がインストールされているか確認してください。
    pause
    exit /b 1
)

echo.
echo [2] 必要なライブラリ確認...
python -c "import pandas, zipfile, json, pathlib; print('✓ 必要ライブラリ確認完了')"
if errorlevel 1 (
    echo 必要なライブラリが不足しています。
    echo pip install pandas を実行してください。
    pause
    exit /b 1
)

echo.
echo [3] 分析対象ファイル確認...
if exist "analysis_results (1).zip" (
    echo ✓ analysis_results (1).zip 発見
    dir "analysis_results (1).zip"
) else (
    echo ⚠ analysis_results (1).zip が見つかりません
)

if exist "analysis_results.zip" (
    echo ✓ analysis_results.zip 発見
    dir "analysis_results.zip"
) else (
    echo ⚠ analysis_results.zip が見つかりません
)

if exist "extracted_results" (
    echo ✓ extracted_results ディレクトリ発見
    dir "extracted_results" /s | find "File(s)"
) else (
    echo ⚠ extracted_results ディレクトリが見つかりません
)

echo.
echo [4] 包括的検証実行...
python comprehensive_output_verification.py

echo.
echo [5] 検証結果確認...
if exist "comprehensive_output_verification_results.json" (
    echo ✓ 検証結果ファイル生成完了
    echo 詳細結果: comprehensive_output_verification_results.json
) else (
    echo ❌ 検証結果ファイルが生成されませんでした
)

echo.
echo ========================================
echo 検証完了
echo ========================================
pause