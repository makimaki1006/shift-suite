#!/usr/bin/env python3
"""
実際のワークフロー統合テスト
app.pyでの実際の動作を模擬
"""

import os
import sys
import tempfile
from pathlib import Path
import zipfile
import json

def test_real_workflow_integration():
    """実際のワークフロー統合テスト"""
    print("=== 実際のワークフロー統合テスト ===")
    
    # 1. 一時的な作業ディレクトリ作成
    with tempfile.TemporaryDirectory() as temp_dir:
        work_root = Path(temp_dir)
        out_dir = work_root / "out"
        out_dir.mkdir()
        
        # 各シナリオディレクトリ作成
        scenarios = ["out_median_based", "out_mean_based", "out_p25_based"]
        for scenario in scenarios:
            scenario_dir = out_dir / scenario
            scenario_dir.mkdir()
            
        print(f"作業ディレクトリ: {work_root}")
        
        # 2. AIレポート生成テスト
        try:
            from shift_suite.tasks.ai_comprehensive_report_generator import AIComprehensiveReportGenerator
            
            generator = AIComprehensiveReportGenerator()
            
            # 模擬分析結果
            mock_analysis_results = {
                "shortage_analysis": {
                    "lack_hours_total": 373.0,
                    "excess_hours_total": 58.0
                },
                "forecast_analysis": {
                    "mape": 0.049,
                    "model": "ETS"
                }
            }
            
            # AIレポート生成
            report = generator.generate_comprehensive_report(
                analysis_results=mock_analysis_results,
                input_file_path="test_data.xlsx",
                output_dir=str(out_dir),
                analysis_params={"scenario": "median_based"}
            )
            
            print("✅ AIレポート生成成功")
            
            # 3. 生成されたファイルの確認
            ai_files = list(out_dir.glob("ai_comprehensive_report_*.json"))
            print(f"生成されたAIレポートファイル: {len(ai_files)}")
            
            if ai_files:
                ai_file = ai_files[0]
                print(f"AIレポートファイル: {ai_file}")
                print(f"ファイルサイズ: {ai_file.stat().st_size / 1024:.1f} KB")
                
                # JSONの内容確認
                with open(ai_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                    print(f"レポートセクション数: {len(report_data)}")
                    
                # 4. app.pyのファイル検索パターンと一致するかテスト
                search_pattern = "out/ai_comprehensive_report_*.json"
                found_files = list(work_root.glob(search_pattern))
                print(f"app.pyの検索パターン '{search_pattern}' でのマッチ: {len(found_files)}")
                
                if found_files:
                    print("✅ app.pyでファイルが見つかります")
                else:
                    print("❌ app.pyでファイルが見つかりません")
                    
                    # より詳細な確認
                    print("実際のファイル位置:")
                    for f in ai_files:
                        relative_path = f.relative_to(work_root)
                        print(f"  - {relative_path}")
                
                # 5. ZIPファイル作成テスト
                zip_path = work_root / "test_analysis_results.zip"
                with zipfile.ZipFile(zip_path, 'w') as zf:
                    # outディレクトリ内の全ファイルをZIPに追加
                    for file_path in out_dir.rglob('*'):
                        if file_path.is_file():
                            arc_name = file_path.relative_to(work_root)
                            zf.write(file_path, arc_name)
                            print(f"ZIPに追加: {arc_name}")
                
                # 6. ZIPファイル内容確認
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zip_contents = zf.namelist()
                    print(f"\nZIPファイル内容 ({len(zip_contents)} ファイル):")
                    
                    ai_in_zip = [f for f in zip_contents if 'ai_comprehensive_report' in f]
                    if ai_in_zip:
                        print(f"✅ AIレポートがZIPに含まれています: {ai_in_zip}")
                        return True
                    else:
                        print("❌ AIレポートがZIPに含まれていません")
                        print("ZIPの全内容:", zip_contents)
                        return False
            else:
                print("❌ AIレポートファイルが生成されませんでした")
                return False
                
        except Exception as e:
            print(f"❌ エラー発生: {e}")
            import traceback
            print("詳細エラー:")
            print(traceback.format_exc())
            return False

def main():
    """メインテスト関数"""
    print("実際のワークフロー統合テスト開始")
    print("=" * 60)
    
    success = test_real_workflow_integration()
    
    print("\n" + "=" * 60)
    print(f"テスト結果: {'✅ 成功' if success else '❌ 失敗'}")
    
    if success:
        print("結論: AIレポートは正常にZIPファイルに含まれます")
    else:
        print("結論: まだ問題があります - ZIPファイル統合が不完全")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)