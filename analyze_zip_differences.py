#!/usr/bin/env python3
"""
Analyze differences between motogi_short.zip and analysis_results (26).zip
"""

import zipfile
import os
import json
import tempfile
import shutil
from pathlib import Path

def analyze_zip_differences():
    """Main analysis function"""
    
    zip1_path = "motogi_short.zip"
    zip2_path = "analysis_results (26).zip"
    
    # Create temporary directories
    temp_dir1 = tempfile.mkdtemp(prefix='motogi_')
    temp_dir2 = tempfile.mkdtemp(prefix='analysis_')
    
    try:
        # Extract both zip files
        with zipfile.ZipFile(zip1_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir1)
        
        with zipfile.ZipFile(zip2_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir2)
        
        print("=== DETAILED COMPARISON ANALYSIS ===")
        
        # 1. File structure comparison
        files1 = get_file_list(temp_dir1)
        files2 = get_file_list(temp_dir2)
        
        print(f"motogi_short.zip: {len(files1)} files")
        print(f"analysis_results (26).zip: {len(files2)} files")
        
        set1 = set(files1)
        set2 = set(files2)
        
        only_in_motogi = set1 - set2
        only_in_analysis = set2 - set1
        common_files = set1 & set2
        
        print(f"\nKey differences found:")
        print(f"- Files only in motogi_short: {len(only_in_motogi)}")
        print(f"- Files only in analysis_results: {len(only_in_analysis)}")
        print(f"- Common files: {len(common_files)}")
        
        # Show the unique files in motogi_short
        print(f"\nFiles only in motogi_short.zip:")
        for file in sorted(only_in_motogi):
            print(f"  - {file}")
        
        # 2. Analyze critical shortage and heatmap files
        print(f"\n=== ANALYZING CRITICAL FILES ===")
        
        # Check shortage summary files
        shortage_files = [f for f in common_files if 'shortage' in f.lower() and f.endswith('.txt')]
        for file in shortage_files:
            print(f"\n--- Analyzing {file} ---")
            analyze_text_file(
                os.path.join(temp_dir1, file),
                os.path.join(temp_dir2, file),
                "motogi_short",
                "analysis_results"
            )
        
        # Check heatmap metadata
        heatmap_meta_files = [f for f in common_files if 'heatmap.meta.json' in f]
        for file in heatmap_meta_files:
            print(f"\n--- Analyzing {file} ---")
            analyze_json_file(
                os.path.join(temp_dir1, file),
                os.path.join(temp_dir2, file),
                "motogi_short",
                "analysis_results"
            )
        
        # Check the out_p25_based directory differences
        print(f"\n=== ANALYZING out_p25_based DIFFERENCES ===")
        
        p25_files_motogi = [f for f in files1 if f.startswith('out_p25_based/')]
        p25_files_analysis = [f for f in files2 if f.startswith('out_p25_based/')]
        
        print(f"out_p25_based files in motogi_short: {len(p25_files_motogi)}")
        print(f"out_p25_based files in analysis_results: {len(p25_files_analysis)}")
        
        p25_only_motogi = set(p25_files_motogi) - set(p25_files_analysis)
        p25_only_analysis = set(p25_files_analysis) - set(p25_files_motogi)
        
        print(f"\nout_p25_based files only in motogi_short:")
        for file in sorted(p25_only_motogi):
            print(f"  - {file}")
        
        print(f"\nout_p25_based files only in analysis_results:")
        for file in sorted(p25_only_analysis):
            print(f"  - {file}")
        
        # 3. Check for the specific missing files
        missing_files = [
            'out_p25_based/ppo_model.zip',
            'out_p25_based/rl_roster.meta.json',
            'out_p25_based/rl_roster.xlsx',
            'motogi_day.zip'
        ]
        
        print(f"\n=== ANALYZING MISSING FILES ===")
        for file in missing_files:
            if file in only_in_motogi:
                file_path = os.path.join(temp_dir1, file)
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    print(f"  - {file}: {size} bytes (exists in motogi_short only)")
                    
                    # If it's a zip file, show contents
                    if file.endswith('.zip'):
                        try:
                            with zipfile.ZipFile(file_path, 'r') as zf:
                                contents = zf.namelist()
                                print(f"    Contains {len(contents)} files")
                                for content in contents[:5]:  # Show first 5 files
                                    print(f"      - {content}")
                                if len(contents) > 5:
                                    print(f"      ... and {len(contents) - 5} more")
                        except Exception as e:
                            print(f"    Error reading zip: {e}")
        
        # 4. Summary and implications
        print(f"\n=== SUMMARY AND IMPLICATIONS ===")
        
        print(f"Key Findings:")
        print(f"1. motogi_short.zip contains {len(only_in_motogi)} additional files")
        print(f"2. These files are primarily in the out_p25_based directory")
        print(f"3. Missing files include:")
        print(f"   - PPO model files (ppo_model.zip, rl_roster.meta.json, rl_roster.xlsx)")
        print(f"   - motogi_day.zip (possibly containing additional day shift data)")
        
        print(f"\nPotential Issues:")
        print(f"1. Machine learning model files are missing from analysis_results")
        print(f"2. Some metadata or configuration files may be missing")
        print(f"3. The motogi_day.zip suggests additional data that wasn't processed")
        
        # 5. Check file sizes for common files
        print(f"\n=== FILE SIZE COMPARISON ===")
        
        # Compare sizes of some key files
        key_comparison_files = [
            'out_p25_based/shortage_summary.txt',
            'out_p25_based/heatmap.meta.json',
            'out_p25_based/hire_plan.txt'
        ]
        
        for file in key_comparison_files:
            if file in common_files:
                file1_path = os.path.join(temp_dir1, file)
                file2_path = os.path.join(temp_dir2, file)
                
                if os.path.exists(file1_path) and os.path.exists(file2_path):
                    size1 = os.path.getsize(file1_path)
                    size2 = os.path.getsize(file2_path)
                    
                    print(f"{file}:")
                    print(f"  motogi_short: {size1} bytes")
                    print(f"  analysis_results: {size2} bytes")
                    if size1 != size2:
                        print(f"  *** SIZE DIFFERENCE: {size1 - size2} bytes ***")
                    else:
                        print(f"  ✓ Same size")
        
        return temp_dir1, temp_dir2
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        return None, None
    finally:
        # Clean up
        shutil.rmtree(temp_dir1, ignore_errors=True)
        shutil.rmtree(temp_dir2, ignore_errors=True)

