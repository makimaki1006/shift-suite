# 按分計算機能導入による副作用の詳細分析

## 概要

按分計算機能の導入により、UIの表示動作が意図せず変更された副作用について詳細に分析しました。ユーザーが報告している問題（「日付なしヒートマップの表示」「その他の表示変更」）の根本原因を特定し、修正方針を明確化します。

## 検出された主要な副作用

### 1. **60日制限機能の導入**

**問題**: 新しいバージョンで60日を超えるデータセットに制限が導入された

**backup版 (dash_app_back.py)**:
```python
# 制限なし - 全ての日付を表示
display_df = df_heat[date_cols]
time_labels = gen_labels(30)
display_df = display_df.reindex(time_labels, fill_value=0)
```

**current版 (dash_app.py)**:
```python
# 60日制限が追加された
if len(display_df_renamed.columns) > 60:  # 60日を超える場合
    log.info(f"[Heatmap] 大量データ検出: {len(display_df_renamed.columns)}日 -> 直近60日に制限")
    display_df_renamed = display_df_renamed.iloc[:, -60:]  # 🔴 ここで日付が切り取られる
```

**影響**: データに60日以上の期間が含まれている場合、古い日付が自動的に除外される

### 2. **動的スロット間隔システムの導入**

**backup版**:
```python
# 固定30分間隔
time_labels = gen_labels(30)
```

**current版**:
```python
# 動的スロット間隔システム
slot_minutes = DETECTED_SLOT_INFO['slot_minutes']
time_labels = gen_labels(slot_minutes)
```

**影響**: スロット間隔の自動検出により、時間軸の表示が変更される可能性

### 3. **統合休日除外システムの導入**

**backup版**:
```python
# 休日除外機能なし
display_df = df_heat[date_cols]
```

**current版**:
```python
# 複雑な休日除外フィルターが追加
if key in ['pre_aggregated_data', 'long_df', 'intermediate_data']:
    df = apply_rest_exclusion_filter(df, f"data_get({key})")

# ヒートマップ生成時にも追加フィルター
# 休日除外フィルタ: 事前生成されたヒートマップデータに0時間のスロットが残っている場合を考慮
```

**影響**: 休日や特定パターンを含む日付が除外され、表示される日付数が減少

### 4. **按分計算システムの統合**

**backup版**:
```python
def create_shortage_from_heat_all(heat_all_df: pd.DataFrame) -> pd.DataFrame:
    """
    heat_ALLデータから不足データを生成する
    """
    # シンプルな不足計算
    for date_col in date_columns:
        if date_col in heat_all_df.columns:
            # 実際の人数から必要人数を引いて不足を計算
```

**current版**:
```python
def create_shortage_from_heat_all(heat_all_df: pd.DataFrame) -> pd.DataFrame:
    """
    heat_ALLデータから不足データを生成する（按分方式対応版）
    
    修正: 2025年7月 - 按分方式による一貫した計算ロジック実装
    全体不足時間を基準として、各時間スロットの不足を按分計算
    """
    # 複雑な按分計算システム
    total_demand_by_slot = {}
    total_actual_by_slot = {}
    # ... 按分計算ロジック
```

**影響**: データ処理プロセスが複雑化し、データの流れが変更された

### 5. **新しいインポートと依存関係**

**backup版には存在しない依存関係**:
```python
from shift_suite.tasks.proportional_calculator import (
    ProportionalCalculator, calculate_proportional_shortage, validate_calculation_consistency,
    calculate_total_shortage_from_data, create_proportional_summary_df, create_employment_summary_df
)
from shift_suite.tasks.time_axis_shortage_calculator import TimeAxisShortageCalculator
from proportional_shortage_helper import (
    generate_proportional_shortage_data, update_data_cache_with_proportional,
    create_consistent_shortage_summary, validate_dashboard_consistency
)
```

**影響**: 新しい計算エンジンが副作用を引き起こしている可能性

## 具体的な表示動作への影響

### A. 日付表示の減少

1. **60日制限**: 長期間データで古い日付が除外される
2. **休日除外**: 実際の勤務がない日（0人の日）が休日と誤認され除外される
3. **データフィルタリング**: apply_rest_exclusion_filter による過度なデータ除外

### B. ヒートマップの表示品質低下

1. **カラースケール調整**: データが均一な場合の対策が追加されたが、副作用を引き起こす可能性
2. **パフォーマンス最適化**: 大量データのサンプリングが表示に影響
3. **フォントサイズ自動調整**: 表示条件に応じた自動調整が視覚的変化を引き起こす

### C. データ処理パイプラインの変更

1. **複数段階フィルタリング**: データ取得時とヒートマップ生成時の二重フィルタリング
2. **按分計算統合**: データ計算ロジックの根本的変更
3. **キャッシュシステム強化**: データの取得・保存方法の変更

## 根本原因の特定

### 主要因: 過度なデータフィルタリング

按分計算機能導入時に、データ品質向上を目的として複数のフィルタリング機能が追加されましたが、これらが**正常なデータまで除外**する副作用を引き起こしています。

1. **60日制限**: パフォーマンス向上のため
2. **休日除外**: データ品質向上のため  
3. **動的スロット**: 柔軟性向上のため

これらの機能は個別には有用ですが、組み合わせることで**ユーザーが期待する全データ表示**を阻害しています。

### 副次的要因: UI動作の予期しない変更

按分計算機能は背景で動作する想定でしたが、関連する最適化機能がUIの表示動作を変更してしまいました。

## 影響度評価

### 🔴 重大な影響
- **日付の欠落**: 60日制限により重要な履歴データが表示されない
- **休日誤除外**: 勤務実績がない正常な勤務日が除外される

### 🟡 中程度の影響  
- **表示スタイル変更**: フォントサイズ、レイアウトの自動調整
- **時間軸変更**: 動的スロット間隔による時間表示の変化

### 🟢 軽微な影響
- **計算精度向上**: 按分計算による数値精度の改善（これは良い変化）
- **パフォーマンス向上**: 大量データ処理の高速化（これは良い変化）

## 次のステップ

1. **RESTORATION_REQUIREMENTS.md**: 具体的な復元要件の定義
2. **FIX_IMPLEMENTATION_PLAN.md**: 段階的修正計画の策定

按分計算機能のメリットを保持しながら、backup版と同じUIの表示動作を復元する詳細な修正計画を作成します。