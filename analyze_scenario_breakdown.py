#!/usr/bin/env python3
"""
シナリオ別数値の詳細分析
各月と3ヶ月一気の真の差異を調査
"""

def analyze_scenario_breakdown():
    """シナリオ別の詳細分析"""
    
    print("🔍 === シナリオ別数値詳細分析 ===\n")
    
    # 実際の抽出結果
    results = {
        '3ヶ月一気': {
            'total_shortage_hours': 55518.0,
            'out_median_based_shortage_hours': 55314.0,
            'out_mean_based_shortage_hours': 55518.0,
            'out_p25_based_shortage_hours': 48972.0
        },
        '7月分': {
            'total_shortage_hours': 759.0,
            'out_median_based_shortage_hours': 751.0,
            'out_mean_based_shortage_hours': 759.0,
            'out_p25_based_shortage_hours': 437.0
        },
        '8月分': {
            'total_shortage_hours': 768.0,
            'out_median_based_shortage_hours': 749.0,
            'out_mean_based_shortage_hours': 768.0,
            'out_p25_based_shortage_hours': 625.0
        },
        '9月分': {
            'total_shortage_hours': 491.0,
            'out_median_based_shortage_hours': 567.0,
            'out_mean_based_shortage_hours': 491.0,
            'out_p25_based_shortage_hours': 368.0
        }
    }
    
    print("【各シナリオの数値確認】")
    for period, data in results.items():
        print(f"\n📅 {period}:")
        print(f"  Total: {data['total_shortage_hours']:8.0f}時間")
        print(f"  平均値: {data['out_mean_based_shortage_hours']:8.0f}時間")
        print(f"  中央値: {data['out_median_based_shortage_hours']:8.0f}時間") 
        print(f"  P25値: {data['out_p25_based_shortage_hours']:8.0f}時間")
    
    print("\n" + "="*60)
    print("【シナリオ別比較分析】")
    
    scenarios = ['out_mean_based_shortage_hours', 'out_median_based_shortage_hours', 'out_p25_based_shortage_hours']
    scenario_names = ['平均値ベース', '中央値ベース', 'P25ベース']
    
    for scenario, name in zip(scenarios, scenario_names):
        print(f"\n🎯 {name} ({scenario}):")
        
        # 月別合計
        monthly_sum = (
            results['7月分'][scenario] + 
            results['8月分'][scenario] + 
            results['9月分'][scenario]
        )
        
        # 3ヶ月一気
        cumulative = results['3ヶ月一気'][scenario]
        
        # 差異計算
        diff = abs(cumulative - monthly_sum)
        diff_ratio = (diff / monthly_sum * 100) if monthly_sum > 0 else 0
        
        print(f"  月別合計: {monthly_sum:8.0f}時間 (7月{results['7月分'][scenario]:.0f} + 8月{results['8月分'][scenario]:.0f} + 9月{results['9月分'][scenario]:.0f})")
        print(f"  3ヶ月一気: {cumulative:8.0f}時間")
        print(f"  差異: {diff:8.0f}時間 ({diff_ratio:.1f}%)")
        
        if diff_ratio > 10:
            print(f"  🚨 重大な差異！期間依存性あり")
        else:
            print(f"  ✅ 妥当な範囲")
    
    print("\n" + "="*60)
    print("【Total値の正体確認】")
    
    for period, data in results.items():
        total = data['total_shortage_hours']
        mean_val = data['out_mean_based_shortage_hours']
        median_val = data['out_median_based_shortage_hours']
        p25_val = data['out_p25_based_shortage_hours']
        
        # Total = 各シナリオの合計？
        scenario_sum = mean_val + median_val + p25_val
        
        print(f"\n📊 {period}:")
        print(f"  Total値: {total:8.0f}時間")
        print(f"  3シナリオ合計: {scenario_sum:8.0f}時間 ({mean_val:.0f}+{median_val:.0f}+{p25_val:.0f})")
        print(f"  差異: {abs(total - scenario_sum):8.0f}時間")
        
        if abs(total - scenario_sum) < 10:
            print(f"  ✅ Total ≈ 3シナリオ合計 (恐らくこれが原因)")
        elif abs(total - mean_val) < 10:
            print(f"  ✅ Total ≈ 平均値ベース")
        else:
            print(f"  ❓ Total値の計算方法不明")

if __name__ == "__main__":
    analyze_scenario_breakdown()