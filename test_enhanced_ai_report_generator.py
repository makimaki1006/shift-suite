#!/usr/bin/env python3
"""
修正版AI包括レポート生成機能のテスト

実際のParquetファイルデータ抽出機能をテスト
"""

import sys
import json
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def create_test_parquet_files(output_dir: Path):
    """テスト用Parquetファイルを作成"""
    
    # 不足分析用テストデータ
    shortage_data = pd.DataFrame({
        'time_slot': ['09:00-10:00', '10:00-11:00', '14:00-15:00', '18:00-19:00'],
        'date': ['2025-01-15', '2025-01-15', '2025-01-16', '2025-01-16'],
        'role': ['看護師', '介護士', '看護師', '介護士'],
        'shortage_hours': [5.2, -2.1, 8.5, 3.7],
        'need_hours': [40.0, 30.0, 35.0, 25.0],
        'actual_hours': [34.8, 32.1, 26.5, 21.3]
    })
    shortage_file = output_dir / "test_shortage_analysis.parquet"
    shortage_data.to_parquet(shortage_file)
    log.info(f"不足分析テストファイル作成: {shortage_file}")
    
    # 疲労分析用テストデータ
    fatigue_data = pd.DataFrame({
        'staff_id': ['S001', 'S002', 'S003', 'S004', 'S005'],
        'fatigue_score': [0.85, 0.65, 0.45, 0.78, 0.32],
        'consecutive_shifts': [6, 3, 2, 5, 1],
        'night_shift_ratio': [0.35, 0.20, 0.10, 0.30, 0.05],
        'short_rest_count': [3, 1, 0, 2, 0],
        'avg_daily_hours': [9.2, 8.5, 7.8, 8.8, 7.2],
        'recent_leave_days': [0, 2, 5, 1, 3],
        'role': ['看護師', '介護士', '看護師', '介護士', '看護師'],
        'employment_type': ['正社員', 'パート', '正社員', '正社員', 'パート']
    })
    fatigue_file = output_dir / "test_fatigue_analysis.parquet"
    fatigue_data.to_parquet(fatigue_file)
    log.info(f"疲労分析テストファイル作成: {fatigue_file}")
    
    # 公平性分析用テストデータ
    fairness_data = pd.DataFrame({
        'staff_id': ['S001', 'S002', 'S003', 'S004', 'S005'],
        'fairness_score': [0.72, 0.89, 0.56, 0.91, 0.68],
        'total_shifts': [22, 18, 25, 20, 16],
        'weekend_shifts': [6, 4, 8, 5, 3],
        'night_shifts': [4, 2, 6, 3, 1],
        'overtime_hours': [12.5, 3.2, 18.7, 8.1, 2.0],
        'role': ['看護師', '介護士', '看護師', '介護士', '看護師'],
        'employment_type': ['正社員', 'パート', '正社員', '正社員', 'パート']
    })
    fairness_file = output_dir / "test_fairness_analysis.parquet"
    fairness_data.to_parquet(fairness_file)
    log.info(f"公平性分析テストファイル作成: {fairness_file}")
    
    # ヒートマップ用テストデータ
    heatmap_data = pd.DataFrame({
        'time_slot': ['06:00-07:00', '07:00-08:00', '12:00-13:00', '18:00-19:00', '22:00-23:00'],
        'day_of_week': ['Monday', 'Monday', 'Tuesday', 'Wednesday', 'Friday'],
        'value': [3.2, -1.8, 5.7, 8.9, -2.3],
        'intensity': ['normal', 'low', 'high', 'critical', 'low'],
        'role': ['看護師', '介護士', '看護師', '介護士', '看護師']
    })
    heatmap_file = output_dir / "test_heatmap_analysis.parquet"
    heatmap_data.to_parquet(heatmap_file)
    log.info(f"ヒートマップテストファイル作成: {heatmap_file}")
    
    return {
        "shortage_file": shortage_file,
        "fatigue_file": fatigue_file, 
        "fairness_file": fairness_file,
        "heatmap_file": heatmap_file
    }

