"""
shift_suite.tasks.forecast  v1.5.0 – 休暇・履歴対応
────────────────────────────────────────────────────────
■ v1.5 変更点 ★
  1. 予測期間の既定を 30 日に延長
  2. build_demand_series / forecast_need が leave_analysis.csv を任意で受け付け
  3. MAPE 計算を 0 除算回避処理付きに修正
  4. forecast_need() が生成する out_df に “model” 列を必ず付与
  5. forecast_need() が祝日データを受け取り exogenous 変数として利用
  6. forecast_need() 実行履歴を ``forecast_history.csv`` に追記
  7. 直近の履歴 MAPE が閾値を超える場合はモデル選択を調整
"""

from __future__ import annotations

import datetime as dt
import logging
import re
import warnings
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

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
    leave_csv: Path | None = None,
) -> Path:
    """heat_ALL.xlsx → 需要系列 CSV(ds,y) を生成

    Parameters
    ----------
    heat_xlsx : Path
        heat_ALL.xlsx のパス
    csv_out : Path
        出力 CSV パス
    summary_col : str, default ``"need"``
        集計対象の列名
    raise_on_empty : bool, default ``True``
        日付列が検出できなかった場合に例外を送出するか
    leave_csv : Path | None, optional
        ``leave_analysis.csv`` (日付・休暇タイプ別取得数) を指定すると、
        休暇取得数を ``leave_…`` 列として付与する
    """
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

    if leave_csv and Path(leave_csv).exists():
        try:
            leave_df = pd.read_csv(leave_csv, parse_dates=["date"])
            pivot = (
                leave_df.pivot_table(
                    index="date",
                    columns="leave_type",
                    values="total_leave_days",
                    aggfunc="sum",
                    fill_value=0,
                )
            )
            pivot = pivot.add_prefix("leave_").reset_index().rename(columns={"date": "ds"})
            df = df.merge(pivot, on="ds", how="left").fillna(0)
        except Exception as e:
            log.warning(f"[forecast] leave_csv load failed: {e}")

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
    periods: int = 30,
    leave_csv: Path | None = None,
    holidays: Sequence[dt.date] | None = None,
    log_csv: Path | None = None,
) -> Path:
    """需要系列 CSV → 1 か月先需要予測 Excel

    Parameters
    ----------
    demand_csv : Path
        :func:`build_demand_series` で生成した CSV
    excel_out : Path
        予測結果を保存する Excel
    choose : {"auto", "arima", "ets"}, default "auto"
        モデル選択方法
    seasonal : str, default "add"
        ETS モデルの季節成分タイプ
    periods : int, default 30
        予測期間（日数）
    leave_csv : Path | None, optional
        ``leave_analysis.csv`` を与えると休暇取得数を説明変数として利用
    holidays : Sequence[datetime.date] | None, optional
        祝日の日付リストを与えると ``holiday`` 列が追加され、ARIMA の説明変数として利用
    log_csv : Path | None, optional
        予測実行履歴を追記する CSV パス。未指定時 ``excel_out`` と同じディレクトリの
        ``forecast_history.csv`` を使用

    Returns
    -------
    Path
        生成した Excel ファイルパス
    """
    log.info("[forecast] forecast_need start")
    df = pd.read_csv(demand_csv, parse_dates=["ds"])

    log_csv = Path(log_csv) if log_csv else excel_out.parent / "forecast_history.csv"

    if holidays:
        holiday_set = {pd.to_datetime(d).date() for d in holidays}
        df["holiday"] = df["ds"].dt.date.map(lambda d: 1 if d in holiday_set else 0)
    else:
        holiday_set = set()

    # ───── 直近履歴確認 ─────
    if log_csv.exists():
        try:
            hist = pd.read_csv(log_csv)
            recent_mape = hist["mape"].tail(5).mean()
            if choose == "auto" and recent_mape > 0.25:
                log.info("[forecast] recent MAPE high → prefer ARIMA")
                choose = "arima"
            if seasonal == "add" and recent_mape > 0.25:
                seasonal = "mul"
        except Exception as e:
            log.warning(f"[forecast] history read failed: {e}")

    if leave_csv and Path(leave_csv).exists():
        try:
            leave_df = pd.read_csv(leave_csv, parse_dates=["date"])
            pivot = (
                leave_df.pivot_table(
                    index="date",
                    columns="leave_type",
                    values="total_leave_days",
                    aggfunc="sum",
                    fill_value=0,
                )
            )
            pivot = pivot.add_prefix("leave_").reset_index().rename(columns={"date": "ds"})
            df = df.merge(pivot, on="ds", how="left").fillna(0)
        except Exception as e:
            log.warning(f"[forecast] leave_csv load failed: {e}")

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

    future_dates = pd.date_range(df["ds"].max() + dt.timedelta(days=1), periods=periods)

    # ───── ETS モデル ─────
    ets_mod = sm.tsa.ExponentialSmoothing(
        df["y"], trend="add", seasonal=seasonal, seasonal_periods=7
    ).fit(optimized=True)
    ets_fc = ets_mod.forecast(periods)
    denom = np.where(df["y"] != 0, df["y"], np.nan)
    ets_mape = np.nanmean(np.abs((ets_mod.fittedvalues - df["y"]) / denom))

    # ───── ARIMA (pmdarima) ─────
    arima_mape = np.inf
    arima_fc = None
    exog_cols = [c for c in df.columns if c not in {"ds", "y"}]
    if _HAS_PMDARIMA:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            arima_mod = pm.auto_arima(
                df["y"],
                exogenous=df[exog_cols] if exog_cols else None,
                seasonal=False,
                stepwise=True,
                suppress_warnings=True,
                error_action="ignore",
            )
        future_exog = (
            pd.DataFrame([df[exog_cols].iloc[-1]] * periods)
            if exog_cols
            else None
        )
        if future_exog is not None:
            if "holiday" in exog_cols:
                future_exog["holiday"] = [1 if d.date() in holiday_set else 0 for d in future_dates]
        arima_fc = arima_mod.predict(n_periods=periods, exogenous=future_exog)
        try:
            train_y = getattr(arima_mod, "y", arima_mod.arima_res_.data.endog)
        except Exception:
            train_y = df["y"].to_numpy()
        denom_a = np.where(train_y != 0, train_y, np.nan)
        arima_mape = np.nanmean(
            np.abs((train_y - arima_mod.predict_in_sample()) / denom_a)
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
    try:
        hist_row = pd.DataFrame({
            "timestamp": [dt.datetime.now().isoformat()],
            "model": [sel],
            "mape": [float(np.round(sel_mape, 6))],
        })
        hist_row.to_csv(log_csv, mode="a", index=False, header=not log_csv.exists())
    except Exception as e:
        log.warning(f"[forecast] failed to update history: {e}")
    log.info(f"[forecast] forecast saved → {excel_out}")
    return excel_out


__all__ = ["build_demand_series", "forecast_need"]
