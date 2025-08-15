import pandas as pd
import re
from collections import Counter

def _normalize(val):
    txt = str(val).replace('　', ' ')
    return re.sub(r'\s+', '', txt).strip()

# Read Excel file with correct header
excel_path = 'テストデータ_勤務表　勤務時間_トライアル.xlsx'
df_sheet = pd.read_excel(excel_path, sheet_name='R7.6', header=0, dtype=str).fillna('')

# Examine actual shift codes in the data
print("=== Examining shift codes in R7.6 sheet ===")
print(f"Sheet shape: {df_sheet.shape}")

# Find date columns (skip first 3 columns which are staff info)
date_cols = []
for col in df_sheet.columns[3:]:  # Skip first 3 columns 
    if isinstance(col, pd.Timestamp) or str(col).startswith('2025'):
        date_cols.append(col)

print(f"Found {len(date_cols)} date columns")

# Collect all shift codes from date columns
all_shift_codes = []
for _, row in df_sheet.iterrows():
    for col in date_cols:
        shift_code = _normalize(str(row[col]))
        if shift_code and shift_code not in ['', 'nan', 'NaN']:
            all_shift_codes.append(shift_code)

# Count shift codes
code_counts = Counter(all_shift_codes)
print(f"\nUnique shift codes found in data:")
for code, count in code_counts.most_common():
    print(f"  '{code}': {count} times")

print(f"\nTotal shift code entries: {len(all_shift_codes)}")

# Compare with shift patterns from 勤務区分 sheet
print(f"\n=== Shift patterns from 勤務区分 sheet ===")
try:
    wt_df = pd.read_excel(excel_path, sheet_name='勤務区分', dtype=str).fillna('')
    code_col = None
    for col in ['記号', 'コード', '勤務記号', 'code']:
        if col in wt_df.columns:
            code_col = col
            break
    
    if code_col:
        defined_codes = []
        for _, row in wt_df.iterrows():
            code = _normalize(row[code_col])
            if code:
                defined_codes.append(code)
        
        print("Defined shift patterns:")
        for code in defined_codes:
            print(f"  '{code}'")
        
        # Check which codes are missing
        missing_codes = set(all_shift_codes) - set(defined_codes)
        if missing_codes:
            print(f"\nCodes in data but not in shift patterns:")
            for code in missing_codes:
                print(f"  '{code}' (appears {code_counts[code]} times)")
        
        unknown_patterns = set(defined_codes) - set(all_shift_codes)
        if unknown_patterns:
            print(f"\nCodes in patterns but not used in data:")
            for code in unknown_patterns:
                print(f"  '{code}'")
                
    else:
        print("Could not find code column in 勤務区分 sheet")

except Exception as e:
    print(f"Error reading 勤務区分 sheet: {e}")

# Show sample of actual data
print(f"\n=== Sample data from first few rows ===")
for i in range(min(5, len(df_sheet))):
    staff_name = df_sheet.iloc[i, 0] if len(df_sheet.columns) > 0 else 'N/A'
    row_codes = []
    for col in date_cols[:5]:  # First 5 date columns
        code = _normalize(str(df_sheet.iloc[i][col]))
        if code and code not in ['', 'nan', 'NaN']:
            row_codes.append(f"{str(col)[:10]}:{code}")
    print(f"Row {i} ({staff_name}): {row_codes}")