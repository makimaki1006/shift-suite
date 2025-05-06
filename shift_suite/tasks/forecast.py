"""
shift_suite.tasks.forecast  v0.9.4 – 需要予測
────────────────────────────────────────────────────────
* heat_ALL.xlsx → 需要系列 CSV 生成 (build_demand_series)
* CSV → Excel 予測値 (forecast_need)
* 「MM/DD(曜)」「MM/DD」「M-D」など列ラベルを柔軟に解釈
* 実績行数 < 2 もしくは need 合計 < 2 の場合は Stop せず naive 予測にフォールバック
"""

from __future__ import annotations

import datetime as dt
import json
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm  # ← requirements.txt に追加済み

from .utils import log, save_df_xlsx, write_meta

# ────────────────── 内部定数・正規表現 ──────────────────
# 列名→日付に使う正規表現
# 例) 03/01(土) / 3/1(土) / 03/01 / 3-1 / 3-1 (土曜)
_COL_RE = re.compile(r"\s*(\d{1,2})[/-](\d{1,2})")

# summary5 (heatmap 右端) で無視する列
_SUMMARY_COLS = {"need", "upper", "staff", "lack", "excess"}


# ────────────────── 内部ヘルパ ──────────────────
def _parse_date_label(label: str, base_year: int) -> dt.date | None:
    """
    heat_ALL の列ラベルを datetime.date に変換
      - "3/1(土)" → 2025-03-01
      - "03/01"   → 2025-03-01
      - "3-1"     → 2025-03-01
    認識できなければ None
    """
    m = _COL_RE.match(str(label))
    if not m:
        return None
    month, day = map(int, m.groups())
    try:
        return dt.date(base_year, month, day)
    except ValueError:
        return None


def _extract_date_columns(df: pd.DataFrame) -> dict[dt.date, str]:
    """
    heat_ALL.xlsx の列 → {date: col_name} 辞書を返す

    基準年の決定:
        - 「今日から６か月後」までなら今年
        - それより先なら前年（年跨ぎのシフトを想定）
    """
    today = dt.date.today()
    year_guess = today.year
    out: dict[dt.date, str] = {}

    for col in df.columns:
        col_lower = str(col).lower()
        if col_lower in _SUMMARY_COLS:
            continue  # summary5 列はスキップ

        # 基準年、前年、翌年の３パターンで解釈を試す
        for y in (year_guess, year_guess - 1, year_guess + 1):
            d = _parse_date_label(col, y)
            if d:
                out[d] = col
                break
    return out


def _weekly_features(df: pd.DataFrame) -> pd.DataFrame:
    """曜日ダミーなど簡易特徴量生成（必要なら拡張可能）"""
    df = df.copy()
    df["dow"] = df["ds"].dt.weekday  # 0=Mon
    df = pd.get_dummies(df, columns=["dow"], drop_first=True)
    return df


# ═══════════════════╗ Public API ║══════════════════
def build_demand_series(
    heat_xlsx: Path,
    csv_out: Path,
    *,
    slot: int | None = None,
    summary_cols: tuple[str, ...] = ("need",),
) -> Path:
    """
    heat_ALL.xlsx → 需要系列 CSV を生成
    """
    log.info("[forecast] build_demand_series start")
    heat = pd.read_excel(heat_xlsx, index_col=0)

    # 列ラベル → 日付マッピング
    date_map = _extract_date_columns(heat)
    if not date_map:
        raise ValueError("有効な日付列が 1 つも見つかりません")

    if summary_cols[0] not in heat.columns:
        raise ValueError(f"heat_ALL.xlsx に {summary_cols[0]} 列がありません")

    # ---- ★ 修正点 ★ ----
    rows = [
        {"ds": d, "y": heat[col].sum()}  # ← Series ではなく DataFrame 列を直接集計
        for d, col in sorted(date_map.items())
    ]
    # ---------------------

    df = pd.DataFrame(rows).sort_values("ds")
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_out, index=False)

    # メタ保存
    write_meta(
        csv_out.with_suffix(".meta.json"),
        source=str(heat_xlsx),
        slot=slot,
        rows=len(df),
    )
    log.info(f"[forecast] demand series saved → {csv_out}")
    return csv_out


def forecast_need(
    demand_csv: Path,
    excel_out: Path,
    *,
    choose: str = "auto",       # "auto" | "arima" | "ets"
    seasonal: str = "add",      # ETS の季節成分: "add" | "mul"
    periods: int = 14,
) -> Path:
    """
    需要 CSV を読み込んで予測し、Excel 保存
    """
    log.info("[forecast] forecast_need start")
    df = pd.read_csv(demand_csv, parse_dates=["ds"])

    # ─── 実績不足チェック ───
    if len(df) < 2 or df["y"].sum() < 2:
        warnings.warn(
            f"予測に十分な実績データがありません "
            f"({len(df)} 行, y.sum={df['y'].sum()}) → naive 予測で継続"
        )
        last_val = df["y"].iloc[-1] if not df.empty else 0
        future_dates = pd.date_range(df["ds"].max() + dt.timedelta(days=1), periods=periods)
        out_df = pd.DataFrame({"ds": future_dates, "yhat": last_val})
        save_df_xlsx(out_df, excel_out)

        write_meta(
            excel_out.with_suffix(".json"),
            selected_model="naive",
            note="実績不足につき直近値コピー",
            rows=len(df),
        )
        log.info(f"[forecast] fallback naive forecast saved → {excel_out}")
        return excel_out

    # ─── ARIMA ───
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        arima_mod = sm.tsa.auto_arima(
            df["y"], seasonal=False, stepwise=True, suppress_warnings=True
        )
    arima_fc = arima_mod.predict(n_periods=periods)
    arima_mape = np.mean(
        np.abs((arima_mod.y - arima_mod.predict_in_sample()) / arima_mod.y)
    )

    # ─── ETS ───
    ets_mod = sm.tsa.ExponentialSmoothing(
        df["y"], trend="add", seasonal=seasonal, seasonal_periods=7
    ).fit(optimized=True)
    ets_fc = ets_mod.forecast(periods)
    ets_mape = np.mean(np.abs((ets_mod.fittedvalues - df["y"]) / df["y"]))

    # ─── best select ───
    if choose == "arima":
        sel, forecast, sel_mape = "ARIMA", arima_fc, arima_mape
    elif choose == "ets":
        sel, forecast, sel_mape = "ETS", ets_fc, ets_mape
    else:  # auto
        if arima_mape <= ets_mape:
            sel, forecast, sel_mape = "ARIMA", arima_fc, arima_mape
        else:
            sel, forecast, sel_mape = "ETS", ets_fc, ets_mape

    future_dates = pd.date_range(df["ds"].max() + dt.timedelta(days=1), periods=periods)
    out_df = pd.DataFrame({"ds": future_dates, "yhat": forecast})
    save_df_xlsx(out_df, excel_out)

    # メタ
    write_meta(
        excel_out.with_suffix(".json"),
        selected_model=sel,
        mape_arima=round(float(arima_mape), 4),
        mape_ets=round(float(ets_mape), 4),
        mape_selected=round(float(sel_mape), 4),
        rows=len(df),
    )

    log.info(f"[forecast] forecast saved → {excel_out}")
    return excel_out


# ────────────────── __all__ ──────────────────
__all__ = [
    "build_demand_series",
    "forecast_need",
]
