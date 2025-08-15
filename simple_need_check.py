#!/usr/bin/env python3
"""
シンプルなNeed値検証
"""

import sys
import os
from pathlib import Path
import pandas as pd
import logging

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shift_suite.tasks.io_excel import ingest_excel
from shift_suite.tasks.heatmap import build_heatmap

# ログ設定
logging.basicConfig(level=logging.WARNING)

def simple_need_check():
    """シンプルなNeed値チェック"""
    
    print("Need calculation verification")
    print("=" * 40)
    
    # テストデータの選択
    test_file = project_root / "デイ_テスト用データ_休日精緻.xlsx"
    if not test_file.exists():
        print(f"Error: Test file not found: {test_file}")
        return
    
    print(f"Test file: {test_file.name}")
    
    try:
        # 1. Excelファイル読み込み
        print("\n1. Loading Excel data...")
        long_df, wt_df, unknown_codes = ingest_excel(
            test_file,
            shift_sheets=["R7.2", "R7.6"],  # 実際のシート名
            header_row=0,  # ヘッダー行
            slot_minutes=30,
            year_month_cell_location=None  # 年月セルなし
        )
        
        print(f"   Records loaded: {len(long_df)}")
        print(f"   Roles: {list(long_df['role'].unique())}")
        print(f"   Date range: {long_df['ds'].min().date()} to {long_df['ds'].max().date()}")
        
        # 2. ヒートマップ生成でNeed計算
        print("\n2. Generating heatmap and calculating Need...")
        output_dir = project_root / "temp_need_check"
        output_dir.mkdir(exist_ok=True)
        
        result = build_heatmap(
            output_dir,
            long_df=long_df,
            wt_df=wt_df,
            slot=30,
            statistic_method="中央値",
            remove_outliers=True,
            iqr_multiplier=1.5,
            adjustment_factor=1.0,
            include_zero_days=True
        )
        
        if result:
            # 生成されたファイルを確認
            heat_all_file = output_dir / "heat_ALL.xlsx"
            if heat_all_file.exists():
                print(f"   heat_ALL.xlsx generated successfully")
                
                # Need値をチェック
                df = pd.read_excel(heat_all_file, index_col=0)
                if 'need' in df.columns:
                    need_sum = df['need'].sum()
                    need_max = df['need'].max()
                    need_mean = df['need'].mean()
                    need_nonzero = (df['need'] > 0).sum()
                    
                    print(f"   Need total: {need_sum:.1f}")
                    print(f"   Need max: {need_max:.1f}")
                    print(f"   Need mean: {need_mean:.2f}")
                    print(f"   Non-zero slots: {need_nonzero}")
                    
                    # 異常値の検出
                    anomalies = []
                    if need_max > 50:
                        anomalies.append(f"Max Need too high: {need_max}")
                    if need_sum > 1000:
                        anomalies.append(f"Total Need too high: {need_sum}")
                    if need_mean > 10:
                        anomalies.append(f"Mean Need too high: {need_mean}")
                    
                    if anomalies:
                        print("   ANOMALIES DETECTED:")
                        for anomaly in anomalies:
                            print(f"   - {anomaly}")
                    else:
                        print("   No obvious anomalies detected")
                        
                    # サンプル値表示
                    print(f"\n   Sample Need values (first 10 non-zero):")
                    nonzero_needs = df[df['need'] > 0]['need'].head(10)
                    for idx, val in nonzero_needs.items():
                        print(f"     {idx}: {val}")
                        
                else:
                    print("   ERROR: 'need' column not found")
            else:
                print("   ERROR: heat_ALL.xlsx not generated")
        else:
            print("   ERROR: build_heatmap failed")
            
        # 職種別ファイルもチェック
        print("\n3. Checking role-specific heatmaps...")
        role_files = list(output_dir.glob("heat_*.xlsx"))
        role_files = [f for f in role_files if f.name != "heat_ALL.xlsx"]
        
        for role_file in role_files[:3]:  # 最初の3つだけ
            role_name = role_file.stem.replace("heat_", "")
            try:
                df_role = pd.read_excel(role_file, index_col=0)
                if 'need' in df_role.columns:
                    role_need_sum = df_role['need'].sum()
                    role_need_max = df_role['need'].max()
                    print(f"   {role_name}: total={role_need_sum:.1f}, max={role_need_max:.1f}")
                else:
                    print(f"   {role_name}: No need column")
            except Exception as e:
                print(f"   {role_name}: Error reading file - {e}")
        
        print(f"\nVerification complete. Check {output_dir} for details.")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_need_check()