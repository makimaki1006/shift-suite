#!/usr/bin/env python3
"""
Investigation script to analyze rest day exclusion issue
Examines the data flow from Excel to dashboard to identify why "×" symbols are not being excluded
"""

import sys
from pathlib import Path
import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)

# Add project path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Main investigation routine"""
    
    log.info("=== REST DAY EXCLUSION INVESTIGATION ===")
    
    # 1. Examine pre_aggregated_data from the extracted analysis results
    log.info("\n1. Examining pre_aggregated_data.parquet...")
    
    try:
        # Load the pre_aggregated data
        pre_agg_path = Path("temp_pre_aggregated.parquet")
        if pre_agg_path.exists():
            df_pre_agg = pd.read_parquet(pre_agg_path)
            log.info(f"Pre-aggregated data shape: {df_pre_agg.shape}")
            log.info(f"Columns: {df_pre_agg.columns.tolist()}")
            
            # Check for zero staff_count entries
            zero_staff = df_pre_agg[df_pre_agg['staff_count'] == 0]
            log.info(f"Zero staff_count records: {len(zero_staff)}")
            
            # Show sample of zero staff_count data
            if not zero_staff.empty:
                log.info("Sample zero staff_count records:")
                print(zero_staff.head(10))
                
            # Check staff_count distribution
            staff_count_dist = df_pre_agg['staff_count'].value_counts().head(10)
            log.info(f"Staff count distribution (top 10):\n{staff_count_dist}")
            
        else:
            log.error(f"Pre-aggregated data file not found: {pre_agg_path}")
            
    except Exception as e:
        log.error(f"Error examining pre_aggregated_data: {e}")
    
    # 2. Examine heatmap data
    log.info("\n2. Examining heatmap data...")
    
    try:
        # Load the heatmap data
        heat_all_path = Path("temp_heat_all.parquet")
        if heat_all_path.exists():
            df_heat = pd.read_parquet(heat_all_path)
            log.info(f"Heatmap data shape: {df_heat.shape}")
            
            # Check for zero values in the heatmap
            date_columns = [col for col in df_heat.columns if col.startswith('2025-')]
            if date_columns:
                sample_date_col = date_columns[0]
                zero_time_slots = df_heat[df_heat[sample_date_col] == 0]
                non_zero_time_slots = df_heat[df_heat[sample_date_col] > 0]
                
                log.info(f"Time slots with 0 staff on {sample_date_col}: {len(zero_time_slots)}")
                log.info(f"Time slots with >0 staff on {sample_date_col}: {len(non_zero_time_slots)}")
                
                log.info(f"Non-zero time slots on {sample_date_col}:")
                print(non_zero_time_slots[sample_date_col])
                
        else:
            log.error(f"Heatmap data file not found: {heat_all_path}")
            
    except Exception as e:
        log.error(f"Error examining heatmap data: {e}")
    
    # 3. Test the rest exclusion filter
    log.info("\n3. Testing rest exclusion filter...")
    
    try:
        from shift_suite.tasks.utils import apply_rest_exclusion_filter
        
        # Create test data with various rest patterns
        test_data = pd.DataFrame({
            'staff': ['田中太郎', '×', 'X', '佐藤花子', '休', '山田次郎', ''],
            'role': ['介護', '介護', '看護師', '介護', '介護', '看護師', '介護'],
            'staff_count': [2, 0, 0, 1, 0, 3, 0],
            'parsed_slots_count': [8, 0, 0, 4, 0, 8, 0],
            'holiday_type': ['通常勤務', '希望休', '希望休', '通常勤務', '施設休', '通常勤務', '通常勤務']
        })
        
        log.info(f"Test data before filtering:\n{test_data}")
        
        filtered_data = apply_rest_exclusion_filter(test_data, "test")
        
        log.info(f"Test data after filtering:\n{filtered_data}")
        
        # Check which records were excluded
        excluded_indices = set(test_data.index) - set(filtered_data.index)
        log.info(f"Excluded record indices: {excluded_indices}")
        
        if excluded_indices:
            excluded_records = test_data.loc[list(excluded_indices)]
            log.info(f"Excluded records:\n{excluded_records}")
        
    except Exception as e:
        log.error(f"Error testing rest exclusion filter: {e}")
    
    # 4. Examine actual Excel files to see how "×" symbols are stored
    log.info("\n4. Examining Excel file contents...")
    
    try:
        excel_files = [
            "シフトデータ_デイ_テスト用データ_休日精緻.xlsx",  
            "シフトデータ_ショート_テスト用データ.xlsx"
        ]
        
        for excel_file in excel_files:
            if Path(excel_file).exists():
                log.info(f"\nExamining {excel_file}...")
                
                # Load the first sheet to see column structure
                try:
                    df_sheet = pd.read_excel(excel_file, sheet_name=0, header=2)
                    log.info(f"Sheet columns: {df_sheet.columns.tolist()}")
                    
                    # Look for staff column
                    staff_col = None
                    for col in df_sheet.columns:
                        if '氏名' in str(col) or '名前' in str(col) or 'staff' in str(col).lower():
                            staff_col = col
                            break
                    
                    if staff_col:
                        log.info(f"Staff column found: {staff_col}")
                        staff_values = df_sheet[staff_col].dropna().unique()[:20]  # First 20 unique values
                        log.info(f"Staff values sample: {staff_values}")
                        
                        # Check for rest symbols in staff names
                        rest_symbols = ['×', 'X', 'x', '休', '欠', 'OFF']
                        found_symbols = []
                        for symbol in rest_symbols:
                            if symbol in staff_values:
                                found_symbols.append(symbol)
                        
                        if found_symbols:
                            log.info(f"Found rest symbols in staff column: {found_symbols}")
                        else:
                            log.info("No rest symbols found in staff column")
                    else:
                        log.info("Staff column not found")
                        
                except Exception as e:
                    log.error(f"Error reading {excel_file}: {e}")
            else:
                log.info(f"Excel file not found: {excel_file}")
    
    except Exception as e:
        log.error(f"Error examining Excel files: {e}")
    
    log.info("\n=== INVESTIGATION COMPLETE ===")

if __name__ == "__main__":
    main()