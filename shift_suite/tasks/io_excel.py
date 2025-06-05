# shift_suite / tasks / io_excel.py
# v2.7.2 (日付パースを dtype=str 前提のv2.6.3ベースに再々修正 + holiday_type 機能)
# =============================================================================
# (中略：目的、主要修正などは適宜更新)
# =============================================================================

from __future__ import annotations

import datetime as dt
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from ..logger_config import configure_logging
from .utils import _parse_as_date

configure_logging()
log = logging.getLogger(__name__)


SLOT_MINUTES = 30
COL_ALIASES = {
    "記号": "code",
    "コード": "code",
    "勤務記号": "code",
    "開始": "start",
    "開始時刻": "start",
    "start": "start",
    "終了": "end",
    "終了時刻": "end",
    "end": "end",
    "備考": "remarks",
    "説明": "remarks",
}
SHEET_COL_ALIAS = {
    "氏名": "staff",
    "名前": "staff",
    "staff": "staff",
    "name": "staff",
    "従業員": "staff",
    "member": "staff",
    "職種": "role",
    "部署": "role",
    "役職": "role",
    "role": "role",
    "雇用形態": "employment",
    "employment": "employment",
}
DOW_TOKENS = {"月", "火", "水", "木", "金", "土", "日", "明"}

HOLIDAY_TYPE_KEYWORDS_MAP = {
    "有給": ["有給"],
    "希望休": ["希望休"],
    "その他休暇": ["休暇", "組織休", "施設休", "特休"],
}
DEFAULT_HOLIDAY_TYPE = "通常勤務"


def _normalize(val: Any) -> str:
    txt = str(val).replace("　", " ")
    return re.sub(r"\s+", "", txt).strip()


def _to_hhmm(v: Any) -> str | None:
    # (v2.7.1案のロジックを流用。大きな問題はなさそうなので一旦このまま)
    if pd.isna(v) or v == "":
        return None
    if isinstance(v, (dt.time)):
        return v.strftime("%H:%M")
    if isinstance(v, (dt.datetime, pd.Timestamp)):
        return pd.to_datetime(v).strftime("%H:%M")
    if isinstance(v, (int, float)):
        try:
            if 0 <= float(v) < 1:
                excel_time_as_datetime = dt.datetime(1899, 12, 30) + dt.timedelta(
                    days=float(v)
                )
                return excel_time_as_datetime.strftime("%H:%M")
            else:
                dt_obj = dt.datetime(1899, 12, 30) + dt.timedelta(days=float(v))
                return dt_obj.strftime("%H:%M")
        except Exception as e:
            log.debug(f"Excelシリアル値からの時刻変換エラー: 値='{v}', エラー='{e}'")
            return None
    s = str(v).strip()
    if re.fullmatch(r"\d{1,2}:\d{2}:\d{2}", s):
        s = s[:-3]
    if re.fullmatch(r"\d{1,2}:\d{2}", s):
        try:
            return dt.datetime.strptime(s, "%H:%M").strftime("%H:%M")
        except ValueError:
            return None
    log.debug(f"HH:MM形式への変換失敗: '{v}'")
    return None


def _expand(
    st: str | None, ed: str | None, slot_minutes: int = SLOT_MINUTES
) -> list[str]:
    """Expand start and end time into time slots spaced by ``slot_minutes``."""
    if not st or not ed:
        return []
    try:
        s_time = dt.datetime.strptime(st, "%H:%M")
        e_time = dt.datetime.strptime(ed, "%H:%M")
    except (ValueError, TypeError):
        return []
    if e_time <= s_time:
        e_time += dt.timedelta(days=1)
    slots: list[str] = []
    current_time = s_time
    max_slots = (24 * 60) // slot_minutes + 1
    while current_time < e_time and len(slots) < max_slots:
        slots.append(current_time.strftime("%H:%M"))
        current_time += dt.timedelta(minutes=slot_minutes)
    if len(slots) >= max_slots:
        log.warning(
            f"勤務コード {st}-{ed} のスロット展開が24時間を超えるため制限しました。"
        )
    return slots


def _determine_holiday_type(remarks_str: str) -> str:
    # (v2.7.1案のロジックを流用)
    if pd.isna(remarks_str) or remarks_str == "":
        return DEFAULT_HOLIDAY_TYPE
    for holiday_name, keywords in HOLIDAY_TYPE_KEYWORDS_MAP.items():
        for keyword in keywords:
            if keyword in remarks_str:
                return holiday_name
    return DEFAULT_HOLIDAY_TYPE


