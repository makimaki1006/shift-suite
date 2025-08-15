# shift_suite システムにおける休日除外問題 - 包括的調査レポート

## 調査概要

shift_suite システムにおいて、休日データがヒートマップに表示される問題について、データフロー全体を通じて包括的に調査しました。

## データフロー分析

### 1. データ生成段階 (io_excel.py → heatmap.py)

#### **問題発見点1: _filter_work_records()の適用範囲**

**ファイル**: `/shift_suite/tasks/heatmap.py` 行394-422

```python
def _filter_work_records(long_df: pd.DataFrame) -> pd.DataFrame:
    """
    通常勤務のレコードのみを抽出する
    休暇レコード（holiday_type != "通常勤務"）を除外し、
    実際に勤務時間がある（parsed_slots_count > 0）レコードのみを返す
    """
    if long_df.empty:
        return long_df

    # 通常勤務且つ勤務時間があるレコードのみ抽出
    work_records = long_df[
        (long_df.get("holiday_type", DEFAULT_HOLIDAY_TYPE) == DEFAULT_HOLIDAY_TYPE)
        & (long_df.get("parsed_slots_count", 0) > 0)
    ].copy()
```

**分析結果**:
- この関数は適切に実装されているが、**heat_ALL.parquet 生成時のみ適用**されている
- **pre_aggregated_data.parquet 生成時には適用されていない可能性**

#### **問題発見点2: build_heatmap()内での適用確認**

**ファイル**: `/shift_suite/tasks/heatmap.py` 行547-548

```python
# 重要: 通常勤務のレコードのみでヒートマップ作成
df_for_heatmap_actuals = _filter_work_records(long_df)
```

**適用場所確認**:
- ✅ **heat_ALL.parquet 生成**: _filter_work_records() が適用される
- ❌ **app.py での pre_aggregated_data.parquet 生成**: 適用されていない可能性

### 2. 中間データ生成段階 (app.py)

#### **問題発見点3: pre_aggregated_data.parquet 生成ロジック**

**ファイル**: `/app.py` 行1735-1746

```python
# すべての組み合わせに実際のスタッフ数を結合し、稼働がない場合は0で埋める
pre_aggregated_df = pd.merge(
    all_combinations_from_long_df,
    staff_counts_actual,
    on=["date_lbl", "time", "role", "employment"],
    how="left",
)
pre_aggregated_df["staff_count"] = pre_aggregated_df["staff_count"].fillna(0).astype(int)

pre_aggregated_df.to_parquet(
    scenario_out_dir / "pre_aggregated_data.parquet",
    index=False,
)
```

**問題分析**:
1. **long_df から直接 staff_counts_actual を生成**している
2. この段階で **_filter_work_records() が適用されていない**
3. 休暇レコードが含まれたまま集計される可能性がある

### 3. dash_app.py でのデータ処理

#### **問題発見点4: data_get()関数での休日除外**

**ファイル**: `/dash_app.py` 行904-905, 914-915, 924-925

```python
# 休日除外が必要なデータキーに対してフィルターを適用
if key in ['pre_aggregated_data', 'long_df', 'intermediate_data']:
    df = apply_rest_exclusion_filter(df, f"data_get({key})")
```

**分析結果**:
- ✅ data_get()で休日除外フィルタが適用される
- ✅ apply_rest_exclusion_filter() は統合版を使用

#### **問題発見点5: update_comparison_heatmaps()での二重フィルタリング**

**ファイル**: `/dash_app.py` 行3702-3707

```python
# 追加の休日除外確認：事前集計データに0スタッフのレコードが残っている場合に備えて
if 'staff_count' in filtered_df.columns:
    before_count = len(filtered_df)
    filtered_df = filtered_df[filtered_df['staff_count'] > 0]
    after_count = len(filtered_df)
    if before_count != after_count:
        log.info(f"[Heatmap] 追加の休日除外フィルタ適用: {before_count} -> {after_count} ({before_count - after_count}件除外)")
```

**分析結果**:
- ✅ ダッシュボードで追加の0スタッフフィルタが適用される
- ✅ ログ出力で確認可能

### 4. 統合版休暇除外フィルタ

#### **問題発見点6: apply_rest_exclusion_filter()の実装**

**ファイル**: `/shift_suite/tasks/utils.py` 行50-139

```python
def apply_rest_exclusion_filter(df: pd.DataFrame, context: str = "unknown") -> pd.DataFrame:
    """データパイプライン全体で使用する統一的な休暇除外フィルター"""
    
    # 1. スタッフ名による除外（最も重要）
    rest_patterns = [
        '×', 'X', 'x', '休', '休み', '休暇', '欠', '欠勤',
        'OFF', 'off', 'Off', '-', '−', '―', 'nan', 'NaN', 'null',
        '有', '有休', '特', '特休', '代', '代休', '振', '振休'
    ]
    
    # 2. parsed_slots_count による除外
    # 3. staff_count による除外（事前集計データ用）  
    # 4. holiday_type による除外
```

**分析結果**:
- ✅ 包括的なパターンマッチング
- ✅ 複数の条件による除外
- ✅ ログ出力で詳細確認可能

