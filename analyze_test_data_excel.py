#!/usr/bin/env python3
"""
テストデータExcelファイルの構造分析
デイ_テスト用データ_休日精緻.xlsxの詳細調査
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analyze_test_data_excel():
    """テストデータExcelファイルの詳細分析"""
    
    print("=" * 80)
    print("テストデータExcel分析: デイ_テスト用データ_休日精緻.xlsx")
    print("=" * 80)
    
    excel_path = "デイ_テスト用データ_休日精緻.xlsx"
    
    if not Path(excel_path).exists():
        print(f"ERROR: ファイルが見つかりません: {excel_path}")
        return
    
    try:
        # 1. シート一覧の確認
        print("\n【STEP 1: シート構造確認】")
        xl = pd.ExcelFile(excel_path)
        sheet_names = xl.sheet_names
        print(f"シート数: {len(sheet_names)}")
        print(f"シート名: {sheet_names}")
        
        # 2. 各シートの詳細分析
        print("\n【STEP 2: 各シート詳細分析】")
        
        for i, sheet_name in enumerate(sheet_names[:3]):  # 最初の3シートのみ
            print(f"\n--- シート{i+1}: {sheet_name} ---")
            
            try:
                # ヘッダーなしで読み込み（最初の5行を確認）
                df_peek = pd.read_excel(excel_path, sheet_name=sheet_name, header=None, nrows=10)
                print(f"データ例（ヘッダーなし）:")
                print(df_peek.head())
                
                # 適切なヘッダー行を推定
                for header_row in [0, 1, 2, 3]:
                    try:
                        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=header_row)
                        if 'role' in df.columns or '職種' in df.columns or '氏名' in df.columns:
                            print(f"  FOUND: ヘッダー行{header_row}でrole系カラム発見")
                            print(f"  形状: {df.shape}")
                            print(f"  カラム: {list(df.columns)}")
                            
                            # roleカラムの確認
                            role_columns = [col for col in df.columns if any(word in str(col) for word in ['role', '職種', '氏名', 'staff'])]
                            if role_columns:
                                print(f"  関連カラム: {role_columns}")
                                for col in role_columns[:2]:  # 最初の2つのrole系カラム
                                    unique_vals = df[col].dropna().unique()
                                    print(f"    {col}: {list(unique_vals)[:10]}")
                            
                            # 時間関連カラムの確認
                            time_columns = [col for col in df.columns if any(word in str(col) for word in ['時', ':', 'slot', 'time'])]
                            if time_columns:
                                print(f"  時間関連カラム: {time_columns[:5]}...")
                            
                            break
                            
                    except Exception as e:
                        continue
                else:
                    print(f"  適切なヘッダー行が見つかりませんでした")
                    
            except Exception as e:
                print(f"  ERROR: シート読み込みエラー: {e}")
        
        # 3. 全シートでrole系データの探索
        print("\n【STEP 3: 全シートでrole系データ探索】")
        
        role_sheets = []
        for sheet_name in sheet_names:
            try:
                for header_row in [0, 1, 2]:
                    try:
                        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=header_row)
                        
                        # role系カラムを探索
                        role_indicators = ['role', '職種', '氏名', 'staff', '従業員', 'member']
                        has_role_data = any(
                            any(indicator in str(col).lower() for indicator in role_indicators)
                            for col in df.columns
                        )
                        
                        if has_role_data:
                            role_sheets.append({
                                'sheet': sheet_name,
                                'header_row': header_row,
                                'shape': df.shape,
                                'columns': list(df.columns)[:5]
                            })
                            break
                            
                    except:
                        continue
                        
            except Exception as e:
                continue
        
        print(f"role系データがあるシート数: {len(role_sheets)}")
        for rs in role_sheets:
            print(f"  {rs['sheet']} (ヘッダー{rs['header_row']}, {rs['shape']}, カラム: {rs['columns']}...)")
        
        # 4. 最も適切なシートでの詳細分析
        if role_sheets:
            print(f"\n【STEP 4: 詳細データ分析】")
            best_sheet = role_sheets[0]  # 最初に見つかったシートを使用
            
            print(f"分析対象: {best_sheet['sheet']} (ヘッダー行{best_sheet['header_row']})")
            
            df = pd.read_excel(excel_path, 
                              sheet_name=best_sheet['sheet'], 
                              header=best_sheet['header_row'])
            
            print(f"データ形状: {df.shape}")
            print(f"全カラム一覧:")
            for i, col in enumerate(df.columns):
                dtype = df[col].dtype
                non_null_count = df[col].count()
                print(f"  [{i:2d}] {str(col)[:20]:20s} ({str(dtype)[:10]:10s}) 非NULL: {non_null_count}")
            
            # 職種データの詳細確認
            role_columns = [col for col in df.columns 
                           if any(word in str(col) for word in ['職種', 'role', '氏名', 'staff'])]
            
            for role_col in role_columns:
                print(f"\n{role_col}の詳細:")
                unique_vals = df[role_col].dropna().unique()
                print(f"  ユニーク値数: {len(unique_vals)}")
                print(f"  値一覧: {list(unique_vals)}")
                
                # 介護関連の確認
                care_related = [val for val in unique_vals if '介護' in str(val)]
                if care_related:
                    print(f"  介護関連: {care_related}")
            
            # データのサンプル表示
            print(f"\nデータサンプル（最初の5行）:")
            print(df.head())
            
            return df  # 分析したデータフレームを返す
        
        else:
            print("role系データが含まれるシートが見つかりませんでした")
            return None
            
    except Exception as e:
        print(f"ERROR: Excel分析エラー: {e}")
        import traceback
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    result = analyze_test_data_excel()
    if result is not None:
        print(f"\n=== 分析完了 ===")
        print(f"データフレーム形状: {result.shape}")
        print("テストデータ構造の理解が深まりました")