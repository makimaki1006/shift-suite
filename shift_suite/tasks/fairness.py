"""
shift_suite.tasks.fairness  v0.6  ─ 完全 Try-&-Recover 版
夜勤負担の公平性 (Jain 指数) を計算して Excel 出力する。

long_df : ingest 後の “縦持ち” データフレーム
          必須情報 … 『スタッフ識別子』『時刻／日付』
          列名バリエーションは自動吸収する（下記参照）

------------------------------------------------------------
● スタッフ列の検索順
    1. 明示指定   staff_col=...
    2. 既知エイリアス: staff / name / worker / employee / member / スタッフ / 職員 / 従業員
    3. Index / MultiIndex に上記が含まれていれば reset_index()
    4. 最後の手段として、object 型列を一つ選び 'staff' と見なす

● 時刻列の検索順
    1. time 列
    2. datetime / dt 列 → .dt.time
    3. DatetimeIndex → index.time
    4. 失敗したら 00:00 を仮置き（警告）

夜勤時間帯（デフォルト 22:00-06:00）は引数で変更可
"""

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


# ═════════════════════════ helper ═════════════════════════
_STAFF_ALIASES = [
    "staff", "name", "worker", "employee", "member",
    "スタッフ", "職員", "従業員",
]


def _find_or_make_staff(df: pd.DataFrame, staff_col: Optional[str] = None) -> pd.Series:
    """staff 列を返す。見つからなければ推定して追加"""
    if staff_col and staff_col in df.columns:
        return df[staff_col]

    # 既知エイリアス
    for col in _STAFF_ALIASES:
        if col in df.columns:
            df.rename(columns={col: "staff"}, inplace=True)
            return df["staff"]

    # index / multi-index?
    if isinstance(df.index, (pd.Index, pd.MultiIndex)):
        for name in df.index.names:
            if name in _STAFF_ALIASES:
                df.reset_index(inplace=True)
                df.rename(columns={name: "staff"}, inplace=True)
                return df["staff"]

    # object 型列のうちユニークが多いものを staff と見なす
    obj_cols = [c for c in df.columns if df[c].dtype == "object"]
    if obj_cols:
        candidate = max(obj_cols, key=lambda c: df[c].nunique())
        logger.warning(f"fairness: staff 列を推定 — '{candidate}' を使用")
        df.rename(columns={candidate: "staff"}, inplace=True)
        return df["staff"]

    raise KeyError("スタッフを示す列が見つかりません（staff/name/…）")


def _ensure_time_column(df: pd.DataFrame) -> pd.Series:
    """time 列が無ければ最大限推定して追加し、返す"""
    if "time" in df.columns:
        return df["time"]

    if "datetime" in df.columns:
        df["time"] = pd.to_datetime(df["datetime"]).dt.time
        return df["time"]
    if "dt" in df.columns:
        df["time"] = pd.to_datetime(df["dt"]).dt.time
        return df["time"]
    if isinstance(df.index, pd.DatetimeIndex):
        df["time"] = df.index.time
        return df["time"]

    logger.warning("fairness: 'time' 列を推定できず全行 00:00 を仮置き")
    df["time"] = dt.time(0, 0)
    return df["time"]


def _is_night(t: dt.time, night_start: dt.time, night_end: dt.time) -> bool:
    if night_start <= night_end:
        return night_start <= t < night_end
    return t >= night_start or t < night_end


# ═════════════════════════ main ═════════════════════════
def run_fairness(
    long_df: pd.DataFrame,
    out_dir: Path | str,
    *,
    staff_col: Optional[str] = None,
    slot_min: int = 30,
    night_start: dt.time = dt.time(22, 0),
    night_end: dt.time = dt.time(6, 0),
) -> None:
    """
    long_df から夜勤比率と Jain 指数を計算し、
    fairness_before.xlsx / fairness_after.xlsx を保存する。
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = long_df.copy()

    # ── 列の確保 ───────────────────────────────
    staff = _find_or_make_staff(df, staff_col)
    times = _ensure_time_column(df)

    # ── 夜勤フラグ ─────────────────────────────
    df["is_night"] = times.apply(lambda t: int(_is_night(t, night_start, night_end)))

    # ── スタッフ別集計 ────────────────────────
    group = df.groupby("staff")["is_night"].agg(
        night_slots="sum", total_slots="size"
    )
    summary = group.reset_index()
    summary["night_ratio"] = summary["night_slots"] / summary["total_slots"]

    # Jain 指数
    from .utils import calculate_jain_index
    s = summary["night_ratio"]
    jain = calculate_jain_index(s)
    summary.attrs["jain"] = jain

    # ── 出力 ──────────────────────────────────
    before_fp = out_dir / "fairness_before.xlsx"
    after_fp = out_dir / "fairness_after.xlsx"  # 調整ロジック未実装 → 同値

    with pd.ExcelWriter(before_fp, engine="openpyxl") as w:
        summary.to_excel(w, sheet_name="before", index=False)
        pd.DataFrame({"metric": ["jain"], "value": [jain]}).to_excel(
            w, sheet_name="meta", index=False
        )
    summary.to_excel(after_fp, sheet_name="after", index=False)

    print(f"[fairness] 完了: Jain={jain:.3f}  →  {before_fp.name}")
