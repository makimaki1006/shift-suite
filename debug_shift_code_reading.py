#!/usr/bin/env python3
"""
勤務コード読み取り問題の詳細デバッグ
"""

import sys
import pandas as pd
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shift_suite.tasks.io_excel import load_shift_patterns

def debug_shift_code_reading():
    """勤務コード読み取りの詳細デバッグ"""
    
    print("Shift Code Reading Debug")
    print("=" * 40)
    
    test_file = project_root / "デイ_テスト用データ_休日精緻.xlsx"
    if not test_file.exists():
        print(f"Error: Test file not found: {test_file}")
        return
    
    print(f"Test file: {test_file.name}")
    
    try:
        # 勤務区分シートを直接読み込み
        print("\n1. Reading raw worktype sheet...")
        df_raw = pd.read_excel(test_file, sheet_name="勤務区分", dtype=str).fillna("")
        
        print(f"Raw sheet shape: {df_raw.shape}")
        print(f"Raw columns: {df_raw.columns.tolist()}")
        print(f"First 10 rows:")
        print(df_raw.head(10).to_string())
        
        # load_shift_patterns関数でどう処理されるか確認
        print("\n2. Processing with load_shift_patterns...")
        wt_df, code2slots = load_shift_patterns(test_file, slot_minutes=30)
        
        print(f"Processed worktype DataFrame:")
        print(wt_df.to_string())
        
        print(f"\nCode to slots mapping:")
        for code, slots in code2slots.items():
            print(f"  {code}: {len(slots)} slots -> {slots[:3] if len(slots) > 3 else slots}")
        
        # 具体的に「朝」コードを詳しく見る
        print(f"\n3. Detailed analysis of '朝' code...")
        asa_rows = df_raw[df_raw.iloc[:, 0].str.contains('朝', na=False)]
        if not asa_rows.empty:
            print(f"Raw '朝' rows:")
            print(asa_rows.to_string())
            
            # 各列の内容
            for idx, row in asa_rows.iterrows():
                print(f"\nRow {idx}:")
                for col_idx, val in enumerate(row):
                    print(f"  Column {col_idx} ('{df_raw.columns[col_idx]}'): '{val}'")
        
        # 時刻変換の確認
        print(f"\n4. Time conversion test...")
        from shift_suite.tasks.io_excel import _to_hhmm
        test_times = ["09:00:00", "18:00:00", "08:30:00", "17:30:00"]
        for time_val in test_times:
            converted = _to_hhmm(time_val)
            print(f"  {time_val} -> {converted}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_shift_code_reading()