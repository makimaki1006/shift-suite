#!/usr/bin/env python3
"""
Test fatigue analysis through app.py workflow
"""
import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
from pathlib import Path

def create_simple_test_excel():
    """Create a simple test Excel file for app.py"""
    print("Creating test Excel file...")
    
    # Create test data
    start_date = datetime(2024, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(30)]
    
    staff_names = ["山田太郎", "佐藤花子", "田中一郎"]
    
    test_data = []
    for date in dates:
        for staff in staff_names:
            # Day shift
            test_data.append({
                "日付": date.strftime("%Y/%m/%d"),
                "スタッフ": staff,
                "勤務時間_09:00": "日勤" if np.random.random() > 0.2 else "",
                "勤務時間_10:00": "日勤" if np.random.random() > 0.2 else "",
                "勤務時間_11:00": "日勤" if np.random.random() > 0.2 else "",
                "勤務時間_12:00": "日勤" if np.random.random() > 0.2 else "",
                "勤務時間_13:00": "日勤" if np.random.random() > 0.2 else "",
                "勤務時間_14:00": "日勤" if np.random.random() > 0.2 else "",
                "勤務時間_15:00": "日勤" if np.random.random() > 0.2 else "",
                "勤務時間_16:00": "日勤" if np.random.random() > 0.2 else "",
                "勤務時間_22:00": "夜勤" if np.random.random() > 0.7 else "",
                "勤務時間_23:00": "夜勤" if np.random.random() > 0.7 else "",
                "職種": "介護",
                "雇用形態": "正社員"
            })
    
    df = pd.DataFrame(test_data)
    output_file = "test_fatigue_excel.xlsx"
    df.to_excel(output_file, index=False)
    print(f"Test Excel file created: {output_file}")
    return output_file

def check_app_configuration():
    """Check if app.py is configured correctly for fatigue analysis"""
    print("Checking app.py configuration...")
    
    try:
        # Check if fatigue module can be imported
        from shift_suite.tasks.fatigue import train_fatigue
        print("SUCCESS: Fatigue module import")
        
        # Check if app.py exists and has correct configuration
        app_path = Path("app.py")
        if app_path.exists():
            print("SUCCESS: app.py exists")
            
            with open(app_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if '"Fatigue"' in content:
                print("SUCCESS: Fatigue option found in app.py")
            else:
                print("WARNING: Fatigue option not found in app.py")
                
            if 'train_fatigue' in content:
                print("SUCCESS: train_fatigue function call found in app.py")
            else:
                print("WARNING: train_fatigue function call not found in app.py")
                
        else:
            print("ERROR: app.py not found")
            
        return True
        
    except Exception as e:
        print(f"ERROR: Configuration check failed: {e}")
        return False

def main():
    print("Testing fatigue analysis through app.py workflow")
    print("=" * 50)
    
    # Step 1: Check configuration
    config_ok = check_app_configuration()
    
    if config_ok:
        # Step 2: Create test file
        test_file = create_simple_test_excel()
        
        print(f"\nTest file created: {test_file}")
        print("\nNext steps:")
        print("1. Start app.py: streamlit run app.py")
        print("2. Upload the test_fatigue_excel.xlsx file")
        print("3. Ensure 'Fatigue' is selected in Extra modules")
        print("4. Run analysis and check for fatigue_score.parquet/xlsx files")
        print("5. Check dashboard fatigue tab for data display")
        
        print("\nExpected result:")
        print("- Fatigue analysis should execute successfully")
        print("- fatigue_score.parquet/xlsx files should be generated")
        print("- Dashboard should display fatigue data without errors")
        
    else:
        print("\nConfiguration issues detected. Please check:")
        print("1. Fatigue module imports")
        print("2. app.py configuration")
        print("3. Available analysis options")

if __name__ == "__main__":
    main()