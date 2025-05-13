"""
shift_suite.tasks.forecast  v1.3.0 – pmdarima 対応 + “model” 列固定出力
────────────────────────────────────────────────────────
■ v1.3 変更点 ★
  1. forecast_need() が生成する out_df に “model” 列を必ず付与
     - app.py 側で 'model' KeyError が発生していた問題を解消
  2. write_meta() に rows/selected_model だけでなく
     - mape_selected, periods, created も記録
  3. ドキュメント整理・型ヒント微調整
"""

from __future__ import annotations

import datetime as dt
import logging
import re
import warnings
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm

from .utils import log, save_df_xlsx, write_meta

# ────────────────── pmdarima (optional) ──────────────────
try:
    import pmdarima as pm

    _HAS_PMDARIMA = True
    log.info("[forecast] pmdarima detected — auto_arima enabled")
except ImportError:
    _HAS_PMDARIMA = False
    log.warning(
        "[forecast] pmdarima not installed — ARIMA auto-search disabled; "
        "run `pip install pmdarima` to enable"
    )

# ────────────────── 定数 ──────────────────
_EXCEL_EPOCH = dt.date(1899, 12, 30)
_COL_RE = re.compile(r"\s*(\d{1,2})[/-](\d{1,2})")  # 3/1  03-01
_SUMMARY_COLS = {"need", "upper", "staff", "lack", "excess"}

# ────────────────── ヘルパ ──────────────────
def _excel_serial_to_date(num: int | float) -> Optional[dt.date]:
    """Excel シリアル値 → date。失敗時 None"""
    try:
        num_i = int(float(num))
        if num_i <= 0:
            return None
        return _EXCEL_EPOCH + dt.timedelta(days=num_i)
    except Exception:
        return None


def _parse_date_label(label: Any, base_year: int) -> Optional[dt.date]:
    """列ラベルを date に解釈（年は補完）"""
    s = str(label).strip()

    # Excel シリアル / 数字文字列
    if isinstance(label, (int, float)) or s.isdigit():
        return _excel_serial_to_date(label)

    # _45355 suffix
    m_serial = re.search(r"(\d{5})$", s)
    if m_serial:
        return _excel_serial_to_date(int(m_serial.group(1)))

    # 3/1, 3-1
    m = _COL_RE.match(s)
    if m:
        month, day = map(int, m.groups())
        try:
            return dt.date(base_year, month, day)
        except ValueError:
            return None

    # ISO 文字列など
    ts = pd.to_datetime(s, errors="coerce")
    if not pd.isna(ts):
        return ts.date()

    log.debug(f"[forecast] could not parse column label as date: {label!r}")
    return None


def _extract_date_columns(
    df: pd.DataFrame, *, today: dt.date | None = None
) -> Dict[dt.date, str]:
    """heat_ALL.xlsx の列ラベル → {date: column_name}"""
    today = today or dt.date.today()
    year_guess = today.year
    date_map: Dict[dt.date, str] = {}

    for col in df.columns:
        if str(col).lower() in _SUMMARY_COLS:
            continue
        for y in (year_guess, year_guess - 1, year_guess + 1):
            d = _parse_date_label(col, y)
            if d:
                date_map[d] = col
                break

    log.info(f"[forecast] date columns detected: {len(date_map)} 個")
    if log.isEnabledFor(logging.DEBUG):
        log.debug(f"[forecast] date_map sample: {list(date_map.items())[:10]}")
    return date_map


