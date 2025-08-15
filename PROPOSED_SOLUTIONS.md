# Proposed Solutions for シフト分析システムの3つの問題

## Overview
Based on the root cause analysis and comparison with backup implementations, here are the proposed solutions for each issue.

## Issue 1: Missing Dates in Heatmap

### Current Problem
```python
# dash_app.py line 3747-3751
actual_work_dates = sorted(filtered_df[filtered_df['staff_count'] > 0]['date_lbl'].unique())
if actual_work_dates:
    dynamic_heatmap_df = dynamic_heatmap_df.reindex(columns=actual_work_dates, fill_value=0)
```

### Solution: Use All Dates from Period
```python
# Restore the approach from dash_app_back.py
def generate_dynamic_heatmap(selected_role, selected_emp):
    """選択された条件で事前集計データをフィルタしピボット化"""
    
    filtered_df = aggregated_df.copy()
    
    # ... filtering logic ...
    
    # 日付順に並び替えてからピボット
    dynamic_heatmap_df = filtered_df.sort_values('date_lbl').pivot_table(
        index='time',
        columns='date_lbl',
        values='staff_count',
        aggfunc='sum',
        fill_value=0,
    )
    
    # ALL dates from the original aggregated data should be preserved
    all_dates_from_aggregated_data = sorted(aggregated_df['date_lbl'].unique())
    
    # Reindex to include ALL dates, filling missing ones with 0
    dynamic_heatmap_df = dynamic_heatmap_df.reindex(columns=all_dates_from_aggregated_data, fill_value=0)
    
    # Continue with time label reindexing...
```

### Alternative: Modify Rest Exclusion Filter
```python
# utils.py - Add holiday detection logic
def apply_rest_exclusion_filter(df: pd.DataFrame, context: str = "unknown") -> pd.DataFrame:
    """
    データパイプライン全体で使用する統一的な休暇除外フィルター
    """
    if df.empty:
        return df
    
    # Only filter out actual holidays, not empty days
    if 'holiday_type' in df.columns:
        # Use explicit holiday marking
        df = df[df['holiday_type'] == '通常勤務']
    elif 'staff' in df.columns:
        # Only filter based on staff patterns, not staff_count
        # This preserves days with 0 scheduled staff
        rest_patterns = ['×', 'X', 'x', '休', '休み', '休暇', ...]
        for pattern in rest_patterns:
            df = df[~df['staff'].str.contains(pattern, na=False, regex=False)]
    
    # DO NOT filter based on staff_count <= 0
    # This preserves legitimate empty days
    
    return df
```

## Issue 2: 'df_shortage_role_filtered' is not defined

### Current Problem
```python
# dash_app.py line 1682-1720
df_shortage_role_filtered = {}  # Defined inside conditional
if not df_shortage_role.empty:
    # ... populate df_shortage_role_filtered ...

# Used outside conditional
if df_shortage_role_filtered:  # NameError if condition was False
    # ... use df_shortage_role_filtered ...
```

### Solution 1: Always Initialize Variables
```python
def create_shortage_analysis_content():
    # Always initialize at the beginning
    df_shortage_role_filtered = {}
    df_shortage_role_excess = {}
    
    # Load data
    df_shortage_role = data_get('shortage_role_summary', pd.DataFrame())
    
    # Process data if available
    if not df_shortage_role.empty:
        # Filter and populate dictionaries
        role_only_df = df_shortage_role[
            (~df_shortage_role['role'].isin(['全体', '合計', '総計'])) &
            (~df_shortage_role['role'].str.startswith('emp_', na=False))
        ]
        
        for _, row in role_only_df.iterrows():
            role = row['role']
            lack_h = row.get('lack_h', 0)
            excess_h = row.get('excess_h', 0)
            
            if lack_h > 0:
                df_shortage_role_filtered[role] = lack_h
            if excess_h > 0:
                df_shortage_role_excess[role] = excess_h
    
    # Safe to use df_shortage_role_filtered here
    if df_shortage_role_filtered:
        # Create visualizations
        ...
```

