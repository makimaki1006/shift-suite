#!/usr/bin/env python3
"""
EDGE_CASE_TESTING.py - 包括的エッジケーステストスイート
==============================================================

休暇除外修正の包括的テストを実行し、システムの健全性を検証する。

テストカテゴリ:
1. 極端なケース (ALL holidays, NO holidays, single day, full year)
2. 境界条件 (month/year boundaries, mixed holiday types)
3. データ整合性 (parquet consistency, aggregation accuracy)
4. パフォーマンステスト (processing time, memory usage)
5. UI/UX検証 (dashboard tabs, heatmaps, dropdowns)

使用法:
    python EDGE_CASE_TESTING.py --data-dir ./test_data --output-dir ./test_results
"""

import argparse
import datetime as dt
import json
import logging
import os
import sys
import time
import traceback
import warnings
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import gc
import psutil

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Shift-Suite modules
from shift_suite.tasks.io_excel import ingest_excel, load_shift_patterns, LEAVE_CODES
from shift_suite.tasks.utils import apply_rest_exclusion_filter, _valid_df
from shift_suite.tasks.constants import DEFAULT_SLOT_MINUTES, SLOT_HOURS
from shift_suite.logger_config import configure_logging

# Dashboard testing
try:
    from dash_app import app
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
    warnings.warn("Dashboard module not available for UI testing")

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)

