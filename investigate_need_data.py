#!/usr/bin/env python
"""
Need計算問題の調査スクリプト
"""
import pandas as pd
import os
from pathlib import Path

def investigate_need_files():
    """Need計算ファイルの調査を実行"""
    
    # ディレクトリパス
    analysis_dir = Path("analysis_results")
    
    print("=== Need計算問題調査 ===\n")
    
    # 1. need_per_date_slot.parquetの調査
    need_file = analysis_dir / "need_per_date_slot.parquet"
    if need_file.exists():
        print("1. need_per_date_slot.parquet の調査:")
        try:
            need_df = pd.read_parquet(need_file)
            print(f"   - 形状: {need_df.shape}")
            print(f"   - 時間軸（index）: {need_df.index[:5].tolist()}")
            print(f"   - 日付列数: {len(need_df.columns)}")
            print(f"   - 列名例: {need_df.columns[:5].tolist()}")
            
            # 全体の合計Need
            total_need = need_df.sum().sum()
            print(f"   - 全体のNeed合計: {total_need:.2f}")
            
            # 曜日別合計（日曜日のみチェック）
            sunday_total = 0
            for col in need_df.columns:
                try:
                    date_obj = pd.to_datetime(col).date()
                    if date_obj.weekday() == 6:  # 日曜日
                        sunday_total += need_df[col].sum()
                except:
                    pass
            print(f"   - 日曜日のNeed合計: {sunday_total:.2f}")
            
        except Exception as e:
            print(f"   - エラー: {e}")
    else:
        print("1. need_per_date_slot.parquet が見つかりません")
    
    print()
    
    # 2. heat_ALL.parquetの調査
    heat_all_file = analysis_dir / "heat_ALL.parquet"
    if heat_all_file.exists():
        print("2. heat_ALL.parquet の調査:")
        try:
            heat_all_df = pd.read_parquet(heat_all_file)
            print(f"   - 形状: {heat_all_df.shape}")
            print(f"   - 列名: {heat_all_df.columns.tolist()}")
            
            if 'need' in heat_all_df.columns:
                need_col_total = heat_all_df['need'].sum()
                print(f"   - 'need'列の合計: {need_col_total:.2f}")
            
        except Exception as e:
            print(f"   - エラー: {e}")
    else:
        print("2. heat_ALL.parquet が見つかりません")
    
    print()
    
    # 3. 職種別ヒートマップの調査
    print("3. 職種別ヒートマップの調査:")
    role_files = list(analysis_dir.glob("heat_*.parquet"))
    role_files = [f for f in role_files if not f.name.startswith("heat_emp_") and f.name != "heat_ALL.parquet"]
    
    total_role_needs = 0
    for role_file in role_files[:5]:  # 最初の5つの職種のみ
        try:
            role_df = pd.read_parquet(role_file)
            role_name = role_file.stem.replace("heat_", "")
            
            if 'need' in role_df.columns:
                role_need = role_df['need'].sum()
                total_role_needs += role_need
                print(f"   - {role_name}: Need={role_need:.2f}")
            
        except Exception as e:
            print(f"   - {role_file.name}: エラー {e}")
    
    print(f"   - 職種別Need合計（最初の5職種）: {total_role_needs:.2f}")
    print()
    
    # 4. 雇用形態別ヒートマップの調査
    print("4. 雇用形態別ヒートマップの調査:")
    emp_files = list(analysis_dir.glob("heat_emp_*.parquet"))
    
    total_emp_needs = 0
    for emp_file in emp_files:
        try:
            emp_df = pd.read_parquet(emp_file)
            emp_name = emp_file.stem.replace("heat_emp_", "")
            
            if 'need' in emp_df.columns:
                emp_need = emp_df['need'].sum()
                total_emp_needs += emp_need
                print(f"   - {emp_name}: Need={emp_need:.2f}")
            
        except Exception as e:
            print(f"   - {emp_file.name}: エラー {e}")
    
    print(f"   - 雇用形態別Need合計: {total_emp_needs:.2f}")
    print()
    
    # 5. shortage関連ファイルの調査
    print("5. shortage関連ファイルの調査:")
    shortage_files = [
        "shortage_role_summary.parquet",
        "shortage_employment_summary.parquet",
        "shortage_time.parquet"
    ]
    
    for file_name in shortage_files:
        file_path = analysis_dir / file_name
        if file_path.exists():
            try:
                df = pd.read_parquet(file_path)
                print(f"   - {file_name}: 形状={df.shape}")
                if 'lack_h' in df.columns:
                    lack_total = df['lack_h'].sum()
                    print(f"     - 不足時間合計: {lack_total}")
                
            except Exception as e:
                print(f"   - {file_name}: エラー {e}")
        else:
            print(f"   - {file_name}: 見つかりません")

if __name__ == "__main__":
    # カレントディレクトリを確認
    print(f"現在のディレクトリ: {os.getcwd()}")
    investigate_need_files()