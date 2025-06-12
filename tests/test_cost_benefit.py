from pathlib import Path

import pandas as pd

from shift_suite.tasks.cost_benefit import analyze_cost_benefit


def _create_base_files(tmp_path: Path):
    df_lack = pd.DataFrame({"role": ["A"], "lack_h": [10]})
    df_lack.to_parquet(tmp_path / "shortage_role_summary.parquet", index=False)


def test_analyze_cost_benefit_with_hire_need(tmp_path: Path):
    _create_base_files(tmp_path)
    df_plan = pd.DataFrame({"role": ["A"], "hire_need": [2]})
    df_plan.to_parquet(tmp_path / "hire_plan.parquet", index=False)

    result = analyze_cost_benefit(tmp_path)
    assert "Cost_JPY" in result.columns


def test_analyze_cost_benefit_with_hire_fte(tmp_path: Path):
    _create_base_files(tmp_path)
    df_plan = pd.DataFrame({"role": ["A"], "hire_fte": [2]})
    df_plan.to_parquet(tmp_path / "hire_plan.parquet", index=False)

    result = analyze_cost_benefit(tmp_path)
    assert "Cost_JPY" in result.columns


