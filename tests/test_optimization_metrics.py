from pathlib import Path
import pandas as pd
from shift_suite.tasks.shortage import shortage_and_brief
from shift_suite.tasks.utils import gen_labels, write_meta


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
    df.to_parquet(out_dir / "heat_ALL.parquet")
    write_meta(
        out_dir / "heatmap.meta.json",
        slot=30,
        dates=["2024-06-01"],
        summary_columns=["need", "upper", "staff", "lack", "excess"],
        estimated_holidays=[],
        dow_need_pattern=[{"time": t, **{str(i): 1 for i in range(7)}} for t in labels],
    )


def test_optimization_outputs(tmp_path: Path) -> None:
    _create_heatmap(tmp_path)
    shortage_and_brief(tmp_path, slot=30)
    surplus_df = pd.read_parquet(tmp_path / "surplus_vs_need_time.parquet")
    margin_df = pd.read_parquet(tmp_path / "margin_vs_upper_time.parquet")
    score_df = pd.read_parquet(tmp_path / "optimization_score_time.parquet")

    assert surplus_df.iloc[0, 0] == 1
    assert surplus_df.iloc[2, 0] == 3
    assert margin_df.iloc[0, 0] == 1
    assert margin_df.iloc[1, 0] == 3
    assert score_df.iloc[0, 0] == 1
    assert abs(score_df.iloc[1, 0] - 0.4) < 0.01
    assert abs(score_df.iloc[2, 0] - 0.6) < 0.01
