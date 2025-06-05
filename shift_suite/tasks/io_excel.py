# shift_suite / tasks / io_excel.py
# v2.7.2 (日付パースを dtype=str 前提のv2.6.3ベースに再々修正 + holiday_type 機能)
# =============================================================================
# (中略：目的、主要修正などは適宜更新)
# =============================================================================

from __future__ import annotations
import datetime as dt
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
import pandas as pd

from ..logger_config import configure_logging

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
        slots = []
        if st_hm and ed_hm:
            slots = _expand(st_hm, ed_hm, slot_minutes=slot_minutes)
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


def ingest_excel(
    excel_path: Path,
    *,
    shift_sheets: List[str],
    header_row: int = 2,
    slot_minutes: int = SLOT_MINUTES,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    wt_df, code2slots = load_shift_patterns(excel_path, slot_minutes=slot_minutes)
    if wt_df.empty:
        log.error("勤務区分情報 (wt_df) が空です。処理を続行できません。")
        raise ValueError("勤務区分情報が読み込めませんでした。")

    records: list[dict] = []
    unknown_codes: set[str] = set()

    for sheet_name_actual in shift_sheets:
        try:
            df_sheet = pd.read_excel(
                excel_path,
                sheet_name=sheet_name_actual,
                header=header_row - 1,
                dtype=str,
            ).fillna("")
            log.info(
                f"シート '{sheet_name_actual}' を読み込みました。Shape: {df_sheet.shape}"
            )
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
        log.debug(
            f"シート '{sheet_name_actual}' の日付列候補: {date_cols_candidate}"
        )

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
                shift_code_raw = row_data.get(
                    col_name_original_str, ""
                )  # ★ キーも文字列
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

                # --- ★ 日付パース処理 (v2.6.3ベースに強化) ---
                date_val_parsed_dt_date: dt.date | None = None

                # pandasがTimestampとして読み込んでいるケースは dtype=str 指定によりほぼなくなるが、
                # 念のため isinstance でのチェックも残す (ただし、このブロックは到達しにくい)
                if isinstance(
                    col_name_original_str, (dt.datetime, pd.Timestamp)
                ):  # 通常ここは通らないはず
                    date_val_parsed_dt_date = (
                        pd.to_datetime(col_name_original_str).normalize().date()
                    )
                    log.debug(
                        f"日付パース (Timestamp直接): {col_name_original_str} -> {date_val_parsed_dt_date}"
                    )
                # 文字列として読み込まれた列名をパースする
                else:
                    col_to_parse = str(
                        col_name_original_str
                    ).strip()  # 明示的に文字列化してstrip

                    # 1. Excelシリアル値風の数値文字列か？ (例: "45689", "45689.0")
                    try:
                        if "." in col_to_parse:
                            serial_val = float(col_to_parse)
                        else:
                            serial_val = int(col_to_parse)

                        if 0 < serial_val < 70000:  # 妥当な範囲
                            date_val_parsed_dt_date = (
                                dt.datetime(1899, 12, 30)
                                + dt.timedelta(days=serial_val)
                            ).date()
                            log.debug(
                                f"日付パース (シリアル風文字列): '{col_to_parse}' -> {date_val_parsed_dt_date}"
                            )
                    except ValueError:  # 数値に変換できない場合は次のステップへ
                        # 2. YYYY-MM-DD[HH:MM:SS] や YYYY/MM/DD[ HH:MM:SS] 形式か？
                        date_part_match = re.match(
                            r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})", col_to_parse
                        )
                        if date_part_match:
                            date_str_to_try = date_part_match.group(1)
                            try:
                                date_val_parsed_dt_date = (
                                    pd.to_datetime(date_str_to_try, errors="raise")
                                    .normalize()
                                    .date()
                                )
                                log.debug(
                                    f"日付パース (YYYY-MM-DD風): '{col_to_parse}' -> '{date_str_to_try}' -> {date_val_parsed_dt_date}"
                                )
                            except (ValueError, TypeError, pd.errors.ParserError):
                                pass  # 次のフォーマットへ

                        if date_val_parsed_dt_date is None:
                            # 3. その他の一般的な日付形式を試す
                            common_formats = [
                                "%Y年%m月%d日",
                                "%m/%d/%Y",
                            ]  # YYYY/MM/DD は上記でカバー
                            parsed_successfully = False
                            for fmt in common_formats:
                                try:
                                    date_val_parsed_dt_date = dt.datetime.strptime(
                                        col_to_parse.split(" ")[0], fmt
                                    ).date()
                                    log.debug(
                                        f"日付パース (strptime fmt='{fmt}'): '{col_to_parse}' -> {date_val_parsed_dt_date}"
                                    )
                                    parsed_successfully = True
                                    break
                                except ValueError:
                                    continue
                            if not parsed_successfully:
                                log.debug(
                                    f"日付列パース最終失敗: 元列名='{col_name_original_str}', 試行文字列='{col_to_parse}'"
                                )
                # --- 日付パース処理ここまで ---

                if date_val_parsed_dt_date is None:
                    if not col_name_original_str.startswith("Unnamed:"):
                        log.warning(
                            f"シート '{sheet_name_actual}' の日付列パースに失敗しました (最終結果None): 元の列名='{col_name_original_str}'"
                        )
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
