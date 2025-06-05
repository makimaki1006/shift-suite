from pathlib import Path

import pandas as pd

from shift_suite.tasks.io_excel import ingest_excel


def test_ingest_excel_employment(tmp_path: Path):
    excel_fp = tmp_path / "shift.xlsx"

    wt = pd.DataFrame({"勤務記号": ["A"], "開始": ["09:00"], "終了": ["18:00"]})
    df = pd.DataFrame(
        {
            "氏名": ["山田"],
            "職種": ["看護師"],
            "雇用形態": ["正社員"],
            "2024-01-01": ["A"],
        }
    )
    with pd.ExcelWriter(excel_fp) as writer:
        wt.to_excel(writer, sheet_name="勤務区分", index=False)
        df.to_excel(writer, sheet_name="Sheet1", index=False)

    long_df, _, unknown = ingest_excel(excel_fp, shift_sheets=["Sheet1"], header_row=1)
    assert not unknown
    assert "employment" in long_df.columns
    assert set(long_df["employment"]) == {"正社員"}
