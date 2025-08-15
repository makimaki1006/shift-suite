import pandas as pd

from shift_suite.tasks.shortage import align_need_staff_columns


def test_column_mismatch_excluded() -> None:
    need_df = pd.DataFrame({"2024-06-01": [2], "2024-06-02": [2]})
    staff_df = pd.DataFrame({"2024-06-01": [1], "2024-06-03": [1]})

    inflated_total = (need_df.fillna(0) - staff_df.fillna(0)).clip(lower=0).sum().sum()

    aligned_need, aligned_staff = align_need_staff_columns(need_df, staff_df)
    fixed_total = (aligned_need - aligned_staff).clip(lower=0).sum().sum()

    assert inflated_total == 3
    assert fixed_total == 1
    assert list(aligned_need.columns) == ["2024-06-01"]
