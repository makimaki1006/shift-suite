#!/usr/bin/env python3
"""
レコード生成プロセスの詳細デバッグ
"""

import sys
import pandas as pd
from pathlib import Path
import datetime as dt

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_record_generation_detailed():
    """レコード生成の詳細デバッグ"""
    
    print("=== Detailed Record Generation Debug ===")
    
    test_file = project_root / "デイ_テスト用データ_休日精緻.xlsx"
    
    try:
        # 1. load_shift_patterns実行
        print("1. Loading shift patterns...")
        from shift_suite.tasks.io_excel import load_shift_patterns, SHEET_COL_ALIAS, _normalize, DOW_TOKENS, DEFAULT_HOLIDAY_TYPE
        
        wt_df, code2slots = load_shift_patterns(test_file, slot_minutes=30)
        print(f"   Loaded {len(code2slots)} shift codes")
        
        # 2. シート読み込み
        print("\n2. Loading R7.2 sheet...")
        df_sheet = pd.read_excel(
            test_file,
            sheet_name="R7.2",
            header=0,
            dtype=str,
        ).fillna("")
        print(f"   Sheet shape: {df_sheet.shape}")
        
        # 3. 列名マッピング
        print("\n3. Column mapping...")
        print(f"   Before: {df_sheet.columns[:5].tolist()}...")
        df_sheet.columns = [
            SHEET_COL_ALIAS.get(_normalize(str(c)), _normalize(str(c)))
            for c in df_sheet.columns
        ]
        print(f"   After: {df_sheet.columns[:5].tolist()}...")
        
        # 4. 必須列確認
        print("\n4. Required columns check...")
        has_staff = "staff" in df_sheet.columns
        has_role = "role" in df_sheet.columns
        print(f"   staff: {has_staff}, role: {has_role}")
        
        if not has_staff or not has_role:
            print("   ❌ Missing required columns!")
            return
        
        # 5. 日付列候補
        print("\n5. Date column candidates...")
        date_cols_candidate = [
            c
            for c in df_sheet.columns
            if c not in ("staff", "role", "employment")
            and not str(c).startswith("Unnamed:")
        ]
        print(f"   Found {len(date_cols_candidate)} candidates")
        print(f"   First 5: {date_cols_candidate[:5]}")
        
        # 6. 日付解析
        print("\n6. Date parsing...")
        from shift_suite.tasks.utils import _parse_as_date
        
        date_col_map = {}
        for c in date_cols_candidate:
            parsed_dt = _parse_as_date(str(c))
            if parsed_dt:
                date_col_map[str(c)] = parsed_dt
                print(f"   OK '{c}' -> {parsed_dt}")
            else:
                print(f"   NG '{c}' -> failed to parse")
        
        print(f"   Successfully parsed {len(date_col_map)} date columns")
        
        if len(date_col_map) == 0:
            print("   ERROR: No date columns parsed!")
            return
        
        # 7. 実際のデータ行処理（詳細）
        print("\n7. Processing data rows...")
        
        records = []
        code_to_start_time = {}
        for _, row in wt_df.iterrows():
            code = row.get("code")
            start_parsed = row.get("start_parsed")
            if code and start_parsed and isinstance(start_parsed, str):
                try:
                    code_to_start_time[code] = dt.datetime.strptime(
                        start_parsed, "%H:%M"
                    ).time()
                except (ValueError, TypeError):
                    code_to_start_time[code] = None
            else:
                code_to_start_time[code] = None
        
        total_rows = len(df_sheet)
        valid_rows = 0
        processed_codes = set()
        
        for idx, row_data in df_sheet.iterrows():
            staff = _normalize(row_data.get("staff", ""))
            role = _normalize(row_data.get("role", ""))
            employment = _normalize(row_data.get("employment", ""))
            
            # スタッフ行フィルタリング
            if (
                staff in DOW_TOKENS
                or role in DOW_TOKENS
                or (staff == "" and role == "")
            ):
                print(f"   Row {idx}: Skipped (empty or dow token) - staff='{staff}', role='{role}'")
                continue
            
            valid_rows += 1
            if valid_rows <= 3:  # 最初の3行のみ詳細表示
                print(f"   Row {idx}: Processing staff='{staff}', role='{role}', employment='{employment}'")
            
            row_record_count = 0
            
            for col_name_original_str in date_cols_candidate:
                shift_code_raw = row_data.get(col_name_original_str, "")
                code_val = _normalize(str(shift_code_raw))
                
                if code_val in ("", "nan", "NaN"):
                    # 空コードレコード生成
                    date_val_parsed_dt_date = date_col_map.get(str(col_name_original_str))
                    if date_val_parsed_dt_date is not None:
                        record_datetime_for_zero_slot = dt.datetime.combine(
                            date_val_parsed_dt_date, dt.time(0, 0)
                        )
                        records.append({
                            "ds": record_datetime_for_zero_slot,
                            "staff": staff,
                            "role": role,
                            "employment": employment,
                            "code": "",
                            "holiday_type": DEFAULT_HOLIDAY_TYPE,
                            "parsed_slots_count": 0,
                        })
                        row_record_count += 1
                    continue
                    
                if code_val in DOW_TOKENS:
                    continue
                    
                if code_val not in code2slots:
                    if valid_rows <= 3:
                        print(f"     Date {col_name_original_str}: Unknown code '{code_val}'")
                    continue
                
                processed_codes.add(code_val)
                
                date_val_parsed_dt_date = date_col_map.get(str(col_name_original_str))
                if date_val_parsed_dt_date is None:
                    continue
                
                current_code_slots_list = code2slots.get(code_val, [])
                wt_row_series = (
                    wt_df[wt_df["code"] == code_val].iloc[0]
                    if not wt_df[wt_df["code"] == code_val].empty
                    else None
                )
                holiday_type_for_record = (
                    wt_row_series["holiday_type"]
                    if wt_row_series is not None
                    else DEFAULT_HOLIDAY_TYPE
                )
                
                if wt_row_series is not None and wt_row_series.get("is_leave_code", False):
                    parsed_slots_count_for_record = 0
                else:
                    parsed_slots_count_for_record = (
                        wt_row_series["parsed_slots_count"]
                        if wt_row_series is not None
                        else 0
                    )
                
                if not current_code_slots_list:
                    # 休暇レコード生成
                    record_datetime_for_zero_slot = dt.datetime.combine(
                        date_val_parsed_dt_date, dt.time(0, 0)
                    )
                    records.append({
                        "ds": record_datetime_for_zero_slot,
                        "staff": staff,
                        "role": role,
                        "employment": employment,
                        "code": code_val,
                        "holiday_type": holiday_type_for_record,
                        "parsed_slots_count": parsed_slots_count_for_record,
                    })
                    row_record_count += 1
                    if valid_rows <= 3:
                        print(f"     Date {col_name_original_str}: Leave record for '{code_val}'")
                    continue
                
                # 勤務レコード生成
                shift_start_time = code_to_start_time.get(code_val)
                for t_slot_val in current_code_slots_list:
                    try:
                        slot_time = dt.datetime.strptime(t_slot_val, "%H:%M").time()
                        current_date = date_val_parsed_dt_date
                        if shift_start_time and slot_time < shift_start_time:
                            current_date += dt.timedelta(days=1)
                        
                        record_datetime = dt.datetime.combine(current_date, slot_time)
                        records.append({
                            "ds": record_datetime,
                            "staff": staff,
                            "role": role,
                            "employment": employment,
                            "code": code_val,
                            "holiday_type": holiday_type_for_record,
                            "parsed_slots_count": parsed_slots_count_for_record,
                        })
                        row_record_count += 1
                    except ValueError as e_time:
                        print(f"     Time slot parse error: {e_time}")
                        continue
            
            if valid_rows <= 3:
                print(f"     Generated {row_record_count} records for this row")
        
        print(f"\n8. Generation summary:")
        print(f"   Total data rows: {total_rows}")
        print(f"   Valid staff rows: {valid_rows}")
        print(f"   Generated records: {len(records)}")
        print(f"   Processed codes: {sorted(processed_codes)}")
        
        if len(records) == 0:
            print("   ERROR: No records generated - this is the root cause!")
        else:
            print("   SUCCESS: Records successfully generated")
            
            # レコード内容のサンプル表示
            print(f"\n9. Sample records:")
            for i, record in enumerate(records[:5]):
                print(f"   {i+1}: {record['ds']} | {record['staff']} | {record['code']} | slots: {record['parsed_slots_count']}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_record_generation_detailed()