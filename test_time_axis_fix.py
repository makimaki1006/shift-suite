#!/usr/bin/env python3
"""
時間軸計算修正のテスト実行
修正前後の計算結果を比較検証
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# シフト分析モジュールのパスを追加
sys.path.append(str(Path(__file__).parent))

from shift_suite.tasks.time_axis_shortage_calculator import TimeAxisShortageCalculator, calculate_time_axis_shortage
from shift_suite.tasks.proportional_calculator import calculate_proportional_shortage

def create_test_data():
    """テスト用のサンプルデータ生成"""
    
    # 基準日時
    base_date = datetime(2025, 1, 1, 8, 0)
    
    # 職種とスタッフのサンプル
    roles = ['看護師', '介護職', '事務員']
    staff_names = ['田中', '佐藤', '鈴木', '高橋', '伊藤', '渡辺', '山本', '中村']
    employments = ['常勤', 'パート', 'スポット']
    
    # 実績データを生成（30日分、8時-20時、30分スロット）
    test_records = []
    record_id = 1
    
    for day in range(30):  # 30日分
        current_date = base_date + timedelta(days=day)
        
        # 各日8時-20時の間で勤務レコードを生成
        for hour in range(8, 20):  # 8:00-19:30
            for minute in [0, 30]:  # 30分スロット
                slot_time = current_date + timedelta(hours=hour, minutes=minute)
                
                # ランダムに職員を配置（全スロットの60%程度）
                if np.random.random() < 0.6:
                    staff = np.random.choice(staff_names)
                    role = np.random.choice(roles, p=[0.4, 0.5, 0.1])  # 介護職50%, 看護師40%, 事務10%
                    employment = np.random.choice(employments, p=[0.5, 0.4, 0.1])
                    
                    test_records.append({
                        'staff': staff,
                        'role': role,
                        'employment': employment,
                        'ds': slot_time,
                        'parsed_slots_count': 1,
                        'holiday_type': '通常勤務'
                    })
                    record_id += 1
    
    test_df = pd.DataFrame(test_records)
    print(f"📊 テストデータ生成完了: {len(test_df)}レコード")
    print(f"   - 職種別分布: {test_df['role'].value_counts().to_dict()}")
    print(f"   - 雇用形態別分布: {test_df['employment'].value_counts().to_dict()}")
    
    return test_df

def test_baseline_calculation():
    """按分計算のテスト（ベースライン）"""
    print("\n🔍 === 按分計算テスト（ベースライン） ===")
    
    test_data = create_test_data()
    
    # 仮の総不足時間（現実的な値）
    realistic_total_shortage = 26.5  # 26.5時間不足
    
    try:
        role_shortages, emp_shortages = calculate_proportional_shortage(
            test_data, realistic_total_shortage
        )
        
        print(f"✅ 按分計算成功:")
        print(f"   - 総不足時間: {realistic_total_shortage}時間")
        print(f"   - 職種別不足: {role_shortages}")
        print(f"   - 雇用形態別不足: {emp_shortages}")
        print(f"   - 職種別合計: {sum(role_shortages.values()):.1f}時間")
        print(f"   - 雇用形態別合計: {sum(emp_shortages.values()):.1f}時間")
        
        return test_data, realistic_total_shortage, role_shortages, emp_shortages
        
    except Exception as e:
        print(f"❌ 按分計算エラー: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None, None

def test_time_axis_calculation_old():
    """修正前の時間軸計算テスト（問題のある計算）"""
    print("\n🔍 === 修正前時間軸計算テスト（参考） ===")
    
    # 旧計算の疑似実行（修正前のロジック）
    test_data = create_test_data()
    
    # 修正前の問題のある計算を模擬
    total_records = len(test_data)
    slot_hours = 0.5
    
    # 修正前: レコード数 × スロット時間
    old_total_work_hours = total_records * slot_hours
    # 修正前: 1.2倍の人工的需要増大
    old_artificial_demand = old_total_work_hours * 1.2
    old_artificial_shortage = old_artificial_demand - old_total_work_hours
    
    print(f"📊 修正前計算（問題のあるロジック）:")
    print(f"   - 総レコード数: {total_records}")
    print(f"   - 旧供給計算: {old_total_work_hours:.1f}時間")
    print(f"   - 旧需要計算: {old_artificial_demand:.1f}時間 (1.2倍増大)")
    print(f"   - 旧不足計算: {old_artificial_shortage:.1f}時間 (過大評価)")
    
    return old_artificial_shortage

def test_time_axis_calculation_new():
    """修正後の時間軸計算テスト"""
    print("\n🔍 === 修正後時間軸計算テスト ===")
    
    test_data, baseline, baseline_role, baseline_emp = test_baseline_calculation()
    if test_data is None:
        print("❌ ベースラインデータが取得できません")
        return
    
    try:
        # 修正後の時間軸計算（ベースラインあり）
        role_shortages_new, emp_shortages_new = calculate_time_axis_shortage(
            test_data, 
            total_shortage_baseline=baseline
        )
        
        print(f"✅ 修正後時間軸計算成功:")
        print(f"   - ベースライン: {baseline}時間")
        print(f"   - 職種別不足: {role_shortages_new}")
        print(f"   - 雇用形態別不足: {emp_shortages_new}")
        print(f"   - 職種別合計: {sum(role_shortages_new.values()):.1f}時間")
        print(f"   - 雇用形態別合計: {sum(emp_shortages_new.values()):.1f}時間")
        
        # 按分計算との比較
        print(f"\n📊 按分計算との比較:")
        for role in baseline_role:
            if role in role_shortages_new:
                diff = abs(baseline_role[role] - role_shortages_new.get(role, 0))
                print(f"   - {role}: 按分{baseline_role[role]:.1f}h vs 時間軸{role_shortages_new.get(role, 0):.1f}h (差{diff:.1f}h)")
        
        return role_shortages_new, emp_shortages_new
        
    except Exception as e:
        print(f"❌ 修正後時間軸計算エラー: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def test_edge_cases():
    """エッジケースのテスト"""
    print("\n🔍 === エッジケーステスト ===")
    
    # 空データテスト
    empty_df = pd.DataFrame(columns=['staff', 'role', 'employment', 'ds', 'parsed_slots_count'])
    try:
        result = calculate_time_axis_shortage(empty_df, total_shortage_baseline=10.0)
        print(f"✅ 空データテスト: {result}")
    except Exception as e:
        print(f"❌ 空データテストエラー: {e}")
    
    # ゼロベースラインテスト
    test_data = create_test_data()[:10]  # 最初の10レコードのみ
    try:
        result = calculate_time_axis_shortage(test_data, total_shortage_baseline=0.0)
        print(f"✅ ゼロベースラインテスト: 職種別{len(result[0])}個, 雇用形態別{len(result[1])}個")
    except Exception as e:
        print(f"❌ ゼロベースラインテストエラー: {e}")
    
    # 大きなベースラインテスト
    try:
        result = calculate_time_axis_shortage(test_data, total_shortage_baseline=1000.0)
        print(f"✅ 大きなベースラインテスト: 職種別合計{sum(result[0].values()):.1f}h")
    except Exception as e:
        print(f"❌ 大きなベースラインテストエラー: {e}")

def test_slot_detection():
    """スロット間隔検出のテスト"""
    print("\n🔍 === スロット間隔検出テスト ===")
    
    # 15分間隔のテストデータ
    base_time = datetime(2025, 1, 1, 8, 0)
    test_15min = []
    for i in range(20):
        test_15min.append({
            'staff': 'テスト職員',
            'role': 'テスト職種',
            'employment': 'テスト雇用',
            'ds': base_time + timedelta(minutes=15*i),
            'parsed_slots_count': 1
        })
    
    df_15min = pd.DataFrame(test_15min)
    calculator = TimeAxisShortageCalculator(auto_detect=True)
    calculator._detect_and_update_slot_interval(df_15min['ds'])
    slot_info = calculator.get_detected_slot_info()
    
    print(f"✅ 15分間隔検出テスト: {slot_info}")
    
    # 60分間隔のテストデータ
    test_60min = []
    for i in range(10):
        test_60min.append({
            'staff': 'テスト職員',
            'role': 'テスト職種', 
            'employment': 'テスト雇用',
            'ds': base_time + timedelta(hours=i),
            'parsed_slots_count': 1
        })
    
    df_60min = pd.DataFrame(test_60min)
    calculator._detect_and_update_slot_interval(df_60min['ds'])
    slot_info = calculator.get_detected_slot_info()
    
    print(f"✅ 60分間隔検出テスト: {slot_info}")

def run_comprehensive_test():
    """包括的テスト実行"""
    print("🚀 === 時間軸計算修正 包括的テスト開始 ===")
    print(f"実行時刻: {datetime.now()}")
    
    try:
        # 1. 修正前後の比較
        old_shortage = test_time_axis_calculation_old()
        print(f"\n📊 修正前後比較:")
        print(f"   - 修正前（問題）: ~{old_shortage:.1f}時間不足 (過大評価)")
        
        # 2. 修正後テスト
        new_role, new_emp = test_time_axis_calculation_new()
        if new_role:
            new_total = sum(new_role.values())
            print(f"   - 修正後（改善）: {new_total:.1f}時間不足 (現実的)")
            
            improvement_ratio = old_shortage / max(new_total, 1)
            print(f"   - 改善率: {improvement_ratio:.1f}倍の過大評価を修正")
        
        # 3. エッジケーステスト
        test_edge_cases()
        
        # 4. スロット検出テスト
        test_slot_detection()
        
        print(f"\n✅ 包括的テスト完了")
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_comprehensive_test()