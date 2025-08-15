#!/usr/bin/env python3
"""
Simple zip file comparison without external dependencies
"""

import zipfile
import os
import json
import tempfile
import shutil

def extract_and_compare_zips(zip1_path, zip2_path):
    """Extract and compare two zip files"""
    
    # Create temporary directories
    temp_dir1 = tempfile.mkdtemp(prefix='motogi_')
    temp_dir2 = tempfile.mkdtemp(prefix='analysis_')
    
    try:
        # Extract both zip files
        with zipfile.ZipFile(zip1_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir1)
        
        with zipfile.ZipFile(zip2_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir2)
        
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
        
        # Compare key files
        print("=== CONTENT COMPARISON ===")
        
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
                file1_path = os.path.join(temp_dir1, filename)
                file2_path = os.path.join(temp_dir2, filename)
                
                if os.path.exists(file1_path) and os.path.exists(file2_path):
                    compare_json_files(file1_path, file2_path)
                else:
                    print(f"  Warning: File not found in one or both directories")
        
        # Show directory structure for detailed analysis
        print("\n=== DIRECTORY STRUCTURE ===")
        print(f"motogi_short extracted to: {temp_dir1}")
        print(f"analysis_results extracted to: {temp_dir2}")
        
        # List first few files from each directory for verification
        print(f"\nSample files from motogi_short:")
        for i, file in enumerate(sorted(files1)[:10]):
            print(f"  {i+1}. {file}")
        
        print(f"\nSample files from analysis_results:")
        for i, file in enumerate(sorted(files2)[:10]):
            print(f"  {i+1}. {file}")
        
        return temp_dir1, temp_dir2
        
    except Exception as e:
        print(f"Error during comparison: {e}")
        # Clean up in case of error
        shutil.rmtree(temp_dir1, ignore_errors=True)
        shutil.rmtree(temp_dir2, ignore_errors=True)
        return None, None

def get_file_list(directory):
    """Get list of all files in directory recursively"""
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            rel_path = os.path.relpath(os.path.join(root, filename), directory)
            files.append(rel_path.replace('\\', '/'))  # Normalize path separators
    return files

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
            
            # Show structural differences
            if isinstance(data1, dict) and isinstance(data2, dict):
                keys1 = set(data1.keys())
                keys2 = set(data2.keys())
                
                if keys1 != keys2:
                    print(f"    Key differences:")
                    only_in_1 = keys1 - keys2
                    only_in_2 = keys2 - keys1
                    if only_in_1:
                        print(f"      Only in motogi: {sorted(only_in_1)}")
                    if only_in_2:
                        print(f"      Only in analysis: {sorted(only_in_2)}")
                
                # Check common keys for value differences
                common_keys = keys1 & keys2
                differences = []
                for key in sorted(common_keys):
                    if data1[key] != data2[key]:
                        differences.append(key)
                
                if differences:
                    print(f"    Value differences in keys: {differences[:10]}")  # Show first 10
                    if len(differences) > 10:
                        print(f"    ... and {len(differences) - 10} more")
            
    except Exception as e:
        print(f"  Error comparing JSON files: {e}")

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
    
    temp_dir1, temp_dir2 = extract_and_compare_zips(zip1_path, zip2_path)
    
    if temp_dir1 and temp_dir2:
        print(f"\nTemporary directories available for inspection:")
        print(f"  motogi_short: {temp_dir1}")
        print(f"  analysis_results: {temp_dir2}")
        
        # Keep directories for now, will clean up later
        print("\nTo manually inspect files:")
        print(f"  ls -la '{temp_dir1}'")
        print(f"  ls -la '{temp_dir2}'")
        
        # Clean up
        input("Press Enter to clean up temporary directories...")
        shutil.rmtree(temp_dir1, ignore_errors=True)
        shutil.rmtree(temp_dir2, ignore_errors=True)
        print("Temporary directories cleaned up")

if __name__ == "__main__":
    main()