def load_shift_patterns(
    xlsx: Path, sheet_name: str = "勤務区分", slot_minutes: int = SLOT_MINUTES
) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
    # (v2.7.1案のロジックを流用)
    log.info(f"勤務区分シート読み込み開始: {sheet_name}")
    try:
        raw = pd.read_excel(xlsx, sheet_name=sheet_name, dtype=str).fillna("")
    except FileNotFoundError as e:
        log.error("Excel file not found: %s", e)
        raise
    except pd.errors.EmptyDataError as e:
        log.error("勤務区分シート '%s' が空です: %s", sheet_name, e)
        raise ValueError(f"勤務区分シート '{sheet_name}' が空です") from e
    except Exception as e:
        log.error(f"勤務区分シート '{sheet_name}' が読めません: {e}")
        raise ValueError(f"勤務区分シート '{sheet_name}' が読めません: {e}") from e
    raw.rename(
        columns={c: COL_ALIASES.get(str(c), str(c)) for c in raw.columns}, inplace=True
    )
    log.info(f"読み込んだ生データ: shape={raw.shape}")
    log.debug(f"列名: {raw.columns.tolist()}")
    log.debug(f"最初の5行:\n{raw.head()}")
    required_cols = {"code", "start", "end"}
    if not required_cols.issubset(raw.columns):
        missing = required_cols - set(raw.columns)
        log.error(f"勤務区分シート '{sheet_name}' に必須列 {missing} がありません")
        raise ValueError(
            f"勤務区分シート '{sheet_name}' に必須列 {missing} がありません"
        )
    wt_rows, code2slots = [], {}
    for r_idx, r in raw.iterrows():
        code = _normalize(r.get("code", ""))
        if not code:
            log.warning(
                f"勤務区分シート '{sheet_name}' の {r_idx + 2}行目: 勤務コードが空のためスキップします。"
            )
            continue
        st_original = r.get("start", "")
        ed_original = r.get("end", "")
        st_hm, ed_hm = _to_hhmm(st_original), _to_hhmm(ed_original)
        log.debug(
            f"処理中の勤務コード: 行{r_idx + 2}, code='{code}', start='{st_original}', end='{ed_original}'"
        )
        log.debug(f"時刻変換結果: {st_original} → {st_hm}, {ed_original} → {ed_hm}")
        slots = []
        if st_hm and ed_hm:
            slots = _expand(st_hm, ed_hm, slot_minutes=slot_minutes)
            log.debug(f"スロット展開: {code} → {len(slots)}個のスロット: {slots}")
        elif st_hm or ed_hm:
            log.warning(
                f"勤務コード '{code}': 開始/終了の一方のみ指定。スロット0扱い (開始='{st_original}', 終了='{ed_original}')"
            )
        remarks_val = r.get("remarks", "")
        holiday_type = _determine_holiday_type(str(remarks_val))
        wt_rows.append(
            {
                "code": code,
                "start_original": st_original,
                "end_original": ed_original,
                "start_parsed": st_hm,
                "end_parsed": ed_hm,
                "parsed_slots_count": len(slots),
                "remarks_original": remarks_val,
                "holiday_type": holiday_type,
            }
        )
        code2slots[code] = slots
    log.info(
        f"勤務区分シート '{sheet_name}' から {len(code2slots)} 件の勤務パターンを読み込みました。"
    )
    return pd.DataFrame(wt_rows), code2slots


def _parse_day_with_year_month(col_name: str, year: int, month: int) -> dt.date | None:
    """Parse column names like '1' or '1(日)' using provided year-month."""
    m = re.match(r"(\d{1,2})", str(col_name).strip())
    if not m:
        return None
    day = int(m.group(1))
    try:
        return dt.date(year, month, day)
    except ValueError:
        return None


def _excel_cell_to_row_col(cell: str) -> tuple[int, int] | None:
    """Convert Excel style cell like 'A1' to 0-based row/column indexes."""
    m = re.match(r"^([A-Za-z]+)(\d+)$", cell.strip())
    if not m:
        return None
    col_txt, row_txt = m.groups()
    col = 0
    for ch in col_txt.upper():
        col = col * 26 + (ord(ch) - 64)
    return int(row_txt) - 1, col - 1


