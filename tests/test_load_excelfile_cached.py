import pandas as pd
from pathlib import Path
from app import load_excelfile_cached

def test_load_excelfile_cached(tmp_path: Path):
    df = pd.DataFrame({"a": [1, 2]})
    fp = tmp_path / "test.xlsx"
    df.to_excel(fp, index=False)

    xls = load_excelfile_cached(str(fp), file_mtime=fp.stat().st_mtime)
    assert isinstance(xls, pd.ExcelFile)

    # Call again to ensure the cached resource is used without pickle errors
    xls2 = load_excelfile_cached(str(fp), file_mtime=fp.stat().st_mtime)
    assert isinstance(xls2, pd.ExcelFile)
