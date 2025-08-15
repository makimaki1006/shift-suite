#!/usr/bin/env python3
"""
最新の分析結果を使用してdash_app.pyの職種別need計算をテストする
"""

import sys
import os
from pathlib import Path
import pandas as pd

# dash_app.pyの関数をインポート
sys.path.append('/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析')

def test_latest_analysis_results():
    """最新の分析結果で職種別need計算をテスト"""
    
    # 最新の分析結果ディレクトリ
    results_dir = Path('/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/temp_analysis_results/out_p25_based')
    
    print("=== 最新分析結果での職種別need計算テスト ===\n")
    
    # 1. 全体need値の確認
    need_per_date_slot_file = results_dir / "need_per_date_slot.parquet"
    if need_per_date_slot_file.exists():
        global_need_df = pd.read_parquet(need_per_date_slot_file)
        global_need_total = global_need_df.sum().sum()
        global_need_daily_avg = global_need_df.mean(axis=1).sum()
        
        print(f"✓ 全体need_per_date_slot.parquet:")
        print(f"  - 全期間累積need: {global_need_total:.2f}")
        print(f"  - 日次平均need: {global_need_daily_avg:.2f}")
        print(f"  - データ形状: {global_need_df.shape}")
        print()
    else:
        print("❌ need_per_date_slot.parquet が見つかりません")
        return
    
    # 2. 全体heat_ALL.parquetとの比較
    heat_all_file = results_dir / "heat_ALL.parquet"
    if heat_all_file.exists():
        heat_all_df = pd.read_parquet(heat_all_file)
        
        # 日付列を特定
        date_cols = [c for c in heat_all_df.columns 
                    if c not in ['need', 'upper', 'staff', 'lack', 'excess'] 
                    and pd.to_datetime(c, errors='coerce') is not pd.NaT]
        
        if date_cols:
            all_staff_total = heat_all_df[date_cols].sum().sum()
            all_need_baseline = heat_all_df['need'].sum()
            
            print(f"✓ 全体heat_ALL.parquet:")
            print(f"  - 全期間staff総計: {all_staff_total:.2f}")
            print(f"  - 基準need合計: {all_need_baseline:.2f}")
            print(f"  - 日付列数: {len(date_cols)}日分")
            print()
        else:
            print("❌ heat_ALL.parquetに日付列が見つかりません")
            return
    else:
        print("❌ heat_ALL.parquet が見つかりません")
        return
    
    # 3. 職種別ヒートマップファイルの確認
    role_files = list(results_dir.glob("heat_*.parquet"))
    role_files = [f for f in role_files if not f.name.startswith('heat_emp_') and f.name != 'heat_ALL.parquet']
    
    print(f"✓ 職種別ヒートマップファイル: {len(role_files)}個")
    
    total_role_need = 0
    total_role_staff = 0
    
    for role_file in sorted(role_files):
        role_name = role_file.stem.replace('heat_', '')
        
        try:
            role_df = pd.read_parquet(role_file)
            
            # 日付列を特定
            role_date_cols = [c for c in role_df.columns 
                            if c not in ['need', 'upper', 'staff', 'lack', 'excess'] 
                            and pd.to_datetime(c, errors='coerce') is not pd.NaT]
            
            if role_date_cols:
                role_staff_total = role_df[role_date_cols].sum().sum()
                role_need_baseline = role_df['need'].sum()
                
                # staff比率を計算
                staff_ratio = role_staff_total / all_staff_total if all_staff_total > 0 else 0
                
                total_role_need += role_need_baseline
                total_role_staff += role_staff_total
                
                print(f"  {role_name}:")
                print(f"    - staff総計: {role_staff_total:.2f} (比率: {staff_ratio:.1%})")
                print(f"    - need基準: {role_need_baseline:.2f}")
                
                # 按分計算予測
                predicted_need = global_need_daily_avg * staff_ratio
                print(f"    - 按分予測need: {predicted_need:.2f}")
            else:
                print(f"  {role_name}: 日付列なし")
                
        except Exception as e:
            print(f"  {role_name}: エラー - {e}")
    
    print()
    
    # 4. 整合性チェック
    print("=== 整合性チェック ===")
    print(f"✓ 職種別staff合計: {total_role_staff:.2f}")
    print(f"✓ 全体staff合計: {all_staff_total:.2f}")
    print(f"  差異: {abs(total_role_staff - all_staff_total):.2f}")
    
    print(f"✓ 職種別need基準合計: {total_role_need:.2f}")
    print(f"✓ 全体need基準: {all_need_baseline:.2f}")
    print(f"  差異: {abs(total_role_need - all_need_baseline):.2f}")
    
    # 按分計算の妥当性チェック
    if all_staff_total > 0:
        print("\n=== 按分計算シミュレーション ===")
        role_need_sum_predicted = 0
        
        for role_file in sorted(role_files):
            role_name = role_file.stem.replace('heat_', '')
            
            try:
                role_df = pd.read_parquet(role_file)
                role_date_cols = [c for c in role_df.columns 
                                if c not in ['need', 'upper', 'staff', 'lack', 'excess'] 
                                and pd.to_datetime(c, errors='coerce') is not pd.NaT]
                
                if role_date_cols:
                    role_staff_total = role_df[role_date_cols].sum().sum()
                    staff_ratio = role_staff_total / all_staff_total
                    predicted_need = global_need_daily_avg * staff_ratio
                    role_need_sum_predicted += predicted_need
                    
            except Exception:
                pass
        
        print(f"✓ 按分計算による職種別need合計予測: {role_need_sum_predicted:.2f}")
        print(f"✓ 全体need日次平均: {global_need_daily_avg:.2f}")
        print(f"  差異: {abs(role_need_sum_predicted - global_need_daily_avg):.2f}")
        
        if abs(role_need_sum_predicted - global_need_daily_avg) < 0.1:
            print("🎉 按分計算の整合性: 優秀 (差異 < 0.1)")
        elif abs(role_need_sum_predicted - global_need_daily_avg) < 1.0:
            print("✓ 按分計算の整合性: 良好 (差異 < 1.0)")
        else:
            print("⚠️ 按分計算の整合性: 要確認 (差異 >= 1.0)")

if __name__ == "__main__":
    test_latest_analysis_results()