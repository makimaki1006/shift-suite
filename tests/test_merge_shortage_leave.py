import pandas as pd
from pathlib import Path
from shift_suite.tasks.merge_shortage_leave import merge_shortage_leave


def test_merge_shortage_leave(tmp_path: Path):
    # Create sample shortage_time.xlsx
    shortage_df = pd.DataFrame(
        {
            "2024-06-01": [2, 1],
            "2024-06-02": [0, 3],
        },
        index=["09:00", "09:30"],
    )
    shortage_fp = tmp_path / "shortage_time.xlsx"
    shortage_df.to_excel(shortage_fp)

    # Create sample leave_analysis.csv
    leave_df = pd.DataFrame(
        [
            {"date": "2024-06-01", "leave_type": "paid", "total_leave_days": 1},
            {"date": "2024-06-01", "leave_type": "requested", "total_leave_days": 2},
            {"date": "2024-06-02", "leave_type": "paid", "total_leave_days": 2},
        ]
    )
    leave_fp = tmp_path / "leave_analysis.csv"
    leave_df.to_csv(leave_fp, index=False)

    log_df = pd.DataFrame(
        [
            {"date": "2024-06-01", "time": "09:00", "count": 1, "type": "shortage", "reason": "Planned leave"},
            {"date": "2024-06-01", "time": "09:30", "count": 1, "type": "shortage", "reason": "Sudden absence"},
        ]
    )
    log_fp = tmp_path / "over_shortage_log.csv"
    log_df.to_csv(log_fp, index=False)

    out_fp = merge_shortage_leave(tmp_path)
    assert out_fp.exists()

    result = pd.read_csv(out_fp, parse_dates=["date"])
    expected_cols = {"time", "date", "lack", "leave_applicants", "net_shortage", "other_reason_lack"}
    assert expected_cols.issubset(result.columns)

    calc_net = (result["lack"] - result["leave_applicants"]).clip(lower=0)
    assert result["net_shortage"].equals(calc_net)
    other_val = result.loc[(result["time"] == "09:30") & (result["date"] == pd.Timestamp("2024-06-01")), "other_reason_lack"].iloc[0]
    assert other_val == 1
