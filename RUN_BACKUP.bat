@echo off
chcp 65001 > nul
echo =====================================
echo 包括的バックアップシステム
echo Comprehensive Backup System
echo =====================================
echo.
echo このスクリプトは以下を実行します:
echo 1. 完全バックアップ（全ファイル）
echo 2. 重要ファイルの検証
echo 3. ZIPアーカイブ作成
echo 4. 復元手順書作成
echo.
echo 準備はよろしいですか？
pause

echo.
echo バックアップを開始します...
python create_comprehensive_backup.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ バックアップが正常に完了しました！
    echo.
    echo 次のステップ:
    echo 1. バックアップフォルダを確認
    echo 2. C:\ShiftAnalysis にフォルダを移動
    echo 3. 新しい場所で仮想環境を構築
) else (
    echo.
    echo ❌ バックアップに失敗しました
    echo ログファイル backup_creation.log を確認してください
)

echo.
pause