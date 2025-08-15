#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡単な修正内容確認スクリプト（依存関係なし）
Phase 1 & Phase 2 の修正が正しく適用されているかコード解析で確認
"""

import os
from pathlib import Path
import datetime as dt

def verify_phase1_fix():
    """Phase 1修正の確認"""
    
    calc_file = Path("shift_suite/tasks/time_axis_shortage_calculator.py")
    
    if not calc_file.exists():
        return {"status": "FILE_NOT_FOUND", "path": str(calc_file)}
    
    with open(calc_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修正が正しく適用されているかチェック
    checks = {
        "circular_amplification_disabled": "FIXED_27486" in content,
        "simple_demand_calculation": "estimated_demand = total_supply * 1.05" in content,
        "baseline_logic_removed": content.count("self.total_shortage_baseline") <= 3,
        "fix_log_present": "27,486.5 hour problem fix" in content,
        "complex_conditions_removed": "if self.total_shortage_baseline and" not in content,
        "old_logic_removed": "baseline_per_day > 500" not in content,
        "comment_fix_present": "以前の循環増幅ロジックは完全に削除" in content
    }
    
    # 修正された行を探す
    lines = content.split('\n')
    fix_line_numbers = []
    for i, line in enumerate(lines, 1):
        if "FIXED_27486" in line or "循環増幅を完全に無効化" in line:
            fix_line_numbers.append(i)
    
    return {
        "status": "SUCCESS",
        "checks": checks,
        "all_passed": all(checks.values()),
        "fix_line_numbers": fix_line_numbers,
        "file_size": calc_file.stat().st_size,
        "total_lines": len(lines)
    }

def verify_phase2_fix():
    """Phase 2修正の確認"""
    
    shortage_file = Path("shift_suite/tasks/shortage.py")
    
    if not shortage_file.exists():
        return {"status": "FILE_NOT_FOUND", "path": str(shortage_file)}
    
    with open(shortage_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Phase 2で追加された機能の確認
    checks = {
        "anomaly_detection_function": "validate_and_cap_shortage" in content,
        "need_validation_function": "validate_need_data" in content,
        "risk_detection_function": "detect_period_dependency_risk" in content,
        "integration_in_main": "PHASE2_APPLIED" in content,
        "risk_warning_integration": "PHASE2_RISK" in content,
        "max_shortage_limit": "MAX_SHORTAGE_PER_DAY = 50" in content,
        "anomaly_log_warning": "ANOMALY_DETECTED" in content,
        "capped_log_warning": "CAPPED" in content
    }
    
    # 追加された関数の行数を確認
    lines = content.split('\n')
    function_line_numbers = {}
    for i, line in enumerate(lines, 1):
        if "def validate_and_cap_shortage" in line:
            function_line_numbers["validate_and_cap_shortage"] = i
        elif "def validate_need_data" in line:
            function_line_numbers["validate_need_data"] = i
        elif "def detect_period_dependency_risk" in line:
            function_line_numbers["detect_period_dependency_risk"] = i
    
    return {
        "status": "SUCCESS",
        "checks": checks,
        "all_passed": all(checks.values()),
        "function_line_numbers": function_line_numbers,
        "file_size": shortage_file.stat().st_size,
        "total_lines": len(lines)
    }

def check_backup_files():
    """バックアップファイルの存在確認"""
    
    backup_files = []
    
    # time_axis_shortage_calculator.py のバックアップ
    calc_backups = list(Path("shift_suite/tasks").glob("time_axis_shortage_calculator.py.backup_*"))
    backup_files.extend([(f.name, f.stat().st_mtime) for f in calc_backups])
    
    # shortage.py のバックアップ
    shortage_backups = list(Path("shift_suite/tasks").glob("shortage.py.backup_*"))
    backup_files.extend([(f.name, f.stat().st_mtime) for f in shortage_backups])
    
    # 最新のバックアップを特定
    backup_files.sort(key=lambda x: x[1], reverse=True)
    
    return {
        "total_backups": len(backup_files),
        "backup_files": [(name, dt.datetime.fromtimestamp(mtime)) for name, mtime in backup_files],
        "latest_backup": backup_files[0] if backup_files else None
    }

def check_test_files():
    """テストファイルの存在確認"""
    
    test_files = [
        "ショート_テスト用データ.xlsx",
        "デイ_テスト用データ_休日精緻.xlsx", 
        "テストデータ_2024 本木ショート（7～9月）.xlsx"
    ]
    
    results = {}
    
    for file_name in test_files:
        file_path = Path.cwd() / file_name
        
        if file_path.exists():
            results[file_name] = {
                "status": "FOUND",
                "size_mb": round(file_path.stat().st_size / (1024*1024), 2),
                "modified": dt.datetime.fromtimestamp(file_path.stat().st_mtime)
            }
        else:
            results[file_name] = {
                "status": "NOT_FOUND",
                "path": str(file_path)
            }
    
    return results

def generate_simple_report(phase1_results, phase2_results, backup_results, test_file_results):
    """簡単な検証レポートの生成"""
    
    report = []
    report.append("=" * 80)
    report.append("修正内容の確認レポート（コード解析版）")
    report.append(f"実行日時: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)
    
    # Phase 1検証結果
    report.append("\n## Phase 1: 循環増幅設計の無効化")
    if phase1_results["status"] == "SUCCESS":
        for check_name, result in phase1_results["checks"].items():
            status = "✅ PASS" if result else "❌ FAIL"
            report.append(f"  {status} {check_name}")
        
        report.append(f"\n  📄 ファイル情報:")
        report.append(f"     サイズ: {phase1_results['file_size']} bytes")
        report.append(f"     総行数: {phase1_results['total_lines']} lines")
        report.append(f"     修正箇所: {phase1_results['fix_line_numbers']} 行")
        
        overall = "✅ 全チェック通過" if phase1_results["all_passed"] else "❌ 一部チェック失敗"
        report.append(f"\n  総合判定: {overall}")
    else:
        report.append(f"  ❌ ファイル確認失敗: {phase1_results.get('path', 'Unknown')}")
    
    # Phase 2検証結果
    report.append("\n## Phase 2: 異常値検出・制限機能")
    if phase2_results["status"] == "SUCCESS":
        for check_name, result in phase2_results["checks"].items():
            status = "✅ PASS" if result else "❌ FAIL"
            report.append(f"  {status} {check_name}")
        
        report.append(f"\n  📄 ファイル情報:")
        report.append(f"     サイズ: {phase2_results['file_size']} bytes")
        report.append(f"     総行数: {phase2_results['total_lines']} lines")
        
        report.append(f"\n  🔧 追加された関数:")
        for func_name, line_num in phase2_results["function_line_numbers"].items():
            report.append(f"     {func_name}: {line_num} 行目")
        
        overall = "✅ 全チェック通過" if phase2_results["all_passed"] else "❌ 一部チェック失敗"
        report.append(f"\n  総合判定: {overall}")
    else:
        report.append(f"  ❌ ファイル確認失敗: {phase2_results.get('path', 'Unknown')}")
    
    # バックアップファイル確認
    report.append("\n## バックアップファイル確認")
    report.append(f"  📁 総バックアップ数: {backup_results['total_backups']}")
    
    if backup_results['backup_files']:
        report.append(f"  📋 バックアップ一覧:")
        for name, timestamp in backup_results['backup_files'][:5]:  # 最新5個を表示
            report.append(f"     {name} ({timestamp})")
        
        if backup_results['latest_backup']:
            latest_name, latest_time = backup_results['latest_backup']
            latest_timestamp = dt.datetime.fromtimestamp(latest_time)
            report.append(f"  🕒 最新: {latest_name} ({latest_timestamp})")
    else:
        report.append(f"  ⚠️  バックアップファイルが見つかりません")
    
    # テストファイル確認
    report.append("\n## テストファイル確認")
    found_files = 0
    for file_name, result in test_file_results.items():
        if result["status"] == "FOUND":
            found_files += 1
            report.append(f"  ✅ {file_name}")
            report.append(f"     サイズ: {result['size_mb']} MB, 更新: {result['modified']}")
        else:
            report.append(f"  ❌ {file_name} (見つかりません)")
    
    report.append(f"\n  📊 発見ファイル数: {found_files}/3")
    
    # 総合判定
    report.append("\n## 総合判定")
    
    phase1_ok = phase1_results.get("all_passed", False)
    phase2_ok = phase2_results.get("all_passed", False)
    has_backups = backup_results['total_backups'] > 0
    has_test_files = found_files > 0
    
    if phase1_ok and phase2_ok:
        report.append("✅ 両方の修正が正常にコードに適用されています")
        report.append("   - Phase 1: 循環増幅の無効化 → 適用済み")
        report.append("   - Phase 2: 異常値検出・制限機能 → 追加済み")
        
        if has_backups:
            report.append("   - バックアップファイル → 確認済み")
        
        if has_test_files:
            report.append("   - テストファイル → 利用可能")
            report.append("\n📋 推奨される次のステップ:")
            report.append("   1. 実際のテストデータで過不足分析を実行")
            report.append("   2. 27,486.5時間 → 5,000時間未満への削減効果を確認")
            report.append("   3. Phase 3 (期間正規化機能) への移行検討")
        else:
            report.append("\n⚠️  テストファイルが見つかりません")
            report.append("   実際の効果確認には適切なテストデータが必要です")
            
    else:
        report.append("❌ 修正に問題があります")
        if not phase1_ok:
            report.append("   - Phase 1の修正が不完全または未適用")
        if not phase2_ok:
            report.append("   - Phase 2の修正が不完全または未適用")
        report.append("   手動での確認・修正が必要です")
    
    # 期待効果の説明
    if phase1_ok and phase2_ok:
        report.append("\n## 期待される修正効果")
        report.append("### Phase 1 効果:")
        report.append("  - 27,486.5時間の異常値 → 5,000時間未満に削減")
        report.append("  - 3ヶ月データでの異常な跳ね上がりを防止")
        report.append("  - 予測可能で安定した計算結果")
        
        report.append("\n### Phase 2 効果:")
        report.append("  - 異常値の自動検出とアラート")
        report.append("  - 1日50時間を超える不足時間の自動制限")
        report.append("  - 期間依存性リスクの早期警告")
        report.append("  - Need値の妥当性チェック（上限5人/スロット）")
    
    return "\n".join(report)

def main():
    """簡単な検証実行"""
    
    print("=" * 60)
    print("修正内容の確認（コード解析版）")
    print("Phase 1 & Phase 2 の適用状況をチェック")
    print("=" * 60)
    
    # Step 1: Phase 1修正の確認
    print("\n🔧 Step 1: Phase 1修正の確認")
    phase1_results = verify_phase1_fix()
    if phase1_results["status"] == "SUCCESS":
        passed = sum(1 for x in phase1_results["checks"].values() if x)
        total = len(phase1_results["checks"])
        print(f"   結果: {passed}/{total} チェック通過")
    else:
        print(f"   エラー: {phase1_results}")
    
    # Step 2: Phase 2修正の確認
    print("\n🛡️ Step 2: Phase 2修正の確認")
    phase2_results = verify_phase2_fix()
    if phase2_results["status"] == "SUCCESS":
        passed = sum(1 for x in phase2_results["checks"].values() if x)
        total = len(phase2_results["checks"])
        print(f"   結果: {passed}/{total} チェック通過")
    else:
        print(f"   エラー: {phase2_results}")
    
    # Step 3: バックアップファイル確認
    print("\n📁 Step 3: バックアップファイル確認")
    backup_results = check_backup_files()
    print(f"   バックアップ数: {backup_results['total_backups']}")
    
    # Step 4: テストファイル確認
    print("\n📊 Step 4: テストファイル確認")
    test_file_results = check_test_files()
    found = sum(1 for x in test_file_results.values() if x["status"] == "FOUND")
    print(f"   発見ファイル: {found}/3")
    
    # Step 5: レポート生成
    print("\n📋 Step 5: レポート生成")
    report = generate_simple_report(phase1_results, phase2_results, backup_results, test_file_results)
    
    # 結果出力
    print("\n" + report)
    
    # レポートファイル保存
    report_file = Path("code_verification_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 詳細レポートを保存: {report_file}")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 検証実行中にエラーが発生しました:")
        print(f"エラー: {e}")
        import traceback
        print(f"詳細: {traceback.format_exc()}")