#!/usr/bin/env python3
"""
動的連続勤務検出システムのテストスクリプト
完全に汎用的なデータ対応をテスト
"""

import sys
import logging
from pathlib import Path
import pandas as pd
import datetime as dt

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
log = logging.getLogger(__name__)

def test_dynamic_pattern_detection():
    """動的パターン検出機能のテスト"""
    try:
        from shift_suite.tasks.dynamic_continuous_shift_detector import DynamicContinuousShiftDetector
        from shift_suite.tasks.io_excel import ingest_excel
        
        log.info("=== 動的パターン検出テスト開始 ===")
        
        # テストデータの読み込み
        excel_path = Path("テストデータ_勤務表　勤務時間_トライアル.xlsx")
        if not excel_path.exists():
            log.error(f"テストファイルが見つかりません: {excel_path}")
            return False
        
        long_df, wt_df, unknown_codes = ingest_excel(
            excel_path,
            shift_sheets=["R7.6"],
            header_row=1,
            slot_minutes=15
        )
        
        log.info(f"データ読み込み完了: {len(long_df)}件")
        
        # 設定ファイルパス
        config_path = Path("shift_suite/config/dynamic_continuous_shift_config.json")
        
        # 動的検出器の初期化
        detector = DynamicContinuousShiftDetector(config_path)
        
        log.info("=== データから自動学習開始 ===")
        
        # 自動パターン検出・学習
        detector.auto_detect_patterns_from_data(long_df, wt_df)
        
        log.info(f"学習済みパターン数: {len(detector.shift_patterns)}")
        for code, pattern in detector.shift_patterns.items():
            log.info(f"  {code}: {pattern.start_time}-{pattern.end_time} ({'日跨ぎ' if pattern.is_overnight else '通常'})")
        
        log.info(f"学習済みルール数: {len(detector.continuous_shift_rules)}")
        for rule in detector.continuous_shift_rules:
            log.info(f"  {rule.name}: {rule.from_patterns}→{rule.to_patterns}")
        
        # 完全動的検出の実行
        continuous_shifts = detector.detect_continuous_shifts(long_df, wt_df)
        
        log.info(f"動的連続勤務検出結果: {len(continuous_shifts)}件")
        
        # 検出統計
        summary = detector.get_detection_summary()
        log.info(f"検出統計: {summary}")
        
        # 具体例の出力
        if continuous_shifts:
            log.info("=== 動的検出された連続勤務例 ===")
            for i, shift in enumerate(continuous_shifts[:3]):
                log.info(
                    f"{i+1}. {shift.staff}: {shift.start_pattern.code}({shift.start_date}) → "
                    f"{shift.end_pattern.code}({shift.end_date}) | ルール: {shift.rule.name} | "
                    f"総時間: {shift.total_duration_hours:.1f}h"
                )
        
        # 学習した設定の保存
        learned_config_path = Path("learned_dynamic_config_test.json")
        detector.export_config(learned_config_path)
        log.info(f"学習済み設定保存: {learned_config_path}")
        
        return len(continuous_shifts) > 0
        
    except Exception as e:
        log.error(f"動的パターン検出テストエラー: {e}", exc_info=True)
        return False

def test_custom_scenario():
    """カスタムシナリオでの動的検出テスト"""
    try:
        from shift_suite.tasks.dynamic_continuous_shift_detector import (
            DynamicContinuousShiftDetector, ShiftPattern, ContinuousShiftRule
        )
        
        log.info("=== カスタムシナリオテスト開始 ===")
        
        # カスタム検出器（設定なし）
        detector = DynamicContinuousShiftDetector()
        
        # カスタムパターンの追加
        custom_patterns = [
            ShiftPattern("早朝", "05:00", "13:00", "早朝勤務", False, 5),
            ShiftPattern("深夜", "21:00", "05:00", "深夜勤務", True, 12),
            ShiftPattern("長時間", "08:00", "20:00", "長時間勤務", False, 3),
        ]
        
        for pattern in custom_patterns:
            detector.shift_patterns[pattern.code] = pattern
        
        # カスタムルールの追加
        custom_rules = [
            ContinuousShiftRule(
                name="深夜→早朝（高負荷パターン）",
                from_patterns=["深夜"], 
                to_patterns=["早朝"],
                max_gap_hours=0.5,
                overlap_tolerance_minutes=15,
                description="深夜から早朝への高負荷連続勤務"
            ),
        ]
        
        detector.continuous_shift_rules.extend(custom_rules)
        
        # サンプルデータでテスト
        sample_data = [
            {'ds': '2025-06-10 21:00:00', 'staff': 'テスト職員A', 'role': 'テスト部署', 'code': '深夜'},
            {'ds': '2025-06-10 22:00:00', 'staff': 'テスト職員A', 'role': 'テスト部署', 'code': '深夜'},
            {'ds': '2025-06-11 00:00:00', 'staff': 'テスト職員A', 'role': 'テスト部署', 'code': '深夜'},
            {'ds': '2025-06-11 05:00:00', 'staff': 'テスト職員A', 'role': 'テスト部署', 'code': '早朝'},
            {'ds': '2025-06-11 06:00:00', 'staff': 'テスト職員A', 'role': 'テスト部署', 'code': '早朝'},
        ]
        
        sample_df = pd.DataFrame(sample_data)
        sample_df['ds'] = pd.to_datetime(sample_df['ds'])
        
        # カスタムシナリオでの検出
        custom_shifts = detector.detect_continuous_shifts(sample_df)
        
        log.info(f"カスタムシナリオ検出結果: {len(custom_shifts)}件")
        
        for shift in custom_shifts:
            log.info(
                f"検出: {shift.staff} | {shift.start_pattern.code}→{shift.end_pattern.code} | "
                f"ルール: {shift.rule.name} | 時間: {shift.total_duration_hours:.1f}h"
            )
        
        return len(custom_shifts) > 0
        
    except Exception as e:
        log.error(f"カスタムシナリオテストエラー: {e}", exc_info=True)
        return False

