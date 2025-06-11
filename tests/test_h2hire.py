from pathlib import Path

import pandas as pd

from shift_suite.tasks.h2hire import build_hire_plan


def test_build_hire_plan_safety_factor(tmp_path: Path):
    df = pd.DataFrame({"role": ["A", "B"], "lack_h": [150, 70]})
    shortage_fp = tmp_path / "shortage_role_summary.parquet"
    df.to_parquet(shortage_fp, index=False)

    out_default = build_hire_plan(tmp_path, monthly_hours_fte=100)
    out_factor1 = build_hire_plan(
        tmp_path,
        out_excel="hire_plan_sf1.parquet",
        monthly_hours_fte=100,
        safety_factor=1.0,
    )
    df_default = pd.read_parquet(out_default)
    df_factor1 = pd.read_parquet(out_factor1)
    pd.testing.assert_frame_equal(df_default, df_factor1)

    out_factor15 = build_hire_plan(
        tmp_path,
        out_excel="hire_plan_sf15.parquet",
        monthly_hours_fte=100,
        safety_factor=1.5,
    )
    df_factor15 = pd.read_parquet(out_factor15)
    assert list(df_factor15["hire_fte"]) == [3, 2]
