#!/usr/bin/env python3
"""
Comprehensive analysis of ZIP file contents to identify missing files and inconsistencies
"""
import zipfile
import json
from pathlib import Path
from collections import defaultdict
import pandas as pd

def analyze_zip_contents(zip_path):
    """Analyze the contents of the analysis results ZIP file"""
    print(f"=== Analyzing {zip_path} ===\n")
    
    # File categories
    file_categories = {
        'heatmap': ['heat_*.parquet', 'heat_*.xlsx', 'heatmap.meta.json'],
        'shortage': ['shortage_*.parquet', 'shortage_*.txt', 'shortage.meta.json'],
        'excess': ['excess_*.parquet'],
        'need': ['need_per_date_slot*.parquet'],
        'leave': ['leave_analysis.csv', 'leave_ratio_breakdown.csv'],
        'fatigue': ['fatigue_score.parquet', 'fatigue_score.xlsx'],
        'forecast': ['forecast_*.parquet', 'demand_series.csv'],
        'cost': ['cost_benefit.parquet', 'daily_cost.parquet'],
        'stats': ['stats_*.parquet', 'stats_summary.txt'],
        'work_patterns': ['work_patterns.parquet', 'work_patterns.csv'],
        'anomaly': ['anomaly_days.parquet'],
        'optimization': ['optimization_score_time.parquet', 'optimal_hire_plan.parquet'],
        'intermediate': ['intermediate_data.parquet', 'pre_aggregated_data.parquet'],
        'attendance': ['attendance.csv', 'combined_score.csv'],
        'logs': ['*.txt', '*.log']
    }
    
    # Track files by scenario
    scenario_files = defaultdict(set)
    all_files = []
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for file_info in zf.filelist:
            filename = file_info.filename
            all_files.append(filename)
            
            # Extract scenario name
            parts = filename.split('/')
            if len(parts) > 1 and parts[0].startswith('out_'):
                scenario = parts[0]
                file_base = '/'.join(parts[1:])
                scenario_files[scenario].add(file_base)
    
    # Print summary
    print(f"Total files: {len(all_files)}")
    print(f"Scenarios found: {list(scenario_files.keys())}\n")
    
    # Check file consistency across scenarios
    print("=== File Consistency Across Scenarios ===")
    
    # Get union of all files
    all_unique_files = set()
    for files in scenario_files.values():
        all_unique_files.update(files)
    
    # Check which files are missing in which scenarios
    missing_files = defaultdict(list)
    for scenario, files in scenario_files.items():
        for file in all_unique_files:
            if file not in files:
                missing_files[file].append(scenario)
    
    # Report missing files
    if missing_files:
        print("\nFiles missing from some scenarios:")
        for file, scenarios in sorted(missing_files.items()):
            if len(scenarios) < len(scenario_files):  # Not missing from all
                print(f"  {file}: missing from {scenarios}")
    
    # Check for expected files
    print("\n=== Expected Files Check ===")
    
    expected_core_files = [
        'heat_ALL.parquet',
        'heat_ALL.xlsx',
        'shortage_time.parquet',
        'shortage_freq.parquet',
        'shortage_ratio.parquet',
        'excess_time.parquet',
        'excess_freq.parquet',
        'excess_ratio.parquet',
        'need_per_date_slot.parquet',
        'intermediate_data.parquet',  # Critical file
        'pre_aggregated_data.parquet',
        'heatmap.meta.json',
        'shortage.meta.json'
    ]
    
    for scenario in scenario_files:
        print(f"\n{scenario}:")
        missing_core = []
        for expected in expected_core_files:
            if expected not in scenario_files[scenario]:
                missing_core.append(expected)
        
        if missing_core:
            print(f"  Missing core files: {missing_core}")
        else:
            print(f"  [OK] All core files present")
    
    # Special check for files that should be in all scenarios
    print("\n=== Files That Should Be In All Scenarios ===")
    
    files_should_be_everywhere = [
        'fatigue_score.parquet',
        'fatigue_score.xlsx',
        'leave_analysis.csv'
    ]
    
    for file in files_should_be_everywhere:
        present_in = [s for s in scenario_files if file in scenario_files[s]]
        if len(present_in) < len(scenario_files):
            print(f"  {file}: only in {present_in} (should be in all)")
    
    # Check for scenario-specific files
    print("\n=== Scenario-Specific Files ===")
    
    for scenario, files in scenario_files.items():
        unique_files = files.copy()
        for other_scenario, other_files in scenario_files.items():
            if other_scenario != scenario:
                unique_files -= other_files
        
        if unique_files:
            print(f"\n{scenario} has unique files:")
            for f in sorted(unique_files):
                print(f"  - {f}")
    
    return scenario_files, missing_files

if __name__ == "__main__":
    # Check the latest analysis results
    zip_files = [
        Path(r"C:\Users\fuji1\OneDrive\デスクトップ\シフト分析\analysis_results (50).zip"),
        Path(r"C:\Users\fuji1\OneDrive\デスクトップ\シフト分析\analysis_results (48).zip")
    ]
    
    for zip_path in zip_files:
        if zip_path.exists():
            analyze_zip_contents(zip_path)
            print("\n" + "="*60 + "\n")