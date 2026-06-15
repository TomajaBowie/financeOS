import pytest
from datetime import date
from app.utils.date_helpers import (
    get_week_boundaries,
    get_month_boundaries,
    get_date_range_days,
    is_same_week
)


class TestGetWeekBoundaries:
    def test_monday_is_week_start(self):
        monday = date(2026, 6, 8)
        start, end = get_week_boundaries(monday)
        assert start == date(2026, 6, 8)
        assert end == date(2026, 6, 14)

    def test_sunday_falls_within_correct_week(self):
        """
        Bug: Sunday (weekday=6) causes week_end to be Saturday.
        A Sunday transaction falls outside the week boundary.
        Fix: week_end should be start + 6 days = Sunday.
        """
        sunday = date(2026, 6, 14)
        start, end = get_week_boundaries(sunday)
        assert start == date(2026, 6, 8), \
            f"Week containing Sunday June 14 should start June 8, got {start}"
        assert end == date(2026, 6, 14), \
            f"Week containing Sunday June 14 should end June 14, got {end}"

    def test_wednesday_in_correct_week(self):
        wednesday = date(2026, 6, 10)
        start, end = get_week_boundaries(wednesday)
        assert start == date(2026, 6, 8)
        assert end == date(2026, 6, 14)


class TestGetMonthBoundaries:
    def test_june_boundaries(self):
        start, end = get_month_boundaries(date(2026, 6, 15))
        assert start == date(2026, 6, 1)
        assert end == date(2026, 6, 30)

    def test_january_boundaries(self):
        start, end = get_month_boundaries(date(2026, 1, 1))
        assert start == date(2026, 1, 1)
        assert end == date(2026, 1, 31)

    def test_december_boundaries(self):
        start, end = get_month_boundaries(date(2026, 12, 15))
        assert start == date(2026, 12, 1)
        assert end == date(2026, 12, 31)

    def test_february_boundaries(self):
        start, end = get_month_boundaries(date(2026, 2, 15))
        assert start == date(2026, 2, 1)
        assert end == date(2026, 2, 28)


class TestGetDateRangeDays:
    def test_same_day_is_one(self):
        result = get_date_range_days(date(2026, 6, 1), date(2026, 6, 1))
        assert result == 1

    def test_week_is_seven(self):
        result = get_date_range_days(date(2026, 6, 8), date(2026, 6, 14))
        assert result == 7