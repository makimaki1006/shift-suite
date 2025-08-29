"""
設定ファイル読み込みモジュール
堅牢な設定読み込みとデフォルト値管理を提供
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

log = logging.getLogger(__name__)

# デフォルト設定値（ハードコーディング回避のため辞書形式で管理）
DEFAULT_SETTINGS = {
    'time_settings': {
        'slot_minutes': 30,
        'night_start_hour': 22,
        'night_end_hour': 6,
        'early_morning_hour': 6
    },
    'wage_settings': {
        'regular_staff': {
            'default': 1500,
            'min': 1000,
            'max': 3000
        },
        'temporary_staff': {
            'default': 2200,
            'min': 1500,
            'max': 5000
        },
        'night_differential': 1.25,
        'overtime_multiplier': 1.25,
        'weekend_differential': 1.10
    },
    'cost_settings': {
        'recruit_cost_per_hire': 200000,
        'hiring_cost_once': 180000,
        'penalty_per_shortage_hour': 4000,
        'monthly_hours_fte': 160
    },
    'facility_types': {
        'day_care': {
            'name': 'デイサービス',
            'staff_ratio': 3.0,
            'max_capacity': 30,
            'operating_hours': 10,
            'max_need_per_slot': 3.0,
            'shortage_warning_ratio': 0.15
        },
        'residential': {
            'name': '入所施設',
            'staff_ratio': 3.0,
            'max_capacity': 100,
            'operating_hours': 24,
            'max_need_per_slot': 4.0,
            'shortage_warning_ratio': 0.20
        }
    },
    'statistical_thresholds': {
        'confidence_level': 0.95,
        'significance_alpha': 0.05,
        'correlation_threshold': 0.7,
        'synergy_high_threshold': 1.5,
        'synergy_low_threshold': 0.3
    }
}

class ConfigLoader:
    """設定ファイルローダークラス"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Args:
            config_path: 設定ファイルのパス（Noneの場合はデフォルトパスを使用）
        """
        if config_path is None:
            # デフォルトパスを複数試行
            possible_paths = [
                Path(__file__).parent.parent.parent / 'config' / 'facility_settings.yaml',
                Path('config') / 'facility_settings.yaml',
                Path.cwd() / 'config' / 'facility_settings.yaml',
            ]
            for path in possible_paths:
                if path.exists():
                    config_path = path
                    break
        
        self.config_path = config_path
        self._settings = None
        self._load_settings()
    
    def _load_settings(self) -> None:
        """設定ファイルを読み込む（エラー時はデフォルト値を使用）"""
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    file_settings = yaml.safe_load(f)
                    
                # デフォルト設定とマージ（ファイル設定を優先）
                self._settings = self._deep_merge(DEFAULT_SETTINGS.copy(), file_settings)
                log.info(f"設定ファイルを読み込みました: {self.config_path}")
                
            except Exception as e:
                log.error(f"設定ファイルの読み込みエラー: {e}")
                self._settings = DEFAULT_SETTINGS.copy()
                log.info("デフォルト設定を使用します")
        else:
            log.info(f"設定ファイルが見つかりません。デフォルト設定を使用します。")
            self._settings = DEFAULT_SETTINGS.copy()
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """辞書を再帰的にマージ（overrideの値を優先）"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        ドット記法でネストされた設定値を取得
        
        Args:
            key_path: 'wage_settings.regular_staff.default' のようなキーパス
            default: キーが存在しない場合のデフォルト値
            
        Returns:
            設定値またはデフォルト値
        """
        if self._settings is None:
            return default
            
        keys = key_path.split('.')
        value = self._settings
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_all(self) -> Dict[str, Any]:
        """全設定を取得"""
        return self._settings.copy() if self._settings else DEFAULT_SETTINGS.copy()
    
    def reload(self) -> None:
        """設定を再読み込み"""
        self._load_settings()
        log.info("設定を再読み込みしました")
    
    def update_runtime(self, key_path: str, value: Any) -> bool:
        """
        実行時に設定値を更新（ファイルには保存しない）
        
        Args:
            key_path: 更新するキーのパス
            value: 新しい値
            
        Returns:
            更新成功の可否
        """
        if self._settings is None:
            self._settings = DEFAULT_SETTINGS.copy()
        
        keys = key_path.split('.')
        target = self._settings
        
        # 最後のキー以外をたどる
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        # 最後のキーに値を設定
        if keys:
            target[keys[-1]] = value
            log.info(f"設定を実行時更新: {key_path} = {value}")
            return True
        
        return False

# グローバルインスタンス
_global_config = None

def get_config() -> ConfigLoader:
    """グローバル設定インスタンスを取得"""
    global _global_config
    if _global_config is None:
        _global_config = ConfigLoader()
    return _global_config

def get_setting(key_path: str, default: Any = None) -> Any:
    """設定値を簡単に取得するヘルパー関数"""
    return get_config().get(key_path, default)