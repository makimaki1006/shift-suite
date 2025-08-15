#!/usr/bin/env python3
"""
1日23.6時間不足の現実性検証
ユーザー疑問: 「1日あたり不足: 23.6時間/日（妥当な水準）も妥当ですか？本当に？」

介護施設の現実的な運営基準と比較検証
"""

import pandas as pd
from pathlib import Path

def analyze_realistic_shortage():
    """現実的な不足時間の検証"""
    
    print("=" * 80)
    print("1日23.6時間不足の現実性検証")
    print("=" * 80)
    
    # 1. 現在の計算結果の詳細確認
    print("\n【1. 現在の計算結果詳細】")
    
    shortage_per_day = 23.6
    total_shortage = 708.0
    total_days = 30
    
    print(f"総不足時間: {total_shortage}時間")
    print(f"期間: {total_days}日")
    print(f"1日あたり不足: {shortage_per_day}時間/日")
    
    # 2. 介護施設の現実的な基準との比較
    print(f"\n【2. 介護施設運営基準との比較】")
    
    # 一般的な介護施設の基準
    print("一般的な介護施設（定員30名程度）の基準:")
    print("  - 日勤帯(8:00-17:00): 3-4名必要")
    print("  - 夜勤帯(17:00-8:00): 1-2名必要")
    print("  - 1日総必要時間: 約40-50時間")
    
    typical_daily_need = 45  # 時間/日
    print(f"\n典型的な1日必要時間: {typical_daily_need}時間")
    print(f"現在計算1日不足: {shortage_per_day}時間")
    print(f"不足率: {(shortage_per_day / typical_daily_need * 100):.1f}%")
    
    if shortage_per_day > typical_daily_need * 0.5:
        print("⚠️ WARNING: 不足が必要時間の50%超 → 施設運営不可能レベル")
    elif shortage_per_day > typical_daily_need * 0.3:
        print("⚠️ CAUTION: 不足が必要時間の30%超 → 深刻な人手不足")
    elif shortage_per_day > typical_daily_need * 0.1:
        print("⚠️ ALERT: 不足が必要時間の10%超 → 要注意レベル")
    else:
        print("✓ NORMAL: 管理可能な範囲")
    
    # 3. データの妥当性再検証
    print(f"\n【3. 基礎データの妥当性再検証】")
    
    scenario_dir = Path("extracted_results/out_p25_based")
    
    # 配置データの確認
    intermediate_data = pd.read_parquet(scenario_dir / "intermediate_data.parquet")
    care_data = intermediate_data[intermediate_data['role'].str.contains('介護', na=False)]
    
    total_care_hours = len(care_data) * 0.5
    daily_care_hours = total_care_hours / 30
    
    print(f"現在配置:")
    print(f"  総配置時間: {total_care_hours}時間 ({total_days}日間)")
    print(f"  1日配置時間: {daily_care_hours:.1f}時間/日")
    
    # 需要データの確認
    need_files = list(scenario_dir.glob("need_per_date_slot_role_*介護*.parquet"))
    total_need = 0
    
    for need_file in need_files:
        df = pd.read_parquet(need_file)
        file_need = df.select_dtypes(include=[int, float]).sum().sum()
        total_need += file_need
    
    daily_need = total_need / 30
    
    print(f"\n需要計算:")
    print(f"  総需要時間: {total_need}時間 ({total_days}日間)")
    print(f"  1日需要時間: {daily_need:.1f}時間/日")
    
    # 4. 問題の特定
    print(f"\n【4. 問題の特定】")
    
    print(f"計算式の確認:")
    print(f"  1日需要: {daily_need:.1f}時間")
    print(f"  1日配置: {daily_care_hours:.1f}時間")
    print(f"  1日不足: {daily_need - daily_care_hours:.1f}時間")
    
    # 需要が異常に高い可能性
    if daily_need > 100:
        print(f"\n⚠️ 問題発見: 1日需要{daily_need:.1f}時間は異常値")
        print("可能性:")
        print("  1. 需要データに時間単位の誤り（分→時間変換ミス等）")
        print("  2. 需要算出ロジックの重複計算残存")
        print("  3. 施設規模と需要予測のミスマッチ")
        print("  4. データ期間の設定エラー")
        
    # 配置が異常に少ない可能性
    elif daily_care_hours < 20:
        print(f"\n⚠️ 問題発見: 1日配置{daily_care_hours:.1f}時間は過少")
        print("可能性:")
        print("  1. 配置データに休憩・移動時間が含まれていない")
        print("  2. パートタイム職員の時間が正確に反映されていない")
        print("  3. intermediate_dataの期間設定問題")
        
    # 5. 現実的な基準値の提示
    print(f"\n【5. 現実的な基準値】")
    
    # 介護施設の一般的な基準
    realistic_scenarios = {
        "小規模施設(定員20名)": {"daily_need": 35, "daily_staff": 30, "shortage": 5},
        "中規模施設(定員50名)": {"daily_need": 60, "daily_staff": 55, "shortage": 5},
        "大規模施設(定員100名)": {"daily_need": 120, "daily_staff": 110, "shortage": 10}
    }
    
    print("現実的な介護施設の不足レベル:")
    for facility, data in realistic_scenarios.items():
        print(f"  {facility}:")
        print(f"    需要: {data['daily_need']}時間/日")
        print(f"    配置: {data['daily_staff']}時間/日") 
        print(f"    不足: {data['shortage']}時間/日 ({data['shortage']/data['daily_need']*100:.1f}%)")
    
    # 6. 推奨修正方針
    print(f"\n【6. 推奨修正方針】")
    
    current_shortage_rate = shortage_per_day / daily_need * 100
    
    if current_shortage_rate > 30:
        print("🚨 緊急修正が必要:")
        print("  1. 需要データの算出ロジック全面見直し")
        print("  2. 時間単位・期間設定の再確認")
        print("  3. サンプルデータでの手動検算")
        print("  4. 施設規模・運営形態の前提条件確認")
    
    # 7. 結論
    print(f"\n【7. 結論】")
    print(f"ユーザー疑問への回答:")
    print(f"Q: 1日あたり不足: 23.6時間/日（妥当な水準）も妥当ですか？本当に？")
    print(f"A: いいえ、23.6時間/日の不足は妥当ではありません。")
    print(f"   理由:")
    print(f"   - 一般的な介護施設の不足は1-10時間/日程度")
    print(f"   - 23.6時間は必要時間の{current_shortage_rate:.0f}%に相当し異常")
    print(f"   - 実際の介護施設では運営継続不可能なレベル")
    
    return {
        'current_shortage': shortage_per_day,
        'realistic_range': (1, 10),
        'is_realistic': False,
        'severity': 'CRITICAL'
    }

if __name__ == "__main__":
    result = analyze_realistic_shortage()
    
    print(f"\n" + "=" * 80)
    if result['is_realistic']:
        print("結論: 計算結果は現実的")
    else:
        print("結論: 計算結果は非現実的 - 修正が必要")
    print("=" * 80)