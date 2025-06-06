import pandas as pd
from pathlib import Path

from shift_suite.tasks.over_shortage_log import load_log


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
