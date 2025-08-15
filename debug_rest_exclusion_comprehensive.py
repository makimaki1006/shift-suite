#!/usr/bin/env python3
"""
総合的な休暇除外デバッグスクリプト
データフローの全段階で休暇データがどのように扱われているかを検証
"""

import pandas as pd
import sys
import os
import json
from pathlib import Path

# Add shift_suite to path
sys.path.insert(0, str(Path(__file__).parent))

def debug_excel_rest_data():
    """Excelファイル内の休暇データを直接分析"""
    print("=== 1. Excelファイル内の休暇データ分析 ===")
    
    excel_file = "ショート_テスト用データ.xlsx"
    if not os.path.exists(excel_file):
        print(f"❌ テストファイルが見つかりません: {excel_file}")
        return None
        
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file)
        print(f"📊 Excel shape: {df.shape}")
        print(f"📊 Columns: {list(df.columns)}")
        
        # Look for staff-related columns
        staff_columns = [col for col in df.columns if 'スタッフ' in col or 'staff' in col.lower()]
        print(f"📊 Staff columns found: {staff_columns}")
        
        if staff_columns:
            staff_col = staff_columns[0]
            unique_values = df[staff_col].value_counts()
            print(f"\n📊 Unique values in {staff_col}:")
            print(unique_values.head(20))
            
            # Count rest patterns
            rest_patterns = ['×', 'X', 'x', '休', '休み', '休暇', 'OFF', 'off', 'Off', '-', '−', '―']
            rest_counts = {}
            
            for pattern in rest_patterns:
                if df[staff_col].dtype == 'object':
                    count = df[staff_col].str.contains(pattern, na=False).sum()
                else:
                    count = (df[staff_col] == pattern).sum()
                    
                if count > 0:
                    rest_counts[pattern] = count
                    
            print(f"\n✅ 休暇パターン検出結果: {rest_counts}")
            return df, staff_col, rest_counts
        else:
            print("❌ スタッフ関連の列が見つかりません")
            return None
            
    except Exception as e:
        print(f"❌ Excelファイル読み込みエラー: {e}")
        return None

def debug_intermediate_data():
    """intermediate_data.parquetの休暇データを分析"""
    print("\n=== 2. intermediate_data.parquet分析 ===")
    
    # Check in current directory and temp directories
    possible_paths = [
        "analysis_results/out_p25_based/intermediate_data.parquet",
        "temp_analysis_results/out_p25_based/intermediate_data.parquet",
        "analysis_results_20/out_p25_based/intermediate_data.parquet",
        "/tmp/tmpdl5z1z7n/motogi_short/out_p25_based/intermediate_data.parquet"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"📂 Found intermediate_data at: {path}")
            try:
                df = pd.read_parquet(path)
                print(f"📊 Shape: {df.shape}")
                print(f"📊 Columns: {list(df.columns)}")
                
                if 'staff' in df.columns:
                    print(f"📊 Unique staff count: {df['staff'].nunique()}")
                    
                    # Check for rest patterns in staff names
                    rest_patterns = ['×', 'X', 'x', '休', '休み', '休暇', 'OFF', 'off', 'Off', '-', '−', '―']
                    rest_in_staff = {}
                    
                    for pattern in rest_patterns:
                        count = df['staff'].str.contains(pattern, na=False).sum()
                        if count > 0:
                            rest_in_staff[pattern] = count
                            
                    print(f"✅ intermediate_data内の休暇パターン: {rest_in_staff}")
                
                if 'parsed_slots_count' in df.columns:
                    zero_slots = (df['parsed_slots_count'] == 0).sum()
                    print(f"📊 parsed_slots_count=0のレコード: {zero_slots}")
                    
                    if zero_slots > 0:
                        print(f"📊 Zero slots sample:")
                        zero_sample = df[df['parsed_slots_count'] == 0][['staff', 'parsed_slots_count']].head(10)
                        print(zero_sample)
                
                return df
                
            except Exception as e:
                print(f"❌ エラー: {e}")
        else:
            print(f"⚠️ Not found: {path}")
    
    print("❌ intermediate_data.parquet が見つかりません")
    return None

