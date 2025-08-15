#!/usr/bin/env python3
"""
Analyze shortage_time.parquet files from the three statistical methods to understand
the 27,486.5 hour calculation issue and why total shortage hours might be 0.0.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
import json

def load_and_analyze_shortage_file(file_path, method_name):
    """Load and analyze a single shortage_time.parquet file."""
    print(f"\n{'='*60}")
    print(f"ANALYZING: {method_name}")
    print(f"File: {file_path}")
    print(f"{'='*60}")
    
    try:
        # Load the parquet file
        df = pd.read_parquet(file_path)
        
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        # Display basic info
        print(f"\nData Types:")
        print(df.dtypes)
        
        print(f"\nFirst few rows:")
        print(df.head())
        
        # Calculate total shortage hours
        if 'shortage_time' in df.columns:
            total_shortage = df['shortage_time'].sum()
            print(f"\nTotal shortage hours (sum of shortage_time column): {total_shortage}")
            
            # Check for non-zero values
            non_zero_count = (df['shortage_time'] != 0).sum()
            print(f"Number of non-zero shortage_time entries: {non_zero_count}")
            
            if non_zero_count > 0:
                print(f"Non-zero shortage_time statistics:")
                non_zero_values = df[df['shortage_time'] != 0]['shortage_time']
                print(f"  Min: {non_zero_values.min()}")
                print(f"  Max: {non_zero_values.max()}")
                print(f"  Mean: {non_zero_values.mean()}")
                print(f"  Count: {len(non_zero_values)}")
        
        # Look for other time-related columns
        time_cols = [col for col in df.columns if 'time' in col.lower() or 'hour' in col.lower()]
        print(f"\nTime-related columns: {time_cols}")
        
        for col in time_cols:
            if col != 'shortage_time':  # Already analyzed above
                total_val = df[col].sum() if pd.api.types.is_numeric_dtype(df[col]) else "N/A (non-numeric)"
                print(f"  {col}: total = {total_val}")
        
        # Summary statistics for all numeric columns
        print(f"\nSummary statistics for numeric columns:")
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            print(df[numeric_cols].describe())
        
        # Check for any column that might contain the 27,486.5 value
        print(f"\nChecking for values around 27,486.5:")
        for col in numeric_cols:
            matching_values = df[df[col].abs().between(27486, 27487)]
            if len(matching_values) > 0:
                print(f"  Found potential matches in column '{col}':")
                print(matching_values[col].values)
        
        return {
            'method': method_name,
            'shape': df.shape,
            'columns': list(df.columns),
            'total_shortage_time': df['shortage_time'].sum() if 'shortage_time' in df.columns else None,
            'non_zero_shortage_count': (df['shortage_time'] != 0).sum() if 'shortage_time' in df.columns else None,
            'numeric_summary': df.select_dtypes(include=[np.number]).describe().to_dict() if len(df.select_dtypes(include=[np.number]).columns) > 0 else {},
            'sample_data': df.head().to_dict()
        }
        
    except Exception as e:
        print(f"ERROR loading {file_path}: {str(e)}")
        return {
            'method': method_name,
            'error': str(e)
        }

def main():
    """Main analysis function."""
    # Use Windows-style paths when running from Windows Python
    import platform
    if platform.system() == "Windows":
        base_path = Path(r"C:\Users\fuji1\OneDrive\デスクトップ\シフト分析\extracted_test")
    else:
        base_path = Path("/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/extracted_test")
    
    # Define the three methods and their paths
    methods = {
        'mean_based': base_path / "out_mean_based" / "shortage_time.parquet",
        'median_based': base_path / "out_median_based" / "shortage_time.parquet", 
        'p25_based': base_path / "out_p25_based" / "shortage_time.parquet"
    }
    
    results = {}
    
    print("SHORTAGE TIME ANALYSIS")
    print("=====================")
    print(f"Analyzing shortage_time.parquet files from three statistical methods")
    print(f"Base path: {base_path}")
    
    # Analyze each file
    for method_name, file_path in methods.items():
        if file_path.exists():
            results[method_name] = load_and_analyze_shortage_file(file_path, method_name)
        else:
            print(f"\nWARNING: File not found: {file_path}")
            results[method_name] = {'method': method_name, 'error': 'File not found'}
    
    # Compare results
    print(f"\n{'='*80}")
    print("COMPARISON SUMMARY")
    print(f"{'='*80}")
    
    for method_name, result in results.items():
        if 'error' not in result:
            print(f"\n{method_name.upper()}:")
            print(f"  Shape: {result['shape']}")
            print(f"  Total shortage hours: {result['total_shortage_time']}")
            print(f"  Non-zero shortage entries: {result['non_zero_shortage_count']}")
        else:
            print(f"\n{method_name.upper()}: ERROR - {result['error']}")
    
    # Check if all methods show 0.0 shortage
    shortage_totals = []
    for method_name, result in results.items():
        if 'error' not in result and result['total_shortage_time'] is not None:
            shortage_totals.append(result['total_shortage_time'])
    
    if shortage_totals:
        all_zero = all(total == 0.0 for total in shortage_totals)
        print(f"\nAll shortage totals are zero: {all_zero}")
        if all_zero:
            print("This explains why the AI report shows 0.0 total shortage hours.")
            print("The 27,486.5 hour calculation might be coming from a different source or calculation.")
    
    # Save results
    output_file = base_path / "shortage_analysis_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\nDetailed results saved to: {output_file}")

if __name__ == "__main__":
    main()