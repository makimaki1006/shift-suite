"""cli.py – コマンドライン一括実行"""
import argparse, shutil
from pathlib import Path
from shift_suite import ingest_excel, build_heatmap, shortage_and_brief, summary
from shift_suite.utils import safe_make_archive

def main():
    ap = argparse.ArgumentParser("shift‑suite CLI")
    ap.add_argument("excel")
    ap.add_argument("out")
    ap.add_argument("--slot", type=int, default=30)
    ap.add_argument("--zip", action="store_true")
    args = ap.parse_args()

    excel = Path(args.excel).expanduser()
    out   = Path(args.out).expanduser()
    shutil.rmtree(out, ignore_errors=True)

    long, wt = ingest_excel(
        excel,
        shift_sheets=None,  # Use all non-master sheets
        master_sheet="勤務区分"  # Default master sheet name
    )
    build_heatmap(long, wt, out, args.slot)
    shortage_and_brief(out, args.slot)
    summary_df = summary.daily_summary(out)
    summary_df.to_csv(out / "summary.csv", index=False)

    if args.zip:
        safe_make_archive(out, out.with_suffix(".zip"))

    print("✔ CLI done →", out)

if __name__ == "__main__":
    main()
