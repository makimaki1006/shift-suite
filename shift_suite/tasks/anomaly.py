"""shift_suite.anomaly – 異常シフト日検知 (IsolationForest)  v0.2
欠損セルは 0 に置換してから学習する
"""
from __future__ import annotations
import pandas as pd
from pathlib import Path
from sklearn.ensemble import IsolationForest
from .utils import save_df_xlsx, log


def detect_anomaly(out_dir: Path, contamination: float = 0.05):
    """
    heat_ALL.xlsx を IsolationForest で日別異常スコア算出
    Parameters
    ----------
    out_dir : Path
        heat_ALL.xlsx が置かれたフォルダ
    contamination : float, default 0.05
        異常日とみなす比率
    Returns
    -------
    DataFrame : date / score / is_anomaly
    """
    hp = out_dir / "heat_ALL.xlsx"
    if not hp.exists():
        log.error("anomaly: heat_ALL.xlsx missing")
        return None

    heat = pd.read_excel(hp, index_col=0)          # rows=time, cols=date
    X = heat.fillna(0).T.values                    # ← 欠損を 0 で埋める

    iso = IsolationForest(
        random_state=0,
        n_estimators=200,
        contamination=contamination,
    )
    iso.fit(X)

    score = iso.decision_function(X)
    flag = iso.predict(X) == -1                    # True = 異常

    df = pd.DataFrame(
        {"date": heat.columns, "score": score, "is_anomaly": flag}
    )
    save_df_xlsx(df, out_dir / "anomaly_days.xlsx", sheet_name="anomaly")
    log.info(f"anomaly: {flag.sum()} / {len(flag)} days flagged")
    return df
