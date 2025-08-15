#!/usr/bin/env python3
"""
動的データ対応修正の検証テスト
"""
import pandas as pd
import sys
import os
sys.path.append('.')

def test_dynamic_demand_calculation():
    """動的データ対応の需要計算をテスト"""
    print("=== 動的データ対応の需要計算テスト ===")
    
    try:
        from shift_suite.tasks.time_axis_shortage_calculator import TimeAxisShortageCalculator
        
        calculator = TimeAxisShortageCalculator()
        
        # テスト1: 実需要データを使用した計算
        supply_by_slot = {'09:00': 10, '10:00': 15, '11:00': 12}
        
        # 模擬需要データ
        need_data = pd.DataFrame({
            '09:00': [5, 6, 7],
            '10:00': [8, 9, 10], 
            '11:00': [4, 5, 6]
        })
        
        working_patterns = {}
        
        demand1 = calculator._calculate_realistic_demand(
            supply_by_slot, need_data, working_patterns, 0.5
        )
        
        print(f"テスト1 - 実需要データ使用: {demand1:.1f}時間")
        
        # テスト2: 働き方パターンベース計算
        working_patterns_with_peak = {
            'peak_hours': [9],
            'peak_ratio': 1.3
        }
        
        demand2 = calculator._calculate_realistic_demand(
            supply_by_slot, pd.DataFrame(), working_patterns_with_peak, 0.5
        )
        
        print(f"テスト2 - パターンベース計算: {demand2:.1f}時間")
        
        # テスト3: 供給比率ベース動的推定
        demand3 = calculator._calculate_realistic_demand(
            supply_by_slot, pd.DataFrame(), {}, 0.3  # 低い供給比率
        )
        
        print(f"テスト3 - 比率ベース推定: {demand3:.1f}時間")
        
        # 検証: 実需要データが最優先で使用されることを確認
        if abs(demand1 - 12.0) < 1.0:  # 期待値: (5+6+7+8+9+10+4+5+6)/3 * 0.5
            print("✓ 実需要データ優先計算成功")
            success1 = True
        else:
            print("❌ 実需要データ計算に問題")
            success1 = False
            
        # 検証: 動的推定が機能することを確認
        total_supply = sum(supply_by_slot.values())
        if demand2 > total_supply and demand3 > total_supply:
            print("✓ 動的推定計算成功")
            success2 = True
        else:
            print("❌ 動的推定計算に問題")
            success2 = False
            
        return success1 and success2
        
    except Exception as e:
        print(f"動的計算テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_need_data_priority():
    """need_dataの優先使用をテスト"""
    print("\n=== 需要データ優先使用テスト ===")
    
    try:
        from shift_suite.tasks.time_axis_shortage_calculator import calculate_time_axis_shortage
        
        # テストデータ作成
        working_data = pd.DataFrame({
            'staff': ['A', 'B', 'C'] * 10,
            'employment': ['パート', '正社員', 'スポット'] * 10,
            'role': ['介護', '看護師', '介護'] * 10,
            'ds': pd.date_range('2025-04-01', periods=30, freq='30min'),
            'parsed_slots_count': [1, 1, 1] * 10
        })
        
        # 実需要データを含むテスト
        need_data = pd.DataFrame({
            '09:00': [3, 4, 5] * 3,
            '09:30': [4, 5, 6] * 3,
            '10:00': [2, 3, 4] * 3
        })
        
        role_shortages, employment_shortages = calculate_time_axis_shortage(
            working_data, need_data, total_shortage_baseline=50.0
        )
        
        print("需要データありの計算結果:")
        print(f"職種別不足合計: {sum(role_shortages.values()):.1f}時間")
        print(f"雇用形態別不足合計: {sum(employment_shortages.values()):.1f}時間")
        
        # 需要データなしのテスト
        role_shortages_no_need, employment_shortages_no_need = calculate_time_axis_shortage(
            working_data, pd.DataFrame(), total_shortage_baseline=50.0
        )
        
        print("\n需要データなしの計算結果:")
        print(f"職種別不足合計: {sum(role_shortages_no_need.values()):.1f}時間")
        print(f"雇用形態別不足合計: {sum(employment_shortages_no_need.values()):.1f}時間")
        
        # 結果が異なることを確認（需要データが反映されている証拠）
        role_diff = abs(sum(role_shortages.values()) - sum(role_shortages_no_need.values()))
        emp_diff = abs(sum(employment_shortages.values()) - sum(employment_shortages_no_need.values()))
        
        if role_diff > 0.5 or emp_diff > 0.5:
            print("✓ 需要データが正しく反映されている")
            return True
        else:
            print("❌ 需要データが適切に反映されていない")
            return False
            
    except Exception as e:
        print(f"需要データ優先テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("動的データ対応修正の検証テスト開始")
    
    test1_success = test_dynamic_demand_calculation()
    test2_success = test_need_data_priority()
    
    print("\n=== 最終結果 ===")
    print(f"動的需要計算テスト: {'✓ 成功' if test1_success else '❌ 失敗'}")
    print(f"需要データ優先テスト: {'✓ 成功' if test2_success else '❌ 失敗'}")
    
    if test1_success and test2_success:
        print("\n✓ 動的データ対応修正が正常に動作")
        print("✓ 実需要データを最優先で活用")
        print("✓ 様々なデータ状況に適応可能")
        return True
    else:
        print("\n⚠️ 一部テストが失敗しました")
        return False

if __name__ == "__main__":
    main()