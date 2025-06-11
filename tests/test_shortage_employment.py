from pathlib import Path

import pandas as pd

from shift_suite.tasks.shortage import shortage_and_brief
from shift_suite.tasks.utils import gen_labels


def _create_heatmaps(out_dir: Path) -> None:
    labels = gen_labels(30)[:2]
    df_all = pd.DataFrame({"need": [1, 1], "2024-06-01": [1, 1]}, index=labels)
    df_all.to_parquet(out_dir / "heat_ALL.parquet")
    df_emp = pd.DataFrame({"need": [1, 1], "2024-06-01": [1, 1]}, index=labels)
    df_emp.to_excel(out_dir / "heat_emp_Fulltime.xlsx")


def test_shortage_employment_output(tmp_path: Path) -> None:
    _create_heatmaps(tmp_path)
    shortage_and_brief(tmp_path, slot=30)
    fp = tmp_path / "shortage_employment_summary.parquet"
    assert fp.exists()
    df = pd.read_parquet(fp)
    assert "employment" in df.columns
