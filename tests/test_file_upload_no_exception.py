import pandas as pd
from pathlib import Path
import pytest
import app


class DummyRerun(Exception):
    pass


class DummyFile:
    def __init__(self, name: str, data: bytes):
        self.name = name
        self._data = data
        self.size = len(data)

    def getbuffer(self):
        return self._data


class DummySt:
    def __init__(self):
        self.session_state = {}

    def rerun(self):
        raise DummyRerun()

    def warning(self, *a, **k):
        pass


def test_file_upload_no_streamlit_exception(monkeypatch, tmp_path: Path):
    df = pd.DataFrame({"a": [1]})
    excel_fp = tmp_path / "in.xlsx"
    with pd.ExcelWriter(excel_fp) as writer:
        df.to_excel(writer, sheet_name="Sheet1", index=False)
        df.to_excel(writer, sheet_name=app.master_sheet_keyword, index=False)
    excel_bytes = excel_fp.read_bytes()
    uploaded = DummyFile("in.xlsx", excel_bytes)

    dummy_st = DummySt()
    dummy_st.session_state["work_root_path_str"] = str(tmp_path)
    dummy_st.session_state["uploaded_files_info"] = {}
    dummy_st.session_state["candidate_sheet_list_for_ui"] = []
    dummy_st.session_state["_force_update_multiselect_flag"] = False

    monkeypatch.setattr(app, "st", dummy_st)
    monkeypatch.setattr(app, "_", lambda x: x)

    with pytest.raises(DummyRerun):
        work_root_on_upload = Path(dummy_st.session_state["work_root_path_str"])
        excel_path = work_root_on_upload / uploaded.name
        with open(excel_path, "wb") as f:
            f.write(uploaded.getbuffer())
        dummy_st.session_state["uploaded_files_info"][uploaded.name] = {
            "path": str(excel_path),
            "size": uploaded.size,
        }
        xls = pd.ExcelFile(excel_path)
        candidate_sheets = [
            s for s in xls.sheet_names if app.master_sheet_keyword not in s
        ]
        if not candidate_sheets:
            dummy_st.warning("none")
        dummy_st.session_state["candidate_sheet_list_for_ui"] = candidate_sheets or []
        dummy_st.session_state["_force_update_multiselect_flag"] = True
        dummy_st.rerun()

    assert dummy_st.session_state["candidate_sheet_list_for_ui"] == ["Sheet1"]
    assert dummy_st.session_state["_force_update_multiselect_flag"] is True
