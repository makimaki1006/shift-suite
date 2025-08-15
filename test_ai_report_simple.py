#!/usr/bin/env python3
"""
AIレポート機能の動作確認テスト
"""

import sys
from pathlib import Path

def test_ai_report_import():
    """AIレポート機能のインポートテスト"""
    print("=== AIレポート機能インポートテスト ===")
    
    try:
        from shift_suite.tasks.ai_comprehensive_report_generator import AIComprehensiveReportGenerator
        print("OK: AIComprehensiveReportGenerator インポート成功")
        return True
    except Exception as e:
        print(f"ERROR インポートエラー: {e}")
        return False

def test_ai_report_generation():
    """AIレポート生成テスト"""
    print("\n=== AIレポート生成テスト ===")
    
    try:
        from shift_suite.tasks.ai_comprehensive_report_generator import AIComprehensiveReportGenerator
        
        # テスト用の基本データ
        test_analysis_results = {
            "shortage_analysis": {
                "lack_hours_total": 373.0,
                "excess_hours_total": 58.0
            },
            "forecast_analysis": {
                "mape": 0.049,
                "model": "ETS"
            }
        }
        
        output_dir = Path("test_ai_report_output")
        output_dir.mkdir(exist_ok=True)
        
        generator = AIComprehensiveReportGenerator()
        
        print("AIレポート生成を開始...")
        report = generator.generate_comprehensive_report(
            analysis_results=test_analysis_results,
            input_file_path="test_data.xlsx",
            output_dir=str(output_dir),
            analysis_params={"scenario": "test"}
        )
        
        print("OK: AIレポート生成成功")
        print(f"生成されたセクション数: {len(report.get('sections', []))}")
        
        # 結果をJSONファイルに保存
        import json
        output_file = output_dir / "test_ai_report.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"レポート保存場所: {output_file}")
        return True
        
    except Exception as e:
        print(f"ERROR AIレポート生成エラー: {e}")
        import traceback
        print("詳細エラー:")
        print(traceback.format_exc())
        return False

def test_ai_report_sections():
    """AIレポートの18セクション確認"""
    print("\n=== 18セクション構成確認 ===")
    
    try:
        from shift_suite.tasks.ai_comprehensive_report_generator import AIComprehensiveReportGenerator
        
        generator = AIComprehensiveReportGenerator()
        
        # セクション定義の確認
        if hasattr(generator, 'section_definitions'):
            sections = generator.section_definitions
            print(f"定義されたセクション数: {len(sections)}")
            
            for i, section in enumerate(sections, 1):
                print(f"{i:2d}. {section.get('name', 'Unknown')}")
        else:
            print("WARNING: セクション定義が見つかりません")
            
        return True
        
    except Exception as e:
        print(f"ERROR セクション確認エラー: {e}")
        return False

def main():
    """メインテスト関数"""
    print("AIレポート機能診断テスト開始")
    print("=" * 50)
    
    results = {}
    
    # 1. インポートテスト
    results['import'] = test_ai_report_import()
    
    # 2. セクション確認
    if results['import']:
        results['sections'] = test_ai_report_sections()
    
    # 3. 生成テスト  
    if results['import']:
        results['generation'] = test_ai_report_generation()
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("テスト結果サマリー:")
    print(f"インポート: {'OK' if results.get('import') else 'ERROR'}")
    print(f"セクション: {'OK' if results.get('sections') else 'ERROR'}")
    print(f"レポート生成: {'OK' if results.get('generation') else 'ERROR'}")
    
    all_passed = all(results.values())
    print(f"\n総合結果: {'OK 全テスト成功' if all_passed else 'ERROR 問題あり'}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)