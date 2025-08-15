#!/usr/bin/env python3
"""
データ入稿フェーズの深い思考検証
全ての入稿プロセスを段階的に検証
"""

import pandas as pd
from pathlib import Path
import sys
import os
import json
from datetime import datetime, timedelta

# パスを追加
sys.path.insert(0, os.getcwd())

from shift_suite.tasks.io_excel import ingest_excel, load_shift_patterns

def deep_verify_data_ingestion():
    """データ入稿フェーズの包括的検証"""
    excel_path = Path("ショート_テスト用データ.xlsx")
    
    if not excel_path.exists():
        print(f"ERROR: Test file not found: {excel_path}")
        return
    
    print("=== データ入稿フェーズ 深い思考検証 ===")
    
    # 1. Excelファイル構造の詳細分析
    print("\n【1. Excelファイル構造分析】")
    excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
    sheet_names = excel_file.sheet_names
    print(f"シート構成: {sheet_names}")
    
    # 勤務区分シートの詳細検証
    print("\n【1-1. 勤務区分シート検証】")
    wt_raw = pd.read_excel(excel_path, sheet_name="勤務区分", dtype=str).fillna("")
    print(f"勤務区分シート形状: {wt_raw.shape}")
    print(f"列名: {wt_raw.columns.tolist()}")
    
    # 各勤務コードの詳細分析
    print("\n勤務コード詳細分析:")
    for i, row in wt_raw.iterrows():
        code = row.iloc[0] if len(row) > 0 else "N/A"
        start = row.iloc[1] if len(row) > 1 else "N/A"
        end = row.iloc[2] if len(row) > 2 else "N/A"
        remarks = row.iloc[3] if len(row) > 3 else "N/A"
        print(f"  行{i+2}: '{code}' | {start} - {end} | 備考: '{remarks}'")
    
    # 実績シートの詳細検証
    shift_sheets = [s for s in sheet_names if "勤務" not in s]
    print(f"\n【1-2. 実績シート検証】")
    print(f"実績シート: {shift_sheets}")
    
    for sheet_name in shift_sheets:
        print(f"\n=== シート: {sheet_name} ===")
        df_raw = pd.read_excel(excel_path, sheet_name=sheet_name, header=0, dtype=str).fillna("")
        print(f"シート形状: {df_raw.shape}")
        print(f"列名サンプル: {df_raw.columns.tolist()[:10]}...")
        
        # スタッフ情報の検証
        staff_col = "氏名" if "氏名" in df_raw.columns else None
        role_col = "職種" if "職種" in df_raw.columns else None
        employment_col = "雇用形態" if "雇用形態" in df_raw.columns else None
        
        print(f"スタッフ列: {staff_col}")
        print(f"職種列: {role_col}")
        print(f"雇用形態列: {employment_col}")
        
        if staff_col:
            staff_list = df_raw[staff_col].dropna().astype(str)
            staff_list = staff_list[staff_list != ""]
            unique_staff = staff_list.unique()
            print(f"総スタッフ数: {len(unique_staff)}")
            print(f"スタッフサンプル: {unique_staff[:5].tolist()}")
        
        if role_col:
            role_list = df_raw[role_col].dropna().astype(str)
            role_list = role_list[role_list != ""]
            unique_roles = role_list.unique()
            print(f"職種一覧: {unique_roles.tolist()}")
        
        # 日付列の検証
        date_cols = [c for c in df_raw.columns if c not in [staff_col, role_col, employment_col] 
                    and not str(c).startswith("Unnamed:")]
        print(f"日付列数: {len(date_cols)}")
        print(f"日付列サンプル: {date_cols[:5]}")
        
        # 各日付列のデータ分析
        print("\n日付列データ分析:")
        for i, col in enumerate(date_cols[:3]):  # 最初の3列のみ詳細分析
            col_data = df_raw[col].dropna().astype(str)
            col_data = col_data[col_data != ""]
            unique_codes = col_data.unique()
            print(f"  {col}: {len(unique_codes)}種類のコード - {unique_codes.tolist()}")
    
    # 2. load_shift_patterns関数の詳細検証
    print("\n【2. 勤務パターン読み込み検証】")
    wt_df, code2slots = load_shift_patterns(excel_path, slot_minutes=30)
    print(f"勤務パターンDF形状: {wt_df.shape}")
    print(f"勤務パターンDF列名: {wt_df.columns.tolist()}")
    
    print("\n詳細な勤務パターン分析:")
    for _, row in wt_df.iterrows():
        code = row['code']
        start_orig = row['start_original']
        end_orig = row['end_original']
        start_parsed = row['start_parsed']
        end_parsed = row['end_parsed']
        slot_count = row['parsed_slots_count']
        holiday_type = row['holiday_type']
        is_leave = row.get('is_leave_code', False)
        
        print(f"  {code}: {start_orig}→{start_parsed} | {end_orig}→{end_parsed} | "
              f"スロット{slot_count}個 | {holiday_type} | 休暇: {is_leave}")
        
        # スロット展開の確認
        if code in code2slots and len(code2slots[code]) > 0:
            slots = code2slots[code]
            print(f"    展開スロット: {slots[:5]}{'...' if len(slots) > 5 else ''}")
    
    # 3. ingest_excel関数の詳細検証
    print("\n【3. データ入稿処理検証】")
    try:
        long_df, wt_df_result, unknown_codes = ingest_excel(
            excel_path,
            shift_sheets=shift_sheets,
            header_row=0,
            slot_minutes=30,
            year_month_cell_location="D1"
        )
        
        print(f"生成レコード数: {len(long_df)}")
        print(f"列構成: {long_df.columns.tolist()}")
        print(f"未知コード: {unknown_codes}")
        
        # データ型確認
        print("\nデータ型分析:")
        print(long_df.dtypes)
        
        # 日付範囲確認
        print(f"\n日付範囲:")
        print(f"  最小日付: {long_df['ds'].min()}")
        print(f"  最大日付: {long_df['ds'].max()}")
        print(f"  ユニーク日数: {long_df['ds'].dt.date.nunique()}")
        
        # コード分布確認
        print(f"\nコード分布:")
        code_dist = long_df['code'].value_counts()
        for code, count in code_dist.items():
            print(f"  '{code}': {count}件")
        
        # 休暇タイプ分布確認
        print(f"\n休暇タイプ分布:")
        holiday_dist = long_df['holiday_type'].value_counts()
        for htype, count in holiday_dist.items():
            print(f"  {htype}: {count}件")
        
        # 時間帯分析
        print(f"\n時間帯分析:")
        long_df['hour'] = pd.to_datetime(long_df['ds']).dt.hour
        hour_dist = long_df['hour'].value_counts().sort_index()
        for hour, count in hour_dist.items():
            print(f"  {hour:02d}時台: {count}件")
        
        # 特に重要な夜勤時間帯の詳細分析
        print(f"\n【4. 夜勤時間帯詳細分析】")
        night_hours = [0, 1, 2, 3, 4, 5]
        night_data = long_df[long_df['hour'].isin(night_hours)]
        print(f"夜勤時間帯データ数: {len(night_data)}")
        
        night_code_dist = night_data['code'].value_counts()
        print("夜勤時間帯コード分布:")
        for code, count in night_code_dist.items():
            print(f"  '{code}': {count}件")
        
        # 明番コード「明」の詳細分析
        if '明' in night_data['code'].values:
            dawn_data = night_data[night_data['code'] == '明']
            print(f"\n明番データ詳細分析:")
            print(f"  明番レコード数: {len(dawn_data)}")
            
            dawn_hour_dist = dawn_data['hour'].value_counts().sort_index()
            print("  時間帯分布:")
            for hour, count in dawn_hour_dist.items():
                print(f"    {hour:02d}時台: {count}件")
            
            # 明番の職種分布
            dawn_role_dist = dawn_data['role'].value_counts()
            print("  職種分布:")
            for role, count in dawn_role_dist.items():
                print(f"    {role}: {count}件")
        
        # 5. データ品質チェック
        print(f"\n【5. データ品質チェック】")
        
        # 欠損値チェック
        print("欠損値チェック:")
        for col in long_df.columns:
            null_count = long_df[col].isnull().sum()
            if null_count > 0:
                print(f"  {col}: {null_count}件の欠損値")
        
        # 重複チェック
        duplicates = long_df.duplicated().sum()
        print(f"重複レコード: {duplicates}件")
        
        # 日付の連続性チェック
        unique_dates = sorted(long_df['ds'].dt.date.unique())
        print(f"日付連続性チェック:")
        print(f"  期待日数: 30日 (2025年6月)")
        print(f"  実際日数: {len(unique_dates)}日")
        
        if len(unique_dates) == 30:
            print("  ✓ 日付連続性OK")
        else:
            print(f"  ⚠ 日付に欠損または重複があります")
            
    except Exception as e:
        print(f"データ入稿処理エラー: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== データ入稿フェーズ検証完了 ===")

if __name__ == "__main__":
    deep_verify_data_ingestion()