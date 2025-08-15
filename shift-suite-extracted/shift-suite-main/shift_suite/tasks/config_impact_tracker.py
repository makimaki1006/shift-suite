"""
設定変更の影響範囲追跡システム

このモジュールは設定変更が及ぼす影響を分析・追跡します：
- 変更前後の設定値の差分分析
- 影響を受ける機能・モジュールの特定
- 変更による計算結果への影響予測
- 設定変更履歴の管理
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum

from .config_manager import ConfigManager, FacilityConfig
from .constants import (
    DEFAULT_SLOT_MINUTES,
    SLOT_HOURS,
    WAGE_RATES,
    COST_PARAMETERS,
    STATISTICAL_THRESHOLDS,
    FATIGUE_PARAMETERS
)

log = logging.getLogger(__name__)


class ImpactLevel(Enum):
    """影響レベル"""
    LOW = "low"          # 軽微な影響（表示のみなど）
    MEDIUM = "medium"    # 中程度の影響（分析結果に影響）
    HIGH = "high"        # 重大な影響（計算ロジックに直接影響）
    CRITICAL = "critical" # 致命的な影響（システム動作に影響）


@dataclass
class ConfigChange:
    """設定変更情報"""
    timestamp: str
    facility_id: str
    section: str  # time, wage, cost, statistical, fatigue, custom
    field: str
    old_value: Any
    new_value: Any
    changed_by: str = "system"


@dataclass
class ImpactAnalysis:
    """影響分析結果"""
    change: ConfigChange
    impact_level: ImpactLevel
    affected_modules: List[str]
    affected_functions: List[str]
    calculation_impact: str
    recommendations: List[str]
    requires_reprocessing: bool = False


class ConfigImpactTracker:
    """設定変更影響追跡システム"""
    
    # 設定項目と影響を受けるモジュールのマッピング
    IMPACT_MAP = {
        'time.slot_minutes': {
            'modules': ['shortage', 'heatmap', 'fatigue', 'cost_benefit', 'daily_cost'],
            'functions': ['gen_labels', 'slots_to_hours', 'calculate_daily_cost'],
            'level': ImpactLevel.CRITICAL,
            'calculation_impact': 'スロット時間変換、時間集計、コスト計算に直接影響'
        },
        'time.night_start_hour': {
            'modules': ['fatigue', 'fairness', 'blueprint_analyzer'],
            'functions': ['is_night_shift_time', '_is_night', 'calculate_night_ratio'],
            'level': ImpactLevel.HIGH,
            'calculation_impact': '夜勤判定、疲労度計算、公平性分析に影響'
        },
        'time.night_end_hour': {
            'modules': ['fatigue', 'fairness', 'blueprint_analyzer'],
            'functions': ['is_night_shift_time', '_is_night', 'calculate_night_ratio'],
            'level': ImpactLevel.HIGH,
            'calculation_impact': '夜勤判定、疲労度計算、公平性分析に影響'
        },
        'wage.regular_staff': {
            'modules': ['daily_cost', 'cost_benefit', 'shortage'],
            'functions': ['calculate_daily_cost', 'estimated_excess_cost'],
            'level': ImpactLevel.MEDIUM,
            'calculation_impact': '人件費計算、コスト分析に影響'
        },
        'wage.temporary_staff': {
            'modules': ['daily_cost', 'cost_benefit', 'shortage'],
            'functions': ['calculate_daily_cost', 'estimated_lack_cost_if_temporary_staff'],
            'level': ImpactLevel.MEDIUM,
            'calculation_impact': '派遣スタッフコスト、不足時コスト計算に影響'
        },
        'wage.night_differential': {
            'modules': ['daily_cost', 'cost_benefit'],
            'functions': ['calculate_daily_cost', 'calculate_night_premium'],
            'level': ImpactLevel.MEDIUM,
            'calculation_impact': '夜勤手当、夜間コスト計算に影響'
        },
        'cost.penalty_per_shortage_hour': {
            'modules': ['shortage', 'cost_benefit'],
            'functions': ['estimated_lack_penalty_cost', 'calculate_shortage_penalty'],
            'level': ImpactLevel.MEDIUM,
            'calculation_impact': '不足時ペナルティコスト計算に影響'
        },
        'statistical.confidence_level': {
            'modules': ['enhanced_blueprint_analyzer', 'statistical_analysis'],
            'functions': ['statistical_test', 'confidence_interval'],
            'level': ImpactLevel.LOW,
            'calculation_impact': '統計的検定、信頼区間計算に影響'
        },
        'statistical.significance_alpha': {
            'modules': ['enhanced_blueprint_analyzer', 'statistical_analysis'],
            'functions': ['statistical_test', 'p_value_comparison'],
            'level': ImpactLevel.LOW,
            'calculation_impact': '統計的有意性判定に影響'
        },
        'fatigue.min_rest_hours': {
            'modules': ['fatigue', 'rest_time_analyzer'],
            'functions': ['analyze_rest_time', 'calculate_rest_penalty'],
            'level': ImpactLevel.HIGH,
            'calculation_impact': '休憩時間分析、疲労度計算に直接影響'
        },
        'fatigue.night_shift_threshold': {
            'modules': ['fatigue', 'blueprint_analyzer'],
            'functions': ['detect_night_shift_pattern', 'analyze_fatigue_risk'],
            'level': ImpactLevel.MEDIUM,
            'calculation_impact': '夜勤パターン検出、疲労リスク評価に影響'
        }
    }
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or ConfigManager()
        self.change_history: List[ConfigChange] = []
        self.history_file = Path("shift_suite/config/change_history.json")
        self._load_history()
    
    def _load_history(self):
        """変更履歴を読み込み"""
        if self.history_file.exists():
            try:
                with self.history_file.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.change_history = [
                        ConfigChange(**item) for item in data
                    ]
            except Exception as e:
                log.warning(f"変更履歴の読み込みに失敗: {e}")
    
    def _save_history(self):
        """変更履歴を保存"""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with self.history_file.open('w', encoding='utf-8') as f:
                data = [asdict(change) for change in self.change_history]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error(f"変更履歴の保存に失敗: {e}")
    
    def analyze_config_change(
        self,
        facility_id: str,
        old_config: FacilityConfig,
        new_config: FacilityConfig,
        changed_by: str = "user"
    ) -> List[ImpactAnalysis]:
        """設定変更の影響を分析"""
        analyses = []
        changes = self._detect_changes(old_config, new_config)
        
        for change in changes:
            change.facility_id = facility_id
            change.changed_by = changed_by
            change.timestamp = datetime.now().isoformat()
            
            # 変更履歴に記録
            self.change_history.append(change)
            
            # 影響分析を実行
            analysis = self._analyze_impact(change)
            analyses.append(analysis)
        
        self._save_history()
        return analyses
    
    def _detect_changes(
        self,
        old_config: FacilityConfig,
        new_config: FacilityConfig
    ) -> List[ConfigChange]:
        """設定の変更を検出"""
        changes = []
        
        # 各セクションの変更を検出
        sections = {
            'time': (asdict(old_config.time), asdict(new_config.time)),
            'wage': (asdict(old_config.wage), asdict(new_config.wage)),
            'cost': (asdict(old_config.cost), asdict(new_config.cost)),
            'statistical': (asdict(old_config.statistical), asdict(new_config.statistical)),
            'fatigue': (asdict(old_config.fatigue), asdict(new_config.fatigue)),
            'custom': (old_config.custom, new_config.custom)
        }
        
        for section_name, (old_section, new_section) in sections.items():
            section_changes = self._compare_dicts(section_name, old_section, new_section)
            changes.extend(section_changes)
        
        return changes
    
    def _compare_dicts(
        self,
        section: str,
        old_dict: Dict[str, Any],
        new_dict: Dict[str, Any]
    ) -> List[ConfigChange]:
        """辞書の差分を検出"""
        changes = []
        all_keys = set(old_dict.keys()) | set(new_dict.keys())
        
        for key in all_keys:
            old_value = old_dict.get(key)
            new_value = new_dict.get(key)
            
            if old_value != new_value:
                changes.append(ConfigChange(
                    timestamp="",  # 後で設定
                    facility_id="",  # 後で設定
                    section=section,
                    field=key,
                    old_value=old_value,
                    new_value=new_value
                ))
        
        return changes
    
    def _analyze_impact(self, change: ConfigChange) -> ImpactAnalysis:
        """単一の変更に対する影響分析"""
        impact_key = f"{change.section}.{change.field}"
        
        if impact_key in self.IMPACT_MAP:
            impact_info = self.IMPACT_MAP[impact_key]
            
            recommendations = self._generate_recommendations(change, impact_info)
            requires_reprocessing = self._check_reprocessing_need(change, impact_info)
            
            return ImpactAnalysis(
                change=change,
                impact_level=impact_info['level'],
                affected_modules=impact_info['modules'],
                affected_functions=impact_info['functions'],
                calculation_impact=impact_info['calculation_impact'],
                recommendations=recommendations,
                requires_reprocessing=requires_reprocessing
            )
        else:
            # 未知の設定項目の場合
            return ImpactAnalysis(
                change=change,
                impact_level=ImpactLevel.LOW,
                affected_modules=[],
                affected_functions=[],
                calculation_impact="影響範囲は未知です",
                recommendations=["設定変更後に結果を確認してください"],
                requires_reprocessing=False
            )
    
    def _generate_recommendations(
        self,
        change: ConfigChange,
        impact_info: Dict[str, Any]
    ) -> List[str]:
        """推奨事項を生成"""
        recommendations = []
        
        # 影響レベルに応じた推奨事項
        if impact_info['level'] == ImpactLevel.CRITICAL:
            recommendations.extend([
                "この変更はシステム全体に重大な影響を与えます",
                "変更前に必ずバックアップを作成してください",
                "変更後は全てのデータを再処理することを強く推奨します",
                "テスト環境での十分な検証を行ってください"
            ])
        elif impact_info['level'] == ImpactLevel.HIGH:
            recommendations.extend([
                "この変更は主要な計算結果に影響します",
                "変更後は関連データの再処理を推奨します",
                "結果の妥当性を確認してください"
            ])
        elif impact_info['level'] == ImpactLevel.MEDIUM:
            recommendations.extend([
                "この変更は一部の計算結果に影響する可能性があります",
                "変更後は結果を確認することを推奨します"
            ])
        
        # 特定の設定項目に応じた推奨事項
        if change.field == 'slot_minutes':
            recommendations.append("スロット時間の変更は過去データとの互換性に影響します")
            recommendations.append("既存の時間ラベルとの整合性を確認してください")
        
        if 'night' in change.field.lower():
            recommendations.append("夜勤時間帯の変更は疲労度分析と公平性分析に影響します")
            recommendations.append("労働基準法との整合性を確認してください")
        
        if 'wage' in change.section or 'cost' in change.section:
            recommendations.append("コスト関連の変更は予算計画に影響する可能性があります")
        
        return recommendations
    
    def _check_reprocessing_need(
        self,
        change: ConfigChange,
        impact_info: Dict[str, Any]
    ) -> bool:
        """再処理が必要かどうかを判定"""
        # CRITICAL または HIGH レベルの変更は再処理が必要
        if impact_info['level'] in [ImpactLevel.CRITICAL, ImpactLevel.HIGH]:
            return True
        
        # 特定の設定項目は再処理が必要
        reprocessing_required_fields = {
            'slot_minutes', 'night_start_hour', 'night_end_hour',
            'min_rest_hours', 'regular_staff', 'temporary_staff'
        }
        
        if change.field in reprocessing_required_fields:
            return True
        
        return False
    
    def get_change_history(
        self,
        facility_id: Optional[str] = None,
        days: int = 30
    ) -> List[ConfigChange]:
        """変更履歴を取得"""
        from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        from_date = from_date.replace(day=from_date.day - days)
        
        filtered_history = []
        for change in self.change_history:
            try:
                change_date = datetime.fromisoformat(change.timestamp)
                if change_date >= from_date:
                    if facility_id is None or change.facility_id == facility_id:
                        filtered_history.append(change)
            except ValueError:
                continue
        
        return sorted(filtered_history, key=lambda x: x.timestamp, reverse=True)
    
    def generate_impact_report(
        self,
        analyses: List[ImpactAnalysis]
    ) -> str:
        """影響分析レポートを生成"""
        if not analyses:
            return "設定変更はありません。"
        
        report_lines = ["# 設定変更影響分析レポート\n"]
        
        # サマリー
        critical_count = sum(1 for a in analyses if a.impact_level == ImpactLevel.CRITICAL)
        high_count = sum(1 for a in analyses if a.impact_level == ImpactLevel.HIGH)
        medium_count = sum(1 for a in analyses if a.impact_level == ImpactLevel.MEDIUM)
        
        report_lines.extend([
            "## サマリー",
            f"- 重要度 CRITICAL: {critical_count}件",
            f"- 重要度 HIGH: {high_count}件",
            f"- 重要度 MEDIUM: {medium_count}件",
            f"- 合計変更: {len(analyses)}件\n"
        ])
        
        # 詳細分析
        report_lines.append("## 詳細分析\n")
        
        for i, analysis in enumerate(analyses, 1):
            change = analysis.change
            report_lines.extend([
                f"### {i}. {change.section}.{change.field} ({analysis.impact_level.value.upper()})",
                f"- **変更内容**: `{change.old_value}` → `{change.new_value}`",
                f"- **影響モジュール**: {', '.join(analysis.affected_modules)}",
                f"- **影響する関数**: {', '.join(analysis.affected_functions)}",
                f"- **計算への影響**: {analysis.calculation_impact}",
                f"- **再処理必要**: {'はい' if analysis.requires_reprocessing else 'いいえ'}",
                ""
            ])
            
            if analysis.recommendations:
                report_lines.append("**推奨事項**:")
                for rec in analysis.recommendations:
                    report_lines.append(f"  - {rec}")
                report_lines.append("")
        
        return "\n".join(report_lines)
    
    def get_affected_facilities(self, change_type: str) -> Set[str]:
        """特定の変更タイプの影響を受ける施設を取得"""
        affected = set()
        for change in self.change_history:
            if f"{change.section}.{change.field}" == change_type:
                affected.add(change.facility_id)
        return affected
    
    def cleanup_old_history(self, days: int = 90):
        """古い変更履歴をクリーンアップ"""
        cutoff_date = datetime.now().replace(day=datetime.now().day - days)
        
        old_count = len(self.change_history)
        self.change_history = [
            change for change in self.change_history
            if datetime.fromisoformat(change.timestamp) >= cutoff_date
        ]
        
        removed_count = old_count - len(self.change_history)
        if removed_count > 0:
            log.info(f"{removed_count}件の古い変更履歴を削除しました")
            self._save_history()


def create_impact_tracker(config_manager: Optional[ConfigManager] = None) -> ConfigImpactTracker:
    """影響追跡システムのインスタンスを作成"""
    return ConfigImpactTracker(config_manager)