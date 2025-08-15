import pathlib
import sys

import pandas as pd

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from shift_suite.tasks.shortage import validate_and_cap_shortage


def test_single_day_spike_capped():
    # Day 1 has 20h shortage, Day 2 has 4h shortage
    shortage_df = pd.DataFrame(
        {
            "slot1": [20, 2],
            "slot2": [0, 2],
        },
        index=[pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-02")],
    )

    capped_df, was_capped = validate_and_cap_shortage(
        shortage_df.copy(), period_days=2, slot_hours=1
    )

    # Day 1 should be capped to 5h
    assert capped_df.loc[pd.Timestamp("2024-01-01")].sum() == 5
    # Day 2 should remain unchanged at 4h
    assert capped_df.loc[pd.Timestamp("2024-01-02")].sum() == 4
    # Capping should be reported
    assert was_capped
