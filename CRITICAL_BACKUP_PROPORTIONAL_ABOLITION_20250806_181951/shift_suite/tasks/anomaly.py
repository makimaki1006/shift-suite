"""shift_suite.anomaly – 異常シフト日検知 (IsolationForest)
v0.3.1 (constants.py から SUMMARY5 を参照)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import numpy as np

from .constants import SUMMARY5  # SUMMARY5 を constants からインポート
from .utils import log, save_df_parquet

# sklearn-free anomaly detection using simple statistical methods
class SimpleAnomalyDetector:
    """Simple anomaly detector using statistical methods (Z-score based)"""
    
    def __init__(self, contamination=0.05):
        self.contamination = contamination
        
    def fit_predict(self, X):
        """Fit the detector and predict anomalies"""
        if len(X) == 0:
            return np.array([])
            
        # Calculate Z-scores for each feature
        z_scores = np.abs((X - np.mean(X, axis=0)) / (np.std(X, axis=0) + 1e-8))
        
        # Calculate anomaly score as max Z-score across features
        anomaly_scores = np.max(z_scores, axis=1)
        
        # Set threshold based on contamination rate
        threshold = np.percentile(anomaly_scores, (1 - self.contamination) * 100)
        
        # Return -1 for anomalies, 1 for normal (sklearn IsolationForest convention)
        return np.where(anomaly_scores > threshold, -1, 1)


def detect_anomaly(out_dir: Path, contamination: float = 0.05):
    hp = out_dir / "heat_ALL.parquet"
    if not hp.exists():
        log.error(f"[anomaly] heat_ALL.parquet が見つかりません: {hp}")
        return None
    try:
        heat = pd.read_parquet(hp)
    except Exception as e:
        log.error(
            f"[anomaly] heat_ALL.parquet の読み込み中にエラー: {e}", exc_info=True
        )
        return None

    date_columns = [col for col in heat.columns if col not in SUMMARY5]
    if not date_columns:
        log.warning("[anomaly] heat_ALL.xlsx に日付データ列が見つかりませんでした。")
        return None
    heat_data_only = heat[date_columns]
    log.debug(f"[anomaly] 異常検知対象の日付列数: {len(heat_data_only.columns)}")
    X = heat_data_only.fillna(0).T.values
    if X.shape[0] == 0:
        log.warning("[anomaly] 異常検知対象のデータがありません (転置後)。")
        return None

    try:
        iso = SimpleAnomalyDetector(contamination=contamination)
        predictions = iso.fit_predict(X)
        scores = predictions  # Use predictions as scores for simplicity
        is_anomaly_flags = predictions == -1
    except Exception as e:
        log.error(f"[anomaly] IsolationForest処理中にエラー: {e}", exc_info=True)
        return None

    df_anomaly_report = pd.DataFrame(
        {
            "date": heat_data_only.columns,
            "score": scores,
            "is_anomaly": is_anomaly_flags,
        }
    )
    output_path = out_dir / "anomaly_days.parquet"
    try:
        save_df_parquet(df_anomaly_report, output_path, index=False)
        log.info(
            f"[anomaly] 異常検知レポート ({is_anomaly_flags.sum()}/{len(is_anomaly_flags)}日異常) 保存: {output_path}"
        )
    except Exception as e:
        log.error(f"[anomaly] anomaly_days.xlsx 保存エラー: {e}", exc_info=True)
        return None
    return df_anomaly_report
