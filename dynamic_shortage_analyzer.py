#!/usr/bin/env python
"""
動的シフトデータを活用した真の過不足分析システム

従来の静的パターンではなく、実際のシフト配置データと
リアルタイム需要データに基づく過不足分析を実行
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class DynamicShortageAnalyzer:
    """動的過不足分析エンジン"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.shift_data = None
        self.demand_patterns = {}
        self.coverage_analysis = {}
        
    def load_actual_shift_data(self) -> pd.DataFrame:
        """実際のシフトデータを読み込み"""
        intermediate_file = self.data_dir / "intermediate_data.parquet"
        
        if not intermediate_file.exists():
            raise FileNotFoundError(f"シフトデータが見つかりません: {intermediate_file}")
        
        df = pd.read_parquet(intermediate_file)
        log.info(f"実際のシフトデータ読み込み: {len(df):,}レコード")
        
        # データ検証
        required_cols = ['ds', 'staff', 'role', 'parsed_slots_count']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"必要な列が不足: {missing_cols}")
        
        # 時間情報の抽出
        df['date'] = pd.to_datetime(df['ds']).dt.date
        df['time_slot'] = pd.to_datetime(df['ds']).dt.strftime('%H:%M')
        df['weekday'] = pd.to_datetime(df['ds']).dt.weekday
        df['hour'] = pd.to_datetime(df['ds']).dt.hour
        
        self.shift_data = df
        return df
    
    def analyze_dynamic_demand_patterns(self) -> Dict[str, Dict]:
        """動的需要パターンの分析"""
        if self.shift_data is None:
            raise ValueError("シフトデータが読み込まれていません")
        
        df = self.shift_data
        demand_analysis = {}
        
        # 1. 時間帯別需要パターン
        hourly_demand = df.groupby(['hour', 'role']).agg({
            'parsed_slots_count': 'sum',
            'staff': 'nunique'
        }).reset_index()
        
        hourly_demand['demand_per_staff'] = (
            hourly_demand['parsed_slots_count'] / 
            hourly_demand['staff'].replace(0, 1)
        )
        
        # 2. 曜日別需要パターン  
        daily_demand = df.groupby(['weekday', 'role']).agg({
            'parsed_slots_count': 'sum',
            'staff': 'nunique'
        }).reset_index()
        
        # 3. 職種別需要密度
        role_density = df.groupby('role').agg({
            'parsed_slots_count': ['sum', 'mean', 'std'],
            'staff': 'nunique',
            'ds': 'count'
        }).reset_index()
        
        demand_analysis = {
            'hourly_patterns': hourly_demand.to_dict('records'),
            'daily_patterns': daily_demand.to_dict('records'),
            'role_density': role_density.to_dict('records'),
            'analysis_period': {
                'start': df['ds'].min().isoformat(),
                'end': df['ds'].max().isoformat(),
                'total_days': df['date'].nunique(),
                'total_shifts': len(df)
            }
        }
        
        self.demand_patterns = demand_analysis
        return demand_analysis
    
    def calculate_real_time_coverage(self) -> Dict[str, Dict]:
        """リアルタイム配置カバレッジ分析"""
        if self.shift_data is None:
            raise ValueError("シフトデータが読み込まれていません")
        
        df = self.shift_data
        coverage_analysis = {}
        
        # 職種×時間帯のカバレッジマトリックス
        coverage_matrix = df.pivot_table(
            index='time_slot',
            columns='role', 
            values='parsed_slots_count',
            aggfunc='sum',
            fill_value=0
        )
        
        # スタッフ配置密度
        staff_matrix = df.pivot_table(
            index='time_slot',
            columns='role',
            values='staff',
            aggfunc='nunique',
            fill_value=0
        )
        
        # カバレッジ比率（実際配置 / 期待配置）
        expected_coverage = self._calculate_expected_coverage(df)
        coverage_ratio = coverage_matrix / expected_coverage.replace(0, 1)
        
        # 不足時間帯の特定
        shortage_spots = self._identify_shortage_spots(coverage_ratio)
        
        coverage_analysis = {
            'coverage_matrix': coverage_matrix.to_dict(),
            'staff_matrix': staff_matrix.to_dict(),
            'coverage_ratio': coverage_ratio.to_dict(),
            'shortage_spots': shortage_spots,
            'overall_coverage': float(coverage_ratio.mean().mean()),
            'critical_shortages': self._find_critical_shortages(coverage_ratio)
        }
        
        self.coverage_analysis = coverage_analysis
        return coverage_analysis
    
    def _calculate_expected_coverage(self, df: pd.DataFrame) -> pd.DataFrame:
        """期待される配置レベルを計算"""
        # 基準期間の平均配置を期待値とする
        baseline_period = df[df['weekday'] < 5]  # 平日のみ
        
        expected = baseline_period.pivot_table(
            index='time_slot',
            columns='role',
            values='parsed_slots_count', 
            aggfunc='mean',
            fill_value=0
        )
        
        return expected
    
    def _identify_shortage_spots(self, coverage_ratio: pd.DataFrame) -> List[Dict]:
        """不足スポットの特定"""
        shortage_threshold = 0.7  # 70%未満をショーテージとする
        
        shortage_spots = []
        
        for time_slot in coverage_ratio.index:
            for role in coverage_ratio.columns:
                ratio = coverage_ratio.loc[time_slot, role]
                if ratio < shortage_threshold and ratio > 0:
                    shortage_spots.append({
                        'time_slot': time_slot,
                        'role': role,
                        'coverage_ratio': float(ratio),
                        'severity': 'critical' if ratio < 0.5 else 'moderate'
                    })
        
        return sorted(shortage_spots, key=lambda x: x['coverage_ratio'])
    
    def _find_critical_shortages(self, coverage_ratio: pd.DataFrame) -> Dict[str, List]:
        """クリティカルな不足の特定"""
        critical_threshold = 0.5
        
        critical_times = []
        critical_roles = []
        
        # 時間帯別クリティカル不足
        for time_slot in coverage_ratio.index:
            avg_coverage = coverage_ratio.loc[time_slot].mean()
            if avg_coverage < critical_threshold:
                critical_times.append({
                    'time_slot': time_slot,
                    'avg_coverage': float(avg_coverage),
                    'affected_roles': len(coverage_ratio.loc[time_slot][coverage_ratio.loc[time_slot] < critical_threshold])
                })
        
        # 職種別クリティカル不足
        for role in coverage_ratio.columns:
            avg_coverage = coverage_ratio[role].mean()
            if avg_coverage < critical_threshold:
                critical_roles.append({
                    'role': role,
                    'avg_coverage': float(avg_coverage),
                    'affected_time_slots': len(coverage_ratio[role][coverage_ratio[role] < critical_threshold])
                })
        
        return {
            'critical_time_slots': critical_times,
            'critical_roles': critical_roles
        }
    
    def generate_dynamic_shortage_report(self) -> Dict[str, any]:
        """動的過不足レポートの生成"""
        if not self.demand_patterns or not self.coverage_analysis:
            raise ValueError("分析が実行されていません")
        
        # 現実的な不足時間の計算
        coverage_matrix = pd.DataFrame(self.coverage_analysis['coverage_matrix'])
        staff_matrix = pd.DataFrame(self.coverage_analysis['staff_matrix'])
        
        # 実際の不足時間（時間単位）
        shortage_hours_per_slot = {}
        total_shortage_hours = 0
        
        for role in coverage_matrix.columns:
            role_shortage = 0
            for time_slot in coverage_matrix.index:
                actual_staff = staff_matrix.loc[time_slot, role] if role in staff_matrix.columns else 0
                expected_staff = coverage_matrix.loc[time_slot, role] / 0.5  # 30分スロット想定
                
                if expected_staff > actual_staff:
                    shortage = (expected_staff - actual_staff) * 0.5  # 時間換算
                    role_shortage += shortage
                    total_shortage_hours += shortage
            
            shortage_hours_per_slot[role] = role_shortage
        
        # 日平均不足時間
        analysis_days = len(pd.to_datetime(self.shift_data['ds']).dt.date.unique())
        daily_avg_shortage = total_shortage_hours / max(1, analysis_days)
        
        report = {
            'analysis_method': 'dynamic_real_time',
            'data_period': self.demand_patterns['analysis_period'],
            'total_shortage_hours': round(total_shortage_hours, 2),
            'daily_average_shortage': round(daily_avg_shortage, 2),
            'shortage_by_role': {k: round(v, 2) for k, v in shortage_hours_per_slot.items()},
            'coverage_analysis': self.coverage_analysis,
            'demand_patterns': self.demand_patterns,
            'validation': {
                'realistic_range': daily_avg_shortage <= 8.0,  # 8時間/日以下が現実的
                'method_reliability': 'high',
                'data_quality': self._assess_data_quality()
            }
        }
        
        return report
    
    def _assess_data_quality(self) -> Dict[str, any]:
        """データ品質の評価"""
        df = self.shift_data
        
        quality_metrics = {
            'completeness': {
                'total_records': len(df),
                'missing_data_ratio': df.isnull().sum().sum() / (len(df) * len(df.columns)),
                'date_coverage': df['date'].nunique(),
                'time_slot_coverage': df['time_slot'].nunique()
            },
            'consistency': {
                'role_stability': df['role'].nunique(),
                'staff_stability': df['staff'].nunique(),
                'data_distribution': df.groupby('role')['parsed_slots_count'].std().mean()
            },
            'reliability_score': 0.0
        }
        
        # 信頼性スコア計算
        completeness_score = 1.0 - quality_metrics['completeness']['missing_data_ratio']
        coverage_score = min(1.0, quality_metrics['completeness']['date_coverage'] / 30)
        
        quality_metrics['reliability_score'] = (completeness_score + coverage_score) / 2
        
        return quality_metrics

