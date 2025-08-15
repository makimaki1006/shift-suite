#!/usr/bin/env python3
"""
問題コードの使用状況詳細分析
"""

import pandas as pd
from pathlib import Path

def analyze_problematic_usage():
    """問題コードの使用状況分析"""
    
    print("=== Problematic Code Usage Analysis ===")
    
    test_file = Path("デイ_テスト用データ_休日精緻.xlsx")
    
    # 問題のコード
    problem_codes = ['有', '欠', '休']
    
    try:
        for sheet_name in ["R7.2", "R7.6"]:
            print(f"\n=== {sheet_name} Sheet ===")
            
            df = pd.read_excel(test_file, sheet_name=sheet_name, header=0, dtype=str).fillna("")
            
            print(f"Sheet shape: {df.shape}")
            print(f"Staff columns: {df.columns[:3].tolist()}")
            
            # 日付列
            date_cols = df.columns[3:]
            print(f"Date columns: {len(date_cols)} columns")
            
            # 各問題コードの使用状況
            for problem_code in problem_codes:
                print(f"\n  --- Code '{problem_code}' Usage ---")
                
                usage_found = False
                for col_idx, col in enumerate(date_cols):
                    for row_idx in range(len(df)):
                        cell_value = str(df.iloc[row_idx, col_idx + 3]).strip()
                        
                        if cell_value == problem_code:
                            staff = str(df.iloc[row_idx, 0]) if df.iloc[row_idx, 0] else "Unknown"
                            role = str(df.iloc[row_idx, 1]) if len(df.columns) > 1 and df.iloc[row_idx, 1] else "Unknown"
                            employment = str(df.iloc[row_idx, 2]) if len(df.columns) > 2 and df.iloc[row_idx, 2] else "Unknown"
                            
                            print(f"    {col} | {staff} ({role}, {employment})")
                            usage_found = True
                
                if not usage_found:
                    print(f"    No usage found")
        
        # 解決策の提案
        print(f"\n=== Analysis Summary ===")
        print(f"1. '有' (有給) - Defined as leave but used in shifts")
        print(f"2. '欠' (欠勤) - Defined as leave but used in shifts") 
        print(f"3. '休' (休暇) - Used in shifts but not defined at all")
        
        print(f"\n=== Possible Solutions ===")
        print(f"A. Data Correction Approach:")
        print(f"   - Replace these codes with proper work codes in shift data")
        print(f"   - Or define them as actual work time codes in worktype sheet")
        
        print(f"B. Definition Completion Approach:")
        print(f"   - Add missing '休' definition to worktype sheet")
        print(f"   - Decide if '有' and '欠' should be work or leave codes")
        
        print(f"C. Data Validation Approach:")
        print(f"   - Verify with user which codes should be work vs leave")
        print(f"   - Ensure consistency between definition and usage")
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_problematic_usage()