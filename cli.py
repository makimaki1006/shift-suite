"""cli.py – コマンドライン一括実行"""
import argparse, shutil
from pathlib import Path
import pandas as pd
from shift_suite import ingest_excel, build_heatmap, shortage_and_brief, summary
from shift_suite.h2hire import build_hire_plan as build_hire_plan_from_shortage
from shift_suite.tasks.cost_benefit import analyze_cost_benefit
from shift_suite.utils import safe_make_archive

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
    ap.add_argument("--holidays", help="Optional holiday CSV or JSON file")
    args = ap.parse_args()

    excel = Path(args.excel).expanduser()
    out   = Path(args.out).expanduser()
    holiday_dates = None
    if args.holidays:
        fp_h = Path(args.holidays).expanduser()
        try:
            if fp_h.suffix.lower() == ".json":
                import json
                with open(fp_h, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    holiday_dates = [pd.to_datetime(d).date() for d in data]
            else:
                df_h = pd.read_csv(fp_h, header=None)
                holiday_dates = [pd.to_datetime(x).date() for x in df_h.iloc[:,0].dropna().unique()]
        except Exception as e:
            print(f"Failed to read holidays from {fp_h}: {e}")
    shutil.rmtree(out, ignore_errors=True)

    # Determine shift sheet names by excluding the master sheet
    xls = pd.ExcelFile(excel)
    shift_sheets = [s for s in xls.sheet_names if "勤務区分" not in s]

    long, _ = ingest_excel(
        excel,
        shift_sheets=shift_sheets,
        header_row=args.header,
    )

    ref_start = pd.to_datetime(long["ds"]).dt.date.min()
    ref_end = pd.to_datetime(long["ds"]).dt.date.max()

    build_heatmap(
        long,
        out,
        args.slot,
        ref_start_date_for_need=ref_start,
        ref_end_date_for_need=ref_end,
        need_statistic_method="中央値",
        need_remove_outliers=True,
        need_iqr_multiplier=1.5,
        min_method="p25",
        max_method="p75",
    )
    shortage_and_brief(out, args.slot, holidays=holiday_dates)
    try:
        build_hire_plan_from_shortage(out)
    except Exception as e:
        print(f"hire_plan generation failed: {e}")
    else:
        try:
            analyze_cost_benefit(out)
        except Exception as e:
            print(f"cost-benefit analysis failed: {e}")
    summary.build_staff_stats(long, out)

    if args.zip:
        safe_make_archive(out, out.with_suffix(".zip"))

    print("✔ CLI done →", out)

if __name__ == "__main__":
    main()
