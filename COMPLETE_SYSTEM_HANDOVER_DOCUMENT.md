# 📚 シフト分析システム完全引継ぎ文書

## 目次
1. [プロジェクト概要](#1-プロジェクト概要)
2. [システム全体のデータフロー](#2-システム全体のデータフロー)
3. [各モジュールの詳細と関連性](#3-各モジュールの詳細と関連性)
4. [データ処理の詳細フロー](#4-データ処理の詳細フロー)
5. [主要機能の動作原理](#5-主要機能の動作原理)
6. [開発経緯と意思決定履歴](#6-開発経緯と意思決定履歴)
7. [現状の課題と評価](#7-現状の課題と評価)
8. [検証手順と確認ポイント](#8-検証手順と確認ポイント)

---

## 1. プロジェクト概要

### 1.1 プロジェクトの目的
介護施設等のシフト管理において、Excelで作成されたシフト表を分析し、以下を実現する：
- 人員不足・過剰の可視化
- スタッフの疲労度分析
- 公平性の評価
- 最適な採用計画の提案
- 将来の需要予測

### 1.2 システム構成
```
C:\ShiftAnalysis/
├── app.py                    # メインアプリケーション（Streamlit）
├── dash_app.py              # ダッシュボード（Dash）
├── cli.py                   # コマンドラインインターフェース
├── shift_suite/             # コアライブラリ
│   ├── __init__.py
│   ├── config.py           # 設定管理
│   ├── i18n.py            # 国際化対応
│   ├── logger_config.py    # ログ設定
│   └── tasks/              # 分析モジュール群
├── requirements.txt         # 依存関係（50+パッケージ）
└── extracted_results/       # 分析結果出力先
```

### 1.3 技術スタック
- **フロントエンド**: Streamlit (app.py) + Dash (dash_app.py)
- **データ処理**: pandas, numpy
- **可視化**: plotly, matplotlib, seaborn
- **機械学習**: scikit-learn, lightgbm, prophet, torch
- **最適化**: ortools, cvxpy, pulp
- **その他**: networkx, psychopy（！）

## 2. システム全体のデータフロー

### 2.1 基本的なデータフロー
```mermaid
graph LR
    A[Excelファイル] --> B[データ入稿]
    B --> C[データ分解・解析]
    C --> D[データ分析]
    D --> E[分析結果の加工]
    E --> F[可視化]
    F --> G[レポート出力]
```

### 2.2 詳細なデータフロー
```
1. データ入稿 (app.py)
   ├── ファイルアップロード処理
   ├── Excel読み込み（openpyxl）
   └── データ検証

2. データ分解 (shift_suite/tasks/)
   ├── build_stats.py: 基本統計の構築
   ├── utils.py: 休暇除外フィルター適用
   └── data_loader.py: データ正規化

3. データ分析 (各分析モジュール)
   ├── shortage.py: 不足・過剰分析
   ├── fatigue.py: 疲労度分析
   ├── fairness.py: 公平性分析
   ├── forecast.py: 需要予測
   └── cluster.py: クラスター分析

4. 分析結果の加工
   ├── unified_analysis_manager.py: 統一管理
   ├── report_generator.py: レポート生成
   └── ai_comprehensive_report_generator.py: AI包括レポート

5. 可視化
   ├── heatmap.py: ヒートマップ生成
   ├── dashboard.py: ダッシュボード表示
   └── visualization_engine.py: 統合可視化
```

## 3. 各モジュールの詳細と関連性

### 3.1 コアモジュール

#### 3.1.1 `app.py` (3,000+行)
**役割**: メインのWebアプリケーション
**主要機能**:
```python
# ファイルアップロード処理
def handle_file_upload():
    # Excelファイルを受け取り、セッションに保存
    
# 分析実行
def run_analysis():
    # 各分析モジュールを順次実行
    # 1. データ読み込み
    # 2. 前処理
    # 3. 各種分析
    # 4. 結果の統合
    
# 結果表示
def display_results():
    # タブ形式で各分析結果を表示
```

**他モジュールとの関係**:
- `shift_suite.tasks.*` の全分析モジュールを呼び出し
- `unified_analysis_manager.py` で結果を統合管理
- `dash_app.py` へのリンクを提供

#### 3.1.2 `shortage.py`
**役割**: 人員不足・過剰の計算
**処理フロー**:
```python
def shortage_and_brief():
    # 1. 必要人員数（need）の計算
    # 2. 実際の人員数（actual）の集計
    # 3. 差分計算（lack = need - actual）
    # 4. 職種別・時間帯別の集計
    # 5. ヒートマップ用データ生成
```

**データ変換**:
- 入力: Excel生データ（日付×スタッフのシフト表）
- 出力: 時間帯別不足データ（DataFrame）

#### 3.1.3 `heatmap.py`
**役割**: ヒートマップ生成と可視化
**処理フロー**:
```python
def generate_heatmaps():
    # 1. 不足データの受け取り
    # 2. 職種別・雇用形態別の分割
    # 3. 色スケールの設定（不足=赤、過剰=青）
    # 4. Plotlyでヒートマップ生成
    # 5. Excel/Parquet形式で保存
```

### 3.2 拡張モジュール（18セクション対応）

#### 3.2.1 認知心理学分析
```python
# cognitive_psychology_analyzer.py (752行)
class CognitivePsychologyAnalyzer:
    def analyze_burnout(self):
        # Maslachバーンアウト理論適用
    def analyze_stress_response(self):
        # Selyeストレス理論適用
    def analyze_motivation(self):
        # 自己決定理論適用
```

#### 3.2.2 組織パターン分析
```python
# organizational_pattern_analyzer.py (1,499行)
class OrganizationalPatternAnalyzer:
    def analyze_culture(self):
        # Schein組織文化モデル
    def analyze_power_dynamics(self):
        # French & Raven権力基盤理論
```

### 3.3 モジュール間の依存関係
```
app.py
├── shift_suite/tasks/
│   ├── build_stats.py ← 基礎データ構築
│   ├── shortage.py ← build_statsの結果を使用
│   ├── heatmap.py ← shortageの結果を可視化
│   ├── fatigue.py ← build_statsから疲労計算
│   ├── fairness.py ← 公平性評価
│   ├── forecast.py ← 時系列予測
│   └── unified_analysis_manager.py ← 全結果を統合
└── ai_comprehensive_report_generator.py ← 18セクションレポート生成
```

## 4. データ処理の詳細フロー

### 4.1 データ入稿プロセス

#### Step 1: Excelファイル読み込み
```python
# shift_suite/tasks/utils.py
def safe_read_excel(fp: Path, **kwargs) -> DataFrame:
    # エラーハンドリング付きExcel読み込み
    # 文字エンコーディング問題対応
    # 空ファイル対応
```

#### Step 2: データ正規化
```python
# shift_suite/tasks/build_stats.py
def build_stats():
    # 1. ヘッダー行の自動検出
    # 2. 日付カラムの識別
    # 3. スタッフ名の抽出
    # 4. シフトコードの解析
    # 5. 時間スロットへの変換
```

#### Step 3: 休暇除外処理
```python
# shift_suite/tasks/utils.py
def apply_rest_exclusion_filter():
    # 休暇パターンの識別
    rest_patterns = ['×', '休', '有休', 'OFF', ...]
    # 休暇レコードの除外
    # 0スロットレコードの除外
```

### 4.2 データ分析プロセス

#### 不足分析の詳細
```python
# shortage.py内の処理
1. need計算:
   - 過去データから必要人員数を推定
   - 職種別・時間帯別に集計
   
2. actual計算:
   - 実際のシフトデータから出勤者数を集計
   - 休暇・欠勤を除外
   
3. 差分計算:
   lack = need - actual
   excess = actual - need (正の場合)
```

#### 疲労分析の詳細
```python
# fatigue.py内の処理
1. 連続勤務日数の計算
2. 夜勤回数のカウント
3. 勤務間隔の計算
4. 疲労スコアの算出（0-1の範囲）
```

### 4.3 分析結果の加工

#### 統一分析管理
```python
# unified_analysis_manager.py
class UnifiedAnalysisManager:
    def create_shortage_analysis():
        # 不足分析結果の標準化
        
    def create_fatigue_analysis():
        # 疲労分析結果の標準化
        
    def get_ai_compatible_results():
        # AI包括レポート用にデータ整形
```

### 4.4 可視化プロセス

#### ヒートマップ生成
```python
# heatmap.py
1. データ準備:
   - 日付×時間スロットのマトリックス作成
   
2. 色設定:
   - 不足: 赤系グラデーション
   - 適正: 白
   - 過剰: 青系グラデーション
   
3. Plotly生成:
   fig = px.imshow(data, color_continuous_scale='RdBu')
   
4. 出力:
   - HTML埋め込み用
   - Excel/Parquet保存
```

## 5. 主要機能の動作原理

### 5.1 シナリオベース分析
システムは3つの統計シナリオで分析を実行：
- **mean_based**: 平均値ベース（標準的）
- **median_based**: 中央値ベース（安定的）
- **p25_based**: 25パーセンタイル（保守的）

### 5.2 動的スロット対応
```python
# constants.py
DEFAULT_SLOT_MINUTES = 30  # 30分単位がデフォルト

# 動的に変更可能
slot_minutes = st.slider("スロット間隔", 15, 60, 30)
```

### 5.3 AI包括レポート生成（18セクション）
```python
# ai_comprehensive_report_generator.py
1. 基本12セクション（従来）
2. 認知心理学分析（13）
3. 組織パターン分析（14）
4. システム思考分析（15）
5. ブループリント分析（16）
6. MECE統合分析（17）
7. 予測最適化分析（18）
```

## 6. 開発経緯と意思決定履歴

### 6.1 初期開発（基本12セクション）
- シフト分析の基本機能実装
- Excel入出力対応
- 基本的な可視化

### 6.2 品質向上フェーズ（91.9% → 100%）
**ユーザー要求**: 「現状最適化継続戦略」の実装
**重要な方向転換**: 「広さではなく深さ」の追求

### 6.3 18セクション拡張
**Phase 1A**: 認知心理学理論の統合
- Maslachバーンアウト理論
- Selyeストレス理論
- 自己決定理論
- 認知負荷理論
- Job Demand-Controlモデル

**Phase 1B**: 組織理論の統合
- Schein組織文化モデル
- システム心理力学
- 社会ネットワーク分析
- French & Raven権力理論
- 制度理論

**Phase 2**: システム思考の統合
- システムダイナミクス
- 複雑適応系理論
- 制約理論（TOC）
- 社会生態系理論
- カオス理論

**Phase 3**: 追加3エンジン
- ブループリント深度分析
- MECE統合分析
- 予測最適化統合

### 6.4 環境問題と対応
- 日本語パス問題（"デスクトップ"）
- C:\ShiftAnalysisへの移行
- 13GB → 990MBのサイズ削減

## 7. 現状の課題と評価

### 7.1 アーキテクチャ的問題

#### 過剰エンジニアリング
- **990MB**のシステムサイズ
- **21,925**個のPythonファイル
- **50+**の依存関係

#### 情報密度の問題
```
システムサイズ: 990MB
↓
出力サイズ: 1.54MB (0.16%)
↓
実用的情報: <1KB (0.0001%)
```

### 7.2 実際の価値vs複雑性

#### 価値のある出力（全体の0.1%）
```
不足時間総計: 373時間
超過時間総計: 58時間
予測精度: MAPE 0.049
休暇パターン分析データ
```

#### 疑問のある機能（全体の99.9%）
- 認知心理学分析（psychopy使用）
- ネットワーク分析（networkx使用）
- ディープラーニング（torch使用）
- 高度な最適化（ortools使用）

### 7.3 保守性の問題
- 単一開発者への依存
- ドキュメント不足
- 過度な抽象化
- テストカバレッジ不明

## 8. 検証手順と確認ポイント

### 8.1 基本動作確認

#### Windows環境でのテスト
```batch
cd C:\ShiftAnalysis

# 仮想環境有効化
venv\Scripts\activate

# 基本実行
python app.py

# テストExcelでの実行
python app.py test_shift_data.xlsx
```

### 8.2 出力品質の検証

#### 検証スクリプト実行
```batch
# 包括的検証
python comprehensive_output_verification.py

# 簡易検証
python simple_output_verification.py
```

#### 確認すべきファイル
1. `extracted_results/out_median_based/stats_summary.txt`
   - 不足・超過時間の確認

2. `extracted_results/leave_analysis.csv`
   - 休暇分析の妥当性

3. `extracted_results/out_median_based/heat_ALL.xlsx`
   - ヒートマップの視覚的確認

### 8.3 パフォーマンス測定

#### メモリ使用量
```python
import psutil
process = psutil.Process()
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB")
```

#### 処理時間
- ファイル読み込み: 目標 <1秒
- 分析実行: 目標 <10秒
- レポート生成: 目標 <5秒

### 8.4 価値評価チェックリスト

#### ビジネス価値
- [ ] 不足時間は正確に計算されているか？
- [ ] ヒートマップは理解しやすいか？
- [ ] 休暇分析は実用的か？
- [ ] 予測精度は十分か？

#### 技術的妥当性
- [ ] 依存関係は必要最小限か？
- [ ] コードは保守可能か？
- [ ] パフォーマンスは許容範囲か？
- [ ] エラーハンドリングは適切か？

## 付録A: 重要ファイル一覧

### コアファイル
- `app.py` - メインアプリケーション
- `dash_app.py` - ダッシュボード
- `shift_suite/tasks/shortage.py` - 不足分析
- `shift_suite/tasks/heatmap.py` - 可視化
- `shift_suite/tasks/build_stats.py` - データ構築

### 設定ファイル
- `requirements.txt` - 依存関係
- `shift_suite/config.json` - システム設定
- `shift_suite/tasks/constants.py` - 定数定義

### 検証・分析レポート
- `COMPREHENSIVE_HANDOVER_DOCUMENT.md` - 初版引継ぎ
- `CRITICAL_OBJECTIVE_ANALYSIS_REPORT.md` - 批判的分析
- `VERIFIED_OUTPUT_QUALITY_REPORT.md` - 品質検証

## 付録B: トラブルシューティング

### よくある問題

#### 1. ModuleNotFoundError
```
原因: 依存関係の不足
解決: pip install -r requirements.txt
```

#### 2. 日本語ファイル名エラー
```
原因: 文字エンコーディング
解決: UTF-8エンコーディングを強制
```

#### 3. メモリ不足
```
原因: 大規模データ処理
解決: スロット間隔を大きくする（30分→60分）
```

---

**作成日**: 2025年8月5日
**バージョン**: 2.0（完全版）
**次回更新予定**: システム再設計後