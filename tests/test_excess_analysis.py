from pathlib import Path

import pandas as pd

from shift_suite.tasks.shortage import shortage_and_brief
from shift_suite.tasks.utils import gen_labels, write_meta


def _create_heatmap_with_upper(out_dir: Path) -> None:
    labels = gen_labels(30)[:2]
    df = pd.DataFrame(
        {
            "need": [1, 1],
            "upper": [2, 2],
            "2024-06-01": [3, 0],
        },
        index=labels,
    )
    df.to_parquet(out_dir / "heat_ALL.parquet")
    write_meta(
        out_dir / "heatmap.meta.json",
        slot=30,
        dates=["2024-06-01"],
        summary_columns=["need", "upper", "staff", "lack", "excess"],
        estimated_holidays=[],
        dow_need_pattern=[{"time": t, **{str(i): 1 for i in range(7)}} for t in labels],
    )


def test_excess_output(tmp_path: Path) -> None:
    _create_heatmap_with_upper(tmp_path)
    shortage_and_brief(tmp_path, slot=30)
    excess_df = pd.read_parquet(tmp_path / "excess_time.parquet")
    shortage_df = pd.read_parquet(tmp_path / "shortage_time.parquet")
    assert excess_df.iloc[0, 0] == 1
    assert excess_df.iloc[1, 0] == 0
    assert shortage_df.iloc[0, 0] == 0
    assert shortage_df.iloc[1, 0] == 1
