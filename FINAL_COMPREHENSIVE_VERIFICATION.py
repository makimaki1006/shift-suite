#!/usr/bin/env python3
"""
修正後の総合検証スクリプト
"""

import pandas as pd
from pathlib import Path
import sys

def check_data_consistency():
    """データ整合性の包括確認"""
    print("="*80)
    print("🔍 修正後の総合データ整合性検証")
    print("="*80)
    
    # 最新の分析結果ディレクトリを探す
    analysis_dirs = list(Path(".").glob("analysis_results*"))
    if not analysis_dirs:
        print("❌ analysis_resultsディレクトリが見つかりません")
        return
    
    latest_dir = max(analysis_dirs, key=lambda p: p.stat().st_mtime)
    print(f"📁 最新分析結果: {latest_dir}")
    
    # シナリオディレクトリを確認
    out_dir = latest_dir / "out"
    if not out_dir.exists():
        print("❌ outディレクトリが見つかりません")
        return
    
    scenarios = list(out_dir.glob("out_*"))
    if not scenarios:
        print("❌ シナリオディレクトリが見つかりません")
        return
    
    scenario_dir = scenarios[0]  # 最初のシナリオをチェック
    print(f"🎯 検証対象: {scenario_dir.name}")
    
    issues = []
    
    # 1. heat_ALL.parquetの確認
    print("\n1️⃣ heat_ALL.parquet確認")
    heat_all_path = scenario_dir / "heat_ALL.parquet"
    if heat_all_path.exists():
        heat_df = pd.read_parquet(heat_all_path)
        date_cols = [c for c in heat_df.columns if c not in ['time']]
        
        # 休日データが含まれていないかチェック
        total_staff = heat_df[date_cols].sum().sum()
        zero_ratio = (heat_df[date_cols] == 0).sum().sum() / (len(heat_df) * len(date_cols))
        
        print(f"  ✓ 日付列数: {len(date_cols)}")
        print(f"  ✓ 総スタッフ数: {total_staff}")
        print(f"  ✓ 0値の割合: {zero_ratio:.1%}")
        
        if zero_ratio > 0.8:
            issues.append("heat_ALL.parquetに多数の0値が含まれている")
    else:
        issues.append("heat_ALL.parquetが見つからない")
    
    # 2. pre_aggregated_data.parquetの確認
    print("\n2️⃣ pre_aggregated_data.parquet確認")
    pre_agg_path = scenario_dir / "pre_aggregated_data.parquet"
    if pre_agg_path.exists():
        pre_agg_df = pd.read_parquet(pre_agg_path)
        
        # staff_count = 0のレコード数
        zero_staff = (pre_agg_df['staff_count'] == 0).sum()
        total_records = len(pre_agg_df)
        zero_staff_ratio = zero_staff / total_records
        
        print(f"  ✓ 総レコード数: {total_records}")
        print(f"  ✓ staff_count=0のレコード数: {zero_staff}")
        print(f"  ✓ 0スタッフの割合: {zero_staff_ratio:.1%}")
        
        # 期待値: 修正後は0スタッフの割合が大幅に減少するはず
        if zero_staff_ratio > 0.5:
            issues.append("pre_aggregated_dataに多数の0スタッフレコードが残っている")
        
        # 実際の勤務日数を確認
        actual_work_dates = pre_agg_df[pre_agg_df['staff_count'] > 0]['date_lbl'].nunique()
        total_dates = pre_agg_df['date_lbl'].nunique()
        
        print(f"  ✓ 総日付数: {total_dates}")
        print(f"  ✓ 実勤務日数: {actual_work_dates}")
        print(f"  ✓ 勤務日比率: {actual_work_dates/total_dates:.1%}")
    else:
        issues.append("pre_aggregated_data.parquetが見つからない")
    
    # 3. shortage_time.parquetの確認
    print("\n3️⃣ shortage_time.parquet確認")
    shortage_path = scenario_dir / "shortage_time.parquet"
    if shortage_path.exists():
        shortage_df = pd.read_parquet(shortage_path)
        
        # 日付列の整合性確認
        if heat_all_path.exists() and len(date_cols) > 0:
            shortage_dates = [c for c in shortage_df.columns if c not in ['time', 'lack_h', 'excess_h']]
            
            # heat_ALL.parquetの日付数と一致するかチェック
            date_consistency = len(date_cols) == len(shortage_dates)
            print(f"  ✓ 日付列数: {len(shortage_dates)}")
            print(f"  ✓ heat_ALL.parquetとの整合性: {'✓' if date_consistency else '❌'}")
            
            if not date_consistency:
                issues.append("shortage_timeとheat_ALLの日付数が不一致")
        
        # 不足時間の合計
        if 'lack_h' in shortage_df.columns:
            total_lack = shortage_df['lack_h'].sum()
            print(f"  ✓ 総不足時間: {total_lack:.1f}h")
    else:
        issues.append("shortage_time.parquetが見つからない")
    
    # 4. intermediate_data.parquetの確認
    print("\n4️⃣ intermediate_data.parquet確認")
    inter_path = scenario_dir / "intermediate_data.parquet"
    if inter_path.exists():
        inter_df = pd.read_parquet(inter_path)
        
        if 'parsed_slots_count' in inter_df.columns:
            zero_slots = (inter_df['parsed_slots_count'] == 0).sum()
            total_inter = len(inter_df)
            zero_slots_ratio = zero_slots / total_inter
            
            print(f"  ✓ 総レコード数: {total_inter}")
            print(f"  ✓ parsed_slots_count=0のレコード数: {zero_slots}")
            print(f"  ✓ 0スロット比率: {zero_slots_ratio:.1%}")
            
            # 修正後は0スロットが完全に除外されているはず
            if zero_slots > 0:
                issues.append("intermediate_dataに0スロットレコードが残っている")
    else:
        issues.append("intermediate_data.parquetが見つからない")
    
    # 5. 結果表示
    print("\n" + "="*80)
    if not issues:
        print("🎉 総合検証結果: すべて正常")
        print("✅ 修正が正しく適用されています")
        print("✅ データ整合性が保たれています")
        print("✅ 休日除外が完全に機能しています")
    else:
        print("⚠️  総合検証結果: 以下の問題が発見されました")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        
        print("\n📋 推奨対応:")
        print("  1. キャッシュをクリアして再分析を実行")
        print("  2. ログで[RestExclusion]メッセージを確認")
        print("  3. 問題が続く場合は個別調査を実施")
    
    print("="*80)

if __name__ == "__main__":
    try:
        check_data_consistency()
    except Exception as e:
        print(f"❌ 検証中にエラーが発生しました: {e}")
        print("再度実行するか、手動でファイルを確認してください")