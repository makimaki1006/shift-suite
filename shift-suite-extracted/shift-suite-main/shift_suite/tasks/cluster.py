"""shift_suite.cluster – 職員タイプ自動クラスタリング (K-Means)"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from .utils import log, save_df_parquet


def cluster_staff(long_df: pd.DataFrame, out_dir: Path, k: int = 3):
    if "staff" not in long_df.columns:
        log.error(
            "[cluster] long_dfに 'staff' 列が見つかりません。処理をスキップします。"
        )
        empty_cluster_df = pd.DataFrame(columns=["n_codes", "cluster"])
        save_df_parquet(empty_cluster_df, out_dir / "staff_cluster.parquet")
        log.info(
            "cluster: 'staff'列がなかったため、空のstaff_cluster.xlsxを作成しました。"
        )
        return empty_cluster_df
    if "code" not in long_df.columns:
        log.error(
            "[cluster] long_dfに 'code' 列が見つかりません。処理をスキップします。"
        )
        empty_cluster_df = pd.DataFrame(columns=["n_codes", "cluster"])
        save_df_parquet(empty_cluster_df, out_dir / "staff_cluster.parquet")
        log.info(
            "cluster: 'code'列がなかったため、空のstaff_cluster.xlsxを作成しました。"
        )
        return empty_cluster_df

    # 特徴量＝担当コードの多様度
    # スタッフ識別列を "name" から "staff" に変更
    feat = long_df.groupby("staff")["code"].nunique().to_frame("n_codes")

    if feat.empty:
        log.warning(
            "[cluster] 特徴量データ(feat)が空です。クラスタリングは実行されません。"
        )
        empty_cluster_df = pd.DataFrame(columns=["n_codes", "cluster"])
        save_df_parquet(empty_cluster_df, out_dir / "staff_cluster.parquet")
        return empty_cluster_df

    # データが1行しかない場合、StandardScalerやKMeansでエラーになることがある
    if len(feat) == 1:
        log.warning(
            "[cluster] 特徴量データの行数が1のため、クラスタリングは実行せず、cluster 0 を割り当てます。"
        )
        feat["cluster"] = 0
        save_df_parquet(feat, out_dir / "staff_cluster.parquet")
        log.info("cluster: k=1 (データ1行のため)")
        return feat

    X = StandardScaler().fit_transform(feat)

    # k の値がサンプル数より大きい場合、KMeansはエラーを出すため調整
    actual_k = min(k, len(feat))
    if actual_k <= 0:  # サンプル数が0またはkが0以下の場合
        log.warning(
            f"[cluster] 有効なクラスタ数 k ({actual_k}) が0以下です。クラスタリングは実行されません。"
        )
        feat["cluster"] = pd.NA  # または適切なデフォルト値
        save_df_parquet(feat, out_dir / "staff_cluster.parquet")
        return feat

    km = KMeans(n_clusters=actual_k, random_state=0, n_init="auto").fit(
        X
    )  # n_init='auto'で警告抑制
    feat["cluster"] = km.labels_
    save_df_parquet(feat, out_dir / "staff_cluster.parquet")
    log.info(f"cluster: k={km.n_clusters} でクラスタリング完了")
    return feat
