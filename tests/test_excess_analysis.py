import pandas as pd
from pathlib import Path
from shift_suite.tasks.shortage import shortage_and_brief
from shift_suite.tasks.utils import gen_labels


def _create_heatmap_with_upper(out_dir: Path) -> None:
    labels = gen_labels(30)[:2]
    df = pd.DataFrame({
        "need": [1, 1],
        "upper": [2, 2],
        "2024-06-01": [3, 0],
    }, index=labels)
    df.to_excel(out_dir / "heat_ALL.xlsx")


def test_excess_output(tmp_path: Path) -> None:
    _create_heatmap_with_upper(tmp_path)
    shortage_and_brief(tmp_path, slot=30)
    excess_df = pd.read_excel(tmp_path / "excess_time.xlsx", index_col=0)
    shortage_df = pd.read_excel(tmp_path / "shortage_time.xlsx", index_col=0)
    assert excess_df.iloc[0, 0] == 1
    assert excess_df.iloc[1, 0] == 0
    assert shortage_df.iloc[0, 0] == 0
    assert shortage_df.iloc[1, 0] == 1
