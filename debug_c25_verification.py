"""
C2.5検証デバッグ
"""
import os
import json
import glob

base_path = "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析"

print("=== C2.5検証デバッグ ===")

# C2.5レポートファイル確認
report_files = [f for f in os.listdir(base_path) 
               if f.startswith('C2_5_Final_Verification_Report_') and f.endswith('.md')]

print(f"📄 C2.5レポートファイル: {len(report_files)}件")
for f in report_files:
    print(f"  - {f}")

if report_files:
    latest_report = sorted(report_files)[-1]
    report_path = os.path.join(base_path, latest_report)
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\n📋 {latest_report} 内容確認:")
    
    indicators = [
        "総合評価: 成功",
        "品質スコア: 9",
        "既存機能の100%保護",
        "モバイルユーザビリティの大幅向上"
    ]
    
    for indicator in indicators:
        found = indicator in content
        status = "✅" if found else "❌"
        print(f"  {status} {indicator}")
        if not found and "品質スコア" in indicator:
            # 品質スコア部分を抽出
            lines = content.split('\n')
            score_lines = [line for line in lines if '品質スコア' in line or 'スコア' in line]
            print(f"    実際のスコア記載: {score_lines}")

# C2.5結果ファイル確認
result_files = [f for f in os.listdir(base_path) 
               if f.startswith('C2_5_Comprehensive_Test_Results_') and f.endswith('.json')]

print(f"\n📊 C2.5結果ファイル: {len(result_files)}件")
for f in result_files:
    print(f"  - {f}")

if result_files:
    latest_result = sorted(result_files)[-1]
    result_path = os.path.join(base_path, latest_result)
    
    with open(result_path, 'r', encoding='utf-8') as f:
        result_data = json.load(f)
    
    print(f"\n📈 {latest_result} 詳細:")
    print(f"  success: {result_data.get('success', 'N/A')}")
    print(f"  quality_score: {result_data.get('quality_score', 'N/A')}")
    
    if 'overall_evaluation' in result_data:
        overall = result_data['overall_evaluation']
        print(f"  overall_success: {overall.get('overall_success', 'N/A')}")
        print(f"  meets_success_criteria: {overall.get('meets_success_criteria', 'N/A')}")