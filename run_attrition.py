"""Command-line runner for attrition.py.

Examples:
  python run_attrition.py --years 2024
  python run_attrition.py --years 2023 2024 2025 --department IT
  python run_attrition.py --years 2024 --state UT --employment-type Part-time --monthly
  python run_attrition.py --years 2023 2024 --export report.pdf --monthly
"""
import argparse
from pathlib import Path
import attrition as a
import exporters


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Calculate attrition rates from an employee roster CSV.")
    p.add_argument("--file", default="employee_roster.csv",
                   help="path to roster CSV (default: employee_roster.csv)")
    p.add_argument("--years", type=int, nargs="+", required=True,
                   help="one or more years, e.g. --years 2023 2024")
    p.add_argument("--department", help="only include this department")
    p.add_argument("--state", help="only include this state")
    p.add_argument("--employment-type", dest="employment_type",
                   help="e.g. Full-time or Part-time")
    p.add_argument("--monthly", action="store_true",
                   help="also show the month-by-month table")
    p.add_argument("--export", metavar="PATH",
                   help="save results to a .csv or .pdf file (type chosen by extension)")
    p.add_argument("--overwrite", action="store_true",
                   help="allow --export to replace an existing file")
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    export_path = Path(args.export) if args.export else None
    if export_path:
        if export_path.suffix.lower() not in (".csv", ".pdf"):
            parser.error("--export file must end in .csv or .pdf")
        if export_path.exists() and not args.overwrite:
            parser.error(
                f"{export_path} already exists. Choose another name or add --overwrite")

    try:
        df, issues = a.load_roster(args.file)
    except FileNotFoundError:
        parser.error(f"Could not find roster file: {args.file}")

    if issues:
        print("Data problems found:")
        for problem in issues:
            print(" -", problem)
        print()

    # Collect only the filters the user actually supplied
    filters = {k: v for k, v in {"department": args.department, "state": args.state,
                                 "employment_type": args.employment_type}.items() if v}
    for col, val in filters.items():
        if col not in df.columns:
            parser.error(f"Roster has no '{col}' column")
        if val not in set(df[col].dropna()):
            parser.error(
                f"No '{val}' in {col}. Valid values: {sorted(df[col].dropna().unique())}")

    # Apply the filters once, up front, so every year and the monthly table use the same data
    subset = df
    for col, val in filters.items():
        subset = subset[subset[col] == val]

    summaries, monthly = [], {}
    for year in args.years:
        summary = a.summarize_year(df, year, **filters)
        summaries.append(summary)
        print(a.format_rate(summary))
        if args.monthly:
            monthly[year] = a.monthly_table(subset, year)
        if args.monthly:
            print(monthly[year].to_string(index=False))
            print()

    if export_path:
        writer = exporters.export_pdf if export_path.suffix.lower(
        ) == ".pdf" else exporters.export_csv
        for written in writer(export_path, summaries, monthly if args.monthly else None):
            print(f"Saved: {written}")


if __name__ == "__main__":
    main()
