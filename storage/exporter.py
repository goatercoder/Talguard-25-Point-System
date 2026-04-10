"""
Export ScreenerResult to CSV or JSON bytes for download.
"""

import csv
import io
import json

from core.models import ScreenerResult


def to_csv_bytes(result: ScreenerResult) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)

    # Header rows
    writer.writerow(["Talguard Investment Screener — Analysis Report"])
    writer.writerow(["Ticker", result.ticker])
    writer.writerow(["Company", result.company_name])
    writer.writerow(["Sector", result.sector])
    writer.writerow(["Industry", result.industry])
    writer.writerow(["Analysis Date", result.analysis_date.strftime("%Y-%m-%d %H:%M")])
    writer.writerow(["Total Score", f"{result.total_points}/23"])
    writer.writerow(["Passed", "YES" if result.passed else "NO"])
    writer.writerow([])

    # Criteria table
    writer.writerow(["#", "Criterion", "Status", "Value", "Threshold", "Points", "AI Reasoning"])
    for c in result.criteria:
        writer.writerow([
            c.criterion_id,
            c.name,
            c.status,
            c.actual_display or "",
            c.threshold_display or "",
            c.points,
            (c.ai_reasoning or "").replace("\n", " "),
        ])

    return buf.getvalue().encode("utf-8-sig")  # UTF-8 with BOM for Excel compatibility


def to_json_bytes(result: ScreenerResult) -> bytes:
    return json.dumps(result.to_dict(), indent=2).encode("utf-8")
