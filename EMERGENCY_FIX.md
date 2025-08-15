# 🚨 緊急修復ガイド

## 問題
仮想環境が壊れており、pip自体が動作しません。

## 解決手順

### 1. 仮想環境再作成（推奨）
```powershell
# PowerShellで実行
.\recreate_venv.bat
```

### 2. 手動での再作成
```powershell
# 1. 古い環境削除
Remove-Item -Recurse -Force venv-py311

# 2. 新環境作成
python -m venv venv-py311

# 3. アクティベート
.\venv-py311\Scripts\Activate.ps1

# 4. 基本パッケージインストール
python -m pip install --upgrade pip
pip install pandas==2.2.3 numpy==1.26.4 openpyxl==3.1.5
pip install plotly==5.20.0 streamlit==1.44.0 dash==2.16.1
pip install pyarrow==17.0.0 matplotlib==3.8.4
```

### 3. システムPython使用（一時的）
```powershell
# 仮想環境なしで直接実行
python -m pip install plotly==5.20.0 streamlit==1.44.0
python app.py
```

## 原因
- 最新plotlyパッケージのnarwhalsライブラリがWindows環境でファイルシステムエラー
- pip実行ファイル自体が影響を受けた

## 対策
- requirements.txtを安定版バージョンに固定済み
- 今後は指定バージョンのみ使用