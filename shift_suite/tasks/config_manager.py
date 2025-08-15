"""
階層的設定管理システム

このモジュールは以下の優先順位で設定値を管理します:
1. 個別施設設定 (最高優先度)
2. 施設タイプ別設定
3. システムデフォルト設定 (constants.py)

使用例:
    config = ConfigManager('hospital_a')
    night_start = config.get_time_config('night_start_hour')
    wage_rates = config.get_wage_config()
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
import datetime as dt

from .constants import (
    DEFAULT_SLOT_MINUTES,
    SLOT_HOURS,
    NIGHT_START_TIME,
    NIGHT_END_TIME,
    NIGHT_START_HOUR,
    NIGHT_END_HOUR,
    EARLY_MORNING_THRESHOLD,
    WAGE_RATES,
    COST_PARAMETERS,
    STATISTICAL_THRESHOLDS,
    FATIGUE_PARAMETERS
)

log = logging.getLogger(__name__)


@dataclass
class TimeConfig:
    """時間関連設定"""
    slot_minutes: int = DEFAULT_SLOT_MINUTES
    slot_hours: float = SLOT_HOURS
    night_start_hour: int = NIGHT_START_HOUR
    night_end_hour: int = NIGHT_END_HOUR
    early_morning_hour: int = 6


@dataclass
class WageConfig:
    """賃金関連設定"""
    regular_staff: float = WAGE_RATES["regular_staff"]
    temporary_staff: float = WAGE_RATES["temporary_staff"]
    average_hourly_wage: float = WAGE_RATES["average_hourly_wage"]
    night_differential: float = WAGE_RATES["night_differential"]
    overtime_multiplier: float = WAGE_RATES["overtime_multiplier"]
    weekend_differential: float = WAGE_RATES["weekend_differential"]


@dataclass
class CostConfig:
    """コスト関連設定"""
    recruit_cost_per_hire: int = COST_PARAMETERS["recruit_cost_per_hire"]
    hiring_cost_once: int = COST_PARAMETERS["hiring_cost_once"]
    penalty_per_shortage_hour: int = COST_PARAMETERS["penalty_per_shortage_hour"]
    monthly_hours_fte: int = COST_PARAMETERS["monthly_hours_fte"]


@dataclass
class StatisticalConfig:
    """統計分析関連設定"""
    confidence_level: float = STATISTICAL_THRESHOLDS["confidence_level"]
    significance_alpha: float = STATISTICAL_THRESHOLDS["significance_alpha"]
    correlation_threshold: float = STATISTICAL_THRESHOLDS["correlation_threshold"]
    high_confidence_threshold: float = STATISTICAL_THRESHOLDS["high_confidence_threshold"]
    min_sample_size: int = STATISTICAL_THRESHOLDS["min_sample_size"]


@dataclass
class FatigueConfig:
    """疲労度・勤務評価設定"""
    min_rest_hours: int = FATIGUE_PARAMETERS["min_rest_hours"]
    night_shift_threshold: float = FATIGUE_PARAMETERS["night_shift_threshold"]
    early_morning_threshold: float = FATIGUE_PARAMETERS["early_morning_threshold"]
    fatigue_alert_threshold: float = FATIGUE_PARAMETERS["fatigue_alert_threshold"]
    consecutive_3_days_weight: float = FATIGUE_PARAMETERS["consecutive_3_days_weight"]
    consecutive_4_days_weight: float = FATIGUE_PARAMETERS["consecutive_4_days_weight"]
    consecutive_5_days_weight: float = FATIGUE_PARAMETERS["consecutive_5_days_weight"]


@dataclass
class FacilityConfig:
    """施設別総合設定"""
    facility_id: str
    facility_name: str
    facility_type: str
    time: TimeConfig
    wage: WageConfig
    cost: CostConfig
    statistical: StatisticalConfig
    fatigue: FatigueConfig
    custom: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom is None:
            self.custom = {}


class ConfigManager:
    """階層的設定管理マネージャー"""
    
    def __init__(
        self,
        facility_id: Optional[str] = None,
        config_dir: Optional[Union[str, Path]] = None
    ):
        self.facility_id = facility_id
        self.config_dir = Path(config_dir) if config_dir else Path("shift_suite/config")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self._default_config = self._create_default_config()
        self._facility_type_configs: Dict[str, Dict[str, Any]] = {}
        self._facility_configs: Dict[str, FacilityConfig] = {}
        
        self._load_all_configs()
        
    def _create_default_config(self) -> FacilityConfig:
        """デフォルト設定を作成"""
        return FacilityConfig(
            facility_id="default",
            facility_name="デフォルト設定",
            facility_type="general",
            time=TimeConfig(),
            wage=WageConfig(),
            cost=CostConfig(),
            statistical=StatisticalConfig(),
            fatigue=FatigueConfig()
        )
    
    def _load_all_configs(self):
        """全ての設定ファイルを読み込み"""
        # 施設タイプ別設定を読み込み
        facility_types_dir = self.config_dir / "facility_types"
        if facility_types_dir.exists():
            for config_file in facility_types_dir.glob("*.json"):
                facility_type = config_file.stem
                try:
                    with config_file.open('r', encoding='utf-8') as f:
                        self._facility_type_configs[facility_type] = json.load(f)
                        log.info(f"施設タイプ別設定を読み込み: {facility_type}")
                except Exception as e:
                    log.warning(f"施設タイプ設定読み込み失敗 {config_file}: {e}")
        
        # 個別施設設定を読み込み
        facilities_dir = self.config_dir / "facilities"
        if facilities_dir.exists():
            for config_file in facilities_dir.glob("*.json"):
                facility_id = config_file.stem
                try:
                    config = self._load_facility_config(config_file)
                    self._facility_configs[facility_id] = config
                    log.info(f"個別施設設定を読み込み: {facility_id}")
                except Exception as e:
                    log.warning(f"施設設定読み込み失敗 {config_file}: {e}")
    
    def _load_facility_config(self, config_file: Path) -> FacilityConfig:
        """個別施設設定を読み込み"""
        with config_file.open('r', encoding='utf-8') as f:
            data = json.load(f)
        
        facility_type = data.get('facility_type', 'general')
        
        # 階層的設定マージ: デフォルト → 施設タイプ → 個別施設
        merged_data = asdict(self._default_config)
        
        # 施設タイプ別設定をマージ
        if facility_type in self._facility_type_configs:
            merged_data = self._deep_merge(merged_data, self._facility_type_configs[facility_type])
        
        # 個別施設設定をマージ
        merged_data = self._deep_merge(merged_data, data)
        
        return FacilityConfig(
            facility_id=merged_data['facility_id'],
            facility_name=merged_data['facility_name'],
            facility_type=merged_data['facility_type'],
            time=TimeConfig(**merged_data['time']),
            wage=WageConfig(**merged_data['wage']),
            cost=CostConfig(**merged_data['cost']),
            statistical=StatisticalConfig(**merged_data['statistical']),
            fatigue=FatigueConfig(**merged_data['fatigue']),
            custom=merged_data.get('custom', {})
        )
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """辞書の深いマージ"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def get_config(self, facility_id: Optional[str] = None) -> FacilityConfig:
        """指定施設の設定を取得"""
        target_id = facility_id or self.facility_id
        
        if target_id and target_id in self._facility_configs:
            return self._facility_configs[target_id]
        
        return self._default_config
    
    def get_time_config(self, facility_id: Optional[str] = None) -> TimeConfig:
        """時間設定を取得"""
        return self.get_config(facility_id).time
    
    def get_wage_config(self, facility_id: Optional[str] = None) -> WageConfig:
        """賃金設定を取得"""
        return self.get_config(facility_id).wage
    
    def get_cost_config(self, facility_id: Optional[str] = None) -> CostConfig:
        """コスト設定を取得"""
        return self.get_config(facility_id).cost
    
    def get_statistical_config(self, facility_id: Optional[str] = None) -> StatisticalConfig:
        """統計分析設定を取得"""
        return self.get_config(facility_id).statistical
    
    def get_fatigue_config(self, facility_id: Optional[str] = None) -> FatigueConfig:
        """疲労度設定を取得"""
        return self.get_config(facility_id).fatigue
    
    def save_facility_config(self, config: FacilityConfig) -> Path:
        """個別施設設定を保存"""
        facilities_dir = self.config_dir / "facilities"
        facilities_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = facilities_dir / f"{config.facility_id}.json"
        
        # JSONシリアライズ可能な形式に変換
        data = asdict(config)
        
        with config_file.open('w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # キャッシュを更新
        self._facility_configs[config.facility_id] = config
        
        log.info(f"施設設定を保存: {config.facility_id} -> {config_file}")
        return config_file
    
    def create_facility_template(
        self,
        facility_type: str,
        template_config: Dict[str, Any]
    ) -> Path:
        """施設タイプ別テンプレートを作成"""
        facility_types_dir = self.config_dir / "facility_types"
        facility_types_dir.mkdir(parents=True, exist_ok=True)
        
        template_file = facility_types_dir / f"{facility_type}.json"
        
        with template_file.open('w', encoding='utf-8') as f:
            json.dump(template_config, f, ensure_ascii=False, indent=2)
        
        # キャッシュを更新
        self._facility_type_configs[facility_type] = template_config
        
        log.info(f"施設タイプテンプレートを作成: {facility_type} -> {template_file}")
        return template_file
    
    def list_facilities(self) -> Dict[str, str]:
        """登録済み施設一覧を取得"""
        return {
            facility_id: config.facility_name
            for facility_id, config in self._facility_configs.items()
        }
    
    def list_facility_types(self) -> List[str]:
        """利用可能な施設タイプ一覧を取得"""
        return list(self._facility_type_configs.keys())
    
    def validate_config(self, config: FacilityConfig) -> List[str]:
        """設定の妥当性チェック"""
        errors = []
        
        # 時間設定の妥当性チェック
        if config.time.slot_minutes <= 0:
            errors.append("slot_minutes must be positive")
        if not (0 <= config.time.night_start_hour <= 23):
            errors.append("night_start_hour must be 0-23")
        if not (0 <= config.time.night_end_hour <= 23):
            errors.append("night_end_hour must be 0-23")
        
        # 賃金設定の妥当性チェック
        if config.wage.regular_staff <= 0:
            errors.append("regular_staff wage must be positive")
        if config.wage.temporary_staff <= 0:
            errors.append("temporary_staff wage must be positive")
        if config.wage.night_differential < 1.0:
            errors.append("night_differential must be >= 1.0")
        
        # 統計設定の妥当性チェック
        if not (0 < config.statistical.confidence_level < 1):
            errors.append("confidence_level must be between 0 and 1")
        if not (0 < config.statistical.significance_alpha < 1):
            errors.append("significance_alpha must be between 0 and 1")
        
        return errors


# グローバルインスタンス（後方互換性のため）
_global_config_manager: Optional[ConfigManager] = None


def get_config_manager(
    facility_id: Optional[str] = None,
    config_dir: Optional[Union[str, Path]] = None
) -> ConfigManager:
    """設定マネージャーのインスタンスを取得"""
    global _global_config_manager
    
    if _global_config_manager is None or facility_id or config_dir:
        _global_config_manager = ConfigManager(facility_id, config_dir)
    
    return _global_config_manager


# 便利関数（後方互換性のため）
def get_time_config(facility_id: Optional[str] = None) -> TimeConfig:
    """時間設定を取得"""
    return get_config_manager().get_time_config(facility_id)


def get_wage_config(facility_id: Optional[str] = None) -> WageConfig:
    """賃金設定を取得"""
    return get_config_manager().get_wage_config(facility_id)


def get_cost_config(facility_id: Optional[str] = None) -> CostConfig:
    """コスト設定を取得"""
    return get_config_manager().get_cost_config(facility_id)


def get_statistical_config(facility_id: Optional[str] = None) -> StatisticalConfig:
    """統計分析設定を取得"""
    return get_config_manager().get_statistical_config(facility_id)


def get_fatigue_config(facility_id: Optional[str] = None) -> FatigueConfig:
    """疲労度設定を取得"""
    return get_config_manager().get_fatigue_config(facility_id)