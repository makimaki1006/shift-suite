# shift_suite / tasks / io_excel.py
# v2.6.1  (2025-05-13 stable)
# =============================================================================
# 目的
#   1.「勤務区分」シート → 勤務コードごとに 30 分スロット配列を生成
#   2. 実績シートを長形式 (long_df) へ展開
#   3. 未定義コード／日付パース失敗はエラーで即停止
# 主要修正
#   • header_row を正しく反映
#   • 列名 normalize の TypeError 修正
#   • 00:00 休スロット／曜日行スキップ／未登録コード abort
# =============================================================================

from __future__ import annotations
import datetime as dt, re, logging
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd, streamlit as st

logger = logging.getLogger(__name__)

# ───────────────────────────────────────────────────────────────
SLOT_MINUTES = 30                                                  # 30 分固定
COL_ALIASES = {                                                    # 勤務区分シート列
    "記号": "code", "コード": "code", "勤務記号": "code",
    "開始": "start", "開始時刻": "start", "start": "start",
    "終了": "end",   "終了時刻": "end",   "end": "end",
}
SHEET_COL_ALIAS = {                                                # 実績シート列
    "氏名": "staff", "名前": "staff", "staff": "staff", "name": "staff",
    "従業員": "staff", "member": "staff",
    "職種": "role",  "部署": "role",  "役職": "role", "role": "role",
}
DOW_TOKENS = {"月", "火", "水", "木", "金", "土", "日", "明"}      # 曜日セル

# ───────────────────────────────────────────────────────────────
def _normalize(val) -> str:
    """全角半角空白/改行を除去して小文字化せず返す"""
    txt = str(val).replace("　", " ")
    return re.sub(r"\s+", "", txt).strip()

def _to_hhmm(v) -> str | None:
    """Excel シリアル値 / 'HH:MM[:SS]' → 'HH:MM' へ正規化"""
    if pd.isna(v) or v == "":
        return None
    if isinstance(v, (int, float)):
        try:
            return (dt.datetime(1899, 12, 30) + dt.timedelta(days=float(v))).strftime("%H:%M")
        except Exception:
            return None
    s = str(v).strip()
    if re.fullmatch(r"\d{1,2}:\d{2}:\d{2}", s):
        s = s[:-3]
    try:
        return dt.datetime.strptime(s, "%H:%M").strftime("%H:%M")
    except ValueError:
        return None

def _expand(st: str, ed: str) -> list[str]:
    """開始〜終了を 30 分刻みに展開（日跨ぎ対応，終了時刻は含めない）"""
    s = dt.datetime.strptime(st, "%H:%M")
    e = dt.datetime.strptime(ed, "%H:%M")
    if e <= s:
        e += dt.timedelta(days=1)
    slots: list[str] = []
    while s < e:
        slots.append(s.strftime("%H:%M"))
        s += dt.timedelta(minutes=SLOT_MINUTES)
    return slots or ["00:00"]

# ───────────────────────────────────────────────────────────────
def load_shift_patterns(xlsx: Path, sheet_name: str = "勤務区分"
                       ) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
    """勤務区分シート → wt_df, code2slots"""
    try:
        raw = pd.read_excel(xlsx, sheet_name=sheet_name, dtype=str).fillna("")
    except Exception as e:
        raise ValueError(f"勤務区分シートが読めません: {e}")

    raw.rename(columns={c: COL_ALIASES.get(c, c) for c in raw.columns}, inplace=True)
    if not {"code", "start", "end"}.issubset(raw.columns):
        raise ValueError("勤務区分シートに code/start/end 列がありません")

    wt_rows, code2slots = [], {}
    for r in raw.itertuples(index=False):
        code = _normalize(r.code)
        st_hm, ed_hm = _to_hhmm(r.start), _to_hhmm(r.end)
        slots = ["00:00"] if not st_hm or not ed_hm else _expand(st_hm, ed_hm)
        wt_rows.append({"code": code, "start": st_hm, "end": ed_hm})
        code2slots[code] = slots

    return pd.DataFrame(wt_rows), code2slots

# ───────────────────────────────────────────────────────────────
def ingest_excel(excel_path: Path, *, shift_sheets: List[str], header_row: int = 2
                ) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    excel_path   : Excel ファイル
    shift_sheets : 「勤務区分」シート以外の実績シート名リスト
    header_row   : “氏名/職種/日付列” が並ぶ行番号 (1-indexed)
    """
    wt_df, code2slots = load_shift_patterns(excel_path)

    records: list[dict] = []
    unknown_codes: set[str] = set()

    for sheet in shift_sheets:
        try:
            df = (pd.read_excel(excel_path, sheet_name=sheet,
                                header=header_row - 1, dtype=str)
                  .fillna(""))
        except Exception as e:
            st.warning(f"[{sheet}] 読み込み失敗: {e}")
            continue

        df.rename(columns={c: SHEET_COL_ALIAS.get(_normalize(c), _normalize(c))
                           for c in df.columns}, inplace=True)

        if not {"staff", "role"}.issubset(df.columns):
            raise ValueError(f"[{sheet}] ‘氏名/職種’ 列が見つかりません")

        date_cols = [c for c in df.columns if c not in ("staff", "role")]

        for _, row in df.iterrows():
            staff = _normalize(row["staff"])
            role  = _normalize(row["role"])

            if staff in DOW_TOKENS or role in DOW_TOKENS or (staff == role == ""):
                continue

            for col in date_cols:
                code = _normalize(row[col])
                if code in ("", "nan", "NaN") or code in DOW_TOKENS:
                    continue
                if code not in code2slots:
                    unknown_codes.add(code)
                    continue

                date_val = pd.to_datetime(col, errors="coerce")
                if pd.isna(date_val):
                    st.warning(f"[{sheet}] 日付列パース失敗: {col}")
                    continue

                for t in code2slots[code]:
                    records.append({
                        "ds": pd.to_datetime(f"{date_val.date()} {t}"),
                        "staff": staff,
                        "role":  role,
                        "code":  code,
                    })

    if unknown_codes:
        raise ValueError(f"勤務区分マスターに無いコード: {sorted(unknown_codes)}")
    if not records:
        raise ValueError("長形式レコードが生成されませんでした – 実績シート確認")

    return pd.DataFrame(records).sort_values("ds").reset_index(drop=True), wt_df

# ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse, sys
    p = argparse.ArgumentParser(description="Shift Excel → long_df / wt_df")
    p.add_argument("xlsx"); p.add_argument("--sheet", nargs="+", required=True)
    p.add_argument("--header", type=int, default=2)
    a = p.parse_args(sys.argv[1:])
    ld, wt = ingest_excel(Path(a.xlsx), shift_sheets=a.sheet, header_row=a.header)
    print(ld.head()); print("---"); print(wt.head())
