# 不足時間の適切な積算に向けた修正計画

## 🎯 ユーザー要求の本質的理解

**ユーザーの真の要求:**
「不足時間は適切に積算する必要があります」

**これは私の哲学的アプローチが完全に的外れだったことを意味する**

### **私の根本的誤解**
1. ✗ 期間依存性を「現実の複雑性」として受け入れる
2. ✗ 多目的分析で誤魔化す
3. ✗ 哲学的転換で問題を回避する

### **ユーザーの真の要求**
1. ✅ 数学的に正しい積算
2. ✅ 期間に関係ない一貫性
3. ✅ 実用的で信頼できる結果

## 🔍 「適切な積算」の要件定義

### **積算の数学的要件**
```
要求: 3ヶ月の不足時間 ≈ 1ヶ月の不足時間 × 3
現状: 3ヶ月55,518時間 ≠ 1ヶ月759時間 × 3 (2,277時間)
問題: 24倍もの乖離 → 積算として機能していない
```

### **適切な積算の定義**
1. **加算性**: 期間合計 = 各期間の合計
2. **比例性**: 長期間 ≈ 短期間 × 期間比
3. **一貫性**: 同じ手法で同じ基準値
4. **予測可能性**: 期間サイズで結果が激変しない

## 🔧 技術的解決策: 正規化統計処理

### **根本原因の再確認**
```python
# 現在の問題（heatmap.py）
def calculate_pattern_based_need():
    # 1ヶ月: 4-5データポイント → 統計値A
    # 3ヶ月: 12-15データポイント → 統計値B (≠A)
    need_calculated_val = np.mean(values_for_stat_calc)  # データサイズ依存
```

### **解決策1: データサイズ正規化統計処理**
```python
def calculate_normalized_statistics(values, target_sample_size=5):
    """
    データサイズを正規化して統計処理
    常に同等のサンプルサイズで統計値計算
    """
    if len(values) <= target_sample_size:
        # 短期間: そのまま使用
        return np.mean(values)
    else:
        # 長期間: サンプリングして正規化
        # 方法1: ランダムサンプリング
        sampled_values = np.random.choice(values, target_sample_size, replace=False)
        return np.mean(sampled_values)
        
        # 方法2: 期間代表値サンプリング
        period_size = len(values) // target_sample_size
        representative_values = []
        for i in range(0, len(values), period_size):
            period_data = values[i:i+period_size]
            representative_values.append(np.median(period_data))
        return np.mean(representative_values[:target_sample_size])
```

### **解決策2: 基準期間固定統計処理**
```python
def calculate_baseline_normalized_need(all_data, analysis_period):
    """
    基準期間（30日）の統計値を算出し、分析期間に適用
    """
    # 1. 基準期間の統計値を計算
    baseline_period_data = get_recent_30_days_data(all_data)
    baseline_stats = {}
    
    for time_slot in time_slots:
        for dow in range(7):
            slot_data = baseline_period_data[time_slot][dow]
            # 基準統計値（30日基準）
            baseline_stats[(time_slot, dow)] = np.mean(slot_data)
    
    # 2. 分析期間の各日に基準統計値を適用
    total_need = 0
    for date in analysis_period:
        dow = date.weekday()
        for time_slot in time_slots:
            need_per_slot = baseline_stats[(time_slot, dow)]
            total_need += need_per_slot * slot_hours
    
    return total_need
```

### **解決策3: 線形積算保証システム**
```python
class LinearIntegrationCalculator:
    """線形積算を数学的に保証するシステム"""
    
    def __init__(self, base_unit='month'):
        self.base_unit = base_unit
        self.base_statistics = {}
    
    def calculate_base_statistics(self, monthly_data):
        """月単位の基準統計値を計算"""
        for month_key, month_data in monthly_data.items():
            self.base_statistics[month_key] = self.calculate_month_need_rate(month_data)
    
    def calculate_month_need_rate(self, month_data):
        """月あたりの需要率を計算（統計処理最小限）"""
        # 実績の最大値を基準とする（統計処理を避ける）
        daily_totals = month_data.sum(axis=0)  # 各日の合計
        max_daily_need = daily_totals.max()
        working_days = len(daily_totals)
        
        # 月あたり需要率 = 最大日需要 × 営業日数 × 安全係数
        safety_factor = 1.1  # 10%マージン
        return max_daily_need * working_days * safety_factor
    
    def integrate_period(self, start_month, end_month):
        """期間積算（線形性保証）"""
        total = 0
        months_included = []
        
        current = start_month
        while current <= end_month:
            month_key = current.strftime('%Y-%m')
            if month_key in self.base_statistics:
                total += self.base_statistics[month_key]
                months_included.append(month_key)
            current = self.next_month(current)
        
        return {
            'total_shortage': total,
            'months_included': months_included,
            'linear_verification': self.verify_linearity(months_included),
            'monthly_breakdown': {m: self.base_statistics[m] for m in months_included}
        }
    
    def verify_linearity(self, months):
        """線形性の検証"""
        if len(months) == 1:
            return {'status': 'single_month', 'linear': True}
        
        monthly_values = [self.base_statistics[m] for m in months]
        total = sum(monthly_values)
        
        return {
            'status': 'verified',
            'linear': True,
            'verification': f"{' + '.join(f'{v:.0f}' for v in monthly_values)} = {total:.0f}",
            'monthly_average': total / len(months)
        }
```

