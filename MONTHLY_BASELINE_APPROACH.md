# 月単位基準値策定方式 - 理想的な解決策

## 🎯 提案されたアプローチ

**「1ヶ月ごとに基準値（Need等）を策定した後に、登録期間（3ヶ月）で統計処理」**

## ✅ なぜこれが優れているか

### 1. **統計的に正しい**
```
現在: 3ヶ月の生データ → 統計値（外れ値・季節変動で歪む）
提案: 各月の基準値 → 3つの値から統計値（安定）
```

### 2. **加算性を保証**
```
7月: 基準値A（759時間）
8月: 基準値B（768時間）  
9月: 基準値C（491時間）

3ヶ月の統計値:
- 平均: (759+768+491)/3 = 673時間
- 中央値: 759時間
- P25: 625時間

→ 月別合計(2,018時間)と整合性が取れる！
```

### 3. **季節変動を適切に扱える**
- 各月の特性を保持
- 極端な月があっても他の月に影響しない
- トレンドも把握可能

## 🔧 実装イメージ

### Phase 1: 月次基準値計算
```python
def calculate_monthly_baseline(month_data):
    """月単位で基準値を計算"""
    return {
        'mean_based': calculate_need_for_month(month_data, method='mean'),
        'median_based': calculate_need_for_month(month_data, method='median'),
        'p25_based': calculate_need_for_month(month_data, method='p25'),
        'total_shortage': calculate_shortage_for_month(month_data)
    }
```

### Phase 2: 期間統計処理
```python
def calculate_period_statistics(monthly_baselines):
    """月次基準値から期間統計を計算"""
    # 各月の基準値を集約
    monthly_values = [m['total_shortage'] for m in monthly_baselines]
    
    return {
        'period_mean': np.mean(monthly_values),
        'period_median': np.median(monthly_values),
        'period_p25': np.percentile(monthly_values, 25),
        'period_total': sum(monthly_values),  # 加算性保証
        'monthly_details': monthly_baselines
    }
```

### Phase 3: 統合システム
```python
class HierarchicalNeedCalculator:
    """階層型Need計算システム"""
    
    def calculate(self, data, analysis_period):
        # 月ごとに分割
        monthly_chunks = split_by_month(data)
        
        # 各月の基準値計算
        monthly_baselines = []
        for month_data in monthly_chunks:
            baseline = calculate_monthly_baseline(month_data)
            monthly_baselines.append(baseline)
        
        # 期間統計
        if len(monthly_baselines) == 1:
            # 1ヶ月なら月次値をそのまま使用
            return monthly_baselines[0]
        else:
            # 複数月なら統計処理
            return calculate_period_statistics(monthly_baselines)
```

## 📊 期待される結果

### 現在の問題
```
1ヶ月: 759時間
3ヶ月一気: 55,518時間 (73倍！)
```

### 提案方式での結果
```
7月: 759時間
8月: 768時間
9月: 491時間
3ヶ月統計:
  - 平均: 673時間/月
  - 合計: 2,018時間
  - 最大月: 768時間
  - 最小月: 491時間
```

## 🏆 メリットまとめ

1. **数学的整合性**: 加算性が保証される
2. **安定性**: 外れ値の影響を最小化
3. **解釈性**: 月次トレンドが見える
4. **柔軟性**: 任意期間に対応可能
5. **互換性**: 既存システムとの共存可能

## ⚠️ 実装時の考慮点

1. **月の境界処理**
   - 月末月初のデータ扱い
   - 不完全な月の処理

2. **重み付け**
   - 日数の違い（28日vs31日）
   - 営業日数の考慮

3. **トレンド分析**
   - 月次推移の可視化
   - 異常月の検出

## 🚀 実装優先度

**最優先**: この方式は根本的に問題を解決するため、最優先で実装すべきです。

**段階的導入**:
1. まず月次基準値計算を実装
2. 既存システムと並行稼働
3. 検証後に完全移行

これにより「全ては動的に、全ては全体最適に」の理念を守りながら、数学的に正しい分析が実現できます！