import pandas as pd
import logging
from shift_suite.tasks.shortage import shortage_and_brief


def test_period_precheck_trims(tmp_path, caplog):
    dates = pd.date_range("2024-01-01", periods=365, freq="D")
    cols = dates.strftime("%Y-%m-%d")
    need_df = pd.DataFrame([1] * len(cols), index=["00:00"], columns=cols)
    staff_df = pd.DataFrame([0] * len(cols), index=["00:00"], columns=cols)
    need_df.to_parquet(tmp_path / "need_per_date_slot.parquet")
    staff_df.to_parquet(tmp_path / "heat_ALL.parquet")
    caplog.set_level(logging.WARNING)
    shortage_and_brief(tmp_path, slot=60)
    output = pd.read_parquet(tmp_path / "shortage_time.parquet")
    warned = any("PERIOD_PRECHECK" in r.message for r in caplog.records)
    assert warned
    assert output.shape[1] < len(cols)
