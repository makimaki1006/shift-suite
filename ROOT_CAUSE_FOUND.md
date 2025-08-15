# 根本原因特定: 不足時間の二重計上問題

## 🚨 問題の核心

**不足時間が期間依存で27倍になる根本原因を特定しました！**

### 問題の流れ

1. **shortage.py:473** で総不足時間を計算
```python
total_shortage_hours_for_proportional = (lack_count_overall_df * slot_hours).sum().sum()
```

2. この値を`total_shortage_baseline`として`time_axis_shortage_calculator.py`へ渡す

3. **time_axis_shortage_calculator.py:241** で問題発生
```python
# 🚨 ここが問題！供給量に不足時間を加算している
estimated_total_demand = total_supply + (self.total_shortage_baseline * role_supply_ratio)
```

### なぜ27倍になるのか

1. **1ヶ月分析時**: 
   - 統計値から適切なNeed値を計算（例: 759時間）
   - total_shortage_baseline = 759時間
   - 時間軸計算で供給量 + 759時間 → まだ妥当な範囲

2. **3ヶ月分析時**:
   - 統計値が変わりNeed値が激増
   - total_shortage_baseline = 55,518時間（既に異常）
   - 時間軸計算で供給量 + 55,518時間 → さらに膨張

### 二重計上のメカニズム

```
統計計算で不足時間算出 → それをベースラインとして渡す → 
時間軸計算で「供給 + 不足」を需要として再計算 → 不足の二重計上
```

## 🎯 修正方針

### 1. 短期修正（即座対応）
`time_axis_shortage_calculator.py`の241行目を修正:
```python
# 修正前: 供給に不足を加算（二重計上）
estimated_total_demand = total_supply + (self.total_shortage_baseline * role_supply_ratio)

# 修正後: ベースラインを直接使用
estimated_total_demand = self.total_shortage_baseline * role_supply_ratio
```

### 2. 中期修正（設計見直し）
- 不足時間の計算フローを一本化
- 統計ベース計算と時間軸ベース計算の役割分担明確化
- 二重計上を防ぐアーキテクチャ設計

### 3. 長期修正（根本解決）
- Need計算の期間依存性解消（前述の基準期間固定方式）
- 時間軸計算の独立性確保
- 加算性の数学的保証

## ✅ 期待効果

**修正前**:
```
1ヶ月: 759時間 → 時間軸で更に加算
3ヶ月: 55,518時間 → 時間軸で更に加算（27倍の差）
```

**修正後**:
```
1ヶ月: 759時間（適正値）
3ヶ月: 2,300時間程度（月別合計に近い値）
```

これで「全ては動的に、全ては全体最適に」を維持しながら、正しい不足時間計算が実現できます。