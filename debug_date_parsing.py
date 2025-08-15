import pandas as pd
import re
from shift_suite.tasks.utils import _parse_as_date

def _normalize(val):
    txt = str(val).replace('　', ' ')
    return re.sub(r'\s+', '', txt).strip()

# Read Excel file with correct header  
excel_path = 'テストデータ_勤務表　勤務時間_トライアル.xlsx'
df_sheet = pd.read_excel(excel_path, sheet_name='R7.6', header=0, dtype=str).fillna('')

print("=== Date Column Processing Debug ===")

# Find date columns (skip first 3 which are staff info)
date_columns = []
for i, col in enumerate(df_sheet.columns[3:10], 3):  # Check first 7 date columns
    print(f"\nColumn {i}:")
    print(f"  Raw column: {repr(col)} (type: {type(col)})")
    
    # Test _parse_as_date on raw column
    parsed_raw = _parse_as_date(col)
    print(f"  _parse_as_date(raw): {parsed_raw}")
    
    # Test normalization
    normalized = _normalize(col)
    print(f"  After _normalize: {repr(normalized)}")
    
    # Test _parse_as_date on normalized
    parsed_normalized = _parse_as_date(normalized)
    print(f"  _parse_as_date(normalized): {parsed_normalized}")
    
    # Check if this would be included as a date column
    if parsed_raw or parsed_normalized:
        date_columns.append(col)
        print(f"  → WOULD BE INCLUDED as date column")
    else:
        print(f"  → WOULD BE EXCLUDED")

print(f"\nTotal date columns that would be recognized: {len(date_columns)}")

# Test the specific issue: try reading without dtype=str
print(f"\n=== Testing different reading methods ===")

# Method 1: Current method (with dtype=str)
df1 = pd.read_excel(excel_path, sheet_name='R7.6', header=0, dtype=str).fillna('')
sample_col1 = df1.columns[3] if len(df1.columns) > 3 else None
print(f"Method 1 (dtype=str): {repr(sample_col1)} -> {_parse_as_date(sample_col1)}")

# Method 2: Without dtype=str (let pandas infer types)
df2 = pd.read_excel(excel_path, sheet_name='R7.6', header=0).fillna('')
sample_col2 = df2.columns[3] if len(df2.columns) > 3 else None
print(f"Method 2 (infer types): {repr(sample_col2)} -> {_parse_as_date(sample_col2)}")

# Test if the second method works better
if sample_col2:
    print(f"Method 2 sample_col2 type: {type(sample_col2)}")
    if hasattr(sample_col2, 'date'):
        print(f"Method 2 has date() method: {sample_col2.date()}")