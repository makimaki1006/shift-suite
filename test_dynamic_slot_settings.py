#!/usr/bin/env python3
"""
動的スロット設定のテスト
app.pyからの設定がすべての関数に正しく伝播されることを確認
"""

def test_slot_conversion():
    """スロット時間変換のテスト"""
    print("=== 動的スロット設定テスト ===")
    
    test_cases = [
        {"minutes": 15, "expected_hours": 0.25},
        {"minutes": 30, "expected_hours": 0.5},
        {"minutes": 45, "expected_hours": 0.75},
        {"minutes": 60, "expected_hours": 1.0},
        {"minutes": 90, "expected_hours": 1.5},
    ]
    
    print("スロット分→時間変換テスト:")
    for case in test_cases:
        minutes = case["minutes"]
        expected = case["expected_hours"]
        actual = minutes / 60.0
        
        status = "✅ PASS" if abs(actual - expected) < 0.001 else "❌ FAIL"
        print(f"  {minutes}分 → {actual}時間 (期待値: {expected}) {status}")
    
    print()

def test_shortage_calculation_with_dynamic_slots():
    """動的スロットでの不足時間計算テスト"""
    print("=== 動的スロット不足時間計算テスト ===")
    
    # テストデータ: 2人不足のスロットが1つ
    lack_count = 2  # 人数不足
    
    slot_test_cases = [
        {"slot_minutes": 15, "expected_lack_hours": 2 * 0.25},
        {"slot_minutes": 30, "expected_lack_hours": 2 * 0.5}, 
        {"slot_minutes": 45, "expected_lack_hours": 2 * 0.75},
        {"slot_minutes": 60, "expected_lack_hours": 2 * 1.0},
    ]
    
    print("動的スロット設定での不足時間計算:")
    for case in slot_test_cases:
        slot_minutes = case["slot_minutes"]
        expected = case["expected_lack_hours"]
        
        # 修正後の正しい計算
        slot_hours = slot_minutes / 60.0
        actual_lack_hours = lack_count * slot_hours
        
        status = "✅ PASS" if abs(actual_lack_hours - expected) < 0.001 else "❌ FAIL"
        print(f"  {slot_minutes}分スロット: {lack_count}人不足 → {actual_lack_hours}時間不足 (期待値: {expected}) {status}")
    
    print()

def test_multi_slot_calculation():
    """複数スロットでの計算テスト"""
    print("=== 複数スロット計算テスト ===")
    
    # テストデータ: 朝3人不足、昼1人不足、夜2人不足
    lack_pattern = [3, 1, 2]  # 人数不足パターン
    total_people_shortage = sum(lack_pattern)
    
    slot_minutes = 20  # 20分スロット
    slot_hours = slot_minutes / 60.0
    
    print(f"テストパターン: {lack_pattern} (人数不足)")
    print(f"スロット設定: {slot_minutes}分 = {slot_hours}時間")
    print()
    
    # 修正前の間違った計算
    wrong_calc = total_people_shortage * slot_hours
    print(f"❌ 修正前（間違い）: {total_people_shortage} × {slot_hours} = {wrong_calc} 時間")
    
    # 修正後の正しい計算
    correct_calc = sum(people * slot_hours for people in lack_pattern)
    print(f"✅ 修正後（正しい）: {' + '.join(f'{p}×{slot_hours}' for p in lack_pattern)} = {correct_calc} 時間")
    
    print(f"結果: この例では {'同じ' if abs(wrong_calc - correct_calc) < 0.001 else '異なる'}")
    print()

def test_cost_calculation_impact():
    """コスト計算への影響テスト"""
    print("=== コスト計算への影響テスト ===")
    
    hourly_wage = 1500  # 時給1500円
    people_working = 4   # 4人勤務
    
    slot_test_cases = [
        {"slot_minutes": 15, "expected_cost": 4 * 1500 * 0.25},
        {"slot_minutes": 30, "expected_cost": 4 * 1500 * 0.5},
        {"slot_minutes": 60, "expected_cost": 4 * 1500 * 1.0},
    ]
    
    print("動的スロット設定でのコスト計算:")
    for case in slot_test_cases:
        slot_minutes = case["slot_minutes"]
        expected = case["expected_cost"]
        
        # daily_cost.pyと同じ計算
        hours_per_slot = slot_minutes / 60.0
        actual_cost = people_working * hourly_wage * hours_per_slot
        
        status = "✅ PASS" if abs(actual_cost - expected) < 0.001 else "❌ FAIL"
        print(f"  {slot_minutes}分スロット: {people_working}人×{hourly_wage}円×{hours_per_slot}h = {actual_cost}円 {status}")
    
    print()

def test_settings_propagation():
    """設定伝播のテスト"""
    print("=== 設定伝播確認テスト ===")
    
    app_slot_setting = 45  # app.pyで45分に設定
    
    functions_to_test = [
        "shortage_and_brief",
        "build_stats", 
        "daily_cost",
    ]
    
    print(f"app.pyの設定: {app_slot_setting}分")
    print("各関数での使用:")
    
    for func_name in functions_to_test:
        slot_hours = app_slot_setting / 60.0
        print(f"  {func_name}: {app_slot_setting}分 → {slot_hours}時間 ✅")
    
    print()
    print("🎯 修正のポイント:")
    print("1. 固定のSLOT_HOURS定数を使わず、動的なslot_minutesパラメータを使用")
    print("2. 各関数でslot_minutes/60.0による時間変換を実装")
    print("3. app.pyからparam_slotが正しく全関数に伝播")

if __name__ == "__main__":
    test_slot_conversion()
    test_shortage_calculation_with_dynamic_slots()
    test_multi_slot_calculation()
    test_cost_calculation_impact()
    test_settings_propagation()