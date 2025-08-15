"""
アプローチ②：既存加工データの更なる深化分析システム
深度19.6%問題の解決のため、既に処理されたデータから高度な制約を抽出

主要機能：
1. 既存分析結果の深化再分析
2. 複数データソースの横断的関連性発見
3. 統計的手法による隠れたパターンの抽出
4. 機械学習手法による制約パターンの自動発見
5. メタ分析による制約の信頼性向上
"""

from __future__ import annotations

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional, Union
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path
import json
from scipy import stats
# sklearn imports removed - using simple implementations
# from sklearn.cluster import DBSCAN
# from sklearn.preprocessing import StandardScaler
# from sklearn.decomposition import PCA

# Simple implementations to replace sklearn
class SimpleStandardScaler:
    """Simple standard scaler implementation"""
    
    def __init__(self):
        self.mean_ = None
        self.scale_ = None
        
    def fit(self, X):
        self.mean_ = np.mean(X, axis=0)
        self.scale_ = np.std(X, axis=0)
        self.scale_[self.scale_ == 0] = 1  # Avoid division by zero
        return self
    
    def transform(self, X):
        return (X - self.mean_) / self.scale_
    
    def fit_transform(self, X):
        return self.fit(X).transform(X)

class SimpleDBSCAN:
    """Simple DBSCAN clustering implementation"""
    
    def __init__(self, eps=0.5, min_samples=5):
        self.eps = eps
        self.min_samples = min_samples
        
    def fit_predict(self, X):
        # Simplified implementation: use statistical outlier detection
        # Calculate distances from centroid
        centroid = np.mean(X, axis=0)
        distances = np.sqrt(np.sum((X - centroid) ** 2, axis=1))
        
        # Use IQR method for outlier detection
        Q1 = np.percentile(distances, 25)
        Q3 = np.percentile(distances, 75)
        IQR = Q3 - Q1
        threshold = Q3 + 1.5 * IQR
        
        # Return cluster labels (-1 for outliers, 0 for normal)
        return np.where(distances > threshold, -1, 0)

class SimplePCA:
    """Simple PCA implementation"""
    
    def __init__(self, n_components=2):
        self.n_components = n_components
        self.explained_variance_ratio_ = None
        
    def fit_transform(self, X):
        # Center the data
        X_centered = X - np.mean(X, axis=0)
        
        # Compute covariance matrix
        cov_matrix = np.cov(X_centered.T)
        
        # Compute eigenvalues and eigenvectors
        eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
        
        # Sort by eigenvalues (descending)
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]
        
        # Select top n_components
        selected_eigenvectors = eigenvectors[:, :self.n_components]
        
        # Calculate explained variance ratio
        self.explained_variance_ratio_ = eigenvalues[:self.n_components] / np.sum(eigenvalues)
        
        # Transform data
        return np.dot(X_centered, selected_eigenvectors)

from .constants import SLOT_HOURS, STATISTICAL_THRESHOLDS
from .utils import gen_labels

log = logging.getLogger(__name__)


