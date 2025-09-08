"""
疎結合な洞察検出サービス
既存システムを変更せずに、外部から洞察検出を実行
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import json
from datetime import datetime
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml

logger = logging.getLogger(__name__)


class InsightDetectionService:
    """
    スタンドアロンの洞察検出サービス
    既存システムには一切手を加えずに動作
    """
    
    def __init__(self):
        """洞察検出サービスの初期化"""
        self.logger = logging.getLogger(__name__)
        self.plugins: List[InsightPlugin] = []
        self.hooks = {}  # フック機能の初期化
        self.config = {
            'parallel_execution': False,
            'max_workers': 4
        }
        
        # デフォルトプラグインの登録
        # 注意: EmploymentConstraintPluginは意図的に除外
        # （データ構造が不適合のため）
        self.register_plugin(EmploymentConstraintPlugin())  # 無効化済み
        self.register_plugin(TimeMismatchPlugin())
        self.register_plugin(WorkloadImbalancePlugin())
        self.register_plugin(FatigueRiskPlugin())
        self.register_plugin(CostAnomalyPlugin())
        self.register_plugin(FairnessPlugin())
        
        # 現実性検証の閾値
        self.REALISTIC_HOURS_MIN = 50    # 月50時間未満は少なすぎ
        self.REALISTIC_HOURS_MAX = 250   # 月250時間超は多すぎ
        self.REALISTIC_DAILY_MAX = 12    # 日12時間超は異常
        
    def _load_config(self, config_path: Optional[Path]) -> Dict:
        """設定ファイルを読み込み"""
        if config_path and config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix == '.yaml':
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        
        # デフォルト設定
        return {
            'enabled_plugins': ['all'],
            'output_format': ['json', 'html', 'csv'],
            'auto_detect': True,
            'parallel_execution': True,
            'max_workers': 4,
            'thresholds': {
                'cost_waste': 10,
                'workload_imbalance': 2.0,
                'fatigue_hours': 200
            }
        }
    
    def _load_plugins(self):
        """プラグインを動的にロード"""
        # 基本プラグインを登録
        self.register_plugin(EmploymentConstraintPlugin())
        self.register_plugin(TimeMismatchPlugin())
        self.register_plugin(WorkloadImbalancePlugin())
        self.register_plugin(FatigueRiskPlugin())
        self.register_plugin(CostAnomalyPlugin())
        self.register_plugin(FairnessPlugin())
        
        # カスタムプラグインディレクトリから動的ロード
        plugin_dir = Path(__file__).parent / 'insight_plugins'
        if plugin_dir.exists():
            for plugin_file in plugin_dir.glob('*.py'):
                try:
                    # 動的インポート（実装は省略）
                    pass
                except Exception as e:
                    logger.warning(f"プラグイン {plugin_file} のロード失敗: {e}")
    
    def register_plugin(self, plugin: 'InsightPlugin'):
        """プラグインを登録"""
        self.plugins.append(plugin)
        logger.info(f"プラグイン登録: {plugin.name}")
    
    def register_hook(self, event: str, callback: Callable):
        """イベントフックを登録"""
        if event not in self.hooks:
            self.hooks[event] = []
        self.hooks[event].append(callback)
    
    def _trigger_hook(self, event: str, data: Any):
        """フックをトリガー"""
        if event in self.hooks:
            for callback in self.hooks[event]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"フック実行エラー ({event}): {e}")
    
    def analyze_directory(self, analysis_dir: Path) -> 'InsightReport':
        """
        分析ディレクトリから洞察を検出（非侵襲的）
        
        Args:
            analysis_dir: 分析結果が格納されたディレクトリ
            
        Returns:
            洞察レポート
        """
        logger.info(f"洞察検出開始: {analysis_dir}")
        
        # 必要なファイルを読み込み
        data_context = self._load_analysis_data(analysis_dir)
        
        if not data_context:
            logger.warning("分析データが見つかりません")
            return InsightReport(insights=[], metadata={})
        
        # 検出開始をフック
        self._trigger_hook('detection_started', data_context)
        
        all_insights = []
        
        if self.config['parallel_execution']:
            # 並列実行
            with ThreadPoolExecutor(max_workers=self.config['max_workers']) as executor:
                futures = {
                    executor.submit(plugin.detect, data_context): plugin
                    for plugin in self.plugins
                    if self._is_plugin_enabled(plugin)
                }
                
                for future in as_completed(futures):
                    plugin = futures[future]
                    try:
                        insights = future.result(timeout=30)
                        all_insights.extend(insights)
                        logger.info(f"{plugin.name}: {len(insights)}個の洞察を検出")
                    except Exception as e:
                        logger.error(f"{plugin.name} でエラー: {e}")
        else:
            # 順次実行
            for plugin in self.plugins:
                if self._is_plugin_enabled(plugin):
                    try:
                        insights = plugin.detect(data_context)
                        all_insights.extend(insights)
                        logger.info(f"{plugin.name}: {len(insights)}個の洞察を検出")
                    except Exception as e:
                        logger.error(f"{plugin.name} でエラー: {e}")
        
        # 現実性検証でフィルタリング
        validated_insights = []
        for insight in all_insights:
            if self._validate_insight_realism(insight):
                validated_insights.append(insight)
            else:
                logger.warning(f"非現実的な洞察を除外: {insight.title}")
        
        # レポート生成
        report = InsightReport(
            insights=validated_insights,
            metadata={
                'analysis_dir': str(analysis_dir),
                'detection_time': datetime.now().isoformat(),
                'plugin_count': len(self.plugins),
                'total_insights': len(validated_insights),
                'filtered_count': len(all_insights) - len(validated_insights)
            }
        )
        
        # 検出完了をフック
        self._trigger_hook('detection_completed', report)
        
        # レポート保存
        self._save_report(report, analysis_dir)
        
        return report
    
    def _load_analysis_data(self, analysis_dir: Path) -> Optional[Dict]:
        """分析データを読み込み（既存ファイルをそのまま利用）"""
        data_context = {}
        
        # 必須ファイル
        required_files = {
            'intermediate_data': 'intermediate_data.parquet',
            'shortage_role': 'shortage_role_summary.parquet',
            'shortage_employment': 'shortage_employment_summary.parquet'
        }
        
        for key, filename in required_files.items():
            file_path = analysis_dir / filename
            if file_path.exists():
                try:
                    data_context[key] = pd.read_parquet(file_path)
                except Exception as e:
                    logger.warning(f"{filename} の読み込み失敗: {e}")
        
        # オプションファイル
        optional_files = {
            'need_data': 'need_per_date_slot.parquet',
            'meta': 'heatmap.meta.json'
        }
        
        for key, filename in optional_files.items():
            file_path = analysis_dir / filename
            if file_path.exists():
                try:
                    if filename.endswith('.json'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data_context[key] = json.load(f)
                    else:
                        data_context[key] = pd.read_parquet(file_path)
                except Exception:
                    pass
        
        return data_context if data_context else None
    
    def _is_plugin_enabled(self, plugin: 'InsightPlugin') -> bool:
        """プラグインが有効か判定"""
        enabled = self.config.get('enabled_plugins', ['all'])
        if 'all' in enabled:
            return True
        return plugin.name in enabled
    
    def _save_report(self, report: 'InsightReport', output_dir: Path):
        """レポートを保存"""
        output_formats = self.config.get('output_format', ['json'])
        
        if 'json' in output_formats:
            json_path = output_dir / 'insights_detected.json'
            report.save_json(json_path)
            logger.info(f"JSONレポート保存: {json_path}")
        
        if 'html' in output_formats:
            html_path = output_dir / 'insights_report.html'
            report.save_html(html_path)
            logger.info(f"HTMLレポート保存: {html_path}")
        
        if 'csv' in output_formats:
            csv_path = output_dir / 'insights_table.csv'
            report.save_csv(csv_path)
            logger.info(f"CSVレポート保存: {csv_path}")

    def _validate_insight_realism(self, insight: 'Insight') -> bool:
        """
        洞察の現実性を検証
        
        非現実的な値を検出してログに記録し、
        必要に応じて洞察を除外する
        """
        # 時間関連の検証
        if 'hours' in insight.evidence:
            hours = insight.evidence['hours']
            if not (self.REALISTIC_HOURS_MIN <= hours <= self.REALISTIC_HOURS_MAX):
                self.logger.warning(
                    f"非現実的な時間を検出: {hours}h/月 "
                    f"(プラグイン: {insight.plugin}, タイトル: {insight.title})"
                )
                return False
                
        if 'avg_hours' in insight.evidence:
            avg_hours = insight.evidence['avg_hours']
            if avg_hours > self.REALISTIC_HOURS_MAX:
                self.logger.error(
                    f"非現実的な平均時間: {avg_hours}h/月 "
                    f"(プラグイン: {insight.plugin})"
                )
                return False
                
        # 財務影響の検証（1億円超は要確認）
        if insight.impact > 10000:
            self.logger.warning(
                f"異常に大きい財務影響: {insight.impact}万円/月 "
                f"(プラグイン: {insight.plugin})"
            )
            
        return True


class InsightPlugin(ABC):
    """洞察検出プラグインの基底クラス"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.enabled = True
    
    @abstractmethod
    def detect(self, data_context: Dict) -> List['Insight']:
        """
        洞察を検出
        
        Args:
            data_context: 分析データのコンテキスト
            
        Returns:
            検出された洞察のリスト
        """
        pass