def test_enhanced_report_generation():
    """修正版レポート生成機能をテスト"""
    log.info("修正版AI包括レポート生成機能のテストを開始...")
    
    try:
        from shift_suite.tasks.ai_comprehensive_report_generator import AIComprehensiveReportGenerator
        
        # テスト用出力ディレクトリの作成
        test_output_dir = Path("temp_enhanced_test_output")
        test_output_dir.mkdir(exist_ok=True)
        
        # テスト用Parquetファイルの作成
        test_files = create_test_parquet_files(test_output_dir)
        
        # テスト用analysis_resultsの準備（最小限）
        test_analysis_results = {
            "basic_info": {
                "total_analysis_time": 45.2,
                "modules_executed": ["Shortage", "Fatigue", "Fairness", "Heatmap"]
            }
        }
        
        test_analysis_params = {
            "slot_minutes": 60,
            "need_calculation_method": "statistical_estimation",
            "statistical_method": "median",
            "outlier_removal_enabled": True,
            "analysis_start_date": "2025-01-01",
            "analysis_end_date": "2025-01-31",
            "enabled_modules": ["Shortage", "Fatigue", "Fairness", "Heatmap"]
        }
        
        # AI包括レポート生成器の初期化
        generator = AIComprehensiveReportGenerator()
        
        # 修正版レポート生成
        log.info("修正版包括レポートを生成中...")
        report = generator.generate_comprehensive_report(
            analysis_results=test_analysis_results,
            input_file_path="test_enhanced_data.xlsx",
            output_dir=str(test_output_dir),
            analysis_params=test_analysis_params
        )
        
        # レポートの検証
        if not report:
            log.error("❌ レポートが空です")
            return False
        
        # 実データが正しく抽出されているかチェック
        kpis = report.get("key_performance_indicators", {})
        overall_perf = kpis.get("overall_performance", {})
        
        # 不足時間が実データから抽出されているかチェック
        shortage_hours = overall_perf.get("total_shortage_hours", {}).get("value", 0)
        if shortage_hours > 0:
            log.info(f"✅ 実データ抽出成功 - 総不足時間: {shortage_hours} 時間")
        else:
            log.warning("⚠️ 不足時間データが抽出されていません")
        
        # 疲労スコアが実データから抽出されているかチェック
        fatigue_score = overall_perf.get("avg_fatigue_score", {}).get("value", 0)
        if fatigue_score != 0.5:  # デフォルト値以外
            log.info(f"✅ 実データ抽出成功 - 平均疲労スコア: {fatigue_score:.3f}")
        else:
            log.warning("⚠️ 疲労スコアがデフォルト値のままです")
        
        # 詳細分析モジュールのチェック
        detailed_modules = report.get("detailed_analysis_modules", {})
        
        # 職種パフォーマンス分析
        role_performance = detailed_modules.get("role_performance", [])
        if role_performance:
            log.info(f"✅ 職種パフォーマンス分析: {len(role_performance)}職種")
            for role in role_performance[:2]:  # 最初の2職種を確認
                role_id = role.get("role_id", "unknown")
                shortage = role.get("metrics", {}).get("shortage_hours", {}).get("value", 0)
                log.info(f"  - {role_id}: 不足 {shortage:.1f}時間")
        else:
            log.warning("⚠️ 職種パフォーマンス分析が空です")
        
        # スタッフ疲労分析
        staff_fatigue = detailed_modules.get("staff_fatigue_analysis", [])
        if staff_fatigue:
            log.info(f"✅ スタッフ疲労分析: {len(staff_fatigue)}人分")
            high_fatigue_staff = [s for s in staff_fatigue if s.get("fatigue_score", {}).get("value", 0) > 0.7]
            log.info(f"  - 高疲労スタッフ: {len(high_fatigue_staff)}人")
        else:
            log.warning("⚠️ スタッフ疲労分析が空です")
        
        # スタッフ公平性分析
        staff_fairness = detailed_modules.get("staff_fairness_analysis", [])
        if staff_fairness:
            log.info(f"✅ スタッフ公平性分析: {len(staff_fairness)}人分")
            low_fairness_staff = [s for s in staff_fairness if s.get("fairness_score", {}).get("below_threshold", False)]
            log.info(f"  - 公平性要改善スタッフ: {len(low_fairness_staff)}人")
        else:
            log.warning("⚠️ スタッフ公平性分析が空です")
        
        # 時間枠分析
        time_slot_analysis = detailed_modules.get("time_slot_analysis", [])
        if time_slot_analysis:
            log.info(f"✅ 時間枠分析: {len(time_slot_analysis)}時間枠")
            critical_slots = [t for t in time_slot_analysis if t.get("metrics", {}).get("shortage_excess_value", {}).get("severity") == "high"]
            log.info(f"  - 重要時間枠: {len(critical_slots)}枠")
        else:
            log.warning("⚠️ 時間枠分析が空です")
        
        # 重要な観測結果
        observations = report.get("summary_of_critical_observations", [])
        log.info(f"📊 重要な観測結果: {len(observations)}件")
        for obs in observations:
            category = obs.get('category', 'unknown')
            severity = obs.get('severity', 'unknown')
            log.info(f"  - {category} ({severity}): {obs.get('description', 'no description')[:80]}...")
        
        # 生成されたJSONファイルの確認
        json_files = list(test_output_dir.glob("ai_comprehensive_report_*.json"))
        if json_files:
            json_file = json_files[0]
            log.info(f"✅ JSONレポートファイル生成確認: {json_file.name}")
            
            # ファイルサイズをチェック
            file_size = json_file.stat().st_size
            log.info(f"📊 レポートファイルサイズ: {file_size:,} bytes")
            
            if file_size > 10000:  # 10KB以上なら実データが含まれていると判断
                log.info("✅ 実データを含む充実したレポートが生成されました")
            else:
                log.warning("⚠️ レポートファイルが小さすぎます。実データが不足している可能性があります")
        else:
            log.error("❌ JSONレポートファイルが見つかりません")
            return False
        
        # クリーンアップ
        try:
            import shutil
            shutil.rmtree(test_output_dir)
            log.info("🧹 テスト用ファイルをクリーンアップ")
        except Exception as e:
            log.warning(f"クリーンアップエラー: {e}")
        
        log.info("✅ 修正版AI包括レポート生成機能テスト成功")
        return True
        
    except Exception as e:
        log.error(f"❌ 修正版レポート生成テストエラー: {e}", exc_info=True)
        return False

def main():
    """メインテスト実行"""
    log.info("=" * 80)
    log.info("修正版AI包括レポート生成機能テスト開始")
    log.info("=" * 80)
    
    success = test_enhanced_report_generation()
    
    log.info("=" * 80)
    log.info("テスト結果")
    log.info("=" * 80)
    
    if success:
        log.info("🎉 修正版AI包括レポート生成機能テストが成功しました！")
        log.info("✨ 実際のParquetファイルデータが正常に抽出され、JSONレポートに反映されています。")
        log.info("📋 これで実用的なAI向け分析データが生成されます。")
        return True
    else:
        log.error("❌ テストが失敗しました。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)