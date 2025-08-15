# Root Cause Analysis Report: シフト分析システムの3つの問題

## Executive Summary
3つの報告された問題は、すべて**過度に厳格な休日除外フィルター**という単一の根本原因に起因しています。

## 問題の詳細

### 1. ヒートマップに欠落日付が表示される問題
**症状**: 実際のデータがない日付がヒートマップに表示されない

**原因の箇所**:
- `dash_app.py` line 904-905: `apply_rest_exclusion_filter`が`pre_aggregated_data`に適用
- `dash_app.py` line 3747-3751: `staff_count > 0`の日付のみを取得

**メカニズム**:
1. データ読み込み時に`staff_count = 0`のレコードがすべて除外される
2. ヒートマップ生成時に「実際の勤務日のみ」を表示する処理が、データなしの日も除外
3. 結果として、スタッフが配置されていない日（休日ではない）も表示されない

### 2. 'df_shortage_role_filtered' is not defined エラー
**症状**: 不足分析タブでNameError発生

**原因の箇所**:
- `dash_app.py` line 1682: `df_shortage_role_filtered = {}`が条件付きブロック内で定義
- `dash_app.py` line 1720: 条件外でも使用される

**メカニズム**:
1. `df_shortage_role`が空の場合、line 1685の`if not df_shortage_role.empty:`がFalse
2. `df_shortage_role_filtered`の定義がスキップされる
3. line 1720で未定義変数を参照してエラー

### 3. 特定職種（介護（ｗ＿２））のヒートマップが単色表示
**症状**: 色のグラデーションが表示されず、単一色になる

**原因の箇所**:
- `utils.py` line 50-139: `apply_rest_exclusion_filter`の過度なフィルタリング
- `dash_app.py` line 1105-1112: ヒートマップのカラースケール設定

**メカニズム**:
1. 特定職種のデータが大幅にフィルタリングされる
2. 残ったデータがすべて同じ値（または0のみ）になる
3. Plotlyのカラースケールが単一値に対して単色を表示

## 根本原因の詳細分析

### apply_rest_exclusion_filterの問題点
```python
# utils.py line 119-123
if 'staff_count' in df.columns:
    zero_staff_mask = df['staff_count'] <= 0
    zero_staff_count = zero_staff_mask.sum()
    if zero_staff_count > 0:
        df = df[~zero_staff_mask]
```

このコードは以下を区別できません：
- **休日**（除外すべき）: スタッフが休みの日
- **空き日**（表示すべき）: スタッフが配置されていないが営業日

### データフローの問題
```
1. parquetファイル読み込み
   ↓
2. apply_rest_exclusion_filter（すべての0値を除外）← 問題の根源
   ↓
3. pre_aggregated_dataキャッシュ
   ↓
4. ヒートマップ生成（さらに0値を除外）← 二重フィルタリング
   ↓
5. 表示データの欠落
```

## 影響の連鎖

1. **初期フィルタリング**で正当なデータが失われる
2. **データ不足**により変数定義がスキップされる
3. **残存データの均一性**により視覚化が単調になる

## 推奨される修正方針

### 1. フィルタリングロジックの改善
- 休日と空き日を区別する新しいフラグを追加
- `holiday_type`フィールドをより積極的に活用
- staff_count = 0でも営業日なら保持

### 2. 変数定義の安全性向上
```python
# 修正前
if not df_shortage_role.empty:
    df_shortage_role_filtered = {}
    # ...処理...

# 修正後
df_shortage_role_filtered = {}  # 常に初期化
if not df_shortage_role.empty:
    # ...処理...
```

### 3. ヒートマップの完全性保証
- すべての営業日を表示（値が0でも）
- 休日のみを明示的に除外
- カラースケールの最小範囲を設定

## 結論
3つの問題はすべて、休日除外フィルターが「データなし」と「休日」を区別できないことに起因しています。この単一の根本原因を修正することで、すべての問題を同時に解決できます。

## 次のステップ
1. `apply_rest_exclusion_filter`の改修
2. データ読み込み時の休日判定ロジックの改善
3. 変数初期化の安全性向上
4. ヒートマップ表示の完全性保証

---
作成日: 2025-07-23
分析者: Claude Code