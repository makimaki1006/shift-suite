# ShiftAnalysis - シフト分析ダッシュボード

## 概要
ShiftAnalysisは、シフト管理と人員配置を最適化するための包括的な分析ダッシュボードです。複数の分析手法を用いて、人員不足の予測、疲労度分析、コスト最適化などを行います。

## 機能
- 📊 **基本分析**: シフトパターンの可視化とヒートマップ
- 👥 **スタッフ分析**: 個別・チーム分析、疲労度、休暇、公平性評価
- 📈 **計画・予測**: 需要予測、採用計画、コスト分析
- 🤖 **高度な分析**: AI駆動の最適化とパターン認識

## 技術スタック
- **Frontend**: Streamlit / Dash
- **Backend**: Python 3.11+
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly, Matplotlib
- **ML/AI**: Scikit-learn, LightGBM, Prophet

## ローカル環境でのセットアップ

### 前提条件
- Python 3.11以上
- 8GB以上のRAM推奨

### インストール手順
```bash
# リポジトリのクローン
git clone https://github.com/YOUR_USERNAME/shiftanalysis.git
cd shiftanalysis

# 仮想環境の作成
python -m venv venv

# Windows
.\venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# 依存パッケージのインストール
pip install -r requirements.txt
```

### 起動方法

#### Streamlitアプリ
```bash
streamlit run app.py
```
ブラウザで http://localhost:8501 を開く

#### Dashアプリ
```bash
python dash_app.py
```
ブラウザで http://localhost:8050 を開く

## Render.comへのデプロイ

### 1. GitHubリポジトリの準備
1. このリポジトリをForkまたはClone
2. 自分のGitHubアカウントにPush

### 2. Renderでの設定
1. [Render.com](https://render.com)にサインイン
2. "New +" → "Web Service"を選択
3. GitHubリポジトリを接続
4. 以下の設定を使用：
   - **Name**: shiftanalysis
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements_render.txt`
   - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

### 3. 環境変数の設定
Renderダッシュボードで以下の環境変数を追加：
- `PYTHON_VERSION`: 3.11.0
- `STREAMLIT_SERVER_HEADLESS`: true
- `STREAMLIT_SERVER_ENABLE_CORS`: false

## データ形式
アプリケーションは以下の形式のデータを受け付けます：
- Excel (.xlsx)
- Parquet (.parquet)
- ZIP形式の分析結果

## プロジェクト構造
```
shiftanalysis/
├── app.py                 # Streamlitメインアプリ
├── dash_app.py           # Dashメインアプリ
├── shift_suite/          # 分析モジュール
│   └── tasks/           # 各種分析タスク
├── assets/              # スタイルシート
├── requirements.txt     # ローカル開発用
├── requirements_render.txt  # Renderデプロイ用
└── render.yaml         # Render設定ファイル
```

## トラブルシューティング

### Python 3.13でのエラー
Python 3.13を使用している場合は、`requirements_py313.txt`を使用してください：
```bash
pip install -r requirements_py313.txt
```

### メモリ不足エラー
大規模データセットの処理時は、Parquet形式の使用を推奨します。

## ライセンス
MIT License

## サポート
問題が発生した場合は、[Issues](https://github.com/YOUR_USERNAME/shiftanalysis/issues)で報告してください。