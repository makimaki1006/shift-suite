# 既存システム設計尊重型・一貫性確保計画

## 🎯 基本方針

**按分方式の数学的正確性を保持**しつつ、**既存shift-suiteアーキテクチャを最大限尊重**する統合アプローチを実施

## 📋 現状問題の構造化理解

### A. データフロー設計の根本問題
```
heatmap.py → need_per_date_slot.parquet (全職種統合Need)
             ↓
shortage.py → 職種別分析で統合Need値を誤用
             ↓
dashboard.py → 不整合な集計値表示
```

### B. Need計算アーキテクチャの分離問題
- **全体Need**: heatmap.pyで正確に計算・保存
- **職種別Need**: shortage.pyで統合値を部分抽出（不正確）
- **雇用形態別Need**: 独立計算（不一致発生）

## 🔧 システム尊重型・統合修正戦略

### Phase 1: 詳細Need計算フロー拡張

#### 1.1 heatmap.py拡張（Need計算の完全化）
```python
# 現状: need_per_date_slot.parquet (全職種統合のみ)
# 拡張: 職種別・雇用形態別Need詳細も併せて保存

def enhanced_build_heatmap(...):
    # 既存の全職種統合Need計算
    need_all_final = calculate_overall_need(...)
    need_all_final.to_parquet("need_per_date_slot.parquet")
    
    # 【新規追加】職種別Need詳細計算
    need_by_role = calculate_role_specific_need(long_df, ...)
    need_by_role.to_parquet("need_per_date_slot_by_role.parquet")
    
    # 【新規追加】雇用形態別Need詳細計算  
    need_by_employment = calculate_employment_specific_need(long_df, ...)
    need_by_employment.to_parquet("need_per_date_slot_by_employment.parquet")
```

#### 1.2 Need計算の一貫性保証メカニズム
```python
def validate_need_consistency(need_overall, need_by_role, need_by_employment):
    """按分係数によるNeed一貫性確保"""
    
    # 職種別Need按分係数計算
    role_proportions = calculate_role_proportions(long_df)
    
    # 一貫性保証Need値計算
    consistent_need_by_role = {}
    for role, proportion in role_proportions.items():
        consistent_need_by_role[role] = need_overall * proportion
    
    # 実際の職種別Need vs 按分Need の検証・補正
    return apply_proportional_consistency(
        consistent_need_by_role, 
        need_by_employment
    )
```

### Phase 2: shortage.py統合修正

#### 2.1 職種別Need計算の正確化
```python
# shortage.py修正箇所 (lines 434-479)

def enhanced_role_shortage_calculation(role_name, need_per_date_slot_df):
    """職種別不足計算の按分方式統合"""
    
    # 【修正前】統合Need値を部分抽出（不正確）
    # need_df_role.loc[time_indices, date_col] = need_per_date_slot_df.loc[time_indices, date_col]
    
    # 【修正後】職種固有Need + 按分一貫性保証
    if need_by_role_df_exists():
        # 職種固有Need値を使用
        need_df_role = load_role_specific_need(role_name)
    else:
        # 按分方式フォールバック
        total_need = need_per_date_slot_df.sum()
        role_proportion = get_role_proportion(role_name)
        need_df_role = total_need * role_proportion
        
    return calculate_shortage_with_consistency(need_df_role, actual_staff)
```

#### 2.2 三つのレベル一貫性強制メカニズム
```python
def enforce_three_level_consistency(shortage_overall, shortage_by_role, shortage_by_employment):
    """按分方式による強制的一貫性確保"""
    
    # 全体不足時間を基準とする
    base_total_shortage = shortage_overall.sum()
    
    # 按分係数による職種別・雇用形態別配分
    role_proportions = get_cached_role_proportions()
    employment_proportions = get_cached_employment_proportions()
    
    consistent_role_shortage = {
        role: base_total_shortage * prop 
        for role, prop in role_proportions.items()
    }
    
    consistent_employment_shortage = {
        emp: base_total_shortage * prop 
        for emp, prop in employment_proportions.items()
    }
    
    return ConsistentShortageResult(
        total=base_total_shortage,
        by_role=consistent_role_shortage,
        by_employment=consistent_employment_shortage
    )
```

### Phase 3: Dashboard統合表示

#### 3.1 一貫性確保された表示データ生成
```python
# dash_app.py拡張

def create_consistent_dashboard_data(scenario):
    """按分方式による一貫表示データ生成"""
    
    # 既存shortage.pyデータ読み込み
    shortage_data = load_shortage_analysis_results()
    
    # 按分方式による一貫性補正
    consistent_data = apply_proportional_consistency_correction(
        shortage_data, scenario
    )
    
    # 三つのレベル検証
    validation_result = validate_three_level_consistency(consistent_data)
    
    if not validation_result.is_consistent:
        log.warning("一貫性違反検出 - 按分補正実行")
        consistent_data = force_proportional_consistency(consistent_data)
    
    return consistent_data
```

#### 3.2 リアルタイム一貫性監視
```python
def monitor_dashboard_consistency():
    """ダッシュボード表示時の一貫性監視"""
    
    total_shortage = get_total_shortage_display()
    role_sum = sum(get_role_shortage_display().values())
    employment_sum = sum(get_employment_shortage_display().values())
    
    tolerance = 0.01  # 1分未満許容
    
    inconsistency_detected = any([
        abs(total_shortage - role_sum) > tolerance,
        abs(total_shortage - employment_sum) > tolerance,
        abs(role_sum - employment_sum) > tolerance
    ])
    
    if inconsistency_detected:
        # 自動補正またはアラート表示
        return trigger_automatic_consistency_correction()
    
    return ConsistencyStatus.VALID
```

## 🎪 実装優先順位

### 高優先度（緊急）
1. **shortage.py修正**: 職種別Need計算の正確化
2. **三つのレベル強制一貫性**: 按分方式による補正
3. **dashboard表示修正**: 一貫データ表示

### 中優先度（重要）
1. **heatmap.py拡張**: 詳細Need計算完全化
2. **一貫性監視**: リアルタイム検証機能
3. **データ検証**: parquetファイル一貫性確保

### 低優先度（改善）
1. **パフォーマンス最適化**: 按分計算効率化
2. **ログ拡張**: 一貫性診断情報
3. **テスト強化**: 統合テストスイート

## 📊 期待効果

### ✅ 即効性のある改善
- **三重カウント問題**: 完全解決
- **数値一貫性**: 数学的保証
- **既存機能**: 全面保持

### ✅ システム設計尊重
- **データフロー**: 最小限の変更
- **parquet構造**: 拡張のみ（破壊なし）
- **API互換性**: 完全維持

### ✅ 運用安定性
- **段階的実装**: リスク最小化
- **フォールバック**: 既存ロジック保持
- **検証機能**: 自動品質保証

この計画により、**按分方式の数学的正確性**と**既存システム設計の尊重**を両立した統合ソリューションを実現します。