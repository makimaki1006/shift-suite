"""
shift_suite.tasks.seasonal_analysis - 季節性分析エンジン
────────────────────────────────────────────────────────────────
■ 実装内容
  1. 時系列データの季節性パターン検出
  2. 季節調整と傾向分析
  3. 休日・祝日の影響分析
  4. 年間・月間・週間・日内周期の解析
  5. 季節性異常値の検出
  6. 将来の季節性パターン予測
"""

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
# sklearn imports removed - using simple implementations
# from sklearn.preprocessing import StandardScaler
# from sklearn.decomposition import PCA
# from sklearn.cluster import KMeans

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

class SimpleKMeans:
    """Simple K-Means clustering implementation"""
    
    def __init__(self, n_clusters=3, max_iter=100, random_state=None):
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.random_state = random_state
        
    def fit(self, X):
        if self.random_state:
            np.random.seed(self.random_state)
            
        # Initialize centroids randomly
        n_samples, n_features = X.shape
        self.centroids = X[np.random.choice(n_samples, self.n_clusters, replace=False)]
        
        for _ in range(self.max_iter):
            # Assign points to nearest centroid
            distances = np.sqrt(((X - self.centroids[:, np.newaxis])**2).sum(axis=2))
            labels = np.argmin(distances, axis=0)
            
            # Update centroids
            new_centroids = np.array([X[labels == k].mean(axis=0) for k in range(self.n_clusters)])
            
            # Check for convergence
            if np.allclose(self.centroids, new_centroids):
                break
                
            self.centroids = new_centroids
            
        return self
    
    def predict(self, X):
        distances = np.sqrt(((X - self.centroids[:, np.newaxis])**2).sum(axis=2))
        return np.argmin(distances, axis=0)
    
    def fit_predict(self, X):
        return self.fit(X).predict(X)
import warnings

from .utils import log, save_df_parquet, write_meta

# 統計分析ライブラリ
try:
    import statsmodels.api as sm
    from statsmodels.tsa.seasonal import seasonal_decompose, STL
    from statsmodels.tsa.stattools import adfuller
    from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
    _HAS_STATSMODELS = True
    log.info("[seasonal_analysis] Statsmodels detected -- Advanced seasonal analysis enabled")
except ImportError:
    _HAS_STATSMODELS = False
    log.warning("[seasonal_analysis] Statsmodels not available -- Basic seasonal analysis only")

# SciPyライブラリ
try:
    from scipy import signal, stats
    from scipy.fft import fft, fftfreq
    _HAS_SCIPY = True
    log.info("[seasonal_analysis] SciPy detected -- Spectral analysis enabled")
except ImportError:
    _HAS_SCIPY = False
    log.warning("[seasonal_analysis] SciPy not available -- Spectral analysis disabled")


