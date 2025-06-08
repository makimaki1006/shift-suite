from pathlib import Path
import pandas as pd
from shift_suite.tasks.shortage import shortage_and_brief
from shift_suite.tasks.utils import gen_labels


def _create_heatmap(out_dir: Path) -> None:
    labels = gen_labels(30)[:3]
    df = pd.DataFrame(
        {
            "need": [1, 1, 1],
            "upper": [3, 3, 3],
            "2024-06-01": [2, 0, 4],
        },
        index=labels,
    )
    df.to_excel(out_dir / "heat_ALL.xlsx")


def test_optimization_outputs(tmp_path: Path) -> None:
    _create_heatmap(tmp_path)
    shortage_and_brief(tmp_path, slot=30)
    surplus_df = pd.read_excel(tmp_path / "surplus_vs_need_time.xlsx", index_col=0)
    margin_df = pd.read_excel(tmp_path / "margin_vs_upper_time.xlsx", index_col=0)
    score_df = pd.read_excel(tmp_path / "optimization_score_time.xlsx", index_col=0)

    assert surplus_df.iloc[0, 0] == 1
    assert surplus_df.iloc[2, 0] == 3
    assert margin_df.iloc[0, 0] == 1
    assert margin_df.iloc[1, 0] == 3
    assert score_df.iloc[0, 0] == 1
    assert abs(score_df.iloc[1, 0] - 0.4) < 0.01
    assert abs(score_df.iloc[2, 0] - 0.6) < 0.01