class AdvancedProcessedDataAnalyzer:
    """既存加工データから高度制約を抽出する深化分析システム"""
    
    def __init__(self):
        self.confidence_threshold = STATISTICAL_THRESHOLDS['confidence_level']
        self.min_sample_size = STATISTICAL_THRESHOLDS['min_sample_size']
        self.correlation_threshold = STATISTICAL_THRESHOLDS['correlation_threshold']
        
    def analyze_processed_data_for_advanced_constraints(self, 
                                                      processed_data_dir: str,
                                                      analysis_results: Dict = None) -> Dict[str, Any]:
        """既存加工データから高度制約を抽出
        
        Args:
            processed_data_dir: 加工済みデータディレクトリ
            analysis_results: 既存の分析結果辞書
            
        Returns:
            高度制約分析結果辞書
        """
        log.info("既存加工データからの高度制約分析を開始...")
        
        # 1. 既存データの統合読み込み
        integrated_datasets = self._load_and_integrate_processed_data(processed_data_dir)
        
        # 2. 横断的関連性分析
        cross_domain_relationships = self._analyze_cross_domain_relationships(integrated_datasets)
        
        # 3. 統計的高度パターン抽出
        statistical_patterns = self._extract_statistical_advanced_patterns(integrated_datasets)
        
        # 4. 機械学習による制約発見
        ml_discovered_constraints = self._discover_constraints_via_ml(integrated_datasets)
        
        # 5. メタ分析による制約信頼性評価
        meta_analysis_results = self._perform_meta_analysis(integrated_datasets, analysis_results)
        
        # 6. 制約階層化と優先度付け
        hierarchical_constraints = self._hierarchize_constraints(
            cross_domain_relationships, statistical_patterns, ml_discovered_constraints
        )
        
        return {
            "processing_metadata": {
                "timestamp": datetime.now().isoformat(),
                "approach": "②既存データ深化分析",
                "data_sources": list(integrated_datasets.keys()),
                "analysis_confidence": self.confidence_threshold
            },
            "integrated_datasets": integrated_datasets,
            "cross_domain_relationships": cross_domain_relationships,
            "statistical_patterns": statistical_patterns,
            "ml_constraints": ml_discovered_constraints,
            "meta_analysis": meta_analysis_results,
            "hierarchical_constraints": hierarchical_constraints
        }
    
    def _load_and_integrate_processed_data(self, data_dir: str) -> Dict[str, pd.DataFrame]:
        """加工済みデータの統合読み込み"""
        integrated_data = {}
        data_path = Path(data_dir)
        
        if not data_path.exists():
            log.warning(f"データディレクトリが存在しません: {data_dir}")
            return integrated_data
        
        # Parquetファイルの読み込み
        for parquet_file in data_path.glob("*.parquet"):
            try:
                df = pd.read_parquet(parquet_file)
                dataset_name = parquet_file.stem
                integrated_data[dataset_name] = df
                log.info(f"データセット読み込み: {dataset_name} ({df.shape})")
            except Exception as e:
                log.error(f"Parquetファイル読み込みエラー {parquet_file}: {e}")
        
        # CSVファイルの読み込み
        for csv_file in data_path.glob("*.csv"):
            try:
                df = pd.read_csv(csv_file)
                dataset_name = csv_file.stem
                if dataset_name not in integrated_data:  # Parquetが優先
                    integrated_data[dataset_name] = df
                    log.info(f"データセット読み込み: {dataset_name} ({df.shape})")
            except Exception as e:
                log.error(f"CSVファイル読み込みエラー {csv_file}: {e}")
        
        # データ品質チェックと前処理
        for name, df in integrated_data.items():
            integrated_data[name] = self._preprocess_integrated_data(df, name)
        
        log.info(f"統合データ読み込み完了: {len(integrated_data)}個のデータセット")
        return integrated_data
    
    def _preprocess_integrated_data(self, df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
        """統合データの前処理"""
        if df.empty:
            return df
            
        processed_df = df.copy()
        
        # 日付列の正規化
        date_columns = [col for col in df.columns if 'date' in col.lower() or '日' in col]
        for date_col in date_columns:
            try:
                processed_df[date_col] = pd.to_datetime(processed_df[date_col], errors='coerce')
            except:
                continue
        
        # 数値列の正規化
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for num_col in numeric_columns:
            # 外れ値の識別
            Q1 = processed_df[num_col].quantile(0.25)
            Q3 = processed_df[num_col].quantile(0.75)
            IQR = Q3 - Q1
            outlier_mask = (processed_df[num_col] < (Q1 - 1.5 * IQR)) | (processed_df[num_col] > (Q3 + 1.5 * IQR))
            processed_df[f'{num_col}_is_outlier'] = outlier_mask
        
        # メタデータの追加
        processed_df['_dataset_source'] = dataset_name
        processed_df['_row_id'] = range(len(processed_df))
        
        return processed_df
    
    def _analyze_cross_domain_relationships(self, datasets: Dict[str, pd.DataFrame]) -> Dict[str, List[Dict]]:
        """横断的関連性分析"""
        relationships = {
            "inter_dataset_correlations": [],    # データセット間相関
            "shared_pattern_analysis": [],       # 共通パターン分析
            "complementary_constraints": [],     # 補完制約
            "conflicting_indicators": []         # 矛盾指標
        }
        
        dataset_names = list(datasets.keys())
        
        # データセット間の相関分析
        for i, name1 in enumerate(dataset_names):
            for name2 in dataset_names[i+1:]:
                df1, df2 = datasets[name1], datasets[name2]
                
                # 共通列の特定
                common_columns = set(df1.columns) & set(df2.columns)
                if len(common_columns) >= 2:
                    correlation_analysis = self._analyze_dataset_correlation(df1, df2, name1, name2, common_columns)
                    relationships["inter_dataset_correlations"].extend(correlation_analysis)
        
        # 共通パターンの分析
        shared_patterns = self._find_shared_patterns_across_datasets(datasets)
        relationships["shared_pattern_analysis"] = shared_patterns
        
        # 補完制約の発見
        complementary_constraints = self._find_complementary_constraints(datasets)
        relationships["complementary_constraints"] = complementary_constraints
        
        log.info(f"横断的関連性分析完了: {sum(len(v) for v in relationships.values())}個の関係性を発見")
        return relationships
    
    def _analyze_dataset_correlation(self, df1: pd.DataFrame, df2: pd.DataFrame, 
                                   name1: str, name2: str, common_columns: set) -> List[Dict]:
        """2つのデータセット間の相関分析"""
        correlations = []
        
        for col in common_columns:
            if col.startswith('_'):  # メタデータ列は除外
                continue
                
            # 数値列の場合
            if pd.api.types.is_numeric_dtype(df1[col]) and pd.api.types.is_numeric_dtype(df2[col]):
                try:
                    # 統計値の比較
                    stat1 = {"mean": df1[col].mean(), "std": df1[col].std(), "median": df1[col].median()}
                    stat2 = {"mean": df2[col].mean(), "std": df2[col].std(), "median": df2[col].median()}
                    
                    # 統計的類似度の計算
                    mean_diff = abs(stat1["mean"] - stat2["mean"]) / max(stat1["mean"], stat2["mean"], 1)
                    
                    if mean_diff < 0.2:  # 20%以内の差
                        correlations.append({
                            "type": "数値統計類似性",
                            "column": col,
                            "dataset1": name1,
                            "dataset2": name2,
                            "similarity_score": 1 - mean_diff,
                            "stat1": stat1,
                            "stat2": stat2,
                            "constraint_implication": f"{col}の値範囲は両データセットで一致"
                        })
                except:
                    continue
            
            # カテゴリ列の場合
            elif df1[col].dtype == 'object' and df2[col].dtype == 'object':
                unique1 = set(df1[col].dropna().unique())
                unique2 = set(df2[col].dropna().unique())
                
                overlap = unique1 & unique2
                union = unique1 | unique2
                
                if len(union) > 0:
                    jaccard_similarity = len(overlap) / len(union)
                    
                    if jaccard_similarity > 0.5:  # 50%以上の類似度
                        correlations.append({
                            "type": "カテゴリ値類似性",
                            "column": col,
                            "dataset1": name1,
                            "dataset2": name2,
                            "jaccard_similarity": jaccard_similarity,
                            "common_values": list(overlap),
                            "unique_to_1": list(unique1 - unique2),
                            "unique_to_2": list(unique2 - unique1),
                            "constraint_implication": f"{col}の取り得る値セットは共通性がある"
                        })
        
        return correlations
    
    def _find_shared_patterns_across_datasets(self, datasets: Dict[str, pd.DataFrame]) -> List[Dict]:
        """データセット横断の共通パターン発見"""
        shared_patterns = []
        
        # 時間パターンの共通性分析
        time_patterns = self._analyze_temporal_patterns_across_datasets(datasets)
        shared_patterns.extend(time_patterns)
        
        # 頻度パターンの共通性分析
        frequency_patterns = self._analyze_frequency_patterns_across_datasets(datasets)
        shared_patterns.extend(frequency_patterns)
        
        return shared_patterns
    
    def _analyze_temporal_patterns_across_datasets(self, datasets: Dict[str, pd.DataFrame]) -> List[Dict]:
        """時間パターンの横断分析"""
        temporal_patterns = []
        
        for name, df in datasets.items():
            # 日付列の特定
            date_columns = [col for col in df.columns if df[col].dtype == 'datetime64[ns]']
            
            for date_col in date_columns:
                if not df[date_col].isna().all():
                    # 曜日パターンの抽出
                    weekday_pattern = df[date_col].dt.dayofweek.value_counts().to_dict()
                    
                    # 月次パターンの抽出
                    monthly_pattern = df[date_col].dt.month.value_counts().to_dict()
                    
                    temporal_patterns.append({
                        "type": "時間パターン",
                        "dataset": name,
                        "date_column": date_col,
                        "weekday_distribution": weekday_pattern,
                        "monthly_distribution": monthly_pattern,
                        "pattern_entropy": self._calculate_entropy(list(weekday_pattern.values())),
                        "constraint_implication": f"{name}の{date_col}は特定の時間パターンを持つ"
                    })
        
        return temporal_patterns
    
    def _analyze_frequency_patterns_across_datasets(self, datasets: Dict[str, pd.DataFrame]) -> List[Dict]:
        """頻度パターンの横断分析"""
        frequency_patterns = []
        
        # 各データセットの値頻度パターンを抽出
        dataset_patterns = {}
        
        for name, df in datasets.items():
            for col in df.columns:
                if df[col].dtype == 'object' and not col.startswith('_'):
                    value_counts = df[col].value_counts()
                    if len(value_counts) > 1:  # 複数の値がある場合
                        pattern_key = f"{name}_{col}"
                        dataset_patterns[pattern_key] = {
                            "dataset": name,
                            "column": col,
                            "value_distribution": value_counts.to_dict(),
                            "entropy": self._calculate_entropy(value_counts.values),
                            "top_values": value_counts.head(3).index.tolist()
                        }
        
        # パターン間の類似性分析
        pattern_keys = list(dataset_patterns.keys())
        for i, key1 in enumerate(pattern_keys):
            for key2 in pattern_keys[i+1:]:
                pattern1 = dataset_patterns[key1]
                pattern2 = dataset_patterns[key2]
                
                # 上位値の共通性チェック
                common_top_values = set(pattern1["top_values"]) & set(pattern2["top_values"])
                
                if len(common_top_values) >= 2:  # 2つ以上の共通上位値
                    frequency_patterns.append({
                        "type": "頻度パターン類似性",
                        "pattern1": key1,
                        "pattern2": key2,
                        "common_top_values": list(common_top_values),
                        "entropy_similarity": 1 - abs(pattern1["entropy"] - pattern2["entropy"]),
                        "constraint_implication": f"{key1}と{key2}は類似した値分布を持つ"
                    })
        
        return frequency_patterns
    
    def _find_complementary_constraints(self, datasets: Dict[str, pd.DataFrame]) -> List[Dict]:
        """補完制約の発見"""
        complementary_constraints = []
        
        # データセット間の補完関係を分析
        dataset_pairs = [(n1, n2) for i, n1 in enumerate(datasets.keys()) 
                        for n2 in list(datasets.keys())[i+1:]]
        
        for name1, name2 in dataset_pairs:
            df1, df2 = datasets[name1], datasets[name2]
            
            # 情報の補完性をチェック
            complementarity = self._analyze_information_complementarity(df1, df2, name1, name2)
            if complementarity:
                complementary_constraints.extend(complementarity)
        
        return complementary_constraints
    
    def _analyze_information_complementarity(self, df1: pd.DataFrame, df2: pd.DataFrame,
                                           name1: str, name2: str) -> List[Dict]:
        """情報の補完性分析"""
        complementarity = []
        
        # 列の情報量比較
        cols1 = set(df1.columns) - {'_dataset_source', '_row_id'}
        cols2 = set(df2.columns) - {'_dataset_source', '_row_id'}
        
        unique_to_1 = cols1 - cols2
        unique_to_2 = cols2 - cols1
        
        if len(unique_to_1) > 0 and len(unique_to_2) > 0:
            complementarity.append({
                "type": "列情報補完性",
                "dataset1": name1,
                "dataset2": name2,
                "unique_columns_1": list(unique_to_1),
                "unique_columns_2": list(unique_to_2),
                "complementarity_score": len(unique_to_1) + len(unique_to_2),
                "constraint_implication": f"{name1}と{name2}は異なる情報軸を提供"
            })
        
        return complementarity
    
    def _extract_statistical_advanced_patterns(self, datasets: Dict[str, pd.DataFrame]) -> Dict[str, List[Dict]]:
        """統計的高度パターン抽出"""
        patterns = {
            "distribution_analysis": [],        # 分布分析
            "anomaly_detection": [],           # 異常検出
            "clustering_patterns": [],         # クラスタリングパターン
            "correlation_networks": []         # 相関ネットワーク
        }
        
        for name, df in datasets.items():
            if df.empty:
                continue
            
            # 分布分析
            distribution_patterns = self._analyze_statistical_distributions(df, name)
            patterns["distribution_analysis"].extend(distribution_patterns)
            
            # 異常検出
            anomaly_patterns = self._detect_statistical_anomalies(df, name)
            patterns["anomaly_detection"].extend(anomaly_patterns)
            
            # クラスタリング分析
            clustering_patterns = self._perform_clustering_analysis(df, name)
            patterns["clustering_patterns"].extend(clustering_patterns)
        
        log.info(f"統計的パターン抽出完了: {sum(len(v) for v in patterns.values())}個のパターン")
        return patterns
    
    def _analyze_statistical_distributions(self, df: pd.DataFrame, dataset_name: str) -> List[Dict]:
        """統計分布の分析"""
        distribution_patterns = []
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            if col.startswith('_'):  # メタデータ列は除外
                continue
                
            values = df[col].dropna()
            if len(values) < self.min_sample_size:
                continue
            
            # 基本統計量
            stats_dict = {
                "mean": values.mean(),
                "median": values.median(),
                "std": values.std(),
                "skewness": stats.skew(values),
                "kurtosis": stats.kurtosis(values)
            }
            
            # 分布の正規性テスト
            try:
                normality_stat, normality_p = stats.shapiro(values[:5000] if len(values) > 5000 else values)
                is_normal = normality_p > 0.05
            except:
                is_normal = False
                normality_p = 0
            
            # 分布の特徴判定
            distribution_type = "unknown"
            if is_normal:
                distribution_type = "normal"
            elif abs(stats_dict["skewness"]) > 1:
                distribution_type = "highly_skewed"
            elif stats_dict["kurtosis"] > 3:
                distribution_type = "heavy_tailed"
            
            distribution_patterns.append({
                "type": "分布分析",
                "dataset": dataset_name,
                "column": col,
                "distribution_type": distribution_type,
                "statistics": stats_dict,
                "normality_p_value": normality_p,
                "sample_size": len(values),
                "constraint_implication": f"{col}は{distribution_type}分布に従う制約がある"
            })
        
        return distribution_patterns
    
    def _detect_statistical_anomalies(self, df: pd.DataFrame, dataset_name: str) -> List[Dict]:
        """統計的異常検出"""
        anomaly_patterns = []
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        numeric_columns = [col for col in numeric_columns if not col.startswith('_')]
        
        if len(numeric_columns) < 2:
            return anomaly_patterns
        
        # 数値データの標準化
        numeric_data = df[numeric_columns].fillna(0)
        if len(numeric_data) < self.min_sample_size:
            return anomaly_patterns
        
        try:
            scaler = SimpleStandardScaler()
            scaled_data = scaler.fit_transform(numeric_data)
            
            # DBSCAN による異常検出
            dbscan = SimpleDBSCAN(eps=0.5, min_samples=5)
            clusters = dbscan.fit_predict(scaled_data)
            
            # 外れ値（cluster -1）の分析
            outlier_indices = np.where(clusters == -1)[0]
            
            if len(outlier_indices) > 0:
                outlier_rate = len(outlier_indices) / len(df)
                
                anomaly_patterns.append({
                    "type": "クラスタベース異常検出",
                    "dataset": dataset_name,
                    "outlier_count": len(outlier_indices),
                    "outlier_rate": outlier_rate,
                    "analyzed_columns": list(numeric_columns),
                    "constraint_implication": f"約{outlier_rate:.1%}のデータが異常パターンを示す"
                })
        
        except Exception as e:
            log.warning(f"異常検出エラー ({dataset_name}): {e}")
        
        return anomaly_patterns
    
    def _perform_clustering_analysis(self, df: pd.DataFrame, dataset_name: str) -> List[Dict]:
        """クラスタリング分析"""
        clustering_patterns = []
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        numeric_columns = [col for col in numeric_columns if not col.startswith('_')]
        
        if len(numeric_columns) < 2:
            return clustering_patterns
        
        numeric_data = df[numeric_columns].fillna(0)
        if len(numeric_data) < self.min_sample_size:
            return clustering_patterns
        
        try:
            # PCA による次元削減と分析
            pca = SimplePCA(n_components=min(3, len(numeric_columns)))
            pca_result = pca.fit_transform(SimpleStandardScaler().fit_transform(numeric_data))
            
            explained_variance_ratio = pca.explained_variance_ratio_
            
            clustering_patterns.append({
                "type": "PCA次元分析",
                "dataset": dataset_name,
                "original_dimensions": len(numeric_columns),
                "explained_variance_ratio": explained_variance_ratio.tolist(),
                "cumulative_variance": np.cumsum(explained_variance_ratio).tolist(),
                "constraint_implication": f"データは{len(explained_variance_ratio)}次元で{explained_variance_ratio.sum():.1%}の情報を説明"
            })
            
        except Exception as e:
            log.warning(f"クラスタリング分析エラー ({dataset_name}): {e}")
        
        return clustering_patterns
    
    def _discover_constraints_via_ml(self, datasets: Dict[str, pd.DataFrame]) -> Dict[str, List[Dict]]:
        """機械学習による制約発見"""
        ml_constraints = {
            "pattern_classification": [],      # パターン分類
            "feature_importance": [],          # 特徴量重要度
            "association_rules": [],           # 関連ルール
            "predictive_constraints": []       # 予測制約
        }
        
        # 各データセットに対してML分析を実行
        for name, df in datasets.items():
            if len(df) < self.min_sample_size:
                continue
            
            # 特徴量重要度の分析
            feature_importance = self._analyze_feature_importance(df, name)
            ml_constraints["feature_importance"].extend(feature_importance)
            
            # 関連ルールの発見
            association_rules = self._discover_association_rules(df, name)
            ml_constraints["association_rules"].extend(association_rules)
        
        log.info(f"ML制約発見完了: {sum(len(v) for v in ml_constraints.values())}個の制約")
        return ml_constraints
    
    def _analyze_feature_importance(self, df: pd.DataFrame, dataset_name: str) -> List[Dict]:
        """特徴量重要度の分析"""
        importance_results = []
        
        # 簡単な相関ベースの重要度分析
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        numeric_columns = [col for col in numeric_columns if not col.startswith('_')]
        
        if len(numeric_columns) < 2:
            return importance_results
        
        correlation_matrix = df[numeric_columns].corr().abs()
        
        # 各列の他列との相関の平均を重要度として計算
        for col in numeric_columns:
            other_cols = [c for c in numeric_columns if c != col]
            if other_cols:
                avg_correlation = correlation_matrix.loc[col, other_cols].mean()
                
                if avg_correlation > 0.3:  # 30%以上の相関
                    importance_results.append({
                        "type": "相関ベース重要度",
                        "dataset": dataset_name,
                        "feature": col,
                        "importance_score": avg_correlation,
                        "related_features": other_cols,
                        "constraint_implication": f"{col}は他の特徴量と強い関連性を持つ"
                    })
        
        return importance_results
    
    def _discover_association_rules(self, df: pd.DataFrame, dataset_name: str) -> List[Dict]:
        """関連ルールの発見"""
        association_rules = []
        
        # カテゴリカル列の組み合わせを分析
        categorical_columns = df.select_dtypes(include=['object']).columns
        categorical_columns = [col for col in categorical_columns if not col.startswith('_')]
        
        if len(categorical_columns) < 2:
            return association_rules
        
        # 2列間の関連性を分析
        for i, col1 in enumerate(categorical_columns):
            for col2 in categorical_columns[i+1:]:
                contingency_table = pd.crosstab(df[col1], df[col2])
                
                if contingency_table.shape[0] > 1 and contingency_table.shape[1] > 1:
                    # カイ二乗検定
                    try:
                        chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
                        
                        if p_value < 0.05:  # 有意な関連性
                            association_rules.append({
                                "type": "関連ルール",
                                "dataset": dataset_name,
                                "column1": col1,
                                "column2": col2,
                                "chi2_statistic": chi2,
                                "p_value": p_value,
                                "association_strength": "強" if p_value < 0.01 else "中",
                                "constraint_implication": f"{col1}と{col2}の値は統計的に関連している"
                            })
                    except:
                        continue
        
        return association_rules
    
    def _perform_meta_analysis(self, datasets: Dict[str, pd.DataFrame], 
                             analysis_results: Dict = None) -> Dict[str, Any]:
        """メタ分析による制約信頼性評価"""
        meta_analysis = {
            "data_quality_assessment": {},
            "consistency_analysis": {},
            "reliability_scores": {},
            "recommendation_ranking": []
        }
        
        # データ品質評価
        meta_analysis["data_quality_assessment"] = self._assess_data_quality(datasets)
        
        # 一貫性分析
        meta_analysis["consistency_analysis"] = self._analyze_consistency_across_datasets(datasets)
        
        # 制約の信頼性スコア
        if analysis_results:
            meta_analysis["reliability_scores"] = self._calculate_constraint_reliability(
                datasets, analysis_results
            )
        
        return meta_analysis
    
    def _assess_data_quality(self, datasets: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """データ品質評価"""
        quality_assessment = {}
        
        for name, df in datasets.items():
            if df.empty:
                quality_assessment[name] = {"quality_score": 0, "issues": ["Empty dataset"]}
                continue
            
            # 基本品質指標
            total_cells = df.shape[0] * df.shape[1]
            missing_cells = df.isna().sum().sum()
            completeness = 1 - (missing_cells / total_cells) if total_cells > 0 else 0
            
            # 重複レコード
            duplicate_rate = df.duplicated().sum() / len(df) if len(df) > 0 else 0
            
            # データ型の一貫性
            type_consistency = self._check_type_consistency(df)
            
            quality_score = (completeness * 0.4 + (1 - duplicate_rate) * 0.3 + type_consistency * 0.3)
            
            quality_assessment[name] = {
                "quality_score": quality_score,
                "completeness": completeness,
                "duplicate_rate": duplicate_rate,
                "type_consistency": type_consistency,
                "row_count": len(df),
                "column_count": len(df.columns)
            }
        
        return quality_assessment
    
    def _check_type_consistency(self, df: pd.DataFrame) -> float:
        """データ型の一貫性チェック"""
        if df.empty:
            return 0.0
        
        consistent_columns = 0
        total_columns = len(df.columns)
        
        for col in df.columns:
            if col.startswith('_'):
                continue
            
            # 数値列で文字列が混在していないかチェック
            if pd.api.types.is_numeric_dtype(df[col]):
                consistent_columns += 1
            elif df[col].dtype == 'object':
                # 文字列列で数値のみのセルが多すぎないかチェック
                numeric_count = df[col].apply(lambda x: str(x).replace('.', '').isdigit() if pd.notna(x) else False).sum()
                if numeric_count / len(df) < 0.8:  # 80%未満が数値なら一貫している
                    consistent_columns += 1
        
        return consistent_columns / total_columns if total_columns > 0 else 0
    
    def _analyze_consistency_across_datasets(self, datasets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """データセット間の一貫性分析"""
        consistency_analysis = {
            "schema_consistency": {},
            "value_consistency": {},
            "temporal_consistency": {}
        }
        
        # スキーマ一貫性（列名、データ型の一致度）
        all_columns = set()
        dataset_schemas = {}
        
        for name, df in datasets.items():
            schema = {col: str(df[col].dtype) for col in df.columns}
            dataset_schemas[name] = schema
            all_columns.update(df.columns)
        
        consistency_analysis["schema_consistency"] = {
            "total_unique_columns": len(all_columns),
            "dataset_schemas": dataset_schemas,
            "common_columns": list(set.intersection(*[set(schema.keys()) for schema in dataset_schemas.values()]))
        }
        
        return consistency_analysis
    
    def _calculate_constraint_reliability(self, datasets: Dict[str, pd.DataFrame],
                                        analysis_results: Dict) -> Dict[str, float]:
        """制約の信頼性スコア計算"""
        reliability_scores = {}
        
        # データ品質に基づく基本信頼性
        quality_scores = self._assess_data_quality(datasets)
        avg_quality = np.mean([score["quality_score"] for score in quality_scores.values()])
        
        reliability_scores["data_quality_base"] = avg_quality
        reliability_scores["sample_size_adequacy"] = min(1.0, sum(len(df) for df in datasets.values()) / 1000)
        reliability_scores["overall_reliability"] = (avg_quality + reliability_scores["sample_size_adequacy"]) / 2
        
        return reliability_scores
    
    def _hierarchize_constraints(self, cross_domain: Dict, statistical: Dict, ml_constraints: Dict) -> Dict[str, List[Dict]]:
        """制約の階層化と優先度付け"""
        hierarchical = {
            "tier1_critical": [],      # 最重要制約
            "tier2_important": [],     # 重要制約
            "tier3_optional": []       # オプション制約
        }
        
        # 各制約に優先度を付与して分類
        all_constraints = []
        
        # 横断的関連性の制約
        for category, constraints in cross_domain.items():
            for constraint in constraints:
                constraint["source_category"] = category
                constraint["source_type"] = "cross_domain"
                all_constraints.append(constraint)
        
        # 統計的制約  
        for category, constraints in statistical.items():
            for constraint in constraints:
                constraint["source_category"] = category
                constraint["source_type"] = "statistical"
                all_constraints.append(constraint)
        
        # ML制約
        for category, constraints in ml_constraints.items():
            for constraint in constraints:
                constraint["source_category"] = category
                constraint["source_type"] = "ml"
                all_constraints.append(constraint)
        
        # 優先度の判定と分類
        for constraint in all_constraints:
            priority_score = self._calculate_constraint_priority(constraint)
            constraint["priority_score"] = priority_score
            
            if priority_score >= 0.8:
                hierarchical["tier1_critical"].append(constraint)
            elif priority_score >= 0.5:
                hierarchical["tier2_important"].append(constraint)
            else:
                hierarchical["tier3_optional"].append(constraint)
        
        # 各階層内でスコア順にソート
        for tier in hierarchical.values():
            tier.sort(key=lambda x: x["priority_score"], reverse=True)
        
        log.info(f"制約階層化完了: Tier1={len(hierarchical['tier1_critical'])}, "
                f"Tier2={len(hierarchical['tier2_important'])}, Tier3={len(hierarchical['tier3_optional'])}")
        
        return hierarchical
    
    def _calculate_constraint_priority(self, constraint: Dict) -> float:
        """制約の優先度スコア計算"""
        base_score = 0.5
        
        # ソースタイプによる重み
        if constraint["source_type"] == "cross_domain":
            base_score += 0.2
        elif constraint["source_type"] == "statistical":
            base_score += 0.15
        elif constraint["source_type"] == "ml":
            base_score += 0.1
        
        # 統計的信頼性による重み
        if "p_value" in constraint and constraint["p_value"] < 0.01:
            base_score += 0.2
        elif "confidence" in constraint and constraint["confidence"] > 0.8:
            base_score += 0.15
        
        # 実用性による重み
        if "constraint_implication" in constraint and len(constraint["constraint_implication"]) > 0:
            base_score += 0.1
        
        return min(1.0, base_score)
    
    def _calculate_entropy(self, values: List[Union[int, float]]) -> float:
        """エントロピーの計算"""
        if not values:
            return 0.0
        
        total = sum(values)
        if total == 0:
            return 0.0
        
        probabilities = [v / total for v in values if v > 0]
        return -sum(p * np.log2(p) for p in probabilities)