#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 4: 修正内容の総合検証テスト
27,486.5時間問題の修正効果確認
"""

import sys
import os
import pandas as pd
import datetime as dt
from pathlib import Path
import traceback

# shift_suiteモジュールのパスを追加
sys.path.insert(0, str(Path.cwd()))

def test_excel_data_loading():
    """テストExcelファイルの読み込み確認"""
    
    test_files = [
        "ショート_テスト用データ.xlsx",
        "デイ_テスト用データ_休日精緻.xlsx", 
        "テストデータ_2024 本木ショート（7～9月）.xlsx"
    ]
    
    results = {}
    
    for file_name in test_files:
        file_path = Path.cwd() / file_name
        
        if file_path.exists():
            try:
                # Excelファイルの基本情報を取得
                excel_file = pd.ExcelFile(file_path)
                sheet_names = excel_file.sheet_names
                
                # 最初のシートを読み込んでデータサイズを確認
                first_sheet = pd.read_excel(file_path, sheet_name=sheet_names[0])
                
                results[file_name] = {
                    "status": "SUCCESS",
                    "sheets": len(sheet_names),
                    "sheet_names": sheet_names,
                    "rows": len(first_sheet),
                    "columns": len(first_sheet.columns),
                    "date_range": "Unknown"
                }
                
                # 日付列を探して期間を特定
                for col in first_sheet.columns:
                    if "日付" in str(col) or "date" in str(col).lower():
                        try:
                            dates = pd.to_datetime(first_sheet[col], errors='coerce').dropna()
                            if len(dates) > 0:
                                start_date = dates.min()
                                end_date = dates.max()
                                period_days = (end_date - start_date).days + 1
                                results[file_name]["date_range"] = f"{start_date.date()} to {end_date.date()} ({period_days} days)"
                                break
                        except:
                            continue
                            
            except Exception as e:
                results[file_name] = {
                    "status": "ERROR",
                    "error": str(e)
                }
        else:
            results[file_name] = {
                "status": "NOT_FOUND",
                "path": str(file_path)
            }
    
    return results

def test_shortage_analysis_with_fixes():
    """修正後の過不足分析テスト"""
    
    try:
        # shift_suiteモジュールをインポート
        from shift_suite.tasks.shortage import shortage_and_brief
        from shift_suite.tasks.io_excel import ingest_excel
        
        test_results = {}
        
        # 3ヶ月データ（問題の原因となっていたファイル）でテスト
        problem_file = "テストデータ_2024 本木ショート（7～9月）.xlsx"
        problem_file_path = Path.cwd() / problem_file
        
        if problem_file_path.exists():
            print(f"Testing problematic file: {problem_file}")
            
            # データ読み込み
            long_format_data = ingest_excel(str(problem_file_path))
            
            if not long_format_data.empty:
                print(f"Data loaded: {len(long_format_data)} records")
                
                # 過不足分析実行
                result = shortage_and_brief(long_format_data)
                
                if result and 'shortage_summary' in result:
                    shortage_summary = result['shortage_summary']
                    total_shortage_hours = shortage_summary.get('total_shortage_hours', 0)
                    
                    test_results[problem_file] = {
                        "status": "SUCCESS",
                        "total_shortage_hours": total_shortage_hours,
                        "is_fixed": total_shortage_hours < 5000,  # 5000時間未満なら修正効果あり
                        "previous_value": 27486.5,
                        "reduction_ratio": (27486.5 - total_shortage_hours) / 27486.5 if total_shortage_hours < 27486.5 else 0,
                        "summary": shortage_summary
                    }
                    
                    print(f"Shortage analysis result: {total_shortage_hours:.1f} hours")
                    
                else:
                    test_results[problem_file] = {
                        "status": "NO_RESULT",
                        "message": "shortage_and_brief returned no valid result"
                    }
            else:
                test_results[problem_file] = {
                    "status": "NO_DATA",
                    "message": "ingest_excel returned empty DataFrame"
                }
        else:
            test_results[problem_file] = {
                "status": "FILE_NOT_FOUND",
                "path": str(problem_file_path)
            }
            
        # 他のテストファイルでも確認
        other_files = ["ショート_テスト用データ.xlsx", "デイ_テスト用データ_休日精緻.xlsx"]
        
        for file_name in other_files:
            file_path = Path.cwd() / file_name
            
            if file_path.exists():
                try:
                    print(f"Testing file: {file_name}")
                    
                    long_format_data = ingest_excel(str(file_path))
                    
                    if not long_format_data.empty:
                        result = shortage_and_brief(long_format_data)
                        
                        if result and 'shortage_summary' in result:
                            shortage_summary = result['shortage_summary']
                            total_shortage_hours = shortage_summary.get('total_shortage_hours', 0)
                            
                            test_results[file_name] = {
                                "status": "SUCCESS",
                                "total_shortage_hours": total_shortage_hours,
                                "is_reasonable": total_shortage_hours < 10000,  # 妥当な範囲内かチェック
                                "summary": shortage_summary
                            }
                            
                            print(f"Result: {total_shortage_hours:.1f} hours")
                        else:
                            test_results[file_name] = {"status": "NO_RESULT"}
                    else:
                        test_results[file_name] = {"status": "NO_DATA"}
                        
                except Exception as e:
                    test_results[file_name] = {
                        "status": "ERROR",
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }
            else:
                test_results[file_name] = {"status": "FILE_NOT_FOUND"}
        
        return test_results
        
    except ImportError as e:
        return {
            "import_error": {
                "status": "IMPORT_ERROR",
                "error": str(e),
                "message": "Failed to import shift_suite modules"
            }
        }
    except Exception as e:
        return {
            "general_error": {
                "status": "GENERAL_ERROR", 
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        }

def verify_phase1_fix():
    """Phase 1修正の確認"""
    
    calc_file = Path("shift_suite/tasks/time_axis_shortage_calculator.py")
    
    if not calc_file.exists():
        return {"status": "FILE_NOT_FOUND"}
    
    with open(calc_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        "circular_amplification_disabled": "FIXED_27486" in content,
        "simple_demand_calculation": "estimated_demand = total_supply * 1.05" in content,
        "baseline_logic_removed": content.count("self.total_shortage_baseline") <= 3,
        "fix_log_present": "27,486.5 hour problem fix" in content,
        "complex_conditions_removed": "if self.total_shortage_baseline and" not in content
    }
    
    return {
        "status": "SUCCESS",
        "checks": checks,
        "all_passed": all(checks.values())
    }

def verify_phase2_fix():
    """Phase 2修正の確認"""
    
    shortage_file = Path("shift_suite/tasks/shortage.py")
    
    if not shortage_file.exists():
        return {"status": "FILE_NOT_FOUND"}
    
    with open(shortage_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        "anomaly_detection_function": "validate_and_cap_shortage" in content,
        "need_validation_function": "validate_need_data" in content,
        "risk_detection_function": "detect_period_dependency_risk" in content,
        "integration_in_main": "PHASE2_APPLIED" in content,
        "risk_warning_integration": "PHASE2_RISK" in content,
        "max_shortage_limit": "MAX_SHORTAGE_PER_DAY = 50" in content
    }
    
    return {
        "status": "SUCCESS",
        "checks": checks,
        "all_passed": all(checks.values())
    }

def generate_verification_report(excel_results, shortage_results, phase1_results, phase2_results):
    """検証レポートの生成"""
    
    report = []
    report.append("=" * 80)
    report.append("修正内容の総合検証レポート")
    report.append(f"実行時刻: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)
    
    # Phase 1検証結果
    report.append("\n## Phase 1: 循環増幅設計の無効化")
    if phase1_results["status"] == "SUCCESS":
        for check_name, result in phase1_results["checks"].items():
            status = "✅ PASS" if result else "❌ FAIL"
            report.append(f"  {status} {check_name}")
        
        overall = "✅ 全チェック通過" if phase1_results["all_passed"] else "❌ 一部チェック失敗"
        report.append(f"\n  総合判定: {overall}")
    else:
        report.append(f"  ❌ ファイル確認失敗: {phase1_results}")
    
    # Phase 2検証結果
    report.append("\n## Phase 2: 異常値検出・制限機能")
    if phase2_results["status"] == "SUCCESS":
        for check_name, result in phase2_results["checks"].items():
            status = "✅ PASS" if result else "❌ FAIL"
            report.append(f"  {status} {check_name}")
        
        overall = "✅ 全チェック通過" if phase2_results["all_passed"] else "❌ 一部チェック失敗"
        report.append(f"\n  総合判定: {overall}")
    else:
        report.append(f"  ❌ ファイル確認失敗: {phase2_results}")
    
    # Excelファイル確認結果
    report.append("\n## テストデータ確認")
    for file_name, result in excel_results.items():
        if result["status"] == "SUCCESS":
            report.append(f"  ✅ {file_name}")
            report.append(f"     シート数: {result['sheets']}, 行数: {result['rows']}")
            report.append(f"     期間: {result['date_range']}")
        elif result["status"] == "NOT_FOUND":
            report.append(f"  ⚠️  {file_name} (ファイルが見つかりません)")
        else:
            report.append(f"  ❌ {file_name} (エラー: {result.get('error', 'Unknown')})")
    
    # 過不足分析結果
    report.append("\n## 過不足分析実行結果")
    
    critical_fixed = False
    
    for file_name, result in shortage_results.items():
        if result["status"] == "SUCCESS":
            hours = result.get("total_shortage_hours", 0)
            report.append(f"  📊 {file_name}")
            report.append(f"     不足時間: {hours:.1f} 時間")
            
            if "is_fixed" in result:
                if result["is_fixed"]:
                    reduction = result.get("reduction_ratio", 0) * 100
                    report.append(f"     ✅ 修正効果確認 (元: 27,486.5h → 現: {hours:.1f}h, {reduction:.1f}% 削減)")
                    critical_fixed = True
                else:
                    report.append(f"     ❌ まだ高い値 (目標: <5,000h)")
            elif "is_reasonable" in result:
                if result["is_reasonable"]:
                    report.append(f"     ✅ 妥当な範囲内")
                else:
                    report.append(f"     ⚠️  やや高い値")
                    
        elif result["status"] == "FILE_NOT_FOUND":
            report.append(f"  ⚠️  {file_name} (ファイルが見つかりません)")
        elif result["status"] == "ERROR":
            report.append(f"  ❌ {file_name} (エラー: {result.get('error', 'Unknown')})")
        else:
            report.append(f"  ⚠️  {file_name} (結果なし: {result.get('message', 'Unknown')})")
    
    # 総合判定
    report.append("\n## 総合判定")
    
    phase1_ok = phase1_results.get("all_passed", False)
    phase2_ok = phase2_results.get("all_passed", False)
    
    if phase1_ok and phase2_ok and critical_fixed:
        report.append("✅ 全修正が正常に適用され、27,486.5時間問題が解決されました")
        report.append("   次のステップ: Phase 3 (期間正規化機能の統合) に進むことができます")
    elif phase1_ok and phase2_ok:
        report.append("⚠️  修正は適用されましたが、テストデータでの効果確認が必要です")
        report.append("   テストファイルの場所や実行環境を確認してください")
    else:
        report.append("❌ 修正に問題があります。手動確認が必要です")
        if not phase1_ok:
            report.append("   - Phase 1の修正が不完全です")
        if not phase2_ok:
            report.append("   - Phase 2の修正が不完全です")
    
    return "\n".join(report)

def main():
    """検証テストのメイン実行"""
    
    print("=" * 60)
    print("Phase 4: 修正内容の総合検証テスト")
    print("27,486.5時間問題の修正効果確認")
    print("=" * 60)
    
    # Step 1: Excelデータの確認
    print("\n📁 Step 1: テストデータの確認")
    excel_results = test_excel_data_loading()
    
    # Step 2: Phase 1修正の確認
    print("\n🔧 Step 2: Phase 1修正の確認")
    phase1_results = verify_phase1_fix()
    
    # Step 3: Phase 2修正の確認
    print("\n🛡️ Step 3: Phase 2修正の確認")
    phase2_results = verify_phase2_fix()
    
    # Step 4: 過不足分析実行テスト
    print("\n📊 Step 4: 過不足分析実行テスト")
    shortage_results = test_shortage_analysis_with_fixes()
    
    # Step 5: レポート生成
    print("\n📋 Step 5: 検証レポート生成")
    report = generate_verification_report(excel_results, shortage_results, phase1_results, phase2_results)
    
    # 結果出力
    print("\n" + report)
    
    # レポートファイル保存
    report_file = Path("verification_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 詳細レポートを保存: {report_file}")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 検証テスト実行中にエラーが発生しました:")
        print(f"エラー: {e}")
        print(f"詳細: {traceback.format_exc()}")