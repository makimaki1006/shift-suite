import pandas as pd
from pathlib import Path
from shift_suite.tasks.io_excel import ingest_excel


def test_ingest_excel_reads_employment_type(tmp_path: Path) -> None:
    excel_fp = tmp_path / "in.xlsx"
    wt_df = pd.DataFrame({"記号": ["A"], "開始": ["08:00"], "終了": ["09:00"]})
    shift_df = pd.DataFrame({
        "氏名": ["Alice"],
        "職種": ["Manager"],
        "雇用形態": ["正社員"],
        "2024-01-01": ["A"],
    })
    with pd.ExcelWriter(excel_fp) as writer:
        wt_df.to_excel(writer, sheet_name="勤務区分", index=False)
        shift_df.to_excel(writer, sheet_name="Sheet1", index=False)

    long_df, _ = ingest_excel(excel_fp, shift_sheets=["Sheet1"], header_row=1)
    assert "employment_type" in long_df.columns
    assert set(long_df["employment_type"]) == {"正社員"}

