from pathlib import Path
import pandas as pd
from app import load_data_cached

def test_load_data_cached_parquet(tmp_path: Path):
    df = pd.DataFrame({"a": [1, 2]})
    fp = tmp_path / "test.parquet"
    df.to_parquet(fp)
    df1 = load_data_cached(str(fp), is_parquet=True, file_mtime=fp.stat().st_mtime)
    df2 = load_data_cached(str(fp), is_parquet=True, file_mtime=fp.stat().st_mtime)
    pd.testing.assert_frame_equal(df1, df2)
