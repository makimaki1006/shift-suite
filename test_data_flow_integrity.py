#!/usr/bin/env python3
"""
データフロー整合性チェック
按分計算 → 時間軸計算の一貫性確認
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from shift_suite.tasks.time_axis_shortage_calculator import TimeAxisShortageCalculator
from shift_suite.tasks.proportional_calculator import calculate_proportional_shortage

def test_data_flow_consistency():
    """データフロー整合性テスト"""
    print("=== データフロー整合性チェック ===")
    
    # 複数の異なる条件でテスト
    test_scenarios = [
        {"name": "小規模データ", "days": 3, "slots_per_day": 8, "fill_rate": 0.6},
        {"name": "中規模データ", "days": 7, "slots_per_day": 16, "fill_rate": 0.7}, 
        {"name": "大規模データ", "days": 15, "slots_per_day": 24, "fill_rate": 0.8}
    ]
    
    for scenario in test_scenarios:
        print(f"\n--- {scenario['name']} ---")
        
        # テストデータ生成
        test_data = generate_scenario_data(
            scenario['days'], scenario['slots_per_day'], scenario['fill_rate']
        )
        
        # 複数の総不足時間でテスト
        baselines = [10.0, 25.0, 50.0, 100.0]
        
        for baseline in baselines:
            # 按分計算
            prop_role, prop_emp = calculate_proportional_shortage(test_data, baseline)
            prop_total = sum(prop_role.values())
            
            # 時間軸計算（修正後）
            time_role, time_emp = test_data.iloc[:0].copy(), test_data.iloc[:0].copy()  # 空DataFrame
            try:
                from shift_suite.tasks.time_axis_shortage_calculator import calculate_time_axis_shortage
                time_role, time_emp = calculate_time_axis_shortage(
                    test_data, total_shortage_baseline=baseline
                )
                time_total = sum(time_role.values())
                
                # 整合性チェック
                diff = abs(prop_total - time_total)
                diff_rate = diff / max(baseline, 1) * 100
                
                if diff_rate < 5:  # 5%以内の誤差許容
                    status = "OK"
                else:
                    status = "NG"
                
                print(f"  ベースライン{baseline:6.1f}h: 按分{prop_total:6.1f}h vs 時間軸{time_total:6.1f}h (差{diff:4.1f}h, {diff_rate:4.1f}%) [{status}]")
                
            except Exception as e:
                print(f"  ベースライン{baseline:6.1f}h: エラー - {e}")

def generate_scenario_data(days, slots_per_day, fill_rate):
    """シナリオ別テストデータ生成"""
    base_date = datetime(2025, 1, 1, 8, 0)
    roles = ['看護師', '介護職', '理学療法士', '事務員']
    staff_names = [f'職員{i:02d}' for i in range(1, 21)]  # 20名
    employments = ['常勤', 'パート', 'スポット']
    
    records = []
    
    for day in range(days):
        current_date = base_date + timedelta(days=day)
        
        for slot in range(slots_per_day):
            slot_time = current_date + timedelta(minutes=30*slot)
            
            if np.random.random() < fill_rate:
                records.append({
                    'staff': np.random.choice(staff_names),
                    'role': np.random.choice(roles, p=[0.3, 0.5, 0.1, 0.1]),
                    'employment': np.random.choice(employments, p=[0.6, 0.3, 0.1]),
                    'ds': slot_time,
                    'parsed_slots_count': 1,
                    'holiday_type': '通常勤務'
                })
    
    return pd.DataFrame(records)

def test_calculation_accuracy():
    """計算精度テスト"""
    print("\n=== 計算精度テスト ===")
    
    # 制御されたテストデータ（結果が予測可能）
    controlled_data = pd.DataFrame([
        {'staff': 'A', 'role': '職種1', 'employment': '常勤', 'ds': datetime(2025,1,1,8,0), 'parsed_slots_count': 1},
        {'staff': 'A', 'role': '職種1', 'employment': '常勤', 'ds': datetime(2025,1,1,8,30), 'parsed_slots_count': 1},
        {'staff': 'B', 'role': '職種2', 'employment': 'パート', 'ds': datetime(2025,1,1,9,0), 'parsed_slots_count': 1},
        {'staff': 'B', 'role': '職種2', 'employment': 'パート', 'ds': datetime(2025,1,1,9,30), 'parsed_slots_count': 1},
    ])
    
    baseline = 20.0
    
    # 按分計算（期待値計算）
    total_records = len(controlled_data)
    role1_records = len(controlled_data[controlled_data['role'] == '職種1'])
    role2_records = len(controlled_data[controlled_data['role'] == '職種2'])
    
    expected_role1 = baseline * (role1_records / total_records)
    expected_role2 = baseline * (role2_records / total_records)
    
    print(f"期待値計算:")
    print(f"  職種1: {expected_role1:.1f}h ({role1_records}/{total_records})")
    print(f"  職種2: {expected_role2:.1f}h ({role2_records}/{total_records})")
    
    # 実際の計算
    prop_role, _ = calculate_proportional_shortage(controlled_data, baseline)
    
    from shift_suite.tasks.time_axis_shortage_calculator import calculate_time_axis_shortage
    time_role, _ = calculate_time_axis_shortage(controlled_data, total_shortage_baseline=baseline)
    
    print(f"\n実際の計算結果:")
    print(f"  按分計算: {prop_role}")
    print(f"  時間軸計算: {time_role}")
    
    # 精度チェック
    for role in ['職種1', '職種2']:
        if role in prop_role and role in time_role:
            prop_val = prop_role[role]
            time_val = time_role[role]
            diff = abs(prop_val - time_val)
            
            if diff < 0.1:  # 0.1時間以内の誤差
                status = "精度OK"
            else:
                status = "精度NG"
            
            print(f"  {role}: 按分{prop_val:.1f}h vs 時間軸{time_val:.1f}h (差{diff:.3f}h) [{status}]")

def run_integrity_tests():
    """整合性テスト実行"""
    print("=== データフロー・計算整合性テスト開始 ===")
    print(f"実行日時: {datetime.now()}")
    
    try:
        # データフロー整合性
        test_data_flow_consistency()
        
        # 計算精度テスト
        test_calculation_accuracy()
        
        print(f"\n=== 整合性テスト完了 ===")
        print("全テストが正常に実行されました。")
        
    except Exception as e:
        print(f"テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_integrity_tests()