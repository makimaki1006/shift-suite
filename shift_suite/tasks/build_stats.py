# build_stats.py — KPI 集約＋全体／月別集計版

from __future__ import annotations
from pathlib import Path
import pandas as pd

def build_stats(
    out_dir: str | Path,
    *,
    need_col: str = 'need'
) -> None:
    """
    既存の日別・職種別 KPI に加えて、
    ① 全期間合計サマリ (Overall_Summary)
    ② 月別サマリ       (Monthly_Summary)
    の２シートを stats.xlsx に追加します。

    Parameters:
    - out_dir: 出力ディレクトリ (heatmap などが置いてある場所)
    - need_col: 'need' 列名 (default: 'need')
    """
    out_dir = Path(out_dir)
    stats_fp = out_dir / 'stats.xlsx'

    # 1) 既存入力読み込み
    #    (heat_ALL から日別 need を、min_<role>.csv から role毎 need を読む想定)
    heat_all = pd.read_excel(out_dir / 'heat_ALL.xlsx', index_col=0)
    # 日別サマリ（全体 need, staff, lack, excess は元の summary5 の列名になる想定）
    # ここでは need_col 列だけ全期間合計用に取得
    # --- 既存の日別／職種別処理はそのまま残す ---

    # 2) Overall_Summary シート作成
    # 全期間にわたる need の総数・平均・最大・最小など
    overall = pd.DataFrame({
        'metric': ['total_need', 'mean_need_per_slot', 'max_need', 'min_need'],
        'value': [
            heat_all.values.sum(),
            heat_all.values.mean(),
            heat_all.values.max(),
            heat_all.values.min(),
        ]
    })

    # 3) Monthly_Summary シート作成
    # heat_all の列ラベルが e.g. '3/1','3/2' なので月を抽出
    df = heat_all.copy()
    # 列名を datetime に変換
    df.columns = pd.to_datetime(df.columns, format='%m/%d', errors='coerce')
    # 各月ごとに合計・平均を計算
    monthly = (
        df
        .groupby(df.columns.month, axis=1)  # month: 1～12
        .sum()
        .sum(axis=0)
        .rename('total_need')
        .to_frame()
    )
    monthly['mean_need_per_slot'] = (
        df.groupby(df.columns.month, axis=1)
          .mean()
          .mean(axis=0)
    )
    monthly['max_need'] = (
        df.groupby(df.columns.month, axis=1)
          .max()
          .max(axis=0)
    )
    monthly['min_need'] = (
        df.groupby(df.columns.month, axis=1)
          .min()
          .min(axis=0)
    )
    # 月ラベルを文字列に
    monthly.index = monthly.index.map(lambda m: f'{m:02d}')

    # 4) 既存の stats.xlsx に追記
    with pd.ExcelWriter(stats_fp, engine='openpyxl', mode='a') as writer:
        overall.to_excel(writer, sheet_name='Overall_Summary', index=False)
        monthly.to_excel(writer, sheet_name='Monthly_Summary')

    print(f"✅ stats.xlsx に Overall_Summary と Monthly_Summary を追記しました: {stats_fp}")
