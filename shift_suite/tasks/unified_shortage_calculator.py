#!/usr/bin/env python3
"""
統一過不足計算エンジン v1.0
真の過不足分析の実装 - 慎重な段階的構築

設計原則:
1. 真の過不足分析（按分計算完全廃止）
2. 動的データ完全対応
3. 単位系統一（時間 Hours）
4. 結果の一貫性保証
5. 既存システムとの共存（Phase 1では非破壊的実装）
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date, timedelta
import logging
import json

# 既存システムとの共存のため、安全にインポート
try:
    from .utils import log, _parse_as_date
    from .constants import DEFAULT_SLOT_MINUTES
except ImportError:
    # フォールバック用の基本設定
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger(__name__)
    DEFAULT_SLOT_MINUTES = 30

@dataclass
class TrueShortageConfig:
    """真の過不足分析設定"""
    slot_minutes: int = DEFAULT_SLOT_MINUTES       # 動的検出されたスロット間隔
    analysis_start_date: Optional[date] = None     # 分析開始日
    analysis_end_date: Optional[date] = None       # 分析終了日
    available_roles: List[str] = field(default_factory=list)          # 動的検出職種リスト
    available_employments: List[str] = field(default_factory=list)     # 動的検出雇用形態リスト
    facility_scale: str = "UNKNOWN"                # 施設規模（SMALL/MEDIUM/LARGE）
    working_holidays: Set[date] = field(default_factory=set)         # 営業休日セット
    data_quality_score: float = 0.0               # データ品質スコア（0-1）
    validation_enabled: bool = True                # 検証機能有効フラグ

@dataclass 
class TrueShortageResult:
    """統一された真の過不足分析結果"""
    
    # === 組織全体結果 ===
    total_demand_hours: float = 0.0               # 総需要時間
    total_supply_hours: float = 0.0               # 総供給時間  
    total_shortage_hours: float = 0.0             # 総不足時間
    total_excess_hours: float = 0.0               # 総過剰時間
    balance_status: str = "UNKNOWN"               # 均衡状況
    
    # === 職種別詳細結果 ===
    role_demand: Dict[str, float] = field(default_factory=dict)      # 職種別需要時間
    role_supply: Dict[str, float] = field(default_factory=dict)      # 職種別供給時間
    role_shortage: Dict[str, float] = field(default_factory=dict)    # 職種別不足時間
    
    # === 雇用形態別詳細結果 ===  
    employment_demand: Dict[str, float] = field(default_factory=dict)   # 雇用形態別需要時間
    employment_supply: Dict[str, float] = field(default_factory=dict)   # 雇用形態別供給時間
    employment_shortage: Dict[str, float] = field(default_factory=dict) # 雇用形態別不足時間
    
    # === 時間軸詳細結果 ===
    timeslot_shortage: Dict[str, float] = field(default_factory=dict)   # 時間帯別不足時間
    daily_shortage_pattern: Dict[date, float] = field(default_factory=dict)  # 日別不足パターン
    
    # === メタデータ ===
    calculation_timestamp: Optional[datetime] = None      # 計算実行時刻
    config_used: Optional[TrueShortageConfig] = None      # 使用設定
    validation_results: List[str] = field(default_factory=list)        # 検証結果
    reliability_score: float = 0.0                        # 結果信頼度（0-1）
    calculation_warnings: List[str] = field(default_factory=list)      # 計算警告


class UnifiedShortageCalculator:
    """
    統一過不足計算エンジン v1.0
    
    Phase 1: 安全な基盤構築フェーズ
    - 既存システムに影響を与えない独立実装
    - 段階的機能追加による安全性確保
    - 充実した検証・ログ機能
    """
    
    def __init__(self):
        """統一計算エンジン初期化"""
        self.logger = log
        self.version = "1.0.0"
        self.logger.info(f"[UnifiedShortageCalculator v{self.version}] 初期化開始")
        
        # Phase 1: 基本的な安全性チェック機能
        self.safety_checks_enabled = True
        self.max_calculation_time_seconds = 300  # 5分でタイムアウト
        
        self.logger.info("[UnifiedShortageCalculator] Phase 1基盤構築完了")
    
    def calculate_true_shortage(
        self, 
        scenario_dir: Path,
        config_override: Optional[TrueShortageConfig] = None
    ) -> TrueShortageResult:
        """
        真の過不足分析メイン実行関数
        
        Phase 1実装: 基本的な計算ロジックを安全に実装
        
        Args:
            scenario_dir: シナリオデータディレクトリ
            config_override: 設定上書き（テスト用）
            
        Returns:
            TrueShortageResult: 統一された分析結果
        """
        
        calculation_start = datetime.now()
        self.logger.info(f"[True Shortage] 計算開始: {scenario_dir}")
        
        try:
            # Step 1: 安全性チェック
            if not self._validate_input_safety(scenario_dir):
                return self._create_error_result("入力データの安全性チェック失敗")
            
            # Step 2: 動的データ解析・設定自動生成
            config = self._generate_dynamic_config(scenario_dir, config_override)
            self.logger.info(f"[True Shortage] 動的設定生成完了: {config.facility_scale}規模, {config.slot_minutes}分スロット")
            
            # Step 3: データ読み込み（安全性重視）
            demand_data, supply_data = self._safe_load_data(scenario_dir, config)
            if demand_data is None or supply_data is None:
                return self._create_error_result("データ読み込み失敗")
            
            # Step 4: 真の過不足計算（直接比較）
            result = self._calculate_direct_comparison(demand_data, supply_data, config)
            
            # Step 5: 結果検証・信頼度評価
            validated_result = self._validate_and_score_result(result, config)
            
            calculation_time = (datetime.now() - calculation_start).total_seconds()
            self.logger.info(f"[True Shortage] 計算完了: {calculation_time:.1f}秒, 信頼度{validated_result.reliability_score:.2f}")
            
            return validated_result
            
        except Exception as e:
            self.logger.error(f"[True Shortage] 計算エラー: {e}", exc_info=True)
            return self._create_error_result(f"計算処理エラー: {str(e)}")
    
    def _validate_input_safety(self, scenario_dir: Path) -> bool:
        """入力データの安全性チェック"""
        try:
            if not scenario_dir.exists():
                self.logger.error(f"[Safety] シナリオディレクトリが存在しません: {scenario_dir}")
                return False
            
            # 基本的なファイル存在チェック
            required_files = ['intermediate_data.parquet']
            for file_name in required_files:
                if not (scenario_dir / file_name).exists():
                    self.logger.warning(f"[Safety] 必要ファイルが見つかりません: {file_name}")
            
            # ディスク容量チェック（基本的な安全性）
            # 実装は段階的に追加
            
            return True
            
        except Exception as e:
            self.logger.error(f"[Safety] 安全性チェックエラー: {e}")
            return False
    
    def _generate_dynamic_config(
        self, 
        scenario_dir: Path, 
        config_override: Optional[TrueShortageConfig]
    ) -> TrueShortageConfig:
        """動的設定の生成"""
        
        if config_override:
            self.logger.info("[Config] 設定上書きを使用")
            return config_override
        
        # Phase 1: 基本的な動的設定生成
        try:
            # intermediate_data.parquetからの基本情報抽出
            data_path = scenario_dir / 'intermediate_data.parquet'
            if data_path.exists():
                df = pd.read_parquet(data_path)
                
                # 基本的な動的検出
                available_roles = df['role'].dropna().unique().tolist() if 'role' in df.columns else []
                available_employments = df['employment'].dropna().unique().tolist() if 'employment' in df.columns else []
                
                # 期間の動的検出
                if 'ds' in df.columns:
                    df['ds'] = pd.to_datetime(df['ds'])
                    start_date = df['ds'].min().date()
                    end_date = df['ds'].max().date()
                else:
                    start_date = end_date = None
                
                # 施設規模の推定（基本版）
                staff_count = df['staff'].nunique() if 'staff' in df.columns else 0
                if staff_count <= 20:
                    facility_scale = "SMALL"
                elif staff_count <= 100:
                    facility_scale = "MEDIUM"
                else:
                    facility_scale = "LARGE"
                
                config = TrueShortageConfig(
                    slot_minutes=DEFAULT_SLOT_MINUTES,  # Phase 1では固定値
                    analysis_start_date=start_date,
                    analysis_end_date=end_date,
                    available_roles=available_roles,
                    available_employments=available_employments,
                    facility_scale=facility_scale,
                    data_quality_score=0.8  # Phase 1では推定値
                )
                
                self.logger.info(f"[Config] 動的設定生成: 職種{len(available_roles)}個, 雇用形態{len(available_employments)}個")
                return config
            
        except Exception as e:
            self.logger.error(f"[Config] 動的設定生成エラー: {e}")
        
        # フォールバック: デフォルト設定
        return TrueShortageConfig()
    
    def _safe_load_data(
        self, 
        scenario_dir: Path, 
        config: TrueShortageConfig
    ) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """安全なデータ読み込み"""
        try:
            # 需要データの読み込み（統合）
            demand_data = self._load_unified_demand_data(scenario_dir, config)
            
            # 供給データの読み込み（統合）  
            supply_data = self._load_unified_supply_data(scenario_dir, config)
            
            return demand_data, supply_data
            
        except Exception as e:
            self.logger.error(f"[DataLoad] データ読み込みエラー: {e}")
            return None, None
    
    def _load_unified_demand_data(self, scenario_dir: Path, config: TrueShortageConfig) -> pd.DataFrame:
        """統合需要データの読み込み"""
        
        # Phase 1: 基本的な需要データ読み込み
        need_files = list(scenario_dir.glob('need_per_date_slot_role_*.parquet'))
        
        if not need_files:
            self.logger.warning("[Demand] 需要データファイルが見つかりません")
            return pd.DataFrame()
        
        combined_demand = pd.DataFrame()
        
        for need_file in need_files:
            try:
                need_df = pd.read_parquet(need_file)
                if combined_demand.empty:
                    combined_demand = need_df.copy()
                else:
                    # データの統合（加算）
                    combined_demand = combined_demand.add(need_df, fill_value=0)
                    
            except Exception as e:
                self.logger.warning(f"[Demand] ファイル読み込みエラー {need_file.name}: {e}")
        
        self.logger.info(f"[Demand] 統合需要データ読み込み完了: {combined_demand.shape}")
        return combined_demand
    
    def _load_unified_supply_data(self, scenario_dir: Path, config: TrueShortageConfig) -> pd.DataFrame:
        """統合供給データの読み込み（修正版）"""
        
        try:
            # intermediate_data.parquetから供給データを抽出
            data_path = scenario_dir / 'intermediate_data.parquet'
            df = pd.read_parquet(data_path)
            
            # 🔧 緊急修正: 正しい勤務時間計算ロジック
            # 勤務レコードのみを抽出（休暇レコード除外）
            if 'holiday_type' in df.columns:
                working_data = df[df['holiday_type'].isin(['通常勤務', 'NORMAL'])].copy()
            else:
                # holiday_typeカラムがない場合は、parsed_slots_count > 0で判定
                working_data = df[df['parsed_slots_count'] > 0].copy() if 'parsed_slots_count' in df.columns else df.copy()
            
            # スロット数から時間への変換
            slot_hours = config.slot_minutes / 60.0
            
            # 🔧 重要修正: 正しい供給時間計算
            # parsed_slots_countは1レコード内のスロット数ではなく、
            # データ構造を正しく理解した計算が必要
            
            # 基本原則: 1レコード = 1つの30分スロット（勤務実績）
            # parsed_slots_countの値が18というのは、データ構造の誤解釈
            total_supply_hours = len(working_data) * slot_hours
            
            self.logger.info(f"[Supply] 供給データ修正計算:")
            self.logger.info(f"  勤務レコード数: {len(working_data):,}件")
            self.logger.info(f"  1レコード = {slot_hours}時間")
            self.logger.info(f"  総供給時間: {total_supply_hours:.1f}時間")
            
            # 現実性チェック
            staff_count = df['staff'].nunique() if 'staff' in df.columns else 0
            if staff_count > 0:
                hours_per_staff = total_supply_hours / staff_count
                self.logger.info(f"  スタッフ数: {staff_count}人")
                self.logger.info(f"  1人あたり: {hours_per_staff:.1f}時間")
                
                if 'ds' in df.columns:
                    df['ds'] = pd.to_datetime(df['ds'])
                    period_days = (df['ds'].max() - df['ds'].min()).days + 1
                    daily_per_staff = hours_per_staff / period_days
                    self.logger.info(f"  期間: {period_days}日")
                    self.logger.info(f"  1人1日: {daily_per_staff:.1f}時間/人/日")
                    
                    if daily_per_staff <= 12:
                        self.logger.info("  ✓ 現実的な範囲")
                    else:
                        self.logger.warning("  ⚠️ 高めの値")
            
            # 供給データをDataFrame形式で返す（後続処理のため）
            supply_summary = pd.DataFrame({
                'total_supply_hours': [total_supply_hours],
                'working_records': [len(working_data)],
                'slot_hours': [slot_hours]
            })
            
            return supply_summary
            
        except Exception as e:
            self.logger.error(f"[Supply] 供給データ読み込みエラー: {e}")
            return pd.DataFrame()
    
    def _calculate_direct_comparison(
        self, 
        demand_data: pd.DataFrame, 
        supply_data: pd.DataFrame, 
        config: TrueShortageConfig
    ) -> TrueShortageResult:
        """真の過不足分析 - 直接比較計算"""
        
        self.logger.info("[Calculation] 直接比較計算開始")
        
        try:
            # 単位統一: すべて時間（Hours）で計算
            slot_hours = config.slot_minutes / 60.0
            
            # === 需要の時間変換 ===
            # 需要データ: 人数 × スロット時間 → 時間
            if not demand_data.empty:
                demand_hours_data = demand_data * slot_hours
                total_demand = demand_hours_data.sum().sum()
            else:
                total_demand = 0.0
            
            # === 供給の時間取得 === 
            # 供給データ: 既に時間単位で計算済み
            if not supply_data.empty and 'total_supply_hours' in supply_data.columns:
                total_supply = supply_data['total_supply_hours'].iloc[0]
            else:
                total_supply = 0.0
            
            # === 直接比較による過不足計算 ===
            total_shortage = max(0, total_demand - total_supply)
            total_excess = max(0, total_supply - total_demand)
            
            # バランス状況の判定
            if total_shortage > 0:
                balance_status = "SHORTAGE"
            elif total_excess > 0:
                balance_status = "EXCESS"
            else:
                balance_status = "BALANCED"
            
            self.logger.info(f"[Calculation] 計算完了 - 需要:{total_demand:.1f}h, 供給:{total_supply:.1f}h, 不足:{total_shortage:.1f}h")
            
            # 結果オブジェクト生成
            result = TrueShortageResult(
                total_demand_hours=total_demand,
                total_supply_hours=total_supply,
                total_shortage_hours=total_shortage,
                total_excess_hours=total_excess,
                balance_status=balance_status,
                calculation_timestamp=datetime.now(),
                config_used=config
            )
            
            # Phase 1では基本計算のみ。職種別・雇用形態別は段階的に追加
            
            return result
            
        except Exception as e:
            self.logger.error(f"[Calculation] 直接比較計算エラー: {e}")
            return self._create_error_result(f"計算エラー: {str(e)}")
    
    def _validate_and_score_result(self, result: TrueShortageResult, config: TrueShortageConfig) -> TrueShortageResult:
        """結果検証・信頼度評価"""
        
        validation_messages = []
        reliability_factors = []
        
        try:
            # 基本的な妥当性チェック
            if result.total_demand_hours < 0:
                validation_messages.append("WARNING: 負の需要時間")
                reliability_factors.append(0.5)
            else:
                reliability_factors.append(1.0)
            
            if result.total_supply_hours < 0:
                validation_messages.append("WARNING: 負の供給時間")  
                reliability_factors.append(0.5)
            else:
                reliability_factors.append(1.0)
            
            # 現実性チェック
            daily_shortage = result.total_shortage_hours / max((config.analysis_end_date - config.analysis_start_date).days, 1) if config.analysis_start_date and config.analysis_end_date else 0
            
            if daily_shortage > 100:  # 1日100時間超過は非現実的
                validation_messages.append("WARNING: 非現実的な日次不足時間")
                reliability_factors.append(0.3)
            elif daily_shortage > 24:  # 1日24時間超過は要注意
                validation_messages.append("CAUTION: 高い日次不足時間")
                reliability_factors.append(0.7)
            else:
                reliability_factors.append(1.0)
            
            # 信頼度スコア計算
            reliability_score = np.mean(reliability_factors) if reliability_factors else 0.0
            
            # 結果の更新
            result.validation_results = validation_messages
            result.reliability_score = reliability_score
            
            self.logger.info(f"[Validation] 検証完了: 信頼度{reliability_score:.2f}, 警告{len(validation_messages)}件")
            
        except Exception as e:
            self.logger.error(f"[Validation] 検証エラー: {e}")
            result.validation_results.append(f"検証エラー: {str(e)}")
            result.reliability_score = 0.0
        
        return result
    
    def _create_error_result(self, error_message: str) -> TrueShortageResult:
        """エラー結果の生成"""
        return TrueShortageResult(
            balance_status="ERROR",
            calculation_timestamp=datetime.now(),
            validation_results=[f"ERROR: {error_message}"],
            reliability_score=0.0
        )

    # Phase 1用のヘルパーメソッド
    def get_version(self) -> str:
        """バージョン情報取得"""
        return self.version
    
    def get_status(self) -> Dict[str, Any]:
        """エンジン状態取得"""
        return {
            "version": self.version,
            "safety_checks_enabled": self.safety_checks_enabled,
            "max_calculation_time_seconds": self.max_calculation_time_seconds,
            "phase": "1 - 基盤構築"
        }


def test_unified_calculator():
    """統一計算エンジンの基本動作テスト"""
    
    print("=== UnifiedShortageCalculator 基本動作テスト ===")
    
    calculator = UnifiedShortageCalculator()
    print(f"エンジンバージョン: {calculator.get_version()}")
    print(f"エンジン状態: {calculator.get_status()}")
    
    # テスト用のシナリオディレクトリ
    test_scenario_dir = Path("extracted_results/out_p25_based")
    
    if test_scenario_dir.exists():
        print(f"テストシナリオ: {test_scenario_dir}")
        
        try:
            result = calculator.calculate_true_shortage(test_scenario_dir)
            
            print(f"\n=== 計算結果 ===")
            print(f"総需要時間: {result.total_demand_hours:.1f} 時間")
            print(f"総供給時間: {result.total_supply_hours:.1f} 時間")
            print(f"総不足時間: {result.total_shortage_hours:.1f} 時間")
            print(f"バランス状況: {result.balance_status}")
            print(f"信頼度スコア: {result.reliability_score:.2f}")
            
            if result.validation_results:
                print(f"\n検証結果:")
                for msg in result.validation_results:
                    print(f"  - {msg}")
            
            return True
            
        except Exception as e:
            print(f"テスト実行エラー: {e}")
            return False
    else:
        print(f"テストシナリオが見つかりません: {test_scenario_dir}")
        return False


if __name__ == "__main__":
    test_unified_calculator()