# ═══════════════════╗ Public API ║══════════════════
def build_demand_series(
    heat_xlsx: Path,
    csv_out: Path,
    *,
    summary_col: str = "need",
    raise_on_empty: bool = True,
) -> Path:
    """heat_ALL.xlsx → 需要系列 CSV(ds,y) を生成"""
    log.info("[forecast] build_demand_series start")
    heat = pd.read_excel(heat_xlsx, index_col=0)

    date_map = _extract_date_columns(heat)
    if not date_map:
        msg = "有効な日付列が 1 つも見つかりません"
        if raise_on_empty:
            raise ValueError(msg)
        warnings.warn(msg)
        pd.DataFrame(columns=["ds", "y"]).to_csv(csv_out, index=False)
        return csv_out

    if summary_col not in heat.columns:
        raise ValueError(f"heat_ALL.xlsx に {summary_col} 列がありません")

    rows = [{"ds": d, "y": heat[col].sum()} for d, col in sorted(date_map.items())]
    df = pd.DataFrame(rows).sort_values("ds")
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_out, index=False)

    write_meta(csv_out.with_suffix(".meta.json"), source=str(heat_xlsx), rows=len(df))
    log.info(f"[forecast] demand series saved → {csv_out}")
    return csv_out


def forecast_need(
    demand_csv: Path,
    excel_out: Path,
    *,
    choose: str = "auto",  # "auto" | "arima" | "ets"
    seasonal: str = "add",
    periods: int = 14,
) -> Path:
    """需要系列 CSV → 14 日先需要予測 Excel

    返り値: 生成した Excel パス
    Excel には必ず列 ["ds","yhat","model"] が含まれる
    """
    log.info("[forecast] forecast_need start")
    df = pd.read_csv(demand_csv, parse_dates=["ds"])

    # ───── データ不足 → Naive ─────
    if len(df) < 2 or df["y"].sum() < 2:
        warnings.warn("実績データが不足しているため Naive 予測で継続")
        last_val = df["y"].iloc[-1] if not df.empty else 0
        future_dates = pd.date_range(
            df["ds"].max() + dt.timedelta(days=1) if not df.empty else dt.date.today(),
            periods=periods,
        )
        out_df = pd.DataFrame({"ds": future_dates, "yhat": last_val, "model": "Naive"})
        save_df_xlsx(out_df, excel_out)
        write_meta(
            excel_out.with_suffix(".json"),
            selected_model="Naive",
            rows=len(df),
            periods=periods,
        )
        return excel_out

    # ───── ETS モデル ─────
    ets_mod = sm.tsa.ExponentialSmoothing(
        df["y"], trend="add", seasonal=seasonal, seasonal_periods=7
    ).fit(optimized=True)
    ets_fc = ets_mod.forecast(periods)
    ets_mape = np.mean(np.abs((ets_mod.fittedvalues - df["y"]) / df["y"]))

    # ───── ARIMA (pmdarima) ─────
    arima_mape = np.inf
    arima_fc = None
    if _HAS_PMDARIMA:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            arima_mod = pm.auto_arima(
                df["y"],
                seasonal=False,
                stepwise=True,
                suppress_warnings=True,
                error_action="ignore",
            )
        arima_fc = arima_mod.predict(n_periods=periods)
        arima_mape = np.mean(
            np.abs((arima_mod.y - arima_mod.predict_in_sample()) / arima_mod.y)
        )
    elif choose in ("auto", "arima"):
        log.warning("[forecast] ARIMA 指定ですが pmdarima が無いため ETS を使用")

    # ───── モデル選択 ─────
    if choose == "ets" or (choose == "auto" and ets_mape <= arima_mape):
        sel, forecast, sel_mape = "ETS", ets_fc, ets_mape
    elif choose == "arima" and arima_fc is not None:
        sel, forecast, sel_mape = "ARIMA", arima_fc, arima_mape
    else:
        sel, forecast, sel_mape = "ETS", ets_fc, ets_mape  # fallback

    # ───── 予測結果組立 ─────
    future_dates = pd.date_range(df["ds"].max() + dt.timedelta(days=1), periods=periods)
    out_df = pd.DataFrame({"ds": future_dates, "yhat": forecast})
    out_df["model"] = sel  # ★ 追加: 常に model 列を付与

    save_df_xlsx(out_df, excel_out)

    write_meta(
        excel_out.with_suffix(".json"),
        selected_model=sel,
        mape_selected=float(np.round(sel_mape, 4)),
        rows=len(df),
        periods=periods,
        created=str(dt.datetime.now()),
    )
    log.info(f"[forecast] forecast saved → {excel_out}")
    return excel_out


__all__ = ["build_demand_series", "forecast_need"]
