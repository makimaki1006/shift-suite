"""
包括的なシフト分析レポート生成モジュール
3ヶ月分などの長期データから時系列分析と詳細な洞察を提供
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
import json

log = logging.getLogger(__name__)


class ComprehensiveReportGenerator:
    """長期シフトデータの包括的分析レポート生成"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_comprehensive_report(self, 
                                    long_df: pd.DataFrame,
                                    analysis_results: Dict[str, pd.DataFrame],
                                    period_months: int = 3) -> Path:
        """
        包括的なレポートを生成
        
        Args:
            long_df: 長期のシフトデータ
            analysis_results: 各分析結果のDataFrame辞書
            period_months: 分析期間（月数）
        
        Returns:
            生成されたレポートファイルのパス
        """
        report_path = self.output_dir / f"comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            # ヘッダー（JSON風構造化データ開始）
            f.write("="*80 + "\n")
            f.write(f"FACILITY_ANALYSIS_REPORT\n")
            f.write("="*80 + "\n")
            f.write(f"FACILITY_ID: {self.output_dir.name}\n")
            f.write(f"ANALYSIS_PERIOD: {self._get_period_str(long_df)}\n")
            f.write(f"REPORT_GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"TOTAL_RECORDS: {len(long_df)}\n")
            f.write("="*80 + "\n\n")
            
            # 1. エグゼクティブサマリー
            f.write(self._generate_executive_summary(long_df, analysis_results))
            
            # 2. 時系列トレンド分析
            f.write(self._generate_trend_analysis(long_df, analysis_results, period_months))
            
            # 3. 職員個別分析
            f.write(self._generate_staff_analysis(long_df, analysis_results))
            
            # 4. 各種分析結果の統合データ
            f.write(self._generate_organizational_health(long_df, analysis_results))
            
            # 5. 詳細データ分解
            f.write(self._generate_detailed_breakdown(long_df, analysis_results))
            
            # レポート終了マーカー
            f.write("="*80 + "\n")
            f.write("END_OF_FACILITY_REPORT\n")
            f.write("="*80 + "\n")
        
        log.info(f"包括的レポートを生成しました: {report_path}")
        return report_path
    
    def _get_period_str(self, df: pd.DataFrame) -> str:
        """分析期間の文字列を取得"""
        if 'ds' in df.columns:
            start_date = pd.to_datetime(df['ds']).min()
            end_date = pd.to_datetime(df['ds']).max()
            return f"{start_date.strftime('%Y年%m月%d日')} 〜 {end_date.strftime('%Y年%m月%d日')}"
        return "期間不明"
    
    def _generate_executive_summary(self, long_df: pd.DataFrame, results: Dict) -> str:
        """基本統計情報の生成"""
        summary = "SECTION: BASIC_STATISTICS\n" + "-"*40 + "\n"
        
        # 基本データ統計
        total_staff = long_df['staff'].nunique() if 'staff' in long_df.columns else 0
        total_days = long_df['ds'].nunique() if 'ds' in long_df.columns else 0
        total_records = len(long_df)
        
        summary += f"TOTAL_STAFF: {total_staff}\n"
        summary += f"ANALYSIS_DAYS: {total_days}\n"
        summary += f"TOTAL_RECORDS: {total_records}\n"
        
        if 'role' in long_df.columns:
            total_roles = long_df['role'].nunique()
            summary += f"ROLE_TYPES: {total_roles}\n"
            # 職種リスト
            roles = long_df['role'].unique()
            summary += f"ROLE_LIST: {','.join(roles)}\n"
            
        if 'employment' in long_df.columns:
            total_employment_types = long_df['employment'].nunique()
            summary += f"EMPLOYMENT_TYPES: {total_employment_types}\n"
            # 雇用形態リスト
            employments = long_df['employment'].unique()
            summary += f"EMPLOYMENT_LIST: {','.join(employments)}\n"
        
        summary += "\nSUBSECTION: ANALYSIS_DATA_VOLUME\n"
        
        # 各分析結果のデータ量（標準化された形式）
        if 'shortage_summary' in results:
            shortage_df = results['shortage_summary']
            summary += f"SHORTAGE_RECORDS: {len(shortage_df)}\n"
            if 'lack' in shortage_df.columns:
                total_shortage = shortage_df['lack'].sum()
                total_excess = shortage_df['excess'].sum() if 'excess' in shortage_df.columns else 0
                summary += f"TOTAL_SHORTAGE_HOURS: {total_shortage:.1f}\n"
                summary += f"TOTAL_EXCESS_HOURS: {total_excess:.1f}\n"
        
        if 'fatigue_score' in results:
            fatigue_df = results['fatigue_score']
            summary += f"FATIGUE_RECORDS: {len(fatigue_df)}\n"
            if 'fatigue_score' in fatigue_df.columns:
                avg_fatigue = fatigue_df['fatigue_score'].mean()
                max_fatigue = fatigue_df['fatigue_score'].max()
                min_fatigue = fatigue_df['fatigue_score'].min()
                summary += f"FATIGUE_AVG: {avg_fatigue:.2f}\n"
                summary += f"FATIGUE_MAX: {max_fatigue:.2f}\n"
                summary += f"FATIGUE_MIN: {min_fatigue:.2f}\n"
        
        if 'fairness_after' in results:
            fairness_df = results['fairness_after']
            summary += f"FAIRNESS_RECORDS: {len(fairness_df)}\n"
            if 'night_ratio' in fairness_df.columns:
                night_avg = fairness_df['night_ratio'].mean()
                night_std = fairness_df['night_ratio'].std()
                summary += f"NIGHT_RATIO_AVG: {night_avg:.3f}\n"
                summary += f"NIGHT_RATIO_STD: {night_std:.3f}\n"
        
        summary += "\n"
        return summary
    
    def _generate_trend_analysis(self, long_df: pd.DataFrame, results: Dict, months: int) -> str:
        """時系列データ推移の生成"""
        trend = "SECTION: TIME_SERIES_DATA\n" + "-"*40 + "\n"
        
        # 月別集計の準備
        if 'ds' in long_df.columns:
            long_df_copy = long_df.copy()
            long_df_copy['month'] = pd.to_datetime(long_df_copy['ds']).dt.to_period('M')
            
            # 月別基本統計（機械読み取り可能形式）
            trend += "SUBSECTION: MONTHLY_BASIC_STATS\n"
            monthly_stats = long_df_copy.groupby('month').agg({
                'staff': 'nunique',
                'ds': 'nunique'
            }).reset_index()
            monthly_stats.columns = ['month', 'unique_staff', 'unique_days']
            
            for _, row in monthly_stats.iterrows():
                trend += f"MONTH:{row['month']}|STAFF:{row['unique_staff']}|DAYS:{row['unique_days']}\n"
            
            # 職種別月別統計（CSV風データ形式）
            if 'role' in long_df_copy.columns:
                trend += "\nSUBSECTION: MONTHLY_ROLE_RECORDS\n"
                role_monthly = long_df_copy.groupby(['month', 'role']).size().reset_index(name='record_count')
                for _, row in role_monthly.iterrows():
                    trend += f"MONTH:{row['month']}|ROLE:{row['role']}|RECORDS:{row['record_count']}\n"
            
            # 月別勤務コード分布（CSV風データ形式）
            if 'code' in long_df_copy.columns:
                trend += "\nSUBSECTION: MONTHLY_WORK_CODE_DISTRIBUTION\n"
                code_monthly = long_df_copy.groupby(['month', 'code']).size().reset_index(name='count')
                for _, row in code_monthly.iterrows():
                    trend += f"MONTH:{row['month']}|CODE:{row['code']}|COUNT:{row['count']}\n"
        
        trend += "\n"
        return trend
    
    def _generate_staff_analysis(self, long_df: pd.DataFrame, results: Dict) -> str:
        """職員別データ集計"""
        analysis = "SECTION: STAFF_INDIVIDUAL_DATA\n" + "-"*40 + "\n"
        
        if 'staff' not in long_df.columns:
            return analysis + "NO_STAFF_DATA\n\n"
        
        # 全職員の基本統計（機械読み取り可能形式）
        staff_summary = long_df.groupby('staff').agg({
            'ds': 'nunique',  # 勤務日数
        }).reset_index()
        staff_summary.columns = ['staff', 'work_days']
        
        analysis += "SUBSECTION: STAFF_BASIC_STATS\n"
        for _, row in staff_summary.iterrows():
            analysis += f"STAFF:{row['staff']}|WORK_DAYS:{row['work_days']}\n"
        
        # 職種別統計（構造化形式）
        if 'role' in long_df.columns:
            role_stats = long_df.groupby(['staff', 'role']).size().reset_index(name='role_records')
            analysis += "\nSUBSECTION: STAFF_ROLE_RECORDS\n"
            for _, row in role_stats.iterrows():
                analysis += f"STAFF:{row['staff']}|ROLE:{row['role']}|RECORDS:{row['role_records']}\n"
        
        # 勤務コード別統計（構造化形式）
        if 'code' in long_df.columns:
            code_stats = long_df.groupby(['staff', 'code']).size().reset_index(name='code_count')
            analysis += "\nSUBSECTION: STAFF_WORK_CODE_COUNT\n"
            for _, row in code_stats.iterrows():
                analysis += f"STAFF:{row['staff']}|CODE:{row['code']}|COUNT:{row['code_count']}\n"
        
        # 分析結果との結合（構造化形式）
        if 'fatigue_score' in results:
            fatigue_df = results['fatigue_score']
            analysis += "\nSUBSECTION: STAFF_FATIGUE_SCORES\n"
            if 'staff' in fatigue_df.columns and 'fatigue_score' in fatigue_df.columns:
                for _, row in fatigue_df.iterrows():
                    analysis += f"STAFF:{row['staff']}|FATIGUE_SCORE:{row['fatigue_score']:.2f}\n"
            elif fatigue_df.index.name == 'staff' or 'staff' in str(fatigue_df.index):
                for staff, score in fatigue_df['fatigue_score'].items():
                    analysis += f"STAFF:{staff}|FATIGUE_SCORE:{score:.2f}\n"
        
        if 'fairness_after' in results:
            fairness_df = results['fairness_after']
            analysis += "\nSUBSECTION: STAFF_FAIRNESS_DATA\n"
            if 'staff' in fairness_df.columns:
                for _, row in fairness_df.iterrows():
                    night_ratio = row.get('night_ratio', 'N/A')
                    unfairness = row.get('unfairness_score', 'N/A')
                    analysis += f"STAFF:{row['staff']}|NIGHT_RATIO:{night_ratio}|UNFAIRNESS_SCORE:{unfairness}\n"
        
        return analysis + "\n"
    
    def _generate_organizational_health(self, long_df: pd.DataFrame, results: Dict) -> str:
        """各種分析結果の統合データ"""
        health = "SECTION: ANALYSIS_RESULTS_INTEGRATION\n" + "-"*40 + "\n"
        
        # 不足・過剰分析の統計値（構造化形式）
        if 'shortage_summary' in results:
            shortage_df = results['shortage_summary']
            health += "SUBSECTION: SHORTAGE_STATISTICS\n"
            if 'lack' in shortage_df.columns:
                total_shortage = shortage_df['lack'].sum()
                max_shortage = shortage_df['lack'].max()
                min_shortage = shortage_df['lack'].min()
                avg_shortage = shortage_df['lack'].mean()
                health += f"SHORTAGE_TOTAL:{total_shortage:.1f}\n"
                health += f"SHORTAGE_MAX:{max_shortage:.1f}\n"
                health += f"SHORTAGE_MIN:{min_shortage:.1f}\n"
                health += f"SHORTAGE_AVG:{avg_shortage:.1f}\n"
            
            if 'excess' in shortage_df.columns:
                total_excess = shortage_df['excess'].sum()
                max_excess = shortage_df['excess'].max()
                min_excess = shortage_df['excess'].min()
                avg_excess = shortage_df['excess'].mean()
                health += f"EXCESS_TOTAL:{total_excess:.1f}\n"
                health += f"EXCESS_MAX:{max_excess:.1f}\n"
                health += f"EXCESS_MIN:{min_excess:.1f}\n"
                health += f"EXCESS_AVG:{avg_excess:.1f}\n"
        
        # 疲労度分析統計（構造化形式）
        if 'fatigue_score' in results:
            fatigue_df = results['fatigue_score']
            health += "\nSUBSECTION: FATIGUE_STATISTICS\n"
            if 'fatigue_score' in fatigue_df.columns:
                health += f"FATIGUE_MAX:{fatigue_df['fatigue_score'].max():.2f}\n"
                health += f"FATIGUE_MIN:{fatigue_df['fatigue_score'].min():.2f}\n"
                health += f"FATIGUE_AVG:{fatigue_df['fatigue_score'].mean():.2f}\n"
                health += f"FATIGUE_STD:{fatigue_df['fatigue_score'].std():.2f}\n"
                health += f"FATIGUE_MEDIAN:{fatigue_df['fatigue_score'].median():.2f}\n"
        
        # 公平性分析統計（構造化形式）
        if 'fairness_after' in results:
            fairness_df = results['fairness_after']
            health += "\nSUBSECTION: FAIRNESS_STATISTICS\n"
            if 'night_ratio' in fairness_df.columns:
                health += f"NIGHT_RATIO_MAX:{fairness_df['night_ratio'].max():.3f}\n"
                health += f"NIGHT_RATIO_MIN:{fairness_df['night_ratio'].min():.3f}\n"
                health += f"NIGHT_RATIO_AVG:{fairness_df['night_ratio'].mean():.3f}\n"
                health += f"NIGHT_RATIO_STD:{fairness_df['night_ratio'].std():.3f}\n"
            
            if 'unfairness_score' in fairness_df.columns:
                health += f"UNFAIRNESS_MAX:{fairness_df['unfairness_score'].max():.3f}\n"
                health += f"UNFAIRNESS_MIN:{fairness_df['unfairness_score'].min():.3f}\n"
                health += f"UNFAIRNESS_AVG:{fairness_df['unfairness_score'].mean():.3f}\n"
                health += f"UNFAIRNESS_STD:{fairness_df['unfairness_score'].std():.3f}\n"
        
        return health + "\n"
    
    def _generate_detailed_breakdown(self, long_df: pd.DataFrame, results: Dict) -> str:
        """詳細データ分解"""
        detailed = "SECTION: DETAILED_DATA_BREAKDOWN\n" + "-"*40 + "\n"
        
        # 時間帯別集計（構造化形式）
        if 'ds' in long_df.columns:
            long_df_copy = long_df.copy()
            long_df_copy['hour'] = pd.to_datetime(long_df_copy['ds']).dt.hour
            hour_stats = long_df_copy.groupby('hour').size().reset_index(name='record_count')
            
            detailed += "SUBSECTION: HOURLY_RECORD_COUNT\n"
            for _, row in hour_stats.iterrows():
                detailed += f"HOUR:{row['hour']:02d}|RECORDS:{row['record_count']}\n"
        
        # 曜日別集計（構造化形式）
        if 'ds' in long_df.columns:
            long_df_copy['weekday'] = pd.to_datetime(long_df_copy['ds']).dt.day_name()
            weekday_stats = long_df_copy.groupby('weekday').size().reset_index(name='record_count')
            
            detailed += "\nSUBSECTION: WEEKDAY_RECORD_COUNT\n"
            for _, row in weekday_stats.iterrows():
                detailed += f"WEEKDAY:{row['weekday']}|RECORDS:{row['record_count']}\n"
        
        # 職種×雇用形態のクロス集計（構造化形式）
        if 'role' in long_df.columns and 'employment' in long_df.columns:
            cross_tab = long_df.groupby(['role', 'employment']).size().reset_index(name='count')
            detailed += "\nSUBSECTION: ROLE_EMPLOYMENT_CROSS_TAB\n"
            for _, row in cross_tab.iterrows():
                detailed += f"ROLE:{row['role']}|EMPLOYMENT:{row['employment']}|COUNT:{row['count']}\n"
        
        return detailed + "\n"
    
    


def generate_comprehensive_report(long_df: pd.DataFrame, 
                                analysis_results: Dict[str, pd.DataFrame],
                                output_dir: Path) -> Path:
    """
    包括的レポートを生成する便利関数
    
    Args:
        long_df: シフトデータ
        analysis_results: 各種分析結果
        output_dir: 出力ディレクトリ
    
    Returns:
        生成されたレポートファイルのパス
    """
    generator = ComprehensiveReportGenerator(output_dir)
    return generator.generate_comprehensive_report(long_df, analysis_results)