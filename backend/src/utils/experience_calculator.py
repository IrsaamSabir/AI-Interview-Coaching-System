"""
Total paid experience from structured job rows. Dates are parsed in Python;
overlapping calendar months are merged (parallel jobs not double-counted).
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional


def _month_ord(year: int, month: int) -> int:
    return year * 12 + month


def _to_half_open(start: tuple[int, int], end: tuple[int, int]) -> tuple[int, int]:
    lo = _month_ord(start[0], start[1])
    hi_incl = _month_ord(end[0], end[1])
    return lo, hi_incl + 1


def _merge_half_open(intervals: list[tuple[int, int]]) -> int:
    if not intervals:
        return 0
    intervals.sort()
    acc_lo, acc_hi = intervals[0]
    total = 0
    for lo, hi in intervals[1:]:
        if lo <= acc_hi:
            acc_hi = max(acc_hi, hi)
        else:
            total += acc_hi - acc_lo
            acc_lo, acc_hi = lo, hi
    total += acc_hi - acc_lo
    return total


def _is_present_token(value: object) -> bool:
    if value is None:
        return False
    t = str(value).strip().lower()
    return t in ("present", "current", "now", "ongoing", "till date", "till now", "today", "-", "")


def parse_job_date(value: Any, ref: datetime, *, is_end: bool) -> Optional[tuple[int, int]]:
    """
    Prefer MM/YYYY (e.g. 07/2025, 7/2025). Also YYYY-MM, YYYY-MM-DD; null / Present => end = ref month.
    """
    if value is None:
        if is_end:
            return ref.year, ref.month
        return None

    if _is_present_token(value):
        if not is_end:
            return None
        return ref.year, ref.month

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        y = int(value)
        if 1950 <= y <= ref.year + 1:
            return y, 12 if is_end else 1
        return None

    s = str(value).strip()
    if not s:
        return None

    # MM/YYYY or M/YYYY (common on resumes)
    m = re.match(r"^(\d{1,2})/(\d{4})$", s)
    if m:
        mo, y = int(m.group(1)), int(m.group(2))
        if 1 <= mo <= 12 and 1950 <= y <= ref.year + 1:
            return y, mo

    # YYYY-MM or YYYY-MM-DD
    for fmt, n in (("%Y-%m-%d", 10), ("%Y-%m", 7)):
        try:
            dt = datetime.strptime(s[:n], fmt)
            return dt.year, dt.month
        except ValueError:
            continue

    m = re.match(r"^(\d{4})-(\d{1,2})(?:-(\d{1,2}))?$", s)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        if 1 <= mo <= 12:
            return y, mo

    m = re.match(r"^(\d{4})$", s)
    if m:
        y = int(m.group(1))
        if 1950 <= y <= ref.year + 1:
            return y, 12 if is_end else 1

    for fmt in ("%b %Y", "%B %Y"):
        try:
            dt = datetime.strptime(s[:20], fmt)
            return dt.year, dt.month
        except ValueError:
            continue

    return None


def total_months_from_jobs(
    jobs: list[dict[str, Any]],
    ref: Optional[datetime] = None,
) -> Optional[int]:
    """
    Build inclusive month ranges per job, merge overlaps, return total distinct months.
    Returns None if there are jobs but no valid interval could be parsed.
    """
    ref = ref or datetime.now()
    if not jobs:
        return 0

    half_open: list[tuple[int, int]] = []
    any_row = False

    for row in jobs or []:
        if not isinstance(row, dict):
            continue
        start_raw = row.get("start")
        end_raw = row.get("end")
        any_row = True

        start = parse_job_date(start_raw, ref, is_end=False)
        if start is None:
            continue

        end = parse_job_date(end_raw, ref, is_end=True)
        if end is None:
            continue

        if _month_ord(end[0], end[1]) < _month_ord(start[0], start[1]):
            start, end = end, start

        half_open.append(_to_half_open(start, end))

    if not half_open:
        return None if any_row else 0
    return _merge_half_open(half_open)


def format_experience_label(total_months: int) -> str:
    if total_months <= 0:
        return "0 months"
    y, m = divmod(total_months, 12)
    if y == 0:
        return f"{m} month{'s' if m != 1 else ''}"
    if m == 0:
        return f"{y} year{'s' if y != 1 else ''}"
    return f"{y} year{'s' if y != 1 else ''} {m} month{'s' if m != 1 else ''}"
