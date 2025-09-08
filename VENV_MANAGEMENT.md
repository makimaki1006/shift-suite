# venv環境管理ガイド (Python 3.13対応)

## 現在の環境状態
- Python Version: 3.13.5
- 主要パッケージ:
  - ✅ plotly 6.3.0 (Python 3.13対応済み)
  - ✅ streamlit 1.47.1 (動作確認済み)
  - ✅ pandas 2.3.1
  - ✅ dash 3.2.0
  - ✅ flask 3.1.1

## 初歩的なミスを防ぐチェックリスト

### 1. 環境確認コマンド
```powershell
# venv環境の確認
.\venv\Scripts\Activate.ps1
python --version
pip show plotly streamlit pandas dash flask
```

### 2. 問題が発生した時の対処法

#### ❌ Plotly構文エラー (Python 3.13)
```
SyntaxError: positional argument follows keyword argument
```
**解決策:**
```powershell
.\venv\Scripts\Activate.ps1
pip install plotly>=6.0.0
```

#### ❌ パッケージバージョン不一致
**解決策:**
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements_py313.txt
```

### 3. 環境の一貫性チェック
```powershell
.\venv\Scripts\Activate.ps1
python check_venv_consistency.py
```

### 4. アプリケーション起動方法

#### Streamlit (app.py)
```powershell
.\venv\Scripts\Activate.ps1
streamlit run app.py
```

#### Dash (dash_app.py)
```powershell
.\venv\Scripts\Activate.ps1
python dash_app.py
```

### 5. 重要な注意事項

1. **必ずvenv環境をアクティベート**してから作業する
2. **システム全体のPython**とvenv環境のPythonを混同しない
3. パッケージインストール時は**どの環境**にインストールしているか確認
4. Python 3.13では**plotly 6.0以上が必須**

### 6. トラブルシューティング

| 問題 | 原因 | 解決策 |
|------|------|--------|
| Plotly構文エラー | plotly < 6.0 | `pip install plotly>=6.3.0` |
| streamlit起動失敗 | venv未アクティベート | `.\venv\Scripts\Activate.ps1` |
| パッケージが見つからない | 別環境にインストール | venv環境で再インストール |
| エンコーディングエラー | Windows cp932 | コードに`sys.stdout.reconfigure(encoding='utf-8')`追加 |

### 7. 定期メンテナンス

月1回実行推奨:
```powershell
.\venv\Scripts\Activate.ps1
python check_venv_consistency.py
pip list --outdated
```

## 今回の教訓
- エラー発生時は**まず環境を確認**
- venv環境とシステム環境を**明確に区別**
- Python 3.13への移行時は**互換性を事前確認**