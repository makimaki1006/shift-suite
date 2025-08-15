# UI表示動作復元実装計画

## 実装概要

按分計算機能を**完全保持**しながら、backup版と同一のUI表示動作を復元するための段階的実装計画。

## フェーズ1: 緊急修正（即座実行）

### 🔥 最優先修正: 60日制限の削除

**対象ファイル**: `/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/dash_app.py`

**修正箇所**: `generate_heatmap_figure()` 関数

```python
# 🔴 削除対象コード（行 ~45-48）
# パフォーマンス最適化: 大きなデータセットの場合はサンプリング
if len(display_df_renamed.columns) > 60:  # 60日を超える場合
    log.info(f"[Heatmap] 大量データ検出: {len(display_df_renamed.columns)}日 -> 直近60日に制限")
    display_df_renamed = display_df_renamed.iloc[:, -60:]

# ✅ 修正後: この部分を完全削除
# （コメントアウトではなく完全削除）
```

**期待効果**: データ期間の全日付が表示されるようになる

### 🔥 最優先修正: 固定30分間隔の復元

**修正箇所**: `generate_heatmap_figure()` 関数

```python
# 🔴 変更対象コード（行 ~20-22）
# 動的スロット間隔を使用してラベル生成
slot_minutes = DETECTED_SLOT_INFO['slot_minutes']
time_labels = gen_labels(slot_minutes)

# ✅ 修正後: backup版と同じ固定30分間隔
time_labels = gen_labels(30)
```

**期待効果**: 時間軸表示がbackup版と同一になる

## フェーズ2: 表示最適化の調整（当日実行）

### 🎯 ヒートマップ表示の簡素化

**修正箇所**: `generate_heatmap_figure()` 関数のカラースケール部分

```python
# 🔴 変更対象: 複雑なカラースケール最適化（行 ~52-70）
data_max = display_df_renamed.max().max()
data_min = display_df_renamed.min().min()
if data_max == data_min:
    color_range = [data_min - 0.1, data_max + 0.1] if data_min != 0 else [0, 1]
else:
    color_range = [data_min, data_max]

fig = px.imshow(
    display_df_renamed,
    aspect='auto',
    color_continuous_scale=px.colors.sequential.Viridis,
    title=title,
    labels={'x': '日付', 'y': '時間', 'color': '人数'},
    text_auto=True,
    zmin=color_range[0],
    zmax=color_range[1]
)

# ✅ 修正後: backup版と同じシンプルな設定
fig = px.imshow(
    display_df_renamed,
    aspect='auto',
    color_continuous_scale=px.colors.sequential.Viridis,
    title=title,
    labels={'x': '日付', 'y': '時間', 'color': '人数'},
    text_auto=True  # zmin, zmaxは指定しない
)
```

### 🎯 レイアウト設定の復元

```python
# 🔴 変更対象: 動的レイアウト調整（行 ~80-110）
confidence_info = ""
if DETECTED_SLOT_INFO['auto_detected']:
    confidence_info = f" (検出スロット: {slot_minutes}分, 信頼度: {DETECTED_SLOT_INFO['confidence']:.2f})"

fig.update_layout(
    height=600,
    xaxis_title="日付",
    yaxis_title=f"時間{confidence_info}",
    title_x=0.5,
    autosize=True,
    font=dict(size=10 if len(display_df_renamed.columns) > 30 else 12),
)

if len(display_df_renamed.columns) > 30:
    fig.update_xaxes(tickangle=45)
else:
    fig.update_xaxes(tickvals=list(range(len(display_df.columns))))

if slot_minutes < 30:
    fig.update_yaxes(dtick=2)

# ✅ 修正後: backup版と同じシンプルなレイアウト
fig.update_traces(
    texttemplate='%{text}',
    textfont={"size": 10}
)
fig.update_xaxes(tickvals=list(range(len(display_df.columns))))
```

## フェーズ3: データフィルタリング調整（翌日実行）

### 🔧 表示用フラグの導入

**修正箇所**: `data_get()` 関数に `for_display` パラメータを追加

