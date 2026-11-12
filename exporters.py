"""Output layer: turn results into files. Knows nothing about how rates are calculated."""
from __future__ import annotations
from datetime import date
from pathlib import Path
import pandas as pd

METHOD_NOTE = ("Method: attrition % = total terminations in the year / mean of the 12 monthly average "
               "headcounts x 100. Monthly average headcount = (start-of-month + end-of-month headcount) / 2. "
               "Total terminations include retirements, so voluntary + involuntary may be less than total.")
SMALL_GROUP_NOTE = "Rates for small groups can swing widely; consider headcount before drawing conclusions."


def summaries_to_frame(summaries: list[dict]) -> pd.DataFrame:
    """One row per year. Rounding happens here, at the output edge, not in the calculations."""
    return pd.DataFrame([{
        "year": s["year"],
        "filters": ", ".join(f"{k}={v}" for k, v in s["filters"].items()) or "all employees",
        "months": s["months"],
        "terminations": s["terminations"],
        "avg_headcount": s["avg_headcount"],
        "total_rate_pct": round(s["total_rate"], 2),
        "voluntary_rate_pct": round(s["voluntary_rate"], 2),
        "involuntary_rate_pct": round(s["involuntary_rate"], 2),
    } for s in summaries])


def export_csv(path: Path, summaries: list[dict], monthly: dict[int, pd.DataFrame] | None = None) -> list[Path]:
    """Writes the summary CSV; if monthly tables are given, also writes <name>_monthly.csv. Returns paths written."""
    written = [path]
    summaries_to_frame(summaries).to_csv(path, index=False)
    if monthly:
        monthly_path = path.with_name(f"{path.stem}_monthly{path.suffix}")
        frames = [t.assign(year=y) for y, t in monthly.items()]
        pd.concat(frames)[["year", *monthly[next(iter(monthly))
                                            ].columns]].to_csv(monthly_path, index=False)
        written.append(monthly_path)
    return written


def export_pdf(path: Path, summaries: list[dict], monthly: dict[int, pd.DataFrame] | None = None) -> list[Path]:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    except ImportError:
        raise SystemExit(
            "PDF export needs the reportlab package. Install it with: pip install reportlab")

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=landscape(
        letter), title="Attrition Report")

    def make_table(df: pd.DataFrame) -> Table:
        data = [list(df.columns)] + df.astype(str).values.tolist()
        t = Table(data, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F4858")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#EEF2F5")]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#B0BAC3")),
        ]))
        return t

    story = [Paragraph("Attrition Report", styles["Title"]),
             Paragraph(f"Generated {date.today():%B %d, %Y}",
                       styles["Normal"]), Spacer(1, 12),
             Paragraph("Annual summary", styles["Heading2"]),
             make_table(summaries_to_frame(summaries)), Spacer(1, 12),
             Paragraph(METHOD_NOTE, styles["Italic"]), Spacer(1, 6),
             Paragraph(SMALL_GROUP_NOTE, styles["Italic"])]

    for year, table in (monthly or {}).items():
        story += [PageBreak(), Paragraph(
            f"{year}: month-by-month detail", styles["Heading2"]), make_table(table)]

    doc.build(story)
    return [path]
