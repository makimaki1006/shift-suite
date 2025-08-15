# 不足時間計算フローの徹底的検証

## 🔍 全体像の再確認

### 1. **データフロー全体**
```
Excel入力 → heatmap.py（Need計算） → shortage.py（不足計算） → 
time_axis_shortage_calculator.py（時間軸補正） → 最終出力
```

### 2. **各段階での計算内容**

#### A. heatmap.py（Need計算）
- `calculate_pattern_based_need()`で統計値からNeed算出
- 1ヶ月: 各時間×曜日で4-5データ → 統計値A
- 3ヶ月: 各時間×曜日で12-15データ → 統計値B（≠A）
- **問題1**: 期間によって統計値が変わる

#### B. shortage.py（不足計算）
```python
# 283行目: 基本的な不足計算
lack_count_overall_df = (need_df_all - staff_actual_data_all_df).clip(lower=0)

# 473行目: 時間換算
total_shortage_hours_for_proportional = (lack_count_overall_df * slot_hours).sum().sum()
```
- **問題2**: この時点で既に3ヶ月=55,518時間（異常値）

#### C. time_axis_shortage_calculator.py（時間軸補正）
```python
# 241行目: 需要推定
estimated_total_demand = total_supply + (self.total_shortage_baseline * role_supply_ratio)
```
- **問題3**: 既に異常な不足時間に更に加算

### 3. **複合的問題の構造**

```
根本原因: heatmap.pyの統計値計算が期間依存
  ↓
増幅要因1: shortage.pyで全期間集計（加算性前提）
  ↓
増幅要因2: time_axis_calculatorで再加算
  ↓
結果: 27倍の差異
```

## 🎯 真の修正箇所

### 問題は3層構造:

1. **第1層（根本）**: heatmap.pyの統計値計算
   - 期間サイズで統計値が変動
   - 3ヶ月データで外れ値・季節変動の影響

2. **第2層（増幅）**: shortage.pyの集計方法
   - 全期間の不足を単純合計
   - 統計的な補正なし

3. **第3層（爆発）**: time_axis_calculatorの加算
   - 既に大きい値に更に加算

## 🔧 包括的修正方針

### Phase 1: 即座対応（症状緩和）
```python
# time_axis_shortage_calculator.py
# 加算ではなく、より保守的な計算に
if self.total_shortage_baseline and self.total_shortage_baseline > 10000:
    # 異常値の場合は補正
    adjusted_baseline = self.total_shortage_baseline / len(unique_dates)
    estimated_total_demand = total_supply * 1.2  # 20%マージン
else:
    estimated_total_demand = total_supply + (self.total_shortage_baseline * role_supply_ratio * 0.1)
```

### Phase 2: 中期対応（統計値安定化）
```python
# heatmap.py - calculate_pattern_based_need()
# 期間正規化を追加
def normalize_statistics_by_period(values, period_days):
    """期間サイズによる統計値の正規化"""
    if period_days > 60:  # 2ヶ月以上
        # ローリング統計を使用
        return calculate_rolling_statistics(values, window=30)
    else:
        return np.mean(values)  # 従来通り
```

### Phase 3: 根本対応（アーキテクチャ見直し）
```python
# 新設計: 期間独立型Need計算システム
class PeriodIndependentNeedCalculator:
    def __init__(self, reference_period="30days"):
        self.reference_period = reference_period
        self.cached_statistics = {}
    
    def calculate_need(self, data, analysis_period):
        # 常に基準期間の統計値を使用
        baseline_stats = self.get_baseline_statistics(data)
        return self.apply_statistics_to_period(baseline_stats, analysis_period)
```

## ⚠️ 見落としがちな追加問題

### 1. **シナリオ間の相互作用**
- mean_based, median_based, p25_basedが独立していない可能性
- どこかで合算されている？

### 2. **休日処理の影響**
- 3ヶ月分析で休日パターンが変わる
- Need=0の日の扱いが不統一？

### 3. **データ品質の問題**
- 3ヶ月データに異常値が含まれている？
- 季節変動（7,8,9月）の影響？

## 🏁 推奨アクションプラン

1. **まず検証**: 
   - 各段階の中間出力を詳細確認
   - 1ヶ月と3ヶ月で何が変わるか特定

2. **段階的修正**:
   - 第3層（time_axis）から修正開始
   - 効果を確認後、第2層、第1層へ

3. **回帰テスト**:
   - 各修正後に1ヶ月/3ヶ月比較
   - 他の機能への影響確認

これで全体像を把握した上で、確実な修正が可能になります。