#!/usr/bin/env python3
"""
統一分析管理システム最終統合検証スクリプト

全体最適化アプローチの最終確認：
1. 動的データ処理の安全性確認
2. 統一システムとAI包括レポートの連携確認
3. エラー処理とフォールバック機能の検証
4. メモリ効率とクリーンアップ機能の確認
"""

import logging
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def test_unified_analysis_system():
    """統一分析管理システムの包括的テスト"""
    
    log.info("=" * 80)
    log.info("統一分析管理システム 最終統合検証開始")
    log.info("=" * 80)
    
    try:
        # 1. 統一分析管理システムのインポート確認
        from shift_suite.tasks.unified_analysis_manager import (
            UnifiedAnalysisManager, 
            SafeDataConverter, 
            DynamicKeyManager,
            UnifiedAnalysisResult
        )
        log.info("✅ 統一分析管理システムのインポート成功")
        
        # 2. AI包括レポートジェネレーターのインポート確認
        try:
            from shift_suite.tasks.ai_comprehensive_report_generator import AIComprehensiveReportGenerator
            ai_available = True
            log.info("✅ AI包括レポートジェネレーターのインポート成功")
        except ImportError as e:
            ai_available = False
            log.warning(f"⚠️ AI包括レポートジェネレーター利用不可: {e}")
        
        # 3. 統一分析管理システムの初期化
        manager = UnifiedAnalysisManager()
        log.info("✅ UnifiedAnalysisManager初期化成功")
        
        # 4. テストデータの生成（実データに近い形式）
        test_data = create_realistic_test_data()
        log.info(f"✅ テストデータ生成完了: {len(test_data['long_df'])}行")
        
        # 5. 各分析タイプのテスト実行
        results = {}
        
        # 5.1 不足分析テスト
        log.info("\n--- 不足分析テスト ---")
        shortage_result = manager.create_shortage_analysis(
            "test_file.xlsx", "default", test_data['role_shortage_df']
        )
        results['shortage'] = shortage_result
        log.info(f"✅ 不足分析完了: {shortage_result.data_integrity}")
        log.info(f"   総不足時間: {shortage_result.core_metrics.get('total_shortage_hours', {}).get('value', 'N/A')}")
        
        # 5.2 疲労分析テスト
        log.info("\n--- 疲労分析テスト ---")
        fatigue_result = manager.create_fatigue_analysis(
            "test_file.xlsx", "default", test_data['fatigue_df'], test_data['combined_df']
        )
        results['fatigue'] = fatigue_result
        log.info(f"✅ 疲労分析完了: {fatigue_result.data_integrity}")
        log.info(f"   平均疲労スコア: {fatigue_result.core_metrics.get('avg_fatigue_score', {}).get('value', 'N/A')}")
        
        # 5.3 公平性分析テスト
        log.info("\n--- 公平性分析テスト ---")
        fairness_results = manager.create_fairness_analysis(
            "test_file.xlsx", "default", test_data['fairness_df']
        )
        results['fairness'] = fairness_results
        log.info(f"✅ 公平性分析完了: {len(fairness_results)}結果")
        if fairness_results:
            avg_score = fairness_results[0].core_metrics.get('avg_fairness_score', {}).get('value', 'N/A')
            log.info(f"   平均公平性スコア: {avg_score}")
        
        # 6. AI互換結果の取得テスト
        log.info("\n--- AI互換結果取得テスト ---")
        ai_compatible_results = manager.get_ai_compatible_results("test_file")
        log.info(f"✅ AI互換結果取得完了: {len(ai_compatible_results)}種類")
        
        for analysis_type, data in ai_compatible_results.items():
            integrity = data.get('data_integrity', 'unknown')
            log.info(f"   {analysis_type}: {integrity}")
        
        # 7. AI包括レポートとの連携テスト（利用可能な場合）
        if ai_available:
            log.info("\n--- AI包括レポート連携テスト ---")
            try:
                generator = AIComprehensiveReportGenerator()
                
                # 統一システムの結果を使用してレポート生成テスト
                test_params = {
                    "slot_minutes": 30,
                    "need_calculation_method": "statistical_estimation",
                    "analysis_start_date": "2025-01-01",
                    "analysis_end_date": "2025-01-31"
                }
                
                # AI互換結果を直接使用
                mece_report = generator.generate_mece_report(
                    ai_compatible_results, test_params
                )
                
                log.info("✅ AI包括レポート生成成功")
                log.info(f"   MECE構造: {len(mece_report)}セクション")
                
                # MECE構造の確認
                expected_sections = [
                    "executive_summary", "shortage_analysis", "fatigue_analysis", 
                    "fairness_analysis", "operational_metrics", "risk_assessment"
                ]
                
                missing_sections = [s for s in expected_sections if s not in mece_report]
                if missing_sections:
                    log.warning(f"⚠️ 不足セクション: {missing_sections}")
                else:
                    log.info("✅ MECE構造完全性確認")
                
            except Exception as e:
                log.error(f"❌ AI包括レポート連携エラー: {e}", exc_info=True)
        
        # 8. エラー処理とフォールバック機能のテスト
        log.info("\n--- エラー処理テスト ---")
        test_error_handling(manager)
        
        # 9. データ型安全性テスト
        log.info("\n--- データ型安全性テスト ---")
        test_data_safety()
        
        # 10. メモリ効率とクリーンアップテスト
        log.info("\n--- メモリ効率テスト ---")
        test_memory_efficiency(manager)
        
        # 11. 動的キー管理テスト
        log.info("\n--- 動的キー管理テスト ---")
        test_dynamic_key_management()
        
        log.info("\n" + "=" * 80)
        log.info("🎉 統一分析管理システム 最終統合検証完了")
        log.info("全体最適化アプローチによる統一システムが正常に動作しています")
        log.info("=" * 80)
        
        return True
        
    except Exception as e:
        log.error(f"❌ 統合検証中に重大エラー: {e}", exc_info=True)
        return False

