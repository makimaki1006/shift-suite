# 包括的バックアップ実行 PowerShell スクリプト
# Comprehensive Backup Execution PowerShell Script

param(
    [switch]$AutoConfirm = $false,
    [string]$BackupLocation = "",
    [switch]$SkipZip = $false,
    [switch]$Verbose = $false
)

# エンコーディング設定
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ログ関数
function Write-LogMessage {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage
    Add-Content -Path "backup_execution.log" -Value $logMessage -Encoding UTF8
}

# メイン実行
function Start-ComprehensiveBackup {
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "       包括的バックアップシステム" -ForegroundColor Green
    Write-Host "    Comprehensive Backup System" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    
    # 現在のディレクトリ確認
    $currentDir = Get-Location
    Write-LogMessage "現在のディレクトリ: $currentDir"
    
    # 重要ファイル存在確認
    $criticalFiles = @(
        "app.py",
        "dash_app.py", 
        "requirements.txt",
        "shift_suite\tasks\ai_comprehensive_report_generator.py",
        "shift_suite\tasks\blueprint_deep_analysis_engine.py",
        "shift_suite\tasks\integrated_mece_analysis_engine.py",
        "shift_suite\tasks\predictive_optimization_integration_engine.py"
    )
    
    Write-Host "重要ファイル存在確認:" -ForegroundColor Yellow
    $missingFiles = @()
    foreach ($file in $criticalFiles) {
        if (Test-Path $file) {
            Write-Host "✓ $file" -ForegroundColor Green
        } else {
            Write-Host "✗ $file" -ForegroundColor Red
            $missingFiles += $file
        }
    }
    
    if ($missingFiles.Count -gt 0) {
        Write-Host ""
        Write-Host "警告: 重要ファイルが不足しています" -ForegroundColor Red
        Write-Host "続行しますか？ (y/n): " -NoNewline
        if (-not $AutoConfirm) {
            $response = Read-Host
            if ($response -ne "y") {
                Write-LogMessage "バックアップをキャンセルしました" "WARN"
                return $false
            }
        }
    }
    
    # ディスク容量確認
    $sourceSize = (Get-ChildItem -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1GB
    Write-Host ""
    Write-Host "ソースディレクトリサイズ: $([math]::Round($sourceSize, 2)) GB" -ForegroundColor Cyan
    
    if ($sourceSize -gt 5) {
        Write-Host "大容量バックアップです。時間がかかる可能性があります。" -ForegroundColor Yellow
        if (-not $AutoConfirm) {
            Write-Host "続行しますか？ (y/n): " -NoNewline
            $response = Read-Host
            if ($response -ne "y") {
                return $false
            }
        }
    }
    
    # Python スクリプト実行確認
    Write-Host ""
    Write-Host "Pythonバックアップスクリプトを実行します..." -ForegroundColor Green
    
    if (-not $AutoConfirm) {
        Write-Host "実行しますか？ (y/n): " -NoNewline
        $response = Read-Host
        if ($response -ne "y") {
            Write-LogMessage "バックアップをキャンセルしました" "WARN"
            return $false
        }
    }
    
    # Python スクリプト実行
    Write-Host ""
    Write-Host "バックアップ実行中..." -ForegroundColor Green
    Write-LogMessage "Pythonバックアップスクリプト開始"
    
    try {
        $process = Start-Process -FilePath "python" -ArgumentList "create_comprehensive_backup.py" -Wait -PassThru -NoNewWindow
        
        if ($process.ExitCode -eq 0) {
            Write-Host ""
            Write-Host "✅ バックアップが正常に完了しました！" -ForegroundColor Green
            Write-LogMessage "バックアップ正常完了"
            
            # バックアップフォルダ確認
            $backupFolders = Get-ChildItem -Directory | Where-Object { $_.Name -match ".*_backup_\d{8}_\d{6}" } | Sort-Object LastWriteTime -Descending
            if ($backupFolders.Count -gt 0) {
                $latestBackup = $backupFolders[0]
                Write-Host ""
                Write-Host "📁 バックアップフォルダ: $($latestBackup.FullName)" -ForegroundColor Cyan
                Write-Host "📄 復元手順書: $($latestBackup.FullName)\RESTORATION_GUIDE_*.md" -ForegroundColor Cyan
                
                # 次のステップ表示
                Write-Host ""
                Write-Host "次のステップ:" -ForegroundColor Yellow
                Write-Host "1. バックアップの確認が完了したら..." -ForegroundColor White
                Write-Host "2. フォルダを C:\ShiftAnalysis に移動" -ForegroundColor White
                Write-Host "3. 新しい場所で仮想環境を再構築" -ForegroundColor White
                
                # 自動移動オプション
                if (-not $AutoConfirm) {
                    Write-Host ""
                    Write-Host "バックアップ確認後、自動的にフォルダ移動を実行しますか？ (y/n): " -NoNewline
                    $moveResponse = Read-Host
                    if ($moveResponse -eq "y") {
                        Start-FolderMove
                    }
                }
            }
            
            return $true
        } else {
            Write-Host ""
            Write-Host "❌ バックアップに失敗しました" -ForegroundColor Red
            Write-LogMessage "バックアップ失敗" "ERROR"
            Write-Host "詳細: backup_creation.log を確認してください" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "エラー: $_" -ForegroundColor Red
        Write-LogMessage "実行エラー: $_" "ERROR"
        return $false
    }
}

function Start-FolderMove {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Blue
    Write-Host "       フォルダ移動実行" -ForegroundColor Blue  
    Write-Host "========================================" -ForegroundColor Blue
    
    $sourcePath = Get-Location
    $targetPath = "C:\ShiftAnalysis"
    
    Write-Host "移動元: $sourcePath" -ForegroundColor Cyan
    Write-Host "移動先: $targetPath" -ForegroundColor Cyan
    
    try {
        if (Test-Path $targetPath) {
            Write-Host "警告: 移動先が既に存在します" -ForegroundColor Yellow
            Write-Host "上書きしますか？ (y/n): " -NoNewline
            $overwrite = Read-Host
            if ($overwrite -ne "y") {
                return
            }
            Remove-Item $targetPath -Recurse -Force
        }
        
        Write-Host "フォルダ移動中..." -ForegroundColor Green
        Move-Item -Path $sourcePath -Destination $targetPath -Force
        
        Write-Host "✅ フォルダ移動完了!" -ForegroundColor Green
        Write-Host "新しい場所: $targetPath" -ForegroundColor Cyan
        
        # 次のステップ案内
        Write-Host ""
        Write-Host "次のステップ:" -ForegroundColor Yellow
        Write-Host "1. cd C:\ShiftAnalysis" -ForegroundColor White
        Write-Host "2. python -m venv venv" -ForegroundColor White
        Write-Host "3. .\venv\Scripts\Activate.ps1" -ForegroundColor White
        Write-Host "4. pip install -r requirements.txt" -ForegroundColor White
        
    } catch {
        Write-Host "移動エラー: $_" -ForegroundColor Red
        Write-LogMessage "移動エラー: $_" "ERROR"
    }
}

# メイン実行
if ($args.Count -eq 0 -or $args[0] -ne "-NoInteractive") {
    Start-ComprehensiveBackup
} else {
    # 非対話モード
    Start-ComprehensiveBackup -AutoConfirm
}