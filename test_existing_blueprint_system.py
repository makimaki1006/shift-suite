#!/usr/bin/env python3
"""
既存ブループリント分析システムのテスト実行
デイ_テスト用データ_休日精緻.xlsxで何個制約を発見できるかテスト
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# 既存システムをインポート
try:
    from shift_suite.tasks.advanced_blueprint_engine_v2 import AdvancedBlueprintEngineV2
    from shift_suite.tasks.blueprint_analyzer import FactExtractor
    from shift_suite.tasks.mece_fact_extractor import MECEFactExtractor
    BLUEPRINT_AVAILABLE = True
except ImportError as e:
    print(f"Blueprint system import failed: {e}")
    BLUEPRINT_AVAILABLE = False

# 直接Excel読み込み
from direct_excel_reader import DirectExcelReader

def convert_excel_to_blueprint_format(excel_file: str) -> pd.DataFrame:
    """ExcelデータをBlueprintシステムが期待する形式に変換"""
    print(f"Converting {excel_file} to blueprint format...")
    
    # Excel読み込み
    reader = DirectExcelReader()
    data = reader.read_xlsx_as_zip(excel_file)
    
    if not data:
        print("Failed to read Excel data")
        return pd.DataFrame()
    
    # データ構造の理解
    print(f"Raw data: {len(data)} rows x {len(data[0]) if data else 0} columns")
    
    # ヘッダー行の特定（1行目がヘッダーと仮定）
    headers = data[0]
    rows = data[1:]
    
    # Long形式データフレーム作成
    long_records = []
    
    # 各行（スタッフ）を処理
    for row in rows:
        if not row or len(row) == 0:
            continue
        
        staff_name = str(row[0]).strip() if row[0] else ""
        if not staff_name or staff_name in ['', 'None', 'nan']:
            continue
            
        # 各列（日付/シフト）を処理
        for col_idx in range(1, min(len(row), len(headers))):
            if col_idx < len(headers) and row[col_idx]:
                date_header = headers[col_idx] if col_idx < len(headers) else f"Day{col_idx}"
                shift_code = str(row[col_idx]).strip()
                
                if shift_code and shift_code not in ['', 'None', 'nan']:
                    # 日付を作成（2024年1月として仮定）
                    base_date = datetime(2024, 1, col_idx)
                    
                    long_records.append({
                        'ds': base_date,
                        'staff': staff_name,
                        'code': shift_code,
                        'role': 'staff',  # デフォルト役割
                        'parsed_slots_count': 1 if shift_code else 0,
                        'workload': 1.0,
                        'date': base_date.date()
                    })
    
    long_df = pd.DataFrame(long_records)
    
    if long_df.empty:
        print("No valid shift data found")
        return long_df
    
    print(f"Converted to long format: {len(long_df)} records")
    print(f"Unique staff: {long_df['staff'].nunique()}")
    print(f"Unique shift codes: {long_df['code'].nunique()}")
    print(f"Shift codes: {sorted(long_df['code'].unique())}")
    
    return long_df

def test_blueprint_system():
    """既存Blueprintシステムのテスト実行"""
    print("=" * 80)
    print("既存ブループリント分析システム テスト実行")
    print("=" * 80)
    
    if not BLUEPRINT_AVAILABLE:
        print("Blueprint system not available")
        return
    
    # テストファイル
    test_file = "デイ_テスト用データ_休日精緻.xlsx"
    
    if not Path(test_file).exists():
        print(f"Test file not found: {test_file}")
        return
    
    # データ変換
    long_df = convert_excel_to_blueprint_format(test_file)
    
    if long_df.empty:
        print("No data to analyze")
        return
    
    print(f"\n=== データ概要 ===")
    print(f"レコード数: {len(long_df)}")
    print(f"スタッフ数: {long_df['staff'].nunique()}")
    print(f"シフトコード数: {long_df['code'].nunique()}")
    print(f"期間: {long_df['ds'].min()} ～ {long_df['ds'].max()}")
    
    # Blueprint V2 エンジン実行
    try:
        print(f"\n=== Blueprint V2 分析実行 ===")
        engine = AdvancedBlueprintEngineV2()
        results = engine.run_full_blueprint_analysis(long_df)
        
        print(f"\n=== 分析結果 ===")
        for category, data in results.items():
            if isinstance(data, dict):
                constraints_count = 0
                if 'human_readable' in data:
                    human_readable = data['human_readable']
                    if isinstance(human_readable, dict):
                        for subcategory, items in human_readable.items():
                            if isinstance(items, list):
                                constraints_count += len(items)
                            elif isinstance(items, dict):
                                constraints_count += len(items)
                
                if 'machine_readable' in data:
                    machine_readable = data['machine_readable']
                    if isinstance(machine_readable, list):
                        constraints_count += len(machine_readable)
                    elif isinstance(machine_readable, dict):
                        constraints_count += len(machine_readable)
                
                print(f"{category}: {constraints_count}個の制約/パターン発見")
        
        # MECE事実抽出結果の詳細表示
        mece_facility = results.get('mece_facility_facts', {})
        if mece_facility:
            human_readable = mece_facility.get('human_readable', {})
            print(f"\n=== 軸1: 施設ルール詳細 ===")
            for category, items in human_readable.items():
                if isinstance(items, list) and items:
                    print(f"\n{category} ({len(items)}個):")
                    for i, item in enumerate(items[:5], 1):  # 最初の5個を表示
                        if isinstance(item, dict):
                            description = item.get('description', item.get('法則', str(item)))
                            confidence = item.get('confidence', item.get('確信度', 'N/A'))
                            print(f"  {i}. {description} (確信度: {confidence})")
        
        # スタッフルール結果
        mece_staff = results.get('mece_staff_facts', {})
        if mece_staff:
            human_readable = mece_staff.get('human_readable', {})
            print(f"\n=== 軸2: スタッフルール詳細 ===")
            total_staff_constraints = 0
            for category, items in human_readable.items():
                if isinstance(items, list):
                    total_staff_constraints += len(items)
                    if items:
                        print(f"{category}: {len(items)}個")
            print(f"スタッフルール総数: {total_staff_constraints}個")
        
        # 時間・カレンダールール結果
        mece_time = results.get('mece_time_calendar_facts', {})
        if mece_time:
            human_readable = mece_time.get('human_readable', {})
            print(f"\n=== 軸3: 時間・カレンダールール詳細 ===")
            total_time_constraints = 0
            for category, items in human_readable.items():
                if isinstance(items, list):
                    total_time_constraints += len(items)
                    if items:
                        print(f"{category}: {len(items)}個")
            print(f"時間ルール総数: {total_time_constraints}個")
        
        # 総制約数計算
        total_constraints = 0
        for category, data in results.items():
            if isinstance(data, dict) and 'human_readable' in data:
                human_readable = data['human_readable']
                if isinstance(human_readable, dict):
                    for items in human_readable.values():
                        if isinstance(items, list):
                            total_constraints += len(items)
        
        print(f"\n=== 最終結果 ===")
        print(f"🎯 発見された制約・パターン総数: {total_constraints}個")
        
        if total_constraints >= 100:
            print("✅ 100個以上の制約発見 - 実用レベル達成！")
        elif total_constraints >= 50:
            print("⚠️ 50個以上の制約発見 - 中程度の性能")
        else:
            print("❌ 制約発見数不足 - 改善が必要")
        
        return total_constraints
        
    except Exception as e:
        print(f"Blueprint analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    result_count = test_blueprint_system()
    
    if result_count:
        print(f"\n既存システムは {result_count}個の制約を発見しました")
        print("これは我々の新システム（8個）を大幅に上回る性能です")
    else:
        print("\n既存システムのテストに失敗しました")