#!/usr/bin/env python3
"""
Source Data Analysis - デイ_テスト用データ_休日精緻.xlsx
"""
import pandas as pd
import os

def analyze_source_excel():
    """元データExcelファイルの詳細分析"""
    
    excel_path = "デイ_テスト用データ_休日精緻.xlsx"
    
    print("=== 元データファイル分析 ===")
    print(f"ファイル: {excel_path}")
    
    if not os.path.exists(excel_path):
        print(f"ERROR: ファイルが見つかりません: {excel_path}")
        return False
    
    file_size = os.path.getsize(excel_path)
    print(f"ファイルサイズ: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    
    try:
        # シート情報の取得
        print("\n=== シート情報 ===")
        xl = pd.ExcelFile(excel_path)
        print(f"シート数: {len(xl.sheet_names)}")
        
        for i, sheet_name in enumerate(xl.sheet_names):
            print(f"{i+1:2d}. {sheet_name}")
        
        # 各シートの基本情報
        print("\n=== シート別詳細情報 ===")
        for sheet_name in xl.sheet_names:
            try:
                # ヘッダー行を特定するため複数行読み込み
                df_preview = pd.read_excel(excel_path, sheet_name=sheet_name, nrows=10)
                
                print(f"\n--- シート: {sheet_name} ---")
                print(f"プレビュー形状: {df_preview.shape}")
                print("最初の5行の列名:")
                for col in df_preview.columns:
                    print(f"  - {col}")
                
                # データのサンプル表示（最初の3行）
                if len(df_preview) > 0:
                    print("データサンプル (最初の3行):")
                    for idx, row in df_preview.head(3).iterrows():
                        print(f"  行{idx+1}: {row.iloc[:5].tolist()}")  # 最初の5列のみ
                
            except Exception as e:
                print(f"シート {sheet_name} 読み込みエラー: {e}")
        
        # 想定される勤務データの確認
        print("\n=== 勤務データ特定 ===")
        main_data_candidates = []
        
        for sheet_name in xl.sheet_names:
            try:
                # ヘッダー行を推測して読み込み
                for header_row in [0, 1, 2]:
                    try:
                        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=header_row, nrows=50)
                        
                        # 勤務データの特徴を確認
                        staff_columns = [col for col in df.columns if any(keyword in str(col) for keyword in ['氏名', '名前', 'staff', 'name', '従業員'])]
                        date_columns = [col for col in df.columns if any(keyword in str(col) for keyword in ['日', 'date', '月'])]
                        shift_columns = [col for col in df.columns if len([c for c in df.columns if '/' in str(c)]) > 5]  # 日付形式の列
                        
                        if staff_columns and (date_columns or shift_columns or len(df.columns) > 10):
                            info = {
                                'sheet': sheet_name,
                                'header_row': header_row,
                                'shape': df.shape,
                                'staff_columns': staff_columns,
                                'date_columns': date_columns,
                                'total_columns': len(df.columns),
                                'sample_data': len(df.dropna())
                            }
                            main_data_candidates.append(info)
                            break
                    except:
                        continue
            except Exception as e:
                print(f"シート {sheet_name} 詳細分析エラー: {e}")
        
        if main_data_candidates:
            print("勤務データ候補:")
            for i, candidate in enumerate(main_data_candidates):
                print(f"{i+1}. シート: {candidate['sheet']}")
                print(f"   ヘッダー行: {candidate['header_row']}")
                print(f"   形状: {candidate['shape']}")
                print(f"   スタッフ列: {candidate['staff_columns']}")
                print(f"   有効データ行数: {candidate['sample_data']}")
        else:
            print("勤務データ候補が見つかりませんでした")
        
        return True
        
    except Exception as e:
        print(f"ファイル分析エラー: {e}")
        return False

if __name__ == "__main__":
    analyze_source_excel()