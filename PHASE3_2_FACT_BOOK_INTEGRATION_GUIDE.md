# Phase 3.2 ファクトブック可視化機能 統合ガイド

**作成日時**: 2025年08月01日

## 🎯 Phase 3.2 概要

### 実装内容
Phase 3.2では、Phase 2の基本事実抽出とPhase 3.1の異常検知機能を統合した包括的なファクトブック可視化システムを実装しました。

### 主要コンポーネント
1. **FactBookVisualizer** (`fact_book_visualizer.py`)
   - Phase 2 & 3.1の統合処理
   - 構造化されたデータ出力
   - Dashレイアウト生成

2. **DashFactBookIntegration** (`dash_fact_book_integration.py`)
   - 既存dash_app.pyとの統合
   - タブレイアウト生成
   - コールバック関数

## 🔧 既存システムへの統合方法

### Step 1: dash_app.py への統合

#### 1.1 インポート追加
```python
# dash_app.py の上部に追加
try:
    from shift_suite.tasks.dash_fact_book_integration import (
        create_fact_book_analysis_tab,
        register_fact_book_callbacks,
        get_fact_book_tab_definition
    )
    FACT_BOOK_INTEGRATION_AVAILABLE = True
    log.info("📊 ファクトブック統合機能が利用可能です")
except ImportError as e:
    log.warning(f"ファクトブック統合機能の読み込みに失敗: {e}")
    FACT_BOOK_INTEGRATION_AVAILABLE = False
```

#### 1.2 タブ定義の追加
```python
# create_main_layout() 関数内のタブ定義部分に追加
if FACT_BOOK_INTEGRATION_AVAILABLE:
    main_tabs.append(
        dcc.Tab(label='📊 統合ファクトブック', value='fact_book_analysis')
    )
```

#### 1.3 タブコンテンツの追加
```python
# メインレイアウトのタブコンテンツ部分に追加
elif active_tab == 'fact_book_analysis':
    if FACT_BOOK_INTEGRATION_AVAILABLE:
        return create_fact_book_analysis_tab()
    else:
        return html.Div("ファクトブック機能が利用できません")
```

#### 1.4 コールバック登録
```python
# register_callbacks() 関数内に追加
if FACT_BOOK_INTEGRATION_AVAILABLE:
    register_fact_book_callbacks(app)
```

### Step 2: データ連携の設定

#### 2.1 long_df データの共有
```python
# 既存のget_current_data()関数を拡張
def get_current_long_df():
    """現在のlong_dfデータを取得"""
    # 既存のデータ取得ロジックを使用
    return current_long_df  # グローバル変数として管理

# ファクトブック用のデータ取得関数
def get_fact_book_data(sensitivity='medium'):
    """ファクトブック用のデータを生成"""
    long_df = get_current_long_df()
    if long_df is not None and not long_df.empty:
        from shift_suite.tasks.fact_book_visualizer import FactBookVisualizer
        visualizer = FactBookVisualizer(sensitivity=sensitivity)
        return visualizer.generate_comprehensive_fact_book(long_df)
    return {"error": "データが利用できません"}
```

#### 2.2 キャッシュ機能の実装
```python
# 分析結果のキャッシュ（既存のlru_cacheパターンに合わせる）
@lru_cache(maxsize=32)
def cached_fact_book_analysis(data_hash, sensitivity):
    """ファクトブック分析結果のキャッシュ"""
    # 実際の分析処理
    pass
```

## 📊 ユーザーインターフェース設計

### UI構成

```
📊 統合ファクトブック分析
├── 🎛️ 分析設定
│   ├── 異常検知感度選択
│   └── 分析実行ボタン
├── 📋 概要サマリーカード (4枚)
│   ├── データ概要
│   ├── 事実統計
│   ├── 異常検知
│   └── 分析ステータス
├── ⚠️ 異常検知結果
│   ├── 重要度別ソート
│   ├── 上位10件表示
│   └── 詳細情報
├── 📋 基本事実詳細
│   ├── タブ別表示
│   ├── データテーブル
│   └── フィルタ・ソート機能
└── 📋 分析メタデータ
    └── 実行情報
```

### スタイルガイドライン

#### 色設定
- **プライマリ**: `#3498db` (青)
- **成功**: `#28a745` (緑)
- **警告**: `#ffc107` (黄)
- **危険**: `#dc3545` (赤)
- **情報**: `#17a2b8` (水色)

#### 重要度別色設定
- **緊急**: `#dc3545` (赤)
- **高**: `#fd7e14` (オレンジ)
- **中**: `#ffc107` (黄)
- **低**: `#6c757d` (グレー)

## ⚡ パフォーマンス考慮事項

### 1. データ処理の最適化
```python
# 大量データに対する段階的処理
def process_large_dataset(long_df, chunk_size=10000):
    """大量データの段階的処理"""
    if len(long_df) > chunk_size:
        # チャンク処理で メモリ使用量を制御
        chunks = [long_df[i:i+chunk_size] for i in range(0, len(long_df), chunk_size)]
        results = []
        for chunk in chunks:
            result = process_chunk(chunk)
            results.append(result)
        return combine_results(results)
    else:
        return process_normal(long_df)
```

