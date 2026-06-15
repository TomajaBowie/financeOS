import pytest
from datetime import date


class TestSpendingTrend:
    def test_increased_spending_negative_trend(self, client, auth_headers, test_account):
        """
        Bug: calculate_trend returns positive when spending increased.
        For expense tracking, increased spending should be negative trend.
        Fix: invert sign in calculate_trend.
        """
        account_id = test_account["id"]

        client.post("/api/transactions", json={
            "account_id": account_id,
            "amount": "100.00",
            "transaction_type": "expense",
            "description": "May expense",
            "transaction_date": "2026-05-15T10:00:00"
        }, headers=auth_headers)

        client.post("/api/transactions", json={
            "account_id": account_id,
            "amount": "200.00",
            "transaction_type": "expense",
            "description": "June expense",
            "transaction_date": "2026-06-15T10:00:00"
        }, headers=auth_headers)

        response = client.get(
            "/api/reports/trend",
            params={
                "start_date": "2026-06-01",
                "end_date": "2026-06-30"
            },
            headers=auth_headers
        )
        data = response.json()

        assert float(data["change_percentage"]) < 0, \
            f"Spending increased so trend should be negative but got {data['change_percentage']}"


class TestNetWorthReport:
    def test_liability_subtracted_from_net_worth(self, client, auth_headers):
        """
        Bug: liability accounts excluded not subtracted.
        Fix: subtract liability/loan balances from net worth.
        """
        client.post("/api/accounts", json={
            "name": "Checking",
            "account_type": "checking",
            "initial_balance": "10000.00",
            "currency": "USD"
        }, headers=auth_headers)

        client.post("/api/accounts", json={
            "name": "Loan",
            "account_type": "loan",
            "initial_balance": "5000.00",
            "currency": "USD"
        }, headers=auth_headers)

        response = client.get(
            "/api/reports/net-worth",
            headers=auth_headers
        )
        data = response.json()

        assert float(data["net_worth"]) == float(data["total_assets"]) - float(data["total_liabilities"]), \
            f"Net worth should be assets minus liabilities"
        assert float(data["total_liabilities"]) > 0, \
            "Loan account should appear as liability"


class TestWeeklyReport:
    def test_sunday_transactions_included(self, client, auth_headers, test_account):
        """
        Bug: week boundary bug means Sunday transactions
        fall outside the week_end boundary.
        Fix: ensure week_end is Sunday not Saturday.
        """
        account_id = test_account["id"]

        client.post("/api/transactions", json={
            "account_id": account_id,
            "amount": "75.00",
            "transaction_type": "expense",
            "description": "Sunday expense",
            "transaction_date": "2026-06-14T18:00:00"
        }, headers=auth_headers)

        response = client.get(
            "/api/reports/weekly",
            params={"reference_date": "2026-06-14"},
            headers=auth_headers
        )
        data = response.json()

        assert float(data["expenses"]) == 75.0, \
            f"Sunday transaction should be in weekly report but expenses={data['expenses']}"