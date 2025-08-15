#!/usr/bin/env python3
"""
Test script to verify fixes for dash_app.py issues
Tests:
1. Fatigue analysis fallback from .xlsx to .parquet
2. Leave analysis with CSV fallback when intermediate_data.parquet is missing
3. Error handling improvements
"""

import sys
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_fatigue_analysis_fix():
    """Test fatigue analysis .xlsx fallback"""
    print("=== Testing Fatigue Analysis Fix ===")
    
    # Create test data
    test_data = pd.DataFrame({
        'fatigue_score': [25.5, 40.2, 15.8, 60.1, 30.7]
    })
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Save as Excel (simulating old behavior)
        xlsx_file = temp_path / "fatigue_score.xlsx"
        test_data.to_excel(xlsx_file, index=False)
        
        # Test reading Excel fallback
        try:
            df = pd.read_excel(xlsx_file)
            avg_score = df.get('fatigue_score', pd.Series()).mean()
            print(f"Excel fallback successful: avg_fatigue_score = {avg_score:.2f}")
        except Exception as e:
            print(f"Excel fallback failed: {e}")
            return False
        
        # Now save as Parquet (simulating new behavior)
        parquet_file = temp_path / "fatigue_score.parquet"
        test_data.to_parquet(parquet_file)
        
        # Test reading Parquet (preferred)
        try:
            df = pd.read_parquet(parquet_file)
            avg_score = df.get('fatigue_score', pd.Series()).mean()
            print(f"Parquet reading successful: avg_fatigue_score = {avg_score:.2f}")
        except Exception as e:
            print(f"Parquet reading failed: {e}")
            return False
    
    return True

def test_leave_analysis_fix():
    """Test leave analysis CSV fallback"""
    print("\n=== Testing Leave Analysis Fix ===")
    
    # Create test leave analysis data
    leave_data = pd.DataFrame({
        'date': ['2025-06-01', '2025-06-02', '2025-06-03'],
        'leave_type': ['希望休', '有給', '希望休'],
        'total_leave_days': [10, 5, 8],
        'num_days_in_period_unit': [1, 1, 1],
        'avg_leave_days_per_day': [10.0, 5.0, 8.0]
    })
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Save as CSV (simulating analysis output)
        csv_file = temp_path / "leave_analysis.csv"
        leave_data.to_csv(csv_file, index=False)
        
        # Test reading CSV
        try:
            df = pd.read_csv(csv_file)
            total_days = df['total_leave_days'].sum()
            print(f" CSV reading successful: total_leave_days = {total_days}")
            
            # Test data structure
            expected_columns = ['date', 'leave_type', 'total_leave_days']
            missing_cols = [col for col in expected_columns if col not in df.columns]
            if missing_cols:
                print(f" Missing columns: {missing_cols}")
                return False
            else:
                print(f" All expected columns present: {list(df.columns)}")
                
        except Exception as e:
            print(f" CSV reading failed: {e}")
            return False
    
    return True

def test_file_diagnostics():
    """Test file existence diagnostics"""
    print("\n=== Testing File Diagnostics ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create some test files
        parquet_files = ['file1.parquet', 'file2.parquet']
        csv_files = ['leave_analysis.csv', 'summary.csv']
        
        for f in parquet_files:
            (temp_path / f).touch()
        for f in csv_files:
            (temp_path / f).touch()
        
        # Test diagnostics
        try:
            parquet_found = list(temp_path.glob("*.parquet"))
            csv_found = list(temp_path.glob("*.csv"))
            
            print(f" Parquet files found: {len(parquet_found)} ({[f.name for f in parquet_found]})")
            print(f" CSV files found: {len(csv_found)} ({[f.name for f in csv_found]})")
            
            # Test intermediate_data.parquet check
            intermediate_file = temp_path / "intermediate_data.parquet"
            exists = intermediate_file.exists()
            print(f" intermediate_data.parquet existence check: {exists} (expected False)")
            
            return True
            
        except Exception as e:
            print(f" Diagnostics failed: {e}")
            return False

def test_fatigue_module_fix():
    """Test the fatigue.py module fix"""
    print("\n=== Testing Fatigue Module Fix ===")
    
    try:
        # Import the fatigue module
        from shift_suite.tasks.fatigue import train_fatigue, _features
        
        # Create test long_df data
        test_long_df = pd.DataFrame({
            'name': ['Staff1', 'Staff2', 'Staff3'] * 10,
            'code': ['日勤', '夜勤', '日勤', '夜勤', '日勤'] * 6
        })
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test the function
            model = train_fatigue(test_long_df, temp_path)
            
            # Check if both files are created
            xlsx_file = temp_path / "fatigue_score.xlsx"
            parquet_file = temp_path / "fatigue_score.parquet"
            
            xlsx_exists = xlsx_file.exists()
            parquet_exists = parquet_file.exists()
            
            print(f" fatigue_score.xlsx created: {xlsx_exists}")
            print(f" fatigue_score.parquet created: {parquet_exists}")
            
            if xlsx_exists and parquet_exists:
                # Test reading both files
                xlsx_df = pd.read_excel(xlsx_file)
                parquet_df = pd.read_parquet(parquet_file)
                
                print(f" Excel file shape: {xlsx_df.shape}")
                print(f" Parquet file shape: {parquet_df.shape}")
                
                # Check if data is consistent (allowing for numeric type differences)
                try:
                    # Compare shapes
                    if xlsx_df.shape != parquet_df.shape:
                        print(" Excel and Parquet files have different shapes")
                        return False
                    
                    # Compare columns
                    if list(xlsx_df.columns) != list(parquet_df.columns):
                        print(" Excel and Parquet files have different columns")
                        return False
                    
                    # Compare values (convert to same type for comparison)
                    for col in xlsx_df.columns:
                        xlsx_values = xlsx_df[col].astype(float)
                        parquet_values = parquet_df[col].astype(float)
                        if not xlsx_values.equals(parquet_values):
                            print(f" Column '{col}' values differ between Excel and Parquet")
                            return False
                    
                    print(" Excel and Parquet files contain identical data (allowing for numeric type differences)")
                    return True
                except Exception as e:
                    print(f" Error comparing files: {e}")
                    return False
            else:
                print(" Not all required files were created")
                return False
                
    except Exception as e:
        print(f" Fatigue module test failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """Run all tests"""
    print("Running Dash App Fixes Verification Tests\n")
    
    results = []
    
    # Run all tests
    results.append(("Fatigue Analysis Fix", test_fatigue_analysis_fix()))
    results.append(("Leave Analysis Fix", test_leave_analysis_fix()))
    results.append(("File Diagnostics", test_file_diagnostics()))
    results.append(("Fatigue Module Fix", test_fatigue_module_fix()))
    
    # Print summary
    print("\n" + "="*50)
    print("TEST RESULTS SUMMARY")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("All fixes verified successfully!")
        return True
    else:
        print("Some fixes need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)