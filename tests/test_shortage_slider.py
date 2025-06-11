from pathlib import Path

import pandas as pd

from shift_suite.tasks.shortage import shortage_and_brief
from shift_suite.tasks.utils import gen_labels


def _create_sample_heatmap(out_dir: Path) -> None:
    """Create a minimal heat_ALL.parquet for testing."""
    labels = gen_labels(30)[:2]  # just a couple of slots
    df = pd.DataFrame({"need": [1, 1], "2024-06-01": [0, 0]}, index=labels)
    df.to_parquet(out_dir / "heat_ALL.parquet")


def test_shortage_time_unchanged_by_slider(tmp_path: Path) -> None:
    """Verify shortage results are independent of slider-like inputs.

    Running ``shortage_and_brief`` with its default parameters and with
    an alternate value simulating a slider (empty ``holidays`` list) should
    produce identical ``shortage_time.parquet`` files.
    """
    _create_sample_heatmap(tmp_path)

    shortage_and_brief(tmp_path, slot=30)
    df_default = pd.read_parquet(tmp_path / "shortage_time.parquet")

    shortage_and_brief(tmp_path, slot=30, holidays=[])
    df_slider0 = pd.read_parquet(tmp_path / "shortage_time.parquet")

    pd.testing.assert_frame_equal(df_default, df_slider0)