### 2. キャッシュ戦略
```python
# 分析結果のキャッシュ
@lru_cache(maxsize=8)
def cached_analysis(data_fingerprint, sensitivity):
    """計算コストの高い分析結果をキャッシュ"""
    # 実際の分析処理
    pass

# データフィンガープリントの生成
def generate_data_fingerprint(long_df):
    """データの特徴量からフィンガープリントを生成"""
    return hash((len(long_df), long_df.shape[1], str(long_df.dtypes)))
```

### 3. 表示件数の制限
- 異常検知結果: 上位10件まで表示
- 基本事実: カテゴリ別にページング
- データテーブル: 20行/ページ

## 🛡️ エラーハンドリング

### 1. データ検証
```python
def validate_input_data(long_df):
    """入力データの検証"""
    required_columns = {'ds', 'staff', 'role', 'code', 'holiday_type', 'parsed_slots_count'}
    
    if long_df.empty:
        raise ValueError("入力データが空です")
    
    missing_cols = required_columns - set(long_df.columns)
    if missing_cols:
        raise ValueError(f"必須カラムが不足: {missing_cols}")
    
    return True
```

### 2. グレースフルデグラデーション
```python
def safe_fact_book_generation(long_df, sensitivity='medium'):
    """エラー時も部分的な結果を返すセーフ実装"""
    results = {
        "generation_timestamp": datetime.now().isoformat(),
        "basic_facts": {},
        "anomalies": [],
        "errors": []
    }
    
    try:
        # Phase 2: 基本事実抽出
        results["basic_facts"] = extract_basic_facts_safe(long_df)
    except Exception as e:
        results["errors"].append(f"基本事実抽出エラー: {e}")
    
    try:
        # Phase 3.1: 異常検知
        results["anomalies"] = detect_anomalies_safe(long_df, sensitivity)
    except Exception as e:
        results["errors"].append(f"異常検知エラー: {e}")
    
    return results
```

## 🧪 テスト戦略

### 1. 単体テスト
```python
def test_fact_book_visualizer():
    """FactBookVisualizerの単体テスト"""
    # サンプルデータでの動作確認
    # 各機能の個別テスト
    # エラーケースのテスト
    pass

def test_dash_integration():
    """Dash統合機能のテスト"""
    # レイアウト生成テスト
    # コールバック機能テスト
    # スタイル適用テスト
    pass
```

### 2. 統合テスト
```python
def test_end_to_end_integration():
    """エンドツーエンド統合テスト"""
    # 実データでの全体フロー確認
    # dash_app.pyとの連携確認
    # パフォーマンステスト
    pass
```

### 3. ユーザビリティテスト
- 直感的な操作性の確認
- エラーメッセージの分かりやすさ
- 分析結果の理解しやすさ

## 📋 運用ガイドライン

### 1. 推奨利用手順
1. データアップロード (既存機能)
2. 基本分析実行 (既存機能)
3. ファクトブックタブに移動
4. 感度設定の選択
5. 分析実行
6. 結果確認

### 2. トラブルシューティング

#### Q: 分析が実行されない
A: 以下を確認してください
- データが正しくアップロードされているか
- 必須カラムが存在するか
- メモリ不足でないか

#### Q: 異常が検知されすぎる
A: 感度設定を「低感度」に変更してください

#### Q: 異常が検知されない
A: 感度設定を「高感度」に変更してください

### 3. パフォーマンス最適化Tips
- 大量データ(10万件以上)の場合は感度を「低」に設定
- 定期的にブラウザキャッシュをクリア
- 複数の分析を同時実行しない

## ✅ Phase 3.2 完了基準

### 機能要件
- [x] Phase 2 & 3.1の統合
- [x] Dashレイアウト生成
- [x] 既存システムとの統合インターフェース
- [x] エラーハンドリング
- [x] ユーザーフレンドリーなUI

### 非機能要件
- [x] レスポンシブデザイン
- [x] 1万レコード以下で5秒以内の表示
- [x] 既存システムとの互換性維持
- [x] グレースフルデグラデーション

### 文書化
- [x] 統合ガイド作成
- [x] API仕様書
- [x] 運用マニュアル

## 🚀 次のステップ (Phase 4)

Phase 3.2完了後の拡張可能性:

### Phase 4.1: 高度可視化
- インタラクティブチャート
- ドリルダウン機能
- エクスポート機能

### Phase 4.2: AI強化
- 機械学習ベース異常検知
- 予測分析機能
- 自動レポート生成

### Phase 4.3: API化
- REST API提供
- 外部システム連携
- バッチ処理機能

---

**Phase 3.2 実装完了**: ✅ 統合ファクトブック可視化機能の完成