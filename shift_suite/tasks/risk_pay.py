"""shift_suite.risk_pay – pay とシフト乖離の単純計算（暫定ロジック）"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)


def risk_pay(out_dir: Path, slot: int, pay_csv: Path | None):
    """
    pay_csv : name,hourly を持つ CSV
    * out_dir/shortage_role.xlsx が無い場合はスキップ
    """
    sh_p = out_dir / "shortage_role_summary.parquet"
    if not sh_p.exists():
        log.warning("risk_pay: shortage_role.xlsx missing – skipped")
        return
    lack = pd.read_parquet(sh_p).rename(columns=str)
    if pay_csv and Path(pay_csv).exists():
        pay = pd.read_csv(pay_csv)
        df = lack.merge(pay, on="role", how="left")
        df["extra_cost"] = df["lack_h"] * df["hourly"].fillna(0)
    else:
        df = lack.assign(hourly=0, extra_cost=0)
    df.to_parquet(out_dir / "risk_pay.parquet", index=False)
