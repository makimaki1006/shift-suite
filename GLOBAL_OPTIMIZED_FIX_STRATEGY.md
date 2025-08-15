# 🎯 全体最適化修正戦略

## 📋 基本原則

### 1. **動的データ対応の前提**
- 全てのファイル形式（CSV, Excel, Parquet, ZIP）に対応
- 任意のスロット間隔（5分〜1440分）に対応
- 任意のシナリオ数に対応
- 任意のデータサイズに対応

### 2. **一貫性保証**
- 全関数で同一のslot_minutes伝播
- 境界値検証の統一
- エラーハンドリングの統一
- ログ出力の統一

### 3. **パフォーマンス最適化**
- メモリ効率を考慮した修正
- 大規模データでの動作保証
- キャッシュ一貫性の維持

## 🔧 修正パターン分類

### Pattern A: 計算エラー修正（Priority: Critical）
```python
# 修正前（間違い）
result = df.sum().sum() * SLOT_HOURS

# 修正後（正しい）
result = (df * slot_hours).sum().sum()
```

### Pattern B: 関数シグネチャ拡張（Priority: High）
```python
# 修正前
def function_name(param1, param2):
    slot_hours = SLOT_HOURS

# 修正後  
def function_name(param1, param2, *, slot_minutes: int = 30):
    slot_hours = slot_minutes / 60.0
```

### Pattern C: 境界値検証追加（Priority: High）
```python
def validate_slot_minutes(slot_minutes: int) -> int:
    if slot_minutes is None:
        raise ValueError("slot_minutes must not be None")
    if slot_minutes <= 0:
        raise ValueError(f"slot_minutes must be positive, got {slot_minutes}")
    if slot_minutes > 1440:
        raise ValueError(f"slot_minutes cannot exceed 1440 (24 hours), got {slot_minutes}")
    return slot_minutes
```

### Pattern D: 設定伝播修正（Priority: High）
```python
# app.py での呼び出し修正
function_call(
    param1=value1,
    slot_minutes=param_slot,  # ←追加
    param2=value2
)
```

## 📊 修正優先度マトリクス

| ファイル | 計算エラー | 設定伝播 | 境界値検証 | 優先度 |
|---------|-----------|----------|------------|--------|
| proportional_calculator.py | ✅ | ✅ | ✅ | Critical | 
| gap_analyzer.py | ✅ | ✅ | ✅ | Critical |
| fatigue_prediction.py | ✅ | ✅ | ✅ | Critical |
| blueprint_analyzer.py | ✅ | ✅ | ✅ | Critical |
| turnover_prediction.py | ✅ | ✅ | ✅ | Critical |
| mece_fact_extractor.py | ✅ | ✅ | ✅ | Critical |
| shift_mind_reader.py | ✅ | ✅ | ✅ | Critical |
| others... | ✅ | ✅ | ✅ | High |

## 🔄 修正手順

### Step 1: ユーティリティ関数作成
```python
# shift_suite/tasks/utils.py に追加
def validate_and_convert_slot_minutes(slot_minutes: int) -> float:
    """動的スロット設定の検証と時間変換"""
    # 境界値検証 + 時間変換 + ログ出力
```

### Step 2: 各ファイルの個別修正
1. 関数シグネチャ拡張
2. 計算ロジック修正
3. 境界値チェック追加
4. ログ出力追加

### Step 3: app.py の呼び出し修正
1. 各関数呼び出しにslot_minutes追加
2. エラーハンドリング強化

### Step 4: 統合テスト
1. 各スロット間隔での動作確認
2. 境界値テスト
3. 大規模データテスト

## 🎯 期待効果

### 即座の効果
- 計算精度の大幅改善
- 任意スロット間隔対応
- システム安定性向上

### 長期効果  
- 保守性向上
- 拡張性向上
- 技術的負債削減

## ⚠️ リスク管理

### 後方互換性
- デフォルト値（30分）で既存動作を保証
- 段階的移行可能

### テスト戦略
- 修正前後の出力比較
- エッジケーステスト
- パフォーマンステスト

### ロールバック計画
- 完全バックアップ済み
- Git履歴での復旧可能