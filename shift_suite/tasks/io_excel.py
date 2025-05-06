# io_excel.py — Excel シフト表の読み込みと長形式変換

import re
import datetime
from pathlib import Path
import logging

import pandas as pd
from openpyxl import load_workbook

from .utils import excel_date, to_hhmm

logger = logging.getLogger("[INGEST]")

default_slots = {
    '日': ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30', 
           '13:00', '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00'],
    '夜': ['17:00', '17:30', '18:00', '18:30', '19:00', '19:30', '20:00', '20:30', 
           '21:00', '21:30', '22:00', '22:30', '23:00', '23:30', '00:00', '00:30', '01:00'],
    '休': ['00:00'],  # 休日は実質的に勤務なしだが、レコード生成のために1つのスロットを設定
    '週休': ['00:00'],  # 週休も同様
    '介': ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30', 
           '13:00', '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00'],
    '遅10': ['10:00', '10:30', '11:00', '11:30', '12:00', '12:30', 
            '13:00', '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30', '18:00']
}

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
        elif code in default_slots:
            slots = default_slots[code]
        elif code.startswith('日') and '日' in default_slots:
            slots = default_slots['日']
        elif code.startswith('夜') and '夜' in default_slots:
            slots = default_slots['夜']
        elif (code == '公休' or code == '有休' or code == '午前休' or 
              code == '午後休' or code == '欠勤') and '休' in default_slots:
            slots = default_slots['休']
        else:
            slots = ['00:00']  # 最低1つのスロットを設定してレコードが生成されるようにする
            
        code2rng[code] = slots
    logger.info(f"コード→スロット マッピング数: {len(code2rng)}")
    logger.info(f"マスターコード一覧: {list(code2rng.keys())}")

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

        if len(df.columns) < 2:
            raise ValueError(f"シート '{sheet}' に必要な列数がありません（最低2列必要）")
            
        name_col = df.columns[0]
        role_col = df.columns[1]
        logger.info(f"[{sheet}] 氏名列として使用: '{name_col}'")
        logger.info(f"[{sheet}] 職種列として使用: '{role_col}'")
        
        col_map = {
            "氏名": name_col,
            "職種": role_col
        }

        date_cols = [c for c in df.columns if c not in (name_col, role_col)]

        if not date_cols:
            raise ValueError(f"シート'{sheet}'に日付列が見つかりません")

        # レコード展開
        for _, row in df.iterrows():
            role = row[role_col]  # 職種列を使用
            name = row[name_col]  # 氏名列を使用
            for c in date_cols:
                code = row[c]
                if pd.isna(code):
                    continue
                code = str(code).strip()
                logger.info(f"[{sheet}] 処理中のコード: '{code}' (列: '{c}', 行: '{row[name_col]}')")
                
                original_code = code
                
                if code == '日' or code.startswith('日') or code == '日勤':
                    if '日' in code2rng:
                        code = '日'
                    elif '日勤' in code2rng:
                        code = '日勤'
                
                elif code == '夜' or code.startswith('夜') or code == '夜勤':
                    if '夜' in code2rng:
                        code = '夜'
                    elif '夜勤' in code2rng:
                        code = '夜勤'
                
                elif code == '休' or code == '週休' or code.startswith('休') or code == '公休':
                    if '休' in code2rng:
                        code = '休'
                    elif '公休' in code2rng:
                        code = '公休'
                
                if code != original_code:
                    logger.info(f"[{sheet}] コードマッピング: '{original_code}' → '{code}'")
                
                if code not in code2rng:
                    missing_codes.add(code)
                    logger.warning(f"[{sheet}] 未登録コード: '{code}' (列: '{c}', 行: '{row[name_col]}')")
                    continue
                # ヘッダ c を日付に変換
                try:
                    if sheet.startswith("R"):
                        month_match = re.search(r'R(\d+)\.(\d+)', sheet)
                        if month_match:
                            year_num = int(month_match.group(1))
                            month_num = int(month_match.group(2))
                            year = 2018 + year_num  # R7.x → 2025年
                            month = month_num       # R7.3 → 3月
                            
                            date_cols_list = list(date_cols)
                            col_idx = date_cols_list.index(c)
                            
                            day = col_idx + 1
                            
                            if 1 <= day <= 31:
                                dt_val = datetime.datetime(year, month, day)
                                logger.info(f"[{sheet}] 日付推測成功: {dt_val.strftime('%Y-%m-%d')} (列: '{c}')")
                            else:
                                day_match = re.search(r'(\d+)', str(c))
                                if day_match:
                                    day = int(day_match.group(1))
                                    if 1 <= day <= 31:
                                        dt_val = datetime.datetime(year, month, day)
                                        logger.info(f"[{sheet}] 日付名から推測: {dt_val.strftime('%Y-%m-%d')} (列: '{c}')")
                                    else:
                                        logger.warning(f"[{sheet}] 日付推測失敗: 無効な日 {day}")
                                        continue
                                else:
                                    logger.warning(f"[{sheet}] 日付推測失敗: 日付情報なし '{c}'")
                                    continue
                        else:
                            logger.warning(f"[{sheet}] シート名から年月を推測できません: {sheet}")
                            continue
                    else:
                        if isinstance(c, (int, float)):
                            dt_val = excel_date(c)
                        else:
                            text = re.sub(r"\s*\(.*\)$", "", str(c))
                            dt_val = pd.to_datetime(text, errors="coerce")
                        
                        if pd.isna(dt_val):
                            logger.warning(f"[{sheet}] 日付パース失敗: '{c}'")
                            continue
                except Exception as e:
                    logger.warning(f"[{sheet}] 日付取得エラー: {e}")
                    continue
                slots = code2rng[code]
                logger.info(f"[{sheet}] レコード追加: コード '{code}', 日付 {dt_val.strftime('%Y-%m-%d')}, スロット数 {len(slots)}")
                
                for t in slots:
                    record = {
                        "date": dt_val,
                        "time": t,
                        "role": role,
                        "name": name,
                        "code": code,  # 元のコードも保存
                    }
                    all_rows.append(record)

    if missing_codes:
        logger.warning(f"未登録コード: {sorted(missing_codes)}")

    if not all_rows:
        raise ValueError("長形式レコードが生成されませんでした")

    long_df = pd.DataFrame(all_rows)
    
    used_codes = set(long_df['code'].unique())
    existing_codes = set(wt_df['code'].astype(str))
    missing_from_master = used_codes - existing_codes
    
    if missing_from_master:
        logger.info(f"マスターに追加するコード: {sorted(missing_from_master)}")
        new_rows = []
        for code in missing_from_master:
            if code in default_slots:
                slots = default_slots[code]
                if len(slots) > 1:
                    start_time = pd.to_datetime(slots[0], format='%H:%M')
                    end_time = pd.to_datetime(slots[-1], format='%H:%M')
                    if end_time <= start_time:  # 日をまたぐ場合
                        end_time += pd.Timedelta(days=1)
                    end_time += pd.Timedelta(minutes=30)  # 最後のスロットの終了時刻
                    new_rows.append({
                        'code': code,
                        'start': start_time.strftime('%H:%M'),
                        'end': end_time.strftime('%H:%M')
                    })
                else:
                    new_rows.append({
                        'code': code,
                        'start': None,
                        'end': None
                    })
            else:
                new_rows.append({
                    'code': code,
                    'start': None,
                    'end': None
                })
        
        new_df = pd.DataFrame(new_rows)
        wt_df = pd.concat([wt_df, new_df], ignore_index=True)
        logger.info(f"更新後のマスターDF サイズ: {wt_df.shape}")
    
    return long_df, wt_df
