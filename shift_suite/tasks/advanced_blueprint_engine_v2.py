"""ShiftMindReaderを統合した、Blueprint-V2の中核エンジン"""
import logging
from typing import Dict, Any

import pandas as pd

from .advanced_blueprint_engine import AdvancedBlueprintEngine
from .shift_mind_reader import ShiftMindReader

log = logging.getLogger(__name__)


class AdvancedBlueprintEngineV2(AdvancedBlueprintEngine):
    """思考プロセス解読機能を追加したエンジン"""

    def __init__(self):
        super().__init__()
        self.mind_reader = ShiftMindReader()

    def run_full_blueprint_analysis(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """V2の全分析を実行する統合メソッド"""
        log.info("Blueprint-V2 フル分析を開始します...")

        mind_reader_results = self.mind_reader.read_creator_mind(long_df)

        # 将来的に既存分析も呼び出すことを想定し、辞書構造を維持する
        return {
            "mind_reading": mind_reader_results,
        }
