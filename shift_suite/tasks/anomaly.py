"""shift_suite.anomaly – 異常シフト日検知 (IsolationForest)
v0.3.1 (constants.py から SUMMARY5 を参照)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.ensemble import IsolationForest

from .constants import SUMMARY5  # SUMMARY5 を constants からインポート
from .utils import log, save_df_xlsx


def detect_anomaly(out_dir: Path, contamination: float = 0.05):
    hp = out_dir / "heat_ALL.xlsx"
    if not hp.exists():
        log.error(f"[anomaly] heat_ALL.xlsx が見つかりません: {hp}")
        return None
    try:
        heat = pd.read_excel(hp, index_col=0)
    except Exception as e:
        log.error(f"[anomaly] heat_ALL.xlsx の読み込み中にエラー: {e}", exc_info=True)
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
        iso = IsolationForest(
            random_state=0, n_estimators=200, contamination=contamination
        )
        iso.fit(X)
        scores = iso.decision_function(X)
        is_anomaly_flags = iso.predict(X) == -1
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
    output_path = out_dir / "anomaly_days.xlsx"
    try:
        save_df_xlsx(df_anomaly_report, output_path, sheet_name="anomaly", index=False)
        log.info(
            f"[anomaly] 異常検知レポート ({is_anomaly_flags.sum()}/{len(is_anomaly_flags)}日異常) 保存: {output_path}"
        )
    except Exception as e:
        log.error(f"[anomaly] anomaly_days.xlsx 保存エラー: {e}", exc_info=True)
        return None
    return df_anomaly_report
