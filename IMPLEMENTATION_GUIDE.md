# Implementation Guide: Fix Three Issues in シフト分析システム

## Quick Fix Priority Order

### 1. IMMEDIATE FIX - Prevent Runtime Error (5 minutes)
Fix the `df_shortage_role_filtered` undefined error in `dash_app.py`:

```python
# Around line 1680 in dash_app.py
# Change FROM:
        # 職種別データのフィルタリングと処理
        df_shortage_role_filtered = {}  # Line 1682 - inside conditional
        df_shortage_role_excess = {}
        
        if not df_shortage_role.empty:  # This condition might be False
            # ... processing ...

# Change TO:
        # 職種別データのフィルタリングと処理
        # Always initialize these dictionaries
        df_shortage_role_filtered = {}
        df_shortage_role_excess = {}
        
        # Load and process data
        if not df_shortage_role.empty:
            # ... existing processing code ...
```

### 2. CRITICAL FIX - Restore Missing Dates in Heatmap (15 minutes)
Fix the overly aggressive date filtering in `dash_app.py`:

```python
# Around line 3745-3752 in generate_dynamic_heatmap function
# Change FROM:
        # 🎯 重要修正: 実際に勤務データがある日付のみを取得（休日除外）
        # staff_count > 0 の日付のみを取得し、休日の0埋めを防ぐ
        actual_work_dates = sorted(filtered_df[filtered_df['staff_count'] > 0]['date_lbl'].unique())
        
        # 実際の勤務日のみでreindex（休日は列として作らない）
        if actual_work_dates:
            dynamic_heatmap_df = dynamic_heatmap_df.reindex(columns=actual_work_dates, fill_value=0)

# Change TO (restore backup version logic):
        # Get ALL dates from the period, not just those with staff > 0
        all_dates_from_aggregated_data = sorted(aggregated_df['date_lbl'].unique())
        
        # Reindex to include ALL dates, filling missing ones with 0
        dynamic_heatmap_df = dynamic_heatmap_df.reindex(columns=all_dates_from_aggregated_data, fill_value=0)
```

### 3. IMPORTANT FIX - Improve Rest Exclusion Filter (20 minutes)
Modify `shift_suite/tasks/utils.py` to preserve empty working days:

```python
# Around line 119-124 in apply_rest_exclusion_filter
# Change FROM:
    # 3. staff_count による除外（事前集計データ用）
    if 'staff_count' in df.columns:
        zero_staff_mask = df['staff_count'] <= 0
        zero_staff_count = zero_staff_mask.sum()
        if zero_staff_count > 0:
            df = df[~zero_staff_mask]
            analysis_logger.info(f"[RestExclusion] {context}: 0人数除外: {zero_staff_count}件")

# Change TO:
    # 3. staff_count による除外は行わない
    # 理由: staff_count = 0 は休日ではなく、スタッフ未配置の営業日の可能性がある
    # holiday_type フィールドで判定するのがより正確
    if 'staff_count' in df.columns:
        # ログのみ出力し、除外は行わない
        zero_staff_count = (df['staff_count'] <= 0).sum()
        if zero_staff_count > 0:
            analysis_logger.info(f"[RestExclusion] {context}: 0人数検出: {zero_staff_count}件 (除外せず)")
```

### 4. ENHANCEMENT - Better Color Scale for Uniform Data (10 minutes)
Fix single-color display in `dash_app.py` generate_heatmap_figure:

```python
# Around line 1105 in generate_heatmap_figure
# Add before px.imshow call:
    # Calculate value range for better color scaling
    min_val = display_df_renamed.min().min()
    max_val = display_df_renamed.max().max()
    
    # Ensure minimum color range for visibility
    if max_val - min_val < 0.1:  # Very small range
        # Force a minimum range to show gradients
        zmin = min_val
        zmax = max(min_val + 1, max_val + 0.1)
    else:
        zmin = min_val
        zmax = max_val

# Modify px.imshow call:
    fig = px.imshow(
        display_df_renamed,
        aspect='auto',
        color_continuous_scale=px.colors.sequential.Viridis,
        title=title,
        labels={'x': '日付', 'y': '時間', 'color': '人数'},
        text_auto=True,
        zmin=zmin,  # Add explicit min
        zmax=zmax,  # Add explicit max
    )
```

## Root Cause Summary

The system's `apply_rest_exclusion_filter` cannot distinguish between:
- **Holidays/Leave** (marked with holiday_type != "通常勤務") - Should be filtered
- **Empty Working Days** (staff_count = 0 but holiday_type = "通常勤務") - Should be preserved

The current implementation removes BOTH, causing:
1. Missing dates in visualizations
2. Empty datasets leading to undefined variables
3. Uniform data causing single-color displays

## Testing After Implementation

1. **Test Data Requirements**:
   - Include days with no scheduled staff but are working days
   - Include actual holidays
   - Include roles with minimal staffing

2. **Verification Steps**:
   - ✓ No NameError in shortage analysis tab
   - ✓ All dates in period appear in heatmaps (with 0s where appropriate)
   - ✓ Color gradients visible even for low-variation data
   - ✓ Actual holidays still excluded properly

3. **Check Logs**:
   ```
   grep "RestExclusion" shift_suite.log
   ```
   Should show:
   - holiday_type-based exclusions (correct)
   - 0人数検出 messages without exclusion (correct)
   - No excessive data removal

## Long-term Recommendation

Consider adding explicit "is_holiday" boolean field during data ingestion to make the distinction clearer:
- True = actual holiday/leave (exclude from analysis)
- False = working day, even if no staff scheduled (include with 0 values)

---
Implementation Time: ~50 minutes total
Risk Level: Low (changes are isolated and reversible)
Created: 2025-07-23