#!/usr/bin/env python3
"""
Need値の信頼性検証スクリプト
Step 1: heatmap.pyのNeed計算ロジックを検証
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
from shift_suite.tasks.utils import log

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def verify_need_calculation():
    """Need計算の基本検証"""
    
    print("="*60)
    print("Need値計算の信頼性検証")
    print("="*60)
    
    # テストデータの選択
    test_file = project_root / "デイ_テスト用データ_休日精緻.xlsx"
    if not test_file.exists():
        print(f"❌ テストファイルが見つかりません: {test_file}")
        return
    
    print(f"📁 テストファイル: {test_file.name}")
    
    try:
        # 1. Excelファイル読み込み
        print("\n1️⃣ Excelデータ読み込み")
        long_df, wt_df, unknown_codes = ingest_excel(
            test_file,
            shift_sheets=["実績"],  # 想定シート名
            header_row=2,
            slot_minutes=30,
            year_month_cell_location="B1"
        )
        
        print(f"   ✅ 読み込み完了: {len(long_df)}レコード")
        print(f"   📋 職種: {long_df['role'].unique()}")
        print(f"   📅 期間: {long_df['ds'].min().date()} 〜 {long_df['ds'].max().date()}")
        
        # 2. 基本統計
        print("\n2️⃣ 基本統計")
        daily_counts = long_df.groupby(long_df['ds'].dt.date).size()
        print(f"   📊 日別レコード数 (最初の5日): {daily_counts.head().to_dict()}")
        
        role_counts = long_df['role'].value_counts()
        print(f"   👥 職種別レコード数: {role_counts.to_dict()}")
        
        # 3. ヒートマップ生成でNeed計算
        print("\n3️⃣ ヒートマップ生成とNeed計算")
        output_dir = project_root / "temp_need_verification"
        output_dir.mkdir(exist_ok=True)
        
        # 統計手法を変えて複数回テスト
        test_methods = ["中央値", "平均値", "25パーセンタイル"]
        
        for method in test_methods:
            print(f"\n   🔍 統計手法: {method}")
            
            method_dir = output_dir / f"test_{method}"
            method_dir.mkdir(exist_ok=True)
            
            # build_heatmap呼び出し
            result = build_heatmap(
                method_dir,
                long_df=long_df,
                wt_df=wt_df,
                slot=30,
                statistic_method=method,
                remove_outliers=True,
                iqr_multiplier=1.5,
                adjustment_factor=1.0,
                include_zero_days=True
            )
            
            if result:
                # 生成されたファイルを確認
                heat_all_file = method_dir / "heat_ALL.xlsx"
                if heat_all_file.exists():
                    print(f"   ✅ {method}: heat_ALL.xlsx生成完了")
                    
                    # Need値をサンプル表示
                    try:
                        df = pd.read_excel(heat_all_file, index_col=0)
                        if 'need' in df.columns:
                            need_sum = df['need'].sum()
                            need_max = df['need'].max()
                            need_mean = df['need'].mean()
                            print(f"      📈 Need合計: {need_sum:.1f}")
                            print(f"      📈 Need最大: {need_max:.1f}")
                            print(f"      📈 Need平均: {need_mean:.2f}")
                            
                            # 異常値チェック
                            if need_max > 50:
                                print(f"      ⚠️  異常値の可能性: 最大Need {need_max}")
                            if need_sum > 1000:
                                print(f"      ⚠️  異常値の可能性: 合計Need {need_sum}")
                        else:
                            print(f"      ❌ need列が見つかりません")
                    except Exception as e:
                        print(f"      ❌ ファイル読み込みエラー: {e}")
                else:
                    print(f"   ❌ {method}: ヒートマップ生成失敗")
        
        print(f"\n✅ 検証完了。詳細は {output_dir} を確認してください。")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_need_calculation()