from pathlib import Path
import pandas as pd
from shift_suite.tasks.optimal_hire_plan import create_optimal_hire_plan


def test_create_optimal_hire_plan(tmp_path: Path):
    out_dir = tmp_path
    out_dir.mkdir(exist_ok=True)

    shortage_summary_df = pd.DataFrame({
        "weekday": ["月曜日", "火曜日"],
        "timeslot": ["09:00", "14:00"],
        "avg_count": [1.8, 1.2],
    })
    shortage_summary_fp = out_dir / "shortage_weekday_timeslot_summary.xlsx"
    shortage_summary_df.to_excel(shortage_summary_fp, index=False)

    role_shortage_df = pd.DataFrame({
        "role": ["看護師", "介護士"],
        "lack_h": [100, 50],
    })
    role_shortage_fp = out_dir / "shortage_role.xlsx"
    role_shortage_df.to_excel(role_shortage_fp, index=False)

    original_excel_fp = tmp_path / "original_shift.xlsx"
    work_patterns_df = pd.DataFrame({
        "勤務記号": ["日勤A", "遅番"],
        "開始": ["08:30", "13:00"],
        "終了": ["17:30", "22:00"],
    })
    with pd.ExcelWriter(original_excel_fp) as writer:
        work_patterns_df.to_excel(writer, sheet_name="勤務区分", index=False)

    result_path = create_optimal_hire_plan(out_dir, original_excel_fp)

    assert result_path is not None
    assert result_path.exists()

    result_df = pd.read_excel(result_path)
    assert not result_df.empty
    assert "推奨職種" in result_df.columns
    assert "推奨勤務区分" in result_df.columns

    first_rec = result_df.iloc[0]
    assert first_rec["推奨職種"] == "看護師"
    assert first_rec["主な不足時間帯"] == "09:00"
    assert first_rec["推奨勤務区分"] == "日勤A"
    assert first_rec["推奨採用人数"] == 2
