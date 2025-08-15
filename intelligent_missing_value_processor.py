#!/usr/bin/env python
"""
インテリジェント欠損値処理システム

従来のfillna(0)から脱却し、interpolate()を使用した現実的な補間
「データ未入力」と「人員0人」の区別による誤った過剰人員算出を防止
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Union
from pathlib import Path
import warnings

log = logging.getLogger(__name__)

class IntelligentMissingValueProcessor:
    """インテリジェント欠損値処理クラス"""
    
    def __init__(self, interpolation_method: str = 'time', fallback_method: str = 'linear'):
        """
        初期化
        
        Args:
            interpolation_method: 主要補間手法（time, linear, polynomial等）
            fallback_method: フォールバック補間手法
        """
        self.interpolation_method = interpolation_method
        self.fallback_method = fallback_method
        self.processing_log = []
        self.data_quality_report = {}
        
    def process_missing_values(
        self, 
        df: pd.DataFrame, 
        datetime_column: str = 'ds',
        preserve_explicit_zeros: bool = True
    ) -> Tuple[pd.DataFrame, Dict[str, any]]:
        """
        欠損値の智的処理
        
        Args:
            df: 処理対象DataFrame
            datetime_column: 日時列名
            preserve_explicit_zeros: 明示的な0値を保持するか
            
        Returns:
            tuple: (処理済みDataFrame, 処理レポート)
        """
        log.info(f"[MISSING_VALUE] 欠損値智的処理開始: shape={df.shape}")
        
        processed_df = df.copy()
        processing_report = {
            'original_shape': df.shape,
            'missing_analysis': {},
            'interpolation_results': {},
            'quality_metrics': {},
            'warnings': []
        }
        
        try:
            # 1. 欠損値パターン分析
            missing_analysis = self._analyze_missing_patterns(df)
            processing_report['missing_analysis'] = missing_analysis
            
            # 2. 時系列インデックス準備
            if datetime_column in df.columns:
                processed_df = self._prepare_time_index(processed_df, datetime_column)
            
            # 3. 職種・列種別の欠損値処理
            data_columns = self._identify_data_columns(processed_df)
            
            for column in data_columns:
                if column in processed_df.columns:
                    column_result = self._process_column_missing_values(
                        processed_df, column, preserve_explicit_zeros
                    )
                    processed_df[column] = column_result['processed_series']
                    processing_report['interpolation_results'][column] = column_result['metadata']
            
            # 4. 品質メトリクス計算
            quality_metrics = self._calculate_quality_metrics(df, processed_df)
            processing_report['quality_metrics'] = quality_metrics
            
            # 5. データ品質警告
            warnings = self._generate_quality_warnings(processing_report)
            processing_report['warnings'] = warnings
            
            log.info(f"[MISSING_VALUE] 処理完了: {len(data_columns)}列処理")
            return processed_df, processing_report
            
        except Exception as e:
            log.error(f"[MISSING_VALUE] 処理エラー: {e}")
            raise ValueError(f"欠損値処理に失敗: {e}")
    
    def _analyze_missing_patterns(self, df: pd.DataFrame) -> Dict[str, any]:
        """欠損値パターンの分析"""
        
        analysis = {
            'total_cells': df.size,
            'missing_cells': df.isnull().sum().sum(),
            'missing_percentage': 0.0,
            'column_missing_rates': {},
            'missing_patterns': {}
        }
        
        if analysis['total_cells'] > 0:
            analysis['missing_percentage'] = (analysis['missing_cells'] / analysis['total_cells']) * 100
        
        # 列別欠損率
        for column in df.columns:
            missing_count = df[column].isnull().sum()
            total_count = len(df[column])
            missing_rate = (missing_count / total_count) * 100 if total_count > 0 else 0
            
            analysis['column_missing_rates'][column] = {
                'missing_count': missing_count,
                'total_count': total_count,
                'missing_rate': missing_rate
            }
        
        # 欠損パターン分析
        if not df.empty:
            # 完全欠損行
            completely_missing_rows = df.isnull().all(axis=1).sum()
            # 部分欠損行
            partially_missing_rows = df.isnull().any(axis=1).sum() - completely_missing_rows
            
            analysis['missing_patterns'] = {
                'completely_missing_rows': completely_missing_rows,
                'partially_missing_rows': partially_missing_rows,
                'complete_rows': len(df) - completely_missing_rows - partially_missing_rows
            }
        
        return analysis
    
    def _prepare_time_index(self, df: pd.DataFrame, datetime_column: str) -> pd.DataFrame:
        """時系列インデックスの準備"""
        
        df_prepared = df.copy()
        
        try:
            # 日時列をdatetimeに変換
            df_prepared[datetime_column] = pd.to_datetime(df_prepared[datetime_column])
            
            # インデックスとして設定（interpolate用）
            if not df_prepared.index.equals(df_prepared[datetime_column]):
                df_prepared = df_prepared.set_index(datetime_column, drop=False)
                df_prepared.index.name = 'datetime_index'
            
            # 時系列順にソート
            df_prepared = df_prepared.sort_index()
            
            log.info(f"[TIME_INDEX] 時系列インデックス準備完了: {len(df_prepared)}レコード")
            
        except Exception as e:
            log.warning(f"[TIME_INDEX] 時系列インデックス準備失敗: {e}")
            # フォールバック: 元のDataFrameを返す
        
        return df_prepared
    
    def _identify_data_columns(self, df: pd.DataFrame) -> List[str]:
        """データ列の特定（数値データのみ）"""
        
        # メタデータ列を除外
        METADATA_COLUMNS = {
            'ds', 'staff', 'role', 'employment', 'datetime_index', 
            'date', 'time', 'hour', 'minute', 'weekday', 'weekday_name',
            'month', 'quarter', 'year', 'is_weekend', 'is_business_hour',
            'time_category', 'week_of_month'
        }
        
        # 数値データ列を特定
        data_columns = []
        for column in df.columns:
            if column not in METADATA_COLUMNS:
                # 数値型またはNumPy数値型の列
                if pd.api.types.is_numeric_dtype(df[column]):
                    data_columns.append(column)
                # 文字列だが数値に変換可能な列
                elif df[column].dtype == 'object':
                    # サンプルデータで数値変換可能性をチェック
                    sample = df[column].dropna().head(10)
                    try:
                        pd.to_numeric(sample)
                        data_columns.append(column)
                    except (ValueError, TypeError):
                        pass
        
        log.info(f"[DATA_COLUMNS] 特定されたデータ列: {len(data_columns)}列")
        return data_columns
    
    def _process_column_missing_values(
        self, 
        df: pd.DataFrame, 
        column: str, 
        preserve_explicit_zeros: bool
    ) -> Dict[str, any]:
        """列の欠損値処理"""
        
        original_series = df[column].copy()
        
        # 数値型に変換
        try:
            numeric_series = pd.to_numeric(original_series, errors='coerce')
        except Exception:
            numeric_series = original_series.copy()
        
        # 明示的な0値の記録（preserve_explicit_zeros=Trueの場合）
        explicit_zeros = pd.Series(False, index=numeric_series.index)
        if preserve_explicit_zeros:
            # 元データで明示的に0が入力されている位置を記録
            explicit_zeros = (original_series == 0) | (original_series == '0')
        
        # 欠損値の数
        missing_count_before = numeric_series.isnull().sum()
        
        # インテリジェント補間
        interpolated_series = self._apply_intelligent_interpolation(numeric_series)
        
        # 明示的な0値を復元
        if preserve_explicit_zeros:
            interpolated_series.loc[explicit_zeros] = 0
        
        # 残存欠損値を0で補完（最後の手段）
        final_series = interpolated_series.fillna(0)
        
        # 処理後の欠損値の数
        missing_count_after = final_series.isnull().sum()
        
        # メタデータ
        metadata = {
            'original_missing_count': missing_count_before,
            'final_missing_count': missing_count_after,
            'explicit_zeros_preserved': explicit_zeros.sum() if preserve_explicit_zeros else 0,
            'interpolation_method_used': self.interpolation_method,
            'processing_success': True
        }
        
        return {
            'processed_series': final_series,
            'metadata': metadata
        }
    
    def _apply_intelligent_interpolation(self, series: pd.Series) -> pd.Series:
        """インテリジェント補間の適用"""
        
        if series.isnull().sum() == 0:
            return series  # 欠損値がない場合はそのまま返す
        
        try:
            # 主要手法での補間
            if self.interpolation_method == 'time':
                # 時系列ベース補間（インデックスがdatetimeの場合に有効）
                interpolated = series.interpolate(method='time', limit_area='inside')
            elif self.interpolation_method == 'linear':
                # 線形補間
                interpolated = series.interpolate(method='linear', limit_area='inside')
            elif self.interpolation_method == 'polynomial':
                # 多項式補間（データ点が十分な場合）
                if len(series.dropna()) >= 3:
                    interpolated = series.interpolate(method='polynomial', order=2, limit_area='inside')
                else:
                    interpolated = series.interpolate(method='linear', limit_area='inside')
            else:
                # その他の手法
                interpolated = series.interpolate(method=self.interpolation_method, limit_area='inside')
            
            # 補間後も欠損値が残る場合はフォールバック手法
            if interpolated.isnull().sum() > 0:
                log.warning(f"[INTERPOLATE] 主要手法で補間不完全、フォールバック適用")
                interpolated = interpolated.interpolate(method=self.fallback_method)
            
            return interpolated
            
        except Exception as e:
            log.error(f"[INTERPOLATE] 補間エラー: {e}, フォールバック手法適用")
            # フォールバック: シンプルな線形補間
            try:
                return series.interpolate(method='linear')
            except Exception:
                # 最終フォールバック: 前方補完と後方補完
                return series.fillna(method='ffill').fillna(method='bfill')
    
    def _calculate_quality_metrics(self, original_df: pd.DataFrame, processed_df: pd.DataFrame) -> Dict[str, any]:
        """品質メトリクスの計算"""
        
        metrics = {
            'data_completeness': {},
            'interpolation_effectiveness': {},
            'value_consistency': {}
        }
        
        # データ完成度
        original_missing = original_df.isnull().sum().sum()
        processed_missing = processed_df.isnull().sum().sum()
        total_cells = original_df.size
        
        metrics['data_completeness'] = {
            'original_completeness': ((total_cells - original_missing) / total_cells) * 100 if total_cells > 0 else 0,
            'processed_completeness': ((total_cells - processed_missing) / total_cells) * 100 if total_cells > 0 else 0,
            'improvement': processed_missing < original_missing
        }
        
        # 補間効果性
        if original_missing > 0:
            interpolation_success_rate = ((original_missing - processed_missing) / original_missing) * 100
        else:
            interpolation_success_rate = 100  # 元々欠損値がない場合
        
        metrics['interpolation_effectiveness'] = {
            'success_rate': interpolation_success_rate,
            'cells_interpolated': original_missing - processed_missing
        }
        
        # 値の一貫性（数値データ列で負の値が生成されていないかチェック）
        data_columns = self._identify_data_columns(processed_df)
        negative_values_count = 0
        
        for column in data_columns:
            if column in processed_df.columns:
                negative_count = (processed_df[column] < 0).sum()
                negative_values_count += negative_count
        
        metrics['value_consistency'] = {
            'negative_values_generated': negative_values_count,
            'data_columns_checked': len(data_columns)
        }
        
        return metrics
    
    def _generate_quality_warnings(self, processing_report: Dict) -> List[Dict[str, str]]:
        """品質警告の生成"""
        
        warnings = []
        
        # 高い欠損率の警告
        missing_analysis = processing_report.get('missing_analysis', {})
        overall_missing_rate = missing_analysis.get('missing_percentage', 0)
        
        if overall_missing_rate > 30:
            warnings.append({
                'level': 'high',
                'category': 'data_quality',
                'message': f'全体的な欠損率が高い: {overall_missing_rate:.1f}%。データ収集プロセスの見直しを推奨'
            })
        elif overall_missing_rate > 15:
            warnings.append({
                'level': 'medium',
                'category': 'data_quality',
                'message': f'欠損率: {overall_missing_rate:.1f}%。補間結果の精度に注意'
            })
        
        # 列別の高欠損率警告
        column_rates = missing_analysis.get('column_missing_rates', {})
        for column, rate_info in column_rates.items():
            if rate_info['missing_rate'] > 50:
                warnings.append({
                    'level': 'high',
                    'category': 'column_specific',
                    'message': f'列 {column} の欠損率が過大: {rate_info["missing_rate"]:.1f}%'
                })
        
        # 補間効果性の警告
        quality_metrics = processing_report.get('quality_metrics', {})
        interpolation_metrics = quality_metrics.get('interpolation_effectiveness', {})
        success_rate = interpolation_metrics.get('success_rate', 0)
        
        if success_rate < 70:
            warnings.append({
                'level': 'medium',
                'category': 'interpolation',
                'message': f'補間成功率が低い: {success_rate:.1f}%。データパターンが不規則な可能性'
            })
        
        # 負の値生成警告
        consistency_metrics = quality_metrics.get('value_consistency', {})
        negative_values = consistency_metrics.get('negative_values_generated', 0)
        
        if negative_values > 0:
            warnings.append({
                'level': 'medium',
                'category': 'value_consistency',
                'message': f'補間により負の値が生成: {negative_values}箇所。人員配置データとして不適切'
            })
        
        return warnings

def process_shift_data_missing_values(
    df: pd.DataFrame, 
    datetime_column: str = 'ds',
    interpolation_method: str = 'time'
) -> Tuple[pd.DataFrame, Dict[str, any]]:
    """
    シフトデータの欠損値処理（便利関数）
    
    Args:
        df: シフトデータDataFrame
        datetime_column: 日時列名
        interpolation_method: 補間手法
        
    Returns:
        tuple: (処理済みDataFrame, 処理レポート)
    """
    processor = IntelligentMissingValueProcessor(interpolation_method=interpolation_method)
    return processor.process_missing_values(df, datetime_column)

def generate_missing_value_report(processing_report: Dict[str, any], output_file: Optional[Path] = None) -> str:
    """
    欠損値処理レポートの生成
    
    Args:
        processing_report: 処理レポート
        output_file: 出力ファイルパス（Noneの場合は文字列として返す）
        
    Returns:
        str: レポート内容
    """
    
    report_lines = [
        "=== インテリジェント欠損値処理レポート ===",
        "",
        f"処理対象データ: {processing_report['original_shape'][0]}行 × {processing_report['original_shape'][1]}列",
        ""
    ]
    
    # 欠損値分析
    missing_analysis = processing_report.get('missing_analysis', {})
    report_lines.extend([
        "【欠損値分析】",
        f"全体欠損率: {missing_analysis.get('missing_percentage', 0):.2f}%",
        f"欠損セル数: {missing_analysis.get('missing_cells', 0):,}",
        ""
    ])
    
    # 補間結果
    interpolation_results = processing_report.get('interpolation_results', {})
    if interpolation_results:
        report_lines.append("【列別補間結果】")
        for column, result in interpolation_results.items():
            before = result.get('original_missing_count', 0)
            after = result.get('final_missing_count', 0)
            zeros_preserved = result.get('explicit_zeros_preserved', 0)
            
            report_lines.append(f"  {column}:")
            report_lines.append(f"    補間前欠損: {before}個")
            report_lines.append(f"    補間後欠損: {after}個")
            if zeros_preserved > 0:
                report_lines.append(f"    保持された明示的0値: {zeros_preserved}個")
        report_lines.append("")
    
    # 品質メトリクス
    quality_metrics = processing_report.get('quality_metrics', {})
    completeness = quality_metrics.get('data_completeness', {})
    effectiveness = quality_metrics.get('interpolation_effectiveness', {})
    
    report_lines.extend([
        "【品質メトリクス】",
        f"データ完成度改善: {completeness.get('original_completeness', 0):.1f}% → {completeness.get('processed_completeness', 0):.1f}%",
        f"補間成功率: {effectiveness.get('success_rate', 0):.1f}%",
        f"補間済みセル数: {effectiveness.get('cells_interpolated', 0):,}",
        ""
    ])
    
    # 警告
    warnings = processing_report.get('warnings', [])
    if warnings:
        report_lines.append("【警告・推奨事項】")
        for warning in warnings:
            level_prefix = f"[{warning['level'].upper()}]"
            report_lines.append(f"  {level_prefix} {warning['message']}")
        report_lines.append("")
    
    report_content = "\n".join(report_lines)
    
    # ファイル出力
    if output_file:
        output_file.write_text(report_content, encoding='utf-8')
        log.info(f"欠損値処理レポート出力: {output_file}")
    
    return report_content

# 使用例とテスト
def test_intelligent_missing_value_processing():
    """インテリジェント欠損値処理のテスト"""
    
    # テストデータ作成（意図的に欠損値を含む）
    dates = pd.date_range('2025-01-01', periods=10, freq='D')
    test_data = {
        'ds': dates,
        'staff_count_1': [2, np.nan, 3, 0, np.nan, 2, 3, np.nan, 1, 2],
        'staff_count_2': [1, 1, np.nan, np.nan, 2, np.nan, 1, 1, np.nan, 1],
        'role': ['介護'] * 10  # メタデータ列
    }
    
    test_df = pd.DataFrame(test_data)
    
    print("=== インテリジェント欠損値処理テスト ===")
    print(f"元データ:")
    print(test_df)
    print(f"\n欠損値数: {test_df.isnull().sum().sum()}")
    
    # 処理実行
    processed_df, report = process_shift_data_missing_values(test_df, datetime_column='ds')
    
    print(f"\n処理後データ:")
    print(processed_df[['ds', 'staff_count_1', 'staff_count_2']])
    print(f"\n処理後欠損値数: {processed_df.isnull().sum().sum()}")
    
    # レポート生成
    report_content = generate_missing_value_report(report)
    print(f"\n{report_content}")
    
    return processed_df, report

if __name__ == "__main__":
    # テスト実行
    test_processed_df, test_report = test_intelligent_missing_value_processing()
    print("\nインテリジェント欠損値処理のテストが完了しました！")