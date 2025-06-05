from __future__ import annotations

from pathlib import Path

import pandas as pd


def list_events(out_dir: Path | str) -> pd.DataFrame:
    """Return shortage/excess events as a DataFrame."""
    out_dir_path = Path(out_dir)
    records = []

    def _read(fp: Path, sheet: str, kind: str) -> None:
        if fp.exists():
            df = pd.read_excel(fp, sheet_name=sheet, index_col=0)
            long = (
                df.reset_index()
                .melt(id_vars=df.index.name, var_name="date", value_name="count")
                .rename(columns={df.index.name: "time"})
            )
            long["date"] = pd.to_datetime(long["date"]).dt.date
            long = long[long["count"] > 0]
            if not long.empty:
                long["type"] = kind
                records.append(long)

    _read(out_dir_path / "shortage_time.xlsx", "lack_time", "shortage")
    _read(out_dir_path / "excess_time.xlsx", "excess_time", "excess")

    if records:
        return pd.concat(records, ignore_index=True)
    return pd.DataFrame(columns=["time", "date", "count", "type"])


def load_log(csv_path: Path | str) -> pd.DataFrame:
    csv_fp = Path(csv_path)
    if csv_fp.exists():
        return pd.read_csv(csv_fp)
    return pd.DataFrame()


def save_log(df: pd.DataFrame, csv_path: Path | str, *, mode: str = "overwrite") -> Path:
    csv_fp = Path(csv_path)
    csv_fp.parent.mkdir(parents=True, exist_ok=True)
    if mode == "append" and csv_fp.exists():
        existing = pd.read_csv(csv_fp)
        df = pd.concat([existing, df], ignore_index=True)
    df.to_csv(csv_fp, index=False)
    return csv_fp

