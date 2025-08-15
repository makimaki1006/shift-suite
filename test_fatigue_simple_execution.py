#!/usr/bin/env python3
"""
Simple fatigue analysis test without unicode characters
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta

def create_test_data():
    """Create test data"""
    print("Creating test data...")
    
    start_date = datetime(2024, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(30)]
    
    staff_names = ["Staff_A", "Staff_B", "Staff_C"]
    
    test_data = []
    for staff in staff_names:
        for date in dates:
            # Day shift
            test_data.append({
                "staff": staff,
                "ds": datetime.combine(date, time(9, 0)),
                "code": "day_shift",
                "parsed_slots_count": 8,
                "start_time": "09:00"
            })
            
            # Random night shift
            if np.random.random() < 0.3:
                test_data.append({
                    "staff": staff,
                    "ds": datetime.combine(date, time(22, 0)),
                    "code": "night_shift",
                    "parsed_slots_count": 8,
                    "start_time": "22:00"
                })
    
    df = pd.DataFrame(test_data)
    print(f"Test data created: {len(df)} rows, {len(staff_names)} staff")
    return df

def test_fatigue_analysis():
    """Test fatigue analysis"""
    print("Testing fatigue analysis...")
    
    try:
        from shift_suite.tasks.fatigue import train_fatigue
        print("SUCCESS: train_fatigue import")
        
        test_df = create_test_data()
        
        output_dir = Path("temp_fatigue_test")
        output_dir.mkdir(exist_ok=True)
        print(f"Output dir: {output_dir}")
        
        print("Running fatigue analysis...")
        
        weights = {
            "start_var": 1.0,
            "diversity": 1.0,
            "worktime_var": 1.0,
            "short_rest": 1.0,
            "consecutive": 1.0,
            "night_ratio": 1.0,
        }
        
        result = train_fatigue(
            test_df, 
            output_dir, 
            weights=weights, 
            slot_minutes=30
        )
        
        print("SUCCESS: fatigue analysis completed")
        
        parquet_file = output_dir / "fatigue_score.parquet"
        xlsx_file = output_dir / "fatigue_score.xlsx"
        
        if parquet_file.exists():
            print(f"SUCCESS: parquet file created: {parquet_file}")
            df_result = pd.read_parquet(parquet_file)
            print(f"Result data: {len(df_result)} rows, {len(df_result.columns)} columns")
            print("Columns:", list(df_result.columns))
            print("First 3 rows:")
            print(df_result.head(3))
        else:
            print("ERROR: parquet file not created")
            
        if xlsx_file.exists():
            print(f"SUCCESS: Excel file created: {xlsx_file}")
        else:
            print("ERROR: Excel file not created")
            
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Comprehensive fatigue analysis execution test")
    print("=" * 50)
    
    success = test_fatigue_analysis()
    
    print("\n" + "=" * 50)
    if success:
        print("SUCCESS: Fatigue analysis test passed!")
        print("\nChecklist:")
        print("1. Check temp_fatigue_test folder for generated files")
        print("2. Verify fatigue_score.parquet/xlsx content")
        print("3. Confirm 6 fatigue factors are calculated")
    else:
        print("WARNING: Fatigue analysis test failed")
        print("Similar errors may occur in app.py execution")
    
    return success

if __name__ == "__main__":
    success = main()
    print(f"\nTest completed: {'SUCCESS' if success else 'FAILED'}")