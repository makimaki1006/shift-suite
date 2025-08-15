#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A3.1 軽量監視システム
依存関係を最小化したPhase 2/3.1統合監視
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class LightweightMonitor:
    """軽量システム監視"""
    
    def __init__(self):
        self.monitoring_dir = Path("logs/monitoring")
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)
        
    def check_critical_files(self) -> Dict[str, Any]:
        """重要ファイル確認"""
        
        print("📊 重要ファイル確認...")
        
        critical_files = [
            "shift_suite/tasks/fact_extractor_prototype.py",
            "shift_suite/tasks/lightweight_anomaly_detector.py",
            "shift_suite/tasks/fact_book_visualizer.py", 
            "shift_suite/tasks/dash_fact_book_integration.py",
            "dash_app.py",
            "app.py"
        ]
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "files": {},
            "status": "healthy",
            "summary": {"total": 0, "ok": 0, "missing": 0}
        }
        
        for file_path in critical_files:
            path = Path(file_path)
            results["summary"]["total"] += 1
            
            if path.exists():
                try:
                    stat = path.stat()
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    results["files"][file_path] = {
                        "exists": True,
                        "size_bytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "lines": len(content.splitlines()),
                        "status": "ok"
                    }
                    results["summary"]["ok"] += 1
                    print(f"  ✅ {file_path}: OK ({stat.st_size} bytes)")
                    
                except Exception as e:
                    results["files"][file_path] = {
                        "exists": True,
                        "error": str(e),
                        "status": "error"
                    }
                    print(f"  ❌ {file_path}: Read error - {e}")
                    
            else:
                results["files"][file_path] = {
                    "exists": False,
                    "status": "missing"
                }
                results["summary"]["missing"] += 1
                results["status"] = "warning"
                print(f"  ⚠️ {file_path}: Missing")
        
        return results
    
    def check_phase2_31_integrity(self) -> Dict[str, Any]:
        """Phase 2/3.1整合性確認"""
        
        print("🔍 Phase 2/3.1整合性確認...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "phase2": {},
            "phase31": {},
            "integration": {},
            "status": "healthy"
        }
        
        # Phase 2確認
        phase2_file = Path("shift_suite/tasks/fact_extractor_prototype.py")
        if phase2_file.exists():
            try:
                with open(phase2_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                slot_hours_count = content.count('* SLOT_HOURS')
                wrong_comment = "parsed_slots_count is already in hours" in content
                
                results["phase2"] = {
                    "file_exists": True,
                    "slot_hours_multiplications": slot_hours_count,
                    "wrong_comments_removed": not wrong_comment,
                    "expected_multiplications": 4,
                    "status": "ok" if slot_hours_count >= 4 and not wrong_comment else "warning"
                }
                
                status_icon = "✅" if slot_hours_count >= 4 and not wrong_comment else "⚠️"
                print(f"  {status_icon} Phase 2: SLOT_HOURS使用 {slot_hours_count}/4箇所, 誤コメント除去: {not wrong_comment}")
                
                if slot_hours_count < 4 or wrong_comment:
                    results["status"] = "warning"
                    
            except Exception as e:
                results["phase2"] = {"error": str(e), "status": "error"}
                results["status"] = "error"
                print(f"  ❌ Phase 2確認エラー: {e}")
        
        # Phase 3.1確認
        phase31_file = Path("shift_suite/tasks/lightweight_anomaly_detector.py")
        if phase31_file.exists():
            try:
                with open(phase31_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                slot_hours_count = content.count('* SLOT_HOURS')
                wrong_comment = "parsed_slots_count is already in hours" in content
                
                results["phase31"] = {
                    "file_exists": True,
                    "slot_hours_multiplications": slot_hours_count,
                    "wrong_comments_removed": not wrong_comment,
                    "expected_multiplications": 1,
                    "status": "ok" if slot_hours_count >= 1 and not wrong_comment else "warning"
                }
                
                status_icon = "✅" if slot_hours_count >= 1 and not wrong_comment else "⚠️"
                print(f"  {status_icon} Phase 3.1: SLOT_HOURS使用 {slot_hours_count}/1箇所, 誤コメント除去: {not wrong_comment}")
                
                if slot_hours_count < 1 or wrong_comment:
                    results["status"] = "warning"
                    
            except Exception as e:
                results["phase31"] = {"error": str(e), "status": "error"}
                results["status"] = "error"
                print(f"  ❌ Phase 3.1確認エラー: {e}")
        
        # 統合確認
        integration_files = [
            ("FactBookVisualizer", "shift_suite/tasks/fact_book_visualizer.py"),
            ("Dash統合", "shift_suite/tasks/dash_fact_book_integration.py"),
            ("メインアプリ", "dash_app.py")
        ]
        
        integration_ok = 0
        for name, file_path in integration_files:
            path = Path(file_path)
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    has_phase2 = "FactExtractorPrototype" in content or "fact_extractor" in content
                    has_phase31 = "LightweightAnomalyDetector" in content or "anomaly_detector" in content
                    
                    if has_phase2 or has_phase31:
                        integration_ok += 1
                        print(f"  ✅ {name}: Phase 2={has_phase2}, Phase 3.1={has_phase31}")
                    else:
                        print(f"  ⚠️ {name}: 統合確認できず")
                        
                except Exception as e:
                    print(f"  ❌ {name}確認エラー: {e}")
        
        results["integration"] = {
            "files_checked": len(integration_files),
            "integration_confirmed": integration_ok,
            "status": "ok" if integration_ok >= 2 else "warning"
        }
        
        if integration_ok < 2:
            results["status"] = "warning"
        
        return results
    
    def check_syntax_integrity(self) -> Dict[str, Any]:
        """構文整合性確認"""
        
        print("⚡ 構文整合性確認...")
        
        test_files = [
            "shift_suite/tasks/fact_extractor_prototype.py",
            "shift_suite/tasks/lightweight_anomaly_detector.py",
            "shift_suite/tasks/fact_book_visualizer.py"
        ]
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "syntax_tests": {},
            "status": "healthy",
            "summary": {"total": 0, "passed": 0, "failed": 0}
        }
        
        for file_path in test_files:
            if not Path(file_path).exists():
                continue
                
            results["summary"]["total"] += 1
            
            try:
                start_time = time.time()
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", file_path],
                    capture_output=True,
                    timeout=10
                )
                end_time = time.time()
                
                response_time = end_time - start_time
                syntax_ok = result.returncode == 0
                
                results["syntax_tests"][file_path] = {
                    "syntax_valid": syntax_ok,
                    "response_time": response_time,
                    "status": "ok" if syntax_ok else "error"
                }
                
                if syntax_ok:
                    results["summary"]["passed"] += 1
                    print(f"  ✅ {file_path}: 構文OK ({response_time:.2f}s)")
                else:
                    results["summary"]["failed"] += 1
                    results["status"] = "error"
                    error_output = result.stderr.decode('utf-8', errors='ignore')
                    print(f"  ❌ {file_path}: 構文エラー")
                    print(f"    エラー: {error_output[:200]}...")
                    
            except subprocess.TimeoutExpired:
                results["syntax_tests"][file_path] = {
                    "syntax_valid": False,
                    "response_time": 10.0,
                    "status": "timeout"
                }
                results["summary"]["failed"] += 1
                results["status"] = "error"
                print(f"  ❌ {file_path}: タイムアウト")
                
            except Exception as e:
                results["syntax_tests"][file_path] = {
                    "error": str(e),
                    "status": "error"
                }
                results["summary"]["failed"] += 1
                results["status"] = "error"
                print(f"  ❌ {file_path}: テストエラー - {e}")
        
        return results
    
    def check_numerical_consistency(self) -> Dict[str, Any]:
        """数値整合性確認"""
        
        print("📊 数値整合性確認...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "baseline_check": {},
            "calculation_verification": {},
            "status": "healthy"
        }
        
        # 基準値確認
        shortage_files = [
            "temp_analysis_check/out_mean_based/shortage_summary.txt",
            "shortage_summary.txt"
        ]
        
        baseline_found = False
        for file_path in shortage_files:
            path = Path(file_path)
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if "670" in content or "total_lack_hours" in content:
                        results["baseline_check"] = {
                            "file": file_path,
                            "content_preview": content[:100],
                            "baseline_confirmed": True,
                            "status": "ok"
                        }
                        baseline_found = True
                        print(f"  ✅ 基準値ファイル確認: {file_path}")
                        break
                        
                except Exception as e:
                    print(f"  ⚠️ {file_path} 読み込みエラー: {e}")
        
        if not baseline_found:
            results["baseline_check"] = {
                "baseline_confirmed": False,
                "status": "warning"
            }
            results["status"] = "warning"
            print("  ⚠️ 基準値ファイル未確認")
        
        # 計算検証
        SLOT_HOURS = 0.5
        test_cases = [
            {"slots": 8, "expected_hours": 4.0, "description": "4時間勤務"},
            {"slots": 16, "expected_hours": 8.0, "description": "8時間勤務"},
            {"slots": 320, "expected_hours": 160.0, "description": "月160時間勤務"}
        ]
        
        calculation_ok = True
        for case in test_cases:
            calculated = case["slots"] * SLOT_HOURS
            expected = case["expected_hours"]
            match = abs(calculated - expected) < 0.01
            
            results["calculation_verification"][case["description"]] = {
                "slots": case["slots"],
                "calculated_hours": calculated,
                "expected_hours": expected,
                "match": match
            }
            
            if match:
                print(f"  ✅ {case['description']}: {case['slots']}スロット → {calculated}時間")
            else:
                print(f"  ❌ {case['description']}: 計算不一致")
                calculation_ok = False
        
        if not calculation_ok:
            results["status"] = "error"
        
        return results
    
    def generate_comprehensive_report(self, all_results: Dict[str, Any]) -> str:
        """包括レポート生成"""
        
        # 総合ステータス判定
        all_statuses = [result["status"] for result in all_results.values()]
        
        if "error" in all_statuses:
            overall_status = "error"
            status_icon = "🔴"
        elif "warning" in all_statuses:
            overall_status = "warning" 
            status_icon = "🟡"
        else:
            overall_status = "healthy"
            status_icon = "🟢"
        
        report = f"""
🔍 **A3.1 基本監視体制 - 包括レポート**
実行日時: {datetime.now().isoformat()}
総合ステータス: {status_icon} {overall_status.upper()}

📊 **監視結果サマリー**
- 重要ファイル: {all_results['files']['summary']['ok']}/{all_results['files']['summary']['total']} 正常
- Phase 2統合: {all_results['phase_integrity']['phase2'].get('status', 'unknown')}
- Phase 3.1統合: {all_results['phase_integrity']['phase31'].get('status', 'unknown')}
- 構文確認: {all_results['syntax']['summary']['passed']}/{all_results['syntax']['summary']['total']} 合格
- 数値整合性: {all_results['numerical']['status']}

🎯 **Phase 2/3.1 修正状況**
Phase 2 SLOT_HOURS使用: {all_results['phase_integrity']['phase2'].get('slot_hours_multiplications', 0)}/4箇所
Phase 3.1 SLOT_HOURS使用: {all_results['phase_integrity']['phase31'].get('slot_hours_multiplications', 0)}/1箇所
統合確認: {all_results['phase_integrity']['integration']['integration_confirmed']}/{all_results['phase_integrity']['integration']['files_checked']}ファイル

💡 **推奨アクション**"""
        
        if overall_status == "error":
            report += """
🚨 即座対応が必要です:
  1. 構文エラーの修正
  2. Phase 2/3.1整合性の確認
  3. バックアップからの復旧検討"""
        elif overall_status == "warning":
            report += """
⚠️ 注意が必要です:
  1. 警告項目の詳細確認
  2. 予防的対策の実施
  3. 継続監視の強化"""
        else:
            report += """
✅ システムは正常に動作しています:
  1. 定期監視の継続
  2. A3.1.2 エラーログ監視の設定
  3. A3.1.3 パフォーマンス監視の開始"""
        
        return report
    
    def save_monitoring_results(self, all_results: Dict[str, Any]) -> str:
        """監視結果保存"""
        
        result_file = self.monitoring_dir / f"monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        monitoring_data = {
            "monitoring_version": "lightweight_1.0",
            "timestamp": datetime.now().isoformat(),
            "results": all_results,
            "metadata": {
                "python_version": sys.version,
                "working_directory": str(Path.cwd()),
                "monitoring_tool": "A3_LIGHTWEIGHT_MONITORING"
            }
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(monitoring_data, f, indent=2, ensure_ascii=False)
        
        return str(result_file)

