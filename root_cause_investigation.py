#!/usr/bin/env python3
"""
根本問題の特定: なぜ23.6時間/日という異常値になるのか
"""

import pandas as pd
from pathlib import Path

def investigate_root_cause():
    """根本原因の調査"""
    
    print("根本問題調査: 23.6時間/日不足の異常値原因")
    print("=" * 50)
    
    scenario_dir = Path("extracted_results/out_p25_based")
    
    # 1. 需要データの詳細分析
    print("\n【需要データ詳細分析】")
    
    need_files = list(scenario_dir.glob("need_per_date_slot_role_*介護*.parquet"))
    total_need = 0
    
    for need_file in need_files:
        df = pd.read_parquet(need_file)
        file_sum = df.select_dtypes(include=[int, float]).sum().sum()
        total_need += file_sum
        
        print(f"{need_file.name}:")
        print(f"  データ形状: {df.shape}")
        print(f"  合計値: {file_sum}")
        print(f"  1日平均: {file_sum/30:.1f}")
        print(f"  最大値: {df.max().max()}")
        print(f"  データ単位: {df.iloc[0,0]}の型={type(df.iloc[0,0])}")
    
    print(f"\n需要合計: {total_need} (1日平均: {total_need/30:.1f})")
    
    # 2. 配置データの詳細分析
    print(f"\n【配置データ詳細分析】")
    
    intermediate_data = pd.read_parquet(scenario_dir / "intermediate_data.parquet")
    care_data = intermediate_data[intermediate_data['role'].str.contains('介護', na=False)]
    
    print(f"intermediate_data:")
    print(f"  総レコード: {len(intermediate_data)}")
    print(f"  介護レコード: {len(care_data)}")
    print(f"  期間: {intermediate_data['ds'].nunique()}日間")
    print(f"  1日平均介護レコード: {len(care_data)/30:.1f}")
    
    # 各レコードの意味を分析
    sample_day = care_data[care_data['ds'] == care_data['ds'].iloc[0]]
    print(f"\nサンプル日の分析 ({sample_day['ds'].iloc[0].date()}):")
    print(f"  その日の介護レコード数: {len(sample_day)}")
    print(f"  職種内訳:")
    for role, count in sample_day['role'].value_counts().items():
        print(f"    {role}: {count}件")
    
    # 3. 時間軸の分析
    print(f"\n【時間軸分析】")
    
    # 1日のタイムスロット数確認
    if 'time_slot' in care_data.columns:
        unique_slots = care_data['time_slot'].nunique()
        print(f"タイムスロット種類: {unique_slots}")
    else:
        print("time_slotカラムなし - ds（日時）から推定")
        
    # dsカラムの時間情報確認
    sample_times = care_data['ds'].dt.time.unique()[:10]
    print(f"時刻サンプル: {sample_times}")
    
    # 4. 単位系の確認
    print(f"\n【単位系確認】")
    
    print("推定される問題:")
    print("1. 需要データの単位が「人」ではなく「人×30分スロット」")
    print("2. 30分スロット = 0.5時間として計算している")
    print("3. しかし実際は「人の必要数」かもしれない")
    
    # 5. 修正案の検討
    print(f"\n【修正案の検討】")
    
    # 仮説1: 需要データが既に時間単位
    corrected_need_1 = total_need / 2  # 時間→人変換
    corrected_shortage_1 = corrected_need_1 - (len(care_data) * 0.5)
    print(f"仮説1（需要を人数に変換）:")
    print(f"  修正需要: {corrected_need_1:.1f}時間")
    print(f"  修正不足: {corrected_shortage_1:.1f}時間")
    print(f"  1日不足: {corrected_shortage_1/30:.1f}時間/日")
    
    # 仮説2: 配置データの解釈変更
    corrected_staff_2 = len(care_data)  # スロット数をそのまま時間数として使用
    corrected_shortage_2 = total_need - corrected_staff_2
    print(f"\n仮説2（配置をスロット数=時間数）:")
    print(f"  修正配置: {corrected_staff_2:.1f}時間") 
    print(f"  修正不足: {corrected_shortage_2:.1f}時間")
    print(f"  1日不足: {corrected_shortage_2/30:.1f}時間/日")
    
    # 仮説3: 両方修正
    corrected_shortage_3 = (total_need / 48) - (len(care_data) / 48)  # 1日48スロットで正規化
    print(f"\n仮説3（1日48スロットで正規化）:")
    print(f"  1日不足: {corrected_shortage_3:.1f}時間/日")
    
    # 6. 現実的範囲との比較
    print(f"\n【現実的範囲との比較】")
    print("現実的な介護施設不足: 1-10時間/日")
    
    scenarios = [
        ("現在", 23.6, "❌ 非現実的"),
        ("仮説1", corrected_shortage_1/30, "❌ 非現実的" if corrected_shortage_1/30 > 10 else "✓ 現実的"),
        ("仮説2", corrected_shortage_2/30, "❌ 非現実的" if corrected_shortage_2/30 > 10 else "✓ 現実的"),
        ("仮説3", corrected_shortage_3, "❌ 非現実的" if corrected_shortage_3 > 10 else "✓ 現実的")
    ]
    
    for name, value, assessment in scenarios:
        print(f"  {name}: {value:.1f}時間/日 - {assessment}")
    
    return scenarios

if __name__ == "__main__":
    investigate_root_cause()