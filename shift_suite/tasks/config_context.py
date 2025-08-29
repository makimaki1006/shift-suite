"""
設定コンテキスト管理
スレッドセーフな動的設定値の管理を提供
"""

import threading
import logging
from typing import Optional

log = logging.getLogger(__name__)

class ConfigContext:
    """
    スレッドローカルな設定コンテキスト
    
    各スレッド（リクエスト）ごとに異なる設定値を保持可能。
    Streamlitのマルチユーザー環境でも安全に動作。
    """
    _local = threading.local()
    _default_slot_minutes = 30  # デフォルト値
    
    @classmethod
    def set_slot_minutes(cls, minutes: int) -> None:
        """
        現在のスレッドのスロット時間を設定
        
        Args:
            minutes: スロット時間（分）。5-120の範囲を推奨
        """
        if not isinstance(minutes, (int, float)):
            raise ValueError(f"スロット時間は数値である必要があります: {minutes}")
        
        if minutes <= 0:
            raise ValueError(f"スロット時間は正の値である必要があります: {minutes}")
        
        if minutes > 120:
            log.warning(f"スロット時間が異常に大きい値です: {minutes}分")
        
        cls._local.slot_minutes = int(minutes)
        log.info(f"ConfigContext: スロット時間を{minutes}分に設定しました")
    
    @classmethod
    def get_slot_minutes(cls) -> int:
        """
        現在のスレッドのスロット時間を取得
        
        Returns:
            スロット時間（分）
        """
        # スレッドローカルに値がない場合はデフォルト値を返す
        minutes = getattr(cls._local, 'slot_minutes', None)
        
        if minutes is None:
            # 設定ファイルから取得を試みる
            try:
                from .config_loader import get_setting
                minutes = get_setting('time_settings.slot_minutes', cls._default_slot_minutes)
            except ImportError:
                minutes = cls._default_slot_minutes
            except Exception as e:
                log.debug(f"設定ファイルからの取得に失敗: {e}")
                minutes = cls._default_slot_minutes
        
        return int(minutes)
    
    @classmethod
    def get_slot_hours(cls) -> float:
        """
        現在のスレッドのスロット時間を時間単位で取得
        
        Returns:
            スロット時間（時間）
        """
        return cls.get_slot_minutes() / 60.0
    
    @classmethod
    def reset(cls) -> None:
        """
        現在のスレッドの設定をリセット
        
        テストやクリーンアップ時に使用
        """
        if hasattr(cls._local, 'slot_minutes'):
            delattr(cls._local, 'slot_minutes')
            log.debug("ConfigContext: スロット時間設定をリセットしました")
    
    @classmethod
    def is_set(cls) -> bool:
        """
        現在のスレッドに設定値が存在するか確認
        
        Returns:
            設定されている場合True
        """
        return hasattr(cls._local, 'slot_minutes')
    
    @classmethod
    def get_info(cls) -> dict:
        """
        現在の設定情報を取得（デバッグ用）
        
        Returns:
            設定情報の辞書
        """
        return {
            'slot_minutes': cls.get_slot_minutes(),
            'slot_hours': cls.get_slot_hours(),
            'is_set': cls.is_set(),
            'thread_id': threading.current_thread().ident
        }

# グローバルインスタンス（シングルトン的に使用）
_global_context = ConfigContext()

# 便利な関数として公開
def set_slot_minutes(minutes: int) -> None:
    """スロット時間を設定"""
    return _global_context.set_slot_minutes(minutes)

def get_slot_minutes() -> int:
    """スロット時間を取得"""
    return _global_context.get_slot_minutes()

def get_slot_hours() -> float:
    """スロット時間を時間単位で取得"""
    return _global_context.get_slot_hours()

def reset_context() -> None:
    """コンテキストをリセット"""
    return _global_context.reset()

def context_info() -> dict:
    """コンテキスト情報を取得"""
    return _global_context.get_info()