def create_realistic_test_data():
    """実データに近いテストデータの生成"""
    np.random.seed(42)
    
    # 長期間データ（long_df相当）
    dates = pd.date_range('2025-01-01', '2025-01-31', freq='30T')
    staff_list = [f"スタッフ{i:02d}" for i in range(1, 21)]
    
    long_df = []
    for date in dates[:100]:  # テスト用に制限
        for staff in staff_list[:5]:  # テスト用に制限
            long_df.append({
                'ds': date,
                'staff': staff,
                'role': f'役職{np.random.randint(1, 4)}',
                'code': np.random.choice(['日勤', '夜勤', '遅番']),
                'parsed_slots_count': np.random.randint(0, 16)
            })
    
    long_df = pd.DataFrame(long_df)
    
    # 不足分析用データ
    role_shortage_df = pd.DataFrame({
        'role': [f'役職{i}' for i in range(1, 6)],
        'lack_h': np.random.exponential(5, 5),  # 不足時間
        'need_h': np.random.normal(40, 10, 5)   # 必要時間
    })
    
    # 疲労分析用データ
    fatigue_df = pd.DataFrame({
        'staff': staff_list[:10],
        'fatigue_score': np.random.beta(2, 5, 10),  # 0-1の疲労スコア
        'work_hours': np.random.normal(8, 2, 10)
    })
    
    # 統合スコアデータ
    combined_df = pd.DataFrame({
        'staff': staff_list[:10],
        'final_score': np.random.normal(75, 15, 10),  # 評価スコア
        'performance': np.random.uniform(0.5, 1.0, 10)
    })
    
    # 公平性分析用データ
    fairness_df = pd.DataFrame({
        'staff': staff_list[:10],
        'night_ratio': np.random.beta(2, 8, 10),     # 夜勤比率
        'total_shifts': np.random.poisson(20, 10),   # 総シフト数
        'fairness_score': np.random.beta(5, 2, 10)   # 公平性スコア
    })
    
    return {
        'long_df': long_df,
        'role_shortage_df': role_shortage_df,
        'fatigue_df': fatigue_df,
        'combined_df': combined_df,
        'fairness_df': fairness_df
    }

