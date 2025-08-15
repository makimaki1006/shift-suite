#!/usr/bin/env python3
"""
Debug script to understand the rest exclusion issue
"""

import pandas as pd
import logging
import sys
from pathlib import Path

# Add project path
sys.path.insert(0, '.')

from shift_suite.tasks.utils import apply_rest_exclusion_filter

# Setup logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def analyze_rest_exclusion_issue():
    """Analyze the rest exclusion filter issue"""
    
    print("=== REST EXCLUSION DEBUGGING ===")
    
    # 1. Simulate the data flow with actual structure from pre_aggregated_data
    print("\n1. Testing with pre_aggregated_data structure...")
    
    # Create test data that matches the pre_aggregated_data structure
    # This simulates data after processing by io_excel.py and aggregation
    test_aggregated_data = pd.DataFrame({
        'ds': pd.to_datetime(['2025-06-01 00:00:00', '2025-06-01 06:30:00', '2025-06-01 07:00:00', 
                             '2025-06-01 00:00:00', '2025-06-01 00:00:00']),
        'role': ['介護', '介護', '介護', '看護師', '介護'],
        'employment': ['正社員', 'パート', 'パート', '正社員', 'パート'],
        'date_lbl': ['2025-06-01', '2025-06-01', '2025-06-01', '2025-06-01', '2025-06-01'],
        'time': ['00:00', '06:30', '07:00', '00:00', '00:00'],
        'staff_count': [0, 2, 3, 0, 1]  # 0 indicates rest periods
    })
    
    print("Test aggregated data before filtering:")
    print(test_aggregated_data)
    
    # Apply the rest exclusion filter
    filtered_data = apply_rest_exclusion_filter(test_aggregated_data, "test_aggregated", for_display=False, exclude_leave_records=False)
    
    print("\nAfter applying rest exclusion filter:")
    print(filtered_data)
    
    # 2. Test with long_df structure (raw shift data)
    print("\n\n2. Testing with long_df structure...")
    
    test_long_data = pd.DataFrame({
        'ds': pd.to_datetime(['2025-06-01 00:00:00', '2025-06-01 06:30:00', '2025-06-01 07:00:00',
                             '2025-06-01 00:00:00', '2025-06-01 00:00:00']),
        'staff': ['田中太郎', '佐藤花子', '山田次郎', '×', '休'],
        'role': ['介護', '介護', '看護師', '介護', '介護'],
        'employment': ['正社員', 'パート', '正社員', 'パート', 'パート'],
        'code': ['L', '2F', '3F', '×', '休'],
        'parsed_slots_count': [8, 16, 20, 0, 0],
        'holiday_type': ['通常勤務', '通常勤務', '通常勤務', '希望休', '施設休']
    })
    
    print("Test long data before filtering:")
    print(test_long_data)
    
    # Apply the rest exclusion filter
    filtered_long_data = apply_rest_exclusion_filter(test_long_data, "test_long_df", for_display=False, exclude_leave_records=False)
    
    print("\nAfter applying rest exclusion filter:")
    print(filtered_long_data)
    
    # 3. Test the heatmap generation process
    print("\n\n3. Testing heatmap data generation...")
    
    # Simulate the aggregation process that creates heatmap data
    # This is what happens in the dashboard when creating heatmaps from pre_aggregated_data
    
    # Start with filtered aggregated data
    heatmap_source = test_aggregated_data.copy()
    
    # Apply rest exclusion (this is where the issue might be)
    heatmap_source_filtered = apply_rest_exclusion_filter(heatmap_source, "heatmap_generation", for_display=False, exclude_leave_records=False)
    
    # Create pivot table (like heatmap generation)
    if not heatmap_source_filtered.empty:
        pivot_data = heatmap_source_filtered.pivot_table(
            index='time',
            columns='date_lbl', 
            values='staff_count',
            aggfunc='sum',
            fill_value=0
        )
        
        print("Heatmap pivot data:")
        print(pivot_data)
    else:
        print("No data remaining after filtering for heatmap")
    
    # 4. Check what happens with different filter approaches
    print("\n\n4. Testing different filtering approaches...")
    
    # Current filter approach (from utils.py)
    current_result = apply_rest_exclusion_filter(test_aggregated_data.copy(), "current_approach", for_display=False, exclude_leave_records=False)
    print(f"Current filter result: {len(current_result)} records remaining")
    
    # Alternative approach: only filter non-zero staff_count
    alt_filtered = test_aggregated_data[test_aggregated_data['staff_count'] > 0]
    print(f"Alternative filter (staff_count > 0): {len(alt_filtered)} records remaining")
    print("Alternative filter result:")
    print(alt_filtered)
    
    # 5. Real data test
    print("\n\n5. Testing with actual pre_aggregated data...")
    
    pre_agg_file = Path("temp_pre_aggregated.parquet")
    if pre_agg_file.exists():
        real_data = pd.read_parquet(pre_agg_file)
        print(f"Real pre_aggregated data shape: {real_data.shape}")
        
        # Count zero staff_count records
        zero_staff_before = (real_data['staff_count'] == 0).sum()
        print(f"Zero staff_count records before filter: {zero_staff_before}")
        
        # Apply filter
        real_filtered = apply_rest_exclusion_filter(real_data, "real_data_test", for_display=False, exclude_leave_records=False)
        
        zero_staff_after = (real_filtered['staff_count'] == 0).sum()
        print(f"Zero staff_count records after filter: {zero_staff_after}")
        
        # Check what remains
        staff_count_dist = real_filtered['staff_count'].value_counts().head()
        print(f"Staff count distribution after filtering:\n{staff_count_dist}")
        
    print("\n=== DEBUGGING COMPLETE ===")

if __name__ == "__main__":
    analyze_rest_exclusion_issue()