from pathlib import Path
import pandas as pd

from shift_suite.tasks.shortage import shortage_and_brief
from shift_suite.tasks.utils import gen_labels, write_meta


def _create_heatmap(out_dir: Path) -> None:
    labels = gen_labels(30)[:2]
    df = pd.DataFrame({"need": [1, 1], "2024-06-08": [1, 1]}, index=labels)
    df.to_parquet(out_dir / "heat_ALL.parquet")
    pattern = [{"time": t, **{str(i): 1 for i in range(5)}} for t in labels]
    write_meta(
        out_dir / "heatmap.meta.json",
        slot=30,
        dates=["2024-06-08"],
        summary_columns=["need", "upper", "staff", "lack", "excess"],
        estimated_holidays=[],
        dow_need_pattern=pattern,
    )


def test_need_zero_when_pattern_missing(tmp_path: Path) -> None:
    _create_heatmap(tmp_path)
    shortage_and_brief(tmp_path, slot=30)
    shortage_df = pd.read_parquet(tmp_path / "shortage_time.parquet")
    surplus_df = pd.read_parquet(tmp_path / "surplus_vs_need_time.parquet")
    assert shortage_df.iloc[0, 0] == 0
    assert surplus_df.iloc[0, 0] == 1
