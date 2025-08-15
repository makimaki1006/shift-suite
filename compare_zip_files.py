#!/usr/bin/env python3
"""
Compare two zip files: motogi_short.zip and analysis_results (26).zip
"""

import zipfile
import os
import json
import pandas as pd
from pathlib import Path
import tempfile
import shutil

def extract_zip_to_temp(zip_path, temp_dir):
    """Extract zip file to temporary directory"""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    return temp_dir

def get_file_list(directory):
    """Get list of all files in directory recursively"""
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            rel_path = os.path.relpath(os.path.join(root, filename), directory)
            files.append(rel_path.replace('\\', '/'))  # Normalize path separators
    return sorted(files)

def compare_file_structures(zip1_path, zip2_path):
    """Compare file structures of two zip files"""
    
    # Create temporary directories
    temp_dir1 = tempfile.mkdtemp(prefix='motogi_')
    temp_dir2 = tempfile.mkdtemp(prefix='analysis_')
    
    try:
        # Extract both zip files
        extract_zip_to_temp(zip1_path, temp_dir1)
        extract_zip_to_temp(zip2_path, temp_dir2)
        
        # Get file lists
        files1 = get_file_list(temp_dir1)
        files2 = get_file_list(temp_dir2)
        
        print("=== ZIP FILE COMPARISON ===")
        print(f"motogi_short.zip: {len(files1)} files")
        print(f"analysis_results (26).zip: {len(files2)} files")
        print()
        
        # Find differences
        set1 = set(files1)
        set2 = set(files2)
        
        only_in_motogi = set1 - set2
        only_in_analysis = set2 - set1
        common_files = set1 & set2
        
        print(f"Files only in motogi_short.zip ({len(only_in_motogi)}):")
        for file in sorted(only_in_motogi):
            print(f"  - {file}")
        print()
        
        print(f"Files only in analysis_results (26).zip ({len(only_in_analysis)}):")
        for file in sorted(only_in_analysis):
            print(f"  - {file}")
        print()
        
        print(f"Common files ({len(common_files)}):")
        for file in sorted(common_files):
            print(f"  - {file}")
        print()
        
        # Compare content of common files
        print("=== CONTENT COMPARISON ===")
        
        # Focus on key files for shortage and heatmap analysis
        key_files = [
            'shortage_summary.json',
            'heatmap_data.json',
            'analysis_summary.json',
            'daily_shortage_summary.json',
            'role_shortage_summary.json'
        ]
        
        for filename in key_files:
            if filename in common_files:
                print(f"\n--- Comparing {filename} ---")
                compare_json_files(
                    os.path.join(temp_dir1, filename),
                    os.path.join(temp_dir2, filename)
                )
        
        # Compare CSV files
        csv_files = [f for f in common_files if f.endswith('.csv')]
        for csv_file in csv_files:
            print(f"\n--- Comparing {csv_file} ---")
            compare_csv_files(
                os.path.join(temp_dir1, csv_file),
                os.path.join(temp_dir2, csv_file)
            )
        
        return temp_dir1, temp_dir2
        
    except Exception as e:
        print(f"Error during comparison: {e}")
        # Clean up in case of error
        shutil.rmtree(temp_dir1, ignore_errors=True)
        shutil.rmtree(temp_dir2, ignore_errors=True)
        return None, None

def compare_json_files(file1, file2):
    """Compare two JSON files"""
    try:
        with open(file1, 'r', encoding='utf-8') as f1:
            data1 = json.load(f1)
        with open(file2, 'r', encoding='utf-8') as f2:
            data2 = json.load(f2)
        
        if data1 == data2:
            print("  ✓ JSON files are identical")
        else:
            print("  ✗ JSON files differ")
            
            # Show key differences
            if isinstance(data1, dict) and isinstance(data2, dict):
                keys1 = set(data1.keys())
                keys2 = set(data2.keys())
                
                if keys1 != keys2:
                    print(f"    Key differences:")
                    only_in_1 = keys1 - keys2
                    only_in_2 = keys2 - keys1
                    if only_in_1:
                        print(f"      Only in motogi: {only_in_1}")
                    if only_in_2:
                        print(f"      Only in analysis: {only_in_2}")
                
                # Check common keys for value differences
                common_keys = keys1 & keys2
                for key in common_keys:
                    if data1[key] != data2[key]:
                        print(f"    {key}: {data1[key]} vs {data2[key]}")
            
    except Exception as e:
        print(f"  Error comparing JSON files: {e}")

def compare_csv_files(file1, file2):
    """Compare two CSV files"""
    try:
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)
        
        if df1.equals(df2):
            print("  ✓ CSV files are identical")
        else:
            print("  ✗ CSV files differ")
            print(f"    motogi: {df1.shape[0]} rows, {df1.shape[1]} columns")
            print(f"    analysis: {df2.shape[0]} rows, {df2.shape[1]} columns")
            
            # Show column differences
            cols1 = set(df1.columns)
            cols2 = set(df2.columns)
            
            if cols1 != cols2:
                only_in_1 = cols1 - cols2
                only_in_2 = cols2 - cols1
                if only_in_1:
                    print(f"      Columns only in motogi: {only_in_1}")
                if only_in_2:
                    print(f"      Columns only in analysis: {only_in_2}")
            
    except Exception as e:
        print(f"  Error comparing CSV files: {e}")

def main():
    zip1_path = "motogi_short.zip"
    zip2_path = "analysis_results (26).zip"
    
    if not os.path.exists(zip1_path):
        print(f"Error: {zip1_path} not found")
        return
    
    if not os.path.exists(zip2_path):
        print(f"Error: {zip2_path} not found")
        return
    
    print("Starting ZIP file comparison...")
    
    temp_dir1, temp_dir2 = compare_file_structures(zip1_path, zip2_path)
    
    if temp_dir1 and temp_dir2:
        print(f"\nTemporary directories created:")
        print(f"  motogi_short: {temp_dir1}")
        print(f"  analysis_results: {temp_dir2}")
        print("\nFiles extracted for detailed analysis")
        
        # Keep temporary directories for further analysis
        print("\nNote: Temporary directories will be cleaned up automatically")
        
        # Clean up
        shutil.rmtree(temp_dir1, ignore_errors=True)
        shutil.rmtree(temp_dir2, ignore_errors=True)

if __name__ == "__main__":
    main()