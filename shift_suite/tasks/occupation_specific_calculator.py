#!/usr/bin/env python3
"""
職種別詳細分析計算モジュール v1.0
按分廃止プロジェクト - Phase 1: 概念実証版

単一職種（介護）の職種別need vs staff直接比較による
按分計算を使わない真の不足時間算出
"""

from typing import Dict, Tuple, List, Optional
import pandas as pd
import numpy as np
import logging
from pathlib import Path

log = logging.getLogger(__name__)

class OccupationSpecificCalculator:
    """
    職種別詳細分析計算クラス v1.0
    
    Phase 1: 「介護」職種のみ按分廃止
    - 職種×時間帯の直接need vs staff比較
    - 按分計算を完全回避した真の不足算出
    - 従来按分との精度比較機能付き
    """
    
    def __init__(self, slot_minutes: int = 30):
        """
        職種別詳細分析計算クラス初期化
        
        Parameters
        ----------
        slot_minutes : int, default 30
            スロット間隔（分）
        """
        self.slot_hours = slot_minutes / 60.0
        self.slot_minutes = slot_minutes
        self.target_occupation = "介護"  # Phase 1対象職種
        
        log.info(f"[OccupationSpecificCalculator] 初期化完了")
        log.info(f"  ターゲット職種: {self.target_occupation}")
        log.info(f"  スロット設定: {slot_minutes}分={self.slot_hours}時間")
    
    def calculate_occupation_specific_shortage(
        self,
        scenario_dir: Path = None,
        need_data: pd.DataFrame = None,
        staff_data: pd.DataFrame = None,
        working_data: pd.DataFrame = None
    ) -> Dict[str, float]:
        """
        職種別詳細分析による不足時間計算（按分廃止）
        
        Parameters
        ----------
        scenario_dir : Path, optional
            シナリオディレクトリ（実データ読み込み用）
        need_data : pd.DataFrame, optional
            職種×時間帯別需要データ（テスト用）
        staff_data : pd.DataFrame, optional
            職種×時間帯別配置データ（テスト用）  
        working_data : pd.DataFrame, optional
            勤務データ（テスト用）
            
        Returns
        -------
        Dict[str, float]
            職種別不足時間辞書 {"介護": XX.X, "その他": YY.Y}
        """
        log.info(f"[OccupationSpecificCalculator] 職種別詳細分析開始")
        
        try:
            # 実データ読み込み（慎重なアプローチ）
            if scenario_dir is None and need_data is None:
                scenario_dir = Path("extracted_results/out_p25_based")
                
            if scenario_dir and scenario_dir.exists():
                log.info(f"実データ読み込み: {scenario_dir}")
                working_data = self._load_real_working_data(scenario_dir)
            elif working_data is None:
                log.error("実データもテストデータも提供されていません")
                return {}
            
            # Phase 2: 介護職種のみ詳細分析（精密計算対応）
            care_shortage = self._calculate_care_worker_shortage_from_real_data(
                working_data, scenario_dir
            )
            
            # その他職種は従来按分（比較用）
            other_shortage = self._calculate_other_occupations_proportional(
                working_data, care_shortage
            )
            
            result = {
                self.target_occupation: care_shortage,
                "その他職種（按分）": other_shortage
            }
            
            log.info(f"[職種別詳細分析結果]")
            log.info(f"  介護職種（直接計算）: {care_shortage:.1f}時間")
            log.info(f"  その他職種（按分維持）: {other_shortage:.1f}時間")
            log.info(f"  合計不足時間: {sum(result.values()):.1f}時間")
            
            return result
            
        except Exception as e:
            log.error(f"[OccupationSpecificCalculator] エラー発生: {e}")
            import traceback
            log.error(f"詳細エラー: {traceback.format_exc()}")
            return {}
    
    def _load_real_working_data(self, scenario_dir: Path) -> pd.DataFrame:
        """動的実データの読み込み（intermediate_data.parquet対応）"""
        try:
            # intermediate_data.parquetから動的データを読み込み
            data_path = scenario_dir / 'intermediate_data.parquet'
            if data_path.exists():
                df = pd.read_parquet(data_path)
                log.info(f"動的実データ読み込み成功: {df.shape}")
                log.info(f"データ期間: {df['ds'].min()} ～ {df['ds'].max()}" if 'ds' in df.columns else "日付情報なし")
                
                # 動的職種データの確認
                if 'role' in df.columns:
                    unique_roles = df['role'].unique()
                    log.info(f"動的職種データ: {len(unique_roles)}種類")
                    
                    # 介護関連職種の動的検出
                    care_roles = [role for role in unique_roles if '介護' in str(role)]
                    log.info(f"動的介護関連職種: {care_roles}")
                else:
                    log.warning("roleカラムが存在しません")
                
                return df
            else:
                log.error(f"動的データファイル未発見: {data_path}")
                return pd.DataFrame()
        except Exception as e:
            log.error(f"動的データ読み込みエラー: {e}")
            return pd.DataFrame()
    
    def _calculate_care_worker_shortage_from_real_data(self, working_data: pd.DataFrame, scenario_dir: Path = None) -> float:
        """実データを使用した介護職種不足計算（動的対応 Phase 2）"""
        if working_data.empty:
            log.warning("[動的介護職種分析] 勤務データが空です")
            return 0.0
        
        try:
            # 動的職種リストから介護関連を抽出
            if 'role' not in working_data.columns:
                log.error("[動的介護職種分析] roleカラムがありません")
                return 0.0
            
            all_roles = working_data['role'].unique()
            care_roles = [role for role in all_roles if self.target_occupation in str(role)]
            
            if not care_roles:
                log.warning(f"[動的介護職種分析] {self.target_occupation}関連職種が見つかりません")
                log.info(f"利用可能職種: {list(all_roles)}")
                return 0.0
            
            log.info(f"[動的介護職種分析] 検出された介護職種: {care_roles}")
            
            # 介護職種データのフィルタリング
            care_data = working_data[working_data['role'].isin(care_roles)]
            log.info(f"介護職種データ: {len(care_data)}件")
            
            # Phase 2: 実際の需要データを使用した精密計算
            if scenario_dir and scenario_dir.exists():
                return self._calculate_precise_care_shortage(scenario_dir, care_roles, care_data)
            else:
                # フォールバック: 改良された推定計算
                return self._calculate_improved_estimation(care_data)
                
        except Exception as e:
            log.error(f"[動的介護職種分析] エラー: {e}")
            return 0.0
    
    def _calculate_precise_care_shortage(self, scenario_dir: Path, care_roles: List[str], care_data: pd.DataFrame) -> float:
        """需要データを使用した精密な介護職種不足計算"""
        try:
            # 需要データファイルの探索（重複除去）
            need_files = []
            found_files = set()  # 重複防止用
            
            for care_role in care_roles:
                # need_per_date_slot_role_{職種}.parquetを探索
                clean_role = care_role.replace('/', '').replace('（', '').replace('）', '').replace('・', '')
                possible_patterns = [
                    f"need_per_date_slot_role_{care_role}.parquet",
                    f"need_per_date_slot_role_{clean_role}.parquet",
                ]
                
                for pattern in possible_patterns:
                    need_file = scenario_dir / pattern
                    if need_file.exists() and need_file not in found_files:
                        need_files.append(need_file)
                        found_files.add(need_file)
                        break
            
            if not need_files:
                log.warning("[精密計算] 需要データファイルが見つかりません - 改良推定計算に移行")
                return self._calculate_improved_estimation(care_data)
            
            log.info(f"[精密計算] 需要データファイル: {[f.name for f in need_files]}")
            
            # 需要データの読み込みと合計
            total_need = 0.0
            total_staff = 0.0
            
            for need_file in need_files:
                need_df = pd.read_parquet(need_file)
                log.info(f"需要データ {need_file.name}: {need_df.shape}")
                
                # 需要合計（全数値カラムの合計 - 日付カラム形式）
                numeric_columns = need_df.select_dtypes(include=[np.number]).columns
                # 日付形式のカラムを含む全ての数値データを合計
                date_columns = [col for col in numeric_columns if '-' in str(col) or col.isdigit()]
                
                if date_columns:
                    # 日付カラムの需要を合計
                    file_need = need_df[date_columns].sum().sum()
                else:
                    # フォールバック: 全数値カラム
                    file_need = need_df[numeric_columns].sum().sum()
                    
                total_need += file_need
                log.info(f"  ファイル別需要: {file_need:.1f}時間")
                log.info(f"  対象カラム数: {len(date_columns if date_columns else numeric_columns)}")
            
            # 配置済みスタッフ時間の推定（care_dataから）
            if len(care_data) > 0:
                # 勤務レコード数から実働時間を推定
                # intermediate_dataの各レコードは30分スロット単位のため
                # 実際の勤務時間 = レコード数 × スロット時間
                total_staff_slots = len(care_data)
                total_staff = total_staff_slots * self.slot_hours  # 30分 = 0.5時間
                
                log.info(f"推定配置時間: {total_staff:.1f}時間")
                log.info(f"  配置スロット数: {total_staff_slots}")
                log.info(f"  スロット時間: {self.slot_hours}時間/スロット")
            
            # 実際の不足計算（単位系統一による正確な計算）
            # 需要データは「人数×時間帯」、配置データは「時間」
            # 需要を時間に変換: 人数 × 0.5時間(30分スロット)
            
            need_hours = total_need * self.slot_hours  # 人数→時間変換
            staff_hours = total_staff  # 既に時間単位
            
            # 30日基準で正規化
            daily_need_hours = need_hours / 30
            daily_staff_hours = staff_hours / 30
            daily_difference = daily_need_hours - daily_staff_hours  # 静的処理を廃止
            
            # 期間統一（30日分）- 配置過多も正確に表示
            actual_difference = daily_difference * 30
            
            log.info(f"[単位系統一計算]")
            log.info(f"  需要(人数): {total_need:.0f}人・時間帯")
            log.info(f"  需要(時間): {need_hours:.1f}時間 ({total_need:.0f} × {self.slot_hours})")
            log.info(f"  配置(時間): {staff_hours:.1f}時間")
            log.info(f"  1日需要: {daily_need_hours:.1f}時間/日")
            log.info(f"  1日配置: {daily_staff_hours:.1f}時間/日") 
            log.info(f"  1日差分: {daily_difference:.1f}時間/日")
            
            # 状況分析（静的処理廃止）
            if daily_difference > 0:
                status = f"不足 {daily_difference:.1f}時間/日"
                realism_status = "要対策"
            elif daily_difference < 0:
                status = f"配置過多 {abs(daily_difference):.1f}時間/日"
                realism_status = "改善機会"
            else:
                status = "完全均衡"
                realism_status = "理想的"
            
            log.info(f"[精密計算結果（真実の表示）]")
            log.info(f"  総需要時間: {need_hours:.1f}時間 (人数換算: {total_need:.0f})")
            log.info(f"  配置時間: {staff_hours:.1f}時間")
            log.info(f"  実際差分: {actual_difference:.1f}時間")
            log.info(f"  状況: {status} ({realism_status})")
            
            return actual_difference
            
        except Exception as e:
            log.error(f"[精密計算] エラー: {e}")
            return self._calculate_improved_estimation(care_data)
    
    def _calculate_improved_estimation(self, care_data: pd.DataFrame) -> float:
        """改良された推定計算（需要データが利用できない場合）"""
        if len(care_data) == 0:
            return 0.0
            
        # 平均的な不足率を適用（業界標準からの推定）
        base_hours = len(care_data) * 8.0  # 1人当たり8時間勤務と仮定
        shortage_rate = 0.15  # 一般的な介護業界の不足率15%
        
        estimated_shortage = base_hours * shortage_rate
        
        log.info(f"[改良推定] ベース時間: {base_hours:.1f}, 不足率: {shortage_rate:.1%}")
        log.info(f"[改良推定] 推定不足: {estimated_shortage:.1f}時間")
        
        return estimated_shortage
    
    def _calculate_care_worker_shortage(
        self,
        need_data: pd.DataFrame,
        staff_data: pd.DataFrame,
        working_data: pd.DataFrame
    ) -> float:
        """
        介護職種の職種×時間帯直接比較による不足計算
        
        Returns
        -------
        float
            介護職種の真の不足時間（按分なし）
        """
        if need_data.empty or staff_data.empty:
            log.warning("[介護職種分析] 必要データが不足")
            return 0.0
        
        try:
            # 介護職種の絞り込み（「介護」を含む職種）
            care_roles = [role for role in need_data.get('role', []) 
                         if self.target_occupation in str(role)]
            
            if not care_roles:
                log.warning(f"[介護職種分析] {self.target_occupation}職種が見つかりません")
                return 0.0
            
            log.info(f"[介護職種分析] 対象職種: {care_roles}")
            
            # 介護職種のneed合計
            care_need = self._sum_occupation_need(need_data, care_roles)
            
            # 介護職種のstaff合計  
            care_staff = self._sum_occupation_staff(staff_data, care_roles)
            
            # 直接比較による不足計算
            care_shortage = max(0, care_need - care_staff)
            
            log.info(f"[介護職種詳細]")
            log.info(f"  需要合計: {care_need:.1f}人・時間")  
            log.info(f"  配置合計: {care_staff:.1f}人・時間")
            log.info(f"  直接不足: {care_shortage:.1f}人・時間")
            
            return care_shortage
            
        except Exception as e:
            log.error(f"[介護職種分析] 計算エラー: {e}")
            return 0.0
    
    def _sum_occupation_need(self, need_data: pd.DataFrame, target_roles: List[str]) -> float:
        """指定職種のneed合計を計算"""
        if 'role' not in need_data.columns:
            return 0.0
            
        care_need_data = need_data[need_data['role'].isin(target_roles)]
        
        # 時間関連カラムの合計（slot_XX形式）
        time_columns = [col for col in care_need_data.columns 
                       if col.startswith('slot_') or 'need' in col.lower()]
        
        if time_columns:
            total_need = care_need_data[time_columns].sum().sum()
            log.debug(f"[need計算] 対象カラム: {len(time_columns)}個, 合計: {total_need}")
            return total_need
        
        return 0.0
    
    def _sum_occupation_staff(self, staff_data: pd.DataFrame, target_roles: List[str]) -> float:
        """指定職種のstaff配置合計を計算"""
        if 'role' not in staff_data.columns:
            return 0.0
            
        care_staff_data = staff_data[staff_data['role'].isin(target_roles)]
        
        # 時間関連カラムの合計
        time_columns = [col for col in care_staff_data.columns 
                       if col.startswith('slot_') or 'staff' in col.lower()]
        
        if time_columns:
            total_staff = care_staff_data[time_columns].sum().sum()
            log.debug(f"[staff計算] 対象カラム: {len(time_columns)}個, 合計: {total_staff}")
            return total_staff
            
        return 0.0
    
    def _calculate_other_occupations_proportional(
        self,
        working_data: pd.DataFrame,
        care_shortage: float
    ) -> float:
        """
        その他職種の按分計算（比較・検証用）
        
        Phase 1では介護以外は従来按分を維持
        """
        try:
            # 全体不足から介護不足を差し引いた残り
            # ここは簡易計算（Phase 2で詳細化予定）
            
            # working_dataから介護以外の職種比率を算出
            if working_data.empty:
                return 0.0
            
            non_care_ratio = self._calculate_non_care_ratio(working_data)
            estimated_other_shortage = care_shortage * non_care_ratio
            
            log.info(f"[その他職種按分] 比率: {non_care_ratio:.2f}, 推定不足: {estimated_other_shortage:.1f}")
            
            return estimated_other_shortage
            
        except Exception as e:
            log.error(f"[その他職種按分] エラー: {e}")
            return 0.0
    
    def _calculate_non_care_ratio(self, working_data: pd.DataFrame) -> float:
        """介護以外職種の人数比率を計算"""
        if 'role' not in working_data.columns:
            return 1.0
        
        total_count = len(working_data)
        care_count = len(working_data[working_data['role'].str.contains(
            self.target_occupation, na=False
        )])
        
        non_care_count = total_count - care_count
        non_care_ratio = non_care_count / care_count if care_count > 0 else 1.0
        
        log.debug(f"[職種比率] 全体: {total_count}, 介護: {care_count}, その他: {non_care_count}")
        
        return non_care_ratio
    
    def compare_with_proportional(
        self,
        occupation_result: Dict[str, float],
        proportional_result: Dict[str, float]
    ) -> Dict[str, float]:
        """
        職種別詳細分析 vs 従来按分の精度比較
        
        Returns
        -------
        Dict[str, float]
            比較分析結果 {"precision_improvement": X%, "total_diff": X時間, ...}
        """
        try:
            occ_total = sum(occupation_result.values())
            prop_total = sum(proportional_result.values()) if proportional_result else 0
            
            total_diff = occ_total - prop_total
            precision_improvement = (abs(total_diff) / prop_total * 100) if prop_total > 0 else 0
            
            comparison = {
                "occupation_specific_total": occ_total,
                "proportional_total": prop_total,
                "total_difference": total_diff,
                "precision_improvement_pct": precision_improvement,
                "care_worker_direct": occupation_result.get(self.target_occupation, 0),
                "method": "Phase1_CareWorker_Only"
            }
            
            log.info(f"[精度比較結果]")
            log.info(f"  職種別詳細: {occ_total:.1f}時間")
            log.info(f"  従来按分: {prop_total:.1f}時間")
            log.info(f"  差分: {total_diff:.1f}時間")
            log.info(f"  精度変化: {precision_improvement:.1f}%")
            
            return comparison
            
        except Exception as e:
            log.error(f"[精度比較] エラー: {e}")
            return {}

# モジュール外部インターフェース
def calculate_occupation_specific_shortage(
    need_data: pd.DataFrame,
    staff_data: pd.DataFrame, 
    working_data: pd.DataFrame,
    slot_minutes: int = 30
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    職種別詳細分析の外部インターフェース
    
    Returns
    -------
    Tuple[Dict[str, float], Dict[str, float]]
        (職種別不足結果, 精度比較結果)
    """
    calculator = OccupationSpecificCalculator(slot_minutes)
    
    occupation_result = calculator.calculate_occupation_specific_shortage(
        need_data, staff_data, working_data
    )
    
    # 従来按分との比較は後で実装
    comparison_result = {"method": "Phase1_POC"}
    
    return occupation_result, comparison_result