def debug_pre_aggregated_data():
    """pre_aggregated_data.parquetの休暇データを分析"""
    print("\n=== 3. pre_aggregated_data.parquet分析 ===")
    
    possible_paths = [
        "analysis_results/out_p25_based/pre_aggregated_data.parquet",
        "temp_analysis_results/out_p25_based/pre_aggregated_data.parquet",
        "analysis_results_20/out_p25_based/pre_aggregated_data.parquet",
        "/tmp/tmpdl5z1z7n/motogi_short/out_p25_based/pre_aggregated_data.parquet"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"📂 Found pre_aggregated_data at: {path}")
            try:
                df = pd.read_parquet(path)
                print(f"📊 Shape: {df.shape}")
                print(f"📊 Columns: {list(df.columns)}")
                
                if 'staff_count' in df.columns:
                    print(f"📊 staff_count stats: min={df['staff_count'].min()}, max={df['staff_count'].max()}")
                    print(f"📊 Zero staff_count records: {(df['staff_count'] == 0).sum()}")
                
                print(f"📊 Sample data:")
                print(df.head(3))
                
                return df
                
            except Exception as e:
                print(f"❌ エラー: {e}")
        else:
            print(f"⚠️ Not found: {path}")
    
    print("❌ pre_aggregated_data.parquet が見つかりません")
    return None

def test_rest_exclusion_filter():
    """現在の休暇除外フィルターをテスト"""
    print("\n=== 4. 休暇除外フィルターのテスト ===")
    
    # Create test data with rest patterns
    test_data = pd.DataFrame({
        'staff': ['田中太郎', '×', '休み', 'OFF', '佐藤花子', '山田次郎', '休', 'x', '正社員A'],
        'parsed_slots_count': [8, 0, 0, 0, 6, 4, 0, 0, 8],
        'role': ['介護', '介護', '介護', '看護師', '看護師', '介護', '介護', '介護', '介護'],
        'date_lbl': ['2025-06-01'] * 9,
        'time': ['09:00'] * 9
    })
    
    print("📊 テストデータ:")
    print(test_data)
    
    # Import the filter function
    try:
        sys.path.append('.')
        from dash_app import create_enhanced_rest_exclusion_filter
        
        print("\n🔧 フィルター適用前:")
        print(f"レコード数: {len(test_data)}")
        
        filtered_data = create_enhanced_rest_exclusion_filter(test_data)
        
        print("\n✅ フィルター適用後:")
        print(f"レコード数: {len(filtered_data)}")
        print("残存データ:")
        print(filtered_data[['staff', 'parsed_slots_count', 'role']])
        
        return filtered_data
        
    except Exception as e:
        print(f"❌ フィルター関数のインポートエラー: {e}")
        return None

def analyze_data_flow():
    """データフローの全体的な分析"""
    print("\n=== 5. データフロー分析サマリー ===")
    
    excel_result = debug_excel_rest_data()
    intermediate_result = debug_intermediate_data()
    pre_agg_result = debug_pre_aggregated_data()
    filter_result = test_rest_exclusion_filter()
    
    print("\n🎯 結論:")
    
    if excel_result:
        _, _, rest_counts = excel_result
        if rest_counts:
            print(f"✅ 1. Excelファイルに休暇データを検出: {sum(rest_counts.values())}件")
        else:
            print("⚠️ 1. Excelファイルで休暇データが検出されませんでした")
    else:
        print("❌ 1. Excelファイルの読み込みに失敗")
    
    if intermediate_result is not None:
        print("✅ 2. intermediate_dataの読み込み成功")
    else:
        print("❌ 2. intermediate_dataが見つからない")
    
    if pre_agg_result is not None:
        print("✅ 3. pre_aggregated_dataの読み込み成功")
    else:
        print("❌ 3. pre_aggregated_dataが見つからない")
    
    if filter_result is not None:
        print("✅ 4. 休暇除外フィルターは動作している")
    else:
        print("❌ 4. 休暇除外フィルターに問題あり")

def main():
    print("🚀 総合的な休暇除外デバッグを開始します\n")
    print("=" * 60)
    
    analyze_data_flow()
    
    print("\n" + "=" * 60)
    print("🎯 推奨される修正アクション:")
    print("1. io_excel.pyでExcel読み込み時に休暇データを除外")
    print("2. データ分解処理で一貫した休暇除外ロジックを適用")
    print("3. 分析処理前に必ず休暇データをクリーニング")
    print("4. 集計処理で休暇データが混入しないよう確認")
    print("5. ダッシュボードで二重フィルタリングを避ける")

if __name__ == "__main__":
    main()