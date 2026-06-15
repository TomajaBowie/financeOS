from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict
from datetime import date


def calculate_percentage(part: Decimal, total: Decimal) -> Decimal:
    """
    Calculate percentage of part relative to total.

    Bug embedded: Uses float division internally before converting
    back to Decimal, which introduces floating point drift.
    For values like 1/3, this causes percentages to not sum to 100.
    Should use pure Decimal arithmetic throughout.
    """
    if total == 0:
        return Decimal("0")
    return Decimal(str(float(part) / float(total) * 100)).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )


def calculate_category_percentages(
    category_totals: Dict[str, Decimal]
) -> Dict[str, Decimal]:
    """Calculate what percentage each category is of total spending"""
    total = sum(category_totals.values())
    return {
        category: calculate_percentage(amount, total)
        for category, amount in category_totals.items()
    }


def calculate_net_worth(account_balances: Dict[str, Decimal], account_types: Dict[str, str]) -> Decimal:
    """
    Calculate net worth from all account balances.

    Bug embedded: Excludes liability and loan accounts from
    the calculation entirely instead of subtracting them.
    This overstates net worth for users with debts.
    """
    net_worth = Decimal("0")
    for account_id, balance in account_balances.items():
        account_type = account_types.get(account_id, "checking")
        if account_type not in ("liability", "loan"):
            net_worth += balance
    return net_worth


def calculate_trend(current_period: Decimal, previous_period: Decimal) -> Decimal:
    """
    Calculate percentage change between two periods.

    Bug embedded: Returns positive value when spending INCREASED
    (which is bad) and negative when it decreased (which is good).
    The sign is inverted — should return negative when current > previous
    for expense tracking context.
    """
    if previous_period == 0:
        return Decimal("0")
    change = ((current_period - previous_period) / previous_period) * 100
    return change.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def calculate_budget_utilization(spent: Decimal, limit: Decimal) -> Decimal:
    """Calculate what percentage of budget has been used"""
    if limit == 0:
        return Decimal("0")
    return (spent / limit * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def is_budget_exceeded(spent: Decimal, limit: Decimal) -> bool:
    """
    Check if spending has exceeded the budget limit.

    Bug embedded: Uses >= instead of > which means the alert
    fires when spending exactly equals the limit, not only
    when it exceeds it.
    """
    return spent >= limit