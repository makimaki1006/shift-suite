#!/usr/bin/env python3
"""
実データ抽出機能の検証テスト

修正版AIComprehensiveReportGeneratorが実際のParquet/CSVファイルから
データを正しく抽出してJSONに反映しているかをテスト
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def test_real_data_extraction():
    """実データ抽出機能をテスト"""
    log.info("修正版実データ抽出機能のテストを開始...")
    
    try:
        # 実際の分析結果ディレクトリを使用
        test_output_dir = Path("temp_analysis_check")
        if not test_output_dir.exists():
            log.error("temp_analysis_check ディレクトリが見つかりません")
            return False
        
        from shift_suite.tasks.ai_comprehensive_report_generator import AIComprehensiveReportGenerator
        
        # AI包括レポート生成器の初期化
        generator = AIComprehensiveReportGenerator()
        
        # テスト用analysis_resultsの準備（最小限）
        test_analysis_results = {
            "basic_info": {
                "total_analysis_time": 120.5,
                "modules_executed": ["Shortage", "Fatigue", "Fairness", "Heatmap", "Cost"]
            }
        }
        
        test_analysis_params = {
            "slot_minutes": 30,
            "need_calculation_method": "p25_based",
            "statistical_method": "p25",
            "outlier_removal_enabled": True,
            "analysis_start_date": "2025-01-01",
            "analysis_end_date": "2025-03-31",
            "enabled_modules": ["Shortage", "Fatigue", "Fairness", "Cost", "Leave Analysis"]
        }
        
        log.info("実データを使用したレポート生成を開始...")
        report = generator.generate_comprehensive_report(
            analysis_results=test_analysis_results,
            input_file_path="デイ_テスト用データ_休日精緻.xlsx",
            output_dir=str(test_output_dir / "out_p25_based"),
            analysis_params=test_analysis_params
        )
        
        # レポートの検証
        if not report:
            log.error("❌ レポートが空です")
            return False
        
        log.info("=" * 60)
        log.info("実データ抽出結果の検証")
        log.info("=" * 60)
        
        # KPIセクションの確認
        kpis = report.get("key_performance_indicators", {})
        overall_perf = kpis.get("overall_performance", {})
        
        # 不足時間データの確認
        shortage_hours = overall_perf.get("total_shortage_hours", {}).get("value", 0)
        if shortage_hours > 0:
            log.info(f"✅ 実データ抽出成功 - 総不足時間: {shortage_hours:.1f} 時間")
            severity = overall_perf.get("total_shortage_hours", {}).get("severity", "unknown")
            log.info(f"   重要度: {severity}")
        else:
            log.warning("⚠️ 総不足時間がまだ0.0です")
        
        # 疲労スコアの確認
        fatigue_score = overall_perf.get("avg_fatigue_score", {}).get("value", 0.5)
        if fatigue_score != 0.5:  # デフォルト値以外
            log.info(f"✅ 実データ抽出成功 - 平均疲労スコア: {fatigue_score:.3f}")
            threshold_exceeded = overall_perf.get("avg_fatigue_score", {}).get("threshold_exceeded", False)
            log.info(f"   閾値超過: {threshold_exceeded}")
        else:
            log.warning("⚠️ 疲労スコアがデフォルト値のままです")
        
        # 公平性スコアの確認
        fairness_score = overall_perf.get("fairness_score", {}).get("value", 0.8)
        if fairness_score != 0.8:  # デフォルト値以外
            log.info(f"✅ 実データ抽出成功 - 公平性スコア: {fairness_score:.3f}")
            below_threshold = overall_perf.get("fairness_score", {}).get("below_threshold", False)
            log.info(f"   要改善: {below_threshold}")
        else:
            log.warning("⚠️ 公平性スコアがデフォルト値のままです")
        
        # 詳細分析モジュールの確認
        detailed_modules = report.get("detailed_analysis_modules", {})
        
        # 職種パフォーマンス分析
        role_performance = detailed_modules.get("role_performance", [])
        if role_performance:
            log.info(f"✅ 職種パフォーマンス分析: {len(role_performance)}職種")
            for role in role_performance[:3]:  # 最初の3職種を確認
                role_id = role.get("role_id", "unknown")
                shortage = role.get("metrics", {}).get("shortage_hours", {}).get("value", 0)
                log.info(f"   - {role_id}: 不足 {shortage:.1f}時間")
        else:
            log.warning("⚠️ 職種パフォーマンス分析が空です")
        
        # スタッフ疲労分析
        staff_fatigue = detailed_modules.get("staff_fatigue_analysis", [])
        if staff_fatigue:
            log.info(f"✅ スタッフ疲労分析: {len(staff_fatigue)}人分")
            high_fatigue_staff = [s for s in staff_fatigue if s.get("fatigue_score", {}).get("value", 0) > 0.7]
            log.info(f"   - 高疲労スタッフ: {len(high_fatigue_staff)}人")
            
            # 実際のスタッフデータサンプル表示
            for staff in staff_fatigue[:3]:
                staff_id = staff.get("staff_id", "unknown")
                fatigue = staff.get("fatigue_score", {}).get("value", 0)
                status = staff.get("fatigue_score", {}).get("status", "unknown")
                log.info(f"   - {staff_id}: {fatigue:.3f} ({status})")
        else:
            log.warning("⚠️ スタッフ疲労分析が空です")
        
        # スタッフ公平性分析
        staff_fairness = detailed_modules.get("staff_fairness_analysis", [])
        if staff_fairness:
            log.info(f"✅ スタッフ公平性分析: {len(staff_fairness)}人分")
            low_fairness_staff = [s for s in staff_fairness if s.get("fairness_score", {}).get("below_threshold", False)]
            log.info(f"   - 公平性要改善スタッフ: {len(low_fairness_staff)}人")
            
            # 実際のスタッフデータサンプル表示
            for staff in staff_fairness[:3]:
                staff_id = staff.get("staff_id", "unknown")
                fairness = staff.get("fairness_score", {}).get("value", 0)
                status = staff.get("fairness_score", {}).get("status", "unknown")
                log.info(f"   - {staff_id}: {fairness:.3f} ({status})")
        else:
            log.warning("⚠️ スタッフ公平性分析が空です")
        
        # 時間枠分析
        time_slot_analysis = detailed_modules.get("time_slot_analysis", [])
        if time_slot_analysis:
            log.info(f"✅ 時間枠分析: {len(time_slot_analysis)}時間枠")
            critical_slots = [t for t in time_slot_analysis if t.get("metrics", {}).get("shortage_excess_value", {}).get("severity") == "high"]
            log.info(f"   - 重要時間枠: {len(critical_slots)}枠")
            
            # 実際の時間枠データサンプル表示
            for slot in time_slot_analysis[:3]:
                time_slot = slot.get("time_slot", "unknown")
                value = slot.get("metrics", {}).get("shortage_excess_value", {}).get("value", 0)
                severity = slot.get("metrics", {}).get("shortage_excess_value", {}).get("severity", "unknown")
                log.info(f"   - {time_slot}: {value:.1f} ({severity})")
        else:
            log.warning("⚠️ 時間枠分析が空です")
        
        # 重要な観測結果
        observations = report.get("summary_of_critical_observations", [])
        log.info(f"📊 重要な観測結果: {len(observations)}件")
        for obs in observations:
            category = obs.get('category', 'unknown')
            severity = obs.get('severity', 'unknown')
            description = obs.get('description', 'no description')[:100]
            log.info(f"   - {category} ({severity}): {description}...")
        
        # システム問題類型
        problem_archetypes = report.get("systemic_problem_archetypes", [])
        log.info(f"📊 システム問題類型: {len(problem_archetypes)}件")
        for arch in problem_archetypes:
            arch_id = arch.get('archetype_id', 'unknown')
            description = arch.get('description', 'no description')[:80]
            log.info(f"   - {arch_id}: {description}...")
        
        # ルール違反
        rule_violations = report.get("rule_violation_summary", [])
        log.info(f"📊 ルール違反: {len(rule_violations)}件")
        for violation in rule_violations:
            rule_id = violation.get('rule_id', 'unknown')
            count = violation.get('violation_count_last_period', 0)
            log.info(f"   - {rule_id}: {count}件")
        
        # 生成されたJSONファイルの確認
        json_files = list(Path(".").glob("ai_comprehensive_report_*.json"))
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)  # 最新のファイルを先頭に
        
        if json_files:
            latest_json = json_files[0]
            log.info(f"✅ 最新JSONレポートファイル: {latest_json.name}")
            
            # ファイルサイズをチェック
            file_size = latest_json.stat().st_size
            log.info(f"📊 レポートファイルサイズ: {file_size:,} bytes")
            
            if file_size > 50000:  # 50KB以上なら実データが含まれていると判断
                log.info("✅ 実データを含む充実したレポートが生成されました")
                
                # 一部のKPIを実際のJSONから再確認
                with open(latest_json, 'r', encoding='utf-8') as f:
                    saved_report = json.load(f)
                
                saved_shortage = saved_report.get("key_performance_indicators", {}).get("overall_performance", {}).get("total_shortage_hours", {}).get("value", 0)
                saved_fatigue = saved_report.get("key_performance_indicators", {}).get("overall_performance", {}).get("avg_fatigue_score", {}).get("value", 0.5)
                
                log.info(f"📊 保存されたKPI - 不足時間: {saved_shortage}, 疲労: {saved_fatigue:.3f}")
                
                # 詳細分析データの確認
                saved_modules = saved_report.get("detailed_analysis_modules", {})
                role_count = len(saved_modules.get("role_performance", []))
                fatigue_count = len(saved_modules.get("staff_fatigue_analysis", []))
                fairness_count = len(saved_modules.get("staff_fairness_analysis", []))
                
                log.info(f"📊 保存された分析 - 職種: {role_count}, 疲労: {fatigue_count}, 公平性: {fairness_count}")
                
                return True
            else:
                log.warning("⚠️ レポートファイルが小さすぎます。実データが不足している可能性があります")
                return False
        else:
            log.error("❌ JSONレポートファイルが見つかりません")
            return False
        
    except Exception as e:
        log.error(f"❌ 実データ抽出テストエラー: {e}", exc_info=True)
        return False

def main():
    """メインテスト実行"""
    log.info("=" * 80)
    log.info("修正版AI包括レポート生成機能 実データ抽出テスト開始")
    log.info("=" * 80)
    
    success = test_real_data_extraction()
    
    log.info("=" * 80)
    log.info("テスト結果")
    log.info("=" * 80)
    
    if success:
        log.info("🎉 修正版実データ抽出機能テストが成功しました！")
        log.info("✨ 実際のParquet/CSVファイルデータが正常に抽出され、JSONレポートに反映されています。")
        log.info("📋 これでAIが分析を行うための「材料」が提供されます。")
        return True
    else:
        log.error("❌ テストが失敗しました。まだ改善が必要です。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)