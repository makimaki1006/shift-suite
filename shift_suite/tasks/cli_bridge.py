from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

from .data_loader import ShiftDataLoader
from .analyzers import LeaveAnalyzer


def main(argv: list[str] | None = None) -> Path:
    parser = ArgumentParser("Shift Suite CLI Bridge")
    parser.add_argument("csv", help="CSV file with shift data")
    parser.add_argument("--out", default="out", help="Output directory")
    args = parser.parse_args(argv)

    loader = ShiftDataLoader(args.csv)
    df = loader.load()

    analyzer = LeaveAnalyzer()
    result = analyzer.analyze(df)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_file = out_dir / "leave_analysis.csv"
    result.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")
    return output_file


if __name__ == "__main__":
    main()