@dataclass
class Insight:
    """検出された洞察"""
    plugin: str
    severity: str  # critical, high, medium, low
    category: str
    title: str
    description: str
    evidence: Dict[str, Any]
    impact: Optional[float] = None
    recommendation: Optional[str] = None
    confidence: float = 0.8


class InsightReport:
    """洞察レポート"""
    
    def __init__(self, insights: List[Insight], metadata: Dict):
        self.insights = insights
        self.metadata = metadata
        self._sort_by_severity()
    
    def _sort_by_severity(self):
        """重要度でソート"""
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        self.insights.sort(key=lambda x: (severity_order.get(x.severity, 99), -x.confidence))
    
    def get_summary(self) -> Dict:
        """サマリーを取得"""
        severity_counts = {}
        for insight in self.insights:
            severity_counts[insight.severity] = severity_counts.get(insight.severity, 0) + 1
        
        total_impact = sum(i.impact for i in self.insights if i.impact)
        
        return {
            'total': len(self.insights),
            'by_severity': severity_counts,
            'financial_impact': total_impact,
            'top_insights': self.insights[:5]
        }
    
    def save_json(self, path: Path):
        """JSON形式で保存"""
        data = {
            'metadata': self.metadata,
            'summary': self.get_summary(),
            'insights': [
                {
                    'plugin': i.plugin,
                    'severity': i.severity,
                    'category': i.category,
                    'title': i.title,
                    'description': i.description,
                    'evidence': i.evidence,
                    'impact': i.impact,
                    'recommendation': i.recommendation,
                    'confidence': i.confidence
                }
                for i in self.insights
            ]
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    def save_html(self, path: Path):
        """HTML形式で保存"""
        html = self._generate_html()
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def save_csv(self, path: Path):
        """CSV形式で保存"""
        import csv
        
        with open(path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'severity', 'category', 'title', 'description', 
                'impact', 'recommendation', 'confidence', 'plugin'
            ])
            writer.writeheader()
            
            for insight in self.insights:
                writer.writerow({
                    'severity': insight.severity,
                    'category': insight.category,
                    'title': insight.title,
                    'description': insight.description,
                    'impact': insight.impact,
                    'recommendation': insight.recommendation,
                    'confidence': insight.confidence,
                    'plugin': insight.plugin
                })
    
    def _generate_html(self) -> str:
        """HTMLレポートを生成"""
        summary = self.get_summary()
        
        html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>洞察検出レポート</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0; }}
        .metric {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #333; }}
        .insight {{ background: white; border-left: 4px solid #667eea; padding: 15px; margin: 15px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .critical {{ border-left-color: #dc2626; }}
        .high {{ border-left-color: #ea580c; }}
        .medium {{ border-left-color: #ca8a04; }}
        .low {{ border-left-color: #16a34a; }}
        .badge {{ display: inline-block; padding: 3px 10px; border-radius: 15px; font-size: 0.8em; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 洞察検出レポート</h1>
        <p>生成日時: {self.metadata.get('detection_time', '')}</p>
    </div>
    
    <div class="summary">
        <div class="metric">
            <div class="metric-value">{summary['total']}</div>
            <div>検出された洞察</div>
        </div>
        <div class="metric">
            <div class="metric-value">{summary['by_severity'].get('critical', 0)}</div>
            <div>緊急対応</div>
        </div>
        <div class="metric">
            <div class="metric-value">{summary['by_severity'].get('high', 0)}</div>
            <div>高優先度</div>
        </div>
        <div class="metric">
            <div class="metric-value">{summary['financial_impact']:.0f}万円</div>
            <div>財務影響</div>
        </div>
    </div>
    
    <h2>検出された洞察</h2>
"""
        
        for insight in self.insights[:20]:  # 上位20個
            severity_class = insight.severity
            html += f"""
    <div class="insight {severity_class}">
        <h3>
            <span class="badge" style="background: {'#dc2626' if insight.severity == 'critical' else '#ea580c' if insight.severity == 'high' else '#ca8a04' if insight.severity == 'medium' else '#16a34a'}; color: white;">
                {insight.severity.upper()}
            </span>
            {insight.title}
        </h3>
        <p>{insight.description}</p>
        {f'<p><strong>財務影響:</strong> {insight.impact:.1f}万円/月</p>' if insight.impact else ''}
        {f'<p><strong>推奨アクション:</strong> {insight.recommendation}</p>' if insight.recommendation else ''}
        <p style="font-size: 0.9em; color: #666;">検出: {insight.plugin} | 確信度: {insight.confidence*100:.0f}%</p>
    </div>
"""
        
        html += """
</body>
</html>
"""
        return html


# =====================================
# プラグイン実装例
# =====================================

class EmploymentConstraintPlugin(InsightPlugin):
    """雇用契約制約を検出"""
    
    def detect(self, data_context: Dict) -> List[Insight]:
        """
        雇用契約制約の検出
        
        注意: intermediate_data.parquetはシフト実績データであり、
        雇用契約の最低保証時間分析には適さないため、
        この分析は無効化されています。
        """
        insights = []
        
        # この分析は現在のデータ構造では適切でないため無効化
        # 理由:
        # 1. intermediate_data.parquetはシフト実績データ
        # 2. 雇用契約の最低保証時間は別途契約データが必要
        # 3. 現在の計算では非現実的な結果（月2000時間超）が発生
        
        return insights


class TimeMismatchPlugin(InsightPlugin):
    """時間帯ミスマッチを検出"""
    
    def detect(self, data_context: Dict) -> List[Insight]:
        insights = []
        
        if 'intermediate_data' not in data_context:
            return insights
        
        df = data_context['intermediate_data']
        
        if 'slot' in df.columns:
            slot_counts = df.groupby('slot').size()
            
            morning = slot_counts[12:20].sum() if len(slot_counts) > 20 else 0
            afternoon = slot_counts[28:36].sum() if len(slot_counts) > 36 else 0
            
            if afternoon > morning * 1.5 and morning > 0:
                excess = afternoon - morning
                impact = excess * 0.5 * 2000 / 10000
                
                insights.append(Insight(
                    plugin=self.name,
                    severity='high',
                    category='efficiency',
                    title="朝の不足と午後の過剰",
                    description=f"朝に比べて午後に{excess}スロット分の過剰配置",
                    evidence={'morning': morning, 'afternoon': afternoon},
                    impact=impact,
                    recommendation="シフトパターンの見直し",
                    confidence=0.9
                ))
        
        return insights


class WorkloadImbalancePlugin(InsightPlugin):
    """作業負荷の不均衡を検出"""
    
    def detect(self, data_context: Dict) -> List[Insight]:
        insights = []
        
        if 'intermediate_data' not in data_context:
            return insights
        
        df = data_context['intermediate_data']
        
        if 'staff' in df.columns:
            staff_loads = df.groupby('staff').size()
            mean_load = staff_loads.mean()
            std_load = staff_loads.std()
            
            for staff, load in staff_loads.items():
                if load > mean_load + 2 * std_load:
                    insights.append(Insight(
                        plugin=self.name,
                        severity='critical' if load > mean_load * 3 else 'high',
                        category='risk',
                        title=f"{staff}の過負荷",
                        description=f"勤務時間が平均の{load/mean_load:.1f}倍",
                        evidence={'staff': staff, 'hours': load * 0.5},
                        impact=None,
                        recommendation="負荷分散とローテーション導入",
                        confidence=0.95
                    ))
        
        return insights


class FatigueRiskPlugin(InsightPlugin):
    """疲労リスクを検出"""
    
    def detect(self, data_context: Dict) -> List[Insight]:
        insights = []
        
        if 'intermediate_data' not in data_context:
            return insights
        
        df = data_context['intermediate_data']
        
        if 'staff' in df.columns:
            staff_hours = df.groupby('staff').size() * 0.5
            
            for staff, hours in staff_hours.items():
                if hours > 200:
                    insights.append(Insight(
                        plugin=self.name,
                        severity='critical',
                        category='risk',
                        title=f"{staff}の疲労蓄積リスク",
                        description=f"月{hours:.0f}時間勤務で離職リスク高",
                        evidence={'staff': staff, 'hours': hours},
                        impact=100,  # 採用コスト
                        recommendation="即座に休暇付与と負荷軽減",
                        confidence=0.9
                    ))
        
        return insights


class CostAnomalyPlugin(InsightPlugin):
    """コスト異常を検出"""
    
    def detect(self, data_context: Dict) -> List[Insight]:
        insights = []
        
        if 'intermediate_data' not in data_context:
            return insights
        
        df = data_context['intermediate_data']
        
        if 'ds' in df.columns:
            df['weekday'] = pd.to_datetime(df['ds']).dt.dayofweek
            weekday_counts = df.groupby('weekday').size()
            
            avg_count = weekday_counts.mean()
            
            for day, count in weekday_counts.items():
                if count > avg_count * 1.3:
                    excess = count - avg_count
                    impact = excess * 0.5 * 2000 * 4 / 10000
                    
                    day_names = ['月', '火', '水', '木', '金', '土', '日']
                    
                    insights.append(Insight(
                        plugin=self.name,
                        severity='high' if impact > 20 else 'medium',
                        category='anomaly',
                        title=f"{day_names[day]}曜日の過剰配置",
                        description=f"平均より{excess:.0f}スロット多い配置",
                        evidence={'weekday': day, 'excess': excess},
                        impact=impact,
                        recommendation="配置理由の調査と適正化",
                        confidence=0.85
                    ))
        
        return insights


class FairnessPlugin(InsightPlugin):
    """公平性問題を検出"""
    
    def detect(self, data_context: Dict) -> List[Insight]:
        insights = []
        
        if 'intermediate_data' not in data_context:
            return insights
        
        df = data_context['intermediate_data']
        
        if 'staff' in df.columns:
            staff_loads = df.groupby('staff').size()
            
            # ジニ係数計算
            sorted_loads = np.sort(staff_loads.values)
            n = len(sorted_loads)
            cumsum = np.cumsum(sorted_loads)
            gini = (2 * np.sum((np.arange(1, n + 1)) * sorted_loads)) / (n * cumsum[-1]) - (n + 1) / n
            
            if gini > 0.3:
                min_staff = staff_loads.idxmin()
                max_staff = staff_loads.idxmax()
                ratio = staff_loads[max_staff] / staff_loads[min_staff]
                
                insights.append(Insight(
                    plugin=self.name,
                    severity='high' if ratio > 3 else 'medium',
                    category='fairness',
                    title="シフト配分の不公平",
                    description=f"スタッフ間で{ratio:.1f}倍の負荷差",
                    evidence={'gini': gini, 'min_staff': min_staff, 'max_staff': max_staff},
                    impact=None,
                    recommendation="配分アルゴリズムの見直し",
                    confidence=0.85
                ))
        
        return insights


# =====================================
# 使用例
# =====================================

def run_insight_detection(analysis_dir: Path):
    """
    スタンドアロンで洞察検出を実行
    
    使用例:
        from pathlib import Path
        from insight_detection_service import run_insight_detection
        
        # 既存の分析結果から洞察を検出
        analysis_dir = Path("output/analysis_20240101")
        report = run_insight_detection(analysis_dir)
    """
    
    # サービスを初期化
    service = InsightDetectionService()
    
    # カスタムフックを登録（オプション）
    def on_detection_completed(report):
        print(f"検出完了: {len(report.insights)}個の洞察")
        
    service.register_hook('detection_completed', on_detection_completed)
    
    # 洞察を検出
    report = service.analyze_directory(analysis_dir)
    
    # サマリーを表示
    summary = report.get_summary()
    print(f"合計: {summary['total']}個の洞察")
    print(f"財務影響: {summary['financial_impact']:.0f}万円/月")
    
    return report


if __name__ == "__main__":
    # テスト実行
    import sys
    if len(sys.argv) > 1:
        analysis_dir = Path(sys.argv[1])
        if analysis_dir.exists():
            report = run_insight_detection(analysis_dir)
            print(f"レポートを保存しました: {analysis_dir}/insights_detected.json")