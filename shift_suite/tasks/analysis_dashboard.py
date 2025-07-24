#!/usr/bin/env python3
"""
analysis_dashboard.py - 網羅的分析情報ダッシュボード
不足分析・最適化分析・Need分析の統合表示システム
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

class ComprehensiveAnalysisDashboard:
    """網羅的分析情報ダッシュボード"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.analysis_files = {}
        self.meta_info = {}
        self._scan_analysis_files()
    
    def _scan_analysis_files(self) -> None:
        """分析ファイルを自動検出・分類"""
        file_patterns = {
            # 基本データファイル
            'need_data': ['need_per_date_slot.parquet', 'need_*.parquet'],
            'heat_data': ['heat_*.parquet', 'heat_*.xlsx'],
            'staff_data': ['intermediate_data.parquet', 'long_*.parquet'],
            
            # 不足分析関連
            'shortage_time': ['shortage_time.parquet'],
            'shortage_role': ['shortage_role.parquet'],
            'shortage_ratio': ['shortage_ratio.parquet'],
            'shortage_freq': ['shortage_freq.parquet'],
            'shortage_summary': ['shortage_weekday_timeslot_summary.parquet'],
            
            # 最適化分析関連
            'optimization': ['optimization_score_time.parquet', 'optimal_hire_plan.parquet'],
            'hire_plan': ['hire_plan_*.parquet', 'hiring_recommendations.parquet'],
            
            # メタデータ
            'meta': ['heatmap.meta.json', 'analysis.meta.json', '*.meta.json'],
            
            # その他分析結果
            'excess_data': ['excess_time.parquet', 'surplus_vs_need_time.parquet'],
            'leave_data': ['leave_analysis.csv', 'shortage_leave.csv'],
            'forecast': ['forecast_*.parquet', 'prediction_*.parquet']
        }
        
        for category, patterns in file_patterns.items():
            self.analysis_files[category] = []
            for pattern in patterns:
                if '*' in pattern:
                    # ワイルドカード検索
                    matches = list(self.output_dir.glob(pattern))
                    self.analysis_files[category].extend([f.name for f in matches if f.is_file()])
                else:
                    # 直接検索
                    file_path = self.output_dir / pattern
                    if file_path.exists():
                        self.analysis_files[category].append(pattern)
    
    def get_comprehensive_analysis_info(self) -> Dict[str, Any]:
        """網羅的な分析情報を取得"""
        info = {
            'scan_timestamp': datetime.now().isoformat(),
            'output_directory': str(self.output_dir),
            'file_inventory': self.analysis_files,
            'data_summaries': {},
            'analysis_status': {},
            'key_metrics': {},
            'recommendations': []
        }
        
        # 各カテゴリのデータサマリーを生成
        for category, files in self.analysis_files.items():
            if files:
                info['data_summaries'][category] = self._get_category_summary(category, files)
        
        # 分析状況の判定
        info['analysis_status'] = self._assess_analysis_completeness()
        
        # 主要メトリクスの計算
        info['key_metrics'] = self._calculate_key_metrics()
        
        # 推奨事項の生成
        info['recommendations'] = self._generate_recommendations()
        
        return info
    
    def _get_category_summary(self, category: str, files: List[str]) -> Dict[str, Any]:
        """カテゴリ別データサマリー"""
        summary = {
            'file_count': len(files),
            'files': files,
            'data_info': {},
            'last_modified': None,
            'size_info': {}
        }
        
        try:
            for file in files:
                file_path = self.output_dir / file
                if not file_path.exists():
                    continue
                    
                # ファイル情報
                stat = file_path.stat()
                summary['size_info'][file] = {
                    'size_mb': round(stat.st_size / (1024*1024), 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
                
                # データ内容の概要（parquetファイルのみ）
                if file.endswith('.parquet'):
                    try:
                        df = pd.read_parquet(file_path)
                        summary['data_info'][file] = {
                            'rows': len(df),
                            'columns': len(df.columns),
                            'column_names': list(df.columns)[:10],  # 最初の10列のみ
                            'data_types': df.dtypes.astype(str).to_dict(),
                            'memory_usage_mb': round(df.memory_usage(deep=True).sum() / (1024*1024), 2)
                        }
                        
                        # 数値データの統計
                        numeric_cols = df.select_dtypes(include=[np.number]).columns
                        if len(numeric_cols) > 0:
                            summary['data_info'][file]['numeric_summary'] = {
                                'mean': df[numeric_cols].mean().to_dict(),
                                'sum': df[numeric_cols].sum().to_dict(),
                                'max': df[numeric_cols].max().to_dict()
                            }
                    except Exception as e:
                        log.warning(f"データ読み込みエラー {file}: {e}")
                        summary['data_info'][file] = {'error': str(e)}
                
                # JSONファイルの処理
                elif file.endswith('.json'):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            json_data = json.load(f)
                            summary['data_info'][file] = {
                                'keys': list(json_data.keys()) if isinstance(json_data, dict) else 'non_dict',
                                'size': len(json_data) if isinstance(json_data, (dict, list)) else 1
                            }
                    except Exception as e:
                        summary['data_info'][file] = {'error': str(e)}
        
        except Exception as e:
            summary['error'] = str(e)
            log.error(f"カテゴリサマリー生成エラー {category}: {e}")
        
        return summary
    
    def _assess_analysis_completeness(self) -> Dict[str, Any]:
        """分析完了状況の評価"""
        status = {
            'overall_score': 0,
            'category_scores': {},
            'missing_files': [],
            'critical_issues': []
        }
        
        # 必須ファイルの定義
        required_files = {
            'need_data': {'weight': 20, 'files': ['need_per_date_slot.parquet']},
            'heat_data': {'weight': 15, 'files': ['heat_ALL.parquet', 'heat_ALL.xlsx']},
            'shortage_time': {'weight': 25, 'files': ['shortage_time.parquet']},
            'shortage_role': {'weight': 15, 'files': ['shortage_role.parquet']},
            'meta': {'weight': 10, 'files': ['heatmap.meta.json']},
            'staff_data': {'weight': 15, 'files': ['intermediate_data.parquet']}
        }
        
        total_weight = sum(req['weight'] for req in required_files.values())
        achieved_weight = 0
        
        for category, req_info in required_files.items():
            category_files = self.analysis_files.get(category, [])
            has_required = any(req_file in category_files for req_file in req_info['files'])
            
            if has_required:
                achieved_weight += req_info['weight']
                status['category_scores'][category] = 'complete'
            else:
                status['category_scores'][category] = 'missing'
                status['missing_files'].extend(req_info['files'])
        
        status['overall_score'] = round((achieved_weight / total_weight) * 100, 1)
        
        # 重要な問題の検出
        if status['overall_score'] < 70:
            status['critical_issues'].append('分析の完了率が70%未満です')
        
        if not self.analysis_files.get('need_data'):
            status['critical_issues'].append('Need基準データが見つかりません')
        
        if not self.analysis_files.get('shortage_time'):
            status['critical_issues'].append('時間別不足データが生成されていません')
        
        return status
    
    def _calculate_key_metrics(self) -> Dict[str, Any]:
        """主要メトリクスの計算"""
        metrics = {
            'total_shortage_hours': 0,
            'avg_daily_shortage': 0,
            'peak_shortage_timeslot': None,
            'role_shortage_distribution': {},
            'shortage_frequency': 0,
            'optimization_score': 0
        }
        
        try:
            # 不足時間データから計算
            shortage_file = self.output_dir / 'shortage_time.parquet'
            if shortage_file.exists():
                shortage_df = pd.read_parquet(shortage_file)
                
                # 総不足時間（30分単位 → 時間換算）
                metrics['total_shortage_hours'] = round(shortage_df.sum().sum() * 0.5, 1)
                
                # 平均日次不足
                if len(shortage_df.columns) > 0:
                    metrics['avg_daily_shortage'] = round(shortage_df.sum(axis=0).mean() * 0.5, 1)
                
                # ピーク不足時間帯
                timeslot_totals = shortage_df.sum(axis=1)
                if not timeslot_totals.empty:
                    peak_index = timeslot_totals.idxmax()
                    metrics['peak_shortage_timeslot'] = {
                        'timeslot': peak_index,
                        'shortage_hours': round(timeslot_totals[peak_index] * 0.5, 1)
                    }
                
                # 不足発生頻度
                shortage_occurrences = (shortage_df > 0).sum().sum()
                total_slots = shortage_df.shape[0] * shortage_df.shape[1]
                if total_slots > 0:
                    metrics['shortage_frequency'] = round(shortage_occurrences / total_slots * 100, 1)
            
            # 職種別不足分布
            shortage_role_file = self.output_dir / 'shortage_role.parquet'
            if shortage_role_file.exists():
                role_df = pd.read_parquet(shortage_role_file)
                if 'lack_h' in role_df.columns and 'role' in role_df.columns:
                    metrics['role_shortage_distribution'] = role_df.set_index('role')['lack_h'].to_dict()
            
            # 最適化スコア
            opt_file = self.output_dir / 'optimization_score_time.parquet'
            if opt_file.exists():
                opt_df = pd.read_parquet(opt_file) 
                if not opt_df.empty:
                    metrics['optimization_score'] = round(opt_df.mean().mean(), 2)
        
        except Exception as e:
            log.error(f"メトリクス計算エラー: {e}")
            metrics['calculation_error'] = str(e)
        
        return metrics
    
    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """推奨事項の生成"""
        recommendations = []
        
        # 分析完了状況に基づく推奨
        status = self._assess_analysis_completeness()
        if status['overall_score'] < 100:
            recommendations.append({
                'type': 'completion',
                'priority': 'high',
                'title': '分析の完了',
                'description': f"分析完了率: {status['overall_score']}% - 不足している分析を実行してください"
            })
        
        # メトリクスに基づく推奨
        metrics = self._calculate_key_metrics()
        if metrics.get('total_shortage_hours', 0) > 100:
            recommendations.append({
                'type': 'optimization',
                'priority': 'critical',
                'title': '深刻な人員不足',
                'description': f"総不足時間: {metrics['total_shortage_hours']}時間 - 緊急の人員補強が必要です"
            })
        
        if metrics.get('shortage_frequency', 0) > 30:
            recommendations.append({
                'type': 'scheduling',
                'priority': 'high', 
                'title': '頻繁な不足発生',
                'description': f"不足発生頻度: {metrics['shortage_frequency']}% - シフトパターンの見直しが必要です"
            })
        
        # ファイル不足に基づく推奨
        if not self.analysis_files.get('need_data'):
            recommendations.append({
                'type': 'data',
                'priority': 'critical',
                'title': 'Need基準データ不足',
                'description': 'need_per_date_slot.parquetが見つかりません - ヒートマップ分析を実行してください'
            })
        
        return recommendations
    
    def generate_analysis_report(self) -> str:
        """分析レポートのテキスト生成"""
        info = self.get_comprehensive_analysis_info()
        
        report = f"""
=== 網羅的分析情報レポート ===
生成日時: {info['scan_timestamp']}
分析ディレクトリ: {info['output_directory']}

【分析完了状況】
全体スコア: {info['analysis_status']['overall_score']}%
"""
        
        for category, score in info['analysis_status']['category_scores'].items():
            status_icon = "✅" if score == 'complete' else "❌"
            report += f"{status_icon} {category}: {score}\n"
        
        if info['analysis_status']['missing_files']:
            report += f"\n不足ファイル: {', '.join(info['analysis_status']['missing_files'])}\n"
        
        report += f"""
【主要メトリクス】
総不足時間: {info['key_metrics'].get('total_shortage_hours', 0)}時間
平均日次不足: {info['key_metrics'].get('avg_daily_shortage', 0)}時間
不足発生頻度: {info['key_metrics'].get('shortage_frequency', 0)}%
"""
        
        if info['key_metrics'].get('peak_shortage_timeslot'):
            peak = info['key_metrics']['peak_shortage_timeslot']
            report += f"ピーク不足時間帯: {peak['timeslot']} ({peak['shortage_hours']}時間)\n"
        
        report += "\n【推奨事項】\n"
        for i, rec in enumerate(info['recommendations'], 1):
            priority_icon = {"critical": "🚨", "high": "⚠️", "medium": "ℹ️"}.get(rec['priority'], "📌")
            report += f"{i}. {priority_icon} {rec['title']}: {rec['description']}\n"
        
        report += f"""
【ファイル一覧】
"""
        for category, files in info['file_inventory'].items():
            if files:
                report += f"{category}: {len(files)}個のファイル\n"
                for file in files[:3]:  # 最初の3つのみ表示
                    report += f"  - {file}\n"
                if len(files) > 3:
                    report += f"  ... および{len(files)-3}個のファイル\n"
        
        return report
    
    def export_analysis_info(self, output_file: str = "comprehensive_analysis_info.json") -> Path:
        """分析情報をJSONで出力"""
        info = self.get_comprehensive_analysis_info()
        output_path = self.output_dir / output_file
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        
        log.info(f"分析情報を出力しました: {output_path}")
        return output_path


# 便利な関数
def get_analysis_dashboard(output_dir: Path) -> ComprehensiveAnalysisDashboard:
    """分析ダッシュボードのインスタンスを取得"""
    return ComprehensiveAnalysisDashboard(output_dir)

def quick_analysis_check(output_dir: Path) -> Dict[str, Any]:
    """クイック分析チェック"""
    dashboard = ComprehensiveAnalysisDashboard(output_dir)
    return dashboard.get_comprehensive_analysis_info()

def generate_analysis_report_file(output_dir: Path, report_file: str = "analysis_report.txt") -> Path:
    """分析レポートファイルを生成"""
    dashboard = ComprehensiveAnalysisDashboard(output_dir)
    report = dashboard.generate_analysis_report()
    
    report_path = output_dir / report_file
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    log.info(f"分析レポートを生成しました: {report_path}")
    return report_path