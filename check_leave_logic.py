#!/usr/bin/env python3
"""Check leave detection logic in io_excel.py"""

import re

# Copy the logic from io_excel.py
LEAVE_CODES = {
    "×": "希望休",
    "希": "希望休",  # 追加: 希望休コード
    "休": "施設休",
    "有": "有給",
    "研": "研修",
    "欠": "欠勤",
    "特": "特休",
    "組": "組織休",
    "P有": "有給",
}

HOLIDAY_TYPE_KEYWORDS_MAP = {
    "有給": ["有給", "有休", "P有"],
    "希望休": ["希望休"],
    "その他休暇": ["休暇", "休み", "組織休", "施設休", "特休", "欠勤", "研修"],
}
DEFAULT_HOLIDAY_TYPE = "通常勤務"

def _normalize(val):
    txt = str(val).replace("　", " ")
    return re.sub(r"\s+", "", txt).strip()

def _is_leave_code(code):
    code_normalized = _normalize(code)
    return code_normalized in LEAVE_CODES

def _determine_holiday_type_from_code(code):
    code_normalized = _normalize(code)
    return LEAVE_CODES.get(code_normalized)

# Test the logic
test_codes = ["休", "有", "希", "×", "L", "2F", "3F", "", "研", "欠", "特", "組", "P有"]

print("LEAVE CODE DETECTION TEST")
print("=" * 60)
print(f"Defined LEAVE_CODES: {list(LEAVE_CODES.keys())}")
print("\nTesting codes:")
print("-" * 60)

for code in test_codes:
    is_leave = _is_leave_code(code)
    holiday_type = _determine_holiday_type_from_code(code)
    print(f"Code: '{code:3s}' -> is_leave: {str(is_leave):5s}, holiday_type: {holiday_type if holiday_type else 'None'}")

print("\nISSUE ANALYSIS:")
print("-" * 60)
print("1. Code '希' is NOT in LEAVE_CODES dictionary")
print("2. This means _is_leave_code('希') returns False")
print("3. Therefore, records with '希' are treated as regular work, not leave")
print("\nSOLUTION: Add '希' to LEAVE_CODES dictionary")
print("LEAVE_CODES['希'] = '希望休'")