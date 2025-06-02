import pandas as pd
from pathlib import Path
from app import load_excel_cached


def test_load_excel_cached_without_parse_dates(monkeypatch, tmp_path: Path):
    df = pd.DataFrame({"d": ["2024-01-01"], "v": [1]})
    fp = tmp_path / "test.xlsx"
    df.to_excel(fp, index=False)

    real_read_excel = pd.read_excel
    captured_kwargs = {}

    def fake_read_excel(path, **kwargs):
        captured_kwargs.update(kwargs)
        return real_read_excel(path, **kwargs)

    monkeypatch.setattr(pd, "read_excel", fake_read_excel)

    result = load_excel_cached(str(fp), file_mtime=fp.stat().st_mtime)

    assert "parse_dates" not in captured_kwargs
    pd.testing.assert_frame_equal(result, real_read_excel(fp))
