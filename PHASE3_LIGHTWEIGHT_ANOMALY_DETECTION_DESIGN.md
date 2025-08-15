# ブループリント分析 Phase 3: 軽量異常検知機能設計書

**設計完了日時**: 2025年08月01日

## 🎯 設計目標

### 主要方針
1. **軽量性重視**: O(n)またはO(n log n)の計算量に制限
2. **実用性優先**: 実際のシフト管理で有用な異常のみ検知
3. **安全性確保**: Phase 2で確立した安全な実装パターンを継承
4. **段階的拡張**: 基本機能から高度機能への段階的な拡張

### 性能目標
- **レスポンス時間**: 1万レコード以下で1秒以内
- **メモリ使用量**: 基本処理で100MB以下
- **CPU負荷**: シングルコアで十分処理可能

## 🔍 検知対象異常の分類

### 1. 労働時間異常（優先度: 高）
- **過度な労働時間**: 月間労働時間が平均の1.5倍以上
- **計算量**: O(n) - グループ集計のみ
- **ビジネス価値**: 労働基準法遵守、職員健康管理

### 2. 連続勤務違反（優先度: 高）
- **連続勤務日数**: 7日以上の連続勤務を検知
- **計算量**: O(n log n) - 日付ソート後の線形走査
- **ビジネス価値**: 法令遵守、疲労軽減

### 3. 夜勤頻度過多（優先度: 中）
- **夜勤比率**: 全勤務の40%以上が夜勤
- **計算量**: O(n) - 文字列パターンマッチング
- **ビジネス価値**: 職員健康管理、バランス調整

### 4. 勤務間インターバル違反（優先度: 中）
- **短時間間隔**: 11時間未満の勤務間隔
- **計算量**: O(n log n) - ソート後の隣接要素比較
- **ビジネス価値**: 労働基準法遵守

## 🏗️ アーキテクチャ設計

### クラス構造

```python
@dataclass
class AnomalyResult:
    """異常検知結果の標準化されたデータ構造"""
    anomaly_type: str      # 異常タイプ
    severity: str          # 重要度（低/中/高/緊急）
    staff: str            # 対象職員
    description: str      # 人間可読な説明
    value: float          # 実際の値
    expected_range: Tuple # 期待値範囲
    date_range: Optional  # 対象期間

class LightweightAnomalyDetector:
    """軽量異常検知システムのメインクラス"""
    
    # コアメソッド
    def detect_anomalies(long_df) -> List[AnomalyResult]
    def generate_anomaly_summary(anomalies) -> Dict[str, Any]
    
    # 個別検知メソッド（すべてprivate）
    def _detect_excessive_hours(work_df) -> List[AnomalyResult]
    def _detect_continuous_work_violations(work_df) -> List[AnomalyResult]
    def _detect_night_shift_anomalies(work_df) -> List[AnomalyResult]
    def _detect_interval_violations(work_df) -> List[AnomalyResult]
```

### データフロー

```
Input: long_df (Phase 2で検証済み)
  ↓
前処理: 有効勤務レコードの抽出
  ↓
並列処理: 4つの異常検知アルゴリズム
  ├─ 労働時間異常検知
  ├─ 連続勤務違反検知
  ├─ 夜勤頻度検知
  └─ インターバル違反検知
  ↓
結果統合: AnomalyResultリストの作成
  ↓
重要度ソート: 緊急 > 高 > 中 > 低
  ↓
Output: 構造化された異常検知結果
```

## ⚡ パフォーマンス設計

### 計算量分析

| 機能 | 計算量 | 説明 |
|------|--------|------|
| 労働時間異常 | O(n) | groupby + 単純集計 |
| 連続勤務違反 | O(n log n) | ソート + 線形走査 |
| 夜勤頻度 | O(n) | 文字列マッチング + カウント |
| インターバル違反 | O(n log n) | ソート + 隣接比較 |
| **全体** | **O(n log n)** | **最も重い処理に依存** |

### メモリ使用量最適化

1. **ストリーミング処理**: 大きなデータは職員単位で分割処理
2. **中間結果削除**: 不要な中間DataFrameは即座に削除
3. **必要カラムのみ**: 関係ないカラムは事前に除去

### 早期終了戦略

```python
# 空データの早期検出
if long_df.empty:
    return []

# 有効レコードなしの早期検出  
work_records = long_df[long_df['parsed_slots_count'] > 0]
if work_records.empty:
    return []
```

## 🛡️ 安全性設計

