import pytest
from decimal import Decimal
from app.utils.calculations import (
    calculate_percentage,
    calculate_category_percentages,
    calculate_net_worth,
    calculate_trend,
    is_budget_exceeded
)


class TestCalculatePercentage:
    def test_basic_percentage(self):
        result = calculate_percentage(Decimal("25"), Decimal("100"))
        assert result == Decimal("25.0")

    def test_zero_total_returns_zero(self):
        result = calculate_percentage(Decimal("50"), Decimal("0"))
        assert result == Decimal("0")

    def test_percentages_sum_to_100(self):
        """
        Bug: float division causes percentages to not sum to 100
        for values like thirds. Fix: use pure Decimal arithmetic.
        """
        totals = {
            "Food": Decimal("100"),
            "Transport": Decimal("100"),
            "Housing": Decimal("100")
        }
        percentages = calculate_category_percentages(totals)
        total = sum(percentages.values())
        assert total == Decimal("100.0"), f"Percentages sum to {total} not 100"


class TestCalculateNetWorth:
    def test_excludes_liability_accounts(self):
        """
        Bug: liability accounts are excluded entirely instead
        of being subtracted. Net worth is overstated.
        Fix: subtract liability and loan balances.
        """
        balances = {
            "1": Decimal("10000"),
            "2": Decimal("5000")
        }
        types = {
            "1": "checking",
            "2": "liability"
        }
        result = calculate_net_worth(balances, types)
        assert result == Decimal("5000"), \
            f"Net worth should be 5000 (10000 - 5000) but got {result}"

    def test_multiple_liabilities(self):
        balances = {
            "1": Decimal("10000"),
            "2": Decimal("3000"),
            "3": Decimal("2000")
        }
        types = {
            "1": "checking",
            "2": "liability",
            "3": "loan"
        }
        result = calculate_net_worth(balances, types)
        assert result == Decimal("5000"), \
            f"Expected 5000 but got {result}"

    def test_no_liabilities(self):
        balances = {"1": Decimal("5000"), "2": Decimal("3000")}
        types = {"1": "checking", "2": "savings"}
        result = calculate_net_worth(balances, types)
        assert result == Decimal("8000")


class TestCalculateTrend:
    def test_trend_sign_for_increased_spending(self):
        """
        Bug: trend returns positive when spending increased.
        For expense tracking, increased spending is negative.
        Fix: invert the sign for expense context.
        """
        current = Decimal("150")
        previous = Decimal("100")
        result = calculate_trend(current, previous)
        assert result < 0, \
            f"Spending increased so trend should be negative but got {result}"

    def test_trend_sign_for_decreased_spending(self):
        current = Decimal("80")
        previous = Decimal("100")
        result = calculate_trend(current, previous)
        assert result > 0, \
            f"Spending decreased so trend should be positive but got {result}"

    def test_zero_previous_returns_zero(self):
        result = calculate_trend(Decimal("100"), Decimal("0"))
        assert result == Decimal("0")


class TestIsBudgetExceeded:
    def test_exactly_at_limit_not_exceeded(self):
        """
        Bug: uses >= so fires at exact limit.
        Fix: use > so it only fires when strictly exceeded.
        """
        result = is_budget_exceeded(Decimal("200"), Decimal("200"))
        assert result == False, \
            "Spending exactly at limit should not be considered exceeded"

    def test_one_cent_over_is_exceeded(self):
        result = is_budget_exceeded(Decimal("200.01"), Decimal("200"))
        assert result == True

    def test_under_limit_not_exceeded(self):
        result = is_budget_exceeded(Decimal("150"), Decimal("200"))
        assert result == False