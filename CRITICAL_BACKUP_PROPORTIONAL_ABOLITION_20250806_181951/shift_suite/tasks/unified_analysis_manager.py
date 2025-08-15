#!/usr/bin/env python3
"""
統一分析結果管理システム - Unified Analysis Manager

全体最適化を目的とした統一されたデータ管理・エラー処理・AI連携システム
動的データ処理と実データ優先を基本方針とする
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
import pandas as pd
import numpy as np
from pathlib import Path

log = logging.getLogger(__name__)

class SafeDataConverter:
    """型安全なデータ変換システム"""
    
    @staticmethod
    def safe_float(value: Any, default: float = 0.0, field_name: str = "unknown") -> float:
        """安全なfloat変換"""
        try:
            if pd.isna(value):
                return default
            converted = float(value)
            if np.isinf(converted):
                log.warning(f"[SafeDataConverter] {field_name}でInf値検出 → {default}に変換")
                return default
            return converted
        except (ValueError, TypeError) as e:
            log.warning(f"[SafeDataConverter] {field_name}の変換エラー: {value} → {default} (理由: {e})")
            return default
    
    @staticmethod
    def safe_int(value: Any, default: int = 0, field_name: str = "unknown") -> int:
        """安全なint変換"""
        try:
            if pd.isna(value):
                return default
            converted = int(float(value))  # float経由でより柔軟に変換
            return converted
        except (ValueError, TypeError) as e:
            log.warning(f"[SafeDataConverter] {field_name}の変換エラー: {value} → {default} (理由: {e})")
            return default
    
    @staticmethod
    def safe_str(value: Any, default: str = "N/A", field_name: str = "unknown") -> str:
        """安全なstr変換"""
        try:
            if pd.isna(value):
                return default
            return str(value)
        except Exception as e:
            log.warning(f"[SafeDataConverter] {field_name}の変換エラー: {value} → {default} (理由: {e})")
            return default

class DynamicKeyManager:
    """動的キー管理システム - マルチシナリオ対応強化版"""
    
    @staticmethod
    def generate_analysis_key(file_name: str, scenario_key: str = "default", 
                            analysis_type: str = "general") -> str:
        """統一されたキー生成（従来互換）"""
        # ファイル名から拡張子を除去し、安全な文字のみ使用
        clean_filename = Path(file_name).stem.replace(' ', '_').replace('-', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        return f"{clean_filename}_{scenario_key}_{analysis_type}_{timestamp}_{unique_id}"
    
    @staticmethod  
    def generate_scenario_analysis_key(
        file_name: str, 
        scenario_key: str,
        analysis_type: str
    ) -> str:
        """🔧 新機能: シナリオ対応の統一キー生成"""
        clean_filename = Path(file_name).stem.replace(' ', '_').replace('-', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        return f"{clean_filename}_{scenario_key}_{analysis_type}_{timestamp}_{unique_id}"
    
    @staticmethod
    def parse_scenario_key(analysis_key: str) -> Dict[str, str]:
        """🔧 新機能: シナリオキーの解析"""
        try:
            parts = analysis_key.split('_')
            if len(parts) >= 5:
                return {
                    "file_name": parts[0],
                    "scenario": parts[1], 
                    "analysis_type": parts[2],
                    "timestamp": f"{parts[3]}_{parts[4]}",
                    "unique_id": parts[5] if len(parts) > 5 else "unknown"
                }
        except Exception as e:
            log.warning(f"シナリオキー解析エラー: {analysis_key} → {e}")
        
        return {"file_name": "unknown", "scenario": "default", 
                "analysis_type": "general", "timestamp": "unknown", "unique_id": "unknown"}
    
    @staticmethod
    def extract_file_info(analysis_key: str) -> Dict[str, str]:
        """キーからファイル情報を抽出"""
        try:
            parts = analysis_key.split('_')
            if len(parts) >= 5:
                return {
                    "file_name": parts[0],
                    "scenario_key": parts[1],
                    "analysis_type": parts[2],
                    "timestamp": f"{parts[3]}_{parts[4]}",
                    "unique_id": parts[5] if len(parts) > 5 else "unknown"
                }
        except Exception as e:
            log.warning(f"キー解析エラー: {analysis_key} → {e}")
        
        return {"file_name": "unknown", "scenario_key": "default", 
                "analysis_type": "general", "timestamp": "unknown", "unique_id": "unknown"}

class UnifiedAnalysisResult:
    """統一分析結果データ構造"""
    
    def __init__(self, analysis_key: str, analysis_type: str):
        self.analysis_key = analysis_key
        self.analysis_type = analysis_type
        self.creation_time = datetime.now().isoformat()
        self.data_integrity = "valid"
        self.error_details = None
        self.core_metrics = {}
        self.extended_data = {}
        self.metadata = {
            "data_source": "real_time_analysis",
            "processing_method": "dynamic_adaptive",
            "quality_score": 1.0
        }
    
    def set_error_state(self, error: Exception, fallback_data: Dict[str, Any] = None):
        """エラー状態の統一設定"""
        self.data_integrity = "error"
        self.error_details = {
            "error_type": type(error).__name__,
            "error_message": str(error)[:200],
            "timestamp": datetime.now().isoformat()
        }
        self.metadata["quality_score"] = 0.0
        
        if fallback_data:
            self.core_metrics.update(fallback_data)
            log.info(f"[{self.analysis_key}] エラー時フォールバックデータを設定")
    
    def add_core_metric(self, key: str, value: Any, description: str = ""):
        """コアメトリクスの安全な追加"""
        self.core_metrics[key] = {
            "value": value,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_ai_compatible_dict(self) -> Dict[str, Any]:
        """AI包括レポート用の辞書生成"""
        return {
            "analysis_key": self.analysis_key,
            "analysis_type": self.analysis_type,
            "creation_time": self.creation_time,
            "data_integrity": self.data_integrity,
            "error_details": self.error_details,
            "core_metrics": self.core_metrics,
            "extended_data": self.extended_data,
            "metadata": self.metadata
        }

class UnifiedAnalysisManager:
    """統一分析結果管理システム - マルチシナリオ対応版"""
    
    def __init__(self):
        self.converter = SafeDataConverter()
        self.key_manager = DynamicKeyManager()
        self.results_registry = {}  # 従来の統合レジストリ
        
        # 🔧 新機能: シナリオ別レジストリ管理
        self.scenario_registries = {
            "mean_based": {},
            "median_based": {},
            "p25_based": {}
        }
        self.default_scenario = "median_based"  # 統計的に最も安定
        
        log.info("[UnifiedAnalysisManager] マルチシナリオ対応で初期化完了")
        log.info(f"[UnifiedAnalysisManager] デフォルトシナリオ: {self.default_scenario}")
    
    def create_shortage_analysis(self, file_name: str, scenario_key: str, 
                               role_df: pd.DataFrame) -> UnifiedAnalysisResult:
        """不足分析結果の統一作成 - マルチシナリオ対応"""
        # 🔧 修正: シナリオ対応キー生成
        analysis_key = self.key_manager.generate_scenario_analysis_key(
            file_name, scenario_key, "shortage"
        )
        result = UnifiedAnalysisResult(analysis_key, "shortage_analysis")
        
        # シナリオ情報をメタデータに追加
        result.metadata["scenario"] = scenario_key
        result.metadata["file_name"] = file_name
        
        try:
            # 動的データ処理 - カラムの存在を確認してから処理
            if "lack_h" in role_df.columns and not role_df.empty:
                total_shortage_hours = self.converter.safe_float(
                    role_df["lack_h"].sum(), 0.0, "total_shortage_hours"
                )
                shortage_events = self.converter.safe_int(
                    (role_df["lack_h"] > 0).sum(), 0, "shortage_events"
                )
                
                # スケーラブルなデータ要約（メモリ効率重視）
                top_shortage_roles = []
                if "lack_h" in role_df.columns:
                    # 動的に上位N件を決定（データ規模に応じて調整）
                    sample_size = min(50, max(10, len(role_df) // 10))
                    top_roles_df = role_df.nlargest(sample_size, 'lack_h')
                    top_shortage_roles = [
                        self.converter.safe_str(role, "Unknown") 
                        for role in top_roles_df.get('role', pd.Series()).tolist()
                    ]
                
                # コアメトリクスの設定
                result.add_core_metric("total_shortage_hours", total_shortage_hours, 
                                     "総不足時間（実測値）")
                result.add_core_metric("shortage_events_count", shortage_events,
                                     "不足発生回数")
                result.add_core_metric("affected_roles_count", len(role_df),
                                     "影響を受けた職種数")
                
                # 拡張データ（AI分析用）
                result.extended_data = {
                    "top_shortage_roles": top_shortage_roles[:10],
                    "severity_level": self._calculate_severity(total_shortage_hours),
                    "role_count": len(role_df),
                    "data_completeness": len(role_df[role_df["lack_h"].notna()]) / len(role_df) if len(role_df) > 0 else 0.0
                }
                
                log.info(f"[{analysis_key}] 不足分析完了: {total_shortage_hours:.1f}時間不足")
                
            else:
                # データ不足時のフォールバック
                result.add_core_metric("total_shortage_hours", 0.0, "データ不足によるデフォルト値")
                result.extended_data = {"severity_level": "unknown", "role_count": 0}
                result.metadata["quality_score"] = 0.5
                log.warning(f"[{analysis_key}] 不足分析: データ不足のためデフォルト値使用")
                
        except Exception as e:
            result.set_error_state(e, {
                "total_shortage_hours": 0.0,
                "shortage_events_count": 0,
                "affected_roles_count": 0
            })
            log.error(f"[{analysis_key}] 不足分析エラー: {e}", exc_info=True)
        
        # 🔧 修正: 統合レジストリとシナリオ別レジストリの両方に登録
        self.results_registry[analysis_key] = result
        
        # シナリオ別レジストリに登録
        if scenario_key in self.scenario_registries:
            self.scenario_registries[scenario_key][analysis_key] = result
            log.debug(f"[UnifiedAnalysisManager] {scenario_key}レジストリに登録: {analysis_key}")
        
        return result
    
    def create_fatigue_analysis(self, file_name: str, scenario_key: str,
                              fatigue_df: Optional[pd.DataFrame] = None,
                              combined_df: Optional[pd.DataFrame] = None) -> UnifiedAnalysisResult:
        """疲労分析結果の統一作成 - マルチシナリオ対応"""
        # 🔧 修正: シナリオ対応キー生成
        analysis_key = self.key_manager.generate_scenario_analysis_key(
            file_name, scenario_key, "fatigue"
        )
        result = UnifiedAnalysisResult(analysis_key, "fatigue_analysis")
        
        # シナリオ情報をメタデータに追加
        result.metadata["scenario"] = scenario_key
        result.metadata["file_name"] = file_name
        
        try:
            avg_fatigue_score = 0.5  # デフォルト
            high_fatigue_count = 0
            total_analyzed = 0
            
            # 動的データソース選択
            active_df = None
            data_source_type = "none"
            
            if fatigue_df is not None and not fatigue_df.empty and "fatigue_score" in fatigue_df.columns:
                active_df = fatigue_df
                data_source_type = "fatigue_score_direct"
                avg_fatigue_score = self.converter.safe_float(
                    fatigue_df["fatigue_score"].mean(), 0.5, "avg_fatigue_score"
                )
                high_fatigue_count = self.converter.safe_int(
                    (fatigue_df["fatigue_score"] > 0.7).sum(), 0, "high_fatigue_count"
                )
                total_analyzed = len(fatigue_df)
                
            elif combined_df is not None and not combined_df.empty and "final_score" in combined_df.columns:
                active_df = combined_df
                data_source_type = "combined_score_estimated"
                scores = combined_df["final_score"]
                if scores.max() > 0:
                    # 低いスコア = 高い疲労の推定
                    avg_fatigue_score = self.converter.safe_float(
                        max(0, 1 - (scores.mean() / scores.max())), 0.5, "estimated_fatigue"
                    )
                    high_fatigue_count = self.converter.safe_int(
                        len(scores[scores < (scores.mean() - scores.std())]), 0, "estimated_high_fatigue"
                    )
                total_analyzed = len(combined_df)
            
            # コアメトリクスの設定
            result.add_core_metric("avg_fatigue_score", avg_fatigue_score, 
                                 f"平均疲労スコア（{data_source_type}）")
            result.add_core_metric("high_fatigue_staff_count", high_fatigue_count,
                                 "高疲労スタッフ数")
            result.add_core_metric("total_staff_analyzed", total_analyzed,
                                 "分析対象スタッフ総数")
            
            # 拡張データ
            result.extended_data = {
                "data_source_type": data_source_type,
                "fatigue_distribution": self._calculate_fatigue_distribution(active_df) if active_df is not None else {},
                "analysis_reliability": "high" if data_source_type == "fatigue_score_direct" else "medium"
            }
            
            log.info(f"[{analysis_key}] 疲労分析完了: 平均スコア {avg_fatigue_score:.3f} ({data_source_type})")
            
        except Exception as e:
            result.set_error_state(e, {
                "avg_fatigue_score": 0.5,
                "high_fatigue_staff_count": 0,
                "total_staff_analyzed": 0
            })
            log.error(f"[{analysis_key}] 疲労分析エラー: {e}", exc_info=True)
        
        # 🔧 修正: 統合レジストリとシナリオ別レジストリの両方に登録
        self.results_registry[analysis_key] = result
        
        # シナリオ別レジストリに登録
        if scenario_key in self.scenario_registries:
            self.scenario_registries[scenario_key][analysis_key] = result
            log.debug(f"[UnifiedAnalysisManager] {scenario_key}レジストリに登録: {analysis_key}")
        
        return result
    
    def create_fairness_analysis(self, file_name: str, scenario_key: str,
                               fairness_df: pd.DataFrame) -> List[UnifiedAnalysisResult]:
        """公平性分析結果の統一作成 - マルチシナリオ対応（複数ファイル対応）"""
        results = []
        
        try:
            # 動的データ処理 - 利用可能なカラムを確認
            score_column = None
            if "night_ratio" in fairness_df.columns:
                score_column = "night_ratio"
            elif "fairness_score" in fairness_df.columns:
                score_column = "fairness_score"
            elif "balance_score" in fairness_df.columns:
                score_column = "balance_score"
            
            if score_column and not fairness_df.empty:
                avg_fairness_score = self.converter.safe_float(
                    fairness_df[score_column].mean(), 0.8, f"avg_{score_column}"
                )
                low_fairness_count = self.converter.safe_int(
                    len(fairness_df[fairness_df[score_column] < 0.7]), 0, "low_fairness_count"
                )
                
                # 複数ファイルの場合は統一結果を作成
                # 🔧 修正: シナリオ対応キー生成
                analysis_key = self.key_manager.generate_scenario_analysis_key(
                    file_name, scenario_key, "fairness"
                )
                result = UnifiedAnalysisResult(analysis_key, "fairness_analysis")
                
                # シナリオ情報をメタデータに追加
                result.metadata["scenario"] = scenario_key
                result.metadata["file_name"] = file_name
                
                result.add_core_metric("avg_fairness_score", avg_fairness_score,
                                     f"平均公平性スコア（{score_column}ベース）")
                result.add_core_metric("low_fairness_staff_count", low_fairness_count,
                                     "改善必要スタッフ数")
                result.add_core_metric("total_staff_analyzed", len(fairness_df),
                                     "分析対象スタッフ総数")
                
                result.extended_data = {
                    "score_column_used": score_column,
                    "fairness_distribution": self._calculate_fairness_distribution(fairness_df, score_column),
                    "improvement_rate": (len(fairness_df) - low_fairness_count) / len(fairness_df) if len(fairness_df) > 0 else 1.0
                }
                
                results.append(result)
                self.results_registry[analysis_key] = result
                
                log.info(f"[{analysis_key}] 公平性分析完了: 平均スコア {avg_fairness_score:.3f}")
                
            else:
                # データ不足時のフォールバック
                analysis_key = self.key_manager.generate_analysis_key(
                    file_name, scenario_key, "fairness"
                )
                result = UnifiedAnalysisResult(analysis_key, "fairness_analysis")
                result.add_core_metric("avg_fairness_score", 0.8, "データ不足によるデフォルト値")
                result.extended_data = {"score_column_used": "none", "improvement_rate": 0.0}
                results.append(result)
                self.results_registry[analysis_key] = result
                
                log.warning(f"[{analysis_key}] 公平性分析: 適切なスコア列が見つからずデフォルト値使用")
                
        except Exception as e:
            # エラー時のフォールバック結果作成
            analysis_key = self.key_manager.generate_analysis_key(
                file_name, scenario_key, "fairness"
            )
            result = UnifiedAnalysisResult(analysis_key, "fairness_analysis")
            result.set_error_state(e, {
                "avg_fairness_score": 0.8,
                "low_fairness_staff_count": 0,
                "total_staff_analyzed": 0
            })
            results.append(result)
            self.results_registry[analysis_key] = result
            log.error(f"[{analysis_key}] 公平性分析エラー: {e}", exc_info=True)
        
        return results
    
    def set_default_scenario(self, scenario: str):
        """🔧 新機能: デフォルトシナリオの設定"""
        valid_scenarios = ["mean_based", "median_based", "p25_based"]
        if scenario in valid_scenarios:
            self.default_scenario = scenario
            log.info(f"[UnifiedAnalysisManager] デフォルトシナリオを設定: {scenario}")
        else:
            log.warning(f"[UnifiedAnalysisManager] 無効なシナリオ: {scenario}. 有効: {valid_scenarios}")
    
    def get_scenario_compatible_results(
        self, 
        file_pattern: str = None,
        scenario: str = None
    ) -> Dict[str, Any]:
        """🔧 新機能: シナリオ対応の結果取得"""
        target_scenario = scenario or self.default_scenario
        
        log.info(f"[get_scenario_compatible_results] 対象シナリオ: {target_scenario}")
        log.info(f"[get_scenario_compatible_results] 検索パターン: '{file_pattern}'")
        
        # シナリオ別レジストリから取得
        if target_scenario in self.scenario_registries:
            scenario_registry = self.scenario_registries[target_scenario]
            log.info(f"[get_scenario_compatible_results] {target_scenario}レジストリサイズ: {len(scenario_registry)}")
            
            if scenario_registry:
                # シナリオ別レジストリから結果を取得
                return self._process_scenario_results(scenario_registry, file_pattern)
            else:
                log.warning(f"[get_scenario_compatible_results] {target_scenario}レジストリが空です")
        
        # フォールバック: 従来の統合レジストリから取得
        log.info("[get_scenario_compatible_results] フォールバック: 統合レジストリから取得")
        return self.get_ai_compatible_results(file_pattern)
    
    def _process_scenario_results(self, registry: Dict[str, 'UnifiedAnalysisResult'], file_pattern: str = None) -> Dict[str, Any]:
        """シナリオ別レジストリの結果処理"""
        ai_results = {}
        
        for key, result in registry.items():
            # パターンマッチング
            if file_pattern is None:
                match = True
            else:
                clean_pattern = Path(file_pattern).stem  # 拡張子を除去
                match = clean_pattern in key or file_pattern in key
                
            if match:
                log.debug(f"[_process_scenario_results] マッチ: {key}")
                # 分析タイプごとに整理
                analysis_type = result.analysis_type
                if analysis_type not in ai_results:
                    ai_results[analysis_type] = []
                
                ai_results[analysis_type].append(result.get_ai_compatible_dict())
        
        # 最新の結果のみを各分析タイプから選択
        consolidated_results = {}
        for analysis_type, results_list in ai_results.items():
            if results_list:
                # 作成時刻でソートして最新を選択
                latest_result = max(results_list, key=lambda x: x["creation_time"])
                
                # コアメトリクスを平坦化
                consolidated_data = {}
                for metric_key, metric_data in latest_result["core_metrics"].items():
                    consolidated_data[metric_key] = metric_data["value"]
                
                # 拡張データも統合
                consolidated_data.update(latest_result["extended_data"])
                consolidated_data["data_integrity"] = latest_result["data_integrity"]
                consolidated_data["metadata"] = latest_result["metadata"]
                
                consolidated_results[analysis_type] = consolidated_data
        
        return consolidated_results
    
    def get_ai_compatible_results(self, file_pattern: str = None) -> Dict[str, Any]:
        """AI包括レポート用の結果辞書生成"""
        ai_results = {}
        
        # 🔧 修正: デバッグログを追加
        log.info(f"[get_ai_compatible_results] 検索パターン: '{file_pattern}'")
        log.info(f"[get_ai_compatible_results] レジストリ内のキー数: {len(self.results_registry)}")
        
        # レジストリ内のキーを表示（デバッグ用）
        if self.results_registry:
            log.debug("[get_ai_compatible_results] レジストリ内のキー:")
            for key in list(self.results_registry.keys())[:5]:  # 最初の5個のみ
                log.debug(f"  - {key}")
        else:
            log.warning("[get_ai_compatible_results] ⚠️ レジストリが空です！")
        
        for key, result in self.results_registry.items():
            # 🔧 修正: パターンマッチングを改善
            if file_pattern is None:
                match = True
            else:
                # ファイル名の部分一致を許可
                from pathlib import Path
                clean_pattern = Path(file_pattern).stem  # 拡張子を除去
                match = clean_pattern in key or file_pattern in key
                
            if match:
                log.debug(f"[get_ai_compatible_results] マッチ: {key}")
                # 分析タイプごとに整理
                analysis_type = result.analysis_type
                if analysis_type not in ai_results:
                    ai_results[analysis_type] = []
                
                ai_results[analysis_type].append(result.get_ai_compatible_dict())
        
        # 最新の結果のみを各分析タイプから選択（重複回避）
        consolidated_results = {}
        for analysis_type, results_list in ai_results.items():
            if results_list:
                # 作成時刻でソートして最新を選択
                latest_result = max(results_list, key=lambda x: x["creation_time"])
                
                # コアメトリクスを平坦化してAI包括レポート形式に適合
                consolidated_data = {}
                for metric_key, metric_data in latest_result["core_metrics"].items():
                    consolidated_data[metric_key] = metric_data["value"]
                
                # 拡張データも統合
                consolidated_data.update(latest_result["extended_data"])
                consolidated_data["data_integrity"] = latest_result["data_integrity"]
                consolidated_data["metadata"] = latest_result["metadata"]
                
                consolidated_results[analysis_type] = consolidated_data
        
        return consolidated_results
    
    def _calculate_severity(self, shortage_hours: float) -> str:
        """不足時間から重要度を動的計算"""
        if shortage_hours > 100:
            return "critical"
        elif shortage_hours > 50:
            return "high"
        elif shortage_hours > 10:
            return "medium"
        else:
            return "low"
    
    def _calculate_fatigue_distribution(self, df: pd.DataFrame) -> Dict[str, int]:
        """疲労分布の動的計算"""
        if df is None or df.empty:
            return {"normal": 0, "elevated": 0, "high": 0, "critical": 0}
        
        score_col = "fatigue_score" if "fatigue_score" in df.columns else "final_score"
        if score_col not in df.columns:
            return {"normal": 0, "elevated": 0, "high": 0, "critical": 0}
        
        scores = df[score_col].fillna(0.5)
        return {
            "normal": int((scores < 0.5).sum()),
            "elevated": int(((scores >= 0.5) & (scores < 0.7)).sum()),
            "high": int(((scores >= 0.7) & (scores < 0.85)).sum()),
            "critical": int((scores >= 0.85).sum())
        }
    
    def _calculate_fairness_distribution(self, df: pd.DataFrame, score_col: str) -> Dict[str, int]:
        """公平性分布の動的計算"""
        if df is None or df.empty or score_col not in df.columns:
            return {"excellent": 0, "good": 0, "needs_improvement": 0, "poor": 0}
        
        scores = df[score_col].fillna(0.8)
        return {
            "excellent": int((scores >= 0.9).sum()),
            "good": int(((scores >= 0.7) & (scores < 0.9)).sum()),
            "needs_improvement": int(((scores >= 0.5) & (scores < 0.7)).sum()),
            "poor": int((scores < 0.5).sum())
        }
    
    def cleanup_old_results(self, max_age_hours: int = 24):
        """古い結果の自動クリーンアップ"""
        current_time = datetime.now()
        keys_to_remove = []
        
        for key, result in self.results_registry.items():
            result_time = datetime.fromisoformat(result.creation_time.replace('Z', '+00:00').replace('+00:00', ''))
            age_hours = (current_time - result_time).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.results_registry[key]
            
        if keys_to_remove:
            log.info(f"[UnifiedAnalysisManager] 古い結果 {len(keys_to_remove)}件をクリーンアップ")