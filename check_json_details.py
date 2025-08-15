#!/usr/bin/env python3
"""
AI包括レポートJSONの詳細確認
"""

import zipfile
import json
from pathlib import Path

def check_json_values():
    zip_path = "analysis_results (55).zip"
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # AI包括レポートを探す
        json_files = [f for f in zf.namelist() if 'comprehensive' in f and f.endswith('.json')]
        
        if not json_files:
            print("AI包括レポートが見つかりません")
            return
            
        json_file = json_files[0]
        print(f"📄 {json_file} の詳細分析")
        print("=" * 80)
        
        with zf.open(json_file) as f:
            data = json.load(f)
        
        # KPIセクションの確認
        if 'key_performance_indicators' in data:
            kpi = data['key_performance_indicators']
            print("\n🎯 主要パフォーマンス指標 (KPI):")
            
            # overall_performanceの確認
            if 'overall_performance' in kpi:
                overall = kpi['overall_performance']
                print("\n  【総合パフォーマンス】")
                
                # 不足時間の確認
                if 'total_shortage_hours' in overall:
                    shortage_hours = overall['total_shortage_hours']
                    print(f"    総不足時間:")
                    print(f"      value: {shortage_hours.get('value', 'なし')}")
                    print(f"      unit: {shortage_hours.get('unit', 'なし')}")
                    print(f"      trend: {shortage_hours.get('trend', 'なし')}")
                    print(f"      severity: {shortage_hours.get('severity', 'なし')}")
                    
                    # 値の妥当性チェック
                    value = shortage_hours.get('value', 0)
                    if isinstance(value, (int, float)):
                        if value == 0:
                            print("      ⚠️ 警告: 不足時間が0です")
                        elif value > 10000:
                            print("      ⚠️ 警告: 不足時間が異常に大きいです")
                        else:
                            print("      ✅ 不足時間は妥当な範囲です")
                
                # 他のメトリクス
                for metric_name, metric_data in overall.items():
                    if metric_name != 'total_shortage_hours' and isinstance(metric_data, dict):
                        print(f"\n    {metric_name}:")
                        print(f"      value: {metric_data.get('value', 'なし')}")
                        if metric_data.get('value') == 0 or metric_data.get('value') == "0":
                            print(f"      ⚠️ デフォルト値の可能性")
        
        # 詳細分析モジュールの確認
        if 'detailed_analysis_modules' in data:
            modules = data['detailed_analysis_modules']
            print("\n\n📊 詳細分析モジュール:")
            
            # 不足分析
            if 'shortage_analysis' in modules:
                shortage = modules['shortage_analysis']
                print("\n  【不足分析】")
                print(f"    analysis_period: {shortage.get('analysis_period', 'なし')}")
                print(f"    total_shortage_incidents: {shortage.get('total_shortage_incidents', 'なし')}")
                
                # 詳細データの確認
                if 'detailed_metrics' in shortage:
                    details = shortage['detailed_metrics']
                    print(f"    詳細メトリクス:")
                    for k, v in details.items():
                        if isinstance(v, (int, float, str)):
                            print(f"      {k}: {v}")
                            if v == 0 or v == "0" or v == "N/A":
                                print(f"        ⚠️ デフォルト値の可能性")
            
            # 疲労分析
            if 'fatigue_analysis' in modules:
                fatigue = modules['fatigue_analysis']
                print("\n  【疲労分析】")
                if 'metrics' in fatigue:
                    for k, v in fatigue['metrics'].items():
                        print(f"    {k}: {v}")
            
            # 公平性分析
            if 'fairness_analysis' in modules:
                fairness = modules['fairness_analysis']
                print("\n  【公平性分析】")
                if 'metrics' in fairness:
                    for k, v in fairness['metrics'].items():
                        print(f"    {k}: {v}")
        
        # デフォルト値の統計
        print("\n\n📈 デフォルト値の統計:")
        default_count = 0
        actual_count = 0
        
        def count_values(obj):
            nonlocal default_count, actual_count
            if isinstance(obj, dict):
                for v in obj.values():
                    if v in [0, 0.0, "0", "N/A", "default", None, "", []]:
                        default_count += 1
                    else:
                        actual_count += 1
                    if isinstance(v, (dict, list)):
                        count_values(v)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, (dict, list)):
                        count_values(item)
        
        count_values(data)
        total = default_count + actual_count
        if total > 0:
            print(f"  実データ数: {actual_count}")
            print(f"  デフォルト値数: {default_count}")
            print(f"  実データ率: {actual_count/total*100:.1f}%")
            
            if actual_count/total > 0.8:
                print(f"  ✅ 実データ率は良好です（80%以上）")
            else:
                print(f"  ⚠️ デフォルト値が多すぎます")

if __name__ == "__main__":
    check_json_values()