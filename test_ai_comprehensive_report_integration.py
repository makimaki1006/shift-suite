#!/usr/bin/env python3
"""
AI向け包括的レポート生成機能の統合テスト

app.pyに統合されたAI包括レポート生成機能が正常に動作することを確認
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def test_ai_report_generator_import():
    """AI包括レポート生成器のインポートテスト"""
    log.info("AI包括レポート生成器のインポートテストを開始...")
    
    try:
        from shift_suite.tasks.ai_comprehensive_report_generator import AIComprehensiveReportGenerator
        log.info("✅ AIComprehensiveReportGenerator のインポート成功")
        return True
    except ImportError as e:
        log.error(f"❌ インポートエラー: {e}")
        return False

def test_report_generation():
    """レポート生成テスト"""
    log.info("レポート生成テストを開始...")
    
    try:
        from shift_suite.tasks.ai_comprehensive_report_generator import AIComprehensiveReportGenerator
        
        # テスト用データの準備
        test_analysis_results = {
            "shortage_analysis": {
                "total_shortage_hours": 150.5,
                "total_excess_hours": 25.0,
                "avg_shortage_per_slot": 5.2
            },
            "fatigue_analysis": {
                "avg_fatigue_score": 0.75,
                "high_fatigue_staff_count": 8,
                "staff_fatigue": {
                    "S001": {"fatigue_score": 0.85, "consecutive_shifts": 6},
                    "S002": {"fatigue_score": 0.65, "consecutive_shifts": 3}
                }
            },
            "fairness_analysis": {
                "avg_fairness_score": 0.68,
                "low_fairness_staff_count": 5
            },
            "data_summary": {
                "total_records": 1000,
                "analysis_period": "2025-01-01 to 2025-03-31",
                "generated_files_count": 15
            }
        }
        
        test_analysis_params = {
            "slot_minutes": 30,
            "need_calculation_method": "statistical_estimation",
            "statistical_method": "median",
            "outlier_removal_enabled": True,
            "analysis_start_date": "2025-01-01",
            "analysis_end_date": "2025-03-31",
            "enabled_modules": ["Shortage", "Fatigue", "Fairness"]
        }
        
        # 一時出力ディレクトリの作成
        output_dir = Path("temp_test_output")
        output_dir.mkdir(exist_ok=True)
        
        # AI包括レポート生成器の初期化
        generator = AIComprehensiveReportGenerator()
        
        # レポート生成
        log.info("包括レポートを生成中...")
        report = generator.generate_comprehensive_report(
            analysis_results=test_analysis_results,
            input_file_path="test_data.xlsx",
            output_dir=str(output_dir),
            analysis_params=test_analysis_params
        )
        
        # レポートの検証
        if not report:
            log.error("❌ レポートが空です")
            return False
        
        # 必須セクションの存在確認
        required_sections = [
            "report_metadata",
            "execution_summary", 
            "data_quality_assessment",
            "key_performance_indicators",
            "detailed_analysis_modules",
            "systemic_problem_archetypes",
            "rule_violation_summary",
            "prediction_and_forecasting",
            "resource_optimization_insights",
            "analysis_limitations_and_external_factors",
            "summary_of_critical_observations",
            "generated_files_manifest"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in report:
                missing_sections.append(section)
        
        if missing_sections:
            log.error(f"❌ 必須セクションが不足: {missing_sections}")
            return False
        
        log.info("✅ 全ての必須セクションが存在")
        
        # 重要なKPIデータの確認
        kpis = report.get("key_performance_indicators", {})
        overall_perf = kpis.get("overall_performance", {})
        
        if "total_shortage_hours" in overall_perf:
            shortage_hours = overall_perf["total_shortage_hours"]["value"]
            log.info(f"📊 総不足時間: {shortage_hours} 時間")
        
        if "avg_fatigue_score" in overall_perf:
            fatigue_score = overall_perf["avg_fatigue_score"]["value"]
            log.info(f"📊 平均疲労スコア: {fatigue_score}")
        
        # 重要な観測結果の確認
        observations = report.get("summary_of_critical_observations", [])
        log.info(f"📊 重要な観測結果: {len(observations)}件")
        
        for obs in observations:
            log.info(f"  - {obs.get('category', 'unknown')}: {obs.get('description', 'no description')[:100]}...")
        
        # 生成されたファイルの確認
        json_files = list(output_dir.glob("ai_comprehensive_report_*.json"))
        if json_files:
            log.info(f"✅ JSONレポートファイル生成確認: {json_files[0].name}")
            
            # JSONファイルの読み込みテスト
            with open(json_files[0], 'r', encoding='utf-8') as f:
                saved_report = json.load(f)
            
            log.info("✅ JSONファイルの読み込み成功")
            log.info(f"📊 レポートID: {saved_report.get('report_metadata', {}).get('report_id', 'unknown')}")
        else:
            log.warning("⚠️ JSONレポートファイルが見つかりません")
        
        # クリーンアップ
        try:
            import shutil
            shutil.rmtree(output_dir)
            log.info("🧹 テスト用ファイルをクリーンアップ")
        except Exception as e:
            log.warning(f"クリーンアップエラー: {e}")
        
        log.info("✅ レポート生成テスト成功")
        return True
        
    except Exception as e:
        log.error(f"❌ レポート生成テストエラー: {e}", exc_info=True)
        return False

def test_app_integration():
    """app.py統合テスト"""
    log.info("app.py統合テストを開始...")
    
    try:
        # app.pyからAI_REPORT_GENERATOR_AVAILABLEフラグをチェック
        import app
        
        if hasattr(app, 'AI_REPORT_GENERATOR_AVAILABLE'):
            if app.AI_REPORT_GENERATOR_AVAILABLE:
                log.info("✅ app.pyでAI包括レポート生成機能が利用可能")
                return True
            else:
                log.error("❌ app.pyでAI包括レポート生成機能が利用不可")
                return False
        else:
            log.error("❌ app.pyにAI_REPORT_GENERATOR_AVAILABLEフラグが見つかりません")
            return False
            
    except ImportError as e:
        log.error(f"❌ app.py インポートエラー: {e}")
        return False
    except Exception as e:
        log.error(f"❌ app.py統合テストエラー: {e}")
        return False

def main():
    """メインテスト実行"""
    log.info("=" * 80)
    log.info("AI向け包括的レポート生成機能 統合テスト開始")
    log.info("=" * 80)
    
    # テスト1: インポートテスト
    test1_success = test_ai_report_generator_import()
    
    # テスト2: レポート生成テスト
    test2_success = test_report_generation()
    
    # テスト3: app.py統合テスト
    test3_success = test_app_integration()
    
    # 結果サマリー
    log.info("=" * 80)
    log.info("テスト結果サマリー")
    log.info("=" * 80)
    log.info(f"インポートテスト: {'✅ 成功' if test1_success else '❌ 失敗'}")
    log.info(f"レポート生成テスト: {'✅ 成功' if test2_success else '❌ 失敗'}")
    log.info(f"app.py統合テスト: {'✅ 成功' if test3_success else '❌ 失敗'}")
    
    if test1_success and test2_success and test3_success:
        log.info("🎉 全てのテストが成功しました！")
        log.info("✨ AI向け包括的レポート生成機能がapp.pyに正常に統合されています。")
        log.info("📋 分析実行時にZIPファイルに自動的にAI向けJSONレポートが追加されます。")
        return True
    else:
        log.error("❌ 一部のテストが失敗しました。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)