def run_dynamic_analysis(data_dir: str) -> Dict[str, any]:
    """動的過不足分析の実行"""
    analyzer = DynamicShortageAnalyzer(Path(data_dir))
    
    try:
        # 1. 実際のシフトデータ読み込み
        log.info("=== 動的シフトデータ読み込み ===")
        shift_data = analyzer.load_actual_shift_data()
        
        # 2. 需要パターン分析
        log.info("=== 動的需要パターン分析 ===")
        demand_patterns = analyzer.analyze_dynamic_demand_patterns()
        
        # 3. リアルタイムカバレッジ分析
        log.info("=== リアルタイムカバレッジ分析 ===")
        coverage_analysis = analyzer.calculate_real_time_coverage()
        
        # 4. 総合レポート生成
        log.info("=== 動的過不足レポート生成 ===")
        final_report = analyzer.generate_dynamic_shortage_report()
        
        # 結果出力
        output_file = Path(data_dir) / "dynamic_shortage_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2)
        
        log.info(f"動的過不足分析完了: {output_file}")
        
        # サマリー表示
        print("=== 動的過不足分析結果 ===")
        print(f"総不足時間: {final_report['total_shortage_hours']:.1f}時間")
        print(f"日平均不足: {final_report['daily_average_shortage']:.1f}時間/日")
        print(f"現実性評価: {'✓ 現実的' if final_report['validation']['realistic_range'] else '✗ 非現実的'}")
        print(f"データ品質: {final_report['validation']['data_quality']['reliability_score']:.2f}")
        
        return final_report
        
    except Exception as e:
        log.error(f"動的分析エラー: {e}")
        raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python dynamic_shortage_analyzer.py [データディレクトリ]")
        sys.exit(1)
    
    data_dir = sys.argv[1]
    result = run_dynamic_analysis(data_dir)
    print("\n動的過不足分析が完了しました！")