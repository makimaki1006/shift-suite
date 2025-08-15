#!/usr/bin/env python
"""
具体的問題点の検証

ユーザー指摘の現状問題が解決されているかを確認
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

# 実装したモジュールのインポート
from unified_shortage_calculator import calculate_true_shortage
from dynamic_parameter_patch import shortage_and_brief_enhanced
from robust_time_axis_processor import process_time_data_for_analysis

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def verify_logic_consistency_problem():
    """
    問題1: 全体分析と職種別分析のロジック統一
    
    従来の問題:
    - 全体: 負の値も含む（真の過不足）
    - 職種別: clip(lower=0)で不足のみ計上
    """
    
    print("=== 問題1: 分析ロジック統一の検証 ===")
    
    # テストシナリオ: 過剰配置がある状況
    # 需要より多くのスタッフが配置されている時間帯を含む
    
    # 需要データ（人数・時間帯）
    need_df = pd.DataFrame({
        'Day1': [2, 1, 3],  # 時間帯別需要
        'Day2': [1, 2, 1],
        'Day3': [3, 1, 2]
    }, index=['09:00', '10:00', '11:00'])
    
    # スタッフ配置データ（人数・時間帯）
    staff_df = pd.DataFrame({
        'Day1': [3, 1, 2],  # 09:00は過剰配置(3>2)
        'Day2': [1, 3, 1],  # 10:00は過剰配置(3>2)  
        'Day3': [2, 1, 3]   # 11:00は過剰配置(3>2)
    }, index=['09:00', '10:00', '11:00'])
    
    print("テストデータ:")
    print("需要:")
    print(need_df)
    print("\nスタッフ配置:")
    print(staff_df)
    
    # 統一計算システムによる分析
    results = calculate_true_shortage(need_df, staff_df, slot_hours=0.5)
    
    print(f"\n=== 統一計算結果 ===")
    print(f"真の過不足（正:不足、負:過剰）:")
    print(results['true_balance'])
    
    print(f"\n不足のみ:")
    print(results['shortage_only'])
    
    print(f"\n過剰のみ:")
    print(results['excess_only'])
    
    print(f"\n時間換算サマリー:")
    print(f"  実質過不足: {results['net_hours']:.1f}時間")
    print(f"  不足時間: {results['shortage_hours']:.1f}時間")
    print(f"  過剰時間: {results['excess_hours']:.1f}時間")
    
    # 検証項目
    has_true_balance = 'true_balance' in results
    has_shortage_only = 'shortage_only' in results  
    has_excess_only = 'excess_only' in results
    
    # 真の過不足で負の値（過剰）が適切に記録されているか
    has_negative_values = (results['true_balance'] < 0).any().any()
    
    # 不足のみで負の値がないか（clip済み）
    shortage_no_negative = (results['shortage_only'] >= 0).all().all()
    
    # 過剰のみで負の値がないか（clip済み）
    excess_no_negative = (results['excess_only'] >= 0).all().all()
    
    logic_unified = (has_true_balance and has_shortage_only and has_excess_only and 
                     has_negative_values and shortage_no_negative and excess_no_negative)
    
    print(f"\n=== 検証結果 ===")
    print(f"[OK] 真の過不足計算: {has_true_balance}")
    print(f"[OK] 不足のみ分離: {has_shortage_only}")  
    print(f"[OK] 過剰のみ分離: {has_excess_only}")
    print(f"[OK] 負の値（過剰）を適切に記録: {has_negative_values}")
    print(f"[OK] 不足のみでclip適用: {shortage_no_negative}")
    print(f"[OK] 過剰のみでclip適用: {excess_no_negative}")
    
    print(f"\n[{'成功' if logic_unified else '失敗'}] 分析ロジック統一: {logic_unified}")
    
    return {
        'success': logic_unified,
        'details': {
            'true_balance_available': has_true_balance,
            'shortage_only_available': has_shortage_only,
            'excess_only_available': has_excess_only,
            'negative_values_recorded': has_negative_values,
            'shortage_properly_clipped': shortage_no_negative,
            'excess_properly_clipped': excess_no_negative
        }
    }

def verify_dynamic_data_adaptation_problem():
    """
    問題2: 動的データへの対応
    
    従来の問題:
    - 期間、職種、時間帯が変動する動的データへの対応が不完全
    - 固定的な前提での計算
    """
    
    print("\n=== 問題2: 動的データ対応の検証 ===")
    
    # テストシナリオ1: 期間の動的変動（3日→14日→5日）
    print("\n[テスト1] 期間の動的変動")
    
    def create_dynamic_period_data(days, roles, time_slots_per_day):
        """動的期間データの生成"""
        dates = pd.date_range('2025-01-01', periods=days, freq='D')
        time_slots = [f"{hour:02d}:00" for hour in range(9, 9+time_slots_per_day)]
        
        data = []
        for date in dates:
            for time_slot in time_slots:
                for role in roles:
                    data.append({
                        'ds': pd.Timestamp.combine(date.date(), pd.Timestamp(time_slot).time()),
                        'staff': f'Staff_{len(data)%3}',
                        'role': role,
                        'need': np.random.randint(1, 4),
                        'allocation': np.random.randint(0, 3)
                    })
        return pd.DataFrame(data)
    
    # 異なる期間でのテスト
    test_periods = [
        (3, ['介護', '看護'], 4, "短期間（3日・2職種・4時間帯）"),
        (14, ['介護', '看護', '事務', 'リハビリ'], 8, "中期間（14日・4職種・8時間帯）"),
        (5, ['新人研修', '夜間巡回'], 6, "カスタム期間（5日・新職種・6時間帯）")
    ]
    
    period_results = []
    
    for days, roles, time_slots, description in test_periods:
        print(f"\n  {description}:")
        
        try:
            # 動的データ生成
            test_df = create_dynamic_period_data(days, roles, time_slots)
            
            # 時間軸処理（動的対応）
            processed_df, slider_config = process_time_data_for_analysis(test_df)
            
            # 期間の正確な検出
            detected_days = slider_config['metadata']['total_days']
            period_correct = detected_days == days
            
            # 職種の動的認識
            detected_roles = len(processed_df['role'].unique())
            roles_correct = detected_roles == len(roles)
            
            # 時間帯の動的処理
            detected_time_slots = len(processed_df['ds'].dt.hour.unique())
            time_slots_handled = detected_time_slots > 0
            
            success = period_correct and roles_correct and time_slots_handled
            
            print(f"    期間検出: {detected_days}日 (期待: {days}日) - {'[OK]' if period_correct else '[NG]'}")
            print(f"    職種認識: {detected_roles}職種 (期待: {len(roles)}職種) - {'[OK]' if roles_correct else '[NG]'}")
            print(f"    時間帯処理: {detected_time_slots}時間帯 - {'[OK]' if time_slots_handled else '[NG]'}")
            print(f"    総合: {'成功' if success else '失敗'}")
            
            period_results.append({
                'description': description,
                'success': success,
                'detected_days': detected_days,
                'expected_days': days,
                'detected_roles': detected_roles,
                'expected_roles': len(roles)
            })
            
        except Exception as e:
            print(f"    エラー: {e}")
            period_results.append({
                'description': description,
                'success': False,
                'error': str(e)
            })
    
    # テストシナリオ2: スロット時間の動的変動
    print(f"\n[テスト2] スロット時間の動的変動")
    
    # 様々なスロット時間でのテスト
    slot_variations = [0.25, 0.5, 1.0, 1.5]  # 15分、30分、1時間、1.5時間
    
    # 基準データ
    base_need = pd.DataFrame([[2, 3]], index=['09:00'], columns=['Day1', 'Day2'])
    base_staff = pd.DataFrame([[1, 2]], index=['09:00'], columns=['Day1', 'Day2'])
    
    slot_results = []
    for slot_hours in slot_variations:
        try:
            result = calculate_true_shortage(base_need, base_staff, slot_hours)
            
            # 時間に比例した結果になっているか
            expected_net_hours = (2-1 + 3-2) * slot_hours  # (need-staff) * slot_hours
            actual_net_hours = result['net_hours']
            scaling_correct = abs(actual_net_hours - expected_net_hours) < 0.01
            
            print(f"    {slot_hours}時間スロット: {actual_net_hours:.1f}h (期待: {expected_net_hours:.1f}h) - {'[OK]' if scaling_correct else '[NG]'}")
            
            slot_results.append({
                'slot_hours': slot_hours,
                'success': scaling_correct,
                'actual': actual_net_hours,
                'expected': expected_net_hours
            })
            
        except Exception as e:
            print(f"    {slot_hours}時間スロット: エラー - {e}")
            slot_results.append({
                'slot_hours': slot_hours,
                'success': False,
                'error': str(e)
            })
    
    # 総合評価
    period_success_rate = sum(1 for r in period_results if r.get('success', False)) / len(period_results)
    slot_success_rate = sum(1 for r in slot_results if r.get('success', False)) / len(slot_results)
    
    overall_dynamic_success = period_success_rate >= 0.8 and slot_success_rate >= 0.8
    
    print(f"\n=== 動的データ対応 検証結果 ===")
    print(f"期間変動対応: {period_success_rate*100:.0f}% ({sum(1 for r in period_results if r.get('success', False))}/{len(period_results)})")
    print(f"スロット変動対応: {slot_success_rate*100:.0f}% ({sum(1 for r in slot_results if r.get('success', False))}/{len(slot_results)})")
    print(f"[{'成功' if overall_dynamic_success else '失敗'}] 動的データ対応: {overall_dynamic_success}")
    
    return {
        'success': overall_dynamic_success,
        'period_results': period_results,
        'slot_results': slot_results,
        'period_success_rate': period_success_rate,
        'slot_success_rate': slot_success_rate
    }

def verify_fixed_assumptions_problem():
    """
    問題3: 固定的前提の解消
    
    従来の問題:
    - 固定された期間・職種・時間帯での計算
    - 変動する実際の運用への対応不足
    """
    
    print("\n=== 問題3: 固定的前提の解消検証 ===")
    
    # テスト: 完全に異なる前提条件での計算
    scenarios = [
        {
            'name': '従来想定（30分・7日・3職種）',
            'slot_hours': 0.5,
            'days': 7,
            'roles': ['介護', '看護', '事務']
        },
        {
            'name': '新想定1（15分・10日・5職種）', 
            'slot_hours': 0.25,
            'days': 10,
            'roles': ['介護', '看護', '事務', 'リハビリ', 'レクリエーション']
        },
        {
            'name': '新想定2（1時間・3日・2職種）',
            'slot_hours': 1.0,
            'days': 3,
            'roles': ['夜間巡回', '新人研修']
        },
        {
            'name': '極端想定（2時間・21日・7職種）',
            'slot_hours': 2.0,
            'days': 21,
            'roles': ['管理職', '清掃', '調理', '送迎', '相談員', '看護師長', '介護主任']
        }
    ]
    
    scenario_results = []
    
    for scenario in scenarios:
        print(f"\n[{scenario['name']}]:")
        
        try:
            # 動的データ生成
            dates = pd.date_range('2025-01-01', periods=scenario['days'], freq='D')
            
            # 需要・配置データの生成（職種数と日数に応じて）
            need_data = np.random.randint(1, 5, size=(len(scenario['roles']), len(dates)))
            staff_data = np.random.randint(0, 4, size=(len(scenario['roles']), len(dates)))
            
            need_df = pd.DataFrame(need_data, 
                                 index=scenario['roles'],
                                 columns=[f'Day_{i+1}' for i in range(len(dates))])
            
            staff_df = pd.DataFrame(staff_data,
                                  index=scenario['roles'], 
                                  columns=[f'Day_{i+1}' for i in range(len(dates))])
            
            # 統一計算システムで処理
            result = calculate_true_shortage(need_df, staff_df, scenario['slot_hours'])
            
            # 計算の妥当性チェック
            calculation_valid = result['validation']['calculation_accuracy']
            data_shape_handled = result['calculation_params']['data_shape'] == need_df.shape
            slot_hours_applied = result['calculation_params']['slot_hours'] == scenario['slot_hours']
            
            success = calculation_valid and data_shape_handled and slot_hours_applied
            
            print(f"  データ形状: {need_df.shape} (職種×日数)")
            print(f"  スロット時間: {scenario['slot_hours']}h")
            print(f"  計算精度: {'[OK]' if calculation_valid else '[NG]'}")
            print(f"  形状処理: {'[OK]' if data_shape_handled else '[NG]'}")
            print(f"  パラメータ適用: {'[OK]' if slot_hours_applied else '[NG]'}")
            print(f"  実質過不足: {result['net_hours']:.1f}h")
            print(f"  総合: {'成功' if success else '失敗'}")
            
            scenario_results.append({
                'scenario': scenario['name'],
                'success': success,
                'shape': need_df.shape,
                'slot_hours': scenario['slot_hours'],
                'net_hours': result['net_hours']
            })
            
        except Exception as e:
            print(f"  エラー: {e}")
            scenario_results.append({
                'scenario': scenario['name'],
                'success': False,
                'error': str(e)
            })
    
    # 固定前提解消の評価
    flexible_success_rate = sum(1 for r in scenario_results if r.get('success', False)) / len(scenario_results)
    fixed_assumptions_resolved = flexible_success_rate >= 0.75
    
    print(f"\n=== 固定的前提の解消 検証結果 ===")
    print(f"柔軟性対応: {flexible_success_rate*100:.0f}% ({sum(1 for r in scenario_results if r.get('success', False))}/{len(scenario_results)})")
    print(f"[{'成功' if fixed_assumptions_resolved else '失敗'}] 固定前提の解消: {fixed_assumptions_resolved}")
    
    return {
        'success': fixed_assumptions_resolved,
        'scenario_results': scenario_results,
        'flexibility_success_rate': flexible_success_rate
    }

def main():
    """メイン検証実行"""
    
    print("現状問題点の解決確認")
    print("=" * 60)
    
    # 各問題の検証
    problem1_result = verify_logic_consistency_problem()
    problem2_result = verify_dynamic_data_adaptation_problem()
    problem3_result = verify_fixed_assumptions_problem()
    
    # 総合結果
    print("\n" + "=" * 60)
    print("問題解決状況サマリー")
    print("=" * 60)
    
    problems = [
        ("問題1: 分析ロジック統一", problem1_result['success']),
        ("問題2: 動的データ対応", problem2_result['success']),
        ("問題3: 固定前提の解消", problem3_result['success'])
    ]
    
    total_problems = len(problems)
    solved_problems = sum(1 for _, solved in problems if solved)
    
    print(f"解決済み問題: {solved_problems}/{total_problems}")
    print(f"解決率: {solved_problems/total_problems*100:.1f}%")
    
    print("\n詳細:")
    for problem_name, solved in problems:
        status = "[解決]" if solved else "[未解決]"
        print(f"  {status} {problem_name}")
    
    if solved_problems == total_problems:
        print(f"\n指摘された全ての問題が解決されました！")
    else:
        print(f"\n{total_problems - solved_problems}問題が残存しています。")
    
    return {
        'problem1': problem1_result,
        'problem2': problem2_result, 
        'problem3': problem3_result,
        'overall_success': solved_problems == total_problems
    }

if __name__ == "__main__":
    validation_results = main()