from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import pandas as pd

from .data_loader import ShiftDataLoader
from .analyzers import (
    LeaveAnalyzer,
    RestTimeAnalyzer,
    WorkPatternAnalyzer,
    AttendanceBehaviorAnalyzer,
    CombinedScoreCalculator,
    LowStaffLoadAnalyzer,
)


DEF_CHOICES = ["leave", "rest", "work", "attendance", "score", "lowstaff", "all"]


def main(argv: list[str] | None = None) -> list[Path]:
    parser = ArgumentParser("Shift Suite CLI Bridge")
    parser.add_argument("csv", help="CSV file with shift data")
    parser.add_argument("--out", default="out", help="Output directory")
    parser.add_argument(
        "--analysis",
        choices=DEF_CHOICES,
        default="leave",
        help="Type of analysis to run",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.25,
        help="Threshold for low staff load. If 0<value<1, treated as quantile",
    )
    args = parser.parse_args(argv)

    loader = ShiftDataLoader(args.csv)
    df = loader.load()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[Path] = []

    if args.analysis in ("leave", "all"):
        leave_res = LeaveAnalyzer().analyze(df)
        fp = out_dir / "leave_analysis.csv"
        leave_res.to_csv(fp, index=False)
        print(f"Results saved to {fp}")
        results.append(fp)

    if args.analysis in ("rest", "score", "all"):
        rta = RestTimeAnalyzer()
        rest_res = rta.analyze(df)
        fp = out_dir / "rest_time.csv"
        rest_res.to_csv(fp, index=False)
        print(f"Results saved to {fp}")
        results.append(fp)

        monthly_rest = rta.monthly(rest_res)
        if not monthly_rest.empty:
            fp_m = out_dir / "rest_time_monthly.csv"
            monthly_rest.to_csv(fp_m, index=False)
            print(f"Results saved to {fp_m}")
            results.append(fp_m)
    else:
        rest_res = None

    if args.analysis in ("work", "score", "all"):
        wpa = WorkPatternAnalyzer()
        work_res = wpa.analyze(df)
        fp = out_dir / "work_patterns.csv"
        work_res.to_csv(fp, index=False)
        print(f"Results saved to {fp}")
        results.append(fp)

        monthly_work = wpa.analyze_monthly(df)
        if not monthly_work.empty:
            fp_m = out_dir / "work_pattern_monthly.csv"
            monthly_work.to_csv(fp_m, index=False)
            print(f"Results saved to {fp_m}")
            results.append(fp_m)
    else:
        work_res = None

    if args.analysis in ("attendance", "score", "all"):
        attend_res = AttendanceBehaviorAnalyzer().analyze(df)
        fp = out_dir / "attendance.csv"
        attend_res.to_csv(fp, index=False)
        print(f"Results saved to {fp}")
        results.append(fp)
    else:
        attend_res = None

    if args.analysis in ("lowstaff", "all"):
        low_res = LowStaffLoadAnalyzer().analyze(df, threshold=args.threshold)
        fp = out_dir / "low_staff_load.csv"
        low_res.to_csv(fp, index=False)
        print(f"Results saved to {fp}")
        results.append(fp)

    if args.analysis in ("score", "all"):
        score_res = CombinedScoreCalculator().calculate(
            rest_res if rest_res is not None else pd.DataFrame(),
            work_res if work_res is not None else pd.DataFrame(),
            attend_res if attend_res is not None else pd.DataFrame(),
        )
        fp = out_dir / "combined_score.csv"
        score_res.to_csv(fp, index=False)
        print(f"Results saved to {fp}")
        results.append(fp)

    return results


if __name__ == "__main__":
    main()
