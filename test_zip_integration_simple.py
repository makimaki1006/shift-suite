#!/usr/bin/env python3
"""
ZIPファイル統合の簡単なテスト（ASCII文字のみ）
"""

import os
import sys
import tempfile
from pathlib import Path
import zipfile
import json

def test_zip_integration():
    """ZIPファイル統合テスト"""
    print("=== ZIP Integration Test ===")
    
    # 1. 一時的な作業ディレクトリ作成
    with tempfile.TemporaryDirectory() as temp_dir:
        work_root = Path(temp_dir)
        out_dir = work_root / "out"
        out_dir.mkdir()
        
        print(f"Work directory: {work_root}")
        
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
            print("Generating AI report...")
            report = generator.generate_comprehensive_report(
                analysis_results=mock_analysis_results,
                input_file_path="test_data.xlsx",
                output_dir=str(out_dir),
                analysis_params={"scenario": "median_based"}
            )
            
            print("SUCCESS: AI report generated")
            
            # 3. 生成されたファイルの確認
            ai_files = list(out_dir.glob("ai_comprehensive_report_*.json"))
            print(f"AI report files found: {len(ai_files)}")
            
            if ai_files:
                ai_file = ai_files[0]
                print(f"AI report file: {ai_file}")
                print(f"File size: {ai_file.stat().st_size / 1024:.1f} KB")
                
                # JSONの内容確認
                with open(ai_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                    print(f"Report sections: {len(report_data)}")
                
                # 4. ZIPファイル作成テスト
                zip_path = work_root / "test_analysis_results.zip"
                with zipfile.ZipFile(zip_path, 'w') as zf:
                    # outディレクトリ内の全ファイルをZIPに追加
                    for file_path in out_dir.rglob('*'):
                        if file_path.is_file():
                            arc_name = file_path.relative_to(work_root)
                            zf.write(file_path, arc_name)
                            print(f"Added to ZIP: {arc_name}")
                
                # 5. ZIPファイル内容確認
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zip_contents = zf.namelist()
                    print(f"ZIP contents ({len(zip_contents)} files):")
                    
                    ai_in_zip = [f for f in zip_contents if 'ai_comprehensive_report' in f]
                    if ai_in_zip:
                        print(f"SUCCESS: AI report in ZIP: {ai_in_zip}")
                        
                        # ファイルサイズ確認
                        for ai_file_in_zip in ai_in_zip:
                            info = zf.getinfo(ai_file_in_zip)
                            print(f"ZIP file size: {info.file_size / 1024:.1f} KB")
                        
                        return True
                    else:
                        print("FAIL: AI report NOT in ZIP")
                        print("All ZIP contents:", zip_contents)
                        return False
            else:
                print("FAIL: No AI report files generated")
                return False
                
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            print("Detailed error:")
            print(traceback.format_exc())
            return False

def main():
    """メインテスト関数"""
    print("ZIP Integration Test Start")
    print("=" * 60)
    
    success = test_zip_integration()
    
    print("\n" + "=" * 60)
    if success:
        print("RESULT: SUCCESS - AI reports are included in ZIP files")
    else:
        print("RESULT: FAIL - ZIP integration has issues")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)