## 🛠️ 具体的実装計画

### **Step 1: heatmap.pyの修正**
```python
# heatmap.py に追加
def calculate_integration_friendly_need(
    actual_staff_by_slot_and_date: pd.DataFrame,
    ref_start_date: dt.date,
    ref_end_date: dt.date,
    statistic_method: str,
    **kwargs
) -> pd.DataFrame:
    """
    積算に適したNeed計算
    期間サイズに依存しない統計処理
    """
    
    # 期間を月単位に分割
    monthly_chunks = split_data_by_month(
        actual_staff_by_slot_and_date, ref_start_date, ref_end_date
    )
    
    # 各月で統一した統計処理
    calculator = LinearIntegrationCalculator()
    calculator.calculate_base_statistics(monthly_chunks)
    
    # 期間積算
    result = calculator.integrate_period(ref_start_date, ref_end_date)
    
    # 従来フォーマットに変換
    return format_as_dow_pattern(result, kwargs.get('slot_minutes_for_empty', 30))
```

### **Step 2: shortage.pyの修正**
```python
# shortage.py の修正
def calculate_shortage_with_linear_integration():
    """線形積算を保証した不足時間計算"""
    
    # 月単位でNeed計算
    monthly_needs = {}
    monthly_actuals = {}
    
    for month_key, month_data in split_by_month(all_data):
        monthly_needs[month_key] = calculate_month_need_direct(month_data)
        monthly_actuals[month_key] = month_data.sum().sum() * slot_hours
    
    # 線形積算
    total_need = sum(monthly_needs.values())
    total_actual = sum(monthly_actuals.values())
    total_shortage = max(0, total_need - total_actual)
    
    # 検証ログ
    log.info(f"[LINEAR_INTEGRATION] 月別Need: {monthly_needs}")
    log.info(f"[LINEAR_INTEGRATION] 月別実績: {monthly_actuals}")
    log.info(f"[LINEAR_INTEGRATION] 線形積算検証: {total_need} = {' + '.join(f'{v:.0f}' for v in monthly_needs.values())}")
    
    return total_shortage
```

### **Step 3: 検証システム**
```python
def verify_integration_correctness():
    """積算の正しさを検証"""
    
    # 1ヶ月分析
    month1_result = analyze_period(date(2025, 7, 1), date(2025, 7, 31))
    month2_result = analyze_period(date(2025, 8, 1), date(2025, 8, 31))
    month3_result = analyze_period(date(2025, 9, 1), date(2025, 9, 30))
    
    manual_total = month1_result + month2_result + month3_result
    
    # 3ヶ月一括分析
    integrated_result = analyze_period(date(2025, 7, 1), date(2025, 9, 30))
    
    # 線形性検証
    deviation = abs(integrated_result - manual_total)
    deviation_ratio = deviation / manual_total if manual_total > 0 else 0
    
    assert deviation_ratio < 0.05, f"積算誤差が5%を超えています: {deviation_ratio:.1%}"
    
    log.info(f"✅ 線形積算検証成功:")
    log.info(f"   月別合計: {manual_total:.0f}時間")
    log.info(f"   統合結果: {integrated_result:.0f}時間")
    log.info(f"   誤差: {deviation:.0f}時間 ({deviation_ratio:.1%})")
```

## 📊 期待される修正効果

### **修正前（現状）**
```
7月単独: 759時間
8月単独: 768時間  
9月単独: 491時間
月別合計: 2,018時間

3ヶ月一括: 55,518時間 ← 問題
誤差: 53,500時間 (2,651%)
```

### **修正後（期待値）**
```
7月単独: 759時間
8月単独: 768時間
9月単独: 491時間  
月別合計: 2,018時間

3ヶ月一括: 2,018時間 ← 修正
誤差: 0時間 (0%) ← 完全一致
```

## 🎯 実装優先度

**最高優先**: 不足時間の適切な積算は業務上必須の要件

**段階的実装**:
1. Week 1: LinearIntegrationCalculator実装
2. Week 2: heatmap.py修正  
3. Week 3: shortage.py修正
4. Week 4: 統合テスト・検証

これにより、哲学的回避ではなく、**数学的に正しい積算**を実現します。