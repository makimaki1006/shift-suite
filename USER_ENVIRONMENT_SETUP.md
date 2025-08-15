# 🔧 **ユーザー環境構築ガイド**

## **システム要件**

### **必須要件**
- **OS**: Windows 10 (1909以降) または Windows 11
- **メモリ**: 8GB以上 (推奨: 16GB)
- **ストレージ**: 空き容量2GB以上
- **ネットワーク**: インターネット接続 (初回セットアップ時)

### **推奨要件**  
- **CPU**: Intel Core i5以上 または AMD Ryzen 5以上
- **ディスプレイ**: 1920x1080以上の解像度
- **ブラウザ**: Chrome 90+ / Edge 90+ / Firefox 90+

### **追加ソフトウェア**
- **Microsoft Excel**: 2016以降 (データ編集・確認用)
- **PDF閲覧ソフト**: Adobe Acrobat Reader DC推奨

---

## 📦 **自動インストールパッケージ**

### **ShiftAnalysis Installer v1.0**

**パッケージ構成**:
```
ShiftAnalysis_Installer_v1.0/
├── install.bat                    # 自動インストールスクリプト
├── requirements.txt               # Python依存関係
├── sample_data/                   # サンプルデータセット
│   ├── sample_shift_basic.xlsx
│   ├── sample_shift_large.xlsx
│   └── sample_shift_japanese.xlsx
├── docs/                         # ドキュメント
│   ├── quick_start_guide.pdf
│   ├── user_manual.pdf
│   └── troubleshooting.pdf
└── shift_suite/                  # アプリケーション本体
    ├── app.py
    ├── dash_app.py
    └── [その他システムファイル]
```

### **簡単インストール手順**

