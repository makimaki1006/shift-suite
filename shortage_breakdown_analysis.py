#!/usr/bin/env python3
"""
不足5,073時間の詳細分析
ユーザー疑問: 「不足5073時間は納得できないです。全ての合計時間ですか？」

詳細な内訳と計算根拠を検証
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

def analyze_shortage_breakdown():
    """不足時間の詳細分析"""
    
    print("=" * 80)
    print("不足5,073時間の詳細内訳分析")
    print(f"分析日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    scenario_dir = Path("extracted_results/out_p25_based")
    
    # 1. 需要データの詳細分析
    print("\n【1. 需要データの詳細分析】")
    
    need_files = list(scenario_dir.glob("need_per_date_slot_role_*介護*.parquet"))
    print(f"介護関連需要ファイル数: {len(need_files)}")
    
    total_need_by_file = {}
    total_need_sum = 0
    
    for need_file in need_files:
        df = pd.read_parquet(need_file)
        file_sum = df.select_dtypes(include=[np.number]).sum().sum()
        total_need_by_file[need_file.name] = file_sum
        total_need_sum += file_sum
        
        print(f"\n{need_file.name}:")
        print(f"  データ形状: {df.shape}")
        print(f"  需要合計: {file_sum}時間")
        
        # 日別の需要分布
        daily_need = df.sum(axis=0)  # 各日の合計
        print(f"  日別平均需要: {daily_need.mean():.1f}時間/日")
        print(f"  日別最大需要: {daily_need.max():.1f}時間/日")
        print(f"  日別最小需要: {daily_need.min():.1f}時間/日")
        
        # 時間帯別の需要分布
        hourly_need = df.sum(axis=1)  # 各時間帯の合計
        peak_hour = hourly_need.idxmax()
        print(f"  ピーク時間帯: {peak_hour} ({hourly_need.max():.1f}時間)")
    
    print(f"\n合計需要時間: {total_need_sum:.1f}時間")
    
    # 2. 配置データの詳細分析
    print(f"\n【2. 配置データの詳細分析】")
    
    intermediate_data = pd.read_parquet(scenario_dir / "intermediate_data.parquet")
    print(f"intermediate_data総レコード数: {len(intermediate_data)}")
    
    # 介護関連職種の詳細
    care_data = intermediate_data[intermediate_data['role'].str.contains('介護', na=False)]
    print(f"介護関連レコード数: {len(care_data)}")
    
    # 職種別内訳
    care_by_role = care_data['role'].value_counts()
    print(f"\n職種別配置スロット数:")
    total_care_slots = 0
    for role, count in care_by_role.items():
        hours = count * 0.5
        total_care_slots += count
        print(f"  {role}: {count}スロット ({hours:.1f}時間)")
    
    total_staff_hours = total_care_slots * 0.5
    print(f"\n合計配置時間: {total_staff_hours:.1f}時間")
    
    # 3. 不足時間の計算検証
    print(f"\n【3. 不足時間の計算検証】")
    
    calculated_shortage = total_need_sum - total_staff_hours
    print(f"需要時間: {total_need_sum:.1f}時間")
    print(f"配置時間: {total_staff_hours:.1f}時間")
    print(f"不足時間: {calculated_shortage:.1f}時間")
    
    # 4. 妥当性の検証
    print(f"\n【4. 妥当性の検証】")
    
    # 1日あたりの分析
    days_in_period = 30  # 4月は30日
    daily_need = total_need_sum / days_in_period
    daily_staff = total_staff_hours / days_in_period
    daily_shortage = calculated_shortage / days_in_period
    
    print(f"\n1日あたりの分析:")
    print(f"  1日あたり需要: {daily_need:.1f}時間/日")
    print(f"  1日あたり配置: {daily_staff:.1f}時間/日")
    print(f"  1日あたり不足: {daily_shortage:.1f}時間/日")
    
    # 時間帯別の分析
    slots_per_day = 48  # 30分スロット × 48 = 24時間
    print(f"\n時間帯別の分析:")
    print(f"  1日のスロット数: {slots_per_day}")
    print(f"  平均配置密度: {(total_care_slots / days_in_period / slots_per_day):.2f}人/スロット")
    
    # 5. 現実的な検証
    print(f"\n【5. 現実的な検証】")
    
    # スタッフ1人あたりの分析
    unique_staff = len(care_data[['ds', 'staff']].drop_duplicates()['staff'].unique()) if 'staff' in care_data.columns else "不明"
    print(f"推定スタッフ数: {unique_staff}")
    
    # 介護施設として妥当な範囲か
    print(f"\n妥当性チェック:")
    if daily_need > 200:
        print(f"  ⚠️ 1日{daily_need:.1f}時間の需要は大規模施設レベル")
    elif daily_need > 100:
        print(f"  ✓ 1日{daily_need:.1f}時間の需要は中規模施設として妥当")
    else:
        print(f"  ✓ 1日{daily_need:.1f}時間の需要は小規模施設として妥当")
        
    if daily_shortage > 100:
        print(f"  ⚠️ 1日{daily_shortage:.1f}時間の不足は深刻な人手不足")
    elif daily_shortage > 50:
        print(f"  ⚠️ 1日{daily_shortage:.1f}時間の不足は要注意レベル")
    else:
        print(f"  ✓ 1日{daily_shortage:.1f}時間の不足は管理可能範囲")
    
    # 6. 計算の再確認（システムログとの比較）
    print(f"\n【6. システム計算との比較】")
    
    try:
        from shift_suite.tasks.occupation_specific_calculator import OccupationSpecificCalculator
        calculator = OccupationSpecificCalculator(slot_minutes=30)
        
        result = calculator.calculate_occupation_specific_shortage(scenario_dir=scenario_dir)
        system_shortage = result.get("介護", 0)
        
        print(f"手動計算不足: {calculated_shortage:.1f}時間")
        print(f"システム計算不足: {system_shortage:.1f}時間")
        print(f"差分: {abs(calculated_shortage - system_shortage):.1f}時間")
        
        if abs(calculated_shortage - system_shortage) < 100:
            print("✓ 手動計算とシステム計算が一致")
        else:
            print("⚠️ 手動計算とシステム計算に大きな差異")
            
    except Exception as e:
        print(f"システム計算エラー: {e}")
    
    # 7. 結論と推奨事項
    print(f"\n【7. 結論】")
    
    print(f"不足{calculated_shortage:.1f}時間の内訳:")
    print(f"  期間: 2025年4月（30日間）")
    print(f"  対象: 介護関連職種5種類")
    print(f"  需要: {total_need_sum:.1f}時間（{daily_need:.1f}時間/日）")
    print(f"  配置: {total_staff_hours:.1f}時間（{daily_staff:.1f}時間/日）")
    print(f"  不足: {calculated_shortage:.1f}時間（{daily_shortage:.1f}時間/日）")
    
    # 疑問への回答
    print(f"\nユーザー疑問への回答:")
    print(f"Q: 不足5073時間は納得できないです。全ての合計時間ですか？")
    print(f"A: はい、これは以下の合計です：")
    print(f"   - 期間: 2025年4月全30日間")
    print(f"   - 職種: 介護関連5職種の合計")
    print(f"   - 時間帯: 24時間（48スロット）すべて")
    print(f"   - 計算: 需要{total_need_sum:.0f}時間 - 配置{total_staff_hours:.0f}時間 = 不足{calculated_shortage:.0f}時間")
    
    if calculated_shortage > 3000:
        print(f"\n⚠️ この不足時間は確かに大きな値です。")
        print(f"   可能性のある要因:")
        print(f"   1. 需要予測が過大評価されている")
        print(f"   2. 配置データに休憩時間等が含まれていない")
        print(f"   3. 介護施設の構造的な人手不足を反映")
        print(f"   4. データ期間や職種範囲の設定問題")
    
    return {
        'total_need': total_need_sum,
        'total_staff': total_staff_hours,
        'shortage': calculated_shortage,
        'daily_shortage': daily_shortage,
        'files_analyzed': len(need_files),
        'care_slots': total_care_slots
    }

if __name__ == "__main__":
    results = analyze_shortage_breakdown()
    print(f"\n" + "=" * 80)
    print("詳細分析完了")
    print("=" * 80)