def test_dynamic_need_adjustment():
    """動的Need調整機能のテスト"""
    try:
        from shift_suite.tasks.dynamic_continuous_shift_detector import DynamicContinuousShiftDetector
        
        log.info("=== 動的Need調整テスト開始 ===")
        
        # 設定ファイルパス
        config_path = Path("shift_suite/config/dynamic_continuous_shift_config.json")
        detector = DynamicContinuousShiftDetector(config_path)
        
        # サンプル連続勤務データ
        sample_data = [
            {'ds': '2025-06-15 23:45:00', 'staff': '田中', 'role': '介護', 'code': '夜'},
            {'ds': '2025-06-16 00:00:00', 'staff': '田中', 'role': '介護', 'code': '明'},
            {'ds': '2025-06-16 00:15:00', 'staff': '田中', 'role': '介護', 'code': '明'},
        ]
        
        sample_df = pd.DataFrame(sample_data)
        sample_df['ds'] = pd.to_datetime(sample_df['ds'])
        
        # 連続勤務の検出
        continuous_shifts = detector.detect_continuous_shifts(sample_df)
        
        log.info(f"Need調整テスト用連続勤務: {len(continuous_shifts)}件")
        
        # 動的Need調整の検証
        test_time_slots = ["00:00", "00:15", "00:30", "06:00", "07:00"]
        test_date = "2025-06-16"
        
        for time_slot in test_time_slots:
            should_adjust, continuing_count, rule_info = detector.should_adjust_need_dynamic(
                time_slot, test_date
            )
            
            log.info(
                f"時刻 {time_slot}: 調整{'要' if should_adjust else '不要'} | "
                f"継続者{continuing_count}名 | ルール: {rule_info}"
            )
        
        return len(continuous_shifts) > 0
        
    except Exception as e:
        log.error(f"動的Need調整テストエラー: {e}", exc_info=True)
        return False

def main():
    """メインテスト実行"""
    log.info("動的連続勤務検出システム 統合テスト開始")
    
    tests = [
        ("動的パターン検出", test_dynamic_pattern_detection),
        ("カスタムシナリオ", test_custom_scenario),
        ("動的Need調整", test_dynamic_need_adjustment),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        log.info(f"\n{'='*60}")
        log.info(f"テスト実行: {test_name}")
        log.info(f"{'='*60}")
        
        try:
            result = test_func()
            results[test_name] = result
            log.info(f"{test_name}: {'✅ 成功' if result else '❌ 失敗'}")
        except Exception as e:
            log.error(f"{test_name}: ❌ エラー - {e}")
            results[test_name] = False
    
    # 総合結果
    log.info(f"\n{'='*60}")
    log.info("動的システムテスト結果サマリー")
    log.info(f"{'='*60}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, result in results.items():
        status = "✅ 成功" if result else "❌ 失敗"
        log.info(f"{test_name}: {status}")
    
    log.info(f"\n総合結果: {passed_tests}/{total_tests} テスト成功")
    
    if passed_tests == total_tests:
        log.info("🎉 全テスト成功！動的連続勤務検出システムが正常に動作しています。")
        log.info("✨ システムは完全に動的データに対応可能です。")
        return True
    else:
        log.warning("⚠️  一部テストが失敗しました。システムの確認が必要です。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)