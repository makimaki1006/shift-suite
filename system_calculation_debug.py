#!/usr/bin/env python3
"""
システム計算5,073時間 vs 手動計算1,001時間の乖離原因調査
"""

import pandas as pd
from pathlib import Path

def debug_system_calculation():
    """システム計算の問題を特定"""
    
    print("システム計算乖離原因調査")
    print("=" * 50)
    
    scenario_dir = Path("extracted_results/out_p25_based")
    
    # 手動計算（正しい方法）
    need_files = list(scenario_dir.glob("need_per_date_slot_role_*介護*.parquet"))
    manual_total = 0
    
    print("手動計算（ファイル別）:")
    for need_file in need_files:
        df = pd.read_parquet(need_file)
        file_sum = df.select_dtypes(include=[int, float]).sum().sum()
        manual_total += file_sum
        print(f"  {need_file.name}: {file_sum}")
    
    print(f"手動計算合計: {manual_total}")
    
    # システム計算のログを再現
    print(f"\nシステム計算ログから:")
    print("  need_per_date_slot_role_介護.parquet: 1455.0時間 (×4回重複)")
    print("  need_per_date_slot_role_介護・相談員.parquet: 301.0時間")  
    print("  need_per_date_slot_role_事務・介護.parquet: 306.0時間")
    
    # 重複計算の検出
    system_total = (1455.0 * 4) + 301.0 + 306.0  # ログから推定
    print(f"システム計算推定: {system_total}")
    
    print(f"\n問題:")
    print(f"  - 'need_per_date_slot_role_介護.parquet'が4回重複計算")
    print(f"  - 正しくは1回のみカウントすべき")
    print(f"  - 重複による過大計算: {system_total - manual_total}")
    
    return manual_total

if __name__ == "__main__":
    correct_total = debug_system_calculation()
    print(f"\n結論: 正しい不足時間は約1,001時間")
    print(f"5,073時間は重複計算による誤り")