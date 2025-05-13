"""
shift_suite.tasks.fairness  v0.7  —  Safe-Time & Detailed-Log 版
夜勤負担の公平性 (Jain 指数) を計算し Excel 出力する。

long_df : ingest 後の “縦持ち” DataFrame
          必須 … スタッフ識別列・時刻情報列（HH:MM 文字列でも可）

------------------------------------------------------------
● スタッフ列探索順
    1. 明示指定 staff_col=...
    2. 既知エイリアス: staff / name / worker / employee / member / スタッフ / 職員 / 従業員
    3. Index / MultiIndex に含まれる場合 reset_index()
    4. 最後の手段として object 型列のユニーク数で推定

● 時刻列探索順
    1. time 列       → 文字列なら HH:MM 解析
    2. datetime 列   → .dt.time
    3. dt 列         → .dt.time
    4. DatetimeIndex → index.time
    5. 失敗したら 00:00 を仮置き (WARN)

夜勤帯デフォルト = 22:00–06:00（引数で変更可）
"""

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import Optional, Sequence

import pandas as pd

logger = logging.getLogger(__name__)
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    )
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

# ═════════════════════════ helper ═════════════════════════
_STAFF_ALIASES: Sequence[str] = [
    "staff",
    "name",
    "worker",
    "employee",
    "member",
    "スタッフ",
    "職員",
    "従業員",
]


def _find_or_make_staff(df: pd.DataFrame, staff_col: Optional[str] = None) -> pd.Series:
    """staff 列を返す。見つからなければ推定して追加"""
    if staff_col and staff_col in df.columns:
        return df[staff_col]

    for col in _STAFF_ALIASES:
        if col in df.columns:
            df.rename(columns={col: "staff"}, inplace=True)
            return df["staff"]

    if isinstance(df.index, (pd.Index, pd.MultiIndex)):
        for name in df.index.names:
            if name in _STAFF_ALIASES:
                df.reset_index(inplace=True)
                df.rename(columns={name: "staff"}, inplace=True)
                return df["staff"]

    obj_cols = [c for c in df.columns if df[c].dtype == "object"]
    if obj_cols:
        candidate = max(obj_cols, key=lambda c: df[c].nunique())
        logger.warning(f"[fairness] staff 列を推定 — '{candidate}' を使用")
        df.rename(columns={candidate: "staff"}, inplace=True)
        return df["staff"]

    raise KeyError("スタッフを示す列が見つかりません（staff/name/…）")


def _parse_time_safe(x) -> Optional[dt.time]:
    """あらゆる入力を dt.time に変換。失敗時 None"""
    if isinstance(x, dt.time):
        return x
    try:
        return pd.to_datetime(str(x), errors="raise").time()
    except Exception:  # pragma: no cover
        return None


def _ensure_time_column(df: pd.DataFrame) -> pd.Series:
    """time 列が無ければ推定して追加し、常に dt.time 型で返す"""
    # 1) 明示的 time 列
    if "time" in df.columns:
        col = df["time"]
        if pd.api.types.is_object_dtype(col.dtype) or pd.api.types.is_string_dtype(col.dtype):
            df["time"] = col.apply(_parse_time_safe)
        elif pd.api.types.is_datetime64_any_dtype(col.dtype):
            df["time"] = pd.to_datetime(col).dt.time
        return df["time"]

    # 2) datetime / dt 列
    for cand in ("datetime", "dt"):
        if cand in df.columns:
            df["time"] = pd.to_datetime(df[cand], errors="coerce").dt.time
            return df["time"]

    # 3) DatetimeIndex
    if isinstance(df.index, pd.DatetimeIndex):
        df["time"] = df.index.time
        return df["time"]

    # 4) fallback
    logger.warning("[fairness] 'time' を推定できず全行 00:00 を仮置き")
    df["time"] = dt.time(0, 0)
    return df["time"]


def _is_night(t: Optional[dt.time], night_start: dt.time, night_end: dt.time) -> bool:
    if t is None:
        return False
    if night_start <= night_end:  # 例: 22–23 時間帯
        return night_start <= t < night_end
    # 翌日跨ぎ 例: 22:00–06:00
    return t >= night_start or t < night_end


# ═════════════════════════ main ═════════════════════════
def run_fairness(
    long_df: pd.DataFrame,
    out_dir: Path | str,
    *,
    staff_col: Optional[str] = None,
    slot_min: int = 30,  # 現在は未使用・将来の集計粒度用
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
    logger.info("[fairness] 夜勤フラグ計算中 …")
    df["is_night"] = times.apply(lambda t: int(_is_night(t, night_start, night_end)))

    # ── スタッフ別集計 ────────────────────────
    group = df.groupby("staff")["is_night"].agg(
        night_slots="sum", total_slots="size"
    )
    summary = group.reset_index()
    summary["night_ratio"] = summary["night_slots"] / summary["total_slots"]

    # Jain 指数
    from .utils import calculate_jain_index  # ローカル util
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

    logger.info(f"[fairness] 完了: Jain={jain:.3f}  →  {before_fp.name}")
