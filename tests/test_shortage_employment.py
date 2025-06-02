import pandas as pd
from pathlib import Path
from shift_suite.tasks.shortage import shortage_and_brief
from shift_suite.tasks.utils import gen_labels


def _create_heatmaps(out_dir: Path) -> None:
    labels = gen_labels(30)[:2]
    df_all = pd.DataFrame({"need": [1, 1], "2024-06-01": [1, 1]}, index=labels)
    df_all.to_excel(out_dir / "heat_ALL.xlsx")
    df_emp = pd.DataFrame({"need": [1, 1], "2024-06-01": [1, 1]}, index=labels)
    df_emp.to_excel(out_dir / "heat_emp_Fulltime.xlsx")


def test_shortage_employment_output(tmp_path: Path) -> None:
    _create_heatmaps(tmp_path)
    shortage_and_brief(tmp_path, slot=30)
    fp = tmp_path / "shortage_employment.xlsx"
    assert fp.exists()
    df = pd.read_excel(fp, sheet_name="employment_summary")
    assert "employment" in df.columns