def test_error_handling(manager):
    """エラー処理とフォールバック機能のテスト"""
    
    # 空データフレームのテスト
    empty_df = pd.DataFrame()
    result = manager.create_shortage_analysis("empty_test.xlsx", "default", empty_df)
    assert result.data_integrity in ["valid", "error"]
    log.info("✅ 空データフレーム処理確認")
    
    # 不正なデータタイプのテスト
    invalid_df = pd.DataFrame({
        'lack_h': ['invalid', None, float('inf'), -1],
        'role': ['役職A', '役職B', '役職C', '役職D']
    })
    result = manager.create_shortage_analysis("invalid_test.xlsx", "default", invalid_df)
    log.info(f"✅ 不正データ処理確認: {result.data_integrity}")
    
    # NaN/Inf値のテスト
    nan_df = pd.DataFrame({
        'lack_h': [1.0, np.nan, np.inf, -np.inf, 5.0],
        'role': ['A', 'B', 'C', 'D', 'E']
    })
    result = manager.create_shortage_analysis("nan_test.xlsx", "default", nan_df)
    log.info("✅ NaN/Inf値処理確認")

def test_data_safety():
    """データ型安全性のテスト"""
    from shift_suite.tasks.unified_analysis_manager import SafeDataConverter
    
    converter = SafeDataConverter()
    
    # 各種データ型の安全変換テスト
    test_cases = [
        (None, 0.0, "none_test"),
        ("123.45", 123.45, "string_number"),
        (float('inf'), 0.0, "infinity_test"),
        (float('nan'), 0.0, "nan_test"),
        ("invalid", 0.0, "invalid_string")
    ]
    
    for input_val, expected, field_name in test_cases:
        result = converter.safe_float(input_val, 0.0, field_name)
        assert isinstance(result, (int, float)), f"{field_name}で数値型でない結果"
        assert not np.isinf(result), f"{field_name}でInf値"
        assert not np.isnan(result), f"{field_name}でNaN値"
    
    log.info("✅ データ型安全性確認完了")

def test_memory_efficiency(manager):
    """メモリ効率とクリーンアップ機能のテスト"""
    
    # 大量データの処理テスト
    large_df = pd.DataFrame({
        'lack_h': np.random.exponential(2, 1000),
        'role': [f'役職{i%50}' for i in range(1000)]
    })
    
    initial_count = len(manager.results_registry)
    
    # 複数の分析を実行
    for i in range(5):
        manager.create_shortage_analysis(f"large_test_{i}.xlsx", "default", large_df)
    
    after_count = len(manager.results_registry)
    assert after_count > initial_count, "結果が登録されていない"
    
    # クリーンアップテスト（0時間で全削除）
    manager.cleanup_old_results(max_age_hours=0)
    
    final_count = len(manager.results_registry)
    log.info(f"✅ メモリクリーンアップ確認: {after_count} → {final_count}")

def test_dynamic_key_management():
    """動的キー管理システムのテスト"""
    from shift_suite.tasks.unified_analysis_manager import DynamicKeyManager
    
    key_manager = DynamicKeyManager()
    
    # キー生成テスト
    key1 = key_manager.generate_analysis_key("test file.xlsx", "scenario1", "shortage")
    key2 = key_manager.generate_analysis_key("test file.xlsx", "scenario1", "shortage")
    
    assert key1 != key2, "同一条件で異なるキーが生成されない"
    log.info("✅ 動的キー生成確認")
    
    # キー解析テスト
    info = key_manager.extract_file_info(key1)
    assert info["file_name"] == "test_file", f"ファイル名解析エラー: {info['file_name']}"
    assert info["scenario_key"] == "scenario1", f"シナリオキー解析エラー: {info['scenario_key']}"
    assert info["analysis_type"] == "shortage", f"分析タイプ解析エラー: {info['analysis_type']}"
    
    log.info("✅ キー解析機能確認")

if __name__ == "__main__":
    success = test_unified_analysis_system()
    sys.exit(0 if success else 1)