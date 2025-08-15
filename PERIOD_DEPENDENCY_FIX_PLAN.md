# 期間依存性修正計画

## 🔍 根本原因確定

**ファイル:** `shift_suite/tasks/heatmap.py:421-432`
**問題箇所:** `calculate_pattern_based_need`関数の統計値計算

```python
# 問題の統計値計算
if current_statistic_method == "25パーセンタイル":
    need_calculated_val = np.percentile(values_for_stat_calc, 25)  # ← データサイズ依存
elif current_statistic_method == "中央値":
    need_calculated_val = np.median(values_for_stat_calc)          # ← データサイズ依存
else:  # 平均値
    need_calculated_val = np.mean(values_for_stat_calc)           # ← データサイズ依存
```

**データ量変化の影響:**
- 1ヶ月: 各時間帯×曜日で約4回のデータ → 安定した統計値
- 3ヶ月: 各時間帯×曜日で約12回のデータ → 外れ値・季節変動の影響で統計値激変

## 🎯 修正方針

### A. 基準期間固定方式 (推奨)
統計値計算を固定期間（例：直近1ヶ月）に基づいて実行し、その基準値を使って任意期間の分析を行う

### B. 期間正規化方式
分析期間に応じて統計値を正規化する係数を適用

### C. 階層集約方式
月別分析を基本単位とし、長期分析は月別結果を集約

## 🔧 実装計画

### Phase 1: 基準期間統計値キャッシュ機能
1. `get_reference_statistics()` 関数を追加
2. 基準期間（直近30日等）の統計値を計算・保存
3. 任意期間分析時はキャッシュされた統計値を使用

### Phase 2: 期間独立Need計算
1. `calculate_pattern_based_need_fixed()` 関数を作成
2. 固定統計値を使用してNeed値計算
3. 加算性を数学的に保証

### Phase 3: 後方互換性維持
1. 既存関数はそのまま保持
2. 新関数を段階的に適用
3. 設定で切り替え可能

## ✅ 期待効果

```
修正前: 3ヶ月一気(55,518h) ≠ 月別合計(2,018h) [2,651%差異]
修正後: 3ヶ月一気 ≈ 月別合計 [<5%差異]
```

**「全ては動的に、全ては全体最適に」の思想を維持しながら加算性を保証**