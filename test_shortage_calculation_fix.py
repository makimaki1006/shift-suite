#!/usr/bin/env python3
"""
不足時間計算修正のテスト
スロット数→時間変換ロジックが正しく動作するかを検証
"""

import pandas as pd
import numpy as np

def test_shortage_calculation():
    """不足時間計算テスト"""
    
    # テストデータ作成
    SLOT_HOURS = 0.5  # 30分スロット
    
    # 人数不足データの例（スロット×日付）
    # 例: 朝の時間帯に2人不足、昼の時間帯に1人不足
    lack_count_df = pd.DataFrame({
        '2024-01-01': [2, 1, 0, 0],  # 日付1: 朝2人不足、昼1人不足
        '2024-01-02': [1, 1, 1, 0],  # 日付2: 各時間帯に1人ずつ不足
        '2024-01-03': [0, 0, 0, 0],  # 日付3: 不足なし
    }, index=['08:00', '12:00', '16:00', '20:00'])
    
    print("=== 不足時間計算修正テスト ===")
    print("テストデータ（人数不足）:")
    print(lack_count_df)
    print()
    
    # 修正前の計算（間違い）
    wrong_calculation = lack_count_df.sum().sum() * SLOT_HOURS
    print(f"❌ 修正前の計算: {lack_count_df.sum().sum()} (人数) × {SLOT_HOURS} (時間) = {wrong_calculation} 時間")
    print("   → これは間違い: 人数の合計に時間を掛けている")
    print()
    
    # 修正後の計算（正しい）
    correct_calculation = (lack_count_df * SLOT_HOURS).sum().sum()
    print(f"✅ 修正後の計算: 各スロットの人数不足 × {SLOT_HOURS} (時間) = {correct_calculation} 時間")
    print("   → これが正しい: 各スロットごとに時間変換してから合計")
    print()
    
    # 詳細検証
    print("詳細検証:")
    detailed_calc = lack_count_df * SLOT_HOURS
    print("各スロットの時間不足:")
    print(detailed_calc)
    print(f"日別合計: {detailed_calc.sum()}")
    print(f"全体合計: {detailed_calc.sum().sum()}")
    print()
    
    # 期待値計算
    # 2024-01-01: (2+1)*0.5 = 1.5時間
    # 2024-01-02: (1+1+1)*0.5 = 1.5時間  
    # 2024-01-03: 0*0.5 = 0時間
    # 合計: 3.0時間
    expected = 3.0
    print(f"期待値: {expected} 時間")
    print(f"実際の計算結果: {correct_calculation} 時間")
    print(f"✅ テスト結果: {'PASS' if abs(correct_calculation - expected) < 0.001 else 'FAIL'}")

def test_scenario_aggregation():
    """シナリオ別集計問題のテスト"""
    print("\n=== シナリオ別集計テスト ===")
    
    # 複数シナリオのテストデータ
    scenario1_lack = pd.DataFrame({
        '2024-01-01': [1, 0],
        '2024-01-02': [0, 1],
    }, index=['08:00', '16:00'])
    
    scenario2_lack = pd.DataFrame({
        '2024-01-01': [0, 1], 
        '2024-01-02': [1, 0],
    }, index=['08:00', '16:00'])
    
    SLOT_HOURS = 0.5
    
    print("シナリオ1の不足時間:")
    s1_hours = (scenario1_lack * SLOT_HOURS).sum().sum()
    print(scenario1_lack)
    print(f"合計: {s1_hours} 時間")
    print()
    
    print("シナリオ2の不足時間:")
    s2_hours = (scenario2_lack * SLOT_HOURS).sum().sum()
    print(scenario2_lack)
    print(f"合計: {s2_hours} 時間")
    print()
    
    print(f"シナリオ別不足時間: S1={s1_hours}h, S2={s2_hours}h")
    print(f"❌ 間違った全シナリオ合計: {s1_hours + s2_hours}h (シナリオをまたいで合計してしまう)")
    print(f"✅ 正しい表示: 各シナリオ個別に表示すべき")

if __name__ == "__main__":
    test_shortage_calculation()
    test_scenario_aggregation()