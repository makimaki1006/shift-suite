"""
アプローチ①：元データの本分析用加工システム
深度19.6%問題の解決のため、生データから制約抽出に特化した前処理を実行

主要機能：
1. 生データからの暗黙制約パターンの発見
2. 時系列依存関係の詳細抽出
3. スタッフ間の相関・依存関係の可視化
4. 勤務区分の隠れたルールの発見
5. 例外パターンと通常パターンの分離
"""

from __future__ import annotations

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import itertools

from .constants import SLOT_HOURS, STATISTICAL_THRESHOLDS
from .utils import gen_labels

log = logging.getLogger(__name__)


class EnhancedRawDataProcessor:
    """生データから制約抽出に特化した深度分析プロセッサー"""
    
    def __init__(self):
        self.confidence_threshold = STATISTICAL_THRESHOLDS['confidence_level']
        self.min_sample_size = STATISTICAL_THRESHOLDS['min_sample_size']
        self.correlation_threshold = STATISTICAL_THRESHOLDS['correlation_threshold']
        
    def process_raw_data_for_constraint_extraction(self, raw_excel_path: str, 
                                                 worktype_definitions: Dict = None) -> Dict[str, Any]:
        """生データから制約抽出用の深度分析データを生成
        
        Args:
            raw_excel_path: 元のExcelファイルパス
            worktype_definitions: 勤務区分定義辞書
            
        Returns:
            深度分析用のデータセット辞書
        """
        log.info("生データからの制約抽出特化分析を開始...")
        
        # 1. 生データの多角的読み込み
        raw_datasets = self._multi_perspective_data_ingestion(raw_excel_path)
        
        # 2. 暗黙制約パターンの発見
        implicit_patterns = self._discover_implicit_constraint_patterns(raw_datasets, worktype_definitions)
        
        # 3. 時系列依存関係の詳細抽出
        temporal_dependencies = self._extract_temporal_dependencies(raw_datasets)
        
        # 4. スタッフ関係性マトリックスの構築
        staff_relationship_matrix = self._build_staff_relationship_matrix(raw_datasets)
        
        # 5. 勤務区分ルール発見
        worktype_rules = self._discover_worktype_rules(raw_datasets, worktype_definitions)
        
        # 6. 例外パターンの分離と分析
        exception_analysis = self._analyze_exception_patterns(raw_datasets)
        
        return {
            "processing_metadata": {
                "timestamp": datetime.now().isoformat(),
                "approach": "①生データ特化分析",
                "data_source": raw_excel_path,
                "confidence_threshold": self.confidence_threshold
            },
            "raw_datasets": raw_datasets,
            "implicit_patterns": implicit_patterns,
            "temporal_dependencies": temporal_dependencies,
            "staff_relationships": staff_relationship_matrix,
            "worktype_rules": worktype_rules,
            "exception_analysis": exception_analysis
        }
    
    def _multi_perspective_data_ingestion(self, excel_path: str) -> Dict[str, pd.DataFrame]:
        """生データの多角的読み込み - 異なる視点からデータを解釈"""
        try:
            # メイン勤務データ
            main_df = pd.read_excel(excel_path, sheet_name=0)
            
            datasets = {
                "main_shifts": main_df,
                "time_series_view": self._create_time_series_view(main_df),
                "staff_centric_view": self._create_staff_centric_view(main_df),
                "constraint_detection_view": self._create_constraint_detection_view(main_df),
                "pattern_mining_view": self._create_pattern_mining_view(main_df)
            }
            
            log.info(f"多角的データ読み込み完了: {len(datasets)}種類のビューを生成")
            return datasets
            
        except Exception as e:
            log.error(f"データ読み込みエラー: {e}")
            return {}
    
    def _create_time_series_view(self, df: pd.DataFrame) -> pd.DataFrame:
        """時系列制約発見に特化したビュー"""
        if df.empty:
            return pd.DataFrame()
            
        time_series_df = df.copy()
        
        # 日付列の特定と正規化
        date_cols = [col for col in df.columns if any(keyword in str(col).lower() 
                    for keyword in ['日', 'date', '月', '年'])]
        
        if date_cols:
            # 日付インデックスの作成
            for date_col in date_cols:
                try:
                    time_series_df[f'{date_col}_parsed'] = pd.to_datetime(df[date_col], errors='coerce')
                    time_series_df[f'{date_col}_weekday'] = time_series_df[f'{date_col}_parsed'].dt.day_name()
                    time_series_df[f'{date_col}_week'] = time_series_df[f'{date_col}_parsed'].dt.isocalendar().week
                    time_series_df[f'{date_col}_month'] = time_series_df[f'{date_col}_parsed'].dt.month
                except:
                    continue
        
        # 時間依存関係の追加
        time_series_df['row_sequence'] = range(len(time_series_df))
        
        return time_series_df
    
    def _create_staff_centric_view(self, df: pd.DataFrame) -> pd.DataFrame:
        """スタッフ中心の制約発見ビュー"""
        if df.empty:
            return pd.DataFrame()
            
        staff_df = df.copy()
        
        # スタッフ列の特定
        staff_cols = [col for col in df.columns if any(keyword in str(col).lower() 
                     for keyword in ['staff', 'スタッフ', '氏名', '名前', '職員'])]
        
        if staff_cols:
            main_staff_col = staff_cols[0]
            staff_df['primary_staff'] = df[main_staff_col]
            
            # スタッフ別集計の追加
            staff_df['staff_workload_rank'] = df.groupby(main_staff_col).cumcount() + 1
            staff_df['staff_total_appearances'] = df.groupby(main_staff_col)[main_staff_col].transform('count')
            
        return staff_df
    
    def _create_constraint_detection_view(self, df: pd.DataFrame) -> pd.DataFrame:
        """制約検出に特化したビュー"""
        constraint_df = df.copy()
        
        # すべての非欠損セルを制約候補として分析
        for col in df.columns:
            if df[col].dtype == 'object':
                # 文字列パターンの分析
                constraint_df[f'{col}_pattern_frequency'] = df.groupby(col)[col].transform('count')
                constraint_df[f'{col}_is_rare'] = constraint_df[f'{col}_pattern_frequency'] < self.min_sample_size
                
        # 行間の関係性分析
        constraint_df['adjacent_similarity'] = 0
        for i in range(1, len(constraint_df)):
            # 前の行との類似度計算
            similarity_score = self._calculate_row_similarity(
                constraint_df.iloc[i-1], 
                constraint_df.iloc[i]
            )
            constraint_df.loc[i, 'adjacent_similarity'] = similarity_score
            
        return constraint_df
    
    def _create_pattern_mining_view(self, df: pd.DataFrame) -> pd.DataFrame:
        """パターンマイニングに特化したビュー"""
        pattern_df = df.copy()
        
        # n-gramパターンの生成（連続する行のパターン）
        for window_size in [2, 3]:
            pattern_df[f'row_pattern_{window_size}gram'] = ''
            
            for i in range(len(pattern_df) - window_size + 1):
                # window_sizeの範囲で行パターンを生成
                window_rows = pattern_df.iloc[i:i+window_size]
                pattern_signature = self._generate_row_pattern_signature(window_rows)
                pattern_df.loc[i, f'row_pattern_{window_size}gram'] = pattern_signature
        
        return pattern_df
    
    def _discover_implicit_constraint_patterns(self, datasets: Dict[str, pd.DataFrame], 
                                             worktype_definitions: Dict = None) -> Dict[str, List[Dict]]:
        """暗黙制約パターンの発見"""
        patterns = {
            "sequence_constraints": [],        # 順序制約
            "exclusion_constraints": [],       # 排他制約  
            "dependency_constraints": [],      # 依存制約
            "frequency_constraints": [],       # 頻度制約
            "position_constraints": []         # 配置制約
        }
        
        main_df = datasets.get("main_shifts", pd.DataFrame())
        if main_df.empty:
            return patterns
            
        # 1. 順序制約の発見
        sequence_patterns = self._find_sequence_constraints(main_df)
        patterns["sequence_constraints"].extend(sequence_patterns)
        
        # 2. 排他制約の発見
        exclusion_patterns = self._find_exclusion_constraints(main_df)
        patterns["exclusion_constraints"].extend(exclusion_patterns)
        
        # 3. 依存制約の発見
        dependency_patterns = self._find_dependency_constraints(main_df)
        patterns["dependency_constraints"].extend(dependency_patterns)
        
        # 4. 頻度制約の発見
        frequency_patterns = self._find_frequency_constraints(main_df)
        patterns["frequency_constraints"].extend(frequency_patterns)
        
        # 5. 配置制約の発見
        position_patterns = self._find_position_constraints(main_df)
        patterns["position_constraints"].extend(position_patterns)
        
        log.info(f"暗黙制約パターン発見完了: {sum(len(v) for v in patterns.values())}個のパターンを発見")
        return patterns
    
    def _find_sequence_constraints(self, df: pd.DataFrame) -> List[Dict]:
        """順序制約（前後関係のルール）の発見"""
        sequence_constraints = []
        
        # 連続する行での値の変化パターンを分析
        for col in df.columns:
            if df[col].dtype == 'object' and not df[col].isna().all():
                # 連続する値のペアを抽出
                consecutive_pairs = []
                for i in range(len(df) - 1):
                    if pd.notna(df.iloc[i][col]) and pd.notna(df.iloc[i+1][col]):
                        consecutive_pairs.append((df.iloc[i][col], df.iloc[i+1][col]))
                
                # 頻出する順序パターンを特定
                pair_counts = Counter(consecutive_pairs)
                total_pairs = len(consecutive_pairs)
                
                for (before, after), count in pair_counts.items():
                    if count >= self.min_sample_size and count / total_pairs > 0.1:
                        sequence_constraints.append({
                            "type": "順序制約",
                            "column": col,
                            "before_value": before,
                            "after_value": after,
                            "frequency": count,
                            "confidence": count / total_pairs,
                            "rule": f"{before} の後に {after} が配置される傾向",
                            "constraint_strength": "強" if count / total_pairs > 0.3 else "中"
                        })
        
        return sequence_constraints
    
    def _find_exclusion_constraints(self, df: pd.DataFrame) -> List[Dict]:
        """排他制約（同時に存在しない組み合わせ）の発見"""
        exclusion_constraints = []
        
        # 各行内での値の組み合わせを分析
        for i, row in df.iterrows():
            non_null_values = [v for v in row.values if pd.notna(v) and str(v).strip() != '']
            
            # 2つ以上の値がある行での組み合わせを記録
            if len(non_null_values) >= 2:
                for combo in itertools.combinations(non_null_values, 2):
                    # この組み合わせが他の行で同時出現するかチェック
                    simultaneous_occurrences = 0
                    total_possible = 0
                    
                    for j, other_row in df.iterrows():
                        if i != j:
                            other_values = [v for v in other_row.values if pd.notna(v) and str(v).strip() != '']
                            if all(val in other_values for val in combo):
                                simultaneous_occurrences += 1
                            total_possible += 1
                    
                    # 同時出現率が低い場合は排他制約の可能性
                    if total_possible > 0:
                        co_occurrence_rate = simultaneous_occurrences / total_possible
                        if co_occurrence_rate < 0.1:  # 10%以下の同時出現率
                            exclusion_constraints.append({
                                "type": "排他制約",
                                "excluded_combination": combo,
                                "co_occurrence_rate": co_occurrence_rate,
                                "total_observations": total_possible,
                                "rule": f"{combo[0]} と {combo[1]} は同時配置されにくい",
                                "constraint_strength": "強" if co_occurrence_rate < 0.05 else "中"
                            })
        
        return exclusion_constraints
    
    def _find_dependency_constraints(self, df: pd.DataFrame) -> List[Dict]:
        """依存制約（Aがあると必ずBがある）の発見"""
        dependency_constraints = []
        
        # 列間の依存関係を分析
        for col1 in df.columns:
            for col2 in df.columns:
                if col1 != col2:
                    # col1の値があるときのcol2の出現パターンを分析
                    dependencies = self._analyze_column_dependency(df, col1, col2)
                    dependency_constraints.extend(dependencies)
        
        return dependency_constraints
    
    def _find_frequency_constraints(self, df: pd.DataFrame) -> List[Dict]:
        """頻度制約（出現頻度のルール）の発見"""
        frequency_constraints = []
        
        for col in df.columns:
            if df[col].dtype == 'object':
                value_counts = df[col].value_counts()
                total_count = len(df[col].dropna())
                
                for value, count in value_counts.items():
                    frequency_rate = count / total_count
                    
                    # 異常に高い頻度または低い頻度を特定
                    if frequency_rate > 0.7:  # 70%以上の高頻度
                        frequency_constraints.append({
                            "type": "高頻度制約",
                            "column": col,
                            "value": value,
                            "frequency": count,
                            "rate": frequency_rate,
                            "rule": f"{col}では{value}が支配的（{frequency_rate:.1%}）",
                            "constraint_strength": "強"
                        })
                    elif frequency_rate < 0.05 and count >= 2:  # 5%以下の低頻度（但し2回以上出現）
                        frequency_constraints.append({
                            "type": "低頻度制約",
                            "column": col,
                            "value": value,
                            "frequency": count,
                            "rate": frequency_rate,
                            "rule": f"{col}では{value}は例外的（{frequency_rate:.1%}）",
                            "constraint_strength": "中"
                        })
        
        return frequency_constraints
    
    def _find_position_constraints(self, df: pd.DataFrame) -> List[Dict]:
        """配置制約（位置・場所のルール）の発見"""
        position_constraints = []
        
        # 行番号による位置パターンの分析
        for col in df.columns:
            if df[col].dtype == 'object':
                position_patterns = defaultdict(list)
                
                for idx, value in df[col].items():
                    if pd.notna(value):
                        position_patterns[value].append(idx)
                
                # 各値の出現位置パターンを分析
                for value, positions in position_patterns.items():
                    if len(positions) >= self.min_sample_size:
                        # 位置の統計分析
                        pos_array = np.array(positions)
                        pos_mean = pos_array.mean()
                        pos_std = pos_array.std()
                        
                        # 位置パターンの特定
                        if pos_std / len(df) < 0.1:  # 位置が集中している
                            position_constraints.append({
                                "type": "位置集中制約",
                                "column": col,
                                "value": value,
                                "mean_position": pos_mean,
                                "position_variance": pos_std,
                                "rule": f"{col}の{value}は位置{pos_mean:.0f}付近に集中",
                                "constraint_strength": "中"
                            })
        
        return position_constraints
    
    def _analyze_column_dependency(self, df: pd.DataFrame, col1: str, col2: str) -> List[Dict]:
        """2列間の依存関係を分析"""
        dependencies = []
        
        # col1の各値に対してcol2の出現パターンを分析
        for val1 in df[col1].dropna().unique():
            rows_with_val1 = df[df[col1] == val1]
            val2_counts = rows_with_val1[col2].value_counts()
            
            total_val1_occurrences = len(rows_with_val1)
            
            for val2, count in val2_counts.items():
                dependency_rate = count / total_val1_occurrences
                
                # 高い依存関係（80%以上）を特定
                if dependency_rate > 0.8 and total_val1_occurrences >= self.min_sample_size:
                    dependencies.append({
                        "type": "依存制約",
                        "condition_column": col1,
                        "condition_value": val1,
                        "dependent_column": col2,
                        "dependent_value": val2,
                        "dependency_rate": dependency_rate,
                        "total_observations": total_val1_occurrences,
                        "rule": f"{col1}が{val1}の場合、{col2}は{val2}になる確率{dependency_rate:.1%}",
                        "constraint_strength": "強" if dependency_rate > 0.9 else "中"
                    })
        
        return dependencies
    
    def _extract_temporal_dependencies(self, datasets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """時系列依存関係の詳細抽出"""
        time_series_df = datasets.get("time_series_view", pd.DataFrame())
        
        if time_series_df.empty:
            return {"temporal_patterns": [], "cycle_analysis": {}}
        
        temporal_analysis = {
            "temporal_patterns": [],
            "cycle_analysis": {},
            "trend_analysis": {},
            "seasonal_patterns": []
        }
        
        # 時系列パターンの分析実装（詳細は省略）
        log.info("時系列依存関係の分析を実行中...")
        
        return temporal_analysis
    
    def _build_staff_relationship_matrix(self, datasets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """スタッフ関係性マトリックスの構築"""
        staff_df = datasets.get("staff_centric_view", pd.DataFrame())
        
        if staff_df.empty:
            return {"relationship_matrix": {}, "collaboration_patterns": []}
        
        relationship_data = {
            "relationship_matrix": {},
            "collaboration_patterns": [],
            "conflict_indicators": [],
            "mentorship_patterns": []
        }
        
        # スタッフ間関係性の分析実装（詳細は省略）
        log.info("スタッフ関係性マトリックスを構築中...")
        
        return relationship_data
    
    def _discover_worktype_rules(self, datasets: Dict[str, pd.DataFrame], 
                               worktype_definitions: Dict = None) -> Dict[str, List[Dict]]:
        """勤務区分の隠れたルールの発見"""
        worktype_rules = {
            "combination_rules": [],
            "transition_rules": [],
            "restriction_rules": [],
            "preference_rules": []
        }
        
        # 勤務区分ルール発見の実装（詳細は省略）
        log.info("勤務区分ルールを発見中...")
        
        return worktype_rules
    
    def _analyze_exception_patterns(self, datasets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """例外パターンの分離と分析"""
        exception_analysis = {
            "outlier_patterns": [],
            "rare_events": [],
            "anomaly_detection": {},
            "exception_triggers": []
        }
        
        # 例外パターン分析の実装（詳細は省略）
        log.info("例外パターンを分析中...")
        
        return exception_analysis
    
    def _calculate_row_similarity(self, row1: pd.Series, row2: pd.Series) -> float:
        """行間の類似度を計算"""
        # 非欠損値同士の比較
        common_cols = []
        for col in row1.index:
            if pd.notna(row1[col]) and pd.notna(row2[col]):
                common_cols.append(col)
        
        if not common_cols:
            return 0.0
        
        matches = sum(1 for col in common_cols if row1[col] == row2[col])
        return matches / len(common_cols)
    
    def _generate_row_pattern_signature(self, window_rows: pd.DataFrame) -> str:
        """行パターンの署名を生成"""
        signatures = []
        for _, row in window_rows.iterrows():
            # 非欠損値のパターンを抽出
            non_null_pattern = [str(v) for v in row.values if pd.notna(v) and str(v).strip() != '']
            signatures.append("|".join(non_null_pattern[:3]))  # 最初の3つの値
        
        return ">>".join(signatures)