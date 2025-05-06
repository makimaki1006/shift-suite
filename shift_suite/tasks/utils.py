"""
shift_suite.tasks.utils  v1.1.1
────────────────────────────────────────────────────────
* 共通ユーティリティ
* 2025-04-30
    - write_meta(): ディレクトリ渡しを許容
    - derive_max_staff(): 1列ヒートマップで NaN→0
"""

from __future__ import annotations

import json
import logging
import math
import re
import shutil
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
from pandas import DataFrame, Series

# ────────────────── 1. ロガー ──────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
log = logging.getLogger("shift_suite")

# ────────────────── 2. Excel 日付ユーティリティ ──────────────────
def excel_date(excel_serial) -> datetime | None:
    """Excel 1900 シリアル or pandas.Timestamp 等 → datetime"""
    if excel_serial in (None, "", np.nan):
        return None
    if isinstance(excel_serial, (datetime, np.datetime64, pd.Timestamp)):
        return pd.Timestamp(excel_serial).to_pydatetime()
    try:
        base = datetime(1899, 12, 30)  # Excel 起点 (1900-01-00)
        return (base + timedelta(days=float(excel_serial))).date()
    except (ValueError, TypeError):
        return None


def to_hhmm(x) -> str | None:
    """8.5 → '08:30' / '23:45' → '23:45' / Excel シリアルなど柔軟変換"""
    if x in (None, "", np.nan):
        return None
    if isinstance(x, (int, float)) and not math.isnan(x):
        h = int(x)
        m = int(round((x - h) * 60))
        return f"{h:02d}:{m:02d}"
    x = str(x).strip()
    m = re.match(r"^(\d{1,2}):(\d{1,2})$", x)
    if m:
        return f"{int(m.group(1)):02d}:{int(m.group(2)):02d}"
    return None


# ────────────────── 3. ラベル／ファイル名 ──────────────────
def gen_labels(slot: int) -> list[str]:
    """00:00-23:59 を slot 分刻みで HH:MM ラベル化"""
    t = datetime(2000, 1, 1)
    labels: list[str] = []
    while t.day == 1:  # 24h
        labels.append(t.strftime("%H:%M"))
        t += timedelta(minutes=slot)
    return labels


INVALID_CHARS = r'[\\/*?:\[\]]|\n|\r'


def safe_sheet(name: str, *, for_path: bool = False) -> str:
    """Excel シート／ファイル用に危険文字を置換"""
    out = re.sub(INVALID_CHARS, "_", str(name))
    out = out.strip()[:31]  # Excel シートは 31 文字上限
    if for_path:
        out = out.replace(" ", "_")
    return out or "sheet"


# ────────────────── 4. DataFrame 保存 ──────────────────
def save_df_xlsx(
    df: DataFrame,
    fp: Path | str,
    sheet: str | None = None,
    *,
    index: bool = True,
    engine: str = "openpyxl",
) -> Path:
    """
    汎用 Excel 保存ラッパー
    - 長いパスも一時ファイル経由で安全に保存
    - sheet=None → ファイル名を安全化
    """
    fp = Path(fp)
    sheet_name = sheet or safe_sheet(fp.stem)
    to_excel_kwargs = dict(index=index, sheet_name=sheet_name, engine=engine)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        df.to_excel(tmp.name, **to_excel_kwargs)
        tmp.flush()
        tmp.close()
        fp.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(tmp.name, fp)

    return fp


# ────────────────── 5. メタファイル ──────────────────
def write_meta(target: Path | str, /, **meta) -> Path:
    """
    JSON メタ情報を書き出し。

    Parameters
    ----------
    target : Path | str
        * ディレクトリを渡した場合 → `<dir>/meta.json`
        * ファイルパスを渡した場合 → そのファイルに書き込み
    meta : dict
        書き込むキー＝値
    """
    target = Path(target)
    meta_fp = target / "meta.json" if target.is_dir() else target
    meta_fp.parent.mkdir(parents=True, exist_ok=True)
    meta_fp.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    return meta_fp


# ────────────────── 6. ZIP ユーティリティ ──────────────────
def safe_make_archive(src_dir: Path, dst_zip: Path) -> Path:
    """Windows 長パス対応付き shutil.make_archive 相当"""
    src_dir, dst_zip = Path(src_dir), Path(dst_zip)
    if dst_zip.exists():
        dst_zip.unlink()

    with zipfile.ZipFile(dst_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in src_dir.rglob("*"):
            zf.write(p, p.relative_to(src_dir))
    return dst_zip


# ────────────────── 7. スタッフ数閾値計算 ──────────────────
def derive_min_staff(heat: DataFrame, method: str = "p25") -> Series:
    values = heat.select_dtypes("number")
    if method == "p25":
        return values.quantile(0.25, axis=1).round()
    if method == "mean-1s":
        return (values.mean(axis=1) - values.std(axis=1)).clip(lower=0).round()
    if method == "mode":
        return values.mode(axis=1).iloc[:, 0].round()
    raise ValueError(f"Unknown min_method: {method}")


def derive_max_staff(heat: DataFrame, method: str = "mean+1s") -> Series:
    values = heat.select_dtypes("number")
    if method == "mean+1s":
        mu = values.mean(axis=1)
        sig = values.std(axis=1).fillna(0)  # ← NaN→0
        return (mu + sig).round()
    if method == "p75":
        return values.quantile(0.75, axis=1).round()
    raise ValueError(f"Unknown max_method: {method}")


# ────────────────── 8. Jain指数計算 ──────────────────
def calculate_jain_index(values: pd.Series) -> float:
    """
    夜勤比率などの分布の公平性を評価するJain指数を計算します。
    値が1に近いほど公平、0に近いほど不公平を示します。
    
    Parameters
    ----------
    values : pd.Series
        評価する値の分布（例：夜勤比率）
        
    Returns
    -------
    float
        Jain指数（0～1の範囲、1が完全に公平）
    """
    if values.empty:
        return 1.0
    return round((values.sum() ** 2) / (len(values) * (values ** 2).sum()), 3)


# ────────────────── 9. Public Re-export ──────────────────
__all__: Sequence[str] = [
    "log",
    "excel_date",
    "to_hhmm",
    "gen_labels",
    "safe_sheet",
    "save_df_xlsx",
    "write_meta",
    "safe_make_archive",
    "derive_min_staff",
    "derive_max_staff",
    "calculate_jain_index",
]
