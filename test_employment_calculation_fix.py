#!/usr/bin/env python3
"""
雇用形態別計算修正の検証テスト
"""
import pandas as pd
import sys
import os
sys.path.append('.')

def test_fixed_employment_calculation():
    """修正後の雇用形態別計算をテスト"""
    print("=== 修正後の雇用形態別計算テスト ===")
    
    try:
        from shift_suite.tasks.time_axis_shortage_calculator import calculate_time_axis_shortage
        
        # テストデータの作成
        test_data = pd.DataFrame({
            'staff': ['A', 'B', 'C'] * 20,
            'employment': ['パート', '正社員', 'スポット'] * 20, 
            'role': ['介護', '看護師', '介護'] * 20,
            'ds': pd.date_range('2025-04-01', periods=60, freq='30min'),
            'parsed_slots_count': [1, 1, 1] * 20
        })
        
        print(f"テストデータ: {len(test_data)}レコード")
        print(f"雇用形態: {test_data['employment'].unique()}")
        
        # 修正後の計算を実行
        role_shortages, employment_shortages = calculate_time_axis_shortage(
            test_data, 
            total_shortage_baseline=100.0  # 100時間のベースライン
        )
        
        print("\n修正後の結果:")
        print("職種別不足:")
        for role, shortage in role_shortages.items():
            print(f"  {role}: {shortage:.1f}時間")
        
        print("雇用形態別不足:")
        for emp, shortage in employment_shortages.items():
            print(f"  {emp}: {shortage:.1f}時間")
        
        # 整合性チェック
        role_total = sum(role_shortages.values())
        emp_total = sum(employment_shortages.values())
        
        ratio = emp_total / role_total if role_total > 0 else 0
        
        print(f"\n整合性チェック:")
        print(f"職種別合計: {role_total:.1f}時間")
        print(f"雇用形態別合計: {emp_total:.1f}時間")
        print(f"比率 (雇用/職種): {ratio:.2f}")
        
        if 0.8 <= ratio <= 1.2:
            print("✓ 整合性OK (±20%以内)")
            success = True
        else:
            print("❌ 整合性に問題あり")
            success = False
            
        return success
        
    except Exception as e:
        print(f"テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_circular_reference_elimination():
    """循環参照が排除されたことを確認"""
    print("\n=== 循環参照排除テスト ===")
    
    try:
        from shift_suite.tasks.time_axis_shortage_calculator import TimeAxisShortageCalculator
        
        calculator = TimeAxisShortageCalculator()
        
        # 同じ供給データで異なるベースラインをテスト
        test_supply = {'09:00': 10, '10:00': 15, '11:00': 12}
        
        # ベースライン1: 100時間
        calculator.total_shortage_baseline = 100.0
        result1 = calculator._calculate_demand_coverage(
            test_supply, pd.DataFrame(), {}, 1.0
        )
        
        # ベースライン2: 1000時間 (10倍)
        calculator.total_shortage_baseline = 1000.0
        result2 = calculator._calculate_demand_coverage(
            test_supply, pd.DataFrame(), {}, 1.0
        )
        
        print(f"ベースライン100h - 需要: {result1['total_demand']:.1f}, 不足: {result1['total_shortage']:.1f}")
        print(f"ベースライン1000h - 需要: {result2['total_demand']:.1f}, 不足: {result2['total_shortage']:.1f}")
        
        # 需要が同じであれば循環参照が排除された証拠
        demand_diff = abs(result1['total_demand'] - result2['total_demand'])
        
        if demand_diff < 1.0:  # 1時間未満の差
            print("✓ 循環参照排除成功 (需要計算が独立)")
            return True
        else:
            print(f"❌ 循環参照が残存 (需要差: {demand_diff:.1f}時間)")
            return False
            
    except Exception as e:
        print(f"循環参照テストエラー: {e}")
        return False

def main():
    print("雇用形態別計算修正の検証テスト開始")
    
    test1_success = test_fixed_employment_calculation()
    test2_success = test_circular_reference_elimination()
    
    print("\n=== 最終結果 ===")
    print(f"修正後計算テスト: {'✓ 成功' if test1_success else '❌ 失敗'}")
    print(f"循環参照排除テスト: {'✓ 成功' if test2_success else '❌ 失敗'}")
    
    if test1_success and test2_success:
        print("\n🎉 修正完了: 雇用形態別計算の9.8倍インフレーション問題を解決")
        print("統合タブの高精度モードが正常に動作します")
        return True
    else:
        print("\n⚠️ 一部テストが失敗しました")
        return False

if __name__ == "__main__":
    main()