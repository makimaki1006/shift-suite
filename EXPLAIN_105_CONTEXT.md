# 1.05の意図の詳細説明

**作成日**: 2025年08月01日

## 🐛 元のバグ

### 循環参照の問題
```python
# 問題のあったコード（概念）
def _calculate_demand_coverage(self, total_shortage_baseline):
    if total_shortage_baseline > 0:
        # バグ：不足から需要を逆算（循環増幅）
        estimated_demand = supply + total_shortage_baseline * factor
```

**結果**: 不足→需要増→不足増→需要増... の無限ループ

## 🔧 修正内容

### 循環参照の排除
```python
# 修正後
def _calculate_demand_coverage(self, supply_by_slot, ...):
    total_supply = sum(supply_by_slot.values())
    # 独立した計算
    estimated_demand = total_supply * 1.05
```

## ❓ なぜ1.05なのか

### 1. 関数の役割
`_calculate_demand_coverage`は時間軸分析の一部で：
- 供給の時間分布を分析
- カバレッジ率を計算
- 効率性指標を算出

**メインのNeed計算ではありません**

### 2. 1.05の意味
- 「需要は供給より5%多い」という業界標準的な仮定
- 循環参照を完全に排除するための独立計算
- カバレッジ率計算のための参考値

### 3. 重要な点
**これは何ではないか：**
- ❌ 実際のNeed値を1.05倍にする処理
- ❌ 全体の需要計算を置き換えるもの
- ❌ データを操作するもの

**これは何か：**
- ✅ 時間軸分析での効率性計算用
- ✅ 循環参照バグの修正
- ✅ 補助的な分析指標

## 📊 実際のNeed計算

### 正しいNeed計算の流れ
1. **データ読み込み** (heatmap.py)
   - Excelから実際のNeed値を読み込み
   - 統計処理を実施
   - need_per_date_slot.parquetに保存

2. **不足計算** (shortage.py)
   - 保存されたNeed値を使用
   - Shortage = Need - Staff

3. **時間軸分析** (time_axis_shortage_calculator.py)
   - 補助的な分析
   - ここで1.05を使用（メインではない）

### 独立性の保証
- 実際のNeed値：Excelデータに基づく正確な値
- 1.05の使用：時間軸分析の効率性評価のみ
- 両者は独立：Need計算に1.05は影響しない

## 🎯 結論

1.05は：
- **循環参照バグを修正**するための措置
- **時間軸分析**での効率性評価用
- **実際のNeed計算には影響しない**

実際のNeed値は：
- Excelデータから正確に読み込まれる
- 統計処理されて保存される
- 1.05の影響を受けない

つまり、1.05は「バグ修正のための技術的措置」であり、「実際の需要計算を歪めるもの」ではありません。