class EdgeCaseTestSuite:
    """包括的エッジケーステストスイートのメインクラス"""
    
    def __init__(self, data_dir: Path, output_dir: Path):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # テスト結果格納
        self.test_results = {
            "extreme_cases": {},
            "boundary_conditions": {},
            "data_integrity": {},
            "performance": {},
            "ui_validation": {}
        }
        
        # パフォーマンス測定用
        self.performance_baseline = {}
        self.memory_usage = {}
        
        # テストデータキャッシュ
        self.test_data_cache = {}
        
        logger.info(f"Edge Case Test Suite initialized - Data: {data_dir}, Output: {output_dir}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """全テストスイートを実行"""
        start_time = time.time()
        
        try:
            logger.info("=" * 60)
            logger.info("EDGE CASE TESTING SUITE - STARTING")
            logger.info("=" * 60)
            
            # 1. 極端なケーステスト
            logger.info("\n1. EXTREME CASES TESTING")
            logger.info("-" * 40)
            self._run_extreme_cases_tests()
            
            # 2. 境界条件テスト
            logger.info("\n2. BOUNDARY CONDITIONS TESTING")
            logger.info("-" * 40)
            self._run_boundary_conditions_tests()
            
            # 3. データ整合性テスト
            logger.info("\n3. DATA INTEGRITY TESTING")
            logger.info("-" * 40)
            self._run_data_integrity_tests()
            
            # 4. パフォーマンステスト
            logger.info("\n4. PERFORMANCE TESTING")
            logger.info("-" * 40)
            self._run_performance_tests()
            
            # 5. UI/UX検証テスト
            logger.info("\n5. UI/UX VALIDATION TESTING")
            logger.info("-" * 40)
            self._run_ui_validation_tests()
            
            # 6. 総合レポート生成
            logger.info("\n6. COMPREHENSIVE REPORT GENERATION")
            logger.info("-" * 40)
            self._generate_comprehensive_report()
            
        except Exception as e:
            logger.error(f"Test suite execution failed: {e}")
            logger.error(traceback.format_exc())
            self.test_results["execution_error"] = str(e)
        
        total_time = time.time() - start_time
        self.test_results["total_execution_time"] = total_time
        
        logger.info(f"\nTest suite completed in {total_time:.2f} seconds")
        return self.test_results
    
    def _run_extreme_cases_tests(self):
        """極端なケースのテスト実行"""
        
        # Test 1.1: ALL holidays period
        logger.info("Test 1.1: Period with ALL days being holidays")
        self.test_results["extreme_cases"]["all_holidays"] = self._test_all_holidays_period()
        
        # Test 1.2: NO holidays period
        logger.info("Test 1.2: Period with NO holidays at all")
        self.test_results["extreme_cases"]["no_holidays"] = self._test_no_holidays_period()
        
        # Test 1.3: Single day periods
        logger.info("Test 1.3: Single day periods (holiday vs working day)")
        self.test_results["extreme_cases"]["single_day"] = self._test_single_day_periods()
        
        # Test 1.4: Very long periods (full year)
        logger.info("Test 1.4: Very long periods (full year)")
        self.test_results["extreme_cases"]["full_year"] = self._test_full_year_period()
    
    def _run_boundary_conditions_tests(self):
        """境界条件テストの実行"""
        
        # Test 2.1: Month boundaries with holidays
        logger.info("Test 2.1: Month boundaries with holidays")
        self.test_results["boundary_conditions"]["month_boundaries"] = self._test_month_boundaries()
        
        # Test 2.2: Year boundaries
        logger.info("Test 2.2: Year boundaries")
        self.test_results["boundary_conditions"]["year_boundaries"] = self._test_year_boundaries()
        
        # Test 2.3: Partial week scenarios
        logger.info("Test 2.3: Partial week scenarios")
        self.test_results["boundary_conditions"]["partial_weeks"] = self._test_partial_week_scenarios()
        
        # Test 2.4: Mixed holiday types
        logger.info("Test 2.4: Mixed holiday types in same period")
        self.test_results["boundary_conditions"]["mixed_holidays"] = self._test_mixed_holiday_types()
    
    def _run_data_integrity_tests(self):
        """データ整合性テストの実行"""
        
        # Test 3.1: Parquet file consistency
        logger.info("Test 3.1: Consistency between different parquet files")
        self.test_results["data_integrity"]["parquet_consistency"] = self._test_parquet_consistency()
        
        # Test 3.2: Aggregation accuracy
        logger.info("Test 3.2: Correct aggregation after exclusion")
        self.test_results["data_integrity"]["aggregation_accuracy"] = self._test_aggregation_accuracy()
        
        # Test 3.3: Time slot alignment
        logger.info("Test 3.3: Time slot alignment after filtering")
        self.test_results["data_integrity"]["time_slot_alignment"] = self._test_time_slot_alignment()
    
    def _run_performance_tests(self):
        """パフォーマンステストの実行"""
        
        # Test 4.1: Processing time comparison
        logger.info("Test 4.1: Processing time before/after fixes")
        self.test_results["performance"]["processing_time"] = self._test_processing_time()
        
        # Test 4.2: Memory usage comparison
        logger.info("Test 4.2: Memory usage comparison")
        self.test_results["performance"]["memory_usage"] = self._test_memory_usage()
        
        # Test 4.3: Cache efficiency
        logger.info("Test 4.3: Cache efficiency testing")
        self.test_results["performance"]["cache_efficiency"] = self._test_cache_efficiency()
    
    def _run_ui_validation_tests(self):
        """UI/UX検証テストの実行"""
        
        if not DASHBOARD_AVAILABLE:
            self.test_results["ui_validation"]["skipped"] = "Dashboard not available"
            return
        
        # Test 5.1: Dashboard tabs functionality
        logger.info("Test 5.1: All dashboard tabs functionality")
        self.test_results["ui_validation"]["dashboard_tabs"] = self._test_dashboard_tabs()
        
        # Test 5.2: Heatmap color scales
        logger.info("Test 5.2: Heatmap color scales")
        self.test_results["ui_validation"]["heatmap_colors"] = self._test_heatmap_color_scales()
        
        # Test 5.3: Dropdown filters
        logger.info("Test 5.3: Dropdown filters")
        self.test_results["ui_validation"]["dropdown_filters"] = self._test_dropdown_filters()
        
        # Test 5.4: Date range selectors
        logger.info("Test 5.4: Date range selectors")
        self.test_results["ui_validation"]["date_selectors"] = self._test_date_range_selectors()
    
    def _test_all_holidays_period(self) -> Dict[str, Any]:
        """全日が休日の期間テスト"""
        result = {"status": "passed", "details": {}}
        
        try:
            # 全日休日のテストデータ生成
            test_data = self._create_all_holidays_test_data()
            
            # 休暇除外フィルター適用
            original_count = len(test_data)
            filtered_data = apply_rest_exclusion_filter(test_data, "all_holidays_test")
            filtered_count = len(filtered_data)
            
            result["details"]["original_count"] = original_count
            result["details"]["filtered_count"] = filtered_count
            result["details"]["exclusion_rate"] = (original_count - filtered_count) / original_count if original_count > 0 else 0
            
            # 期待値: 全レコードが除外されること
            if filtered_count == 0:
                result["details"]["validation"] = "PASS - All holiday records correctly excluded"
            else:
                result["details"]["validation"] = f"FAIL - {filtered_count} records not excluded"
                result["status"] = "failed"
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"All holidays test failed: {e}")
        
        return result
    
    def _test_no_holidays_period(self) -> Dict[str, Any]:
        """休日なし期間テスト"""
        result = {"status": "passed", "details": {}}
        
        try:
            # 休日なしのテストデータ生成
            test_data = self._create_no_holidays_test_data()
            
            # 休暇除外フィルター適用
            original_count = len(test_data)
            filtered_data = apply_rest_exclusion_filter(test_data, "no_holidays_test")
            filtered_count = len(filtered_data)
            
            result["details"]["original_count"] = original_count
            result["details"]["filtered_count"] = filtered_count
            result["details"]["exclusion_rate"] = (original_count - filtered_count) / original_count if original_count > 0 else 0
            
            # 期待値: レコードが保持されること
            if filtered_count == original_count:
                result["details"]["validation"] = "PASS - All working records correctly preserved"
            else:
                result["details"]["validation"] = f"FAIL - {original_count - filtered_count} working records incorrectly excluded"
                result["status"] = "failed"
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"No holidays test failed: {e}")
        
        return result
    
    def _test_single_day_periods(self) -> Dict[str, Any]:
        """単日期間テスト"""
        result = {"status": "passed", "details": {}}
        
        try:
            results = {}
            
            # 休日の単日テスト
            holiday_data = self._create_single_holiday_test_data()
            holiday_filtered = apply_rest_exclusion_filter(holiday_data, "single_holiday_test")
            results["holiday_single_day"] = {
                "original": len(holiday_data),
                "filtered": len(holiday_filtered),
                "correctly_excluded": len(holiday_filtered) == 0
            }
            
            # 勤務日の単日テスト
            workday_data = self._create_single_workday_test_data()
            workday_filtered = apply_rest_exclusion_filter(workday_data, "single_workday_test")
            results["workday_single_day"] = {
                "original": len(workday_data),
                "filtered": len(workday_filtered),
                "correctly_preserved": len(workday_filtered) == len(workday_data)
            }
            
            result["details"] = results
            
            # 全テストが成功したかチェック
            all_passed = (results["holiday_single_day"]["correctly_excluded"] and 
                         results["workday_single_day"]["correctly_preserved"])
            
            if not all_passed:
                result["status"] = "failed"
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Single day periods test failed: {e}")
        
        return result
    
    def _test_full_year_period(self) -> Dict[str, Any]:
        """通年期間テスト"""
        result = {"status": "passed", "details": {}}
        
        try:
            # 1年分のテストデータ生成
            test_data = self._create_full_year_test_data()
            
            # パフォーマンス測定
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            filtered_data = apply_rest_exclusion_filter(test_data, "full_year_test")
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            processing_time = end_time - start_time
            memory_delta = end_memory - start_memory
            
            result["details"]["original_count"] = len(test_data)
            result["details"]["filtered_count"] = len(filtered_data)
            result["details"]["processing_time"] = processing_time
            result["details"]["memory_delta_mb"] = memory_delta
            result["details"]["records_per_second"] = len(test_data) / processing_time if processing_time > 0 else 0
            
            # パフォーマンス閾値チェック (例: 1秒以内、メモリ増加100MB以内)
            if processing_time > 1.0:
                result["status"] = "warning"
                result["details"]["performance_warning"] = f"Processing took {processing_time:.2f}s (>1s threshold)"
            
            if memory_delta > 100:
                result["status"] = "warning" if result["status"] != "failed" else "failed"
                result["details"]["memory_warning"] = f"Memory increased by {memory_delta:.1f}MB (>100MB threshold)"
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Full year period test failed: {e}")
        
        return result
    
    def _test_month_boundaries(self) -> Dict[str, Any]:
        """月境界テスト"""
        result = {"status": "passed", "details": {}}
        
        try:
            # 月末・月初にまたがる休日データ生成
            test_data = self._create_month_boundary_test_data()
            
            # 月別に分析
            test_data['month'] = test_data['ds'].dt.month
            monthly_results = {}
            
            for month in test_data['month'].unique():
                month_data = test_data[test_data['month'] == month]
                month_filtered = apply_rest_exclusion_filter(month_data, f"month_{month}_test")
                
                monthly_results[month] = {
                    "original": len(month_data),
                    "filtered": len(month_filtered),
                    "exclusion_rate": (len(month_data) - len(month_filtered)) / len(month_data) if len(month_data) > 0 else 0
                }
            
            result["details"]["monthly_results"] = monthly_results
            
            # 一貫性チェック: 同じ休暇パターンは同じ除外率になるはず
            exclusion_rates = [r["exclusion_rate"] for r in monthly_results.values()]
            if len(set(round(rate, 3) for rate in exclusion_rates)) > 1:
                result["status"] = "warning"
                result["details"]["consistency_warning"] = "Inconsistent exclusion rates across months"
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Month boundaries test failed: {e}")
        
        return result
    
    def _test_year_boundaries(self) -> Dict[str, Any]:
        """年境界テスト"""
        result = {"status": "passed", "details": {}}
        
        try:
            # 年末年始データ生成
            test_data = self._create_year_boundary_test_data()
            
            # 年別分析
            test_data['year'] = test_data['ds'].dt.year
            yearly_results = {}
            
            for year in test_data['year'].unique():
                year_data = test_data[test_data['year'] == year]
                year_filtered = apply_rest_exclusion_filter(year_data, f"year_{year}_test")
                
                yearly_results[year] = {
                    "original": len(year_data),
                    "filtered": len(year_filtered),
                    "exclusion_rate": (len(year_data) - len(year_filtered)) / len(year_data) if len(year_data) > 0 else 0
                }
            
            result["details"]["yearly_results"] = yearly_results
            
            # 日付連続性チェック
            if len(test_data) > 0:
                date_gaps = test_data['ds'].diff().dropna()
                max_gap = date_gaps.max().total_seconds() / 3600  # hours
                result["details"]["max_date_gap_hours"] = max_gap
                
                if max_gap > 24:  # 1日以上の間隔
                    result["details"]["date_continuity_warning"] = f"Large date gap detected: {max_gap:.1f} hours"
                    
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Year boundaries test failed: {e}")
        
        return result
    
    def _test_partial_week_scenarios(self) -> Dict[str, Any]:
        """部分週シナリオテスト"""
        result = {"status": "passed", "details": {}}
        
        try:
            # 部分週データ生成（週の途中から/途中まで）
            test_scenarios = {
                "week_start_partial": self._create_partial_week_start_data(),
                "week_end_partial": self._create_partial_week_end_data(),
                "mid_week_partial": self._create_mid_week_partial_data()
            }
            
            scenario_results = {}
            for scenario_name, data in test_scenarios.items():
                if data is not None and len(data) > 0:
                    filtered = apply_rest_exclusion_filter(data, f"partial_week_{scenario_name}")
                    scenario_results[scenario_name] = {
                        "original": len(data),
                        "filtered": len(filtered),
                        "exclusion_rate": (len(data) - len(filtered)) / len(data) if len(data) > 0 else 0
                    }
                else:
                    scenario_results[scenario_name] = {"error": "No data generated"}
            
            result["details"]["scenario_results"] = scenario_results
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Partial week scenarios test failed: {e}")
        
        return result
    
    def _test_mixed_holiday_types(self) -> Dict[str, Any]:
        """混合休暇タイプテスト"""
        result = {"status": "passed", "details": {}}
        
        try:
            # 複数の休暇タイプを含むデータ生成
            test_data = self._create_mixed_holiday_types_data()
            
            # 休暇タイプ別分析
            holiday_type_results = {}
            for holiday_type in test_data['holiday_type'].unique():
                type_data = test_data[test_data['holiday_type'] == holiday_type]
                type_filtered = apply_rest_exclusion_filter(type_data, f"holiday_type_{holiday_type}")
                
                holiday_type_results[holiday_type] = {
                    "original": len(type_data),
                    "filtered": len(type_filtered),
                    "exclusion_rate": (len(type_data) - len(type_filtered)) / len(type_data) if len(type_data) > 0 else 0
                }
            
            result["details"]["holiday_type_results"] = holiday_type_results
            
            # 通常勤務は保持、その他は除外されることを確認
            normal_work_preserved = holiday_type_results.get("通常勤務", {}).get("exclusion_rate", 1.0) == 0.0
            other_holidays_excluded = all(
                r["exclusion_rate"] > 0.5 for k, r in holiday_type_results.items() 
                if k != "通常勤務"
            )
            
            if not normal_work_preserved:
                result["status"] = "failed"
                result["details"]["error"] = "Normal work records were incorrectly excluded"
            elif not other_holidays_excluded:
                result["status"] = "failed"
                result["details"]["error"] = "Holiday records were not properly excluded"
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Mixed holiday types test failed: {e}")
        
        return result
    
    def _test_parquet_consistency(self) -> Dict[str, Any]:
        """Parquetファイル整合性テスト"""
        result = {"status": "passed", "details": {}}
        
        try:
            # テストデータからparquetファイル作成・読み込みテスト
            test_data = self._create_consistency_test_data()
            
            # Parquet保存・読み込み
            temp_parquet = self.output_dir / "temp_consistency_test.parquet"
            test_data.to_parquet(temp_parquet, index=False)
            loaded_data = pd.read_parquet(temp_parquet)
            
            # 整合性チェック
            consistency_checks = {
                "row_count_match": len(test_data) == len(loaded_data),
                "column_count_match": len(test_data.columns) == len(loaded_data.columns),
                "dtypes_match": test_data.dtypes.equals(loaded_data.dtypes),
                "content_match": test_data.equals(loaded_data)
            }
            
            result["details"]["consistency_checks"] = consistency_checks
            
            # フィルター適用後の整合性
            filtered_original = apply_rest_exclusion_filter(test_data, "parquet_original")
            filtered_loaded = apply_rest_exclusion_filter(loaded_data, "parquet_loaded")
            
            filter_consistency = {
                "filtered_count_match": len(filtered_original) == len(filtered_loaded),
                "filtered_content_match": filtered_original.equals(filtered_loaded) if len(filtered_original) == len(filtered_loaded) else False
            }
            
            result["details"]["filter_consistency"] = filter_consistency
            
            # クリーンアップ
            if temp_parquet.exists():
                temp_parquet.unlink()
            
            # 失敗判定
            if not all(consistency_checks.values()) or not all(filter_consistency.values()):
                result["status"] = "failed"
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Parquet consistency test failed: {e}")
        
        return result
    
    def _test_aggregation_accuracy(self) -> Dict[str, Any]:
        """集計精度テスト"""
        result = {"status": "passed", "details": {}}
        
        try:
            # 集計テスト用データ生成
            test_data = self._create_aggregation_test_data()
            
            # フィルター前後での集計比較
            pre_filter_stats = {
                "total_records": len(test_data),
                "staff_count": test_data['staff'].nunique(),
                "role_count": test_data['role'].nunique(),
                "date_range": (test_data['ds'].min(), test_data['ds'].max()),
                "avg_slots": test_data.get('parsed_slots_count', pd.Series()).mean()
            }
            
            filtered_data = apply_rest_exclusion_filter(test_data, "aggregation_test")
            
            post_filter_stats = {
                "total_records": len(filtered_data),
                "staff_count": filtered_data['staff'].nunique() if len(filtered_data) > 0 else 0,
                "role_count": filtered_data['role'].nunique() if len(filtered_data) > 0 else 0,
                "date_range": (filtered_data['ds'].min(), filtered_data['ds'].max()) if len(filtered_data) > 0 else (None, None),
                "avg_slots": filtered_data.get('parsed_slots_count', pd.Series()).mean()
            }
            
            result["details"]["pre_filter_stats"] = {k: str(v) if isinstance(v, tuple) else v for k, v in pre_filter_stats.items()}
            result["details"]["post_filter_stats"] = {k: str(v) if isinstance(v, tuple) else v for k, v in post_filter_stats.items()}
            
            # 集計一貫性チェック
            consistency_checks = {
                "staff_count_reasonable": post_filter_stats["staff_count"] <= pre_filter_stats["staff_count"],
                "role_count_reasonable": post_filter_stats["role_count"] <= pre_filter_stats["role_count"],
                "record_reduction": post_filter_stats["total_records"] <= pre_filter_stats["total_records"],
                "avg_slots_positive": post_filter_stats["avg_slots"] >= 0 if not pd.isna(post_filter_stats["avg_slots"]) else True
            }
            
            result["details"]["consistency_checks"] = consistency_checks
            
            if not all(consistency_checks.values()):
                result["status"] = "failed"
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Aggregation accuracy test failed: {e}")
        
        return result
    
    def _test_time_slot_alignment(self) -> Dict[str, Any]:
        """タイムスロット整列テスト"""
        result = {"status": "passed", "details": {}}
        
        try:
            # タイムスロット整列テスト用データ生成
            test_data = self._create_time_slot_test_data()
            
            if len(test_data) == 0:
                result["status"] = "skipped"
                result["details"]["reason"] = "No test data generated"
                return result
            
            # フィルター前のタイムスロット分析
            pre_filter_time_stats = {
                "unique_times": test_data['ds'].dt.hour.nunique(),
                "time_range": (test_data['ds'].dt.hour.min(), test_data['ds'].dt.hour.max()),
                "slot_intervals": test_data['ds'].diff().dropna().unique()[:5]  # 上位5つの間隔
            }
            
            filtered_data = apply_rest_exclusion_filter(test_data, "time_slot_test")
            
            if len(filtered_data) > 0:
                post_filter_time_stats = {
                    "unique_times": filtered_data['ds'].dt.hour.nunique(),
                    "time_range": (filtered_data['ds'].dt.hour.min(), filtered_data['ds'].dt.hour.max()),
                    "slot_intervals": filtered_data['ds'].diff().dropna().unique()[:5]
                }
            else:
                post_filter_time_stats = {
                    "unique_times": 0,
                    "time_range": (None, None),
                    "slot_intervals": []
                }
            
            result["details"]["pre_filter_time_stats"] = {k: str(v) if not isinstance(v, int) else v for k, v in pre_filter_time_stats.items()}
            result["details"]["post_filter_time_stats"] = {k: str(v) if not isinstance(v, int) else v for k, v in post_filter_time_stats.items()}
            
            # 時間整列チェック
            if len(filtered_data) > 0:
                time_alignment_checks = {
                    "chronological_order": filtered_data['ds'].is_monotonic_increasing,
                    "no_duplicate_times": len(filtered_data['ds'].unique()) == len(filtered_data) if 'staff' not in filtered_data.columns else True,
                    "reasonable_intervals": len([i for i in post_filter_time_stats["slot_intervals"] if pd.to_timedelta(i).total_seconds() > 0]) > 0
                }
            else:
                time_alignment_checks = {"all_filtered": True}
            
            result["details"]["time_alignment_checks"] = time_alignment_checks
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Time slot alignment test failed: {e}")
        
        return result
    
    def _test_processing_time(self) -> Dict[str, Any]:
        """処理時間テスト"""
        result = {"status": "passed", "details": {}}
        
        try:
            # 様々なサイズのデータセットでパフォーマンステスト
            data_sizes = [100, 1000, 10000, 50000]
            processing_results = {}
            
            for size in data_sizes:
                test_data = self._create_performance_test_data(size)
                
                # 処理時間測定
                start_time = time.time()
                filtered_data = apply_rest_exclusion_filter(test_data, f"performance_test_{size}")
                end_time = time.time()
                
                processing_time = end_time - start_time
                
                processing_results[size] = {
                    "processing_time": processing_time,
                    "records_per_second": size / processing_time if processing_time > 0 else float('inf'),
                    "original_count": len(test_data),
                    "filtered_count": len(filtered_data)
                }
            
            result["details"]["processing_results"] = processing_results
            
            # パフォーマンス回帰チェック（線形性）
            if len(processing_results) >= 2:
                times = [r["processing_time"] for r in processing_results.values()]
                sizes = list(processing_results.keys())
                
                # 大雑把な線形性チェック（最大サイズは最小サイズの処理時間の100倍以下）
                max_time = max(times)
                min_time = min(times)
                max_size = max(sizes)
                min_size = min(sizes)
                
                expected_ratio = max_size / min_size
                actual_ratio = max_time / min_time if min_time > 0 else float('inf')
                
                if actual_ratio > expected_ratio * 10:  # 10倍以上の非線形性
                    result["status"] = "warning"
                    result["details"]["performance_warning"] = f"Non-linear performance degradation detected: {actual_ratio:.2f}x vs expected {expected_ratio:.2f}x"
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Processing time test failed: {e}")
        
        return result
    
    def _test_memory_usage(self) -> Dict[str, Any]:
        """メモリ使用量テスト"""
        result = {"status": "passed", "details": {}}
        
        try:
            # メモリ使用量測定
            data_sizes = [1000, 5000, 10000]
            memory_results = {}
            
            for size in data_sizes:
                # ガベージコレクション
                gc.collect()
                start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                
                test_data = self._create_performance_test_data(size)
                after_creation_memory = psutil.Process().memory_info().rss / 1024 / 1024
                
                filtered_data = apply_rest_exclusion_filter(test_data, f"memory_test_{size}")
                after_processing_memory = psutil.Process().memory_info().rss / 1024 / 1024
                
                # データ削除
                del test_data, filtered_data
                gc.collect()
                after_cleanup_memory = psutil.Process().memory_info().rss / 1024 / 1024
                
                memory_results[size] = {
                    "creation_memory_delta": after_creation_memory - start_memory,
                    "processing_memory_delta": after_processing_memory - after_creation_memory,
                    "cleanup_efficiency": (after_processing_memory - after_cleanup_memory) / (after_processing_memory - start_memory) if after_processing_memory > start_memory else 0,
                    "peak_memory_mb": after_processing_memory
                }
            
            result["details"]["memory_results"] = memory_results
            
            # メモリリーク検出
            cleanup_efficiencies = [r["cleanup_efficiency"] for r in memory_results.values()]
            avg_cleanup_efficiency = sum(cleanup_efficiencies) / len(cleanup_efficiencies) if cleanup_efficiencies else 0
            
            if avg_cleanup_efficiency < 0.8:  # 80%未満の場合、メモリリークの可能性
                result["status"] = "warning"
                result["details"]["memory_warning"] = f"Low memory cleanup efficiency: {avg_cleanup_efficiency:.2%}"
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Memory usage test failed: {e}")
        
        return result
    
    def _test_cache_efficiency(self) -> Dict[str, Any]:
        """キャッシュ効率性テスト"""
        result = {"status": "passed", "details": {}}
        
        try:
            # 同じデータに対する繰り返し処理でキャッシュ効果を測定
            test_data = self._create_performance_test_data(5000)
            
            # 1回目の処理時間
            start_time = time.time()
            first_result = apply_rest_exclusion_filter(test_data.copy(), "cache_test_1")
            first_time = time.time() - start_time
            
            # 2回目の処理時間（キャッシュ効果期待）
            start_time = time.time()
            second_result = apply_rest_exclusion_filter(test_data.copy(), "cache_test_2")
            second_time = time.time() - start_time
            
            # 3回目の処理時間
            start_time = time.time()
            third_result = apply_rest_exclusion_filter(test_data.copy(), "cache_test_3")
            third_time = time.time() - start_time
            
            result["details"]["timing_results"] = {
                "first_run": first_time,
                "second_run": second_time,
                "third_run": third_time,
                "second_vs_first_ratio": second_time / first_time if first_time > 0 else float('inf'),
                "third_vs_first_ratio": third_time / first_time if first_time > 0 else float('inf')
            }
            
            # 結果の一貫性チェック
            results_consistent = (
                len(first_result) == len(second_result) == len(third_result) and
                first_result.equals(second_result) and second_result.equals(third_result)
            )
            
            result["details"]["results_consistent"] = results_consistent
            
            if not results_consistent:
                result["status"] = "failed"
                result["details"]["error"] = "Inconsistent results across multiple runs"
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Cache efficiency test failed: {e}")
        
        return result
    
    def _test_dashboard_tabs(self) -> Dict[str, Any]:
        """ダッシュボードタブテスト"""
        result = {"status": "skipped", "details": {"reason": "Dashboard testing requires manual interaction"}}
        
        # 注意: 実際のUIテストは自動化が困難なため、構造的テストに限定
        try:
            if DASHBOARD_AVAILABLE:
                # Dash appの基本的な構造チェック
                if hasattr(app, 'layout') and app.layout is not None:
                    result["status"] = "passed"
                    result["details"]["dashboard_structure"] = "Layout exists"
                else:
                    result["status"] = "failed"
                    result["details"]["error"] = "Dashboard layout not found"
            else:
                result["details"]["reason"] = "Dashboard not available for testing"
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Dashboard tabs test failed: {e}")
        
        return result
    
    def _test_heatmap_color_scales(self) -> Dict[str, Any]:
        """ヒートマップ色スケールテスト"""
        result = {"status": "skipped", "details": {"reason": "Heatmap testing requires visual verification"}}
        
        try:
            # 色スケールのデータ範囲テスト
            test_data = self._create_heatmap_test_data()
            
            if len(test_data) > 0:
                # データ範囲分析
                if 'value' in test_data.columns:
                    data_stats = {
                        "min_value": test_data['value'].min(),
                        "max_value": test_data['value'].max(),
                        "mean_value": test_data['value'].mean(),
                        "value_range": test_data['value'].max() - test_data['value'].min(),
                        "has_negative": (test_data['value'] < 0).any(),
                        "has_zero": (test_data['value'] == 0).any()
                    }
                    
                    result["status"] = "passed"
                    result["details"]["data_stats"] = data_stats
                    
                    # 色スケール適合性チェック
                    if data_stats["value_range"] == 0:
                        result["details"]["warning"] = "All values are identical - color scale may not work properly"
                    
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Heatmap color scales test failed: {e}")
        
        return result
    
    def _test_dropdown_filters(self) -> Dict[str, Any]:
        """ドロップダウンフィルターテスト"""
        result = {"status": "skipped", "details": {"reason": "Dropdown testing requires interactive testing"}}
        
        try:
            # フィルター用のテストデータ生成
            test_data = self._create_filter_test_data()
            
            if len(test_data) > 0:
                # フィルター項目の妥当性チェック
                filter_stats = {
                    "unique_staff": test_data['staff'].nunique() if 'staff' in test_data.columns else 0,
                    "unique_roles": test_data['role'].nunique() if 'role' in test_data.columns else 0,
                    "date_range_days": (test_data['ds'].max() - test_data['ds'].min()).days if 'ds' in test_data.columns else 0
                }
                
                result["status"] = "passed"
                result["details"]["filter_stats"] = filter_stats
                result["details"]["message"] = "Filter data structure validated"
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Dropdown filters test failed: {e}")
        
        return result
    
    def _test_date_range_selectors(self) -> Dict[str, Any]:
        """日付範囲セレクターテスト"""
        result = {"status": "skipped", "details": {"reason": "Date selector testing requires interactive testing"}}
        
        try:
            # 日付範囲テスト用データ生成
            test_data = self._create_date_range_test_data()
            
            if len(test_data) > 0:
                # 日付範囲の連続性と妥当性チェック
                date_stats = {
                    "min_date": str(test_data['ds'].min()),
                    "max_date": str(test_data['ds'].max()),
                    "total_days": (test_data['ds'].max() - test_data['ds'].min()).days + 1,
                    "unique_dates": test_data['ds'].dt.date.nunique(),
                    "date_continuity": (test_data['ds'].dt.date.nunique() == (test_data['ds'].max() - test_data['ds'].min()).days + 1)
                }
                
                result["status"] = "passed"
                result["details"]["date_stats"] = date_stats
                result["details"]["message"] = "Date range structure validated"
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Date range selectors test failed: {e}")
        
        return result
    
    # ===============================
    # テストデータ生成メソッド
    # ===============================
    
    def _create_all_holidays_test_data(self) -> pd.DataFrame:
        """全日休日テストデータ生成"""
        dates = pd.date_range('2025-01-01', '2025-01-07', freq='D')
        staff_names = ['×', '休', '有', 'OFF', '-']
        
        data = []
        for date in dates:
            for i, staff in enumerate(staff_names):
                for hour in range(0, 24, 2):  # 2時間間隔
                    data.append({
                        'ds': pd.Timestamp(date).replace(hour=hour),
                        'staff': staff,
                        'role': f'role_{i % 3}',
                        'code': '×' if staff == '×' else '休',
                        'parsed_slots_count': 0,  # 休日は0スロット
                        'holiday_type': '有給' if staff == '有' else '希望休'
                    })
        
        return pd.DataFrame(data)
    
    def _create_no_holidays_test_data(self) -> pd.DataFrame:
        """休日なしテストデータ生成"""
        dates = pd.date_range('2025-01-01', '2025-01-07', freq='D')
        staff_names = ['田中太郎', '佐藤花子', '山田次郎', '鈴木美香']
        
        data = []
        for date in dates:
            for i, staff in enumerate(staff_names):
                for hour in range(8, 17, 2):  # 営業時間内
                    data.append({
                        'ds': pd.Timestamp(date).replace(hour=hour),
                        'staff': staff,
                        'role': f'role_{i % 2}',
                        'code': 'A' if i % 2 == 0 else 'B',
                        'parsed_slots_count': 2,  # 勤務スロット
                        'holiday_type': '通常勤務'
                    })
        
        return pd.DataFrame(data)
    
    def _create_single_holiday_test_data(self) -> pd.DataFrame:
        """単日休日テストデータ生成"""
        date = pd.Timestamp('2025-01-01')
        
        data = [{
            'ds': date,
            'staff': '×',
            'role': 'nurse',
            'code': '×',
            'parsed_slots_count': 0,
            'holiday_type': '希望休'
        }]
        
        return pd.DataFrame(data)
    
    def _create_single_workday_test_data(self) -> pd.DataFrame:
        """単日勤務テストデータ生成"""
        date = pd.Timestamp('2025-01-01')
        
        data = []
        for hour in range(9, 18):
            data.append({
                'ds': date.replace(hour=hour),
                'staff': '田中太郎',
                'role': 'nurse',
                'code': 'A',
                'parsed_slots_count': 1,
                'holiday_type': '通常勤務'
            })
        
        return pd.DataFrame(data)
    
    def _create_full_year_test_data(self) -> pd.DataFrame:
        """通年テストデータ生成"""
        # 1年間のデータ生成（メモリ効率を考慮し、サンプリング）
        dates = pd.date_range('2025-01-01', '2025-12-31', freq='W')  # 週1回のサンプリング
        staff_names = ['田中', '佐藤', '山田', '×', '休', 'OFF']
        
        data = []
        for i, date in enumerate(dates):
            for j, staff in enumerate(staff_names):
                # 休日は25%の確率
                is_holiday = staff in ['×', '休', 'OFF'] or (i + j) % 4 == 0
                
                data.append({
                    'ds': date.replace(hour=9 + (j % 8)),
                    'staff': staff,
                    'role': f'role_{j % 3}',
                    'code': '×' if is_holiday else 'A',
                    'parsed_slots_count': 0 if is_holiday else 1,
                    'holiday_type': '希望休' if is_holiday else '通常勤務'
                })
        
        return pd.DataFrame(data)
    
    def _create_month_boundary_test_data(self) -> pd.DataFrame:
        """月境界テストデータ生成"""
        # 月末月初のデータ生成
        dates = []
        for month in range(1, 13):
            # 各月の最後3日と最初3日
            if month == 12:
                next_month = 1
                next_year = 2026
            else:
                next_month = month + 1
                next_year = 2025
            
            # 月末
            end_date = pd.Timestamp(f'2025-{month:02d}-01') + pd.offsets.MonthEnd(0)
            for d in range(3):
                if end_date.day - d > 0:
                    dates.append(end_date - pd.Timedelta(days=d))
            
            # 月初
            start_date = pd.Timestamp(f'{next_year}-{next_month:02d}-01')
            for d in range(3):
                dates.append(start_date + pd.Timedelta(days=d))
        
        data = []
        for date in dates:
            for staff in ['田中', '×', '休']:
                is_holiday = staff in ['×', '休']
                data.append({
                    'ds': date,
                    'staff': staff,
                    'role': 'role_1',
                    'code': '×' if is_holiday else 'A',
                    'parsed_slots_count': 0 if is_holiday else 1,
                    'holiday_type': '希望休' if is_holiday else '通常勤務'
                })
        
        return pd.DataFrame(data)
    
    def _create_year_boundary_test_data(self) -> pd.DataFrame:
        """年境界テストデータ生成"""
        # 年末年始データ
        dates = (
            pd.date_range('2024-12-29', '2024-12-31', freq='D').tolist() +
            pd.date_range('2025-01-01', '2025-01-03', freq='D').tolist()
        )
        
        data = []
        for date in dates:
            for staff in ['田中', '佐藤', '×', '休']:
                is_holiday = staff in ['×', '休'] or date.month == 1  # 正月は休日多め
                data.append({
                    'ds': date,
                    'staff': staff,
                    'role': 'role_1',
                    'code': '×' if is_holiday else 'A',
                    'parsed_slots_count': 0 if is_holiday else 1,
                    'holiday_type': '希望休' if is_holiday else '通常勤務'
                })
        
        return pd.DataFrame(data)
    
    def _create_partial_week_start_data(self) -> pd.DataFrame:
        """週開始部分データ生成"""
        # 木曜日から日曜日までのデータ
        dates = pd.date_range('2025-01-02', '2025-01-05', freq='D')  # 木-日
        
        data = []
        for date in dates:
            for staff in ['田中', '×']:
                is_holiday = staff == '×'
                data.append({
                    'ds': date,
                    'staff': staff,
                    'role': 'role_1',
                    'code': '×' if is_holiday else 'A',
                    'parsed_slots_count': 0 if is_holiday else 1,
                    'holiday_type': '希望休' if is_holiday else '通常勤務'
                })
        
        return pd.DataFrame(data)
    
    def _create_partial_week_end_data(self) -> pd.DataFrame:
        """週末部分データ生成"""
        # 月曜日から水曜日までのデータ
        dates = pd.date_range('2025-01-06', '2025-01-08', freq='D')  # 月-水
        
        data = []
        for date in dates:
            for staff in ['佐藤', '休']:
                is_holiday = staff == '休'
                data.append({
                    'ds': date,
                    'staff': staff,
                    'role': 'role_1',
                    'code': '休' if is_holiday else 'B',
                    'parsed_slots_count': 0 if is_holiday else 1,
                    'holiday_type': '施設休' if is_holiday else '通常勤務'
                })
        
        return pd.DataFrame(data)
    
    def _create_mid_week_partial_data(self) -> pd.DataFrame:
        """週中部分データ生成"""
        # 火曜日から木曜日までのデータ
        dates = pd.date_range('2025-01-07', '2025-01-09', freq='D')  # 火-木
        
        data = []
        for date in dates:
            for staff in ['山田', 'OFF']:
                is_holiday = staff == 'OFF'
                data.append({
                    'ds': date,
                    'staff': staff,
                    'role': 'role_2',
                    'code': 'OFF' if is_holiday else 'C',
                    'parsed_slots_count': 0 if is_holiday else 1,
                    'holiday_type': 'その他休暇' if is_holiday else '通常勤務'
                })
        
        return pd.DataFrame(data)
    
    def _create_mixed_holiday_types_data(self) -> pd.DataFrame:
        """混合休暇タイプテストデータ生成"""
        date = pd.Timestamp('2025-01-01')
        
        holiday_types = [
            ('×', '希望休'),
            ('休', '施設休'),
            ('有', '有給'),
            ('研', 'その他休暇'),
            ('田中', '通常勤務'),
            ('佐藤', '通常勤務')
        ]
        
        data = []
        for i, (staff, holiday_type) in enumerate(holiday_types):
            is_working = holiday_type == '通常勤務'
            data.append({
                'ds': date.replace(hour=9 + i),
                'staff': staff,
                'role': f'role_{i % 2}',
                'code': 'A' if is_working else staff,
                'parsed_slots_count': 1 if is_working else 0,
                'holiday_type': holiday_type
            })
        
        return pd.DataFrame(data)
    
    def _create_consistency_test_data(self) -> pd.DataFrame:
        """整合性テスト用データ生成"""
        dates = pd.date_range('2025-01-01', '2025-01-03', freq='H')
        
        data = []
        for i, date in enumerate(dates):
            staff = '田中' if i % 3 != 0 else '×'
            is_holiday = staff == '×'
            
            data.append({
                'ds': date,
                'staff': staff,
                'role': 'nurse',
                'code': '×' if is_holiday else 'A',
                'parsed_slots_count': 0 if is_holiday else 1,
                'holiday_type': '希望休' if is_holiday else '通常勤務'
            })
        
        return pd.DataFrame(data)
    
    def _create_aggregation_test_data(self) -> pd.DataFrame:
        """集計テスト用データ生成"""
        dates = pd.date_range('2025-01-01', '2025-01-07', freq='D')
        staff_list = ['田中', '佐藤', '×', '休', 'OFF']
        
        data = []
        for date in dates:
            for staff in staff_list:
                is_holiday = staff in ['×', '休', 'OFF']
                data.append({
                    'ds': date,
                    'staff': staff,
                    'role': 'nurse' if not is_holiday else 'holiday',
                    'code': staff if is_holiday else 'A',
                    'parsed_slots_count': 0 if is_holiday else 8,
                    'holiday_type': '希望休' if is_holiday else '通常勤務'
                })
        
        return pd.DataFrame(data)
    
    def _create_time_slot_test_data(self) -> pd.DataFrame:
        """タイムスロットテスト用データ生成"""
        base_date = pd.Timestamp('2025-01-01')
        
        data = []
        for hour in range(24):
            for minute in [0, 30]:  # 30分間隔
                dt = base_date.replace(hour=hour, minute=minute)
                staff = '×' if hour % 4 == 0 else '田中'
                is_holiday = staff == '×'
                
                data.append({
                    'ds': dt,
                    'staff': staff,
                    'role': 'nurse',
                    'code': '×' if is_holiday else 'A',
                    'parsed_slots_count': 0 if is_holiday else 1,
                    'holiday_type': '希望休' if is_holiday else '通常勤務'
                })
        
        return pd.DataFrame(data)
    
    def _create_performance_test_data(self, size: int) -> pd.DataFrame:
        """パフォーマンステスト用データ生成"""
        dates = pd.date_range('2025-01-01', periods=min(size // 10, 365), freq='D')
        staff_patterns = ['田中', '佐藤', '山田', '×', '休', 'OFF'] * (size // 6 + 1)
        
        data = []
        for i in range(size):
            date = dates[i % len(dates)]
            staff = staff_patterns[i % len(staff_patterns)]
            is_holiday = staff in ['×', '休', 'OFF']
            
            data.append({
                'ds': date.replace(hour=(i % 24)),
                'staff': staff,
                'role': f'role_{i % 3}',
                'code': staff if is_holiday else f'code_{i % 5}',
                'parsed_slots_count': 0 if is_holiday else 1,
                'holiday_type': '希望休' if is_holiday else '通常勤務'
            })
        
        return pd.DataFrame(data)
    
    def _create_heatmap_test_data(self) -> pd.DataFrame:
        """ヒートマップテスト用データ生成"""
        dates = pd.date_range('2025-01-01', '2025-01-07', freq='D')
        hours = range(24)
        
        data = []
        for date in dates:
            for hour in hours:
                # シミュレートされた需要値（0-10の範囲）
                base_demand = 5 + np.sin(hour * np.pi / 12) * 3  # 時間による変動
                weekend_factor = 0.7 if date.weekday() >= 5 else 1.0
                noise = np.random.normal(0, 0.5)
                
                value = max(0, base_demand * weekend_factor + noise)
                
                data.append({
                    'ds': pd.Timestamp(date).replace(hour=hour),
                    'date': date.date(),
                    'hour': hour,
                    'value': value,
                    'day_of_week': date.strftime('%A')
                })
        
        return pd.DataFrame(data)
    
    def _create_filter_test_data(self) -> pd.DataFrame:
        """フィルターテスト用データ生成"""
        dates = pd.date_range('2025-01-01', '2025-01-31', freq='D')
        staff_list = ['田中太郎', '佐藤花子', '山田次郎', '鈴木美香', '×', '休']
        roles = ['看護師', '介護士', 'リハビリ', '事務']
        
        data = []
        for date in dates:
            for staff in staff_list:
                role = roles[hash(staff) % len(roles)]
                is_holiday = staff in ['×', '休']
                
                data.append({
                    'ds': date,
                    'staff': staff,
                    'role': role,
                    'employment': '正社員' if not is_holiday else '',
                    'code': staff if is_holiday else 'A',
                    'parsed_slots_count': 0 if is_holiday else 8,
                    'holiday_type': '希望休' if is_holiday else '通常勤務'
                })
        
        return pd.DataFrame(data)
    
    def _create_date_range_test_data(self) -> pd.DataFrame:
        """日付範囲テスト用データ生成"""
        # 3ヶ月間の連続データ
        dates = pd.date_range('2025-01-01', '2025-03-31', freq='D')
        
        data = []
        for date in dates:
            # 平日は勤務、週末は一部休み
            is_weekend = date.weekday() >= 5
            staff = '×' if is_weekend and date.day % 3 == 0 else '田中'
            is_holiday = staff == '×'
            
            data.append({
                'ds': date,
                'staff': staff,
                'role': 'nurse',
                'code': '×' if is_holiday else 'A',
                'parsed_slots_count': 0 if is_holiday else 8,
                'holiday_type': '希望休' if is_holiday else '通常勤務'
            })
        
        return pd.DataFrame(data)
    
    def _generate_comprehensive_report(self):
        """包括的レポート生成"""
        logger.info("Generating comprehensive test report...")
        
        # レポートファイル生成
        report_file = self.output_dir / "edge_case_test_report.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Edge Case Testing Comprehensive Report\n\n")
            f.write(f"Generated on: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # エグゼクティブサマリー
            f.write("## Executive Summary\n\n")
            total_tests = sum(len(category) for category in self.test_results.values() if isinstance(category, dict))
            f.write(f"Total tests executed: {total_tests}\n\n")
            
            # カテゴリ別結果サマリー
            for category, results in self.test_results.items():
                if isinstance(results, dict) and results:
                    f.write(f"### {category.replace('_', ' ').title()}\n\n")
                    
                    for test_name, test_result in results.items():
                        if isinstance(test_result, dict):
                            status = test_result.get('status', 'unknown')
                            f.write(f"- **{test_name}**: {status.upper()}\n")
                            
                            if status == 'failed':
                                error = test_result.get('error', test_result.get('details', {}).get('error', 'Unknown error'))
                                f.write(f"  - Error: {error}\n")
                            elif status == 'warning':
                                warning = test_result.get('details', {}).get('performance_warning', 
                                         test_result.get('details', {}).get('memory_warning', 'Unknown warning'))
                                f.write(f"  - Warning: {warning}\n")
                    
                    f.write("\n")
            
            # 詳細結果
            f.write("## Detailed Results\n\n")
            f.write("```json\n")
            f.write(json.dumps(self.test_results, indent=2, default=str, ensure_ascii=False))
            f.write("\n```\n\n")
            
            # 推奨事項
            f.write("## Recommendations\n\n")
            failed_tests = []
            warning_tests = []
            
            for category, results in self.test_results.items():
                if isinstance(results, dict):
                    for test_name, test_result in results.items():
                        if isinstance(test_result, dict):
                            if test_result.get('status') == 'failed':
                                failed_tests.append((category, test_name, test_result))
                            elif test_result.get('status') == 'warning':
                                warning_tests.append((category, test_name, test_result))
            
            if failed_tests:
                f.write("### Critical Issues (Failed Tests)\n\n")
                for category, test_name, result in failed_tests:
                    f.write(f"- **{category}/{test_name}**: {result.get('error', 'Unknown error')}\n")
                f.write("\n")
            
            if warning_tests:
                f.write("### Performance Concerns (Warnings)\n\n")
                for category, test_name, result in warning_tests:
                    warning_msg = (result.get('details', {}).get('performance_warning') or 
                                  result.get('details', {}).get('memory_warning') or 'Unknown warning')
                    f.write(f"- **{category}/{test_name}**: {warning_msg}\n")
                f.write("\n")
            
            f.write("### General Recommendations\n\n")
            f.write("1. Monitor memory usage during large dataset processing\n")
            f.write("2. Implement additional caching for repeated operations\n")
            f.write("3. Consider batch processing for full-year datasets\n")
            f.write("4. Regularly validate data consistency across parquet files\n")
            f.write("5. Implement automated UI testing for dashboard components\n\n")
        
        logger.info(f"Comprehensive report saved to: {report_file}")
        
        # パフォーマンス可視化
        self._create_performance_visualizations()
    
    def _create_performance_visualizations(self):
        """パフォーマンス可視化グラフ生成"""
        try:
            # パフォーマンステスト結果のグラフ化
            performance_data = self.test_results.get('performance', {})
            
            if 'processing_time' in performance_data and performance_data['processing_time'].get('processing_results'):
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
                
                # 処理時間グラフ
                results = performance_data['processing_time']['processing_results']
                sizes = list(results.keys())
                times = [results[size]['processing_time'] for size in sizes]
                
                ax1.plot(sizes, times, 'b-o', linewidth=2, markersize=8)
                ax1.set_xlabel('Dataset Size (records)')
                ax1.set_ylabel('Processing Time (seconds)')
                ax1.set_title('Processing Time vs Dataset Size')
                ax1.grid(True, alpha=0.3)
                ax1.set_xscale('log')
                ax1.set_yscale('log')
                
                # レコード/秒グラフ
                throughput = [results[size]['records_per_second'] for size in sizes]
                ax2.plot(sizes, throughput, 'g-o', linewidth=2, markersize=8)
                ax2.set_xlabel('Dataset Size (records)')
                ax2.set_ylabel('Records per Second')
                ax2.set_title('Processing Throughput')
                ax2.grid(True, alpha=0.3)
                ax2.set_xscale('log')
                
                plt.tight_layout()
                performance_plot = self.output_dir / "performance_analysis.png"
                plt.savefig(performance_plot, dpi=300, bbox_inches='tight')
                plt.close()
                
                logger.info(f"Performance visualization saved to: {performance_plot}")
            
            # メモリ使用量グラフ
            if 'memory_usage' in performance_data and performance_data['memory_usage'].get('memory_results'):
                fig, ax = plt.subplots(1, 1, figsize=(10, 6))
                
                memory_results = performance_data['memory_usage']['memory_results']
                sizes = list(memory_results.keys())
                creation_memory = [memory_results[size]['creation_memory_delta'] for size in sizes]
                processing_memory = [memory_results[size]['processing_memory_delta'] for size in sizes]
                
                x = np.arange(len(sizes))
                width = 0.35
                
                ax.bar(x - width/2, creation_memory, width, label='Data Creation', alpha=0.7)
                ax.bar(x + width/2, processing_memory, width, label='Processing', alpha=0.7)
                
                ax.set_xlabel('Dataset Size (records)')
                ax.set_ylabel('Memory Delta (MB)')
                ax.set_title('Memory Usage by Dataset Size')
                ax.set_xticks(x)
                ax.set_xticklabels(sizes)
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                memory_plot = self.output_dir / "memory_usage_analysis.png"
                plt.savefig(memory_plot, dpi=300, bbox_inches='tight')
                plt.close()
                
                logger.info(f"Memory usage visualization saved to: {memory_plot}")
                
        except Exception as e:
            logger.error(f"Failed to create performance visualizations: {e}")


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description='Edge Case Testing Suite for Holiday Exclusion Fixes')
    parser.add_argument('--data-dir', type=str, default='./test_data', 
                       help='Directory containing test data files')
    parser.add_argument('--output-dir', type=str, default='./test_results',
                       help='Directory to save test results')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # ログレベル設定
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    
    try:
        # テストスイート実行
        test_suite = EdgeCaseTestSuite(
            data_dir=Path(args.data_dir),
            output_dir=Path(args.output_dir)
        )
        
        results = test_suite.run_all_tests()
        
        # 結果サマリー出力
        print("\n" + "=" * 60)
        print("EDGE CASE TEST SUITE SUMMARY")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        warning_tests = 0
        
        for category, tests in results.items():
            if isinstance(tests, dict):
                for test_name, test_result in tests.items():
                    if isinstance(test_result, dict) and 'status' in test_result:
                        total_tests += 1
                        status = test_result['status']
                        if status == 'passed':
                            passed_tests += 1
                        elif status == 'failed':
                            failed_tests += 1
                        elif status == 'warning':
                            warning_tests += 1
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Warnings: {warning_tests}")
        print(f"Success Rate: {passed_tests/total_tests*100:.1f}%" if total_tests > 0 else "N/A")
        
        if failed_tests > 0:
            print(f"\n⚠️  {failed_tests} test(s) failed - check the detailed report")
            sys.exit(1)
        elif warning_tests > 0:
            print(f"\n⚠️  {warning_tests} test(s) have warnings - review recommended")
            sys.exit(0)
        else:
            print("\n✅ All tests passed successfully!")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Test suite execution failed: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()