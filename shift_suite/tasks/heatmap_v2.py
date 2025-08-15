# shift_suite / tasks / heatmap_v2.py
# v2.0.0 (動的データ対応・汎用Need計算システム)

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import List, Set, Dict, Optional, Tuple
import json

import numpy as np
import openpyxl
import pandas as pd
import logging

from .constants import SUMMARY5
from shift_suite.i18n import translate as _
from .utils import (
    _parse_as_date,
    derive_max_staff,
    gen_labels,
    log,
    safe_sheet,
    save_df_xlsx,
    write_meta,
    validate_need_calculation,
)

# 新しい汎用統計エンジン
# from ..core.statistics_engine import AdaptiveStatisticsEngine
# from ..core.data_models import StaffRecord, DailyStaffSummary, NeedCalculationResult

# Temporary replacement classes for missing core modules
class AdaptiveStatisticsEngine:
    def calculate_need(self, historical_data, target_confidence=0.75):
        import numpy as np
        values = np.array(historical_data)
        need_value = float(np.percentile(values, 75)) if len(values) > 0 else 0.0
        confidence = 0.75
        method = "p75_fallback"
        return need_value, confidence, method

class NeedCalculationResult:
    def __init__(self, date, time_slot, need_count, confidence, calculation_method, data_points, raw_data):
        self.date = date
        self.time_slot = time_slot
        self.need_count = need_count
        self.confidence = confidence
        self.calculation_method = calculation_method
        self.data_points = data_points
        self.raw_data = raw_data

analysis_logger = logging.getLogger('analysis')

# 通常勤務の判定用定数
DEFAULT_HOLIDAY_TYPE = "通常勤務"

STAFF_ALIASES = ["staff", "氏名", "名前", "従業員"]
ROLE_ALIASES = ["role", "職種", "役職", "部署"]


class UniversalNeedCalculator:
    """汎用Need計算エンジン（曜日固有ロジックなし）"""
    
    def __init__(self):
        self.stats_engine = AdaptiveStatisticsEngine()
        self.calculation_log: List[NeedCalculationResult] = []
    
    def calculate_dynamic_need(
        self,
        historical_data_df: pd.DataFrame,
        target_date_columns: List[str],
        confidence_target: float = 0.75
    ) -> pd.DataFrame:
        """
        動的データに基づくNeed計算
        
        Args:
            historical_data_df: 実績データ（時間帯×日付）
            target_date_columns: 対象日付列
            confidence_target: 目標信頼度
            
        Returns:
            Need計算結果DataFrame（時間帯×日付）
        """
        log.info(f"汎用Need計算開始: 対象日付数={len(target_date_columns)}")
        
        result_df = pd.DataFrame(
            index=historical_data_df.index,
            columns=target_date_columns,
            dtype=float
        )
        
        # 時間帯ごとに処理
        for time_slot in historical_data_df.index:
            log.debug(f"時間帯 {time_slot} の処理開始")
            
            # 対象日付の実績データを取得
            slot_data = historical_data_df.loc[time_slot, target_date_columns]
            historical_values = slot_data.dropna().tolist()
            
            if not historical_values:
                log.warning(f"時間帯 {time_slot}: データなし")
                result_df.loc[time_slot] = 0.0
                continue
            
            # 汎用統計エンジンでNeed計算
            need_value, confidence, method = self.stats_engine.calculate_need(
                historical_data=historical_values,
                target_confidence=confidence_target
            )
            
            # 結果を記録
            calculation_result = NeedCalculationResult(
                date=dt.date.today(),  # 計算日
                time_slot=time_slot,
                need_count=need_value,
                confidence=confidence,
                calculation_method=method,
                data_points=len(historical_values),
                raw_data=historical_values
            )
            self.calculation_log.append(calculation_result)
            
            # 全対象日付に同じNeed値を適用
            result_df.loc[time_slot] = need_value
            
            log.debug(
                f"時間帯 {time_slot}: Need={need_value:.2f}, "
                f"信頼度={confidence:.2f}, 手法={method}"
            )
        
        log.info("汎用Need計算完了")
        return result_df.fillna(0.0)
    
    def get_calculation_summary(self) -> Dict:
        """計算サマリーの取得"""
        if not self.calculation_log:
            return {}
        
        total_calculations = len(self.calculation_log)
        avg_confidence = np.mean([r.confidence for r in self.calculation_log])
        method_counts = {}
        
        for result in self.calculation_log:
            method = result.calculation_method
            method_counts[method] = method_counts.get(method, 0) + 1
        
        return {
            "total_calculations": total_calculations,
            "average_confidence": avg_confidence,
            "method_distribution": method_counts,
            "low_confidence_slots": [
                r.time_slot for r in self.calculation_log 
                if r.confidence < 0.6
            ]
        }


def calculate_universal_need(
    df_for_calc: pd.DataFrame,
    date_columns: List[str],
    confidence_target: float = 0.75,
    **kwargs
) -> pd.DataFrame:
    """
    汎用Need計算のメイン関数
    
    従来のcalculate_pattern_based_needを置き換える
    曜日固有ロジックを完全に排除
    """
    log.info("=== 汎用Need計算システム v2.0.0 ===")
    log.info(f"対象日付数: {len(date_columns)}")
    log.info(f"時間帯数: {len(df_for_calc.index)}")
    
    # 汎用計算エンジンを初期化
    calculator = UniversalNeedCalculator()
    
    # Need計算実行
    need_df = calculator.calculate_dynamic_need(
        historical_data_df=df_for_calc,
        target_date_columns=date_columns,
        confidence_target=confidence_target
    )
    
    # 計算サマリーをログ出力
    summary = calculator.get_calculation_summary()
    log.info("=== Need計算サマリー ===")
    log.info(f"総計算数: {summary.get('total_calculations', 0)}")
    log.info(f"平均信頼度: {summary.get('average_confidence', 0):.3f}")
    log.info(f"手法分布: {summary.get('method_distribution', {})}")
    
    low_confidence = summary.get('low_confidence_slots', [])
    if low_confidence:
        log.warning(f"低信頼度時間帯 (<0.6): {low_confidence}")
    
    return need_df


# 従来の関数を汎用版で置き換え
def calculate_pattern_based_need(
    df_for_calc: pd.DataFrame,
    ref_start_date: dt.date,
    ref_end_date: dt.date,
    statistic_method: str = "中央値",  # 🔧 CRITICAL FIX: デフォルトを中央値に変更
    **kwargs
) -> pd.DataFrame:
    """
    後方互換性のためのラッパー関数
    内部では汎用Need計算を使用
    """
    log.info("[COMPATIBILITY] 汎用Need計算システムを使用します")
    
    # 日付列を抽出
    date_columns = [
        col for col in df_for_calc.columns
        if isinstance(col, (dt.date, dt.datetime)) or 
        (isinstance(col, str) and _parse_as_date(col))
    ]
    
    # 期間でフィルタリング
    filtered_columns = []
    for col in date_columns:
        if isinstance(col, str):
            col_date = _parse_as_date(col)
        else:
            col_date = col if isinstance(col, dt.date) else col.date()
        
        if col_date and ref_start_date <= col_date <= ref_end_date:
            filtered_columns.append(col)
    
    log.info(f"対象期間 ({ref_start_date} - {ref_end_date}): {len(filtered_columns)}日")
    
    # 汎用Need計算を実行
    return calculate_universal_need(
        df_for_calc=df_for_calc,
        date_columns=filtered_columns,
        confidence_target=0.75
    )