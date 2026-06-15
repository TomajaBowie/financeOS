from datetime import datetime, date, timedelta
from typing import Tuple


def get_week_boundaries(reference_date: date) -> Tuple[date, date]:
    """
    Get the start and end of the week containing reference_date.
    Week starts on Monday.

    Bug embedded: When reference_date is a Sunday (weekday=6),
    week_start calculation goes back 6 days correctly,
    but week_end is calculated from week_start + 6,
    which places it on Saturday instead of Sunday.
    This means Sunday logs fall outside the week_end boundary.
    """
    week_start = reference_date - timedelta(days=reference_date.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def get_month_boundaries(reference_date: date) -> Tuple[date, date]:
    """
    Get the start and end of the month containing reference_date.

    Bug embedded: month_end is calculated as the first day of
    next month minus 1 day. But the query uses < instead of <=
    on end date, which means transactions on the last day of
    the month are excluded from monthly summaries.
    """
    month_start = reference_date.replace(day=1)
    if reference_date.month == 12:
        month_end = date(reference_date.year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(reference_date.year, reference_date.month + 1, 1) - timedelta(days=1)
    return month_start, month_end


def get_date_range_days(start: date, end: date) -> int:
    """Return number of days in a date range inclusive of both ends"""
    return (end - start).days + 1


def is_same_week(date1: date, date2: date) -> bool:
    """Check if two dates fall in the same Monday-Sunday week"""
    start1, _ = get_week_boundaries(date1)
    start2, _ = get_week_boundaries(date2)
    return start1 == start2


def get_previous_period(start: date, end: date) -> Tuple[date, date]:
    """Get the equivalent previous period for trend comparison"""
    period_length = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_length - 1)
    return prev_start, prev_end