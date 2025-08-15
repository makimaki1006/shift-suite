#!/usr/bin/env python3
"""
Investigate motogi_day.zip contents to understand the additional data
"""

import zipfile
import os
import json
import tempfile
import shutil

def investigate_motogi_day():
    """Investigate the contents of motogi_day.zip"""
    
    # First extract motogi_short.zip to access motogi_day.zip
    temp_dir = tempfile.mkdtemp(prefix='motogi_investigation_')
    
    try:
        # Extract motogi_short.zip
        with zipfile.ZipFile("motogi_short.zip", 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Check if motogi_day.zip exists
        motogi_day_path = os.path.join(temp_dir, "motogi_day.zip")
        
        if os.path.exists(motogi_day_path):
            print("=== MOTOGI_DAY.ZIP INVESTIGATION ===")
            print(f"File size: {os.path.getsize(motogi_day_path)} bytes")
            
            # Extract motogi_day.zip
            day_temp_dir = tempfile.mkdtemp(prefix='motogi_day_')
            
            try:
                with zipfile.ZipFile(motogi_day_path, 'r') as day_zip:
                    day_zip.extractall(day_temp_dir)
                
                # Get file list
                day_files = get_file_list(day_temp_dir)
                print(f"Contains {len(day_files)} files")
                
                # Analyze file structure
                print("\n=== FILE STRUCTURE ANALYSIS ===")
                
                # Group files by directory
                directories = {}
                for file in day_files:
                    if '/' in file:
                        dir_name = file.split('/')[0]
                        if dir_name not in directories:
                            directories[dir_name] = []
                        directories[dir_name].append(file)
                    else:
                        if 'root' not in directories:
                            directories['root'] = []
                        directories['root'].append(file)
                
                for dir_name, files in directories.items():
                    print(f"\n{dir_name}/ ({len(files)} files):")
                    for file in sorted(files)[:10]:  # Show first 10
                        print(f"  - {file}")
                    if len(files) > 10:
                        print(f"  ... and {len(files) - 10} more files")
                
                # Check for key files
                print("\n=== KEY FILES ANALYSIS ===")
                
                key_files = [
                    'shortage_summary.txt',
                    'heatmap.meta.json',
                    'hire_plan.txt'
                ]
                
                for key_file in key_files:
                    matching_files = [f for f in day_files if key_file in f]
                    if matching_files:
                        print(f"\n{key_file} files found:")
                        for file in matching_files:
                            file_path = os.path.join(day_temp_dir, file)
                            if os.path.exists(file_path):
                                size = os.path.getsize(file_path)
                                print(f"  - {file} ({size} bytes)")
                                
                                # Read shortage summary files
                                if 'shortage_summary.txt' in file:
                                    try:
                                        with open(file_path, 'r', encoding='utf-8') as f:
                                            content = f.read()
                                            print(f"    Content: {content.strip()}")
                                    except Exception as e:
                                        print(f"    Error reading: {e}")
                
                # Compare with main analysis
                print("\n=== COMPARISON WITH MAIN ANALYSIS ===")
                
                # Check if there are out_p25_based files
                p25_files = [f for f in day_files if f.startswith('out_p25_based/')]
                if p25_files:
                    print(f"out_p25_based files: {len(p25_files)}")
                    
                    # Check shortage summary
                    p25_shortage = [f for f in p25_files if 'shortage_summary.txt' in f]
                    if p25_shortage:
                        file_path = os.path.join(day_temp_dir, p25_shortage[0])
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                print(f"motogi_day p25 shortage: {content.strip()}")
                        except Exception as e:
                            print(f"Error reading p25 shortage: {e}")
                
                # Check for unique files not in main analysis
                main_files = get_main_analysis_files()
                unique_files = [f for f in day_files if f not in main_files]
                
                if unique_files:
                    print(f"\n=== UNIQUE FILES IN MOTOGI_DAY ({len(unique_files)}) ===")
                    for file in sorted(unique_files)[:20]:  # Show first 20
                        print(f"  - {file}")
                    if len(unique_files) > 20:
                        print(f"  ... and {len(unique_files) - 20} more")
                
                # Check for different time slot configurations
                print("\n=== TIME SLOT ANALYSIS ===")
                heatmap_files = [f for f in day_files if 'heatmap.meta.json' in f]
                for heatmap_file in heatmap_files:
                    file_path = os.path.join(day_temp_dir, heatmap_file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if 'slot' in data:
                                print(f"  {heatmap_file}: slot = {data['slot']}")
                            if 'dow_need_pattern' in data and len(data['dow_need_pattern']) > 0:
                                first_pattern = data['dow_need_pattern'][0]
                                print(f"  {heatmap_file}: first pattern = {first_pattern}")
                    except Exception as e:
                        print(f"  Error reading {heatmap_file}: {e}")
                
            finally:
                shutil.rmtree(day_temp_dir, ignore_errors=True)
        
        else:
            print("motogi_day.zip not found in motogi_short.zip")
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def get_file_list(directory):
    """Get list of all files in directory recursively"""
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            rel_path = os.path.relpath(os.path.join(root, filename), directory)
            files.append(rel_path.replace('\\', '/'))
    return files

def get_main_analysis_files():
    """Get list of files that should be in main analysis"""
    # This is a simplified list - in practice you'd compare with actual analysis_results
    return [
        'concentration_requested.csv',
        'daily_cost.parquet',
        'daily_cost.xlsx',
        'fairness_after.parquet',
        'fairness_before.parquet',
        'fatigue_score.parquet',
        'leave_analysis.csv',
        'leave_ratio_breakdown.csv',
        'staff_balance_daily.csv',
        'staff_cluster.parquet',
        'skill_matrix.parquet'
    ]

if __name__ == "__main__":
    investigate_motogi_day()