#!/usr/bin/env python3
"""
不足時間データのデバッグスクリプト
shortage_role_summary.parquetのlack_hカラムの値を確認
"""

import pandas as pd
from pathlib import Path
import numpy as np

def debug_shortage_data():
    """不足時間データのデバッグ"""
    
    print("🔍 === 不足時間データ調査 ===\n")
    
    # シナリオディレクトリを探索
    scenario_dirs = list(Path(".").glob("*_based"))
    
    for scenario_dir in scenario_dirs:
        print(f"\n📁 シナリオ: {scenario_dir.name}")
        
        # shortage_role_summary.parquet を確認
        shortage_file = scenario_dir / "shortage_role_summary.parquet"
        if shortage_file.exists():
            df = pd.read_parquet(shortage_file)
            print(f"  ✅ shortage_role_summary.parquet 発見")
            print(f"  カラム: {df.columns.tolist()}")
            
            if 'lack_h' in df.columns:
                print(f"\n  【lack_h カラムの分析】")
                print(f"  - データ型: {df['lack_h'].dtype}")
                print(f"  - 最小値: {df['lack_h'].min():.2f}")
                print(f"  - 最大値: {df['lack_h'].max():.2f}")
                print(f"  - 平均値: {df['lack_h'].mean():.2f}")
                print(f"  - 合計値: {df['lack_h'].sum():.2f}")
                print(f"  - NULL数: {df['lack_h'].isna().sum()}")
                
                # 上位5件のデータ表示
                print(f"\n  【上位5件のデータ】")
                top_5 = df.nlargest(5, 'lack_h')[['role', 'lack_h', 'need_h', 'staff_h']]
                for idx, row in top_5.iterrows():
                    print(f"  {row['role']:20s} | lack_h: {row['lack_h']:8.2f} | need_h: {row['need_h']:8.2f} | staff_h: {row['staff_h']:8.2f}")
            else:
                print("  ⚠️ lack_h カラムが存在しません")
        else:
            print(f"  ❌ shortage_role_summary.parquet が見つかりません")
        
        # shortage_time.parquet も確認
        shortage_time_file = scenario_dir / "shortage_time.parquet"
        if shortage_time_file.exists():
            time_df = pd.read_parquet(shortage_time_file)
            print(f"\n  ✅ shortage_time.parquet 発見")
            
            # 数値列のみ取得
            numeric_cols = time_df.select_dtypes(include=[np.number])
            if not numeric_cols.empty:
                total_slots = float(np.nansum(numeric_cols.values))
                print(f"  - 総スロット数: {total_slots:.0f}")
                
                # スロット時間を推定（30分 = 0.5時間を仮定）
                estimated_hours = total_slots * 0.5
                print(f"  - 推定不足時間（30分/スロット）: {estimated_hours:.2f}時間")
                
                # 動的スロット時間での計算も表示
                for minutes in [15, 30, 60]:
                    hours = total_slots * (minutes / 60.0)
                    print(f"  - {minutes}分/スロットでの不足時間: {hours:.2f}時間")

def check_data_consistency():
    """データ整合性のチェック"""
    print("\n\n🔧 === データ整合性チェック ===")
    
    # すべてのシナリオでの値を比較
    all_data = {}
    
    for scenario_dir in Path(".").glob("*_based"):
        shortage_file = scenario_dir / "shortage_role_summary.parquet"
        if shortage_file.exists():
            df = pd.read_parquet(shortage_file)
            if 'lack_h' in df.columns:
                total = df['lack_h'].sum()
                all_data[scenario_dir.name] = total
    
    if all_data:
        print("\n【シナリオ間比較】")
        for scenario, total in all_data.items():
            print(f"  {scenario:15s}: {total:10.2f}時間")
        
        # 値の桁数チェック
        values = list(all_data.values())
        max_val = max(values)
        min_val = min(values)
        
        if max_val > 10000:  # 10,000時間以上は異常の可能性
            print(f"\n⚠️ 警告: 最大値 {max_val:.2f}時間は異常に大きい可能性があります")
            print("  → スロット数を時間として扱っている可能性があります")
        
        if max_val / min_val > 10:  # 10倍以上の差は要確認
            print(f"\n⚠️ 警告: シナリオ間で{max_val/min_val:.1f}倍の差があります")

if __name__ == "__main__":
    debug_shortage_data()
    check_data_consistency()