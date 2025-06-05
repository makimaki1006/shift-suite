import importlib
import sys
import types
import datetime as dt

# Provide minimal pandas/numpy stubs so the module can be imported without the real dependencies
fake_pd = types.SimpleNamespace(
    Timestamp=lambda x: types.SimpleNamespace(
        to_pydatetime=lambda: dt.datetime.fromtimestamp(float(x))
    ),
    to_datetime=lambda x, errors="raise": dt.datetime.fromisoformat(x),
    DataFrame=object,
    Series=object,
)
fake_np = types.SimpleNamespace(nan=float("nan"))
sys.modules.setdefault("pandas", fake_pd)
sys.modules.setdefault("numpy", fake_np)

utils = importlib.import_module("shift_suite.tasks.utils")


def test_excel_date_serial():
    d = utils.excel_date(1)
    assert d == dt.date(1899, 12, 31)


def test_to_hhmm_variants():
    assert utils.to_hhmm(8.5) == "08:30"
    assert utils.to_hhmm("23:45") == "23:45"
    assert utils.to_hhmm("12:00:59") == "12:00"
    assert utils.to_hhmm(None) is None