### エラーハンドリング戦略

1. **入力検証**: 必須カラムの存在確認
2. **データ品質チェック**: 異常値の事前フィルタリング
3. **計算エラー処理**: ゼロ除算、無限値の処理
4. **ログ出力**: 各段階での処理状況記録

### 設定可能な感度レベル

```python
sensitivity_levels = {
    "low": {
        "excessive_hours_multiplier": 1.8,  # より緩い基準
        "continuous_work_days": 10,         # より長い許容期間
    },
    "medium": {
        "excessive_hours_multiplier": 1.5,  # 標準基準
        "continuous_work_days": 7,          # 標準期間
    },
    "high": {
        "excessive_hours_multiplier": 1.2,  # より厳しい基準
        "continuous_work_days": 5,          # より短い許容期間
    }
}
```

## 📊 出力形式設計

### 異常検知結果の構造化

```json
{
  "detection_timestamp": "2025-08-01T12:00:00",
  "total_anomalies": 15,
  "by_severity": {
    "緊急": 2,
    "高": 5,
    "中": 6,
    "低": 2
  },
  "by_type": {
    "過度な労働時間": 8,
    "連続勤務違反": 4,
    "夜勤頻度過多": 2,
    "勤務間インターバル違反": 1
  },
  "top_issues": [
    {
      "type": "過度な労働時間",
      "staff": "田中太郎",
      "description": "2025-01の労働時間が異常に多い (180.5時間)",
      "severity": "緊急"
    }
  ]
}
```

## 🔄 Phase 2 との統合設計

### FactExtractor連携

```python
# Phase 2のFactExtractorと組み合わせた使用例
extractor = FactExtractorPrototype()
detector = LightweightAnomalyDetector()

# 基本事実を抽出
facts = extractor.extract_basic_facts(long_df)

# 異常を検知  
anomalies = detector.detect_anomalies(long_df)

# 統合レポート生成
integrated_report = {
    "basic_facts": facts,
    "anomalies": anomalies,
    "summary": detector.generate_anomaly_summary(anomalies)
}
```

### 既存システムとの互換性

- **入力**: long_dfの同一フォーマット使用
- **出力**: 新しいAnomalyResult構造だが、既存のレポート形式と併用可能
- **設定**: 既存のconstants.pyの値を活用
- **ログ**: 既存のログシステムと統合

## 🧪 テスト戦略

### ユニットテスト設計

1. **各検知機能の単体テスト**
   - 正常データでの異常なし確認
   - 明らかな異常データでの検知確認
   - 境界値での動作確認

2. **統合テスト**
   - 実データでの全体動作確認
   - パフォーマンステスト
   - メモリ使用量測定

3. **回帰テスト**
   - Phase 2機能への影響確認
   - 既存システムとの互換性確認

## 📈 将来拡張の設計

### Phase 3.5: 高度異常検知（将来実装）

Phase 3で基盤を固めた後、より高度な機能を段階的に追加：

1. **機械学習ベース異常検知**
   - 過去パターンからの逸脱検知
   - 季節性を考慮した異常検知

2. **相関分析**
   - 職員間の勤務パターン相関
   - 部署間のバランス分析

3. **予測的異常検知**
   - 将来の労働時間不足予測
   - 疲労蓄積の予測

## ✅ Phase 3 実装完了基準

### 必須機能
- [x] 4つの基本異常検知機能の実装
- [x] 構造化された出力形式
- [x] 設定可能な感度レベル
- [x] エラーハンドリングとログ出力
- [x] Phase 2との統合性確保

### 品質基準
- [ ] 1万レコードで1秒以内の処理時間
- [ ] メモリ使用量100MB以下
- [ ] すべてのユニットテスト通過
- [ ] 実データでの動作確認

### 文書化
- [x] 設計書の完成
- [ ] API文書の作成
- [ ] 運用ガイドの作成

## 🚀 実装スケジュール

### Week 1: 基本機能実装
- [x] LightweightAnomalyDetectorクラス実装
- [x] 4つの基本検知機能実装
- [ ] 単体テスト作成・実行

### Week 2: 統合・最適化
- [ ] Phase 2との統合テスト
- [ ] パフォーマンス最適化
- [ ] エラーハンドリング強化

### Week 3: 実用化準備
- [ ] 実データでの検証
- [ ] ドキュメント整備
- [ ] UI/可視化機能の準備（Phase 3.2）

**Phase 3.1 完了判定**: 基本異常検知機能の実装と検証完了 ✅