def ingest_excel(
    excel_path: Path,
    *,
    shift_sheets: List[str],
    header_row: int = 2,
    slot_minutes: int = SLOT_MINUTES,
    year_month_cell_location: str | None = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    wt_df, code2slots = load_shift_patterns(excel_path, slot_minutes=slot_minutes)
    if wt_df.empty:
        log.error("勤務区分情報 (wt_df) が空です。処理を続行できません。")
        raise ValueError("勤務区分情報が読み込めませんでした。")

    records: list[dict] = []
    unknown_codes: set[str] = set()
    year_val: int | None = None
    month_val: int | None = None
    if year_month_cell_location:
        try:
            log.info(f"年月セル読み込み試行: セル位置={year_month_cell_location}")
            rc = _excel_cell_to_row_col(year_month_cell_location)
            if rc is None:
                raise ValueError(f"Invalid cell: {year_month_cell_location}")
            row, col = rc
            ym_df = pd.read_excel(
                excel_path,
                sheet_name=shift_sheets[0],
                header=None,
                skiprows=row,
                nrows=1,
                usecols=[col],
                dtype=str,
            )
            ym_raw = str(ym_df.iloc[0, 0])
            log.debug(f"読み込んだ年月セルの生データ: '{ym_raw}'")
            m = re.search(r"(\d{4})年(\d{1,2})月", ym_raw)
            if not m:
                raise ValueError(f"'{ym_raw}' does not match YYYY年MM月 format")
            year_val, month_val = int(m.group(1)), int(m.group(2))
            log.info(f"解析結果: 年={year_val}, 月={month_val}")
        except Exception as e:
            log.error(f"年月セル '{year_month_cell_location}' の読み込み失敗: {e}")
            raise ValueError("年月セルの取得に失敗しました") from e

    for sheet_name_actual in shift_sheets:
        try:
            log.info(f"シート処理開始: {sheet_name_actual}")
            df_sheet = pd.read_excel(
                excel_path,
                sheet_name=sheet_name_actual,
                header=header_row - 1,
                dtype=str,
            ).fillna("")
            log.info(f"シート shape: {df_sheet.shape}")
            log.debug(f"列名マッピング前: {df_sheet.columns.tolist()}")
        except FileNotFoundError as e:
            log.error("Excel file not found while reading sheet '%s': %s", sheet_name_actual, e)
            raise
        except pd.errors.EmptyDataError as e:
            log.warning("シート '%s' が空です: %s", sheet_name_actual, e)
            continue
        except Exception as e:
            log.warning(
                f"シート '{sheet_name_actual}' の読み込みに失敗しました: {e}"
            )
            continue

        df_sheet.columns = [
            SHEET_COL_ALIAS.get(_normalize(str(c)), _normalize(str(c)))
            for c in df_sheet.columns
        ]
        log.debug(f"列名マッピング後: {df_sheet.columns.tolist()}")

        if not {"staff", "role"}.issubset(df_sheet.columns):
            log.error(
                f"シート '{sheet_name_actual}' に ‘staff’ (氏名) または ‘role’ (職種) 列が見つかりません。"
            )
            raise ValueError(
                f"シート '{sheet_name_actual}' に ‘staff’ (氏名) または ‘role’ (職種) 列が見つかりません。"
            )

        date_cols_candidate = [
            c
            for c in df_sheet.columns
            if c not in ("staff", "role", "employment")
            and not str(c).startswith("Unnamed:")
        ]
        if not date_cols_candidate:
            log.warning(
                f"シート '{sheet_name_actual}' に日付データ列が見つかりませんでした。"
            )
            continue
        log.info(
            f"日付列候補: {len(date_cols_candidate)}個 - {date_cols_candidate}"
        )

        date_col_map: Dict[str, dt.date] = {}
        for c in date_cols_candidate:
            parsed_dt: dt.date | None = None
            if year_val is not None and month_val is not None:
                parsed_dt = _parse_day_with_year_month(str(c), year_val, month_val)
                if parsed_dt:
                    date_col_map[str(c)] = parsed_dt
                    continue
                parsed_dt = _parse_as_date(str(c))
            if parsed_dt:
                date_col_map[str(c)] = parsed_dt
            else:
                if not str(c).startswith("Unnamed:"):
                    log.warning(
                        f"シート '{sheet_name_actual}' の日付列パースに失敗しました: 元の列名='{c}'"
                    )

        log.debug(f"日付列マッピング結果: {len(date_col_map)}個成功")
        for col, date in date_col_map.items():
            log.debug(f"  {col} → {date}")

        for _, row_data in df_sheet.iterrows():
            staff = _normalize(row_data.get("staff", ""))
            role = _normalize(row_data.get("role", ""))
            employment = _normalize(row_data.get("employment", ""))

            if (
                staff in DOW_TOKENS
                or role in DOW_TOKENS
                or (staff == "" and role == "")
            ):
                continue

            for col_name_original_str in date_cols_candidate:  # ★ 必ず文字列として扱う
                shift_code_raw = row_data.get(col_name_original_str, "")
                code_val = _normalize(str(shift_code_raw))

                if code_val in ("", "nan", "NaN") or code_val in DOW_TOKENS:
                    continue
                if code_val not in code2slots:
                    if code_val not in unknown_codes:
                        log.warning(
                            f"シート '{sheet_name_actual}', スタッフ '{staff}', 日付列 '{col_name_original_str}' で未知の勤務コード '{code_val}' が見つかりました。"
                        )
                        unknown_codes.add(code_val)
                    continue

                date_val_parsed_dt_date = date_col_map.get(str(col_name_original_str))
                if date_val_parsed_dt_date is None:
                    continue

                current_code_slots_list = code2slots.get(code_val, [])
                wt_row_series = (
                    wt_df[wt_df["code"] == code_val].iloc[0]
                    if not wt_df[wt_df["code"] == code_val].empty
                    else None
                )
                holiday_type_for_record = (
                    wt_row_series["holiday_type"]
                    if wt_row_series is not None
                    else DEFAULT_HOLIDAY_TYPE
                )
                parsed_slots_count_for_record = (
                    wt_row_series["parsed_slots_count"]
                    if wt_row_series is not None
                    else 0
                )

                if not current_code_slots_list:
                    record_datetime_for_zero_slot = dt.datetime.combine(
                        date_val_parsed_dt_date, dt.time(0, 0)
                    )
                    records.append(
                        {
                            "ds": record_datetime_for_zero_slot,
                            "staff": staff,
                            "role": role,
                            "employment": employment,
                            "code": code_val,
                            "holiday_type": holiday_type_for_record,
                            "parsed_slots_count": parsed_slots_count_for_record,
                        }
                    )
                    continue

                for t_slot_val in current_code_slots_list:
                    try:
                        record_datetime = dt.datetime.combine(
                            date_val_parsed_dt_date,
                            dt.datetime.strptime(t_slot_val, "%H:%M").time(),
                        )
                        records.append(
                            {
                                "ds": record_datetime,
                                "staff": staff,
                                "role": role,
                                "employment": employment,
                                "code": code_val,
                                "holiday_type": holiday_type_for_record,
                                "parsed_slots_count": parsed_slots_count_for_record,
                            }
                        )
                    except ValueError as e_time:
                        log.error(
                            f"時刻スロット '{t_slot_val}' のパース中にエラー (スタッフ: {staff}, 日付: {date_val_parsed_dt_date}, コード: {code_val}): {e_time}"
                        )
                        continue

    if unknown_codes:
        log.warning(
            f"処理中に以下の未知の勤務コードが見つかりました (これらは無視されます): {sorted(list(unknown_codes))}"
        )

    if not records:
        log.error(
            "処理対象となる有効なシフトレコードが1件も見つかりませんでした。入力Excelの実績シートの列名（日付形式）、勤務区分、ヘッダー行の設定を確認してください。"
        )
        raise ValueError("有効なシフトレコードが生成されませんでした。")

    log.info(f"合計 {len(records)} 件の長形式レコードを生成しました。")
    final_long_df = pd.DataFrame(records)
    if not final_long_df.empty:
        final_long_df["ds"] = pd.to_datetime(final_long_df["ds"])
        final_long_df = final_long_df.sort_values("ds").reset_index(drop=True)

    return final_long_df, wt_df


# --- CLI use -----------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    configure_logging(level=logging.DEBUG)
    p = argparse.ArgumentParser(description="Shift Excel → long_df / wt_df")
    p.add_argument("xlsx", help="Excel シフト原本 (.xlsx)")
    p.add_argument(
        "--sheets",
        nargs="+",
        required=True,
        help="対象シート名 (「勤務区分」シート以外)",
    )
    p.add_argument("--header", type=int, default=2, help="ヘッダー開始行 (1-indexed)")
    p.add_argument("--slot", type=int, default=SLOT_MINUTES, help="スロット長 (分)")
    p.add_argument("--ymcell", type=str, help="年月情報セル位置 (例: A1)")
    a = p.parse_args()
    try:
        log.info(
            f"Excelファイル: {a.xlsx}, 対象シート: {a.sheets}, ヘッダー行: {a.header}, スロット: {a.slot}"
        )
        ld, wt = ingest_excel(
            Path(a.xlsx),
            shift_sheets=a.sheets,
            header_row=a.header,
            slot_minutes=a.slot,
            year_month_cell_location=a.ymcell,
        )
        log.info("正常に処理が完了しました。")
        if not ld.empty:
            log.info("--- long_df (最初の5行) ---")
            log.info(ld.head())
            log.info(f"long_df columns: {ld.columns.tolist()}")
            log.info(f"long_df dtypes:\n{ld.dtypes}")
        else:
            log.info("--- long_df は空です ---")
        if not wt.empty:
            log.info("--- wt_df (最初の5行) ---")
            log.info(wt.head())
            log.info(f"wt_df columns: {wt.columns.tolist()}")
            log.info(f"wt_df dtypes:\n{wt.dtypes}")
        else:
            log.info("--- wt_df は空です ---")
    except ValueError as e:
        log.error(f"処理中にエラーが発生しました: {e}")
    except FileNotFoundError as e:
        log.error(f"ファイルが見つかりません: {e}")
    except Exception as e:
        log.error(f"予期せぬエラーが発生しました: {e}", exc_info=True)
