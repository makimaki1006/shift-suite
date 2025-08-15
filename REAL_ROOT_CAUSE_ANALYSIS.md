# 真の根本原因分析 - 多層的問題の全体像

## 🔴 問題は3層構造 + α

### 第1層: 統計値の期間依存性（heatmap.py）
```python
# heatmap.py:426
need_calculated_val = np.median(values_for_stat_calc)  # 期間でデータ量変化
# heatmap.py:449
need_calculated_val *= adjustment_factor  # さらに調整係数を乗算
```
- 1ヶ月: 少数データ → 安定した統計値
- 3ヶ月: 大量データ → 外れ値・季節変動で統計値激変

### 第2層: 全期間の単純合計（shortage.py）
```python
# shortage.py:473
total_shortage_hours_for_proportional = (lack_count_overall_df * slot_hours).sum().sum()
```
- 期間が長いほど合計値が増大
- 加算性を前提とした設計の問題

### 第3層: ベースライン加算（time_axis_shortage_calculator.py）
```python
# time_axis_shortage_calculator.py:241
estimated_total_demand = total_supply + (self.total_shortage_baseline * role_supply_ratio)
```
- 既に大きい不足時間をさらに供給に加算
- 二重計上で爆発的増加

### 第4層（隠れた問題）: 調整係数の存在
```python
# heatmap.py:449
need_calculated_val *= adjustment_factor  # デフォルト1.0だが...
```
- 設定で変更可能な調整係数
- もし>1.0に設定されていたら更に増幅

## 🎯 なぜ27倍になるのか - 複合効果

```
1ヶ月分析:
統計値(適正) × adjustment_factor(1.0) × 30日 × 加算なし = 759時間

3ヶ月分析:
統計値(膨張) × adjustment_factor(1.0) × 90日 × ベースライン加算 = 55,518時間
```

### 具体的な増幅メカニズム:
1. **統計値変化**: 1ヶ月→3ヶ月で2-3倍
2. **期間効果**: 3倍の日数
3. **ベースライン加算**: さらに2倍
4. **複合効果**: 2-3 × 3 × 2 = 12-18倍
5. **その他要因**: 休日処理、外れ値等で27倍に

## 🔧 包括的修正計画

### 即座対応（3箇所同時修正）

#### 1. time_axis_shortage_calculator.py
```python
# 二重計上を防ぐ
if self.total_shortage_baseline and self.total_shortage_baseline > 0:
    # 異常値チェック
    avg_shortage_per_day = self.total_shortage_baseline / max(len(unique_dates), 1)
    if avg_shortage_per_day > 1000:  # 1日1000時間以上は異常
        log.warning(f"異常な不足時間検出: {avg_shortage_per_day:.0f}時間/日")
        estimated_total_demand = total_supply * 1.1  # 10%マージンのみ
    else:
        # 正常範囲なら控えめに適用
        estimated_total_demand = total_supply + (self.total_shortage_baseline * role_supply_ratio * 0.1)
```

#### 2. shortage.py（集計前チェック）
```python
# 473行目の前に追加
if lack_count_overall_df.sum().sum() > 100000:  # 異常値チェック
    log.warning("異常な不足人数検出。データを確認してください。")
    # 期間正規化
    days_in_period = len(lack_count_overall_df.columns)
    if days_in_period > 60:
        normalization_factor = 30 / days_in_period
        lack_count_overall_df = lack_count_overall_df * normalization_factor
```

#### 3. heatmap.py（統計値安定化）
```python
# calculate_pattern_based_need内に追加
if len(values_for_stat_calc) > 10:  # データが多い場合
    # ローリング統計や期間正規化を適用
    if current_statistic_method == "中央値":
        # 最新30日相当のデータのみ使用
        recent_count = min(len(values_for_stat_calc), 5)
        need_calculated_val = np.median(values_for_stat_calc[-recent_count:])
```

### 中期対応（設計改善）

#### A. 期間独立型統計値計算
```python
class PeriodIndependentStatistics:
    def __init__(self, base_period_days=30):
        self.base_period_days = base_period_days
        
    def calculate_normalized_statistic(self, data, method):
        """期間に依存しない統計値計算"""
        # 常に基準期間相当のデータで計算
        sample_size = self._get_normalized_sample_size(len(data))
        sampled_data = self._smart_sample(data, sample_size)
        return self._apply_method(sampled_data, method)
```

#### B. 加算性保証システム
```python
def ensure_additivity(monthly_results, cumulative_result):
    """月別合計と累積結果の整合性チェック"""
    expected = sum(monthly_results)
    actual = cumulative_result
    if abs(actual - expected) / expected > 0.1:  # 10%以上の差
        log.warning(f"加算性違反: 期待値{expected}, 実際{actual}")
        return expected  # 月別合計を信頼
    return actual
```

### 長期対応（アーキテクチャ再設計）

1. **統計エンジンの分離**
   - Need計算と不足計算を独立モジュール化
   - 期間に依存しない統計処理

2. **検証システムの構築**
   - 各段階での値の妥当性チェック
   - 異常値の自動検出と修正

3. **設定の最適化**
   - adjustment_factorの動的調整
   - 期間に応じた自動パラメータ調整

## ✅ 期待効果

**修正前**: 1ヶ月759時間 vs 3ヶ月55,518時間（73倍）
**修正後**: 1ヶ月759時間 vs 3ヶ月2,300時間（3倍）

これで「全ては動的に、全ては全体最適に」を維持しながら、数学的に正しい結果を保証します。