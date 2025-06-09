import pandas as pd
from pathlib import Path

import pytest

from shift_suite.tasks.over_shortage_log import list_events, load_log, save_log


def test_load_log_missing_file(tmp_path: Path):
    fp = tmp_path / "over_shortage_log.csv"
    df = load_log(fp)
    assert df.empty
    assert set(df.columns) == {
        "date",
        "time",
        "type",
        "count",
        "reason",
        "staff",
        "memo",
    }


def test_load_log_invalid_columns(tmp_path: Path):
    fp = tmp_path / "over_shortage_log.csv"
    pd.DataFrame({"foo": [1], "bar": [2]}).to_csv(fp, index=False)
    df = load_log(fp)
    assert df.empty
    assert set(df.columns) == {
        "date",
        "time",
        "type",
        "count",
        "reason",
        "staff",
        "memo",
    }


def test_list_events_missing_files(tmp_path: Path) -> None:
    df = list_events(tmp_path)
    assert df.empty
    assert list(df.columns) == ["time", "date", "count", "type"]


def test_save_log_invalid_mode(tmp_path: Path) -> None:
    csv_fp = tmp_path / "log.csv"
    with pytest.raises(ValueError):
        save_log(pd.DataFrame(), csv_fp, mode="bad")
