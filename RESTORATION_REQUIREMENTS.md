# UI表示動作復元要件定義書

## 目標

按分計算機能のメリットを**完全に保持**しながら、backup版（dash_app_back.py）と**完全に同一**のUI表示動作を復元する。

## 復元対象の特定

### 🎯 完全復元が必要な動作

#### 1. **日付表示の完全性**
- **要件**: データに含まれる**全ての日付**を表示する
- **現状問題**: 60日制限により古い日付が除外される
- **復元目標**: backup版と同じく、1年分のデータでも全日付を表示

#### 2. **実績なし日付の表示**  
- **要件**: 勤務実績が0人の日付も正常に表示する
- **現状問題**: 休日除外フィルターが実績なし日を誤って除外
- **復元目標**: 0人の勤務日も含めて全日程を表示

#### 3. **固定時間スロット間隔**
- **要件**: backup版と同じ30分固定間隔での表示
- **現状問題**: 動的スロット間隔により表示が変動する
- **復元目標**: 常に30分間隔で一貫した時間軸表示

#### 4. **シンプルなヒートマップ生成**
- **要件**: backup版と同じシンプルなヒートマップ描画
- **現状問題**: 複雑な最適化処理により表示スタイルが変化
- **復元目標**: 基本的なヒートマップ表示のみ

### 🔧 保持すべき按分計算機能

#### 1. **按分計算エンジン**
- ProportionalCalculator
- TimeAxisShortageCalculator  
- 按分計算による不足時間の精密計算

#### 2. **データ計算精度**
- 按分方式による一貫した計算
- 統計的分析の精度向上
- レポート生成の高品質化

#### 3. **パフォーマンス改善**
- データ処理の高速化
- メモリ使用量の最適化（表示制限を除く）

## 具体的修正要件

### A. ヒートマップ表示修正

#### A-1. 60日制限の無効化
```python
# 🔴 削除対象コード
if len(display_df_renamed.columns) > 60:
    log.info(f"[Heatmap] 大量データ検出: {len(display_df_renamed.columns)}日 -> 直近60日に制限")
    display_df_renamed = display_df_renamed.iloc[:, -60:]

# ✅ 復元要件: 制限なしで全日付表示
# 制限機能は完全削除し、backup版と同じ動作に戻す
```

#### A-2. 固定スロット間隔の復元
```python
# 🔴 変更対象コード
slot_minutes = DETECTED_SLOT_INFO['slot_minutes']
time_labels = gen_labels(slot_minutes)

# ✅ 復元要件: backup版と同じ固定30分間隔
time_labels = gen_labels(30)
```

#### A-3. 休日除外の無効化（表示レベル）
```python
# 🔴 変更対象: ヒートマップ表示時の過度な除外処理

# ✅ 復元要件: 
# - 計算レベルでの休日除外は保持（按分計算の精度のため）
# - 表示レベルでの除外は無効化（全データ表示のため）
```

### B. データフィルタリング修正

#### B-1. data_get()関数の復元
```python
# 🔴 現在の過度なフィルタリング
if key in ['pre_aggregated_data', 'long_df', 'intermediate_data']:
    df = apply_rest_exclusion_filter(df, f"data_get({key})")

# ✅ 復元要件: 
# - 計算用データには休日除外を適用（按分計算精度のため）
# - 表示用データには休日除外を非適用（全日表示のため）
```

#### B-2. ヒートマップ用データの特別処理
```python
# ✅ 新要件: 表示目的の場合はフィルタリングをスキップ
def data_get(key, default=None, for_display=False):
    # for_display=True の場合は休日除外フィルタを適用しない
    # これによりヒートマップで全日程を表示可能
```

### C. UI表示最適化の調整

#### C-1. カラースケール設定の簡素化
```python
# 🔴 複雑な最適化ロジック（表示変更の原因）
data_max = display_df_renamed.max().max()
data_min = display_df_renamed.min().min()
if data_max == data_min:
    color_range = [data_min - 0.1, data_max + 0.1] if data_min != 0 else [0, 1]

# ✅ 復元要件: backup版と同じシンプルな設定
fig = px.imshow(
    display_df_renamed,
    aspect='auto',
    color_continuous_scale=px.colors.sequential.Viridis,
    title=title,
    labels={'x': '日付', 'y': '時間', 'color': '人数'},
    text_auto=True
)
```

#### C-2. レイアウト設定の復元
```python
# 🔴 動的レイアウト調整（表示変更の原因）
font=dict(size=10 if len(display_df_renamed.columns) > 30 else 12)
if len(display_df_renamed.columns) > 30:
    fig.update_xaxes(tickangle=45)

# ✅ 復元要件: backup版と同じ固定レイアウト
fig.update_xaxes(tickvals=list(range(len(display_df.columns))))
```

## 修正方針

### フェーズ1: 表示レベルの復元（優先度：最高）

1. **60日制限の完全削除**
2. **固定30分間隔の復元**  
3. **ヒートマップ表示の簡素化**

### フェーズ2: データ処理の調整（優先度：高）

1. **表示用フラグの導入**（for_display=True）
2. **条件付きフィルタリング**の実装
3. **backup版互換レイヤー**の追加

### フェーズ3: 整合性確保（優先度：中）

1. **按分計算結果の保持確認**
2. **パフォーマンステスト**
3. **回帰テスト**

## 成功基準

### ✅ 必須達成項目

1. **完全日付表示**: データ期間の全日付が表示される
2. **0実績日表示**: 勤務実績0の日も正常に表示される  
3. **固定時間軸**: 30分間隔で一貫した時間表示
4. **按分計算保持**: 按分計算機能が正常に動作する

### ✅ 確認方法

1. **比較テスト**: backup版と current版で同一データの表示結果を比較
2. **長期データテスト**: 1年分データでの表示確認
3. **按分計算テスト**: 計算結果の精度確認

### ✅ 非回帰要件

1. **既存機能**: 按分計算以外の機能に影響なし
2. **パフォーマンス**: 表示速度の大幅低下なし
3. **データ整合性**: 計算結果の一貫性維持

## 実装優先順位

1. **即座対応**: 60日制限削除（最も影響大）
2. **当日対応**: 固定間隔復元、表示簡素化
3. **翌日対応**: データフィルタリング調整
4. **検証期間**: 総合テスト、性能確認

この要件に基づいて、詳細な実装計画を FIX_IMPLEMENTATION_PLAN.md で策定します。