## **根本原因の特定**

### **主要な問題: app.py での pre_aggregated_data.parquet 生成時の休暇除外不備**

**問題箇所**: `/app.py` 行1735周辺の staff_counts_actual 生成部分

**現在のロジック**:
```python
# 実際のスタッフ数をカウント（休暇除外なし）
staff_counts_actual = (
    long_df_with_additional_columns.drop_duplicates(subset=["date_lbl", "time", "staff"])
    .groupby(["date_lbl", "time", "role", "employment"], observed=True)
    .size()
    .reset_index(name="staff_count")
)
```

**問題点**:
1. long_df_with_additional_columns に **休暇レコードが含まれている**
2. **_filter_work_records() が適用されていない**
3. **apply_rest_exclusion_filter() が適用されていない**

### **副次的な問題: データの一貫性**

1. **heat_ALL.parquet**: _filter_work_records() で適切に除外済み
2. **pre_aggregated_data.parquet**: 休暇レコードが混入している可能性
3. **dash_app.py**: data_get()とupdate_comparison_heatmaps()で二重に補正

## **推奨解決策**

### **解決策1: app.py での事前フィルタリング実装**

**修正箇所**: `/app.py` 行1730周辺

```python
# 修正前
staff_counts_actual = (
    long_df_with_additional_columns.drop_duplicates(subset=["date_lbl", "time", "staff"])
    .groupby(["date_lbl", "time", "role", "employment"], observed=True)
    .size()
    .reset_index(name="staff_count")
)

# 修正後
from shift_suite.tasks.heatmap import _filter_work_records

# 休暇レコードを除外してからカウント
filtered_long_df = _filter_work_records(long_df_with_additional_columns)
staff_counts_actual = (
    filtered_long_df.drop_duplicates(subset=["date_lbl", "time", "staff"])
    .groupby(["date_lbl", "time", "role", "employment"], observed=True)
    .size()
    .reset_index(name="staff_count")
)
```

### **解決策2: 統合版フィルタの追加適用**

```python
# さらに安全のため統合版フィルタも適用
from shift_suite.tasks.utils import apply_rest_exclusion_filter

filtered_long_df = apply_rest_exclusion_filter(
    _filter_work_records(long_df_with_additional_columns), 
    "pre_aggregated_generation"
)
```

### **解決策3: データ一貫性の検証**

```python
# pre_aggregated_data 生成後の検証
total_staff_pre_agg = pre_aggregated_df['staff_count'].sum()
total_staff_heat_all = # heat_ALL.parquet の合計と比較

if abs(total_staff_pre_agg - total_staff_heat_all) > threshold:
    log.warning(f"データ不整合検出: pre_agg={total_staff_pre_agg}, heat_all={total_staff_heat_all}")
```

## **影響範囲分析**

### **直接的影響**
1. ダッシュボードのヒートマップに休日データが表示される
2. 職種別・雇用形態別の集計値が過大評価される
3. 人員配置の意思決定に誤解を与える可能性

### **間接的影響**
1. shortage_time.parquet 等の依存データにも影響
2. need計算の基礎データとしての信頼性低下
3. レポート生成時の精度低下

## **検証方法**

### **即座に確認できる方法**

1. **ログ確認**:
```bash
grep "RestExclusion" shift_suite.log
grep "追加の休日除外フィルタ適用" shift_suite.log
```

2. **データファイル比較**:
```python
heat_all = pd.read_parquet("heat_ALL.parquet")
pre_agg = pd.read_parquet("pre_aggregated_data.parquet")

# 同日の合計スタッフ数比較
date = "2024-11-15"
heat_total = heat_all[date].sum()  
pre_agg_total = pre_agg[pre_agg['date_lbl']==date]['staff_count'].sum()
```

3. **dash_app.py でのフィルタ効果確認**:
ダッシュボード実行時のログで以下が出力されるか確認：
```
[Heatmap] 追加の休日除外フィルタ適用: XXXX -> YYYY (ZZ件除外)
```

## **結論**

shift_suite システムにおける休日除外問題の根本原因は、**app.py での pre_aggregated_data.parquet 生成時に休暇レコードの除外処理が不完全**であることが判明しました。

heat_ALL.parquet では適切に _filter_work_records() が適用されているのに対し、pre_aggregated_data.parquet では同等の処理が行われていないため、ダッシュボードで使用されるデータに休暇レコードが混入している可能性があります。

dash_app.py 側では apply_rest_exclusion_filter() と追加の0スタッフフィルタによって補正が行われていますが、データ生成段階での修正が根本的な解決策となります。

## **優先度**

🔴 **高優先**: app.py での pre_aggregated_data 生成時の休暇除外実装  
🟡 **中優先**: データ一貫性検証機能の追加  
🟢 **低優先**: ログ出力の改善とモニタリング強化  

---

**調査日時**: 2025-07-22  
**調査範囲**: データフロー全体 (io_excel.py → heatmap.py → app.py → dash_app.py)  
**発見された問題**: 1件の根本原因 + 複数の補正機能  
**推奨アクション**: app.py の修正実装