def get_file_list(directory):
    """Get list of all files in directory recursively"""
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            rel_path = os.path.relpath(os.path.join(root, filename), directory)
            files.append(rel_path.replace('\\', '/'))
    return files

def analyze_text_file(file1, file2, name1, name2):
    """Compare two text files"""
    try:
        with open(file1, 'r', encoding='utf-8') as f1:
            content1 = f1.read()
        with open(file2, 'r', encoding='utf-8') as f2:
            content2 = f2.read()
        
        if content1 == content2:
            print(f"  ✓ Files are identical")
        else:
            print(f"  ✗ Files differ")
            print(f"    {name1}: {len(content1)} characters")
            print(f"    {name2}: {len(content2)} characters")
            
            # Show first few lines of each
            lines1 = content1.split('\n')[:5]
            lines2 = content2.split('\n')[:5]
            
            print(f"    First lines from {name1}:")
            for i, line in enumerate(lines1):
                print(f"      {i+1}: {line[:100]}...")
            
            print(f"    First lines from {name2}:")
            for i, line in enumerate(lines2):
                print(f"      {i+1}: {line[:100]}...")
    
    except Exception as e:
        print(f"  Error comparing text files: {e}")

def analyze_json_file(file1, file2, name1, name2):
    """Compare two JSON files"""
    try:
        with open(file1, 'r', encoding='utf-8') as f1:
            data1 = json.load(f1)
        with open(file2, 'r', encoding='utf-8') as f2:
            data2 = json.load(f2)
        
        if data1 == data2:
            print(f"  ✓ JSON files are identical")
        else:
            print(f"  ✗ JSON files differ")
            
            if isinstance(data1, dict) and isinstance(data2, dict):
                keys1 = set(data1.keys())
                keys2 = set(data2.keys())
                
                print(f"    {name1}: {len(keys1)} keys")
                print(f"    {name2}: {len(keys2)} keys")
                
                if keys1 != keys2:
                    only_in_1 = keys1 - keys2
                    only_in_2 = keys2 - keys1
                    if only_in_1:
                        print(f"    Keys only in {name1}: {sorted(only_in_1)}")
                    if only_in_2:
                        print(f"    Keys only in {name2}: {sorted(only_in_2)}")
                
                # Show some key differences
                common_keys = keys1 & keys2
                differences = []
                for key in sorted(common_keys):
                    if data1[key] != data2[key]:
                        differences.append(key)
                        if len(differences) <= 3:  # Show first 3 differences
                            print(f"    {key}: {data1[key]} vs {data2[key]}")
                
                if len(differences) > 3:
                    print(f"    ... and {len(differences) - 3} more differences")
    
    except Exception as e:
        print(f"  Error comparing JSON files: {e}")

if __name__ == "__main__":
    analyze_zip_differences()