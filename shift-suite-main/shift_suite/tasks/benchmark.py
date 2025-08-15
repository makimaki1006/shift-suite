"""shift_suite.benchmark  v0.1
──────────────────────────────────────────────────────────
* out_dir 群の KPI をまとめて比較
* KPI: total_hours, lack_hours, staff_slot (peak)
* 出力: benchmark_summary.xlsx
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .utils import derive_min_staff, log


def _meta(p: Path) -> dict:
    m = p / "meta.json"
    if m.exists():
        return json.loads(m.read_text(encoding="utf-8"))
    return {}


def _kpi(out_dir: Path) -> dict:
    heat_p = out_dir / "heat_ALL.parquet"
    if not heat_p.exists():
        return {}
    heat = pd.read_parquet(heat_p)
    total_h = heat.sum().sum()
    need = derive_min_staff(heat, "mean-1s")
    lack_h = heat.sub(need, axis=0).clip(lower=0).sum().sum()
    peak = heat.values.max()
    meta = _meta(out_dir)
    return dict(
        facility=meta.get("facility", out_dir.name),
        month=meta.get("month", ""),
        total_h=total_h,
        lack_h=lack_h,
        peak_slot=peak,
    )


def benchmark_multi(out_dirs: list[Path], out_path: Path | None = None) -> pd.DataFrame:
    rows = [_kpi(d) for d in out_dirs if _kpi(d)]
    if not rows:
        log.error("benchmark_multi: KPI 行が 0")
        return pd.DataFrame()

    df = pd.DataFrame(rows).sort_values(["month", "facility"])
    if out_path:
        df.to_parquet(out_path, index=False)
        log.info("benchmark_multi: %s に保存", out_path.name)
    else:
        log.info("benchmark_multi: DataFrame 返却のみ (%d 施設)", len(df))
    return df