#### **Step 1: パッケージダウンロード**
1. 配布されたインストーラーをダウンロード
2. `ShiftAnalysis_Installer_v1.0.zip` を任意のフォルダに展開
3. 展開先フォルダを確認 (例: `C:\ShiftAnalysis\`)

#### **Step 2: 自動インストール実行**
1. `install.bat` を **右クリック** → **管理者として実行**
2. インストール処理の完了を待機 (5-10分)
3. 「インストール完了」メッセージの確認

#### **Step 3: 初回起動テスト**
1. デスクトップの `ShiftAnalysis` ショートカットをダブルクリック
2. ブラウザが自動起動・ダッシュボード表示確認
3. サンプルデータでのテスト実行

---

## 🛠 **手動インストール手順 (上級者向け)**

### **Python環境構築**

#### **Python 3.11+ インストール**
1. [Python公式サイト](https://www.python.org/downloads/)からPython 3.11以降をダウンロード
2. インストーラー実行時に「Add Python to PATH」をチェック
3. インストール完了後、コマンドプロンプトで確認:
   ```cmd
   python --version
   pip --version
   ```

#### **仮想環境作成**
```cmd
cd C:\ShiftAnalysis
python -m venv venv-py311
venv-py311\Scripts\activate
```

#### **依存関係インストール**
```cmd
pip install --upgrade pip
pip install -r requirements.txt
```

### **アプリケーション設定**

#### **設定ファイル配置**
1. `config/` フォルダ内の設定ファイル確認
2. 必要に応じて `config.json` の編集
3. ログレベル・出力パスの設定

#### **初期データ準備**
1. `sample_data/` フォルダ内のサンプルファイル確認  
2. 実際のシフトデータでのテスト準備
3. バックアップ・復旧手順の確認

---

## 🚀 **起動・実行方法**

### **通常起動**
```cmd
# 方法1: バッチファイル使用
start_dashboard_production.bat

# 方法2: 直接起動
venv-py311\Scripts\python dash_app.py
```

### **本番モード起動 (推奨)**
```cmd
start_dashboard_production.bat
```
- UTF-8エンコーディング自動設定
- 静寂ログモード有効
- 最適化された本番設定

### **開発・デバッグモード起動**
```cmd
venv-py311\Scripts\python dash_app.py --debug
```
- 詳細ログ出力有効
- 自動リロード機能
- エラー詳細表示

---

## 📱 **ブラウザアクセス**

### **アクセス方法**
- **本番モード**: システム起動後、ブラウザが自動起動
- **手動アクセス**: http://localhost:8050
- **ネットワークアクセス**: http://[PC-IP]:8050 (同一ネットワーク内)

### **対応ブラウザ**
- ✅ **Chrome** 90+ (推奨)
- ✅ **Microsoft Edge** 90+ 
- ✅ **Firefox** 90+
- ⚠️ **Internet Explorer**: 非対応

### **ブラウザ設定**
- JavaScript: 有効
- Cookie: 有効  
- ローカルストレージ: 有効
- ポップアップブロック: 無効 (ShiftAnalysisドメイン)

---

## 🔧 **トラブルシューティング**

### **よくある問題と解決方法**

#### **問題1: Pythonが認識されない**
**症状**: 「'python' は、内部コマンドまたは外部コマンド...」エラー
**解決方法**:
1. Python インストール確認
2. 環境変数 PATH に Python パス追加
3. コマンドプロンプト再起動

#### **問題2: 依存パッケージエラー**
**症状**: 「ModuleNotFoundError」エラー
**解決方法**:
```cmd
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

#### **問題3: 文字化け発生**  
**症状**: 日本語が「��」で表示
**解決方法**:
1. `start_dashboard_production.bat` 使用
2. 環境変数設定:
   ```cmd
   set PYTHONIOENCODING=utf-8
   chcp 65001
   ```

#### **問題4: ポートエラー**
**症状**: 「Port 8050 is already in use」エラー
**解決方法**:
```cmd
# 使用中プロセス確認
netstat -ano | findstr :8050

# プロセス終了 (PID確認後)
taskkill /PID [PID番号] /F
```

#### **問題5: ファイルアップロードエラー**
**症状**: Excelファイルが読み込めない
**解決方法**:
1. ファイル形式確認 (.xlsx/.xls)
2. ファイルが他アプリで開いていないか確認
3. ファイル権限・アクセス権限確認
4. サンプルデータでのテスト

### **高度な問題対応**

#### **ログ確認方法**
```cmd
# システムログ確認
type shift_suite.log

# エラーログ確認  
type shortage_analysis.log
```

#### **設定リセット**
```cmd
# 設定ファイル初期化
copy config\default_config.json config\config.json

# キャッシュクリア
rmdir /s /q __pycache__
rmdir /s /q .streamlit
```

#### **完全再インストール**
```cmd
# 仮想環境削除
rmdir /s /q venv-py311

# 再インストール実行
install.bat
```

---

## 📞 **サポート体制**

### **サポート時間**
- **平日**: 9:00-18:00 (JST)
- **土日祝**: メール対応のみ

### **連絡方法**
- **メール**: support@shiftanalysis.com
- **電話**: 03-XXXX-XXXX (平日のみ)
- **チャット**: ダッシュボード内サポートチャット

### **サポートレベル**
- **Level 1**: 基本操作・設定サポート
- **Level 2**: 技術的問題・エラー対応
- **Level 3**: カスタマイズ・高度設定

### **事前準備情報**
サポート依頼時は以下情報をお知らせください:
- OS・ブラウザバージョン
- エラーメッセージの正確な内容
- 問題発生時の操作手順
- ログファイル (可能な場合)

---

## 📋 **環境確認チェックリスト**

### **インストール前確認**
- [ ] システム要件充足確認
- [ ] 管理者権限での実行権限確認
- [ ] インターネット接続確認
- [ ] ウイルス対策ソフトの例外設定

### **インストール後確認**
- [ ] Python・pip 動作確認
- [ ] 依存パッケージインストール完了
- [ ] アプリケーション起動成功
- [ ] ブラウザアクセス成功
- [ ] サンプルデータ処理成功

### **本番使用前確認**
- [ ] 実データでの動作確認  
- [ ] 文字化け無し確認
- [ ] パフォーマンス確認
- [ ] エクスポート機能確認
- [ ] バックアップ・復旧手順確認

---

## 🔄 **アップデート手順**

### **自動アップデート (推奨)**
1. ダッシュボード内「アップデート確認」クリック
2. 新バージョン検出時の自動ダウンロード・適用
3. システム再起動・動作確認

### **手動アップデート**
1. 新バージョンインストーラーダウンロード
2. 既存データのバックアップ
3. インストーラー実行・上書きインストール
4. 設定・データ復旧・動作確認

---

**最終更新日**: 2025-08-12  
**対応バージョン**: ShiftAnalysis v1.0  
**サポート有効期限**: 2025年12月末まで