```python
def data_get(key: str, default=None, for_display: bool = False):
    """
    データキャッシュから値を取得（表示用フラグ追加版）
    
    Args:
        key: データキー
        default: デフォルト値  
        for_display: True の場合、表示用として休日除外フィルタを適用しない
    """
    # ... 既存のキャッシュ確認ロジック ...
    
    # 🔧 新規追加: 表示用の場合は休日除外フィルタをスキップ
    if not for_display and key in ['pre_aggregated_data', 'long_df', 'intermediate_data']:
        df = apply_rest_exclusion_filter(df, f"data_get({key})")
    
    # 按分計算用のデータは常にフィルタリング適用
    # 表示用のデータはフィルタリングスキップ
```

### 🔧 ヒートマップ用データ取得の修正

**修正箇所**: ヒートマップ生成時のデータ取得

```python
# 🔴 変更対象
df_heat = data_get(heat_key, pd.DataFrame())

# ✅ 修正後: 表示用フラグを指定
df_heat = data_get(heat_key, pd.DataFrame(), for_display=True)
```

## フェーズ4: 按分計算機能の保護（並行実行）

### 🛡️ 按分計算エンジンの独立性確保

按分計算機能は表示システムとは独立して動作させ、UI修正の影響を受けないよう保護します。

**保護対象**:
- `ProportionalCalculator`
- `TimeAxisShortageCalculator`  
- `proportional_shortage_helper`の全機能

**実装方針**:
- 按分計算は従来通り、フィルタリング済みデータを使用
- 表示は未フィルタリングデータを使用
- 計算精度と表示完全性の両立

## フェーズ5: 検証とテスト（修正後実行）

### 🧪 比較テスト

```python
# テスト実装例
def test_ui_restoration():
    """backup版との表示結果比較テスト"""
    
    # 1. 同一データでの表示結果比較
    test_data = load_test_excel()
    
    backup_result = generate_heatmap_backup_version(test_data)
    current_result = generate_heatmap_current_version(test_data)
    
    # 2. 日付数の比較
    assert backup_result.date_count == current_result.date_count
    
    # 3. 時間軸の比較  
    assert backup_result.time_axis == current_result.time_axis
    
    # 4. 表示データの比較
    assert backup_result.display_data.equals(current_result.display_data)
```

### 🧪 長期データテスト

```python
def test_long_term_data():
    """1年分データでの表示確認"""
    
    # 365日分のテストデータ生成
    long_term_data = generate_yearly_test_data()
    
    result = generate_heatmap(long_term_data)
    
    # 全日付が表示されることを確認
    assert result.date_count == 365
    assert "60日制限" not in result.logs
```

### 🧪 按分計算精度テスト

```python
def test_proportional_calculation_accuracy():
    """按分計算機能の精度確認"""
    
    # UI修正後も按分計算が正常動作することを確認
    calc_result = ProportionalCalculator.calculate(test_data)
    
    assert calc_result.accuracy >= 0.95
    assert calc_result.consistency_check == True
```

## 実装スケジュール

### Day 1 (即座実行)
- ✅ フェーズ1: 60日制限削除、固定間隔復元

### Day 1 (同日)  
- ✅ フェーズ2: 表示最適化調整
- ✅ 初期テスト実行

### Day 2
- ✅ フェーズ3: データフィルタリング調整
- ✅ フェーズ4: 按分計算保護
- ✅ フェーズ5: 総合検証

### Day 3
- ✅ 回帰テスト
- ✅ パフォーマンステスト
- ✅ ユーザー確認

## リスク管理

### 🚨 想定リスク

1. **按分計算精度低下**: データフィルタリング変更による影響
2. **パフォーマンス低下**: 60日制限削除による影響  
3. **予期しない副作用**: 他機能への波及影響

### 🛡️ 対策

1. **段階的実装**: フェーズ分けによるリスク分散
2. **バックアップ保持**: 各段階での動作バックアップ
3. **ロールバック準備**: 問題発生時の即座復旧

## 成功判定基準

### ✅ 必須達成項目

1. **日付表示**: データ期間の全日付表示 ✓
2. **時間軸**: 30分固定間隔表示 ✓  
3. **0実績日**: 勤務0の日も正常表示 ✓
4. **按分計算**: 計算精度維持 ✓

### ✅ 確認方法

1. **視覚確認**: backup版と同一の表示
2. **数値確認**: 表示日数、時間軸の一致
3. **機能確認**: 按分計算結果の一致

この計画に従って修正を実行することで、按分計算機能を保持しながらbackup版と同一のUI表示動作を復元できます。