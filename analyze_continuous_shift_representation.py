#!/usr/bin/env python3
"""
Comprehensive analysis of how continuous work patterns (night→morning shifts) 
are represented in the shift data and converted to long_df format.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def analyze_shift_data():
    print("=== Comprehensive Analysis of Continuous Work Representation ===\n")
    
    # Load the Excel file and examine all sheets
    try:
        xl_file = pd.ExcelFile('デイ_テスト用データ_休日精緻.xlsx')
        print(f"Available sheets: {xl_file.sheet_names}\n")
        
        # Analyze shift pattern definitions
        print("1. SHIFT PATTERN DEFINITIONS")
        print("=" * 50)
        patterns_df = pd.read_excel('デイ_テスト用データ_休日精緻.xlsx', sheet_name=0)
        print(patterns_df.to_string())
        print()
        
        # Create a mapping of shift codes to time ranges
        shift_mapping = {}
        for _, row in patterns_df.iterrows():
            code = row['記号']
            start_time = row['開始']
            end_time = row['終了']
            notes = row['備考']
            shift_mapping[code] = {
                'start': start_time,
                'end': end_time,
                'notes': notes
            }
        
        # Analyze June schedule data (R7.6)
        print("2. JUNE SCHEDULE DATA ANALYSIS")
        print("=" * 50)
        df = pd.read_excel('デイ_テスト用データ_休日精緻.xlsx', sheet_name='R7.6', header=None)
        
        # Extract dates from header row
        date_columns = []
        for i in range(3, df.shape[1]):
            if pd.notna(df.iloc[0, i]):
                date_columns.append((i, df.iloc[0, i]))
        
        print(f"Date range: {str(date_columns[0][1])[:10]} to {str(date_columns[-1][1])[:10]}")
        print(f"Number of days: {len(date_columns)}")
        print()
        
        # Extract all unique shift codes
        all_codes = set()
        for row in range(2, df.shape[0]):
            for col in range(3, df.shape[1]):
                value = df.iloc[row, col]
                if pd.notna(value) and str(value).strip():
                    all_codes.add(str(value).strip())
        
        print("Unique shift codes found:")
        for code in sorted(all_codes):
            if code in shift_mapping:
                start = shift_mapping[code]['start']
                end = shift_mapping[code]['end']
                notes = shift_mapping[code]['notes']
                print(f"  '{code}': {start} - {end} ({notes})")
            else:
                print(f"  '{code}': [No definition found]")
        print()
        
        # Analyze potential continuous work patterns
        print("3. CONTINUOUS WORK PATTERN ANALYSIS")
        print("=" * 50)
        
        # Look for patterns that might indicate continuous work
        # Even without explicit night/morning codes, we can look for patterns like:
        # - Late shifts followed by early shifts
        # - Special codes that might indicate continuous work
        
        continuous_candidates = []
        
        for staff_row in range(2, df.shape[0]):
            staff_name = df.iloc[staff_row, 0]
            role = df.iloc[staff_row, 1]
            employment = df.iloc[staff_row, 2]
            
            if pd.isna(staff_name):
                continue
            
            # Check consecutive days for potential continuous patterns
            for i in range(len(date_columns) - 1):
                col_idx_1 = date_columns[i][0]
                col_idx_2 = date_columns[i+1][0]
                date_1 = str(date_columns[i][1])[:10]
                date_2 = str(date_columns[i+1][1])[:10]
                
                shift_1 = str(df.iloc[staff_row, col_idx_1]).strip() if pd.notna(df.iloc[staff_row, col_idx_1]) else ''
                shift_2 = str(df.iloc[staff_row, col_idx_2]).strip() if pd.notna(df.iloc[staff_row, col_idx_2]) else ''
                
                # Look for potential continuous work indicators
                # This might be same staff with shifts on consecutive days
                if shift_1 and shift_2 and shift_1 != '休' and shift_2 != '休' and shift_1 != '有' and shift_2 != '有':
                    # Get time information for these shifts
                    shift_1_info = shift_mapping.get(shift_1, {})
                    shift_2_info = shift_mapping.get(shift_2, {})
                    
                    continuous_candidates.append({
                        'staff': staff_name,
                        'role': role,
                        'employment': employment,
                        'date1': date_1,
                        'shift1': shift_1,
                        'shift1_start': shift_1_info.get('start'),
                        'shift1_end': shift_1_info.get('end'),
                        'date2': date_2,
                        'shift2': shift_2,
                        'shift2_start': shift_2_info.get('start'),
                        'shift2_end': shift_2_info.get('end'),
                    })
        
        # Display continuous work candidates
        print("Potential continuous work patterns (consecutive working days):")
        print("Note: In real night→morning shifts, night shift would end at ~24:00 and morning shift would start at ~00:00")
        print()
        
        for i, candidate in enumerate(continuous_candidates[:10]):  # Show first 10
            print(f"{i+1}. {candidate['staff']} ({candidate['role']})")
            print(f"   {candidate['date1']}: {candidate['shift1']} ({candidate['shift1_start']} - {candidate['shift1_end']})")
            print(f"   {candidate['date2']}: {candidate['shift2']} ({candidate['shift2_start']} - {candidate['shift2_end']})")
            print()
        
        if len(continuous_candidates) > 10:
            print(f"... and {len(continuous_candidates) - 10} more patterns")
            print()
        
        # Simulate how this would be converted to long_df format
        print("4. SIMULATION OF LONG_DF CONVERSION")
        print("=" * 50)
        
        print("When this schedule data is converted to long_df format:")
        print("- Each shift becomes multiple time slot records (every 15 minutes)")
        print("- A night shift (23:45-23:59) would create records at 23:45")
        print("- A morning shift (00:00-00:15) would create records at 00:00")
        print("- These would appear as SEPARATE, INDEPENDENT records")
        print("- The system has NO WAY to know they represent continuous work")
        print()
        
        # Show example of how continuous work would look in long_df
        print("Example of continuous work in long_df format:")
        print("staff_name | date       | time  | shift_code | role     | employment")
        print("-----------|------------|-------|------------|----------|------------")
        print("田中 太郎   | 2024-06-02 | 23:45 | 夜         | 介護     | 正社員")
        print("田中 太郎   | 2024-06-03 | 00:00 | 明         | 介護     | 正社員")
        print("田中 太郎   | 2024-06-03 | 00:15 | 明         | 介護     | 正社員")
        print()
        print("PROBLEM: The system treats these as separate shifts!")
        print("- Record 1: Night shift ending at 23:45")
        print("- Record 2: Morning shift starting at 00:00")
        print("- No connection between them is preserved")
        print("- This leads to incorrect Need calculations")
        print()
        
        # Analyze the impact on Need calculation
        print("5. IMPACT ON NEED CALCULATION")
        print("=" * 50)
        print("When continuous work is treated as separate shifts:")
        print("1. Night shift contributes to staffing until 23:59")
        print("2. Morning shift contributes to staffing from 00:00")
        print("3. But the SAME PERSON is counted twice")
        print("4. This creates false abundance of staff during transition")
        print("5. Need calculation becomes inaccurate")
        print()
        print("Real scenario:")
        print("- 1 person works continuously from 23:00 to 08:00")
        print("- Should count as 1 person throughout the period")
        print()
        print("System's interpretation:")
        print("- 1 person works night shift (ends at 23:59)")
        print("- 1 person works morning shift (starts at 00:00)")
        print("- Counts as 2 different people = DOUBLE COUNTING")
        
        return continuous_candidates, shift_mapping
        
    except Exception as e:
        print(f"Error analyzing data: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    continuous_candidates, shift_mapping = analyze_shift_data()
    
    if continuous_candidates:
        print(f"\n=== SUMMARY ===")
        print(f"Found {len(continuous_candidates)} potential continuous work patterns")
        print("These patterns, when converted to long_df, lose their continuity information")
        print("This is the root cause of Need calculation inaccuracies")