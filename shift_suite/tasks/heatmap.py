# heatmap.py — ヒートマップ＋summary5生成版

from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from .utils import (
    derive_min_staff, derive_max_staff,
    excel_date, to_hhmm, gen_labels,
    safe_sheet, save_df_xlsx, write_meta, log
)
from .io_excel import default_slots

def _time_rng(start: str, end: str, slot: int) -> list[str]:
    """
    Generate list of time labels between start and end at slot-minute intervals.
    Handles overnight spans.
    """
    fmt = "%H:%M"
    s = pd.to_datetime(start, fmt)
    e = pd.to_datetime(end, fmt)
    if e <= s:
        e += pd.Timedelta(days=1)
    times = []
    while s < e:
        times.append(s.strftime(fmt))
        s += pd.Timedelta(minutes=slot)
    return times

def build_heatmap(
    long_df: pd.DataFrame,
    wt_df: pd.DataFrame,
    out_dir: str | Path,
    slot_minutes: int = 30,
    min_method: str = 'p25',
    max_method: str = 'p75',
) -> None:
    """
    Generate heatmap Excel and CSV outputs.

    Parameters:
    - long_df: DataFrame with ['date','code','role'] in long format.
    - wt_df: Master DataFrame ['code','start','end'].
    - out_dir: Directory path to save outputs.
    - slot_minutes: Slot interval in minutes.
    - min_method: derive_min_staff method.
    - max_method: derive_max_staff method.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) code→time slots mapping
    c2rng: dict[str, list[str]] = {}
    for r in wt_df.itertuples(index=False):
        code = str(r.code)
        st = to_hhmm(r.start)
        ed = to_hhmm(r.end)
        
        if st and ed:
            c2rng[code] = _time_rng(st, ed, slot_minutes)
        elif code in default_slots:
            log.info(f"Using default slots for code={code}")
            c2rng[code] = default_slots[code]
        elif code.startswith('日') and '日' in default_slots:
            log.info(f"Using default day slots for code={code}")
            c2rng[code] = default_slots['日']
        elif code.startswith('夜') and '夜' in default_slots:
            log.info(f"Using default night slots for code={code}")
            c2rng[code] = default_slots['夜']
        elif (code == '公休' or code == '有休' or code == '午前休' or 
              code == '午後休' or code == '欠勤' or code == '週休') and '休' in default_slots:
            log.info(f"Using default rest slots for code={code}")
            c2rng[code] = default_slots['休']
        else:
            log.warning(f"Time parse failed for code={code}, using default slot")
            c2rng[code] = ['00:00']

    # 2) validate codes
    df_codes = set(long_df['code'].dropna().unique())
    common = df_codes & set(c2rng.keys())
    if not common:
        raise ValueError(f"No matching codes: long_df {sorted(df_codes)[:5]} wt_df {sorted(c2rng.keys())[:5]}")

    # 3) expand records
    rows: list[dict] = []
    for r in long_df.itertuples(index=False):
        rng = c2rng.get(r.code, [])
        if not rng:
            log.warning(f"No slots for code={r.code}")
            continue
        for t in rng:
            rows.append({'time': t, 'date': r.date, 'role': r.role or 'Unknown'})

    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("No heatmap data generated; check inputs")

    # 4) format date labels
    df['date_w'] = df['date'].dt.strftime("%-m/%-d")
    time_labels = gen_labels(slot_minutes)

    # 5) ALL pivot
    base = (
        df.pivot_table(index='time', columns='date_w', values='role', aggfunc='count')
        .reindex(time_labels)
        .fillna(0)
    )
    
    need_series = derive_min_staff(base, method=min_method)
    base['need'] = need_series
    
    save_df_xlsx(base, out_dir / 'heat_ALL.xlsx', sheet='ALL')

    date_cols = list(base.columns)

    # 6) Role pivot
    for role in sorted([r for r in df['role'].unique() if pd.notna(r)]):
        sub = df[df['role'] == role]
        heat = (
            sub.pivot_table(index='time', columns='date_w', values='role', aggfunc='count')
            .reindex(time_labels)
            .reindex(columns=date_cols)
            .fillna(0)
        )
        fname = out_dir / f"heat_{safe_sheet(role)}.xlsx"
        save_df_xlsx(heat, fname, sheet=role)

    # 7) min/max staff
    for role in ['ALL'] + sorted([r for r in df['role'].unique() if pd.notna(r)]):
        if role == 'ALL':
            data = base
        else:
            data = pd.read_excel(out_dir / f"heat_{safe_sheet(role)}.xlsx", index_col=0)
        series = data.sum(axis=1)
        mins = derive_min_staff(series, method=min_method)
        maxs = derive_max_staff(series, method=max_method)
        pd.DataFrame({'min_staff': mins}).to_csv(out_dir / f"min_{safe_sheet(role)}.csv")
        pd.DataFrame({'max_staff': maxs}).to_csv(out_dir / f"max_{safe_sheet(role)}.csv")

    # 8) write meta
    meta = {'slot': slot_minutes, 'dates': date_cols, 'roles': sorted([r for r in df['role'].unique() if pd.notna(r)])}
    write_meta(out_dir, **meta)
