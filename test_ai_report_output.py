# -*- coding: utf-8 -*-
"""
AI包括レポート生成機能のテスト実行
app.pyのテキスト分析結果出力機能を実際に実行してみる
"""

import sys
import os
import tempfile
import json
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

def test_ai_comprehensive_report():
    """AI包括レポート生成機能をテスト"""
    
    print("AI COMPREHENSIVE REPORT GENERATOR TEST")
    print("=" * 60)
    
    try:
        # shift_suite パスを追加
        current_dir = Path(__file__).parent
        sys.path.append(str(current_dir))
        
        # AI包括レポート生成器をインポート
        from shift_suite.tasks.ai_comprehensive_report_generator import AIComprehensiveReportGenerator
        print("✓ AIComprehensiveReportGenerator imported successfully")
        
        # テスト用分析結果データを作成
        print("\n1. Creating test analysis data...")
        
        # 模擬分析結果データ
        analysis_results = {
            'shortage_analysis': {
                'total_shortage_hours': 245.7,
                'shortage_by_role': {
                    'nurse': 120.5,
                    'caregiver': 85.2,
                    'admin': 40.0
                },
                'shortage_by_employment': {
                    'full_time': 180.2,
                    'part_time': 65.5
                }
            },
            'fatigue_analysis': {
                'average_fatigue_score': 67.8,
                'high_fatigue_staff_count': 8,
                'fatigue_distribution': {
                    'low': 12,
                    'medium': 15,
                    'high': 8
                }
            },
            'fairness_analysis': {
                'overall_fairness_score': 0.78,
                'fairness_violations': 3,
                'distribution_coefficient': 0.23
            },
            'leave_analysis': {
                'total_leave_days': 245,
                'paid_leave_ratio': 0.68,
                'unplanned_leave_ratio': 0.12
            }
        }
        
        # テスト用パラメータ
        analysis_params = {
            'input_file': 'test_shift_data.xlsx',
            'analysis_period': '2025-01-01 to 2025-01-31',
            'staff_count': 35,
            'scenarios': ['median_based', 'p25_based'],
            'slot_minutes': 30
        }
        
        # 一時出力ディレクトリ作成
        temp_dir = Path(tempfile.mkdtemp(prefix="ai_report_test_"))
        scenario_dir = temp_dir / "out_median_based"
        scenario_dir.mkdir(parents=True, exist_ok=True)
        
        # テスト用parquetファイルを作成（AIレポート生成器が期待するファイル）
        shortage_role_data = pd.DataFrame({
            'role': ['nurse', 'caregiver', 'admin', 'rehab'],
            'shortage_hours': [120.5, 85.2, 40.0, 15.3],
            'excess_hours': [0.0, 12.1, 0.0, 8.2],
            'total_need': [1200, 850, 400, 200],
            'total_supply': [1079.5, 777.9, 360, 193.1]
        })
        shortage_role_data.to_parquet(scenario_dir / "shortage_role_summary.parquet")
        
        fatigue_data = pd.DataFrame({
            'staff': [f'staff_{i:02d}' for i in range(1, 36)],
            'fatigue_score': np.random.normal(67.8, 15.2, 35).clip(0, 100),
            'workload_hours': np.random.normal(8.2, 1.8, 35).clip(4, 12),
            'consecutive_days': np.random.randint(1, 7, 35)
        })
        fatigue_data.to_parquet(scenario_dir / "fatigue_score.parquet")
        
        fairness_data = pd.DataFrame({
            'staff': [f'staff_{i:02d}' for i in range(1, 36)],
            'fairness_score': np.random.normal(0.78, 0.15, 35).clip(0, 1),
            'shift_balance': np.random.normal(0.8, 0.12, 35).clip(0, 1),
            'overtime_ratio': np.random.normal(0.15, 0.08, 35).clip(0, 0.5)
        })
        fairness_data.to_parquet(scenario_dir / "fairness_after.parquet")
        
        print(f"✓ Test parquet files created in: {scenario_dir}")
        
        # 2. AI包括レポート生成器を初期化
        print("\n2. Initializing AI Comprehensive Report Generator...")
        ai_generator = AIComprehensiveReportGenerator()
        print(f"✓ Report ID: {ai_generator.report_id}")
        
        # 3. 包括レポート生成を実行
        print("\n3. Generating comprehensive report...")
        
        comprehensive_report = ai_generator.generate_comprehensive_report(
            analysis_results=analysis_results,
            input_file_path="test_shift_data.xlsx",
            output_dir=str(temp_dir),
            analysis_params=analysis_params
        )
        
        print(f"✓ Comprehensive report generated successfully")
        print(f"  Report sections: {len(comprehensive_report)}")
        
        # 4. 生成されたレポートの内容を表示
        print("\n4. COMPREHENSIVE REPORT CONTENT PREVIEW")
        print("-" * 50)
        
        # 各セクションの概要を表示
        section_order = [
            'report_metadata',
            'execution_summary', 
            'data_quality_assessment',
            'key_performance_indicators',
            'detailed_analysis_modules',
            'systemic_problem_archetypes',
            'rule_violation_summary',
            'prediction_and_forecasting',
            'resource_optimization_insights',
            'analysis_limitations_and_external_factors',
            'summary_of_critical_observations',
            'generated_files_manifest'
        ]
        
        for section_name in section_order:
            if section_name in comprehensive_report:
                section_data = comprehensive_report[section_name]
                print(f"\n📊 {section_name.upper().replace('_', ' ')}")
                
                if isinstance(section_data, dict):
                    # 重要な情報だけを表示
                    key_items = list(section_data.keys())[:5]  # 最初の5項目
                    for key in key_items:
                        value = section_data[key]
                        if isinstance(value, (int, float)):
                            print(f"   {key}: {value}")
                        elif isinstance(value, str) and len(value) < 100:
                            print(f"   {key}: {value}")
                        elif isinstance(value, dict):
                            print(f"   {key}: {len(value)} items")
                        elif isinstance(value, list):
                            print(f"   {key}: {len(value)} items")
                    
                    if len(section_data) > 5:
                        print(f"   ... and {len(section_data) - 5} more items")
                
                elif isinstance(section_data, list):
                    print(f"   Total items: {len(section_data)}")
                    if section_data and isinstance(section_data[0], dict):
                        first_item_keys = list(section_data[0].keys())[:3]
                        print(f"   Sample keys: {first_item_keys}")
                else:
                    print(f"   Value: {section_data}")
        
        # 5. 特に重要なKPIを詳細表示
        if 'key_performance_indicators' in comprehensive_report:
            print(f"\n🎯 KEY PERFORMANCE INDICATORS DETAIL")
            print("-" * 40)
            kpis = comprehensive_report['key_performance_indicators']
            
            # 不足時間関連
            if 'shortage_metrics' in kpis:
                shortage = kpis['shortage_metrics']
                print(f"Shortage Analysis:")
                print(f"  Total shortage hours: {shortage.get('total_shortage_hours', 'N/A')}")
                print(f"  Affected roles: {shortage.get('roles_with_shortage', 'N/A')}")
                print(f"  Critical shortage threshold: {shortage.get('critical_shortage_threshold', 'N/A')}")
            
            # 疲労スコア関連
            if 'fatigue_metrics' in kpis:
                fatigue = kpis['fatigue_metrics']
                print(f"Fatigue Analysis:")
                print(f"  Average fatigue score: {fatigue.get('average_fatigue_score', 'N/A')}")
                print(f"  High fatigue staff: {fatigue.get('high_fatigue_staff_count', 'N/A')}")
                print(f"  Fatigue risk level: {fatigue.get('overall_fatigue_risk_level', 'N/A')}")
            
            # 効率性指標
            if 'efficiency_metrics' in kpis:
                efficiency = kpis['efficiency_metrics']
                print(f"Efficiency Analysis:")
                print(f"  Overall efficiency: {efficiency.get('overall_efficiency_score', 'N/A')}")
                print(f"  Resource utilization: {efficiency.get('resource_utilization_rate', 'N/A')}")
        
        # 6. 重要な観測結果を表示
        if 'summary_of_critical_observations' in comprehensive_report:
            print(f"\n🔍 CRITICAL OBSERVATIONS")
            print("-" * 30)
            observations = comprehensive_report['summary_of_critical_observations']
            
            if 'top_insights' in observations:
                insights = observations['top_insights']
                for i, insight in enumerate(insights[:5], 1):
                    if isinstance(insight, dict):
                        insight_text = insight.get('insight', insight.get('description', str(insight)))
                        severity = insight.get('severity', 'unknown')
                        print(f"{i}. [{severity.upper()}] {insight_text}")
                    else:
                        print(f"{i}. {insight}")
        
        # 7. レポートをJSONファイルとして保存
        report_file = temp_dir / f"ai_comprehensive_report_{ai_generator.report_id}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📁 REPORT SAVED")
        print(f"   File: {report_file}")
        print(f"   Size: {report_file.stat().st_size:,} bytes")
        
        # クリーンアップ
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"✓ Cleaned up temporary directory")
        
        return True, comprehensive_report
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("AI Comprehensive Report Generator is not available")
        return False, {}
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, {}

if __name__ == "__main__":
    print("Testing app.py AI Comprehensive Report Output Feature")
    print("This will show what comprehensive text analysis results look like")
    
    success, report = test_ai_comprehensive_report()
    
    print("\n" + "=" * 60)
    print("AI COMPREHENSIVE REPORT TEST RESULT")
    print("=" * 60)
    
    if success:
        print("✅ SUCCESS: AI Comprehensive Report generated successfully!")
        print(f"   Report contains {len(report)} major sections")
        print("   This demonstrates the comprehensive text analysis output capability of app.py")
        
        print(f"\n📊 REPORT STRUCTURE:")
        for section_name in report.keys():
            print(f"   • {section_name}")
        
        print(f"\nThis comprehensive report includes:")
        print("   • Detailed KPI analysis")
        print("   • System problem identification") 
        print("   • Resource optimization recommendations")
        print("   • Critical observations and insights")
        print("   • Prediction and forecasting data")
        print("   • Complete analysis metadata")
        
    else:
        print("❌ FAILED: Could not generate AI comprehensive report")
        print("   The feature may not be fully available in current environment")
    
    print(f"\nThis demonstrates app.py's comprehensive text analysis output capabilities")
    print("beyond just visualization - it provides detailed structured analysis results.")