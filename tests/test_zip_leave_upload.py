import pandas as pd
from pathlib import Path
import app


def _sample_heatmap(path: Path) -> None:
    df = pd.DataFrame({"need": [0], "2024-06-01": [1], "2024-06-02": [2]})
    df.to_excel(path / "heat_ALL.xlsx")


def test_load_leave_results_reconstructs(tmp_path: Path):
    _sample_heatmap(tmp_path)
    leave_df = pd.DataFrame({
        "date": ["2024-06-01", "2024-06-02"],
        "leave_type": [app.LEAVE_TYPE_REQUESTED, app.LEAVE_TYPE_REQUESTED],
        "total_leave_days": [1, 2],
    })
    leave_df.to_csv(tmp_path / "leave_analysis.csv", index=False)

    results = app.load_leave_results_from_dir(tmp_path)
    assert "staff_balance_daily" in results
    assert "concentration_requested" in results
    assert "concentration_both" in results
    assert len(results["staff_balance_daily"]) == 2
    assert list(results["concentration_requested"]["leave_applicants_count"]) == [1, 2]
    assert list(results["concentration_both"]["paid_count"]) == [0, 0]


def test_load_leave_results_reads_optional_files(tmp_path: Path):
    _sample_heatmap(tmp_path)
    leave_df = pd.DataFrame({
        "date": ["2024-06-01"],
        "leave_type": [app.LEAVE_TYPE_REQUESTED],
        "total_leave_days": [1],
    })
    leave_df.to_csv(tmp_path / "leave_analysis.csv", index=False)

    staff_df = pd.DataFrame({"date": ["2024-06-01"], "total_staff": [5]})
    staff_df.to_csv(tmp_path / "staff_balance_daily.csv", index=False)
    conc_df = pd.DataFrame({"date": ["2024-06-01"], "leave_applicants_count": [1]})
    conc_df.to_csv(tmp_path / "concentration_requested.csv", index=False)

    results = app.load_leave_results_from_dir(tmp_path)
    assert results["staff_balance_daily"].iloc[0]["total_staff"] == 5
    assert results["concentration_requested"].iloc[0]["leave_applicants_count"] == 1
    assert "concentration_both" in results