class SeasonalAnalysisEngine:
    """季節性分析エンジン"""
    
    def __init__(self, 
                 enable_decomposition: bool = True,
                 enable_spectral: bool = True,
                 enable_holiday_effects: bool = True,
                 enable_clustering: bool = True):
        """
        Parameters
        ----------
        enable_decomposition : bool, default True
            時系列分解による季節性分析を有効にするか
        enable_spectral : bool, default True
            スペクトル解析による周期性検出を有効にするか
        enable_holiday_effects : bool, default True
            祝日・休日効果の分析を有効にするか
        enable_clustering : bool, default True
            季節性パターンのクラスタリングを有効にするか
        """
        self.enable_decomposition = enable_decomposition and _HAS_STATSMODELS
        self.enable_spectral = enable_spectral and _HAS_SCIPY
        self.enable_holiday_effects = enable_holiday_effects
        self.enable_clustering = enable_clustering
        
        self.decomposition_results: Dict[str, Any] = {}
        self.spectral_results: Dict[str, Any] = {}
        self.holiday_effects: Dict[str, Any] = {}
        self.seasonal_patterns: Dict[str, Any] = {}
        
        log.info(f"[SeasonalAnalysisEngine] Initialized with decomposition={self.enable_decomposition}, "
                f"spectral={self.enable_spectral}, holiday={self.enable_holiday_effects}, "
                f"clustering={self.enable_clustering}")
    
    def prepare_time_series_data(self, long_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """時系列データの準備と前処理"""
        time_series_data = {}
        
        # 基本的な時系列データを作成
        long_df = long_df.copy()
        long_df['ds'] = pd.to_datetime(long_df['ds'])
        
        # 全体の人員数時系列
        daily_total = long_df.groupby('ds').size().reset_index(name='count')
        daily_total = daily_total.set_index('ds').resample('D').sum().fillna(0)
        time_series_data['total_staff'] = daily_total
        
        # 職種別時系列
        if 'role' in long_df.columns:
            for role in long_df['role'].unique():
                role_data = long_df[long_df['role'] == role].groupby('ds').size().reset_index(name='count')
                role_data = role_data.set_index('ds').resample('D').sum().fillna(0)
                time_series_data[f'role_{role}'] = role_data
        
        # 雇用形態別時系列
        if 'employment' in long_df.columns:
            for emp in long_df['employment'].unique():
                emp_data = long_df[long_df['employment'] == emp].groupby('ds').size().reset_index(name='count')
                emp_data = emp_data.set_index('ds').resample('D').sum().fillna(0)
                time_series_data[f'employment_{emp}'] = emp_data
        
        # 時間帯別パターン（日内周期）
        long_df['hour'] = long_df['ds'].dt.hour
        hourly_pattern = long_df.groupby('hour').size().reset_index(name='count')
        time_series_data['hourly_pattern'] = hourly_pattern
        
        # 曜日別パターン（週間周期）
        long_df['weekday'] = long_df['ds'].dt.dayofweek
        weekly_pattern = long_df.groupby('weekday').size().reset_index(name='count')
        time_series_data['weekly_pattern'] = weekly_pattern
        
        return time_series_data
    
    def detect_seasonal_components(self, ts_data: pd.Series, period: int = 365) -> Dict[str, Any]:
        """季節性成分の分解と検出"""
        if not self.enable_decomposition:
            log.warning("[SeasonalAnalysisEngine] Seasonal decomposition disabled")
            return {}
        
        try:
            # データの準備
            ts_clean = ts_data.dropna()
            if len(ts_clean) < period * 2:
                log.warning(f"[SeasonalAnalysisEngine] Insufficient data for seasonal analysis: {len(ts_clean)} < {period * 2}")
                return {}
            
            # STL分解（Seasonal and Trend decomposition using Loess）
            stl = STL(ts_clean, seasonal=period, robust=True)
            stl_result = stl.fit()
            
            # 古典的な季節分解
            classical_decomp = seasonal_decompose(ts_clean, model='additive', period=period)
            
            # 季節性の強度を計算
            seasonal_strength = np.var(stl_result.seasonal) / np.var(ts_clean)
            trend_strength = np.var(stl_result.trend.dropna()) / np.var(ts_clean)
            
            # 季節性パターンの統計
            seasonal_pattern = stl_result.seasonal.groupby(stl_result.seasonal.index % period).mean()
            
            return {
                'stl_trend': stl_result.trend,
                'stl_seasonal': stl_result.seasonal,
                'stl_resid': stl_result.resid,
                'classical_trend': classical_decomp.trend,
                'classical_seasonal': classical_decomp.seasonal,
                'classical_resid': classical_decomp.resid,
                'seasonal_strength': seasonal_strength,
                'trend_strength': trend_strength,
                'seasonal_pattern': seasonal_pattern,
                'period': period
            }
            
        except Exception as e:
            log.error(f"[SeasonalAnalysisEngine] Seasonal decomposition failed: {e}")
            return {}
    
    def perform_spectral_analysis(self, ts_data: pd.Series) -> Dict[str, Any]:
        """スペクトル解析による周期性検出"""
        if not self.enable_spectral:
            log.warning("[SeasonalAnalysisEngine] Spectral analysis disabled")
            return {}
        
        try:
            # データの準備
            ts_clean = ts_data.dropna().values
            if len(ts_clean) < 100:
                log.warning("[SeasonalAnalysisEngine] Insufficient data for spectral analysis")
                return {}
            
            # FFT解析
            fft_values = fft(ts_clean)
            fft_freq = fftfreq(len(ts_clean))
            
            # パワースペクトル密度
            power_spectrum = np.abs(fft_values) ** 2
            
            # 主要な周期の検出
            # 低周波成分（長期周期）に焦点
            positive_freq_mask = fft_freq > 0
            positive_freqs = fft_freq[positive_freq_mask]
            positive_power = power_spectrum[positive_freq_mask]
            
            # パワーが大きい上位の周波数を取得
            top_freq_indices = np.argsort(positive_power)[-10:]  # 上位10個
            dominant_frequencies = positive_freqs[top_freq_indices]
            dominant_periods = 1 / dominant_frequencies
            dominant_powers = positive_power[top_freq_indices]
            
            # ピーク検出
            peaks, _ = signal.find_peaks(positive_power, height=np.percentile(positive_power, 95))
            peak_frequencies = positive_freqs[peaks]
            peak_periods = 1 / peak_frequencies
            peak_powers = positive_power[peaks]
            
            return {
                'fft_frequencies': fft_freq,
                'power_spectrum': power_spectrum,
                'dominant_periods': dominant_periods,
                'dominant_powers': dominant_powers,
                'peak_periods': peak_periods,
                'peak_powers': peak_powers,
                'total_power': np.sum(power_spectrum)
            }
            
        except Exception as e:
            log.error(f"[SeasonalAnalysisEngine] Spectral analysis failed: {e}")
            return {}
    
    def analyze_holiday_effects(self, ts_data: pd.Series, holidays: Optional[List[str]] = None) -> Dict[str, Any]:
        """祝日・休日効果の分析"""
        if not self.enable_holiday_effects:
            log.warning("[SeasonalAnalysisEngine] Holiday effects analysis disabled")
            return {}
        
        try:
            # 日本の基本的な祝日パターン
            if holidays is None:
                holidays = ['01-01', '01-02', '01-03',  # 正月
                           '04-29', '05-03', '05-04', '05-05',  # GW
                           '08-11', '08-12', '08-13', '08-14', '08-15',  # お盆
                           '12-29', '12-30', '12-31']  # 年末
            
            # データフレームに変換
            df = ts_data.reset_index()
            df['date'] = pd.to_datetime(df.index)
            df['month_day'] = df['date'].dt.strftime('%m-%d')
            df['weekday'] = df['date'].dt.dayofweek
            df['is_weekend'] = df['weekday'].isin([5, 6])
            df['is_holiday'] = df['month_day'].isin(holidays)
            
            # 各カテゴリの統計
            weekend_stats = df[df['is_weekend']]['count'].agg(['mean', 'std', 'count'])
            weekday_stats = df[~df['is_weekend']]['count'].agg(['mean', 'std', 'count'])
            holiday_stats = df[df['is_holiday']]['count'].agg(['mean', 'std', 'count'])
            normal_stats = df[~(df['is_weekend'] | df['is_holiday'])]['count'].agg(['mean', 'std', 'count'])
            
            # 統計的有意性のテスト
            weekend_effect = None
            holiday_effect = None
            
            if len(df[df['is_weekend']]) > 0 and len(df[~df['is_weekend']]) > 0:
                weekend_test = stats.ttest_ind(
                    df[df['is_weekend']]['count'].dropna(),
                    df[~df['is_weekend']]['count'].dropna()
                )
                weekend_effect = {
                    'mean_difference': weekend_stats['mean'] - weekday_stats['mean'],
                    'p_value': weekend_test.pvalue,
                    'significant': weekend_test.pvalue < 0.05
                }
            
            if len(df[df['is_holiday']]) > 0 and len(df[~df['is_holiday']]) > 0:
                holiday_test = stats.ttest_ind(
                    df[df['is_holiday']]['count'].dropna(),
                    df[~df['is_holiday']]['count'].dropna()
                )
                holiday_effect = {
                    'mean_difference': holiday_stats['mean'] - normal_stats['mean'],
                    'p_value': holiday_test.pvalue,
                    'significant': holiday_test.pvalue < 0.05
                }
            
            return {
                'weekend_stats': weekend_stats.to_dict(),
                'weekday_stats': weekday_stats.to_dict(),
                'holiday_stats': holiday_stats.to_dict(),
                'normal_stats': normal_stats.to_dict(),
                'weekend_effect': weekend_effect,
                'holiday_effect': holiday_effect,
                'analyzed_holidays': holidays
            }
            
        except Exception as e:
            log.error(f"[SeasonalAnalysisEngine] Holiday effects analysis failed: {e}")
            return {}
    
    def cluster_seasonal_patterns(self, all_patterns: Dict[str, pd.Series]) -> Dict[str, Any]:
        """季節性パターンのクラスタリング"""
        if not self.enable_clustering:
            log.warning("[SeasonalAnalysisEngine] Seasonal clustering disabled")
            return {}
        
        try:
            # パターンをマトリックスに変換
            pattern_matrix = []
            pattern_names = []
            
            for name, pattern in all_patterns.items():
                if hasattr(pattern, 'values') and len(pattern) > 0:
                    # 長さを統一（最小公倍数または標準長）
                    if len(pattern) >= 365:  # 年間パターン
                        standardized = pattern[:365].values
                    elif len(pattern) >= 52:  # 週間パターン
                        standardized = np.repeat(pattern.values, 365 // len(pattern) + 1)[:365]
                    elif len(pattern) >= 12:  # 月間パターン
                        standardized = np.repeat(pattern.values, 365 // len(pattern) + 1)[:365]
                    else:  # 日間パターン
                        standardized = np.tile(pattern.values, 365 // len(pattern) + 1)[:365]
                    
                    pattern_matrix.append(standardized)
                    pattern_names.append(name)
            
            if len(pattern_matrix) < 2:
                log.warning("[SeasonalAnalysisEngine] Insufficient patterns for clustering")
                return {}
            
            # 標準化
            scaler = StandardScaler()
            pattern_matrix_scaled = scaler.fit_transform(pattern_matrix)
            
            # 主成分分析
            pca = PCA(n_components=min(5, len(pattern_matrix)))
            pca_result = pca.fit_transform(pattern_matrix_scaled)
            
            # K-means クラスタリング
            n_clusters = min(4, len(pattern_matrix))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(pca_result)
            
            # クラスタリング結果の整理
            clusters = {}
            for i, (name, label) in enumerate(zip(pattern_names, cluster_labels)):
                cluster_key = f'cluster_{label}'
                if cluster_key not in clusters:
                    clusters[cluster_key] = []
                clusters[cluster_key].append(name)
            
            return {
                'cluster_labels': dict(zip(pattern_names, cluster_labels)),
                'clusters': clusters,
                'pca_components': pca.components_,
                'pca_explained_variance': pca.explained_variance_ratio_,
                'cluster_centers': kmeans.cluster_centers_,
                'n_clusters': n_clusters
            }
            
        except Exception as e:
            log.error(f"[SeasonalAnalysisEngine] Seasonal clustering failed: {e}")
            return {}
    
    def detect_seasonal_anomalies(self, ts_data: pd.Series, seasonal_component: pd.Series, threshold: float = 2.0) -> Dict[str, Any]:
        """季節性異常値の検出"""
        try:
            # 残差の計算
            residuals = ts_data - seasonal_component
            residuals = residuals.dropna()
            
            # 異常値の検出（Z-score基準）
            z_scores = np.abs(stats.zscore(residuals))
            anomaly_mask = z_scores > threshold
            
            anomalies = residuals[anomaly_mask]
            anomaly_dates = anomalies.index
            
            # 異常値の統計
            anomaly_stats = {
                'count': len(anomalies),
                'mean_deviation': np.mean(np.abs(anomalies)),
                'max_deviation': np.max(np.abs(anomalies)) if len(anomalies) > 0 else 0,
                'anomaly_rate': len(anomalies) / len(residuals) * 100
            }
            
            # 月別異常値分布
            if len(anomaly_dates) > 0:
                anomaly_months = pd.to_datetime(anomaly_dates).month
                monthly_anomaly_counts = pd.Series(anomaly_months).value_counts().sort_index()
            else:
                monthly_anomaly_counts = pd.Series()
            
            return {
                'anomalies': anomalies,
                'anomaly_dates': anomaly_dates,
                'anomaly_stats': anomaly_stats,
                'monthly_distribution': monthly_anomaly_counts,
                'threshold_used': threshold
            }
            
        except Exception as e:
            log.error(f"[SeasonalAnalysisEngine] Anomaly detection failed: {e}")
            return {}
    
    def generate_seasonal_forecast(self, ts_data: pd.Series, seasonal_component: pd.Series, periods: int = 30) -> Dict[str, Any]:
        """季節性パターンに基づく予測"""
        try:
            # 基本的な季節性予測
            # 直近の季節性パターンを使用
            pattern_length = len(seasonal_component)
            last_values = seasonal_component.tail(pattern_length)
            
            # 将来の日付を生成
            last_date = ts_data.index[-1]
            future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=periods, freq='D')
            
            # 季節性パターンの繰り返し
            seasonal_forecast = []
            for i in range(periods):
                pattern_index = i % pattern_length
                seasonal_forecast.append(last_values.iloc[pattern_index])
            
            # トレンド成分の推定（簡単な線形トレンド）
            recent_trend = ts_data.tail(30).diff().mean()
            trend_forecast = [recent_trend * (i + 1) for i in range(periods)]
            
            # 最終的な予測値
            final_forecast = np.array(seasonal_forecast) + np.array(trend_forecast)
            
            forecast_df = pd.DataFrame({
                'date': future_dates,
                'seasonal_forecast': seasonal_forecast,
                'trend_forecast': trend_forecast,
                'total_forecast': final_forecast
            })
            
            return {
                'forecast': forecast_df,
                'confidence_interval': None,  # 簡易版では省略
                'method': 'seasonal_pattern_repetition'
            }
            
        except Exception as e:
            log.error(f"[SeasonalAnalysisEngine] Seasonal forecast failed: {e}")
            return {}
    
    def analyze_all_seasonality(self, time_series_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """全ての時系列データの季節性を包括的に分析"""
        log.info("[SeasonalAnalysisEngine] Starting comprehensive seasonal analysis...")
        
        results = {
            'decomposition': {},
            'spectral': {},
            'holiday_effects': {},
            'patterns': {},
            'clustering': {},
            'anomalies': {},
            'forecasts': {}
        }
        
        # 各時系列に対して分析を実行
        seasonal_patterns = {}
        
        for series_name, series_df in time_series_data.items():
            if series_name in ['hourly_pattern', 'weekly_pattern']:
                # 日内・週間パターンは別途処理
                continue
            
            try:
                ts_series = series_df['count'] if 'count' in series_df.columns else series_df.iloc[:, 0]
                
                # 時系列分解
                decomp_result = self.detect_seasonal_components(ts_series)
                if decomp_result:
                    results['decomposition'][series_name] = decomp_result
                    seasonal_patterns[f'{series_name}_seasonal'] = decomp_result['seasonal_pattern']
                
                # スペクトル解析
                spectral_result = self.perform_spectral_analysis(ts_series)
                if spectral_result:
                    results['spectral'][series_name] = spectral_result
                
                # 祝日効果分析
                holiday_result = self.analyze_holiday_effects(ts_series)
                if holiday_result:
                    results['holiday_effects'][series_name] = holiday_result
                
                # 季節性異常値検出
                if decomp_result and 'stl_seasonal' in decomp_result:
                    anomaly_result = self.detect_seasonal_anomalies(ts_series, decomp_result['stl_seasonal'])
                    if anomaly_result:
                        results['anomalies'][series_name] = anomaly_result
                
                # 季節性予測
                if decomp_result and 'stl_seasonal' in decomp_result:
                    forecast_result = self.generate_seasonal_forecast(ts_series, decomp_result['stl_seasonal'])
                    if forecast_result:
                        results['forecasts'][series_name] = forecast_result
                
            except Exception as e:
                log.error(f"[SeasonalAnalysisEngine] Analysis failed for {series_name}: {e}")
                continue
        
        # パターンクラスタリング
        if seasonal_patterns:
            clustering_result = self.cluster_seasonal_patterns(seasonal_patterns)
            if clustering_result:
                results['clustering'] = clustering_result
        
        # 日内・週間パターンの分析
        if 'hourly_pattern' in time_series_data:
            results['patterns']['hourly'] = time_series_data['hourly_pattern']['count'].to_dict()
        
        if 'weekly_pattern' in time_series_data:
            results['patterns']['weekly'] = time_series_data['weekly_pattern']['count'].to_dict()
        
        log.info(f"[SeasonalAnalysisEngine] Seasonal analysis completed for {len(time_series_data)} series")
        
        return results


def analyze_seasonal_patterns(
    long_df: pd.DataFrame,
    output_path: Path,
    *,
    enable_decomposition: bool = True,
    enable_spectral: bool = True,
    enable_holiday_effects: bool = True,
    enable_clustering: bool = True
) -> Path:
    """
    季節性パターンの包括的分析を実行
    
    Parameters
    ----------
    long_df : pd.DataFrame
        シフトデータ（long形式）
    output_path : Path
        出力ファイルパス
    enable_decomposition : bool, default True
        時系列分解を有効にするか
    enable_spectral : bool, default True
        スペクトル解析を有効にするか
    enable_holiday_effects : bool, default True
        祝日効果分析を有効にするか
    enable_clustering : bool, default True
        パターンクラスタリングを有効にするか
    
    Returns
    -------
    Path
        出力ファイルパス
    """
    log.info(f"[analyze_seasonal_patterns] Starting seasonal pattern analysis")
    
    # 分析エンジンの初期化
    engine = SeasonalAnalysisEngine(
        enable_decomposition=enable_decomposition,
        enable_spectral=enable_spectral,
        enable_holiday_effects=enable_holiday_effects,
        enable_clustering=enable_clustering
    )
    
    # 時系列データの準備
    time_series_data = engine.prepare_time_series_data(long_df)
    if not time_series_data:
        log.warning("[analyze_seasonal_patterns] No time series data prepared")
        return output_path
    
    # 季節性分析の実行
    analysis_results = engine.analyze_all_seasonality(time_series_data)
    
    # 結果のサマリー作成
    summary = {
        'total_series_analyzed': len(time_series_data),
        'decomposition_completed': len(analysis_results['decomposition']),
        'spectral_analysis_completed': len(analysis_results['spectral']),
        'holiday_effects_analyzed': len(analysis_results['holiday_effects']),
        'patterns_detected': len(analysis_results['patterns']),
        'clustering_performed': bool(analysis_results['clustering']),
        'anomalies_detected': sum([len(a.get('anomalies', [])) for a in analysis_results['anomalies'].values()]),
        'forecasts_generated': len(analysis_results['forecasts'])
    }
    
    # 結果の保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # メイン結果をParquetで保存（DataFrame形式に変換）
    results_df = pd.DataFrame([summary])
    save_df_parquet(results_df, output_path)
    
    # 詳細結果をJSONで保存
    write_meta(
        output_path.with_suffix('.meta.json'),
        analysis_type="seasonal_patterns",
        summary=summary,
        decomposition_results=analysis_results['decomposition'],
        spectral_results=analysis_results['spectral'],
        holiday_effects=analysis_results['holiday_effects'],
        patterns=analysis_results['patterns'],
        clustering=analysis_results['clustering'],
        anomalies_summary={k: v.get('anomaly_stats', {}) for k, v in analysis_results['anomalies'].items()},
        forecast_summary={k: len(v.get('forecast', [])) for k, v in analysis_results['forecasts'].items()},
        created=str(dt.datetime.now())
    )
    
    log.info(f"[analyze_seasonal_patterns] Seasonal analysis completed → {output_path}")
    log.info(f"[analyze_seasonal_patterns] Summary: {summary}")
    
    return output_path


__all__ = ['SeasonalAnalysisEngine', 'analyze_seasonal_patterns']