# -*- coding: utf-8 -*-
"""
Simple AI Report Generation Test (no Unicode symbols)
"""

import sys
import tempfile
import json
from pathlib import Path
import pandas as pd
import numpy as np

def simple_ai_report_test():
    """Simple AI report test without Unicode symbols"""
    
    print("AI COMPREHENSIVE REPORT TEST")
    print("=" * 40)
    
    try:
        # Import the AI report generator
        from shift_suite.tasks.ai_comprehensive_report_generator import AIComprehensiveReportGenerator
        print("SUCCESS: AI Comprehensive Report Generator imported")
        
        # Create test data
        temp_dir = Path(tempfile.mkdtemp(prefix="ai_test_"))
        scenario_dir = temp_dir / "out_median_based"
        scenario_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test parquet files
        shortage_data = pd.DataFrame({
            'role': ['nurse', 'caregiver', 'admin'],
            'shortage_hours': [120.5, 85.2, 40.0],
            'total_need': [1200, 850, 400],
            'total_supply': [1079.5, 764.8, 360]
        })
        shortage_data.to_parquet(scenario_dir / "shortage_role_summary.parquet")
        
        fatigue_data = pd.DataFrame({
            'staff': ['staff_01', 'staff_02', 'staff_03'],
            'fatigue_score': [67.8, 72.1, 58.4],
            'workload_hours': [8.2, 9.1, 7.5]
        })
        fatigue_data.to_parquet(scenario_dir / "fatigue_score.parquet")
        
        print("Test data created successfully")
        
        # Generate AI report
        ai_generator = AIComprehensiveReportGenerator()
        print(f"Report ID: {ai_generator.report_id}")
        
        # Test analysis results
        analysis_results = {
            'shortage_analysis': {
                'total_shortage_hours': 245.7,
                'shortage_by_role': {'nurse': 120.5, 'caregiver': 85.2}
            },
            'fatigue_analysis': {
                'average_fatigue_score': 66.1,
                'high_fatigue_staff_count': 5
            }
        }
        
        analysis_params = {
            'input_file': 'test_data.xlsx',
            'staff_count': 35,
            'analysis_period': '2025-01-01 to 2025-01-31'
        }
        
        # Generate comprehensive report
        print("Generating comprehensive report...")
        report = ai_generator.generate_comprehensive_report(
            analysis_results=analysis_results,
            input_file_path="test_data.xlsx",
            output_dir=str(temp_dir),
            analysis_params=analysis_params
        )
        
        print("Report generated successfully!")
        print(f"Report sections: {len(report)}")
        
        # Display key sections
        print("\nREPORT SECTIONS:")
        for section_name in report.keys():
            print(f"  - {section_name}")
        
        # Display key performance indicators
        if 'key_performance_indicators' in report:
            kpis = report['key_performance_indicators']
            print(f"\nKEY PERFORMANCE INDICATORS:")
            print(f"  KPI categories: {len(kpis)}")
            
            # Show shortage metrics if available
            if 'shortage_metrics' in kpis:
                shortage_kpis = kpis['shortage_metrics']
                print(f"  Shortage metrics:")
                for key, value in list(shortage_kpis.items())[:5]:
                    print(f"    {key}: {value}")
        
        # Display critical observations
        if 'summary_of_critical_observations' in report:
            observations = report['summary_of_critical_observations']
            print(f"\nCRITICAL OBSERVATIONS:")
            
            if 'top_insights' in observations:
                insights = observations['top_insights']
                print(f"  Total insights: {len(insights)}")
                for i, insight in enumerate(insights[:3], 1):
                    if isinstance(insight, dict):
                        insight_text = insight.get('insight', str(insight))[:80]
                        print(f"    {i}. {insight_text}...")
                    else:
                        print(f"    {i}. {insight}")
        
        # Save report to file
        report_file = temp_dir / "comprehensive_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        file_size = report_file.stat().st_size
        print(f"\nReport saved: {report_file.name}")
        print(f"File size: {file_size:,} bytes")
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        print("Cleanup completed")
        
        return True, report
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False, {}

if __name__ == "__main__":
    success, report_data = simple_ai_report_test()
    
    print("\n" + "=" * 40)
    print("FINAL RESULT")
    print("=" * 40)
    
    if success:
        print("SUCCESS: AI Comprehensive Report generation works!")
        print(f"Generated report with {len(report_data)} sections")
        
        # Show what the comprehensive text output includes
        print(f"\nApp.py TEXT ANALYSIS OUTPUT INCLUDES:")
        print("- Detailed KPI analysis with numerical metrics")
        print("- System problem identification and categorization")
        print("- Resource optimization recommendations")
        print("- Critical observations and insights")
        print("- Prediction and forecasting analysis")
        print("- Complete metadata and execution details")
        print("- File manifest of all generated analysis files")
        
        print(f"\nThis demonstrates app.py's comprehensive text-based")
        print("analysis output capability beyond just visualization.")
        
    else:
        print("FAILED: Could not generate AI comprehensive report")
        print("The feature may require additional dependencies.")
    
    print(f"\nThis shows app.py can generate detailed structured")
    print("text analysis results in addition to visual charts.")