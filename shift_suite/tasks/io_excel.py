# io_excel.py — Excel シフト表の読み込みと長形式変換

import re
from pathlib import Path
import logging

import pandas as pd
from openpyxl import load_workbook

from .utils import excel_date, to_hhmm

logger = logging.getLogger("[INGEST]")

def ingest_excel(
    path_or_buffer: str | Path,
    *,
    shift_sheets: list[str],
    master_sheet: str,
    header_row: int = 3
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Excelファイルを読み込み、
      - long_df: {'time','date','role'} の長形式 DataFrame
      - wt_df: 勤務区分マスター (code, start, end) DataFrame
    を返します。

    パラメータ:
      - shift_sheets: 解析対象のシフトシート名リスト
      - master_sheet : 勤務区分マスターシート名
      - header_row   : 実データにおけるヘッダー開始行 (1-indexed)
    """
    logger.info(f"開始: {path_or_buffer}")
    xls = pd.ExcelFile(path_or_buffer, engine="openpyxl")
    logger.info(f"シート一覧: {xls.sheet_names}")

    # 1) マスター読み込み
    wt_df = pd.read_excel(xls, master_sheet, engine="openpyxl")
    for col in ("code", "start", "end"):
        if col not in wt_df.columns:
            raise ValueError(f"マスターシートに必須列 '{col}' がありません")
    logger.info(f"マスターDF サイズ: {wt_df.shape}")

    # 2) コード→時刻スロット辞書
    code2rng: dict[str, list[str]] = {}
    for r in wt_df.itertuples(index=False):
        code = str(r.code)
        st_str = to_hhmm(r.start); ed_str = to_hhmm(r.end)
        slots: list[str] = []
        if st_str and ed_str:
            s = pd.to_datetime(st_str, "%H:%M")
            e = pd.to_datetime(ed_str, "%H:%M")
            if e <= s:
                e += pd.Timedelta(days=1)
            while s < e:
                slots.append(s.strftime("%H:%M"))
                s += pd.Timedelta(minutes=30)
        code2rng[code] = slots
    logger.info(f"コード→スロット マッピング数: {len(code2rng)}")

    all_rows = []
    missing_codes = set()

    # 3) 各シフトシート処理
    for sheet in shift_sheets:
        logger.info(f"--- シート処理開始: {sheet} ---")
        df = pd.read_excel(
            xls,
            sheet,
            header=header_row - 1,
            engine="openpyxl"
        )
        logger.info(f"[{sheet}] 読込DF サイズ: {df.shape}")

        # 固定列チェック
        for req in ("氏名", "職種"):
            if req not in df.columns:
                raise ValueError(f"シート '{sheet}' に必須列 '{req}' が見つかりません")

        # 日付列は '氏名','職種' 以外すべて
        date_cols = [c for c in df.columns if c not in ("氏名", "職種")]

        if not date_cols:
            raise ValueError(f"シート'{sheet}'に日付列が見つかりません")

        # レコード展開
        for _, row in df.iterrows():
            role = row["職種"]
            for c in date_cols:
                code = row[c]
                if pd.isna(code):
                    continue
                code = str(code).strip()
                if code not in code2rng:
                    missing_codes.add(code)
                    continue
                # ヘッダ c を日付に変換
                if isinstance(c, (int, float)):
                    dt_val = excel_date(c)
                else:
                    text = re.sub(r"\s*\(.*\)$", "", str(c))
                    dt_val = pd.to_datetime(text, errors="coerce")
                if pd.isna(dt_val):
                    logger.warning(f"[{sheet}] 日付パース失敗 '{c}'")
                    continue
                for t in code2rng[code]:
                    all_rows.append({
                        "date": dt_val,
                        "time": t,
                        "role": role,
                    })

    if missing_codes:
        logger.warning(f"未登録コード: {sorted(missing_codes)}")

    if not all_rows:
        raise ValueError("長形式レコードが生成されませんでした")

    long_df = pd.DataFrame(all_rows)
    return long_df, wt_df
