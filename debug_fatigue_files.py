#!/usr/bin/env python3
"""
Debug script to check fatigue file differences
"""
import sys
import pandas as pd
from pathlib import Path
import tempfile

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_fatigue_files():
    """Debug fatigue files to see differences"""
    print("=== Debugging Fatigue Files ===")
    
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
            
            if xlsx_file.exists() and parquet_file.exists():
                # Test reading both files
                xlsx_df = pd.read_excel(xlsx_file)
                parquet_df = pd.read_parquet(parquet_file)
                
                print(f"Excel file shape: {xlsx_df.shape}")
                print(f"Parquet file shape: {parquet_df.shape}")
                
                print("\nExcel file columns:", list(xlsx_df.columns))
                print("Parquet file columns:", list(parquet_df.columns))
                
                print("\nExcel file data types:")
                print(xlsx_df.dtypes)
                print("\nParquet file data types:")
                print(parquet_df.dtypes)
                
                print("\nExcel file head:")
                print(xlsx_df.head())
                print("\nParquet file head:")
                print(parquet_df.head())
                
                # Check if data is consistent
                if xlsx_df.equals(parquet_df):
                    print("✓ Excel and Parquet files contain identical data")
                    return True
                else:
                    print("✗ Excel and Parquet files contain different data")
                    
                    # More detailed comparison
                    if list(xlsx_df.columns) == list(parquet_df.columns):
                        print("✓ Columns are the same")
                        
                        if xlsx_df.shape == parquet_df.shape:
                            print("✓ Shapes are the same")
                            
                            # Compare values
                            for col in xlsx_df.columns:
                                if not xlsx_df[col].equals(parquet_df[col]):
                                    print(f"✗ Column '{col}' differs")
                                    print(f"  Excel values: {xlsx_df[col].tolist()}")
                                    print(f"  Parquet values: {parquet_df[col].tolist()}")
                                else:
                                    print(f"✓ Column '{col}' is identical")
                    else:
                        print("✗ Columns differ")
                        print(f"  Excel: {list(xlsx_df.columns)}")
                        print(f"  Parquet: {list(parquet_df.columns)}")
                    
                    return False
            else:
                print("✗ Not all required files were created")
                return False
                
    except Exception as e:
        print(f"✗ Debug failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    debug_fatigue_files()