from pathlib import Path

import pandas as pd

from shift_suite.tasks.report_generator import generate_summary_report


def _create_sample_files(out_dir: Path) -> None:
    # heat_ALL.xlsx for date range detection
    heat_df = pd.DataFrame({"2024-06-01": [1], "2024-07-01": [2]})
    heat_df.to_parquet(out_dir / "heat_ALL.parquet")

    role_df = pd.DataFrame(
        {
            "role": ["A", "B"],
            "lack_h": [5.0, 2.0],
            "excess_h": [1.0, 0.0],
            "estimated_lack_cost_if_temporary_staff": [5000, 2000],
            "estimated_lack_penalty_cost": [10000, 4000],
            "estimated_excess_cost": [1000, 0],
        }
    )
    role_df.to_parquet(out_dir / "shortage_role_summary.parquet", index=False)

    emp_df = pd.DataFrame({"employment": ["FT"], "lack_h": [3]})
    emp_df.to_parquet(out_dir / "shortage_employment_summary.parquet", index=False)

    overall_df = pd.DataFrame({"summary_item": ["lack", "excess"], "value": [7, 3]})
    monthly_df = pd.DataFrame(
        {
            "month": ["2024-06", "2024-07"],
            "summary_item": ["lack", "lack"],
            "total_value_period (hours)": [10, 12],
        }
    )
    alerts_df = pd.DataFrame({"alert": ["check A", "check B"]})
    overall_df.to_parquet(out_dir / "stats_overall_summary.parquet", index=False)
    monthly_df.to_parquet(out_dir / "stats_monthly_summary.parquet", index=False)
    alerts_df.to_parquet(out_dir / "stats_alerts.parquet", index=False)

    wd_df = pd.DataFrame(
        {"weekday": ["Mon", "Tue"], "timeslot": ["09:00", "10:00"], "lack": [3, 1]}
    )
    wd_df.to_parquet(out_dir / "shortage_weekday_timeslot_summary.parquet", index=False)


def test_generate_summary_report(tmp_path: Path) -> None:
    _create_sample_files(tmp_path)
    md_path = generate_summary_report(tmp_path)
    assert md_path.exists()
    text = md_path.read_text(encoding="utf-8")
    assert "総不足時間" in text
