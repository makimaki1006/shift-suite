"""shift_suite.cluster – 職員タイプ自動クラスタリング (K-Means)"""
from __future__ import annotations
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from .utils import save_df_xlsx, log


def cluster_staff(long_df: pd.DataFrame, out_dir: Path, k: int = 3):
    # 特徴量＝担当コードの多様度
    feat = long_df.groupby("name")["code"].nunique().to_frame("n_codes")
    X = StandardScaler().fit_transform(feat)
    km = KMeans(n_clusters=min(k, len(feat)), random_state=0).fit(X)
    feat["cluster"] = km.labels_
    save_df_xlsx(feat, out_dir / "staff_cluster.xlsx", "cluster")
    log.info("cluster: k=%d", km.n_clusters)
    return feat
