"""cli.py – コマンドライン一括実行"""

import sys
from pathlib import Path
# Add project root to the Python path to allow direct execution
sys.path.insert(0, str(Path(__file__).parent))

import argparse
import logging
import shutil
from pathlib import Path

import pandas as pd

from shift_suite import build_heatmap, ingest_excel, shortage_and_brief, summary
from shift_suite.tasks.h2hire import build_hire_plan as build_hire_plan_from_shortage
from shift_suite.tasks.cost_benefit import analyze_cost_benefit
from shift_suite.tasks.utils import safe_make_archive
from shift_suite.tasks.report_generator import generate_summary_report

log = logging.getLogger(__name__)


def main():
    ap = argparse.ArgumentParser("shift‑suite CLI")
    ap.add_argument("excel")
    ap.add_argument("out")
    ap.add_argument("--slot", type=int, default=30)
    ap.add_argument(
        "--header",
        type=int,
        default=2,
        help="Header row number of shift sheets (1-indexed)",
    )
    ap.add_argument("--zip", action="store_true")
    ap.add_argument("--holidays-global", help="Global holiday CSV or JSON file")
    ap.add_argument("--holidays-local", help="Local holiday CSV or JSON file")
    ap.add_argument(
        "--safety-factor",
        type=float,
        default=1.0,
        help="Multiplier applied to shortage hours when converting to hires",
    )
    ap.add_argument("--ymcell", type=str, help="Year-month cell location (e.g., A1)")
    args = ap.parse_args()

    excel = Path(args.excel).expanduser()
    out = Path(args.out).expanduser()
    holiday_dates_global = None
    holiday_dates_local = None

    def _read_holiday_file(fp: Path):
        if fp.suffix.lower() == ".json":
            import json

            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            return (
                [pd.to_datetime(d).date() for d in data]
                if isinstance(data, list)
                else None
            )
        df_h = pd.read_csv(fp, header=None)
        return [pd.to_datetime(x).date() for x in df_h.iloc[:, 0].dropna().unique()]

    if args.holidays_global:
        fp_hg = Path(args.holidays_global).expanduser()
        try:
            holiday_dates_global = _read_holiday_file(fp_hg)
        except Exception as e:
            log.error("Failed to read holidays from %s: %s", fp_hg, e)

    if args.holidays_local:
        fp_hl = Path(args.holidays_local).expanduser()
        try:
            holiday_dates_local = _read_holiday_file(fp_hl)
        except Exception as e:
            log.error("Failed to read holidays from %s: %s", fp_hl, e)
    shutil.rmtree(out, ignore_errors=True)

    # Determine shift sheet names by excluding the master sheet
    xls = pd.ExcelFile(excel)
    shift_sheets = [s for s in xls.sheet_names if "勤務区分" not in s]

    long, _, unknown_codes = ingest_excel(
        excel,
        shift_sheets=shift_sheets,
        header_row=args.header,
        slot_minutes=args.slot,
        year_month_cell_location=args.ymcell,
    )
    if unknown_codes:
        log.warning("Unknown shift codes found: %s", sorted(unknown_codes))

    ref_start = pd.to_datetime(long["ds"]).dt.date.min()
    ref_end = pd.to_datetime(long["ds"]).dt.date.max()

    build_heatmap(
        long,
        out,
        args.slot,
        include_zero_days=True,
        ref_start_date_for_need=ref_start,
        ref_end_date_for_need=ref_end,
        need_statistic_method="中央値",
        need_remove_outliers=True,
        need_adjustment_factor=1.0,
        need_iqr_multiplier=1.5,
        min_method="p25",
        max_method="p75",
    )
    shortage_and_brief(
        out,
        args.slot,
        holidays=(holiday_dates_global or []) + (holiday_dates_local or []),
        include_zero_days=True,
    )
    try:
        build_hire_plan_from_shortage(out, safety_factor=args.safety_factor)
    except Exception as e:
        log.error("hire_plan generation failed: %s", e)
    else:
        try:
            analyze_cost_benefit(out)
        except Exception as e:
            log.error("cost-benefit analysis failed: %s", e)
    summary.build_staff_stats(long, out)

    try:
        generate_summary_report(out)
    except Exception as e:
        log.error("summary report generation failed: %s", e)

    if args.zip:
        safe_make_archive(out, out.with_suffix(".zip"))

    log.info("✔ CLI done → %s", out)


if __name__ == "__main__":
    main()
