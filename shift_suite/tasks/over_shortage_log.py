from __future__ import annotations

from pathlib import Path
import logging

import pandas as pd

log = logging.getLogger(__name__)


def list_events(out_dir: Path | str) -> pd.DataFrame:
    """Return shortage/excess events as a DataFrame."""
    out_dir_path = Path(out_dir)
    records = []

    def _read(fp: Path, sheet: str, kind: str) -> None:
        if not fp.exists():
            return
        try:
            df = pd.read_parquet(fp)
        except Exception as e:  # noqa: BLE001
            log.warning("Failed to read %s [%s]: %s", fp, sheet, e)
            return

        # ``melt`` can mis-handle the index when ``df.index.name`` is None.
        # These parquet files always use ``time`` as the index name, so be
        # explicit to avoid accidentally turning the index into a data column.
        df_reset = df.reset_index()
        long = df_reset.melt(id_vars="time", var_name="date", value_name="count")
        long["date"] = pd.to_datetime(long["date"]).dt.date
        long = long[long["count"] > 0]
        if not long.empty:
            long["type"] = kind
            records.append(long)

    _read(out_dir_path / "shortage_time.parquet", "lack_time", "shortage")
    _read(out_dir_path / "excess_time.parquet", "excess_time", "excess")

    if records:
        return pd.concat(records, ignore_index=True)
    return pd.DataFrame(columns=["time", "date", "count", "type"])


def load_log(csv_path: Path | str) -> pd.DataFrame:
    """Load the shortage/excess log CSV with graceful fallback.

    If the file is missing or lacks the expected columns, an empty DataFrame
    with the standard schema is returned. The ``date`` column is parsed to
    ``datetime.date`` when present.
    """

    csv_fp = Path(csv_path)
    columns = ["date", "time", "type", "count", "reason", "staff", "memo"]

    if csv_fp.exists():
        try:
            df = pd.read_csv(csv_fp)
        except Exception as e:  # noqa: BLE001
            log.warning("Failed to read log CSV %s: %s", csv_fp, e)
            return pd.DataFrame(columns=columns)

        if not set({"date", "time", "type"}).issubset(df.columns):
            log.warning("Log CSV %s missing required columns", csv_fp)
            return pd.DataFrame(columns=columns)

        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
        # Ensure all expected columns exist
        for col in columns:
            if col not in df.columns:
                df[col] = pd.NA
        return df[columns]

    log.debug("Log CSV %s not found; returning empty frame", csv_fp)
    return pd.DataFrame(columns=columns)


def save_log(
    df: pd.DataFrame, csv_path: Path | str, *, mode: str = "overwrite"
) -> Path:
    csv_fp = Path(csv_path)
    if mode not in {"overwrite", "append"}:
        raise ValueError("mode must be 'overwrite' or 'append'")

    csv_fp.parent.mkdir(parents=True, exist_ok=True)
    if mode == "append" and csv_fp.exists():
        existing = pd.read_csv(csv_fp)
        df = pd.concat([existing, df], ignore_index=True)

    df.to_csv(csv_fp, index=False)
    return csv_fp


__all__ = ["list_events", "load_log", "save_log"]
