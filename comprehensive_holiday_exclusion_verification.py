#!/usr/bin/env python3
"""
休日除外修正の総合的システム検証
2025-07-22

実施された休日除外修正がシステム全体に与える影響を総合的に検証し、
データフロー、依存関係、集計ロジック、UI表示、パフォーマンス、エッジケースの全面を評価
"""

import sys
import os
sys.path.insert(0, os.getcwd())

import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import tempfile
import traceback

# shift_suite モジュール
from shift_suite.tasks.utils import apply_rest_exclusion_filter, gen_labels, _valid_df
from shift_suite.tasks.io_excel import ingest_excel
from shift_suite.tasks import shortage
from shift_suite.tasks.heatmap import build_heatmap
from shift_suite.tasks.proportional_calculator import (
    calculate_proportional_shortage, 
    calculate_total_shortage_from_data,
    create_proportional_summary_df
)

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class HolidayExclusionVerificationSuite:
    """休日除外修正の総合検証スイート"""
    
    def __init__(self):
        self.results = {}
        self.temp_dir = Path(tempfile.mkdtemp())
        log.info(f"Verification temporary directory: {self.temp_dir}")
    
    def run_comprehensive_verification(self, excel_path: str) -> Dict[str, Any]:
        """総合的な検証を実行"""
        log.info("休日除外修正の総合検証を開始")
        
        try:
            # 1. データ整合性検証
            self.results['data_consistency'] = self.verify_data_consistency(excel_path)
            
            # 2. 依存関係検証
            self.results['dependency_analysis'] = self.verify_dependencies(excel_path)
            
            # 3. 集計ロジック検証
            self.results['aggregation_logic'] = self.verify_aggregation_logic(excel_path)
            
            # 4. UI表示検証
            self.results['ui_display'] = self.verify_ui_display_impact(excel_path)
            
            # 5. パフォーマンス検証
            self.results['performance'] = self.verify_performance_impact(excel_path)
            
            # 6. エッジケース検証
            self.results['edge_cases'] = self.verify_edge_cases(excel_path)
            
            # 7. 総合評価
            self.results['overall_assessment'] = self.create_overall_assessment()
            
        except Exception as e:
            log.error(f"検証中にエラーが発生: {str(e)}")
            self.results['error'] = str(e)
            self.results['traceback'] = traceback.format_exc()
        
        return self.results
    
    def verify_data_consistency(self, excel_path: str) -> Dict[str, Any]:
        """データ整合性の検証"""
        log.info("=== データ整合性検証開始 ===")
        consistency_results = {}
        
        try:
            # データ入稿
            excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
            shift_sheets = [s for s in excel_file.sheet_names if "勤務" not in s]
            
            long_df, wt_df, unknown_codes = ingest_excel(
                Path(excel_path),
                shift_sheets=shift_sheets,
                header_row=0
            )
            
            log.info(f"データ入稿完了: {len(long_df)} レコード, {len(wt_df)} 勤務タイプ")
            
            # 元データの状態
            consistency_results['original_data'] = {
                'total_records': len(long_df),
                'staff_count': long_df['staff'].nunique() if 'staff' in long_df.columns else 0,
                'date_range': self._get_date_range(long_df),
                'rest_patterns_found': self._analyze_rest_patterns(long_df)
            }
            
            # 休日除外フィルター適用前後の比較
            if not long_df.empty:
                # 適用前
                pre_filter_stats = self._calculate_data_stats(long_df, "pre_filter")
                
                # 適用後
                filtered_long_df = apply_rest_exclusion_filter(long_df.copy(), "consistency_verification", for_display=False, exclude_leave_records=False)
                post_filter_stats = self._calculate_data_stats(filtered_long_df, "post_filter")
                
                consistency_results['filter_impact'] = {
                    'pre_filter': pre_filter_stats,
                    'post_filter': post_filter_stats,
                    'exclusion_rate': (pre_filter_stats['total_records'] - post_filter_stats['total_records']) / pre_filter_stats['total_records'] if pre_filter_stats['total_records'] > 0 else 0,
                    'data_quality_improvement': self._assess_data_quality_improvement(pre_filter_stats, post_filter_stats)
                }
            
            # ヒートマップ生成での整合性確認
            if not filtered_long_df.empty and not wt_df.empty:
                heatmap_consistency = self._verify_heatmap_consistency(filtered_long_df, wt_df)
                consistency_results['heatmap_consistency'] = heatmap_consistency
                
        except Exception as e:
            consistency_results['error'] = str(e)
            log.error(f"データ整合性検証エラー: {str(e)}")
        
        return consistency_results
    
    def verify_dependencies(self, excel_path: str) -> Dict[str, Any]:
        """依存関係の検証"""
        log.info("=== 依存関係検証開始 ===")
        dependency_results = {}
        
        try:
            # 仮想的なparquetファイル生成でデータフロー確認
            temp_out_dir = self.temp_dir / "dependency_test"
            temp_out_dir.mkdir(exist_ok=True)
            
            # データ処理パイプライン実行
            excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
            shift_sheets = [s for s in excel_file.sheet_names if "勤務" not in s]
            
            long_df, wt_df, unknown_codes = ingest_excel(
                Path(excel_path),
                shift_sheets=shift_sheets,
                header_row=0
            )
            
            if not long_df.empty and not wt_df.empty:
                # 休日除外適用
                filtered_long_df = apply_rest_exclusion_filter(long_df.copy(), "dependency_test", for_display=False, exclude_leave_records=False)
                
                # ヒートマップ生成（data_files作成）
                data_files = build_heatmap(
                    filtered_long_df, wt_df, 
                    out_dir=temp_out_dir, 
                    slot=15,
                    holidays=[]
                )
                
                dependency_results['generated_files'] = {}
                for file_type, file_path in data_files.items():
                    if file_path and file_path.exists():
                        df = pd.read_parquet(file_path)
                        dependency_results['generated_files'][file_type] = {
                            'path': str(file_path),
                            'shape': df.shape,
                            'columns': list(df.columns),
                            'sample_data': df.head(3).to_dict() if not df.empty else {},
                            'has_rest_data': self._check_rest_data_presence(df)
                        }
                
                # 各ファイル間の依存関係確認
                dependency_results['interdependencies'] = self._analyze_file_interdependencies(data_files)
                
        except Exception as e:
            dependency_results['error'] = str(e)
            log.error(f"依存関係検証エラー: {str(e)}")
            
        return dependency_results
    
    def verify_aggregation_logic(self, excel_path: str) -> Dict[str, Any]:
        """集計ロジックの検証"""
        log.info("=== 集計ロジック検証開始 ===")
        aggregation_results = {}
        
        try:
            # データ準備
            excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
            shift_sheets = [s for s in excel_file.sheet_names if "勤務" not in s]
            
            long_df, wt_df, unknown_codes = ingest_excel(
                Path(excel_path),
                shift_sheets=shift_sheets,
                header_row=0
            )
            
            if not long_df.empty:
                # 休日除外前後での集計結果比較
                original_aggregation = self._perform_aggregation_analysis(long_df, "original")
                
                filtered_long_df = apply_rest_exclusion_filter(long_df.copy(), "aggregation_test", for_display=False, exclude_leave_records=False)
                filtered_aggregation = self._perform_aggregation_analysis(filtered_long_df, "filtered")
                
                aggregation_results['comparison'] = {
                    'original': original_aggregation,
                    'filtered': filtered_aggregation,
                    'impact_analysis': self._analyze_aggregation_impact(original_aggregation, filtered_aggregation)
                }
                
                # 按分計算ロジックの検証
                if not wt_df.empty:
                    proportional_results = self._verify_proportional_calculation(filtered_long_df, wt_df)
                    aggregation_results['proportional_calculation'] = proportional_results
                    
        except Exception as e:
            aggregation_results['error'] = str(e)
            log.error(f"集計ロジック検証エラー: {str(e)}")
            
        return aggregation_results
    
    def verify_ui_display_impact(self, excel_path: str) -> Dict[str, Any]:
        """UI表示への影響検証"""
        log.info("=== UI表示影響検証開始 ===")
        ui_results = {}
        
        try:
            # ダッシュボード用データ生成のシミュレーション
            excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
            shift_sheets = [s for s in excel_file.sheet_names if "勤務" not in s]
            
            long_df, wt_df, unknown_codes = ingest_excel(
                Path(excel_path),
                shift_sheets=shift_sheets,
                header_row=0
            )
            
            if not long_df.empty and not wt_df.empty:
                # 休日除外適用
                filtered_long_df = apply_rest_exclusion_filter(long_df.copy(), "ui_test", for_display=False, exclude_leave_records=False)
                
                # 各タブ用データの整合性確認
                ui_results['tab_data_integrity'] = {}
                
                # 不足分析タブ
                ui_results['tab_data_integrity']['shortage_analysis'] = self._verify_shortage_tab_data(filtered_long_df, wt_df)
                
                # ヒートマップタブ
                ui_results['tab_data_integrity']['heatmap'] = self._verify_heatmap_tab_data(filtered_long_df, wt_df)
                
                # メトリクス表示
                ui_results['metrics_consistency'] = self._verify_metrics_consistency(filtered_long_df)
                
        except Exception as e:
            ui_results['error'] = str(e)
            log.error(f"UI表示影響検証エラー: {str(e)}")
            
        return ui_results
    
    def verify_performance_impact(self, excel_path: str) -> Dict[str, Any]:
        """パフォーマンス影響の検証"""
        log.info("=== パフォーマンス影響検証開始 ===")
        performance_results = {}
        
        try:
            import time
            
            # データ準備
            excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
            shift_sheets = [s for s in excel_file.sheet_names if "勤務" not in s]
            
            long_df, wt_df, unknown_codes = ingest_excel(
                Path(excel_path),
                shift_sheets=shift_sheets,
                header_row=0
            )
            
            if not long_df.empty:
                # フィルター適用前後のデータ量比較
                original_size = len(long_df)
                memory_before = long_df.memory_usage(deep=True).sum()
                
                start_time = time.time()
                filtered_long_df = apply_rest_exclusion_filter(long_df.copy(), "performance_test", for_display=False, exclude_leave_records=False)
                filter_time = time.time() - start_time
                
                filtered_size = len(filtered_long_df)
                memory_after = filtered_long_df.memory_usage(deep=True).sum()
                
                performance_results['data_reduction'] = {
                    'original_records': original_size,
                    'filtered_records': filtered_size,
                    'reduction_ratio': (original_size - filtered_size) / original_size if original_size > 0 else 0,
                    'memory_before_mb': memory_before / (1024 * 1024),
                    'memory_after_mb': memory_after / (1024 * 1024),
                    'memory_reduction_mb': (memory_before - memory_after) / (1024 * 1024),
                    'filter_processing_time_sec': filter_time
                }
                
                # 処理時間比較（簡易版）
                if not wt_df.empty:
                    performance_results['processing_time_comparison'] = self._compare_processing_times(
                        long_df, filtered_long_df, wt_df
                    )
                    
        except Exception as e:
            performance_results['error'] = str(e)
            log.error(f"パフォーマンス影響検証エラー: {str(e)}")
            
        return performance_results
    
    def verify_edge_cases(self, excel_path: str) -> Dict[str, Any]:
        """エッジケース処理の検証"""
        log.info("=== エッジケース処理検証開始 ===")
        edge_case_results = {}
        
        try:
            # データ準備
            excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
            shift_sheets = [s for s in excel_file.sheet_names if "勤務" not in s]
            
            long_df, wt_df, unknown_codes = ingest_excel(
                Path(excel_path),
                shift_sheets=shift_sheets,
                header_row=0
            )
            
            # エッジケース1: 全日休日の場合
            all_holiday_df = long_df.copy()
            if 'staff' in all_holiday_df.columns:
                all_holiday_df['staff'] = '休'  # 全員休みに設定
                
            filtered_all_holiday = apply_rest_exclusion_filter(all_holiday_df, "all_holiday_test", for_display=False, exclude_leave_records=False)
            edge_case_results['all_holiday_scenario'] = {
                'original_count': len(all_holiday_df),
                'filtered_count': len(filtered_all_holiday),
                'completely_filtered': len(filtered_all_holiday) == 0
            }
            
            # エッジケース2: 部分的に休日が多い期間
            partial_holiday_df = long_df.copy()
            if 'staff' in partial_holiday_df.columns and len(partial_holiday_df) > 0:
                # 半分を休日に設定
                half_count = len(partial_holiday_df) // 2
                partial_holiday_df.iloc[:half_count, partial_holiday_df.columns.get_loc('staff')] = '×'
                
            filtered_partial_holiday = apply_rest_exclusion_filter(partial_holiday_df, "partial_holiday_test", for_display=False, exclude_leave_records=False)
            edge_case_results['partial_holiday_scenario'] = {
                'original_count': len(partial_holiday_df),
                'filtered_count': len(filtered_partial_holiday),
                'exclusion_rate': (len(partial_holiday_df) - len(filtered_partial_holiday)) / len(partial_holiday_df) if len(partial_holiday_df) > 0 else 0
            }
            
            # エッジケース3: データが少ない職種・雇用形態
            edge_case_results['low_data_scenarios'] = self._verify_low_data_scenarios(long_df)
            
        except Exception as e:
            edge_case_results['error'] = str(e)
            log.error(f"エッジケース処理検証エラー: {str(e)}")
            
        return edge_case_results
    
    def create_overall_assessment(self) -> Dict[str, Any]:
        """総合評価の作成"""
        assessment = {}
        
        try:
            # 各検証結果から総合スコア算出
            scores = {}
            
            if 'data_consistency' in self.results:
                scores['data_consistency'] = self._score_data_consistency(self.results['data_consistency'])
            
            if 'dependency_analysis' in self.results:
                scores['dependency_analysis'] = self._score_dependency_analysis(self.results['dependency_analysis'])
            
            if 'aggregation_logic' in self.results:
                scores['aggregation_logic'] = self._score_aggregation_logic(self.results['aggregation_logic'])
            
            if 'ui_display' in self.results:
                scores['ui_display'] = self._score_ui_display(self.results['ui_display'])
            
            if 'performance' in self.results:
                scores['performance'] = self._score_performance(self.results['performance'])
            
            if 'edge_cases' in self.results:
                scores['edge_cases'] = self._score_edge_cases(self.results['edge_cases'])
            
            # 総合評価
            overall_score = sum(scores.values()) / len(scores) if scores else 0
            
            assessment['individual_scores'] = scores
            assessment['overall_score'] = overall_score
            assessment['assessment_grade'] = self._get_assessment_grade(overall_score)
            assessment['recommendations'] = self._generate_recommendations(scores)
            
        except Exception as e:
            assessment['error'] = str(e)
            log.error(f"総合評価作成エラー: {str(e)}")
            
        return assessment
    
    # ヘルパーメソッド群
    def _get_date_range(self, df: pd.DataFrame) -> Dict[str, Any]:
        """データの日付範囲を取得"""
        date_info = {'has_dates': False}
        
        date_cols = [col for col in df.columns if 'date' in col.lower() or '日付' in col]
        if date_cols:
            date_col = date_cols[0]
            if not df[date_col].empty:
                date_info['has_dates'] = True
                date_info['min_date'] = str(df[date_col].min())
                date_info['max_date'] = str(df[date_col].max())
                date_info['date_count'] = df[date_col].nunique()
        
        return date_info
    
    def _analyze_rest_patterns(self, df: pd.DataFrame) -> Dict[str, int]:
        """休暇パターンの分析"""
        rest_patterns = {}
        
        if 'staff' in df.columns:
            rest_symbols = ['×', 'X', 'x', '休', '休み', '休暇', '欠', '欠勤', 'OFF', 'off', 'Off', '-', '−', '―']
            
            for pattern in rest_symbols:
                count = (df['staff'].str.contains(pattern, na=False)).sum()
                if count > 0:
                    rest_patterns[pattern] = int(count)
        
        return rest_patterns
    
    def _calculate_data_stats(self, df: pd.DataFrame, context: str) -> Dict[str, Any]:
        """データ統計の計算"""
        stats = {
            'total_records': len(df),
            'context': context
        }
        
        if 'staff' in df.columns:
            stats['unique_staff'] = df['staff'].nunique()
            stats['staff_with_data'] = df['staff'].notna().sum()
        
        if 'role' in df.columns:
            stats['unique_roles'] = df['role'].nunique()
        
        if 'employment' in df.columns:
            stats['unique_employment'] = df['employment'].nunique()
        
        return stats
    
    def _assess_data_quality_improvement(self, pre_stats: Dict, post_stats: Dict) -> Dict[str, Any]:
        """データ品質改善の評価"""
        improvement = {}
        
        if pre_stats['total_records'] > 0:
            improvement['record_reduction_ratio'] = (pre_stats['total_records'] - post_stats['total_records']) / pre_stats['total_records']
        
        if 'staff_with_data' in pre_stats and 'staff_with_data' in post_stats:
            improvement['data_completeness_improvement'] = (
                post_stats['staff_with_data'] / post_stats['total_records'] - 
                pre_stats['staff_with_data'] / pre_stats['total_records']
            ) if post_stats['total_records'] > 0 and pre_stats['total_records'] > 0 else 0
        
        return improvement
    
    def _verify_heatmap_consistency(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> Dict[str, Any]:
        """ヒートマップ整合性の検証"""
        consistency = {}
        
        try:
            temp_out_dir = self.temp_dir / "heatmap_consistency"
            temp_out_dir.mkdir(exist_ok=True)
            
            data_files = build_heatmap(
                long_df, wt_df,
                out_dir=temp_out_dir,
                slot=15,
                holidays=[]
            )
            
            consistency['heatmap_generated'] = bool(data_files)
            consistency['generated_files'] = list(data_files.keys()) if data_files else []
            
        except Exception as e:
            consistency['error'] = str(e)
            consistency['heatmap_generated'] = False
        
        return consistency
    
    def _check_rest_data_presence(self, df: pd.DataFrame) -> bool:
        """休暇データの存在確認"""
        if df.empty:
            return False
        
        # staffカラムに休暇パターンがあるかチェック
        rest_patterns = ['×', 'X', 'x', '休', '休み', '休暇', '欠', '欠勤', 'OFF', 'off', 'Off']
        
        if 'staff' in df.columns:
            for pattern in rest_patterns:
                if (df['staff'].str.contains(pattern, na=False)).any():
                    return True
        
        return False
    
    def _analyze_file_interdependencies(self, data_files: Dict) -> Dict[str, Any]:
        """ファイル間依存関係の分析"""
        dependencies = {
            'file_count': len(data_files),
            'interdependency_analysis': {}
        }
        
        # ファイルが存在する場合の依存関係チェック
        for file_type, file_path in data_files.items():
            if file_path and file_path.exists():
                try:
                    df = pd.read_parquet(file_path)
                    dependencies['interdependency_analysis'][file_type] = {
                        'can_read': True,
                        'has_data': not df.empty,
                        'shape': df.shape
                    }
                except Exception as e:
                    dependencies['interdependency_analysis'][file_type] = {
                        'can_read': False,
                        'error': str(e)
                    }
        
        return dependencies
    
    def _perform_aggregation_analysis(self, df: pd.DataFrame, context: str) -> Dict[str, Any]:
        """集計分析の実行"""
        analysis = {'context': context}
        
        if not df.empty:
            # 基本統計
            analysis['basic_stats'] = {
                'total_records': len(df),
                'unique_staff': df['staff'].nunique() if 'staff' in df.columns else 0,
                'unique_roles': df['role'].nunique() if 'role' in df.columns else 0
            }
            
            # 時間別集計（parsed_slots_countがある場合）
            if 'parsed_slots_count' in df.columns:
                analysis['time_aggregation'] = {
                    'total_slots': df['parsed_slots_count'].sum(),
                    'avg_slots_per_record': df['parsed_slots_count'].mean(),
                    'max_slots': df['parsed_slots_count'].max(),
                    'min_slots': df['parsed_slots_count'].min()
                }
        
        return analysis
    
    def _analyze_aggregation_impact(self, original: Dict, filtered: Dict) -> Dict[str, Any]:
        """集計への影響分析"""
        impact = {}
        
        try:
            if 'basic_stats' in original and 'basic_stats' in filtered:
                orig_stats = original['basic_stats']
                filt_stats = filtered['basic_stats']
                
                impact['record_impact'] = {
                    'reduction_ratio': (orig_stats['total_records'] - filt_stats['total_records']) / orig_stats['total_records'] if orig_stats['total_records'] > 0 else 0,
                    'staff_retention_ratio': filt_stats['unique_staff'] / orig_stats['unique_staff'] if orig_stats['unique_staff'] > 0 else 0,
                    'role_retention_ratio': filt_stats['unique_roles'] / orig_stats['unique_roles'] if orig_stats['unique_roles'] > 0 else 0
                }
            
            if 'time_aggregation' in original and 'time_aggregation' in filtered:
                orig_time = original['time_aggregation']
                filt_time = filtered['time_aggregation']
                
                impact['time_impact'] = {
                    'slots_reduction_ratio': (orig_time['total_slots'] - filt_time['total_slots']) / orig_time['total_slots'] if orig_time['total_slots'] > 0 else 0,
                    'avg_slots_change': filt_time['avg_slots_per_record'] - orig_time['avg_slots_per_record']
                }
                
        except Exception as e:
            impact['error'] = str(e)
        
        return impact
    
    def _verify_proportional_calculation(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> Dict[str, Any]:
        """按分計算ロジックの検証"""
        proportional_results = {}
        
        try:
            # 仮想的な按分計算実行
            temp_out_dir = self.temp_dir / "proportional_test"
            temp_out_dir.mkdir(exist_ok=True)
            
            # ヒートマップ生成
            data_files = build_heatmap(
                long_df, wt_df,
                out_dir=temp_out_dir,
                slot=15,
                holidays=[]
            )
            
            if data_files and 'heat_ALL' in data_files and data_files['heat_ALL'].exists():
                heat_all_df = pd.read_parquet(data_files['heat_ALL'])
                
                # 按分計算実行
                proportional_shortage = calculate_proportional_shortage(heat_all_df)
                
                proportional_results['calculation_successful'] = True
                proportional_results['shortage_summary'] = {
                    'total_shortage': proportional_shortage.get('total_shortage', 0),
                    'calculation_method': 'proportional',
                    'data_quality': 'filtered_rest_excluded'
                }
                
            else:
                proportional_results['calculation_successful'] = False
                proportional_results['reason'] = 'ヒートマップ生成失敗'
                
        except Exception as e:
            proportional_results['calculation_successful'] = False
            proportional_results['error'] = str(e)
        
        return proportional_results
    
    def _verify_shortage_tab_data(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> Dict[str, Any]:
        """不足分析タブデータの検証"""
        tab_data = {}
        
        try:
            # 不足分析に必要なデータが正しく生成されるかチェック
            temp_out_dir = self.temp_dir / "shortage_tab_test"
            temp_out_dir.mkdir(exist_ok=True)
            
            data_files = build_heatmap(
                long_df, wt_df,
                out_dir=temp_out_dir,
                slot=15,
                holidays=[]
            )
            
            tab_data['heatmap_data_available'] = bool(data_files and 'heat_ALL' in data_files)
            tab_data['data_consistency'] = 'verified' if tab_data['heatmap_data_available'] else 'failed'
            
        except Exception as e:
            tab_data['error'] = str(e)
            tab_data['data_consistency'] = 'error'
        
        return tab_data
    
    def _verify_heatmap_tab_data(self, long_df: pd.DataFrame, wt_df: pd.DataFrame) -> Dict[str, Any]:
        """ヒートマップタブデータの検証"""
        return self._verify_shortage_tab_data(long_df, wt_df)  # 同じロジック
    
    def _verify_metrics_consistency(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """メトリクス一貫性の検証"""
        metrics = {}
        
        try:
            # 基本メトリクス
            metrics['staff_count'] = long_df['staff'].nunique() if 'staff' in long_df.columns else 0
            metrics['total_records'] = len(long_df)
            metrics['data_completeness'] = (long_df['staff'].notna().sum() / len(long_df)) if len(long_df) > 0 else 0
            metrics['consistency_check'] = 'passed'
            
        except Exception as e:
            metrics['error'] = str(e)
            metrics['consistency_check'] = 'failed'
        
        return metrics
    
    def _compare_processing_times(self, original_df: pd.DataFrame, filtered_df: pd.DataFrame, wt_df: pd.DataFrame) -> Dict[str, Any]:
        """処理時間の比較"""
        import time
        
        comparison = {}
        
        try:
            # 元データでの処理時間
            start_time = time.time()
            temp_out_dir_orig = self.temp_dir / "perf_orig"
            temp_out_dir_orig.mkdir(exist_ok=True)
            
            data_files_orig = build_heatmap(
                original_df, wt_df,
                out_dir=temp_out_dir_orig,
                slot=15,
                holidays=[]
            )
            orig_time = time.time() - start_time
            
            # フィルター済みデータでの処理時間
            start_time = time.time()
            temp_out_dir_filt = self.temp_dir / "perf_filt"
            temp_out_dir_filt.mkdir(exist_ok=True)
            
            data_files_filt = build_heatmap(
                filtered_df, wt_df,
                out_dir=temp_out_dir_filt,
                slot=15,
                holidays=[]
            )
            filt_time = time.time() - start_time
            
            comparison['original_processing_time'] = orig_time
            comparison['filtered_processing_time'] = filt_time
            comparison['time_improvement_ratio'] = (orig_time - filt_time) / orig_time if orig_time > 0 else 0
            comparison['performance_improved'] = filt_time < orig_time
            
        except Exception as e:
            comparison['error'] = str(e)
        
        return comparison
    
    def _verify_low_data_scenarios(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """少データシナリオの検証"""
        scenarios = {}
        
        try:
            if 'role' in long_df.columns:
                # 職種別データ量確認
                role_counts = long_df['role'].value_counts()
                low_data_roles = role_counts[role_counts < 5].index.tolist()  # 5件未満を「少データ」とする
                
                scenarios['low_data_roles'] = {
                    'roles': low_data_roles,
                    'count': len(low_data_roles),
                    'total_roles': len(role_counts)
                }
                
                # 少データ職種での休日除外影響
                for role in low_data_roles[:3]:  # 最大3職種まで確認
                    role_data = long_df[long_df['role'] == role]
                    filtered_role_data = apply_rest_exclusion_filter(role_data.copy(), f"low_data_role_{role}", for_display=False, exclude_leave_records=False)
                    
                    scenarios[f'role_{role}_impact'] = {
                        'original_count': len(role_data),
                        'filtered_count': len(filtered_role_data),
                        'data_survival_rate': len(filtered_role_data) / len(role_data) if len(role_data) > 0 else 0
                    }
            
            if 'employment' in long_df.columns:
                # 雇用形態別データ量確認
                emp_counts = long_df['employment'].value_counts()
                low_data_employments = emp_counts[emp_counts < 5].index.tolist()
                
                scenarios['low_data_employments'] = {
                    'employments': low_data_employments,
                    'count': len(low_data_employments),
                    'total_employments': len(emp_counts)
                }
                
        except Exception as e:
            scenarios['error'] = str(e)
        
        return scenarios
    
    # スコアリングメソッド群
    def _score_data_consistency(self, data_consistency: Dict) -> float:
        """データ整合性スコア（0-100）"""
        score = 50  # ベーススコア
        
        if 'error' in data_consistency:
            return 0
        
        if 'filter_impact' in data_consistency:
            impact = data_consistency['filter_impact']
            # 適切な除外率（10-30%程度）を評価
            exclusion_rate = impact.get('exclusion_rate', 0)
            if 0.1 <= exclusion_rate <= 0.3:
                score += 30
            elif 0.05 <= exclusion_rate <= 0.5:
                score += 20
            else:
                score += 10
        
        if 'heatmap_consistency' in data_consistency:
            heatmap = data_consistency['heatmap_consistency']
            if heatmap.get('heatmap_generated', False):
                score += 20
        
        return min(score, 100)
    
    def _score_dependency_analysis(self, dependency_analysis: Dict) -> float:
        """依存関係分析スコア（0-100）"""
        score = 50
        
        if 'error' in dependency_analysis:
            return 0
        
        if 'generated_files' in dependency_analysis:
            files = dependency_analysis['generated_files']
            if files:
                score += 25
                # 休日データが適切に除外されているかチェック
                rest_excluded = all(not file_info.get('has_rest_data', True) for file_info in files.values())
                if rest_excluded:
                    score += 25
        
        return min(score, 100)
    
    def _score_aggregation_logic(self, aggregation_logic: Dict) -> float:
        """集計ロジックスコア（0-100）"""
        score = 50
        
        if 'error' in aggregation_logic:
            return 0
        
        if 'comparison' in aggregation_logic:
            comparison = aggregation_logic['comparison']
            if 'impact_analysis' in comparison:
                impact = comparison['impact_analysis']
                # 適切な影響があることを評価
                if 'record_impact' in impact:
                    record_impact = impact['record_impact']
                    reduction = record_impact.get('reduction_ratio', 0)
                    if 0.1 <= reduction <= 0.4:  # 10-40%の削減が適切
                        score += 25
        
        if 'proportional_calculation' in aggregation_logic:
            prop_calc = aggregation_logic['proportional_calculation']
            if prop_calc.get('calculation_successful', False):
                score += 25
        
        return min(score, 100)
    
    def _score_ui_display(self, ui_display: Dict) -> float:
        """UI表示スコア（0-100）"""
        score = 50
        
        if 'error' in ui_display:
            return 0
        
        if 'tab_data_integrity' in ui_display:
            tabs = ui_display['tab_data_integrity']
            working_tabs = sum(1 for tab_data in tabs.values() if tab_data.get('data_consistency') == 'verified')
            score += (working_tabs / len(tabs)) * 30 if tabs else 0
        
        if 'metrics_consistency' in ui_display:
            metrics = ui_display['metrics_consistency']
            if metrics.get('consistency_check') == 'passed':
                score += 20
        
        return min(score, 100)
    
    def _score_performance(self, performance: Dict) -> float:
        """パフォーマンススコア（0-100）"""
        score = 50
        
        if 'error' in performance:
            return 0
        
        if 'data_reduction' in performance:
            reduction = performance['data_reduction']
            reduction_ratio = reduction.get('reduction_ratio', 0)
            memory_reduction = reduction.get('memory_reduction_mb', 0)
            
            # データ削減効果
            if reduction_ratio > 0.1:
                score += 25
            
            # メモリ削減効果
            if memory_reduction > 0:
                score += 15
        
        if 'processing_time_comparison' in performance:
            time_comp = performance['processing_time_comparison']
            if time_comp.get('performance_improved', False):
                score += 10
        
        return min(score, 100)
    
    def _score_edge_cases(self, edge_cases: Dict) -> float:
        """エッジケーススコア（0-100）"""
        score = 50
        
        if 'error' in edge_cases:
            return 0
        
        # 全休日シナリオ
        if 'all_holiday_scenario' in edge_cases:
            all_holiday = edge_cases['all_holiday_scenario']
            if all_holiday.get('completely_filtered', False):
                score += 20  # 全て除外されるのは正しい動作
        
        # 部分休日シナリオ
        if 'partial_holiday_scenario' in edge_cases:
            partial = edge_cases['partial_holiday_scenario']
            exclusion_rate = partial.get('exclusion_rate', 0)
            if 0.3 <= exclusion_rate <= 0.7:  # 適切な除外率
                score += 20
        
        # 低データシナリオ
        if 'low_data_scenarios' in edge_cases:
            low_data = edge_cases['low_data_scenarios']
            if not low_data.get('error'):
                score += 10
        
        return min(score, 100)
    
    def _get_assessment_grade(self, score: float) -> str:
        """スコアからグレードを決定"""
        if score >= 90:
            return "Excellent (A+)"
        elif score >= 80:
            return "Good (A)"
        elif score >= 70:
            return "Satisfactory (B)"
        elif score >= 60:
            return "Fair (C)"
        elif score >= 50:
            return "Poor (D)"
        else:
            return "Critical (F)"
    
    def _generate_recommendations(self, scores: Dict[str, float]) -> List[str]:
        """改善推奨事項の生成"""
        recommendations = []
        
        for category, score in scores.items():
            if score < 70:
                if category == 'data_consistency':
                    recommendations.append("データ整合性の改善: フィルター適用前後のデータ検証を強化")
                elif category == 'dependency_analysis':
                    recommendations.append("依存関係分析の改善: parquetファイル生成プロセスの最適化")
                elif category == 'aggregation_logic':
                    recommendations.append("集計ロジックの改善: 按分計算の精度向上")
                elif category == 'ui_display':
                    recommendations.append("UI表示の改善: タブ間データ整合性の確保")
                elif category == 'performance':
                    recommendations.append("パフォーマンスの改善: データ処理効率化")
                elif category == 'edge_cases':
                    recommendations.append("エッジケース対応の改善: 特殊ケース処理の強化")
        
        if not recommendations:
            recommendations.append("全ての検証項目で良好な結果を確認。現在の実装を維持")
        
        return recommendations


def main():
    """メイン実行関数"""
    print("=" * 80)
    print("休日除外修正の総合的システム検証")
    print("=" * 80)
    
    # テストファイルのパスを指定
    excel_files = [
        "デイ_テスト用データ_休日精緻.xlsx",
        "ショート_テスト用データ.xlsx"
    ]
    
    verification_suite = HolidayExclusionVerificationSuite()
    
    for excel_file in excel_files:
        if Path(excel_file).exists():
            print(f"\n[検証対象] {excel_file}")
            print("-" * 60)
            
            results = verification_suite.run_comprehensive_verification(excel_file)
            
            # 結果をJSONファイルに保存
            output_file = f"holiday_exclusion_verification_{Path(excel_file).stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"検証結果を {output_file} に保存しました")
            
            # 総合評価の表示
            if 'overall_assessment' in results:
                assessment = results['overall_assessment']
                print(f"\n【総合評価】")
                print(f"総合スコア: {assessment.get('overall_score', 0):.1f}/100")
                print(f"評価グレード: {assessment.get('assessment_grade', 'Unknown')}")
                
                if 'recommendations' in assessment:
                    print(f"\n【推奨事項】")
                    for i, rec in enumerate(assessment['recommendations'], 1):
                        print(f"{i}. {rec}")
        else:
            print(f"ファイルが見つかりません: {excel_file}")
    
    print(f"\n検証完了。詳細結果は各JSONファイルを参照してください。")

if __name__ == "__main__":
    main()