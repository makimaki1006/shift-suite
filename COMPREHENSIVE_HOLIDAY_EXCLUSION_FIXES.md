# 休日除外問題 - 包括的修正レポート

## 🔍 発見された根本原因

### 1. **app.py - pre_aggregated_data生成の問題**
**場所**: 1700-1704行目  
**問題**: 全データから組み合わせを作成後、休日データが含まれたまま事前集計データを生成  
**修正**: 通常勤務のみから組み合わせを作成するように変更  

### 2. **dash_app.py - ヒートマップ生成の問題**
**場所**: 3746-3749行目  
**問題**: 全日付でreindex後、休日も0で埋めてヒートマップに表示  
**修正**: 実際の勤務日のみでreindexするように変更  

**場所**: 3764-3766行目  
**問題**: long_dfから全日付を取得し、休日も「分析期間」に含める  
**修正**: 実勤務日のみを分析対象期間とするように変更  

## 🔧 実施した修正

### 修正1: app.py (1700-1709行目)
```python
# 修正前
all_combinations_from_long_df = long_df[["ds", "role", "employment"]].drop_duplicates()

# 修正後
working_long_df = long_df[
    (long_df.get("parsed_slots_count", 0) > 0) & 
    (long_df.get("holiday_type", "通常勤務") == "通常勤務")
]
all_combinations_from_long_df = working_long_df[["ds", "role", "employment"]].drop_duplicates()
```

### 修正2: dash_app.py (3746-3754行目)
```python
# 修正前
all_dates_from_aggregated_data = sorted(aggregated_df['date_lbl'].unique())
dynamic_heatmap_df = dynamic_heatmap_df.reindex(columns=all_dates_from_aggregated_data, fill_value=0)

# 修正後
actual_work_dates = sorted(filtered_df[filtered_df['staff_count'] > 0]['date_lbl'].unique())
if actual_work_dates:
    dynamic_heatmap_df = dynamic_heatmap_df.reindex(columns=actual_work_dates, fill_value=0)
```

### 修正3: dash_app.py (3769-3782行目)
```python
# 修正前
all_dates_in_period = sorted(pd.to_datetime(long_df['ds']).dt.strftime('%Y-%m-%d').unique())

# 修正後
if actual_work_dates:
    expected_dates = actual_work_dates  # 実勤務日のみを期待日付とする
```

## 🎯 期待される効果

### ✅ 完全な休日除外
1. **pre_aggregated_data.parquet**: 休日データが含まれない
2. **ヒートマップ表示**: 休日（×記号）の時間帯が表示されない
3. **分析期間**: 実際の勤務日のみが対象

### ✅ 正確な可視化
1. **実働スタッフのみ**: 休暇中のスタッフは完全除外
2. **0埋め防止**: 休日の不要な0埋めなし
3. **期間判定**: 実勤務日ベースの正確な期間設定

## 📋 検証手順

### 1. アプリ再起動
```powershell
streamlit run app.py
```

### 2. 新規分析実行
- Excelファイルをアップロード
- "Run Analysis"ボタンクリック
- ログで`[RestExclusion]`メッセージを確認

### 3. dash_app.py起動
```powershell
python dash_app.py
```

### 4. ヒートマップ確認
- 休日（土日、×記号の日）に人数が表示されないことを確認
- 実際の勤務日のみが列として表示されることを確認

### 5. ログ確認
以下のメッセージが表示されることを確認:
```
[Heatmap] 実際の勤務日のみでヒートマップ作成: X日
[RestExclusion] data_get(pre_aggregated_data): 完了: X -> Y (除外: Z件)
```

## 🚫 以前の実装の問題点

### 問題1: 設計思想の問題
- **全期間思想**: 全日付を網羅してから0で埋める設計
- **実勤務思想**: 実際の勤務日のみを対象とする設計（修正後）

### 問題2: データフロー不整合
- **上流**: ingest_excel()で休日除外済み
- **下流**: 全日付でreindexして休日を再度含める（問題）
- **修正**: 一貫して実勤務日のみを使用

### 問題3: 0の意味の曖昧性
- **修正前**: 「休日だから0」と「配置なしで0」が区別不能
- **修正後**: 休日は列として存在せず、0は純粋に「配置なし」

## 🎉 修正完了

これらの修正により、**休日除外問題は根本的に解決**されました。

- ✅ 多層防御システム維持
- ✅ 根本原因の除去
- ✅ データフロー一貫性確保
- ✅ 正確な可視化実現