### Solution 2: Use DataFrame Directly (from backup)
```python
def create_shortage_analysis_content():
    df_shortage_role = data_get('shortage_role_summary', pd.DataFrame())
    
    if df_shortage_role.empty:
        return html.P("職種別データが読み込まれていません。")
    
    # Filter once
    role_only_df = df_shortage_role[
        (~df_shortage_role['role'].isin(['全体', '合計', '総計'])) &
        (~df_shortage_role['role'].str.startswith('emp_', na=False))
    ]
    
    # Work with filtered DataFrame directly
    if not role_only_df.empty:
        # Create bar chart directly from DataFrame
        fig_role_combined = go.Figure()
        
        # Add traces for lack and excess
        fig_role_combined.add_trace(go.Bar(
            x=role_only_df['role'],
            y=role_only_df['lack_h'],
            name='不足時間',
            marker_color='red',
            opacity=0.7
        ))
        
        if 'excess_h' in role_only_df.columns:
            fig_role_combined.add_trace(go.Bar(
                x=role_only_df['role'],
                y=role_only_df['excess_h'],
                name='過剰時間',
                marker_color='blue',
                opacity=0.7
            ))
        
        # Update layout and display
        ...
```

## Issue 3: Single Color Display for Specific Roles

### Current Problem
When a role has uniform values (all 0s or minimal variation), the color scale shows a single color.

### Solution 1: Set Minimum Color Range
```python
def generate_heatmap_figure(df_heat: pd.DataFrame, title: str) -> go.Figure:
    """指定されたデータフレームからヒートマップグラフを生成する"""
    
    # ... existing code ...
    
    # Calculate min and max values for color scale
    min_val = display_df_renamed.min().min()
    max_val = display_df_renamed.max().max()
    
    # Ensure a minimum range for color scale
    if max_val - min_val < 1:  # If range is too small
        # Set a minimum range to ensure gradient visibility
        color_range = [min_val, max(min_val + 1, max_val)]
    else:
        color_range = [min_val, max_val]
    
    fig = px.imshow(
        display_df_renamed,
        aspect='auto',
        color_continuous_scale=px.colors.sequential.Viridis,
        title=title,
        labels={'x': '日付', 'y': '時間', 'color': '人数'},
        text_auto=True,
        zmin=color_range[0],  # Set explicit min
        zmax=color_range[1],  # Set explicit max
    )
    
    # ... rest of the function ...
```

### Solution 2: Use Different Color Scale for Low-Variation Data
```python
def generate_heatmap_figure(df_heat: pd.DataFrame, title: str) -> go.Figure:
    # Calculate data variance
    data_variance = display_df_renamed.values.var()
    
    # Choose color scale based on variance
    if data_variance < 0.1:  # Very low variation
        # Use a discrete color scale for better visibility
        color_scale = [[0, 'white'], [0.5, 'lightblue'], [1, 'darkblue']]
    else:
        # Use standard continuous scale
        color_scale = px.colors.sequential.Viridis
    
    fig = px.imshow(
        display_df_renamed,
        aspect='auto',
        color_continuous_scale=color_scale,
        title=title,
        labels={'x': '日付', 'y': '時間', 'color': '人数'},
        text_auto=True
    )
```

## Implementation Priority

1. **High Priority**: Fix `df_shortage_role_filtered` error (Issue 2)
   - This causes runtime errors and blocks functionality
   - Simple fix with variable initialization

2. **Medium Priority**: Restore missing dates in heatmap (Issue 1)
   - Affects data completeness and analysis accuracy
   - Requires careful modification of filtering logic

3. **Low Priority**: Improve color scale for uniform data (Issue 3)
   - Cosmetic issue that doesn't block functionality
   - Can be addressed after core issues are resolved

## Testing Recommendations

1. Test with data containing:
   - Mix of holidays and empty working days
   - Roles with no shortage data
   - Roles with uniform staffing patterns

2. Verify:
   - All dates in the period appear in heatmaps
   - No NameError in shortage analysis tab
   - Color gradients visible for all role heatmaps

3. Check edge cases:
   - Empty data files
   - Single-day data
   - All-zero staffing patterns

---
Created: 2025-07-23
Author: Claude Code