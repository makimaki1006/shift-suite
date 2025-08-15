#!/usr/bin/env python3
"""
AIレポート生成の詳細デバッグ
"""

import sys
from pathlib import Path
import json

def debug_ai_report_generation():
    """AIレポート生成の詳細デバッグ"""
    print("=== AIレポート生成詳細デバッグ ===")
    
    try:
        from shift_suite.tasks.ai_comprehensive_report_generator import AIComprehensiveReportGenerator
        
        # テスト用のデータ準備
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
        
        test_output_dir = Path("debug_ai_output")
        test_output_dir.mkdir(exist_ok=True)
        
        print(f"出力ディレクトリ: {test_output_dir}")
        print(f"分析結果データ: {test_analysis_results}")
        
        # AIレポート生成の実行
        print("\nAIレポートジェネレーターの初期化...")
        generator = AIComprehensiveReportGenerator()
        print(f"レポートID: {generator.report_id}")
        
        print("\nAIレポート生成実行...")
        report = generator.generate_comprehensive_report(
            analysis_results=test_analysis_results,
            input_file_path="test_data.xlsx",
            output_dir=str(test_output_dir),
            analysis_params={"scenario": "median_based"}
        )
        
        print("AIレポート生成完了")
        print(f"生成されたセクション数: {len(report)}")
        
        # セクション一覧の表示
        print("\n生成されたセクション:")
        for i, (key, value) in enumerate(report.items(), 1):
            print(f"{i:2d}. {key}")
        
        # ファイル確認
        print(f"\n出力ディレクトリの内容確認:")
        if test_output_dir.exists():
            files = list(test_output_dir.glob("*"))
            if files:
                for file in files:
                    size_kb = file.stat().st_size / 1024
                    print(f"  - {file.name} ({size_kb:.1f} KB)")
            else:
                print("  ファイルが見つかりません！")
        
        # 予想されるファイル名の確認
        expected_file = test_output_dir / f"ai_comprehensive_report_{generator.report_id}.json"
        print(f"\n予想ファイル名: {expected_file}")
        print(f"ファイル存在確認: {expected_file.exists()}")
        
        if expected_file.exists():
            file_size = expected_file.stat().st_size / 1024
            print(f"ファイルサイズ: {file_size:.1f} KB")
            
            # ファイル内容の簡易確認
            try:
                with open(expected_file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                print(f"JSONファイル読み込み成功: {len(content)} 項目")
            except Exception as e:
                print(f"JSONファイル読み込みエラー: {e}")
        
        return True
        
    except Exception as e:
        print(f"エラー発生: {e}")
        import traceback
        print("\n詳細エラー:")
        print(traceback.format_exc())
        return False

def debug_app_integration():
    """app.pyでの統合確認"""
    print("\n=== app.py統合デバッグ ===")
    
    # AI_REPORT_GENERATOR_AVAILABLEフラグの確認
    try:
        from shift_suite.tasks.ai_comprehensive_report_generator import AIComprehensiveReportGenerator
        print("OK: AIComprehensiveReportGenerator インポート成功")
        print("AI_REPORT_GENERATOR_AVAILABLE = True")
    except ImportError as e:
        print(f"ERROR: AIComprehensiveReportGenerator インポート失敗: {e}")
        print("AI_REPORT_GENERATOR_AVAILABLE = False")
        return False
    
    # extracted_resultsディレクトリの確認
    results_dir = Path("extracted_results")
    if results_dir.exists():
        print(f"extracted_resultsディレクトリ存在: {results_dir}")
        
        # out ディレクトリの確認
        out_dirs = []
        for scenario in ["out_mean_based", "out_median_based", "out_p25_based"]:
            scenario_dir = results_dir / scenario
            if scenario_dir.exists():
                out_dirs.append(scenario_dir)
                print(f"  - {scenario}: 存在")
            else:
                print(f"  - {scenario}: 存在しない")
        
        # AIレポートファイルの検索
        print("\nAIレポートファイル検索:")
        ai_files = list(results_dir.rglob("ai_comprehensive_report_*.json"))
        if ai_files:
            print(f"  見つかったAIレポートファイル: {len(ai_files)}")
            for file in ai_files:
                size_kb = file.stat().st_size / 1024
                print(f"    - {file} ({size_kb:.1f} KB)")
        else:
            print("  AIレポートファイルが見つかりません")
    else:
        print("extracted_resultsディレクトリが存在しません")
    
    return True

def main():
    """メインデバッグ関数"""
    print("AIレポート生成デバッグ開始")
    print("=" * 60)
    
    # 1. 直接生成テスト
    result1 = debug_ai_report_generation()
    
    # 2. app.py統合確認
    result2 = debug_app_integration()
    
    print("\n" + "=" * 60)
    print("デバッグ結果:")
    print(f"直接生成テスト: {'成功' if result1 else '失敗'}")
    print(f"app.py統合確認: {'成功' if result2 else '失敗'}")
    
    if result1 and result2:
        print("\n結論: AIレポート機能は正常に動作します")
        print("問題は app.py での呼び出し条件にある可能性があります")
    elif result1:
        print("\n結論: AIレポート機能は動作しますが、統合に問題があります")
    else:
        print("\n結論: AIレポート機能自体に問題があります")

if __name__ == "__main__":
    main()