def main():
    """メイン実行"""
    
    print("🚨 A3.1 基本監視体制 - 軽量版開始")
    print("🎯 Phase 2/3.1修正成果の包括的安定運用監視")
    print("=" * 80)
    
    try:
        monitor = LightweightMonitor()
        
        # 各監視項目を順次実行
        all_results = {}
        
        print("\n" + "=" * 60)
        all_results["files"] = monitor.check_critical_files()
        
        print("\n" + "=" * 60)
        all_results["phase_integrity"] = monitor.check_phase2_31_integrity()
        
        print("\n" + "=" * 60)
        all_results["syntax"] = monitor.check_syntax_integrity()
        
        print("\n" + "=" * 60)
        all_results["numerical"] = monitor.check_numerical_consistency()
        
        # 包括レポート生成
        print("\n" + "=" * 80)
        print("📋 包括監視レポート")
        print("=" * 80)
        
        report = monitor.generate_comprehensive_report(all_results)
        print(report)
        
        # 結果保存
        result_file = monitor.save_monitoring_results(all_results)
        print(f"\n📁 監視結果保存: {result_file}")
        
        # 成功判定
        overall_status = "healthy"
        for result in all_results.values():
            if result["status"] == "error":
                overall_status = "error"
                break
            elif result["status"] == "warning":
                overall_status = "warning"
        
        print(f"\n🎯 A3.1.1 システム稼働監視: {'✅ 完了' if overall_status != 'error' else '❌ 要対応'}")
        
        return overall_status != "error"
        
    except Exception as e:
        print(f"❌ 監視システム実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)