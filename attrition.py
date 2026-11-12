from __future__ import annotations
from typing import Sequence
import pandas as pd

REQUIRED_COLUMNS = ["employee_id", "hire_date",
                    "termination_date", "termination_type"]
VALID_TERM_TYPES = {"Voluntary", "Involuntary", "Retirement"}


# ---------- Layer 1: loading and cleaning ----------
def load_roster(path: str) -> tuple[pd.DataFrame, list[str]]:
    """Read a roster CSV without altering the source file. Returns (clean_df, issues)."""
    raw = pd.read_csv(
        path, dtype=str)           # read everything as text first, so nothing is silently coerced
    missing = [c for c in REQUIRED_COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError(f"Roster is missing required columns: {missing}")

    df = raw.copy()
    df = df.apply(lambda s: s.str.strip() if s.dtype == "object" else s)
    df = df.replace("", pd.NA)

    issues: list[str] = []
    for col in ("hire_date", "termination_date"):
        parsed = pd.to_datetime(df[col], errors="coerce")
        bad = df[col].notna() & parsed.isna()
        if bad.any():
            issues.append(
                f"{bad.sum()} unparseable {col} value(s): {df.loc[bad, 'employee_id'].tolist()}")
        df[col] = parsed

    df["termination_type"] = df["termination_type"].str.title()
    bad_type = df["termination_date"].notna(
    ) & ~df["termination_type"].isin(VALID_TERM_TYPES)
    if bad_type.any():
        issues.append(f"{bad_type.sum()} terminated employee(s) with missing/unknown termination_type: "
                      f"{df.loc[bad_type, 'employee_id'].tolist()}")

    if df["employee_id"].duplicated().any():
        issues.append(
            f"Duplicate employee_id(s): {df.loc[df['employee_id'].duplicated(), 'employee_id'].tolist()}")
    if df["hire_date"].isna().any():
        issues.append(
            f"{df['hire_date'].isna().sum()} row(s) with no hire_date")
    before_hire = df["termination_date"] < df["hire_date"]
    if before_hire.any():
        issues.append(
            f"Terminated before hired: {df.loc[before_hire, 'employee_id'].tolist()}")
    return df, issues


# ---------- Layer 2: metrics (pure functions) ----------
def headcount_start(df: pd.DataFrame, day) -> int:
    day = pd.Timestamp(day)
    return int(((df["hire_date"] < day) &
                (df["termination_date"].isna() | (df["termination_date"] >= day))).sum())


def headcount_end(df: pd.DataFrame, day) -> int:
    day = pd.Timestamp(day)
    return int(((df["hire_date"] <= day) &
                (df["termination_date"].isna() | (df["termination_date"] > day))).sum())


def monthly_table(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """One row per month: start/end/avg headcount and terminations (total, voluntary, involuntary)."""
    rows = []
    for ms in pd.date_range(f"{year}-01-01", f"{year}-12-01", freq="MS"):
        me = ms + pd.offsets.MonthEnd(0)
        left = df[df["termination_date"].between(ms, me)]
        s, e = headcount_start(df, ms), headcount_end(df, me)
        rows.append({"month": ms.strftime("%Y-%m"), "start_hc": s, "end_hc": e, "avg_hc": (s + e) / 2,
                     "terminations": len(left),
                     "voluntary": int((left["termination_type"] == "Voluntary").sum()),
                     "involuntary": int((left["termination_type"] == "Involuntary").sum())})
    return pd.DataFrame(rows)


def attrition_rate(terminations: Sequence[int], avg_headcounts: Sequence[float]) -> float:
    """
    Attrition % = total terminations / mean of the average headcounts * 100.
    Both sequences must cover the same periods (e.g. 12 months). Raises ValueError otherwise.
    Returns an unrounded float; round only when displaying.
    """
    if len(terminations) != len(avg_headcounts):
        raise ValueError(
            f"Length mismatch: {len(terminations)} termination values vs {len(avg_headcounts)} headcount values")
    if len(terminations) == 0:
        raise ValueError("No data supplied")
    mean_hc = sum(avg_headcounts) / len(avg_headcounts)
    if mean_hc == 0:
        raise ValueError("Average headcount is zero; rate is undefined")
    return sum(terminations) / mean_hc * 100


# ---------- Layer 3: questions ----------
def summarize_year(df: pd.DataFrame, year: int, **filters) -> dict:
    """e.g. summarize_year(df, 2024, department="IT", state="UT")"""
    for col, val in filters.items():
        df = df[df[col] == val]
    t = monthly_table(df, year)
    return {"year": year, "filters": filters, "months": len(t),
            "terminations": int(t["terminations"].sum()), "avg_headcount": round(t["avg_hc"].mean(), 2),
            "total_rate": attrition_rate(t["terminations"], t["avg_hc"]),
            "voluntary_rate": attrition_rate(t["voluntary"], t["avg_hc"]),
            "involuntary_rate": attrition_rate(t["involuntary"], t["avg_hc"])}


def format_rate(summary: dict) -> str:
    f = ", ".join(f"{k}={v}" for k,
                  v in summary["filters"].items()) or "all employees"
    return f"{summary['year']} ({f}): {summary['total_rate']:.2f}% total, " \
        f"{summary['voluntary_rate']:.2f}% voluntary, {summary['involuntary_rate']:.2f}% involuntary"
