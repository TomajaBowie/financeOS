import pytest
from datetime import date


class TestRecurringNextDueDate:
    def test_monthly_recurring_on_31st(self, client, auth_headers, test_account):
        """
        Bug: monthly recurring uses timedelta(days=30) instead
        of proper calendar month arithmetic. Created on Jan 31
        next due is March 2 instead of Feb 28.
        Fix: use dateutil.relativedelta or replace month component.
        """
        account_id = test_account["id"]

        recurring = client.post("/api/recurring", json={
            "account_id": account_id,
            "amount": "100.00",
            "transaction_type": "expense",
            "description": "Monthly bill",
            "frequency": "monthly",
            "start_date": "2026-01-31"
        }, headers=auth_headers).json()

        next_due = date.fromisoformat(recurring["next_due_date"])
        assert next_due.month == 2, \
            f"Next due after Jan 31 should be in February but got {next_due}"
        assert next_due.day == 28, \
            f"Next due should be Feb 28 but got {next_due}"

    def test_weekly_recurring_adds_seven_days(self, client, auth_headers, test_account):
        account_id = test_account["id"]

        recurring = client.post("/api/recurring", json={
            "account_id": account_id,
            "amount": "25.00",
            "transaction_type": "expense",
            "description": "Weekly bill",
            "frequency": "weekly",
            "start_date": "2026-06-09"
        }, headers=auth_headers).json()

        next_due = date.fromisoformat(recurring["next_due_date"])
        assert next_due == date(2026, 6, 16)


class TestRecurringDuplicates:
    def test_generate_twice_no_duplicates(self, client, auth_headers, test_account):
        """
        Bug: generate_due_transactions does not check
        last_generated before creating transactions.
        Calling twice on same day creates duplicates.
        Fix: check last_generated == today before generating.
        """
        account_id = test_account["id"]

        client.post("/api/recurring", json={
            "account_id": account_id,
            "amount": "50.00",
            "transaction_type": "expense",
            "description": "Daily bill",
            "frequency": "daily",
            "start_date": "2026-06-09"
        }, headers=auth_headers)

        result1 = client.post(
            "/api/recurring/generate",
            params={"as_of_date": "2026-06-10"},
            headers=auth_headers
        ).json()

        result2 = client.post(
            "/api/recurring/generate",
            params={"as_of_date": "2026-06-10"},
            headers=auth_headers
        ).json()

        transactions = client.get(
            "/api/transactions",
            headers=auth_headers
        ).json()

        recurring_txs = [
            t for t in transactions["transactions"]
            if t["description"] == "Daily bill"
        ]
        assert len(recurring_txs) == 1, \
            f"Should only generate once but found {len(recurring_txs)} transactions"