#!/usr/bin/env python3
"""
Detailed analysis of shortage_time.parquet files to understand the shortage calculation.
The files have a time-series structure: rows are time slots, columns are dates.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

def analyze_shortage_file_detailed(file_path, method_name):
    """Analyze a shortage_time.parquet file with proper time-series understanding."""
    print(f"\n{'='*70}")
    print(f"DETAILED ANALYSIS: {method_name}")
    print(f"File: {file_path}")
    print(f"{'='*70}")
    
    try:
        # Load the parquet file
        df = pd.read_parquet(file_path)
        
        print(f"Shape: {df.shape} (rows=time_slots, columns=dates)")
        print(f"Date range: {df.columns[0]} to {df.columns[-1]}")
        print(f"Time slots: {len(df)} (index: {df.index.name})")
        
        # Calculate total shortage hours across all time slots and dates
        total_shortage_count = df.sum().sum()  # Sum across all cells
        
        # Each shortage count typically represents a 30-minute or 1-hour period
        # Let's check the time slot pattern
        time_slots = df.index.tolist()
        print(f"Time slot sample: {time_slots[:10]}")
        
        # Calculate time interval (assuming 30-minute slots based on common pattern)
        time_interval_hours = 0.5  # 30 minutes
        if len(time_slots) == 24:
            time_interval_hours = 1.0  # 1 hour slots
        elif len(time_slots) == 48:
            time_interval_hours = 0.5  # 30 minute slots
        else:
            # Try to determine from the time format
            if len(time_slots) > 10:
                sample_times = time_slots[:10]
                print(f"Analyzing time slot pattern from: {sample_times}")
        
        total_shortage_hours = total_shortage_count * time_interval_hours
        
        print(f"\nSHORTAGE CALCULATION:")
        print(f"  Total shortage counts: {total_shortage_count}")
        print(f"  Time interval per slot: {time_interval_hours} hours")
        print(f"  TOTAL SHORTAGE HOURS: {total_shortage_hours}")
        
        # Analyze distribution across dates
        daily_shortages = df.sum()  # Sum per date (column)
        daily_shortage_hours = daily_shortages * time_interval_hours
        
        print(f"\nDAILY SHORTAGE DISTRIBUTION:")
        print(f"  Days with shortages: {(daily_shortages > 0).sum()}")
        print(f"  Max daily shortage: {daily_shortages.max()} counts ({daily_shortages.max() * time_interval_hours} hours)")
        print(f"  Average daily shortage: {daily_shortages.mean():.2f} counts ({daily_shortages.mean() * time_interval_hours:.2f} hours)")
        
        # Top 10 days with highest shortages
        top_shortage_days = daily_shortage_hours.nlargest(10)
        if len(top_shortage_days[top_shortage_days > 0]) > 0:
            print(f"\nTOP SHORTAGE DAYS:")
            for date, hours in top_shortage_days[top_shortage_days > 0].items():
                print(f"  {date}: {hours} hours")
        
        # Analyze distribution across time slots
        hourly_shortages = df.sum(axis=1)  # Sum per time slot (row)
        hourly_shortage_days = hourly_shortages  # This is count of days, not hours
        
        print(f"\nTIME SLOT SHORTAGE DISTRIBUTION:")
        print(f"  Time slots with shortages: {(hourly_shortages > 0).sum()}")
        print(f"  Max shortage time slot: {hourly_shortages.max()} days")
        
        # Top 10 time slots with highest shortages
        top_shortage_times = hourly_shortages.nlargest(10)
        if len(top_shortage_times[top_shortage_times > 0]) > 0:
            print(f"\nTOP SHORTAGE TIME SLOTS:")
            for time_slot, day_count in top_shortage_times[top_shortage_times > 0].items():
                print(f"  {time_slot}: shortage on {day_count} days")
        
        # Sample of actual shortage data
        print(f"\nSAMPLE DATA (first 5 time slots, first 10 dates):")
        sample_data = df.iloc[:5, :10]
        print(sample_data)
        
        # Check for any suspicious large values
        max_value = df.max().max()
        if max_value > 10:
            print(f"\nWARNING: Found unusually large shortage values (max: {max_value})")
            large_values = df[df > 10].stack()
            if len(large_values) > 0:
                print(f"Large values found:")
                for (time_slot, date), value in large_values.head(10).items():
                    print(f"  {date} at {time_slot}: {value}")
        
        return {
            'method': method_name,
            'shape': df.shape,
            'total_shortage_counts': int(total_shortage_count),
            'time_interval_hours': time_interval_hours,
            'total_shortage_hours': float(total_shortage_hours),
            'days_with_shortages': int((daily_shortages > 0).sum()),
            'max_daily_shortage_hours': float(daily_shortages.max() * time_interval_hours),
            'avg_daily_shortage_hours': float(daily_shortages.mean() * time_interval_hours),
            'time_slots_with_shortages': int((hourly_shortages > 0).sum()),
            'max_value': int(max_value),
            'date_range': f"{df.columns[0]} to {df.columns[-1]}",
            'top_shortage_days': dict(daily_shortage_hours.nlargest(5).to_dict()),
            'top_shortage_times': dict(hourly_shortages.nlargest(5).to_dict())
        }
        
    except Exception as e:
        print(f"ERROR loading {file_path}: {str(e)}")
        import traceback
        traceback.print_exc()
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
    
    print("DETAILED SHORTAGE TIME ANALYSIS")
    print("===============================")
    print(f"Analyzing shortage_time.parquet files from three statistical methods")
    print(f"Base path: {base_path}")
    
    # Analyze each file
    for method_name, file_path in methods.items():
        if file_path.exists():
            results[method_name] = analyze_shortage_file_detailed(file_path, method_name)
        else:
            print(f"\nWARNING: File not found: {file_path}")
            results[method_name] = {'method': method_name, 'error': 'File not found'}
    
    # Final comparison
    print(f"\n{'='*80}")
    print("FINAL COMPARISON SUMMARY")
    print(f"{'='*80}")
    
    shortage_totals = []
    for method_name, result in results.items():
        if 'error' not in result:
            total_hours = result['total_shortage_hours']
            shortage_totals.append(total_hours)
            print(f"\n{method_name.upper()}:")
            print(f"  Total shortage hours: {total_hours:,.1f}")
            print(f"  Days with shortages: {result['days_with_shortages']}")
            print(f"  Max daily shortage: {result['max_daily_shortage_hours']:.1f} hours")
            print(f"  Time slots affected: {result['time_slots_with_shortages']}")
        else:
            print(f"\n{method_name.upper()}: ERROR - {result['error']}")
    
    if shortage_totals:
        print(f"\nCOMPARISON:")
        print(f"  All totals: {[f'{x:,.1f}' for x in shortage_totals]}")
        print(f"  All are zero: {all(total == 0.0 for total in shortage_totals)}")
        print(f"  Range: {min(shortage_totals):,.1f} to {max(shortage_totals):,.1f} hours")
        
        if all(total == 0.0 for total in shortage_totals):
            print(f"\n  This explains why the AI report shows 0.0 total shortage hours!")
            print(f"  The 27,486.5 hour calculation must be coming from a different")
            print(f"  source or calculation method not captured in these files.")
        elif any(abs(total - 27486.5) < 1 for total in shortage_totals):
            print(f"\n  FOUND MATCH! One of the methods shows ~27,486.5 hours!")
    
    # Save detailed results
    output_file = base_path / "detailed_shortage_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\nDetailed results saved to: {output_file}")

if __name__ == "__main__":
    main()